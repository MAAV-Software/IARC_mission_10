"""
CUDA-Accelerated Method B: Voronoi Diagram Pathfinding
Uses GPU acceleration for Voronoi-based minefield navigation.
Optimized for NVIDIA GPUs using CuPy and PyTorch.
"""

import numpy as np
import cupy as cp
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, distance
import time
import networkx as nx

# Check CUDA availability
if torch.cuda.is_available():
    device = torch.device('cuda')
    print(f"CUDA available! Using: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
else:
    device = torch.device('cpu')
    print("WARNING: CUDA not available, falling back to CPU")

class VoronoiPathfinderCUDA:
    def __init__(self, grid_size=(300, 80), num_mines=1000, mine_buffer=3.0):
        """
        Initialize the CUDA-accelerated Voronoi pathfinder.
        
        Args:
            grid_size: (width, height) in feet - matching IARC arena dimensions
            num_mines: Number of mines to place
            mine_buffer: Minimum safety buffer around each mine in feet
        """
        self.width, self.height = grid_size
        self.num_mines = num_mines
        self.mine_buffer = mine_buffer
        self.mines = None
        self.mines_gpu = None
        self.start = (0, self.height / 2)
        self.end = (self.width, self.height / 2)
        self.vor = None
        self.graph = None
        self.device = device
        
    def generate_minefield(self, seed=42):
        """Generate random mine positions and transfer to GPU."""
        np.random.seed(seed)
        mines_np = np.random.rand(self.num_mines, 2).astype(np.float32)
        
        # Scale to arena size with safe zones
        safe_zone = 10
        mines_np[:, 0] = mines_np[:, 0] * (self.width - 2*safe_zone) + safe_zone
        mines_np[:, 1] = mines_np[:, 1] * self.height
        
        self.mines = mines_np
        
        # Transfer to GPU
        self.mines_cp = cp.asarray(mines_np)
        self.mines_torch = torch.from_numpy(mines_np).to(self.device)
    
    def compute_voronoi(self):
        """Compute Voronoi diagram with boundary reflections."""
        # Add reflected points for better boundary handling
        reflected_points = []
        
        for mine in self.mines:
            x, y = mine
            
            # Boundary reflections
            if x < self.width / 2:
                reflected_points.append([-x, y])
            if x > self.width / 2:
                reflected_points.append([2 * self.width - x, y])
            if y > self.height / 2:
                reflected_points.append([x, 2 * self.height - y])
            if y < self.height / 2:
                reflected_points.append([x, -y])
            
            # Corner reflections
            if x < self.width / 2 and y < self.height / 2:
                reflected_points.append([-x, -y])
            if x < self.width / 2 and y > self.height / 2:
                reflected_points.append([-x, 2 * self.height - y])
            if x > self.width / 2 and y < self.height / 2:
                reflected_points.append([2 * self.width - x, -y])
            if x > self.width / 2 and y > self.height / 2:
                reflected_points.append([2 * self.width - x, 2 * self.height - y])
        
        # Combine original and reflected points
        all_points = np.vstack([self.mines, reflected_points])
        
        # Compute Voronoi diagram (still CPU-based)
        self.vor = Voronoi(all_points)
        
        return self.vor
    
    def filter_vertices_gpu(self):
        """GPU-accelerated filtering of Voronoi vertices."""
        vertices = self.vor.vertices
        n_vertices = len(vertices)
        
        if n_vertices == 0:
            return np.array([]), []
        
        # Transfer vertices to GPU
        vertices_gpu = torch.tensor(vertices, dtype=torch.float32, device=self.device)
        
        # Check bounds
        in_bounds = (vertices_gpu[:, 0] >= 0) & (vertices_gpu[:, 0] <= self.width) & \
                   (vertices_gpu[:, 1] >= 0) & (vertices_gpu[:, 1] <= self.height)
        
        # Compute distances to all mines using broadcasting
        vertices_expanded = vertices_gpu.unsqueeze(1)  # (V, 1, 2)
        mines_expanded = self.mines_torch.unsqueeze(0)  # (1, M, 2)
        
        # Compute all pairwise distances
        distances = torch.norm(vertices_expanded - mines_expanded, dim=2)  # (V, M)
        
        # Check if minimum distance to any mine is greater than buffer
        min_distances = torch.min(distances, dim=1)[0]  # (V,)
        safe_from_mines = min_distances >= self.mine_buffer
        
        # Combine conditions
        valid_mask = in_bounds & safe_from_mines
        valid_indices = torch.where(valid_mask)[0].cpu().numpy()
        
        valid_vertices = vertices[valid_indices]
        
        return valid_vertices, valid_indices.tolist()
    
    def batch_edge_safety_check_gpu(self, edges):
        """
        GPU-accelerated batch checking of edge safety.
        
        Args:
            edges: List of (p1, p2) tuples representing edges
        
        Returns:
            Boolean array indicating which edges are safe
        """
        if len(edges) == 0:
            return []
        
        # Prepare edge data
        starts = torch.tensor([e[0] for e in edges], dtype=torch.float32, device=self.device)
        ends = torch.tensor([e[1] for e in edges], dtype=torch.float32, device=self.device)
        
        # Compute distances from all mines to all edges
        n_edges = len(edges)
        n_mines = len(self.mines)
        
        # Reshape for broadcasting
        mines = self.mines_torch.unsqueeze(1)  # (M, 1, 2)
        starts_exp = starts.unsqueeze(0)  # (1, E, 2)
        ends_exp = ends.unsqueeze(0)  # (1, E, 2)
        
        # Vector from start to end for each edge
        edge_vecs = ends_exp - starts_exp  # (1, E, 2)
        
        # Vector from start to each mine
        start_to_mines = mines - starts_exp  # (M, E, 2)
        
        # Compute t parameter for closest point on each edge to each mine
        edge_lens_sq = torch.sum(edge_vecs ** 2, dim=2)  # (1, E)
        edge_lens_sq = torch.clamp(edge_lens_sq, min=1e-8)
        
        dots = torch.sum(start_to_mines * edge_vecs, dim=2)  # (M, E)
        t = torch.clamp(dots / edge_lens_sq, 0, 1).unsqueeze(2)  # (M, E, 1)
        
        # Find closest points
        closest_points = starts_exp + t * edge_vecs  # (M, E, 2)
        
        # Compute distances
        distances = torch.norm(mines - closest_points, dim=2)  # (M, E)
        
        # Check if all mines are far enough from each edge
        min_distances = torch.min(distances, dim=0)[0]  # (E,)
        safe = (min_distances >= self.mine_buffer).cpu().numpy()
        
        return safe
    
    def build_voronoi_graph_gpu(self):
        """Build graph from Voronoi edges with GPU acceleration."""
        valid_vertices, vertex_indices = self.filter_vertices_gpu()
        
        if len(valid_vertices) == 0:
            print("Warning: No valid Voronoi vertices found!")
            return None
        
        # Create NetworkX graph
        self.graph = nx.Graph()
        
        # Add nodes
        self.graph.add_node('start', pos=self.start)
        self.graph.add_node('end', pos=self.end)
        
        for i, vertex in enumerate(valid_vertices):
            self.graph.add_node(f'v{i}', pos=tuple(vertex))
        
        # Prepare batch of edges to check
        vertex_to_node = {tuple(v): f'v{i}' for i, v in enumerate(valid_vertices)}
        potential_edges = []
        edge_info = []
        
        # Collect Voronoi ridge edges
        for ridge in self.vor.ridge_vertices:
            if -1 not in ridge:
                v1 = tuple(self.vor.vertices[ridge[0]])
                v2 = tuple(self.vor.vertices[ridge[1]])
                
                if v1 in vertex_to_node and v2 in vertex_to_node:
                    potential_edges.append((v1, v2))
                    edge_info.append((vertex_to_node[v1], vertex_to_node[v2]))
        
        # Batch check edge safety on GPU
        if potential_edges:
            safe_edges = self.batch_edge_safety_check_gpu(potential_edges)
            
            # Add safe edges to graph
            for (node1, node2), is_safe in zip(edge_info, safe_edges):
                if is_safe:
                    pos1 = self.graph.nodes[node1]['pos']
                    pos2 = self.graph.nodes[node2]['pos']
                    dist = distance.euclidean(pos1, pos2)
                    self.graph.add_edge(node1, node2, weight=dist)
        
        # Connect start and end to nearby vertices
        start_edges = []
        start_nodes = []
        end_edges = []
        end_nodes = []
        
        for node in self.graph.nodes():
            if node not in ['start', 'end']:
                pos = self.graph.nodes[node]['pos']
                start_edges.append((self.start, pos))
                start_nodes.append(node)
                end_edges.append((self.end, pos))
                end_nodes.append(node)
        
        # Batch check connectivity on GPU
        if start_edges:
            start_safe = self.batch_edge_safety_check_gpu(start_edges)
            for node, is_safe in zip(start_nodes, start_safe):
                if is_safe:
                    pos = self.graph.nodes[node]['pos']
                    dist = distance.euclidean(self.start, pos)
                    self.graph.add_edge('start', node, weight=dist)
        
        if end_edges:
            end_safe = self.batch_edge_safety_check_gpu(end_edges)
            for node, is_safe in zip(end_nodes, end_safe):
                if is_safe:
                    pos = self.graph.nodes[node]['pos']
                    dist = distance.euclidean(self.end, pos)
                    self.graph.add_edge('end', node, weight=dist)
        
        # Check direct path
        direct_safe = self.batch_edge_safety_check_gpu([(self.start, self.end)])
        if direct_safe[0]:
            dist = distance.euclidean(self.start, self.end)
            self.graph.add_edge('start', 'end', weight=dist)
        
        return self.graph
    
    def find_shortest_path(self):
        """Find shortest path through Voronoi graph."""
        if self.graph is None or 'start' not in self.graph or 'end' not in self.graph:
            print("Graph not properly initialized")
            return None, float('inf')
        
        try:
            path_nodes = nx.shortest_path(self.graph, 'start', 'end', weight='weight')
            path_length = nx.shortest_path_length(self.graph, 'start', 'end', weight='weight')
            
            path_coords = []
            for node in path_nodes:
                path_coords.append(self.graph.nodes[node]['pos'])
            
            return path_coords, path_length
            
        except nx.NetworkXNoPath:
            print("No path found between start and end!")
            return None, float('inf')
    
    def find_optimal_path(self):
        """Main method to find optimal path using GPU-accelerated Voronoi diagram."""
        print("Computing Voronoi diagram...")
        start_time = time.time()
        
        # Warm up GPU
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        
        # Compute Voronoi diagram
        self.compute_voronoi()
        voronoi_time = time.time() - start_time
        print(f"Voronoi computation time: {voronoi_time:.3f} seconds")
        
        # Build graph with GPU acceleration
        print("Building graph from Voronoi edges (GPU-accelerated)...")
        graph_start = time.time()
        
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        
        self.build_voronoi_graph_gpu()
        
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        
        graph_time = time.time() - graph_start
        print(f"Graph building time: {graph_time:.3f} seconds")
        
        # Find shortest path
        print("Finding shortest path...")
        path_start = time.time()
        path, path_distance = self.find_shortest_path()
        path_time = time.time() - path_start
        print(f"Pathfinding time: {path_time:.3f} seconds")
        
        total_time = time.time() - start_time
        
        if self.graph:
            print(f"\nGraph statistics:")
            print(f"Number of nodes: {self.graph.number_of_nodes()}")
            print(f"Number of edges: {self.graph.number_of_edges()}")
        
        # Report GPU memory usage
        if self.device.type == 'cuda':
            memory_allocated = torch.cuda.memory_allocated() / 1024**2
            memory_cached = torch.cuda.memory_reserved() / 1024**2
            print(f"GPU Memory - Allocated: {memory_allocated:.1f}MB, Cached: {memory_cached:.1f}MB")
        
        return path, path_distance, total_time
    
    def visualize(self, path=None, title="CUDA-Accelerated Voronoi Method"):
        """Visualize the minefield, Voronoi diagram, and path."""
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Draw boundary
        ax.add_patch(plt.Rectangle((0, 0), self.width, self.height, 
                                  fill=False, edgecolor='black', linewidth=2))
        
        # Draw Voronoi edges
        if self.vor is not None:
            for ridge in self.vor.ridge_vertices:
                if -1 not in ridge:
                    v1 = self.vor.vertices[ridge[0]]
                    v2 = self.vor.vertices[ridge[1]]
                    
                    if (0 <= v1[0] <= self.width and 0 <= v1[1] <= self.height and
                        0 <= v2[0] <= self.width and 0 <= v2[1] <= self.height):
                        # Quick safety check
                        edge_safe = self.batch_edge_safety_check_gpu([(v1, v2)])
                        if edge_safe[0]:
                            ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'b-', 
                                  alpha=0.2, linewidth=0.5)
        
        # Draw mines
        for mine in self.mines:
            ax.plot(mine[0], mine[1], 'r^', markersize=8)
            circle = plt.Circle(mine, self.mine_buffer, fill=False, 
                               edgecolor='red', linestyle='--', alpha=0.5)
            ax.add_patch(circle)
        
        # Draw start and end
        ax.plot(self.start[0], self.start[1], 'go', markersize=15, label='Start')
        ax.plot(self.end[0], self.end[1], 'bo', markersize=15, label='End')
        
        # Draw path
        if path:
            path_x = [p[0] for p in path]
            path_y = [p[1] for p in path]
            ax.plot(path_x, path_y, 'g-', linewidth=3, label='Safe Path', zorder=10)
            
            for i, point in enumerate(path[1:-1], 1):
                ax.plot(point[0], point[1], 'yo', markersize=5, zorder=10)
        
        ax.set_xlim(-5, self.width + 5)
        ax.set_ylim(-5, self.height + 5)
        ax.set_aspect('equal')
        ax.set_xlabel('Distance (feet)')
        ax.set_ylabel('Distance (feet)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add GPU info
        if self.device.type == 'cuda':
            ax.text(0.5, 1.02, f'GPU: {torch.cuda.get_device_name(0)}', 
                   transform=ax.transAxes, ha='center', fontsize=10, color='green')
        
        return fig

def main():
    # Initialize CUDA-accelerated pathfinder
    pathfinder = VoronoiPathfinderCUDA(grid_size=(300, 80), num_mines=1000, mine_buffer=3.0)
    
    # Generate minefield
    pathfinder.generate_minefield(seed=42)
    
    # Find optimal path with GPU acceleration
    print("=" * 60)
    print("CUDA-ACCELERATED VORONOI METHOD")
    print("=" * 60)
    print(f"Arena size: {pathfinder.width} x {pathfinder.height} feet")
    print(f"Number of mines: {pathfinder.num_mines}")
    print(f"Mine safety buffer: {pathfinder.mine_buffer} feet")
    print()
    
    path, distance, total_time = pathfinder.find_optimal_path()
    
    print(f"\nResults:")
    print(f"Total computation time: {total_time:.2f} seconds")
    print(f"Optimal path distance: {distance:.2f} feet")
    if path:
        print(f"Number of waypoints: {len(path)}")
    
    # Visualize
    fig = pathfinder.visualize(path, 
                              title=f"CUDA Voronoi Method - Distance: {distance:.2f} ft")
    plt.savefig('voronoi_cuda_result.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return pathfinder, path, distance

if __name__ == "__main__":
    main()

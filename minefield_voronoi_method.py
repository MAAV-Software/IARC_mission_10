"""
Method B: Voronoi Diagram Pathfinding
Finds shortest safe path through minefield using Voronoi diagrams
to maximize distance from mines while maintaining safety buffer.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d, distance
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
import time
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

class VoronoiPathfinder:
    def __init__(self, grid_size=(300, 80), num_mines=1000, mine_buffer=3.0):
        """
        Initialize the Voronoi-based pathfinder.
        
        Args:
            grid_size: (width, height) in feet - matching IARC arena dimensions
            num_mines: Number of mines to place
            mine_buffer: Minimum safety buffer around each mine in feet
        """
        self.width, self.height = grid_size
        self.num_mines = num_mines
        self.mine_buffer = mine_buffer
        self.mines = []
        self.start = (0, self.height / 2)  # Start on left side, middle
        self.end = (self.width, self.height / 2)  # End on right side, middle
        self.vor = None
        self.graph = None
        
    def generate_minefield(self, seed=42):
        """Generate random mine positions."""
        np.random.seed(seed)
        self.mines = []
        
        # Generate mines ensuring they don't overlap with start/end zones
        safe_zone = 10  # Keep mines away from start/end edges
        for _ in range(self.num_mines):
            x = np.random.uniform(safe_zone, self.width - safe_zone)
            y = np.random.uniform(0, self.height)
            self.mines.append((x, y))
    
    def compute_voronoi(self):
        """Compute Voronoi diagram with boundary reflections."""
        mines_array = np.array(self.mines)
        
        # Add reflected points for better boundary handling
        reflected_points = []
        
        # Reflect across boundaries
        for mine in self.mines:
            x, y = mine
            
            # Left boundary reflection
            if x < self.width / 2:
                reflected_points.append((-x, y))
            
            # Right boundary reflection
            if x > self.width / 2:
                reflected_points.append((2 * self.width - x, y))
            
            # Top boundary reflection
            if y > self.height / 2:
                reflected_points.append((x, 2 * self.height - y))
            
            # Bottom boundary reflection
            if y < self.height / 2:
                reflected_points.append((x, -y))
            
            # Corner reflections
            if x < self.width / 2 and y < self.height / 2:
                reflected_points.append((-x, -y))
            if x < self.width / 2 and y > self.height / 2:
                reflected_points.append((-x, 2 * self.height - y))
            if x > self.width / 2 and y < self.height / 2:
                reflected_points.append((2 * self.width - x, -y))
            if x > self.width / 2 and y > self.height / 2:
                reflected_points.append((2 * self.width - x, 2 * self.height - y))
        
        # Combine original and reflected points
        all_points = np.vstack([mines_array, reflected_points])
        
        # Compute Voronoi diagram
        self.vor = Voronoi(all_points)
        
        return self.vor
    
    def filter_valid_vertices(self):
        """Filter Voronoi vertices to keep only those within bounds and safe from mines."""
        valid_vertices = []
        vertex_indices = []
        
        for i, vertex in enumerate(self.vor.vertices):
            x, y = vertex
            
            # Check if vertex is within bounds
            if 0 <= x <= self.width and 0 <= y <= self.height:
                # Check if vertex is safe from all mines
                is_safe = True
                for mine in self.mines:
                    dist = distance.euclidean(vertex, mine)
                    if dist < self.mine_buffer:
                        is_safe = False
                        break
                
                if is_safe:
                    valid_vertices.append(vertex)
                    vertex_indices.append(i)
        
        return np.array(valid_vertices), vertex_indices
    
    def build_voronoi_graph(self):
        """Build a graph from Voronoi edges that are safe from mines."""
        valid_vertices, vertex_indices = self.filter_valid_vertices()
        
        if len(valid_vertices) == 0:
            print("Warning: No valid Voronoi vertices found!")
            return None
        
        # Create NetworkX graph
        self.graph = nx.Graph()
        
        # Add start and end nodes
        self.graph.add_node('start', pos=self.start)
        self.graph.add_node('end', pos=self.end)
        
        # Add valid Voronoi vertices as nodes
        for i, vertex in enumerate(valid_vertices):
            self.graph.add_node(f'v{i}', pos=tuple(vertex))
        
        # Add edges between Voronoi vertices along ridges
        vertex_to_node = {tuple(v): f'v{i}' for i, v in enumerate(valid_vertices)}
        
        for ridge in self.vor.ridge_vertices:
            if -1 not in ridge:  # Ignore infinite ridges
                v1 = tuple(self.vor.vertices[ridge[0]])
                v2 = tuple(self.vor.vertices[ridge[1]])
                
                # Check if both vertices are valid
                if v1 in vertex_to_node and v2 in vertex_to_node:
                    # Check if edge is safe from mines
                    if self.is_edge_safe(v1, v2):
                        dist = distance.euclidean(v1, v2)
                        self.graph.add_edge(vertex_to_node[v1], vertex_to_node[v2], weight=dist)
        
        # Connect start to nearby safe vertices (limit search radius)
        max_connect_dist = max(self.width, self.height) * 0.15
        for node in self.graph.nodes():
            if node not in ['start', 'end']:
                pos = self.graph.nodes[node]['pos']
                dist = distance.euclidean(self.start, pos)
                if dist <= max_connect_dist and self.is_edge_safe(self.start, pos):
                    self.graph.add_edge('start', node, weight=dist)

        # If no edges found, expand search radius progressively
        if self.graph.degree('start') == 0:
            for node in self.graph.nodes():
                if node not in ['start', 'end']:
                    pos = self.graph.nodes[node]['pos']
                    dist = distance.euclidean(self.start, pos)
                    if dist <= max_connect_dist * 3 and self.is_edge_safe(self.start, pos):
                        self.graph.add_edge('start', node, weight=dist)

        # Connect end to nearby safe vertices (limit search radius)
        for node in self.graph.nodes():
            if node not in ['start', 'end']:
                pos = self.graph.nodes[node]['pos']
                dist = distance.euclidean(self.end, pos)
                if dist <= max_connect_dist and self.is_edge_safe(self.end, pos):
                    self.graph.add_edge('end', node, weight=dist)

        # If no edges found, expand search radius progressively
        if self.graph.degree('end') == 0:
            for node in self.graph.nodes():
                if node not in ['start', 'end']:
                    pos = self.graph.nodes[node]['pos']
                    dist = distance.euclidean(self.end, pos)
                    if dist <= max_connect_dist * 3 and self.is_edge_safe(self.end, pos):
                        self.graph.add_edge('end', node, weight=dist)
        
        # Also check direct path from start to end
        if self.is_edge_safe(self.start, self.end):
            dist = distance.euclidean(self.start, self.end)
            self.graph.add_edge('start', 'end', weight=dist)
        
        return self.graph
    
    def is_edge_safe(self, p1, p2):
        """Check if an edge is safe from all mines (maintains buffer distance)."""
        for mine in self.mines:
            # Calculate distance from mine to line segment
            dist = self.point_to_line_distance(mine, p1, p2)
            if dist < self.mine_buffer:
                return False
        return True
    
    def point_to_line_distance(self, point, line_start, line_end):
        """Calculate minimum distance from point to line segment."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Vectord from start to end
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            # Line segment is a point
            return np.sqrt((x0 - x1)**2 + (y0 - y1)**2)
        
        # Parameter t for closest point on line
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)))
        
        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return np.sqrt((x0 - closest_x)**2 + (y0 - closest_y)**2)
    
    def find_shortest_path(self):
        """Find shortest path through Voronoi graph using Dijkstra's algorithm."""
        if self.graph is None or 'start' not in self.graph or 'end' not in self.graph:
            print("Graph not properly initialized")
            return None, float('inf')
        
        try:
            # Use NetworkX to find shortest path
            path_nodes = nx.shortest_path(self.graph, 'start', 'end', weight='weight')
            path_length = nx.shortest_path_length(self.graph, 'start', 'end', weight='weight')
            
            # Convert node IDs to coordinates
            path_coords = []
            for node in path_nodes:
                path_coords.append(self.graph.nodes[node]['pos'])
            
            return path_coords, path_length
            
        except nx.NetworkXNoPath:
            print("No path found between start and end!")
            return None, float('inf')
    
    def find_optimal_path(self):
        """Main method to find optimal path using Voronoi diagram."""
        print("Computing Voronoi diagram...")
        start_time = time.time()
        
        # Compute Voronoi diagram
        self.compute_voronoi()
        voronoi_time = time.time() - start_time
        print(f"Voronoi computation time: {voronoi_time:.3f} seconds")
        
        # Build graph from Voronoi edges
        print("Building graph from Voronoi edges...")
        graph_start = time.time()
        self.build_voronoi_graph()
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
        
        return path, path_distance, total_time
    
    def visualize(self, path=None, title="Voronoi Method Pathfinding"):
        """Visualize the minefield, Voronoi diagram, and path."""
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Draw minefield boundary
        ax.add_patch(plt.Rectangle((0, 0), self.width, self.height, 
                                  fill=False, edgecolor='black', linewidth=2))
        
        # Draw Voronoi diagram (filtered edges only)
        if self.vor is not None:
            for ridge in self.vor.ridge_vertices:
                if -1 not in ridge:  # Ignore infinite ridges
                    v1 = self.vor.vertices[ridge[0]]
                    v2 = self.vor.vertices[ridge[1]]
                    
                    # Check if edge is within bounds and safe
                    if (0 <= v1[0] <= self.width and 0 <= v1[1] <= self.height and
                        0 <= v2[0] <= self.width and 0 <= v2[1] <= self.height):
                        if self.is_edge_safe(v1, v2):
                            ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'b-', 
                                  alpha=0.2, linewidth=0.5)
        
        # Draw mines with buffer zones
        for mine in self.mines:
            # Mine location
            ax.plot(mine[0], mine[1], 'r^', markersize=8)
            # Safety buffer
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
            
            # Draw waypoints
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
        
        return fig

def main():
    # Initialize pathfinder with IARC arena dimensions
    pathfinder = VoronoiPathfinder(grid_size=(300, 80), num_mines=1000, mine_buffer=3.0)
    
    # Generate minefield (same seed as tangent method for fair comparison)
    pathfinder.generate_minefield(seed=42)
    
    # Find optimal path
    print("=" * 60)
    print("VORONOI METHOD - Diagram-based Pathfinding")
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
    
    # Visualize results
    fig = pathfinder.visualize(path, title=f"Voronoi Method - Distance: {distance:.2f} ft")
    plt.savefig('voronoi_method_result.png', dpi=150, bbox_inches='tight')
    
    # Additional analysis plot - show Voronoi cell sizes
    if pathfinder.vor is not None:
        fig2, ax = plt.subplots(figsize=(12, 8))
        
        # Color Voronoi regions by distance to nearest mine
        voronoi_plot_2d(pathfinder.vor, ax=ax, show_vertices=False, 
                       line_colors='blue', line_width=0.5, line_alpha=0.3, 
                       point_size=2)
        
        # Overlay mines
        for mine in pathfinder.mines:
            ax.plot(mine[0], mine[1], 'r^', markersize=6)
            circle = plt.Circle(mine, pathfinder.mine_buffer, fill=False, 
                              edgecolor='red', linestyle='--', alpha=0.5)
            ax.add_patch(circle)
        
        # Overlay path
        if path:
            path_x = [p[0] for p in path]
            path_y = [p[1] for p in path]
            ax.plot(path_x, path_y, 'g-', linewidth=3, label='Safe Path')
        
        ax.set_xlim(0, pathfinder.width)
        ax.set_ylim(0, pathfinder.height)
        ax.set_aspect('equal')
        ax.set_xlabel('Distance (feet)')
        ax.set_ylabel('Distance (feet)')
        ax.set_title('Voronoi Diagram with Safe Path')
        ax.legend()
        
        plt.savefig('voronoi_diagram_detail.png', dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return pathfinder, path, distance

if __name__ == "__main__":
    main()
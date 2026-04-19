"""
CUDA-Accelerated Method A: Iterative Circle Reduction with Tangent Paths
Uses GPU acceleration for minefield navigation pathfinding.
Optimized for NVIDIA GPUs using CuPy and PyTorch.
"""

import numpy as np
import cupy as cp
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from scipy.spatial import distance
import time
import heapq

# Check CUDA availability
if torch.cuda.is_available():
    device = torch.device('cuda')
    print(f"CUDA available! Using: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Compute Capability: {torch.cuda.get_device_capability(0)}")
else:
    device = torch.device('cpu')
    print("WARNING: CUDA not available, falling back to CPU")

class TangentPathfinderCUDA:
    def __init__(self, grid_size=(300, 80), num_mines=1000, mine_buffer=3.0):
        """
        Initialize the CUDA-accelerated tangent-based pathfinder.
        
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
        
        # Transfer to GPU using both CuPy and PyTorch
        self.mines_cp = cp.asarray(mines_np)
        self.mines_torch = torch.from_numpy(mines_np).to(self.device)
    
    def batch_point_to_line_distance_gpu(self, mines, line_starts, line_ends):
        """
        GPU-accelerated batch computation of distances from mines to line segments.
        
        Args:
            mines: (N, 2) tensor of mine positions
            line_starts: (M, 2) tensor of line segment start points
            line_ends: (M, 2) tensor of line segment end points
        
        Returns:
            (N, M) tensor of distances
        """
        # Convert to PyTorch tensors if not already
        if not isinstance(mines, torch.Tensor):
            mines = torch.tensor(mines, dtype=torch.float32, device=self.device)
        if not isinstance(line_starts, torch.Tensor):
            line_starts = torch.tensor(line_starts, dtype=torch.float32, device=self.device)
        if not isinstance(line_ends, torch.Tensor):
            line_ends = torch.tensor(line_ends, dtype=torch.float32, device=self.device)
        
        # Reshape for broadcasting
        mines = mines.unsqueeze(1)  # (N, 1, 2)
        line_starts = line_starts.unsqueeze(0)  # (1, M, 2)
        line_ends = line_ends.unsqueeze(0)  # (1, M, 2)
        
        # Vector from start to end
        line_vec = line_ends - line_starts  # (1, M, 2)
        
        # Vector from start to point
        start_to_point = mines - line_starts  # (N, M, 2)
        
        # Compute t parameter for closest point on line
        line_len_sq = torch.sum(line_vec ** 2, dim=2, keepdim=True)  # (1, M, 1)
        line_len_sq = torch.clamp(line_len_sq, min=1e-8)  # Avoid division by zero
        
        dot_product = torch.sum(start_to_point * line_vec, dim=2, keepdim=True)  # (N, M, 1)
        t = torch.clamp(dot_product / line_len_sq, 0, 1)  # (N, M, 1)
        
        # Closest point on line segment
        closest = line_starts + t * line_vec  # (N, M, 2)
        
        # Distance from mine to closest point
        distances = torch.norm(mines - closest, dim=2)  # (N, M)
        
        return distances
    
    def check_paths_clear_gpu(self, paths, current_radius):
        """
        GPU-accelerated check if multiple paths avoid all mine circles.
        
        Args:
            paths: List of (start, end) tuples
            current_radius: Safety radius around mines
        
        Returns:
            Boolean array indicating which paths are clear
        """
        if len(paths) == 0:
            return []
        
        # Prepare path data
        starts = torch.tensor([p[0] for p in paths], dtype=torch.float32, device=self.device)
        ends = torch.tensor([p[1] for p in paths], dtype=torch.float32, device=self.device)
        
        # Compute all distances at once on GPU
        distances = self.batch_point_to_line_distance_gpu(self.mines_torch, starts, ends)
        
        # Check if all mines are far enough from each path
        min_distances = torch.min(distances, dim=0)[0]  # Min distance for each path
        clear = (min_distances >= current_radius).cpu().numpy()
        
        return clear
    
    def generate_waypoints_gpu(self, current_radius, num_angles=16):
        """
        GPU-accelerated generation of waypoints around mine perimeters.
        """
        # Generate angles
        angles = torch.linspace(0, 2*np.pi, num_angles, device=self.device, dtype=torch.float32)
        angles = angles[:-1]  # Remove duplicate 0/2π
        
        # Broadcast computation for all mines and angles
        mines_expanded = self.mines_torch.unsqueeze(1)  # (N, 1, 2)
        angles_expanded = angles.unsqueeze(0)  # (1, A)
        
        # Compute waypoints
        cos_angles = torch.cos(angles_expanded)
        sin_angles = torch.sin(angles_expanded)
        
        waypoints_x = mines_expanded[:, :, 0] + current_radius * cos_angles  # (N, A)
        waypoints_y = mines_expanded[:, :, 1] + current_radius * sin_angles  # (N, A)
        
        waypoints = torch.stack([waypoints_x, waypoints_y], dim=2)  # (N, A, 2)
        waypoints = waypoints.reshape(-1, 2)  # (N*A, 2)
        
        # Filter waypoints within bounds
        mask = (waypoints[:, 0] >= 0) & (waypoints[:, 0] <= self.width) & \
               (waypoints[:, 1] >= 0) & (waypoints[:, 1] <= self.height)
        
        valid_waypoints = waypoints[mask].cpu().numpy()
        
        # Reduce number of waypoints if too many (for memory efficiency)
        if len(valid_waypoints) > 500:
            indices = np.random.choice(len(valid_waypoints), 500, replace=False)
            valid_waypoints = valid_waypoints[indices]
        
        return valid_waypoints
    
    def build_graph_gpu(self, points, current_radius):
        """
        GPU-accelerated graph construction with path validity checking.
        """
        n_points = len(points)
        
        # Batch size for GPU memory efficiency
        batch_size = 1000
        graph = {i: [] for i in range(n_points)}
        
        # Process in batches to avoid GPU memory overflow
        for i_start in range(0, n_points, batch_size):
            i_end = min(i_start + batch_size, n_points)
            
            for j_start in range(i_start, n_points, batch_size):
                j_end = min(j_start + batch_size, n_points)
                
                # Create all pairs in this batch
                paths = []
                indices = []
                
                for i in range(i_start, i_end):
                    for j in range(max(j_start, i + 1), j_end):
                        paths.append((points[i], points[j]))
                        indices.append((i, j))
                
                if len(paths) > 0:
                    # Check all paths in batch on GPU
                    clear = self.check_paths_clear_gpu(paths, current_radius)
                    
                    # Add edges for clear paths
                    for (i, j), is_clear in zip(indices, clear):
                        if is_clear:
                            dist = distance.euclidean(points[i], points[j])
                            graph[i].append((j, dist))
                            graph[j].append((i, dist))
        
        return graph
    
    def find_path_with_radius(self, current_radius):
        """Find shortest path with given mine avoidance radius using GPU acceleration."""
        # Check direct path first
        direct_clear = self.check_paths_clear_gpu([(self.start, self.end)], current_radius)
        if direct_clear[0]:
            return [self.start, self.end], distance.euclidean(self.start, self.end)
        
        # Generate waypoints on GPU
        waypoints = self.generate_waypoints_gpu(current_radius, num_angles=12)
        
        # Build graph with GPU acceleration
        all_points = [self.start] + list(waypoints) + [self.end]
        graph = self.build_graph_gpu(all_points, current_radius)
        
        # A* pathfinding (still on CPU for now)
        path = self.astar(graph, 0, len(all_points) - 1, all_points)
        
        if path:
            path_points = [all_points[i] for i in path]
            total_dist = sum(distance.euclidean(path_points[i], path_points[i+1]) 
                           for i in range(len(path_points) - 1))
            return path_points, total_dist
        
        return None, float('inf')
    
    def astar(self, graph, start, goal, points):
        """A* pathfinding algorithm (CPU implementation)."""
        heap = [(0, start, [start])]
        visited = set()
        
        while heap:
            cost, current, path = heapq.heappop(heap)
            
            if current == goal:
                return path
                
            if current in visited:
                continue
                
            visited.add(current)
            
            for neighbor, edge_cost in graph[current]:
                if neighbor not in visited:
                    g_cost = cost + edge_cost
                    h_cost = distance.euclidean(points[neighbor], points[goal])
                    f_cost = g_cost + h_cost
                    heapq.heappush(heap, (f_cost, neighbor, path + [neighbor]))
        
        return None
    
    def find_optimal_path(self, max_iterations=40):
        """
        GPU-accelerated iterative circle reduction to find optimal path.
        """
        initial_radius = self.mine_buffer * 10
        final_radius = self.mine_buffer
        
        best_path = None
        best_distance = float('inf')
        radius_history = []
        distance_history = []
        gpu_time_total = 0
        
        print(f"Starting GPU-accelerated iterative circle reduction...")
        print(f"Using device: {self.device}")
        print(f"Initial radius: {initial_radius:.2f} ft")
        print(f"Final radius: {final_radius:.2f} ft")
        print(f"Number of mines: {self.num_mines}")
        
        # Warm up GPU
        if self.device.type == 'cuda':
            torch.cuda.synchronize()
        
        for iteration in range(max_iterations):
            progress = iteration / max_iterations
            current_radius = initial_radius * (1 - progress) + final_radius * progress
            
            start_time = time.time()
            
            # Synchronize GPU for accurate timing
            if self.device.type == 'cuda':
                torch.cuda.synchronize()
            
            path, path_distance = self.find_path_with_radius(current_radius)
            
            if self.device.type == 'cuda':
                torch.cuda.synchronize()
            
            elapsed = time.time() - start_time
            gpu_time_total += elapsed
            
            radius_history.append(current_radius)
            distance_history.append(path_distance)
            
            if path and path_distance < best_distance:
                best_path = path
                best_distance = path_distance
                
            print(f"Iteration {iteration+1}: radius={current_radius:.2f}ft, "
                  f"distance={path_distance:.2f}ft, time={elapsed:.3f}s")
        
        print(f"\nTotal GPU computation time: {gpu_time_total:.2f}s")
        
        # Report GPU memory usage
        if self.device.type == 'cuda':
            memory_allocated = torch.cuda.memory_allocated() / 1024**2
            memory_cached = torch.cuda.memory_reserved() / 1024**2
            print(f"GPU Memory - Allocated: {memory_allocated:.1f}MB, Cached: {memory_cached:.1f}MB")
        
        return best_path, best_distance, radius_history, distance_history
    
    def visualize(self, path=None, title="CUDA-Accelerated Tangent Method"):
        """Visualize the minefield and path."""
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Draw minefield boundary
        ax.add_patch(plt.Rectangle((0, 0), self.width, self.height, 
                                  fill=False, edgecolor='black', linewidth=2))
        
        # Draw mines with buffer zones
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
            ax.plot(path_x, path_y, 'g-', linewidth=2, label='Safe Path')
            
            for i, point in enumerate(path[1:-1], 1):
                ax.plot(point[0], point[1], 'yo', markersize=5)
        
        ax.set_xlim(-5, self.width + 5)
        ax.set_ylim(-5, self.height + 5)
        ax.set_aspect('equal')
        ax.set_xlabel('Distance (feet)')
        ax.set_ylabel('Distance (feet)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add GPU info to title
        if self.device.type == 'cuda':
            ax.text(0.5, 1.02, f'GPU: {torch.cuda.get_device_name(0)}', 
                   transform=ax.transAxes, ha='center', fontsize=10, color='green')
        
        return fig

def main():
    # Initialize CUDA-accelerated pathfinder
    pathfinder = TangentPathfinderCUDA(grid_size=(300, 80), num_mines=1000, mine_buffer=3.0)
    
    # Generate minefield
    pathfinder.generate_minefield(seed=42)
    
    # Find optimal path with GPU acceleration
    print("=" * 60)
    print("CUDA-ACCELERATED TANGENT METHOD")
    print("=" * 60)
    
    start_time = time.time()
    path, distance, radius_hist, dist_hist = pathfinder.find_optimal_path(max_iterations=20)
    total_time = time.time() - start_time
    
    print(f"\nResults:")
    print(f"Total computation time: {total_time:.2f} seconds")
    print(f"Optimal path distance: {distance:.2f} feet")
    if path:
        print(f"Number of waypoints: {len(path)}")
    
    # Visualize results
    fig = pathfinder.visualize(path, 
                              title=f"CUDA Tangent Method - Distance: {distance:.2f} ft")
    plt.savefig('tangent_cuda_result.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return pathfinder, path, distance

if __name__ == "__main__":
    main()

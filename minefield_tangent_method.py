"""
Method A: Iterative Circle Reduction with Tangent Paths
Finds shortest safe path through minefield by starting with large safety circles
around mines and iteratively reducing them while finding tangent paths.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance
import time
from collections import deque
import heapq

class TangentPathfinder:
    def __init__(self, grid_size=(300, 80), num_mines=1000, mine_buffer=3.0):
        """
        Initialize the tangent-based pathfinder.
        
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
            
    def find_tangent_points(self, p1, p2, center, radius):
        """Find external tangent points between two circles or point and circle."""
        # If p1 is a point (start/end position)
        if isinstance(p1, tuple):
            dx = center[0] - p1[0]
            dy = center[1] - p1[1]
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist <= radius:
                return []  # Point inside circle
                
            # Calculate tangent points
            angle = np.arctan2(dy, dx)
            tangent_angle = np.arcsin(radius / dist)
            
            tangents = []
            for sign in [-1, 1]:
                t_angle = angle + sign * tangent_angle
                tx = center[0] - radius * np.cos(t_angle)
                ty = center[1] - radius * np.sin(t_angle)
                tangents.append((tx, ty))
            return tangents
        
        # Both are circles - find external tangents
        else:
            c1, r1 = p1
            c2, r2 = center, radius
            
            dx = c2[0] - c1[0]
            dy = c2[1] - c1[1]
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist <= r1 + r2:
                return []  # Circles overlap
                
            tangent_pairs = []
            
            # External tangents
            angle = np.arctan2(dy, dx)
            
            # Common external tangents
            if abs(r1 - r2) < dist:
                alpha = np.arcsin((r2 - r1) / dist)
                for sign in [-1, 1]:
                    t_angle = angle + sign * (np.pi/2 - alpha)
                    
                    # Points on first circle
                    t1x = c1[0] + r1 * np.cos(t_angle)
                    t1y = c1[1] + r1 * np.sin(t_angle)
                    
                    # Points on second circle
                    t2x = c2[0] + r2 * np.cos(t_angle)
                    t2y = c2[1] + r2 * np.sin(t_angle)
                    
                    tangent_pairs.append(((t1x, t1y), (t2x, t2y)))
                    
            return tangent_pairs
    
    def check_path_clear(self, p1, p2, current_radius):
        """Check if a straight path between two points avoids all mine circles."""
        for mine in self.mines:
            # Calculate distance from mine center to line segment
            dist = self.point_to_line_distance(mine, p1, p2)
            if dist < current_radius:
                return False
        return True
    
    def point_to_line_distance(self, point, line_start, line_end):
        """Calculate minimum distance from point to line segment."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Vector from start to end
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
    
    def find_path_with_radius(self, current_radius):
        """Find shortest path with given mine avoidance radius using A* search."""
        # Create graph of tangent connections
        nodes = [self.start, self.end]
        mine_circles = [(mine, current_radius) for mine in self.mines]
        
        # Build visibility graph
        edges = {}
        
        # Check direct path from start to end
        if self.check_path_clear(self.start, self.end, current_radius):
            return [self.start, self.end], distance.euclidean(self.start, self.end)
        
        # Use A* to find shortest path through tangent network
        # Simplified version - in practice would build full tangent graph
        waypoints = []
        
        # Sample points around mine perimeters
        for mine in self.mines:
            for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
                wx = mine[0] + current_radius * np.cos(angle)
                wy = mine[1] + current_radius * np.sin(angle)
                if 0 <= wx <= self.width and 0 <= wy <= self.height:
                    waypoints.append((wx, wy))
        
        # A* search
        all_points = [self.start] + waypoints + [self.end]
        
        # Build adjacency list
        graph = {i: [] for i in range(len(all_points))}
        
        for i in range(len(all_points)):
            for j in range(i + 1, len(all_points)):
                if self.check_path_clear(all_points[i], all_points[j], current_radius):
                    dist = distance.euclidean(all_points[i], all_points[j])
                    graph[i].append((j, dist))
                    graph[j].append((i, dist))
        
        # A* pathfinding
        path = self.astar(graph, 0, len(all_points) - 1, all_points)
        
        if path:
            path_points = [all_points[i] for i in path]
            total_dist = sum(distance.euclidean(path_points[i], path_points[i+1]) 
                           for i in range(len(path_points) - 1))
            return path_points, total_dist
        
        return None, float('inf')
    
    def astar(self, graph, start, goal, points):
        """A* pathfinding algorithm."""
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
    
    def find_optimal_path(self, max_iterations=20):
        """
        Iteratively reduce circle sizes to find optimal path.
        Start with large circles and gradually reduce them.
        """
        # Start with circles 3x the minimum buffer
        initial_radius = self.mine_buffer * 3
        final_radius = self.mine_buffer
        
        best_path = None
        best_distance = float('inf')
        radius_history = []
        distance_history = []
        
        print(f"Starting iterative circle reduction...")
        print(f"Initial radius: {initial_radius:.2f} ft")
        print(f"Final radius: {final_radius:.2f} ft")
        print(f"Number of mines: {self.num_mines}")
        
        for iteration in range(max_iterations):
            # Exponential decay of radius
            progress = iteration / max_iterations
            current_radius = initial_radius * (1 - progress) + final_radius * progress
            
            start_time = time.time()
            path, path_distance = self.find_path_with_radius(current_radius)
            elapsed = time.time() - start_time
            
            radius_history.append(current_radius)
            distance_history.append(path_distance)
            
            if path and path_distance < best_distance:
                best_path = path
                best_distance = path_distance
                
            print(f"Iteration {iteration+1}: radius={current_radius:.2f}ft, "
                  f"distance={path_distance:.2f}ft, time={elapsed:.3f}s")
        
        return best_path, best_distance, radius_history, distance_history
    
    def visualize(self, path=None, title="Tangent Method Pathfinding"):
        """Visualize the minefield and path."""
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Draw minefield boundary
        ax.add_patch(plt.Rectangle((0, 0), self.width, self.height, 
                                  fill=False, edgecolor='black', linewidth=2))
        
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
            ax.plot(path_x, path_y, 'g-', linewidth=2, label='Safe Path')
            
            # Draw waypoints
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
        
        return fig

def main():
    # Initialize pathfinder with IARC arena dimensions
    pathfinder = TangentPathfinder(grid_size=(300, 80), num_mines=1000, mine_buffer=3.0)
    
    # Generate minefield
    pathfinder.generate_minefield(seed=42)
    
    # Find optimal path
    print("=" * 60)
    print("TANGENT METHOD - Iterative Circle Reduction")
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
    fig = pathfinder.visualize(path, title=f"Tangent Method - Distance: {distance:.2f} ft")
    plt.savefig('tangent_method_result.png', dpi=150, bbox_inches='tight')
    
    # Plot convergence
    fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    ax1.plot(radius_hist, 'b-')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Circle Radius (ft)')
    ax1.set_title('Circle Radius Reduction')
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(dist_hist, 'r-')
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Path Distance (ft)')
    ax2.set_title('Path Distance Evolution')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('tangent_convergence.png', dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return pathfinder, path, distance

if __name__ == "__main__":
    main()
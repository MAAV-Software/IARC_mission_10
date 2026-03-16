"""
Voronoi Pathfinder for SVG Minefield
Extracts coordinates from the provided SVG grid and calculates a safe path
using Voronoi diagrams and A* search.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, distance
import heapq
import time

class SVGVoronoiPathfinder:
    def __init__(self, mine_buffer=1.0):
        # Grid derived from SVG axes
        self.width = 40
        self.height = 150
        self.mine_buffer = mine_buffer
        
        # Start and end points based on the green/blue entry zones in the SVG
        self.start = (27, 0)
        self.end = (28, 150)
        
        # Raw pixel data from the red rects in the SVG
        raw_red_rects = [
            (360, 1490), (390, 1490), (240, 1480), (220, 1470), (70, 1460), (150, 1460),
            (380, 1410), (390, 1390), (370, 1380), (340, 1370), (400, 1360), (80, 1350),
            (200, 1350), (50, 1340), (420, 1330), (290, 1310), (170, 1300), (170, 1290),
            (370, 1280), (260, 1260), (330, 1260), (410, 1260), (60, 1240), (190, 1240),
            (240, 1210), (260, 1210), (30, 1180), (410, 1180), (190, 1160), (50, 1130),
            (420, 1120), (380, 1090), (100, 1080), (200, 1080), (340, 1080), (150, 1070),
            (340, 1070), (410, 1070), (100, 1060), (210, 1060), (240, 1060), (250, 1060),
            (320, 1050), (190, 1040), (360, 1040), (50, 1030), (120, 1030), (190, 1030),
            (230, 1030), (240, 1030), (220, 1020), (380, 1020), (400, 1020), (50, 1010),
            (60, 1010), (190, 1010), (290, 1010), (260, 1000), (330, 1000), (150, 990),
            (110, 980), (260, 970), (310, 970), (280, 950), (30, 940), (120, 940),
            (250, 940), (390, 940), (410, 940), (90, 930), (130, 930), (170, 930),
            (210, 930), (290, 930), (320, 930), (80, 920), (160, 920), (210, 920),
            (220, 920), (260, 920), (210, 910), (250, 910), (370, 910), (50, 900),
            (110, 900), (120, 900), (410, 900), (170, 890), (330, 890), (270, 880),
            (380, 870), (80, 860), (100, 850), (160, 850), (360, 850), (30, 840),
            (200, 840), (300, 820), (60, 810), (160, 800), (40, 780), (410, 780),
            (110, 760), (160, 760), (350, 760), (190, 750), (350, 750), (260, 730),
            (160, 720), (160, 710), (270, 710), (200, 700), (250, 700), (30, 680),
            (90, 680), (220, 680), (80, 670), (50, 590), (140, 590), (300, 580),
            (290, 520), (40, 500), (100, 400), (400, 400), (200, 370), (390, 300),
            (270, 270), (310, 270), (210, 230), (240, 210), (350, 150), (260, 110),
            (420, 90), (100, 60), (380, 30)
        ]
        
        # Convert pixel coordinates to grid coordinates based on SVG axes
        # X: 30px -> 0, 80px -> 5  =>  data_x = (px - 30) / 10
        # Y: 1500px -> 0, 1450px -> 5 => data_y = (1500 - py) / 10
        self.mines = [((x - 30)/10.0, (1500 - y)/10.0) for x, y in raw_red_rects]
        self.vor = None
        self.graph_nodes = set()
        
    def point_to_line_dist(self, point, line_start, line_end):
        """Calculate minimum distance from a point to a line segment."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return np.sqrt((x0 - x1)**2 + (y0 - y1)**2)
            
        t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx**2 + dy**2)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return np.sqrt((x0 - closest_x)**2 + (y0 - closest_y)**2)
        
    def check_path_clear(self, p1, p2):
        """Check if segment strictly respects the mine buffer."""
        for mine in self.mines:
            if self.point_to_line_dist(mine, p1, p2) < self.mine_buffer:
                return False
        return True

    def build_voronoi_graph(self):
        """Builds graph from Voronoi edges that are far enough from mines."""
        print("Building Voronoi graph...")
        # Add dummy points far outside the boundary to close open Voronoi regions
        dummy_points = [
            (-100, -100), (self.width+100, -100),
            (-100, self.height+100), (self.width+100, self.height+100)
        ]
        all_points = self.mines + dummy_points
        self.vor = Voronoi(all_points)
        
        graph = {}
        
        def is_valid_point(p):
            # Must be within bounds
            if not (0 <= p[0] <= self.width and 0 <= p[1] <= self.height):
                return False
            # Must be safe distance from all mines
            min_dist = min(distance.euclidean(p, m) for m in self.mines)
            if min_dist < self.mine_buffer:
                return False
            return True

        # Extract valid edges
        for v1_idx, v2_idx in self.vor.ridge_vertices:
            if v1_idx == -1 or v2_idx == -1:
                continue
                
            p1 = tuple(self.vor.vertices[v1_idx])
            p2 = tuple(self.vor.vertices[v2_idx])
            
            # If both points are valid, and the path between them is safe
            if is_valid_point(p1) and is_valid_point(p2) and self.check_path_clear(p1, p2):
                dist = distance.euclidean(p1, p2)
                if p1 not in graph: graph[p1] = []
                if p2 not in graph: graph[p2] = []
                
                graph[p1].append((p2, dist))
                graph[p2].append((p1, dist))
                self.graph_nodes.add(p1)
                self.graph_nodes.add(p2)
                
        # Connect Start and End to the graph safely
        for target in [self.start, self.end]:
            graph[target] = []
            # Sort valid nodes by proximity
            sorted_nodes = sorted(list(self.graph_nodes), key=lambda n: distance.euclidean(target, n))
            
            connections = 0
            for node in sorted_nodes:
                if self.check_path_clear(target, node):
                    dist = distance.euclidean(target, node)
                    graph[target].append((node, dist))
                    graph[node].append((target, dist))
                    connections += 1
                    # Connect to up to 5 safe nearby nodes to ensure graph entry
                    if connections >= 5: 
                        break
                        
        return graph

    def astar(self, graph):
        """Standard A* search algorithm."""
        print("Running A* search...")
        heap = [(0, self.start, [self.start])]
        visited = set()
        
        while heap:
            cost, current, path = heapq.heappop(heap)
            
            if distance.euclidean(current, self.end) < 0.1:  # Reached end
                return path
                
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor, edge_cost in graph.get(current, []):
                if neighbor not in visited:
                    g_cost = cost + edge_cost
                    h_cost = distance.euclidean(neighbor, self.end)
                    f_cost = g_cost + h_cost
                    heapq.heappush(heap, (f_cost, neighbor, path + [neighbor]))
        
        return None

    def visualize(self, path=None, exec_time=0):
        """Plot the arena, mines, Voronoi network, and final path."""
        fig, ax = plt.subplots(figsize=(6, 12))
        ax.set_title(f"SVG Minefield - Voronoi Method\nCompute Time: {exec_time:.3f}s", fontweight='bold')
        
        # Bounding box
        ax.add_patch(plt.Rectangle((0, 0), self.width, self.height, 
                                  fill=False, edgecolor='black', linewidth=2))
        
        # Draw Voronoi edges
        if self.vor:
            for v1_idx, v2_idx in self.vor.ridge_vertices:
                if v1_idx != -1 and v2_idx != -1:
                    p1 = self.vor.vertices[v1_idx]
                    p2 = self.vor.vertices[v2_idx]
                    if (0 <= p1[0] <= self.width and 0 <= p1[1] <= self.height and
                        0 <= p2[0] <= self.width and 0 <= p2[1] <= self.height):
                        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'c-', alpha=0.3, linewidth=0.5)

        # Draw Mines
        for mine in self.mines:
            ax.plot(mine[0], mine[1], 'r^', markersize=6, zorder=3)
            # Safe Buffer
            circle = plt.Circle(mine, self.mine_buffer, fill=False, 
                              edgecolor='red', alpha=0.4, linestyle='--', linewidth=1)
            ax.add_patch(circle)
            
        # Draw Start / End
        ax.plot(self.start[0], self.start[1], 'go', markersize=12, label='Start', zorder=5)
        ax.plot(self.end[0], self.end[1], 'bo', markersize=12, label='End', zorder=5)
        
        # Draw Path
        if path:
            path_x = [p[0] for p in path]
            path_y = [p[1] for p in path]
            
            # Calculate total length
            length = sum(distance.euclidean(path[i], path[i+1]) for i in range(len(path)-1))
            
            ax.plot(path_x, path_y, 'm-', linewidth=3, label=f'Safe Path: {length:.1f} units', zorder=10)
            for point in path[1:-1]:
                ax.plot(point[0], point[1], 'mo', markersize=4, zorder=11)
        else:
            ax.text(self.width/2, self.height/2, 'NO PATH FOUND', 
                   ha='center', va='center', fontsize=16, color='red', fontweight='bold')

        ax.set_xlim(-5, self.width + 5)
        ax.set_ylim(-5, self.height + 5)
        ax.set_aspect('equal')
        ax.set_xlabel('Distance (units)')
        ax.set_ylabel('Distance (units)')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('voronoi_svg_result.png', dpi=150, bbox_inches='tight')
        print(f"Plot saved as 'voronoi_svg_result.png'")
        plt.show()

def main():
    print("=" * 60)
    print(" VORONOI METHOD ON CUSTOM SVG COORDINATES ")
    print("=" * 60)
    
    # 1.0 buffer equates to 10 pixels on the SVG, perfectly matching your rect sizes.
    pathfinder = SVGVoronoiPathfinder(mine_buffer=1.0)
    
    start_time = time.time()
    graph = pathfinder.build_voronoi_graph()
    path = pathfinder.astar(graph)
    total_time = time.time() - start_time
    
    if path:
        print(f"\nSUCCESS! Found safe path with {len(path)} waypoints.")
    else:
        print("\nFAILED: No continuous safe path found connecting start and end.")
        
    pathfinder.visualize(path, exec_time=total_time)

if __name__ == "__main__":
    main()
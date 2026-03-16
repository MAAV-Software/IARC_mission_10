#!/usr/bin/env python3
"""
Enhanced Visualization for IARC Mission 10 Pathfinding
Shows:
- Tangent method: Circles at successful radius
- Voronoi method: Voronoi diagram edges
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from matplotlib.collections import LineCollection
import sys
import os

def load_enhanced_tangent_results(filename):
    """Load tangent results including successful radius"""
    mines = []
    path = []
    metrics = {}
    
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return np.array([]), np.array([]), {}
    
    mode = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line == 'MINES':
                mode = 'mines'
            elif line == 'PATH':
                mode = 'path'
            elif line == 'METRICS':
                mode = 'metrics'
            elif mode == 'mines' and ',' in line:
                x, y = map(float, line.split(','))
                mines.append((x, y))
            elif mode == 'path' and ',' in line:
                x, y = map(float, line.split(','))
                path.append((x, y))
            elif mode == 'metrics' and ',' in line:
                key, value = line.split(',')
                metrics[key] = float(value)
    
    return np.array(mines), np.array(path), metrics

def load_enhanced_voronoi_results(filename):
    """Load voronoi results including edges"""
    mines = []
    path = []
    voronoi_edges = []
    metrics = {}
    
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return np.array([]), np.array([]), [], {}
    
    mode = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line == 'MINES':
                mode = 'mines'
            elif line == 'PATH':
                mode = 'path'
            elif line == 'VORONOI_EDGES':
                mode = 'voronoi'
            elif line == 'METRICS':
                mode = 'metrics'
            elif mode == 'mines' and ',' in line:
                x, y = map(float, line.split(','))
                mines.append((x, y))
            elif mode == 'path' and ',' in line:
                x, y = map(float, line.split(','))
                path.append((x, y))
            elif mode == 'voronoi' and ',' in line:
                coords = list(map(float, line.split(',')))
                if len(coords) == 4:
                    voronoi_edges.append([(coords[0], coords[1]), (coords[2], coords[3])])
            elif mode == 'metrics' and ',' in line:
                key, value = line.split(',')
                metrics[key] = float(value)
    
    return np.array(mines), np.array(path), voronoi_edges, metrics

def plot_tangent_with_circles(ax, mines, path, metrics, buffer_radius=3.0):
    """Plot tangent method with circles at successful radius"""
    
    # Get the successful radius
    successful_radius = metrics.get('successful_radius', buffer_radius)
    
    # Plot circles at successful radius (lighter color)
    for mine in mines:
        circle_success = Circle((mine[0], mine[1]), successful_radius, 
                                color='orange', alpha=0.15, fill=True, 
                                edgecolor='orange', linewidth=0.5, linestyle='--',
                                label='Successful radius' if mine is mines[0] else '')
        ax.add_patch(circle_success)
    
    # Plot minimum buffer zones (darker red)
    for mine in mines:
        circle_buffer = Circle((mine[0], mine[1]), buffer_radius, 
                              color='red', alpha=0.25, fill=True,
                              edgecolor='red', linewidth=1,
                              label='Minimum buffer' if mine is mines[0] else '')
        ax.add_patch(circle_buffer)
    
    # Plot mines
    if len(mines) > 0:
        ax.scatter(mines[:, 0], mines[:, 1], c='red', s=40, 
                  alpha=1.0, label='Mines', zorder=5, edgecolors='darkred', linewidth=1)
    
    # Plot path
    if len(path) > 0:
        # Draw path with arrows
        ax.plot(path[:, 0], path[:, 1], 'b-', linewidth=2.5, 
               label='Path', zorder=4, alpha=0.8)
        
        # Add arrows to show direction
        for i in range(0, len(path)-1, max(1, len(path)//5)):
            dx = path[i+1, 0] - path[i, 0]
            dy = path[i+1, 1] - path[i, 1]
            ax.arrow(path[i, 0], path[i, 1], dx*0.3, dy*0.3, 
                    head_width=2, head_length=1.5, fc='blue', ec='blue', 
                    alpha=0.6, zorder=4)
        
        ax.plot(path[0, 0], path[0, 1], 'go', markersize=12, 
               label='Start', zorder=6)
        ax.plot(path[-1, 0], path[-1, 1], 'mo', markersize=12, 
               label='End', zorder=6)
        
        # Add waypoints
        for i, point in enumerate(path[1:-1]):
            ax.plot(point[0], point[1], 'b.', markersize=8, zorder=4)
    
    # Set title with metrics
    path_length = metrics.get('path_length', 0)
    comp_time = metrics.get('computation_time_ms', 0)
    ax.set_title(f"Tangent Circle Reduction\n" + 
                f"Radius: {successful_radius:.1f} ft | " +
                f"Length: {path_length:.1f} ft | Time: {comp_time:.1f} ms",
                fontsize=11, fontweight='bold')
    
    ax.set_xlabel('X (feet)', fontsize=10)
    ax.set_ylabel('Y (feet)', fontsize=10)
    
    # Custom legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(-5, 305)
    ax.set_ylim(-5, 85)
    ax.set_aspect('equal', adjustable='box')

def plot_voronoi_with_diagram(ax, mines, path, voronoi_edges, metrics, buffer_radius=3.0):
    """Plot Voronoi method with Voronoi diagram edges"""
    
    # Plot Voronoi edges first (in background)
    if voronoi_edges:
        edge_collection = LineCollection(voronoi_edges, colors='gray', 
                                        linewidths=0.5, alpha=0.4, 
                                        linestyle='-', label='Voronoi edges')
        ax.add_collection(edge_collection)
    
    # Plot mine buffer zones (light red circles)
    for mine in mines:
        circle = Circle((mine[0], mine[1]), buffer_radius, 
                       color='red', alpha=0.15, fill=True,
                       edgecolor='red', linewidth=0.5)
        ax.add_patch(circle)
    
    # Plot mines
    if len(mines) > 0:
        ax.scatter(mines[:, 0], mines[:, 1], c='red', s=40, 
                  alpha=1.0, label='Mines', zorder=5, edgecolors='darkred', linewidth=1)
    
    # Plot path
    if len(path) > 0:
        # Draw path with thicker line
        ax.plot(path[:, 0], path[:, 1], 'b-', linewidth=3, 
               label='Optimal path', zorder=4, alpha=0.9)
        
        # Add arrows to show direction
        for i in range(0, len(path)-1, max(1, len(path)//5)):
            dx = path[i+1, 0] - path[i, 0]
            dy = path[i+1, 1] - path[i, 1]
            ax.arrow(path[i, 0], path[i, 1], dx*0.3, dy*0.3, 
                    head_width=2, head_length=1.5, fc='blue', ec='blue', 
                    alpha=0.6, zorder=4)
        
        ax.plot(path[0, 0], path[0, 1], 'go', markersize=12, 
               label='Start', zorder=6)
        ax.plot(path[-1, 0], path[-1, 1], 'mo', markersize=12, 
               label='End', zorder=6)
        
        # Add waypoints
        for i, point in enumerate(path[1:-1]):
            ax.plot(point[0], point[1], 'b.', markersize=8, zorder=4)
    
    # Set title with metrics
    path_length = metrics.get('path_length', 0)
    comp_time = metrics.get('computation_time_ms', 0)
    ax.set_title(f"Voronoi Diagram Method\n" +
                f"Edges: {len(voronoi_edges)} | " +
                f"Length: {path_length:.1f} ft | Time: {comp_time:.1f} ms",
                fontsize=11, fontweight='bold')
    
    ax.set_xlabel('X (feet)', fontsize=10)
    ax.set_ylabel('Y (feet)', fontsize=10)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(-5, 305)
    ax.set_ylim(-5, 85)
    ax.set_aspect('equal', adjustable='box')

def calculate_iarc_score(path_length, comp_time_ms, buffer=3.0, missed_mines=0, weight_penalty=0):
    """Calculate IARC Mission 10 score"""
    A = (comp_time_ms / 1000.0) / 60.0  # Convert to minutes
    B = missed_mines
    L = path_length
    W = buffer
    N = weight_penalty
    
    if L == 0:
        return 0
    
    score = (150000 * W) / ((1 + B) * L * (1 + 7*A + 100*N))
    return score

def main():
    print("=" * 80)
    print(" ENHANCED IARC MISSION 10 - PATHFINDING VISUALIZATION")
    print("=" * 80)
    
    # Load results
    mines_t, path_t, metrics_t = load_enhanced_tangent_results('tangent_enhanced.txt')
    mines_v, path_v, edges_v, metrics_v = load_enhanced_voronoi_results('voronoi_enhanced.txt')
    
    if len(mines_t) == 0 and len(mines_v) == 0:
        print("\nNo results found. Please run the C++ program first:")
        print("  g++ -O3 minefield_enhanced_viz.cpp -lCGAL -lgmp -o enhanced_viz")
        print("  ./enhanced_viz")
        sys.exit(1)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(18, 10))
    
    # Create main comparison plots
    ax1 = plt.subplot(2, 2, 1)
    ax2 = plt.subplot(2, 2, 2)
    
    # Plot both methods with enhanced visualization
    plot_tangent_with_circles(ax1, mines_t, path_t, metrics_t)
    plot_voronoi_with_diagram(ax2, mines_v, path_v, edges_v, metrics_v)
    
    # Create comparison metrics subplot
    ax3 = plt.subplot(2, 1, 2)
    ax3.axis('off')
    
    # Calculate scores
    score_t = calculate_iarc_score(
        metrics_t.get('path_length', 0),
        metrics_t.get('computation_time_ms', 0)
    )
    score_v = calculate_iarc_score(
        metrics_v.get('path_length', 0),
        metrics_v.get('computation_time_ms', 0)
    )
    
    # Create detailed comparison table
    comparison_text = f"""
    {'='*80}
    ENHANCED COMPARISON METRICS
    {'='*80}
    
    {'Metric':<30} {'Tangent Method':<25} {'Voronoi Method':<25} {'Winner':<15}
    {'-'*80}
    {'Path Length (ft)':<30} {metrics_t.get('path_length', 0):<25.1f} {metrics_v.get('path_length', 0):<25.1f} {'Tangent' if metrics_t.get('path_length', 0) < metrics_v.get('path_length', 0) else 'Voronoi':<15}
    {'Computation Time (ms)':<30} {metrics_t.get('computation_time_ms', 0):<25.1f} {metrics_v.get('computation_time_ms', 0):<25.1f} {'Tangent' if metrics_t.get('computation_time_ms', 0) < metrics_v.get('computation_time_ms', 0) else 'Voronoi':<15}
    {'IARC Score':<30} {score_t:<25.0f} {score_v:<25.0f} {'Tangent' if score_t > score_v else 'Voronoi':<15}
    {'-'*80}
    
    VISUALIZATION DETAILS:
    • Tangent Method: Shows circles at radius {metrics_t.get('successful_radius', 3.0):.1f} ft (orange) where path was found
    • Voronoi Method: Shows {len(edges_v)} Voronoi edges (gray lines) forming the navigation mesh
    • Red circles: Minimum safety buffer (3 ft) around each mine
    • Blue arrows: Direction of travel along the path
    
    🏆 OVERALL WINNER: {'TANGENT METHOD' if score_t > score_v else 'VORONOI METHOD'} (Higher IARC Score)
    
    Note: IARC Score = (150000 × W) / [(1 + B) × L × (1 + 7A + 100N)]
    Where: W=buffer width, B=missed mines, L=path length, A=time (min), N=weight penalty
    """
    
    ax3.text(0.5, 0.5, comparison_text, transform=ax3.transAxes,
            fontsize=10, verticalalignment='center',
            horizontalalignment='center', fontfamily='monospace')
    
    # Add main title
    plt.suptitle('IARC Mission 10 - Enhanced Pathfinding Visualization\nShowing Algorithm-Specific Features', 
                fontsize=14, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save figure
    output_file = 'enhanced_pathfinding_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Enhanced visualization saved to {output_file}")
    
    # Print summary to console
    print("\n" + "="*50)
    print(" RESULTS SUMMARY")
    print("="*50)
    print(f"\nTangent Method:")
    print(f"  Path Length: {metrics_t.get('path_length', 0):.1f} feet")
    print(f"  Computation: {metrics_t.get('computation_time_ms', 0):.1f} ms")
    print(f"  Successful Radius: {metrics_t.get('successful_radius', 3.0):.1f} feet")
    print(f"  IARC Score:  {score_t:.0f}")
    
    print(f"\nVoronoi Method:")
    print(f"  Path Length: {metrics_v.get('path_length', 0):.1f} feet")
    print(f"  Computation: {metrics_v.get('computation_time_ms', 0):.1f} ms")
    print(f"  Voronoi Edges: {len(edges_v)}")
    print(f"  IARC Score:  {score_v:.0f}")
    
    print(f"\n🏆 Winner: {'Tangent' if score_t > score_v else 'Voronoi'} Method")
    
    # Show plot
    plt.show()

if __name__ == "__main__":
    main()

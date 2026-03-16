#!/usr/bin/env python3
"""
Visualization script for IARC Mission 10 Pathfinding Results
Reads output from C++ program and creates comparison plots
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
import sys
import os

def load_results(filename):
    """Load results from C++ output file"""
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

def plot_minefield(ax, mines, path, metrics, title, buffer_radius=3.0):
    """Plot minefield with path and mine buffers"""
    
    # Plot mine buffer zones (light red circles)
    for mine in mines:
        circle = Circle((mine[0], mine[1]), buffer_radius, 
                       color='red', alpha=0.1, fill=True)
        ax.add_patch(circle)
    
    # Plot mines
    if len(mines) > 0:
        ax.scatter(mines[:, 0], mines[:, 1], c='red', s=30, 
                  alpha=0.8, label='Mines', zorder=3)
    
    # Plot path
    if len(path) > 0:
        ax.plot(path[:, 0], path[:, 1], 'b-', linewidth=2.5, 
               label='Path', zorder=4, alpha=0.8)
        ax.plot(path[0, 0], path[0, 1], 'go', markersize=12, 
               label='Start', zorder=5)
        ax.plot(path[-1, 0], path[-1, 1], 'mo', markersize=12, 
               label='End', zorder=5)
        
        # Add waypoints
        for i, point in enumerate(path[1:-1]):
            ax.plot(point[0], point[1], 'b.', markersize=6, zorder=4)
    
    # Set title with metrics
    path_length = metrics.get('path_length', 0)
    comp_time = metrics.get('computation_time_ms', 0)
    ax.set_title(f"{title}\nLength: {path_length:.1f} ft | Time: {comp_time:.1f} ms",
                fontsize=11, fontweight='bold')
    
    ax.set_xlabel('X (feet)', fontsize=10)
    ax.set_ylabel('Y (feet)', fontsize=10)
    ax.legend(loc='upper right', fontsize=9)
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
    print(" IARC MISSION 10 - PATHFINDING RESULTS VISUALIZATION")
    print("=" * 80)
    
    # Load results
    mines_t, path_t, metrics_t = load_results('tangent_results.txt')
    mines_v, path_v, metrics_v = load_results('voronoi_results.txt')
    
    if len(mines_t) == 0 and len(mines_v) == 0:
        print("\nNo results found. Please run the C++ program first:")
        print("  ./minefield_comparison")
        sys.exit(1)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create main comparison plots
    ax1 = plt.subplot(2, 2, 1)
    ax2 = plt.subplot(2, 2, 2)
    
    # Plot both methods
    plot_minefield(ax1, mines_t, path_t, metrics_t, "Method A: Tangent Circle Reduction")
    plot_minefield(ax2, mines_v, path_v, metrics_v, "Method B: Voronoi Diagram")
    
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
    
    # Create comparison table
    comparison_text = f"""
    {'='*70}
    COMPARISON METRICS
    {'='*70}
    
    {'Metric':<25} {'Tangent Method':<20} {'Voronoi Method':<20} {'Winner':<15}
    {'-'*70}
    {'Path Length (ft)':<25} {metrics_t.get('path_length', 0):<20.1f} {metrics_v.get('path_length', 0):<20.1f} {'Tangent' if metrics_t.get('path_length', 0) < metrics_v.get('path_length', 0) else 'Voronoi':<15}
    {'Computation Time (ms)':<25} {metrics_t.get('computation_time_ms', 0):<20.1f} {metrics_v.get('computation_time_ms', 0):<20.1f} {'Tangent' if metrics_t.get('computation_time_ms', 0) < metrics_v.get('computation_time_ms', 0) else 'Voronoi':<15}
    {'IARC Score':<25} {score_t:<20.0f} {score_v:<20.0f} {'Tangent' if score_t > score_v else 'Voronoi':<15}
    {'-'*70}
    
    🏆 OVERALL WINNER: {'TANGENT METHOD' if score_t > score_v else 'VORONOI METHOD'} (Higher IARC Score)
    
    Note: IARC Score = (150000 × W) / [(1 + B) × L × (1 + 7A + 100N)]
    Where: W=buffer width, B=missed mines, L=path length, A=time (min), N=weight penalty
    """
    
    ax3.text(0.5, 0.5, comparison_text, transform=ax3.transAxes,
            fontsize=11, verticalalignment='center',
            horizontalalignment='center', fontfamily='monospace')
    
    # Add main title
    plt.suptitle('IARC Mission 10 - Minefield Pathfinding Comparison\nC++ Implementation Results', 
                fontsize=14, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save figure
    output_file = 'pathfinding_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Visualization saved to {output_file}")
    
    # Print summary to console
    print("\n" + "="*50)
    print(" RESULTS SUMMARY")
    print("="*50)
    print(f"\nTangent Method:")
    print(f"  Path Length: {metrics_t.get('path_length', 0):.1f} feet")
    print(f"  Computation: {metrics_t.get('computation_time_ms', 0):.1f} ms")
    print(f"  IARC Score:  {score_t:.0f}")
    
    print(f"\nVoronoi Method:")
    print(f"  Path Length: {metrics_v.get('path_length', 0):.1f} feet")
    print(f"  Computation: {metrics_v.get('computation_time_ms', 0):.1f} ms")
    print(f"  IARC Score:  {score_v:.0f}")
    
    print(f"\n🏆 Winner: {'Tangent' if score_t > score_v else 'Voronoi'} Method")
    
    # Show plot
    plt.show()

if __name__ == "__main__":
    main()

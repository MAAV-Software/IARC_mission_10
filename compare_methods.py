"""
Fixed version with proper mine buffers for both methods and timing displays
"""

import numpy as np
import matplotlib.pyplot as plt
import torch
import time
from scipy.spatial import Voronoi
from minefield_tangent_cuda import TangentPathfinderCUDA
from minefield_voronoi_cuda import VoronoiPathfinderCUDA

def calculate_iarc_score(path, time_minutes, missed_mines=0, weight_penalty=0):
    """Calculate IARC Mission 10 Score"""
    if path is None or len(path) < 2:
        return 0, float('inf'), 0
    
    L = sum(np.linalg.norm(np.array(path[i+1]) - np.array(path[i])) 
            for i in range(len(path)-1))
    W = 3.0  # 3-foot safety buffer per IARC rules
    A = time_minutes
    B = missed_mines
    N = weight_penalty
    
    if L == 0 or L == float('inf'):
        return 0, L, W
    
    score = (150000 * W) / ((1 + B) * L * (1 + 7*A + 100*N))
    return score, L, W

def run_comparison_with_timing(num_mines=30, max_iterations=25):
    """
    Run comparison with proper mine buffers and timing display
    """
    
    print("=" * 80)
    print(" IARC MISSION 10 - MINEFIELD PATHFINDING ")
    print("=" * 80)
    
    grid_size = (80,300)  # Square arena
    mine_buffer = 3.0  # IARC requires 1-foot minimum, using 3-foot for safety
    
    print(f"Configuration:")
    print(f"  Arena: {grid_size[0]} x {grid_size[1]} feet")
    print(f"  Mines: {num_mines}")
    print(f"  Safety buffer: {mine_buffer} feet (IARC requirement)")
    print(f"  Tangent iterations: {max_iterations}")
    print()
    
    # Initialize
    tangent_finder = TangentPathfinderCUDA(grid_size, num_mines, mine_buffer)
    voronoi_finder = VoronoiPathfinderCUDA(grid_size, num_mines, mine_buffer)
    
    # Set start/end
    tangent_finder.start = (0, grid_size[1]/2)
    tangent_finder.end = (grid_size[0], grid_size[1]/2)
    voronoi_finder.start = (0, grid_size[1]/2)
    voronoi_finder.end = (grid_size[0], grid_size[1]/2)
    
    # Generate identical minefields
    tangent_finder.generate_minefield(seed=42)
    voronoi_finder.generate_minefield(seed=42)
    
    # TANGENT METHOD WITH TIMING
    print(f"Running TANGENT METHOD...")
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    tangent_start = time.time()
    tangent_path, tangent_dist, radius_hist, dist_hist = tangent_finder.find_optimal_path(max_iterations=max_iterations)
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    tangent_time = time.time() - tangent_start
    tangent_score, t_length, t_width = calculate_iarc_score(tangent_path, tangent_time/60)
    print(f"  Computation time: {tangent_time:.3f} seconds")
    print(f"  Path found: {'Yes' if tangent_path else 'No'}")
    
    # VORONOI METHOD WITH TIMING
    print(f"\nRunning VORONOI METHOD...")
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    voronoi_start = time.time()
    voronoi_path, voronoi_dist, voronoi_detailed_time = voronoi_finder.find_optimal_path()
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    voronoi_time = time.time() - voronoi_start
    voronoi_score, v_length, v_width = calculate_iarc_score(voronoi_path, voronoi_time/60)
    print(f"  Computation time: {voronoi_time:.3f} seconds")
    print(f"  Path found: {'Yes' if voronoi_path else 'No'}")
    
    # ============ VISUALIZATION WITH TIMING ============
    fig = plt.figure(figsize=(22, 11))
    
    # TANGENT METHOD
    ax1 = plt.subplot(2, 4, (1, 5))  # Span 2 rows
    ax1.set_title(f'TANGENT METHOD\n{tangent_time:.3f}s computation', 
                  fontsize=13, fontweight='bold', color='green')
    ax1.add_patch(plt.Rectangle((0, 0), grid_size[0], grid_size[1], 
                                fill=False, edgecolor='black', linewidth=2))
    
    # Draw mines WITH SAFETY BUFFERS
    for mine in tangent_finder.mines:
        ax1.plot(mine[0], mine[1], 'r^', markersize=6, zorder=3)
        # IMPORTANT: Show the safety buffer
        circle = plt.Circle(mine, mine_buffer, fill=False, 
                          edgecolor='red', alpha=0.4, linestyle='--', linewidth=1)
        ax1.add_patch(circle)
    
    # Draw path
    ax1.plot(0, grid_size[1]/2, 'go', markersize=14, label='Start', zorder=5)
    ax1.plot(grid_size[0], grid_size[1]/2, 'bo', markersize=14, label='End', zorder=5)
    
    if tangent_path:
        path_x = [p[0] for p in tangent_path]
        path_y = [p[1] for p in tangent_path]
        ax1.plot(path_x, path_y, 'g-', linewidth=3, 
                label=f'Path: {t_length:.1f}ft', zorder=4, alpha=0.8)
        # Show waypoints
        for i in range(1, len(tangent_path)-1):
            ax1.plot(tangent_path[i][0], tangent_path[i][1], 'yo', markersize=4, zorder=4)
    else:
        ax1.text(grid_size[0]/2, grid_size[1]/2, 'NO PATH FOUND', 
                ha='center', va='center', fontsize=16, color='red', fontweight='bold')
    
    ax1.set_xlim(-5, grid_size[0]+5)
    ax1.set_ylim(-5, grid_size[1]+5)
    ax1.set_aspect('equal')
    ax1.set_xlabel('Distance (feet)', fontsize=11)
    ax1.set_ylabel('Distance (feet)', fontsize=11)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # VORONOI METHOD
    ax2 = plt.subplot(2, 4, (2, 6))  # Span 2 rows
    ax2.set_title(f'VORONOI METHOD\n{voronoi_time:.3f}s computation', 
                  fontsize=13, fontweight='bold', color='magenta')
    ax2.add_patch(plt.Rectangle((0, 0), grid_size[0], grid_size[1], 
                                fill=False, edgecolor='black', linewidth=2))
    
    # Draw Voronoi edges (clipped to bounds)
    if voronoi_finder.vor:
        for simplex in voronoi_finder.vor.ridge_vertices:
            simplex = np.asarray(simplex)
            if np.all(simplex >= 0):
                v1 = voronoi_finder.vor.vertices[simplex[0]]
                v2 = voronoi_finder.vor.vertices[simplex[1]]
                # Only show edges within bounds
                if (0 <= v1[0] <= grid_size[0] and 0 <= v1[1] <= grid_size[1] and
                    0 <= v2[0] <= grid_size[0] and 0 <= v2[1] <= grid_size[1]):
                    ax2.plot([v1[0], v2[0]], [v1[1], v2[1]], 'c-', alpha=0.3, linewidth=0.5)
    
    # Draw mines WITH SAFETY BUFFERS (same as tangent)
    for mine in voronoi_finder.mines:
        ax2.plot(mine[0], mine[1], 'r^', markersize=6, zorder=3)
        # IMPORTANT: Show the safety buffer that path must avoid
        circle = plt.Circle(mine, mine_buffer, fill=False, 
                          edgecolor='red', alpha=0.4, linestyle='--', linewidth=1)
        ax2.add_patch(circle)
    
    # Draw path
    ax2.plot(0, grid_size[1]/2, 'go', markersize=14, label='Start', zorder=5)
    ax2.plot(grid_size[0], grid_size[1]/2, 'bo', markersize=14, label='End', zorder=5)
    
    if voronoi_path:
        path_x = [p[0] for p in voronoi_path]
        path_y = [p[1] for p in voronoi_path]
        ax2.plot(path_x, path_y, 'm-', linewidth=3, 
                label=f'Path: {v_length:.1f}ft', zorder=10, alpha=0.8)
        # Show Voronoi waypoints
        for i in range(1, len(voronoi_path)-1):
            ax2.plot(voronoi_path[i][0], voronoi_path[i][1], 'mo', markersize=5, zorder=11)
    else:
        ax2.text(grid_size[0]/2, grid_size[1]/2, 'NO PATH FOUND', 
                ha='center', va='center', fontsize=16, color='red', fontweight='bold')
    
    ax2.set_xlim(-5, grid_size[0]+5)
    ax2.set_ylim(-5, grid_size[1]+5)
    ax2.set_aspect('equal')
    ax2.set_xlabel('Distance (feet)', fontsize=11)
    ax2.set_ylabel('Distance (feet)', fontsize=11)
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # COMPARISON OVERLAY
    ax3 = plt.subplot(2, 4, (3, 7))  # Span 2 rows
    ax3.set_title(f'DIRECT COMPARISON\nSpeedup: {tangent_time/voronoi_time:.1f}x', 
                  fontsize=13, fontweight='bold')
    ax3.add_patch(plt.Rectangle((0, 0), grid_size[0], grid_size[1], 
                                fill=False, edgecolor='black', linewidth=2))
    
    # Mines with buffers (lighter)
    for mine in tangent_finder.mines:
        ax3.plot(mine[0], mine[1], 'r.', markersize=3, alpha=0.3)
        circle = plt.Circle(mine, mine_buffer, fill=False, 
                          edgecolor='red', alpha=0.1, linestyle='-', linewidth=0.3)
        ax3.add_patch(circle)
    
    ax3.plot(0, grid_size[1]/2, 'go', markersize=12, zorder=5)
    ax3.plot(grid_size[0], grid_size[1]/2, 'bo', markersize=12, zorder=5)
    
    # Both paths
    if tangent_path:
        path_x = [p[0] for p in tangent_path]
        path_y = [p[1] for p in tangent_path]
        ax3.plot(path_x, path_y, 'g-', linewidth=2.5, alpha=0.7, 
                label=f'Tangent: {t_length:.1f}ft ({tangent_time:.2f}s)')
    
    if voronoi_path:
        path_x = [p[0] for p in voronoi_path]
        path_y = [p[1] for p in voronoi_path]
        ax3.plot(path_x, path_y, 'm--', linewidth=2.5, alpha=0.7, 
                label=f'Voronoi: {v_length:.1f}ft ({voronoi_time:.2f}s)')
    
    ax3.set_xlim(-5, grid_size[0]+5)
    ax3.set_ylim(-5, grid_size[1]+5)
    ax3.set_aspect('equal')
    ax3.set_xlabel('Distance (feet)', fontsize=11)
    ax3.set_ylabel('Distance (feet)', fontsize=11)
    ax3.legend(loc='best', fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    # METRICS PANEL
    ax4 = plt.subplot(2, 4, 4)
    ax4.set_title('Timing Breakdown', fontsize=12, fontweight='bold')
    methods = ['Tangent', 'Voronoi']
    times = [tangent_time, voronoi_time]
    colors = ['green', 'magenta']
    bars = ax4.bar(methods, times, color=colors, alpha=0.6, edgecolor='black', linewidth=2)
    ax4.set_ylabel('Time (seconds)', fontsize=11)
    for bar, t in zip(bars, times):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{t:.3f}s', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    ax5 = plt.subplot(2, 4, 8)
    ax5.set_title('IARC Competition Scores', fontsize=12, fontweight='bold')
    scores = [tangent_score, voronoi_score]
    bars = ax5.bar(methods, scores, color=colors, alpha=0.6, edgecolor='black', linewidth=2)
    ax5.set_ylabel('Score', fontsize=11)
    for bar, score in zip(bars, scores):
        if score > 0:
            ax5.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{score:.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle(f'IARC Mission 10 - {num_mines} Mines - GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"}', 
                fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'iarc_timed_{num_mines}mines.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # Print detailed results
    print("\n" + "=" * 60)
    print(" RESULTS ")
    print("=" * 60)
    print(f"Tangent Method:")
    print(f"  Time: {tangent_time:.3f}s | Path: {t_length:.1f}ft | Score: {tangent_score:.1f}")
    print(f"Voronoi Method:")
    print(f"  Time: {voronoi_time:.3f}s | Path: {v_length:.1f}ft | Score: {voronoi_score:.1f}")
    print(f"\nSpeedup: {tangent_time/voronoi_time:.2f}x")
    print(f"Winner: {'TANGENT' if tangent_score > voronoi_score else 'VORONOI'}")

if __name__ == "__main__":
    num_mines = 472
    max_iterations = 25
    
    print(f"\n🎮 Running with {num_mines} mines...")
    run_comparison_with_timing(num_mines, max_iterations)
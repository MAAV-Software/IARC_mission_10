"""
Local IARC Mission 10 Minefield Simulator
Generates random minefields on a 40x150 grid (2ft squares, 80ft x 300ft field)
and scores paths using the official IARC scoring formula.

Score = 150000 * W / ( (1+B) * L * (1 + 7*A + 100*N) )

Grid: x=0-39 (columns, left to right), y=0-149 (rows, bottom to top)
Path: S,x,G then U/D/L/R,n commands

Methods:
  voronoi  - Voronoi diagram waypoints + grid A* between them
  astar    - Pure grid A* with mine proximity penalty
  batch    - Compare both methods across many seeds
"""

import numpy as np
import heapq
import time
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from minefield_voronoi_method import VoronoiPathfinder


# -- Grid / field constants ------------------------------------------
COLS = 40        # x: 0-39
ROWS = 150       # y: 0-149
CELL_FT = 2      # each cell is 2x2 feet
FIELD_W = COLS * CELL_FT   # 80 ft
FIELD_H = ROWS * CELL_FT   # 300 ft


# ====================================================================
# Mine generation
# ====================================================================

def generate_minefield(num_mines=135, seed=0.1934):
    """Generate mine positions on the grid, returns set of (x, y) grid coords."""
    rng = np.random.RandomState(int(abs(seed * 1e6)) % (2**31))
    all_cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
    indices = rng.choice(len(all_cells), size=min(num_mines, len(all_cells)), replace=False)
    mines = set(all_cells[i] for i in indices)
    return mines


def build_mine_neighbor_set(mines):
    """Build set of cells adjacent to mines (for proximity penalty)."""
    near_mines = set()
    for (mx, my) in mines:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = mx + dx, my + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in mines:
                near_mines.add((nx, ny))
    return near_mines


# ====================================================================
# Grid A* pathfinder
# ====================================================================

def grid_astar(mines, start, end, proximity_penalty=0.3):
    """
    A* on the 40x150 grid. 4-connected (U/D/L/R).
    Cells in `mines` are blocked. Cells adjacent to mines get a cost penalty.
    Returns list of (x,y) cells from start to end, or None if no path.
    """
    if start in mines or end in mines:
        return None

    near_mines = build_mine_neighbor_set(mines)

    # Priority queue: (f_score, tiebreaker, (x, y))
    open_set = [(0, 0, start)]
    came_from = {}
    g_score = {start: 0}
    counter = 1

    while open_set:
        f, _, current = heapq.heappop(open_set)

        if current == end:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cx, cy = current
        for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
            nx, ny = cx + dx, cy + dy
            neighbor = (nx, ny)

            if not (0 <= nx < COLS and 0 <= ny < ROWS):
                continue
            if neighbor in mines:
                continue

            # Base cost 1 + penalty if near a mine
            move_cost = 1.0
            if neighbor in near_mines:
                move_cost += proximity_penalty

            tentative_g = g_score[current] + move_cost

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                # Manhattan heuristic
                h = abs(nx - end[0]) + abs(ny - end[1])
                heapq.heappush(open_set, (tentative_g + h, counter, neighbor))
                counter += 1

    return None  # No path found


# ====================================================================
# Path utilities
# ====================================================================

def find_safest_column(mines, row):
    """Find the column in a given row that is farthest from any mine."""
    best_col = COLS // 2
    best_dist = -1

    for col in range(COLS):
        if (col, row) in mines:
            continue
        # Minimum distance to any mine (simple grid distance)
        min_d = float('inf')
        for mx, my in mines:
            d = abs(col - mx) + abs(row - my)
            if d < min_d:
                min_d = d
        if min_d > best_dist:
            best_dist = min_d
            best_col = col

    return best_col


def grid_path_to_commands(grid_path, G=0):
    """Convert list of (x,y) grid cells to S,U,D,L,R command string."""
    if not grid_path:
        return ""

    start_x, start_y = grid_path[0]
    commands = [f"S,{start_x},{G}"]

    i = 1
    while i < len(grid_path):
        cx, cy = grid_path[i - 1]
        nx, ny = grid_path[i]
        dx, dy = nx - cx, ny - cy

        if dy == 1:
            direction = 'U'
        elif dy == -1:
            direction = 'D'
        elif dx == 1:
            direction = 'R'
        elif dx == -1:
            direction = 'L'
        else:
            i += 1
            continue

        # Count consecutive steps in same direction
        count = 1
        while i + count < len(grid_path):
            px, py = grid_path[i + count - 1]
            qx, qy = grid_path[i + count]
            if (qx - px, qy - py) == (dx, dy):
                count += 1
            else:
                break

        commands.append(f"{direction},{count}")
        i += count

    return '\n'.join(commands)


def compute_green_zone(path_cells, G):
    """Compute green zone cells (within G squares of blue path but not on it)."""
    if G == 0:
        return set()
    blue_set = set(path_cells)
    green_set = set()
    for (px, py) in path_cells:
        for dx in range(-G, G + 1):
            for dy in range(-G, G + 1):
                nx, ny = px + dx, py + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    if (nx, ny) not in blue_set:
                        green_set.add((nx, ny))
    return green_set


def score_path(path_cells, G, mines, scan_time_A=7, overweight_N=0):
    """Score a path against a minefield using official IARC formula."""
    blue_set = set(path_cells)
    green_set = compute_green_zone(path_cells, G)

    orange_mines = blue_set & mines     # mines on blue path = death
    yellow_mines = green_set & mines    # mines in green zone = missed

    B = len(yellow_mines)
    A = scan_time_A
    N = overweight_N
    L = len(path_cells) * CELL_FT
    W = (1 + 2 * G) * CELL_FT

    if len(orange_mines) > 0:
        score = 0.0
    else:
        denominator = (1 + B) * L * (1 + 7 * A + 100 * N)
        score = 150000 * W / denominator if denominator > 0 else 0.0

    return {
        'score': score,
        'path_length_ft': L,
        'path_width_ft': W,
        'path_cells': len(path_cells),
        'green_zone_cells': len(green_set),
        'mines_on_path': len(orange_mines),
        'mines_in_green': B,
        'scan_time': A,
        'overweight': N,
        'dead': len(orange_mines) > 0,
    }


# ====================================================================
# Voronoi-guided grid pathfinding
# ====================================================================

def voronoi_to_grid_path(voronoi_waypoints_ft, mines):
    """
    Convert Voronoi waypoints (feet) to a mine-safe grid path
    by running A* between consecutive waypoints on the actual grid.
    """
    if not voronoi_waypoints_ft:
        return None

    # Convert foot coords to grid coords
    grid_waypoints = []
    for (fx, fy) in voronoi_waypoints_ft:
        gx = int(np.clip(fx / CELL_FT, 0, COLS - 1))
        gy = int(np.clip(fy / CELL_FT, 0, ROWS - 1))
        # If waypoint lands on a mine, nudge to nearest safe cell
        if (gx, gy) in mines:
            found = False
            for r in range(1, 5):
                for ddx in range(-r, r + 1):
                    for ddy in range(-r, r + 1):
                        nx, ny = gx + ddx, gy + ddy
                        if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in mines:
                            gx, gy = nx, ny
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

        if not grid_waypoints or (gx, gy) != grid_waypoints[-1]:
            grid_waypoints.append((gx, gy))

    if len(grid_waypoints) < 2:
        return None

    # A* between consecutive waypoints
    full_path = []
    for i in range(len(grid_waypoints) - 1):
        segment = grid_astar(mines, grid_waypoints[i], grid_waypoints[i + 1],
                             proximity_penalty=0.1)

        if segment is None:
            # Skip this waypoint, try direct to next
            continue

        if full_path:
            segment = segment[1:]  # avoid duplicating junction cell
        full_path.extend(segment)

    return full_path if full_path else None


def run_voronoi_method(mines, num_mines, scan_time=7, G=0, verbose=True):
    """Run Voronoi-guided pathfinding on a minefield."""
    mine_coords_ft = [((gx + 0.5) * CELL_FT, (gy + 0.5) * CELL_FT) for gx, gy in mines]

    # Try with decreasing buffer until we get a path
    for buffer_mult in [2.0, 1.5, 1.0]:
        pathfinder = VoronoiPathfinder(
            grid_size=(FIELD_W, FIELD_H),
            num_mines=num_mines,
            mine_buffer=CELL_FT * buffer_mult
        )
        pathfinder.mines = mine_coords_ft

        # Find safe start/end positions
        start_col = find_safest_column(mines, 0)
        end_col = find_safest_column(mines, ROWS - 1)
        pathfinder.start = ((start_col + 0.5) * CELL_FT, 0.5 * CELL_FT)
        pathfinder.end = ((end_col + 0.5) * CELL_FT, (ROWS - 0.5) * CELL_FT)

        path, path_dist, comp_time = pathfinder.find_optimal_path()

        if path is not None:
            if verbose:
                print(f"  Voronoi path: {len(path)} waypoints, buffer={CELL_FT * buffer_mult:.1f}ft")

            # Convert to grid path using A*
            grid_path = voronoi_to_grid_path(path, mines)

            if grid_path:
                # Ensure path starts at y=0 and ends at y=ROWS-1
                # Prepend/append if needed
                sx, sy = grid_path[0]
                if sy != 0:
                    prefix = grid_astar(mines, (sx, 0), (sx, sy), proximity_penalty=0.1)
                    if prefix:
                        grid_path = prefix + grid_path[1:]

                ex, ey = grid_path[-1]
                if ey != ROWS - 1:
                    suffix = grid_astar(mines, (ex, ey), (ex, ROWS - 1), proximity_penalty=0.1)
                    if suffix:
                        grid_path = grid_path + suffix[1:]

                return grid_path, comp_time

    # Voronoi failed completely - fall back to pure A*
    if verbose:
        print("  Voronoi failed, falling back to pure A*")
    return None, 0


# ====================================================================
# Pure grid A* pathfinding
# ====================================================================

def run_astar_method(mines, scan_time=7, G=0, verbose=True):
    """Run pure grid A* pathfinding."""
    start_col = find_safest_column(mines, 0)
    end_col = find_safest_column(mines, ROWS - 1)

    start = (start_col, 0)
    end = (end_col, ROWS - 1)

    t0 = time.time()
    grid_path = grid_astar(mines, start, end, proximity_penalty=0.3)
    comp_time = time.time() - t0

    if verbose and grid_path:
        print(f"  A* path: {len(grid_path)} cells, {comp_time:.3f}s")

    return grid_path, comp_time


# ====================================================================
# Visualization
# ====================================================================

def visualize_result(mines, path_cells, G, result, title="IARC Simulator", save_path=None):
    """Visualize the minefield with path, green zone, and mines color-coded."""
    fig, ax = plt.subplots(figsize=(6, 18))

    blue_set = set(path_cells)
    green_set = compute_green_zone(path_cells, G)

    for x in range(COLS):
        for y in range(ROWS):
            cell = (x, y)
            if cell in mines and cell in blue_set:
                color = 'orange'
            elif cell in blue_set:
                color = '#4488ff'
            elif cell in mines and cell in green_set:
                color = 'yellow'
            elif cell in green_set:
                color = 'lightgreen'
            elif cell in mines:
                color = 'red'
            else:
                color = 'white'

            rect = plt.Rectangle((x, y), 1, 1, facecolor=color,
                                  edgecolor='gray', linewidth=0.1)
            ax.add_patch(rect)

    ax.set_xlim(0, COLS)
    ax.set_ylim(0, ROWS)
    ax.set_aspect('equal')
    ax.set_xlabel('Column (x)')
    ax.set_ylabel('Row (y)')

    score_str = "DEAD" if result['dead'] else f"{result['score']:.3f}"
    ax.set_title(f"{title}\nScore: {score_str} | L={result['path_length_ft']}ft | "
                 f"W={result['path_width_ft']}ft | Missed={result['mines_in_green']}")

    legend_patches = [
        mpatches.Patch(color='#4488ff', label='Blue path'),
        mpatches.Patch(color='lightgreen', label='Green zone'),
        mpatches.Patch(color='red', label='Mine'),
        mpatches.Patch(color='orange', label='Mine on path (DEAD)'),
        mpatches.Patch(color='yellow', label='Mine in green (missed)'),
    ]
    ax.legend(handles=legend_patches, loc='upper right', fontsize=7)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


# ====================================================================
# Simulation runners
# ====================================================================

def run_simulation(method='both', num_mines=135, seed=42, G=0, scan_time=7, show_plot=True):
    """Run pathfinding simulation with specified method."""
    print("=" * 60)
    print(f"IARC SIMULATOR | Mines: {num_mines} | Seed: {seed} | G={G}")
    print("=" * 60)

    mines = generate_minefield(num_mines=num_mines, seed=seed)

    results = {}

    if method in ('voronoi', 'both'):
        print("\n[VORONOI METHOD]")
        grid_path, comp_time = run_voronoi_method(mines, num_mines, scan_time, G)
        if grid_path:
            result = score_path(grid_path, G, mines, scan_time_A=scan_time)
            results['voronoi'] = result
            print_result(result, comp_time)
            commands = grid_path_to_commands(grid_path, G)
            if show_plot:
                visualize_result(mines, grid_path, G, result,
                                 title=f"Voronoi | Seed={seed}", save_path='iarc_voronoi_result.png')
        else:
            print("  No path found!")
            results['voronoi'] = None

    if method in ('astar', 'both'):
        print("\n[PURE A* METHOD]")
        grid_path, comp_time = run_astar_method(mines, scan_time, G)
        if grid_path:
            result = score_path(grid_path, G, mines, scan_time_A=scan_time)
            results['astar'] = result
            print_result(result, comp_time)
            commands = grid_path_to_commands(grid_path, G)
            if show_plot:
                visualize_result(mines, grid_path, G, result,
                                 title=f"A* | Seed={seed}", save_path='iarc_astar_result.png')

            # Print commands for best method
            print(f"\nPath commands (paste into simulator):")
            print(commands)
        else:
            print("  No path found!")
            results['astar'] = None

    return results


def print_result(result, comp_time):
    """Print scored result."""
    score_str = "DEAD (mine on path!)" if result['dead'] else f"{result['score']:.3f}"
    print(f"  Score:         {score_str}")
    print(f"  Path length:   {result['path_length_ft']} ft ({result['path_cells']} cells)")
    print(f"  Path width:    {result['path_width_ft']} ft")
    print(f"  Mines on path: {result['mines_on_path']}")
    print(f"  Missed mines:  {result['mines_in_green']}")
    print(f"  Compute time:  {comp_time:.3f}s")


def batch_test(num_trials=20, num_mines=135, G=0, scan_time=7):
    """Compare Voronoi and A* across many seeds."""
    print(f"\nBatch test: {num_trials} trials, {num_mines} mines, G={G}, A={scan_time}")
    print(f"{'Seed':<8} {'Voronoi':<12} {'V-Len':<8} {'A*':<12} {'A*-Len':<8}")
    print("-" * 56)

    v_scores, a_scores = [], []
    v_deaths, a_deaths = 0, 0
    v_fails = 0

    for i in range(num_trials):
        seed = i * 0.1 + 0.01
        mines = generate_minefield(num_mines=num_mines, seed=seed)

        # Voronoi method
        v_path, _ = run_voronoi_method(mines, num_mines, scan_time, G, verbose=False)
        if v_path:
            v_result = score_path(v_path, G, mines, scan_time_A=scan_time)
            v_score_s = "DEAD" if v_result['dead'] else f"{v_result['score']:.3f}"
            v_len_s = str(v_result['path_length_ft'])
            if v_result['dead']:
                v_deaths += 1
            else:
                v_scores.append(v_result['score'])
        else:
            v_score_s = "NO PATH"
            v_len_s = "-"
            v_fails += 1

        # A* method
        a_path, _ = run_astar_method(mines, scan_time, G, verbose=False)
        if a_path:
            a_result = score_path(a_path, G, mines, scan_time_A=scan_time)
            a_score_s = "DEAD" if a_result['dead'] else f"{a_result['score']:.3f}"
            a_len_s = str(a_result['path_length_ft'])
            if a_result['dead']:
                a_deaths += 1
            else:
                a_scores.append(a_result['score'])
        else:
            a_score_s = "NO PATH"
            a_len_s = "-"

        print(f"{seed:<8.4f} {v_score_s:<12} {v_len_s:<8} {a_score_s:<12} {a_len_s:<8}")

    print(f"\n{'=' * 56}")
    print(f"{'':15} {'VORONOI':<20} {'A*':<20}")
    print(f"  Avg score:     {np.mean(v_scores):.3f} ({len(v_scores)} alive)     "
          f"{np.mean(a_scores):.3f} ({len(a_scores)} alive)" if v_scores and a_scores else "")
    if v_scores:
        print(f"  Best (V):      {max(v_scores):.3f}")
    if a_scores:
        print(f"  Best (A*):     {max(a_scores):.3f}")
    print(f"  Deaths:        V={v_deaths}  A*={a_deaths}  V-fails={v_fails}")
    print(f"  Survival:      V={100*(num_trials-v_deaths-v_fails)/num_trials:.0f}%  "
          f"A*={100*(num_trials-a_deaths)/num_trials:.0f}%")


# ====================================================================
# Brute-force optimizer: try all start/end columns and G values
# ====================================================================

def optimize(num_mines=135, seed=42, scan_time=7, max_G=10, show_plot=True):
    """
    Find the absolute best score by trying all start columns, end columns,
    and green zone widths. Uses A* for each combo.
    """
    print("=" * 60)
    print(f"OPTIMIZER | Mines: {num_mines} | Seed: {seed} | A={scan_time}")
    print(f"Trying all 40 start cols x 40 end cols x G=0..{max_G}")
    print("=" * 60)

    mines = generate_minefield(num_mines=num_mines, seed=seed)
    near_mines = build_mine_neighbor_set(mines)

    best_score = 0
    best_config = None
    best_path = None
    best_result = None
    total_tried = 0
    paths_found = 0

    t0 = time.time()

    # Cache A* paths: key = (start_col, end_col)
    path_cache = {}

    for start_col in range(COLS):
        if (start_col, 0) in mines:
            continue
        for end_col in range(COLS):
            if (end_col, ROWS - 1) in mines:
                continue

            start = (start_col, 0)
            end = (end_col, ROWS - 1)

            # Run A* with no proximity penalty for shortest path
            grid_path = grid_astar(mines, start, end, proximity_penalty=0.0)
            total_tried += 1

            if grid_path is None:
                continue
            paths_found += 1

            # Try each G value
            for G in range(0, max_G + 1):
                result = score_path(grid_path, G, mines, scan_time_A=scan_time)

                if not result['dead'] and result['score'] > best_score:
                    best_score = result['score']
                    best_config = {'start_col': start_col, 'end_col': end_col, 'G': G}
                    best_path = grid_path
                    best_result = result

    elapsed = time.time() - t0
    print(f"\nSearched {total_tried} combos ({paths_found} valid paths) in {elapsed:.2f}s")

    if best_result:
        print(f"\n*** BEST SCORE: {best_score:.3f} ***")
        print(f"  Start col:     {best_config['start_col']}")
        print(f"  End col:       {best_config['end_col']}")
        print(f"  G (green zone):{best_config['G']}")
        print(f"  Path length:   {best_result['path_length_ft']} ft ({best_result['path_cells']} cells)")
        print(f"  Path width:    {best_result['path_width_ft']} ft")
        print(f"  Mines on path: {best_result['mines_on_path']}")
        print(f"  Missed mines:  {best_result['mines_in_green']}")
        print(f"  Theoretical max (G=0, L=300): {300000 / (300 * (1 + 7 * scan_time)):.3f}")

        commands = grid_path_to_commands(best_path, best_config['G'])
        print(f"\nPath commands (paste into simulator):")
        print(commands)

        if show_plot:
            visualize_result(mines, best_path, best_config['G'], best_result,
                             title=f"OPTIMIZED | Seed={seed} | G={best_config['G']}",
                             save_path='iarc_optimized_result.png')
    else:
        print("No valid path found!")

    return best_result, best_path, best_config


def optimize_batch(num_trials=20, num_mines=135, scan_time=7, max_G=10):
    """Run optimizer across many seeds."""
    print(f"\nOptimizer batch: {num_trials} trials, {num_mines} mines, A={scan_time}")
    print(f"{'Seed':<8} {'Score':<10} {'G':<4} {'Length':<8} {'Width':<8} {'Missed':<8} {'Start':<6} {'End':<6}")
    print("-" * 66)

    scores = []

    for i in range(num_trials):
        seed = i * 0.1 + 0.01
        result, path, config = optimize(num_mines=num_mines, seed=seed,
                                         scan_time=scan_time, max_G=max_G, show_plot=False)
        if result and not result['dead']:
            scores.append(result['score'])
            print(f"{seed:<8.4f} {result['score']:<10.3f} {config['G']:<4} "
                  f"{result['path_length_ft']:<8} {result['path_width_ft']:<8} "
                  f"{result['mines_in_green']:<8} {config['start_col']:<6} {config['end_col']:<6}")
        else:
            print(f"{seed:<8.4f} {'FAIL':<10}")

    if scores:
        print(f"\n{'=' * 66}")
        print(f"  Avg score:  {np.mean(scores):.3f}")
        print(f"  Best score: {max(scores):.3f}")
        print(f"  Worst score:{min(scores):.3f}")
        print(f"  Survival:   {len(scores)}/{num_trials} ({100*len(scores)/num_trials:.0f}%)")


# ====================================================================

if __name__ == "__main__":
    import sys
    matplotlib.use('Agg')

    mode = sys.argv[1] if len(sys.argv) > 1 else 'both'

    if mode == 'batch':
        batch_test(num_trials=20)
    elif mode == 'optimize':
        optimize(num_mines=135, seed=42, scan_time=7, max_G=10)
    elif mode == 'optimize-batch':
        optimize_batch(num_trials=20, num_mines=135, scan_time=7, max_G=10)
    else:
        run_simulation(method=mode, num_mines=135, seed=42, G=0, scan_time=7, show_plot=True)

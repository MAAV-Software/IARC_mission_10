import heapq

# Your exact field coordinates
svg_mines = [
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

class CleanSweepOptimizer:
    def __init__(self, pixel_mines):
        self.grid_w = 40
        self.grid_l = 150 # Must reach exactly Y=150
        self.mines = set()
        
        for px, py in pixel_mines:
            col = (px - 30) // 10
            row = (1490 - py) // 10
            self.mines.add((col, row))

    def get_path_for_G(self, G):
        """Builds a 'No-Fly Zone' based on G, ensuring the green sweep NEVER touches a mine"""
        invalid_cells = set()
        
        # Artificially expand every mine by the width of the green zone
        for mx, my in self.mines:
            for dx in range(-G, G + 1):
                for dy in range(-G, G + 1):
                    invalid_cells.add((mx + dx, my + dy))

        best_path = None
        best_len = float('inf')

        # Test every possible starting column at the bottom of the field
        for start_x in range(self.grid_w):
            if (start_x, 0) in invalid_cells: continue

            heap = [(self.grid_l, 0, start_x, 0, 0, [(start_x, 0)])] # f, g, x, y, prev_dx, path
            visited = {}

            while heap:
                f, g, x, y, prev_dx, path = heapq.heappop(heap)

                if y == self.grid_l:
                    if g < best_len:
                        best_len = g
                        best_path = path
                    break 

                state = (x, y)
                if state in visited and visited[state] <= g: continue
                visited[state] = g

                # Standard U, D, L, R routing
                for dx, dy in [(0, 1), (-1, 0), (1, 0), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    
                    if 0 <= nx < self.grid_w and 0 <= ny <= self.grid_l:
                        if (nx, ny) not in invalid_cells:
                            
                            # RUBBER BAND TIE-BREAKER: 
                            # Constantly pulls the path back to the start_x column.
                            # This completely prevents blocky L-shapes and squiggly wandering,
                            # forcing it to use tight stair-step diagonals when dodging.
                            drift_penalty = abs(nx - start_x) * 0.001
                            
                            # Tiny turn penalty keeps lines straight and rigid
                            turn_penalty = 0.0001 if dx != prev_dx else 0
                            
                            new_g = g + 1 + drift_penalty + turn_penalty
                            h = self.grid_l - ny
                            
                            heapq.heappush(heap, (new_g + h, new_g, nx, ny, dx, path + [(nx, ny)]))

        return best_path

    def optimize_score(self):
        best_score = -1
        best_G = 0
        best_path = None

        print(f"Loaded {len(self.mines)} mines.")
        print("Calculating exact IARC formulas for 100% Clean Green Zones...")
        
        # Test massive sweeping bounds down to small ones.
        for G in range(15, -1, -1):
            path = self.get_path_for_G(G)
            
            if path:
                L_ft = (len(path) - 1) * 2
                W_ft = 2 * (1 + 2 * G)
                
                # Because our "No-Fly Zone" logic is bulletproof, B is guaranteed to be 0.
                # Formula becomes: 150000 * W / (1 * L)
                score_factor = W_ft / L_ft
                
                print(f"   Tested G={G} -> Path Found! L={L_ft}ft, W={W_ft}ft | Score Factor: {score_factor:.4f}")
                
                if score_factor > best_score:
                    best_score = score_factor
                    best_G = G
                    best_path = path

        return best_path, best_G

    def export_to_simulator(self, path, G_value):
        if not path: return []
        commands = [f"S,{path[0][0]},{G_value}"]
        
        current_cmd = None
        count = 0
        
        for i in range(1, len(path)):
            pc, pr = path[i-1]
            nc, nr = path[i]
            
            cmd = None
            if nc == pc and nr == pr + 1: cmd = 'U'
            elif nc == pc and nr == pr - 1: cmd = 'D'
            elif nc == pc - 1 and nr == pr: cmd = 'L'
            elif nc == pc + 1 and nr == pr: cmd = 'R'
            
            if cmd is None: continue 
            
            if cmd == current_cmd:
                count += 1
            else:
                if current_cmd: commands.append(f"{current_cmd},{count}")
                current_cmd = cmd
                count = 1
                
        if current_cmd: commands.append(f"{current_cmd},{count}")
        return commands

if __name__ == "__main__":
    optimizer = CleanSweepOptimizer(svg_mines)
    path, best_G = optimizer.optimize_score()
    
    if path:
        L_ft = (len(path) - 1) * 2
        W_ft = 2 * (1 + 2 * best_G)
        
        print("\n✅ PERFECT PATH GENERATED!")
        print(f"Start Column: {path[0][0]}")
        print(f"Green Zone (G): {best_G} squares on each side")
        print(f"Total Swept Width (W): {W_ft} feet")
        print(f"Path Length (L): {L_ft} feet")
        print(f"Missed Mines (B): 0 Guaranteed")
        print("-" * 40)
        
        commands = optimizer.export_to_simulator(path, best_G)
        with open("clean_sweep_input.txt", "w") as f:
            f.write("\n".join(commands))
            
        print("✅ Ready! Paste the contents of 'clean_sweep_input.txt' into the simulator.")
    else:
        print("❌ Failed to calculate a path.")
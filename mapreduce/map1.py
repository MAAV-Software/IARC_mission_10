#!/usr/bin/env python3
import sys
import pathlib

current_dir = pathlib.Path(__file__).parent.parent
map_output = current_dir / "output" / "map-1-output.txt"
with open(map_output, "w") as f: # Clear the output before writing into it again
    pass

for line in sys.stdin:
    values = line.strip().split() # key represents term, val represents the doc_id, tf, nk
    with open(map_output, "a") as f:
        f.write(f"{values[0]}\t{values[1]},{values[2]},{values[3]},{values[4]},{values[5]},{values[6]},{values[7]}\n")
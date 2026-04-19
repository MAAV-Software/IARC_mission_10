import subprocess

locations_path = "sample_locations.txt"
output_path = "results.txt"

with open(output_path, "w") as f:
    pass

with open(locations_path, "r") as f:
    for i, line in enumerate(f):
        line_contents = line.strip().split()
        args = []
        args.append("python3")
        args.append("gps_calc2.py")
        args.append(line_contents[0])
        args.append(line_contents[1])
        subprocess.run(args)
         

import subprocess

command = []
for i in range(2):
	command.append("./bin/run_cam")
	print(f"{i}")
	command.append(str(i))
	subprocess.run(command)
	command = []

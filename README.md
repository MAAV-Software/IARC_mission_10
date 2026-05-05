# IARC :) 
yum
hello

Object Detection (Testing):
- test_model.py

Object Detection (Training):
- train_model.py
- blender/
- weights/
- Would still need a dataset folder containing the validation and yaml if we wanted to use it

Object Detection (Image Dataset):
- test_images/

On-board Camera Functions:
- computer_vision/

Navigation:
- software_ws/ directory contains

Mine Location Calculation:
- drones/scout_swati_charlie_zj_vincent.py

Computer Networking:
- /drones/roles/explorer.py
- /drones/roles/manager.py
- /drones/run_master.py
- /drones/run_worker.py

Rotate GPS:
- gps_calc2.py

Misc:
- sample_locations.txt (sample blender locations xyz)
- results.txt (sample output of converting mine locations)
- DervinSmellsLikePoop.csv and DervinsGOUToutBREAK.txt (input and output to tcp servers)

Current Pipeline:
- Record the bounding boxes of the field in the /constants directory
- Drones need to take in the readings during flight (navigation stuff and store into format similar to sample_locations.txt)
- Once we have that, everything else can basically be done through the /drones directory
- Each drone will run the /drones/skib.py, and this basically just rotates all the mines to be properly oriented with true north
- That will save the rotated results to results.txt
- Then the drones will run /drones/bidi.py, which then takes the YOLO readings and finds the mines within the pictures and outputs the mine locations in world coordinates, store them into DervinSmellsLikePoop.csv
- Once each drone has populated the csv file, the non-master drones will run the /drones/run_worker.py script, and the master drone will run the /drones/run_master.py script
- This step basically makes it so that all the drones send their results over to one place
- The master drone will collect all of the results, and then run the IARC pathfinder that Noah and co wrote to find the best path
- The /donres/run_master.py script will output the iarc_result.png image out, showing the best path
- Optional: We also print out the list of instructions to the terminal and we can save those results if needed as well



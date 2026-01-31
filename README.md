# Drone Fleet #

## Networking ##

With the upcoming IARC Missio 10 upcoming, the competition requires a fleet of 4 drones, not just a single drone to compete. The goal of these 4 drones are to 
map out a football-sized airfield, take note of any obstacles, map them, and calculate a path through those obstacles.

In order to get the maximal efficiency out of our drones, we plan on having each drone explore it's own area and then having them communicate their results
back to a "Manager" drone in order to aggregate results and calculate the path. To do this efficiently, we utilized Python TCP sockets in order to ensure
that messages sent via the sockets are accurate.

## MapReduce ##

To process the results, a MapReduce framework was implemented to streamline the processing of the results that were communicated from drone to drone. We utilized
a map stage to format the results, and then a reduce stage to transform the outputted object detection locations into our local coordinates. Additional Python scripts were
used to visualize out the mines and the path.

To calculate the paths, we implemented a simple Breadth-First-Search (BFS) with Binary Search. By iteratively increasing the width of our BFS path using Binary Search, we were
able to find the widest path avaiable given the field, but also the shortest path width the given width.

Attached below is an image of our results:
- Red squares indicate obstacles that we would like to avoid
- Green path represents the optimal path
- Blue path represents an alternative path

<img width="3000" height="3000" alt="output_path" src="https://github.com/user-attachments/assets/a6d7c69e-4bb9-4967-83fe-8b47e4c7a30f" />

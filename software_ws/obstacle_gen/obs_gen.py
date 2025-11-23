import random
import math
import pyproj
import chevron
import pymap3d as pm
starting_coord = (7, 7, 0) # degree starting position plus height
# total_way_points = 10
way_points = []
way_points.append(starting_coord)

f = open("trees.sdf", "w")

source_proj = pyproj.Proj(init='epsg:4326')  # WGS84
target_proj = pyproj.Proj(init='epsg:3857') 
# we changed these to absolute paths for the vscode debugger to work
with open('templates/world_template.mustache', 'r') as m:
    rendered_content = chevron.render(m)
    f.write(rendered_content)
    # print(rendered_content)
    
lat0 = 0
lon0 = 0
h0 = 0

FT_TO_METER = 0.3049
for i in range(0, 11):
    lat = random.uniform(0, 300 * FT_TO_METER)
    lon = random.uniform(0, 80 * FT_TO_METER)
    h = 0
    # new_point = pm.geodetic2enu(lat, lon, h, lat0, lon0, h0)
    with open('templates/tree_template.mustache', 'r') as m:
        rendered_content = chevron.render(m, {'point': (i+1), 'x': lat, 'y': lon, 'z': 0})
        f.write(rendered_content)

f.write("</world>\n")
f.write("</sdf>\n")

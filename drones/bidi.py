
import os
import cv2
import pathlib
from ultralytics import YOLOWorld
import numpy as np
import math

input_path = "results.txt"

# camera 
# h: 46.5 in
# w: 36.25 in

def main():

    # TODO We now have the "global" location of the mines, as well as the bounding boxes of the mines
    # What we need to do now is to make it so that we calculate the location of the mine in the global space
    # We can now just assume that the center of the bounding box is the center of the mine

    # for (c, x, y, z, pic_x_min, pic_y_min, pic_x_max, pic_y_max) in coords_list:
        
    #     loc_pic_vertical = 2 * z * math.tan(math.radians(25.5))
    #     loc_pic_horizontal = 2 * z * math.tan(math.radians(32.5))

    #     mine_x = (pic_x_min + pic_x_max) / 2
    #     mine_y = (pic_y_min + pic_y_max) / 2

    #     # Relative mine coordinates with 0.5,0.5 center
    #     mine_x_relation = mine_x - .5
    #     mine_y_relation = mine_y - .5

    #     scaled_x = mine_x_relation * loc_pic_horizontal
    #     scaled_y = mine_y_relation * loc_pic_vertical

    #     global_x = scaled_x + x
    #     global_y = y - scaled_y

    #     f.write(f"{global_x},{global_y}\n")

    # need to hardcode these coordinates before the co
    '''TL_longitude =  -83.711819
    TL_latitude = 42.293341999999996

    TR_longitude = -83.71151429291044
    TR_latitude = 42.293341999999996

    BL_longitude = -83.711819
    BL_latitude = 42.29309574987266

    BR_longitude = -83.71151429291044
    BR_latitude = 42.29309574987266'''

    # TL:  (42.293341999999996, -83.711819)
    # TR:  (42.293341999999996, -83.71151429291044)
    # BR:  (42.29309574987266, -83.71151429291044)
    # BL:  (42.29309574987266, -83.711819)

    # TODO Change these to take into account the height later on
    img_height_inch = 46.5
    img_width_inch = 36.25

    mine_locations = []

    with open(input_path, "r") as f:
        for line in f:

            # pt_longitude = -83.7117520228778
            # pt_latitude = 42.29331413210881

            line_contents = line.strip().split()
            pt_latitude = float(line_contents[0])
            pt_longitude = float(line_contents[1])
            absolute_height = float(line_contents[2])
            mine_x_min = float(line_contents[3])
            mine_x_max = float(line_contents[4])
            mine_y_min = float(line_contents[5])
            mine_y_max = float(line_contents[6])

            
            img_height_cm = (img_height_inch * 2.54) / 100 #convert to inches
            img_width_cm = (img_width_inch * 2.54) / 100
            
            # mine_x_min, mine_y_min, mine_x_max, mine_y_max = (0.11155333116319445, 0.15966543579101564, 0.19914363606770832, 0.22527638753255208)
            mine_x , mine_y = (mine_x_min + mine_x_max ) / 2, (mine_y_min + mine_y_max ) / 2
            mine_x_relative = mine_x - 0.5
            mine_y_relative = mine_y - 0.5
            
            scaled_x = mine_x_relative * img_width_cm
            scaled_y = mine_y_relative * img_height_cm

            #from 4/5 onwards
            scaled_x_meters = scaled_x / 100 #convert to meters
            scaled_y_meters = scaled_y / 100

            change_in_lat = scaled_y_meters/111320 #find change in latitude from center to point
            change_in_long = scaled_x_meters/(111320*np.cos(math.radians(pt_latitude)))

            new_lat = change_in_lat + pt_latitude #calculate new lat/long
            new_long = change_in_long + pt_longitude
            mine_locations.append((new_lat, new_long))
        
    with open("DervinSmellsLikePoop.csv", "w") as f:    
        f.write("lat,lon\n")
        for location in mine_locations:
            f.write(f"{location[0]},{location[1]}\n")

    
if __name__ == "__main__":
    main()

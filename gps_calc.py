import math
import numpy as np
#import socket
#import json
import re

def convert_to_dec_degrees(coord1):
    coord1str = coord1
    result_coord = []

    for i in range(0, 2):
        #if there is an empty space at the beginning, get rid of it
        if (coord1str[0] == " "):
            coord1str = coord1str[1:]
        mult_by_neg_one = False

        #extract 1st D
        separator = "°"
        index = coord1str.find(separator)
        D = coord1str[:index]
        coord1str = coord1str.replace(D, '')
        coord1str = coord1str[1:]
        print(D)
        print(coord1str)
        D = float(D)

        #extract 1st M
        separator = "'"
        index = coord1str.find(separator)
        M = coord1str[:index]
        coord1str = coord1str.replace(M, '')
        coord1str = coord1str[1:]
        print(M)
        print(coord1str)
        M = float(M)

        #extract 1st S
        separator = '"'
        index = coord1str.find(separator)
        S = coord1str[:index]
        coord1str = coord1str.replace(S, '')
        coord1str = coord1str[1:]
        print(S)
        print(coord1str)
        S = float(S)

        #extract 1st direction
        direction = coord1str[0]
        coord1str = coord1str[1:]
        if ((direction == "S") or (direction == "W")):
            mult_by_neg_one = True

        #calc result
        result = D + M/60 + S/3600
        if (mult_by_neg_one):
            result *= 1
        
        result_coord.append(result)
    
    return result_coord #list w 2 #s: 1st is x-coord, 2nd is y-coord



#aligns a gps coord to the x & y axis according to a pivot point & given the angle to rotate 
def align_coordinates(pivot_pt, gps_coord, theta): 
    #subtract the pivot point from the gps coord to treat the pivot as the origin 
    x_shift = (gps_coord[0] - pivot_pt[0])
    y_shift = gps_coord[1] - pivot_pt[1]

    #rotate according to theta to align w x and y coords of pivot point
    x_final = ((x_shift*math.cos(theta) - y_shift*math.sin(theta)))
    y_final = (x_shift*math.sin(theta) + y_shift*math.cos(theta))

    #translate back to actual coordinates
    x_final += pivot_pt[0]
    y_final += pivot_pt[1]

    return (x_final, y_final)

def rotate_back(pivot_pt, gps_coord, theta): 
    #subtract the pivot point from the gps coord to treat the pivot as the origin 
    x_shift = gps_coord[0] - pivot_pt[0]
    y_shift = gps_coord[1] - pivot_pt[1]

    #rotate according to theta
    x_final = (x_shift*math.cos(-theta) - y_shift*math.sin(-theta))
    y_final = (x_shift*math.sin(-theta) + y_shift*math.cos(-theta))

    #translate back to actual coordinates
    x_final += pivot_pt[0]
    y_final += pivot_pt[1]

    return (x_final, y_final)

#coordinates are in form D°M'S"(N/S/W/E) D°M'S"(N/S/W/E)
field_tl = """42°24'40.07"N 83°29'53.85"W"""
field_tr = """42°24'40.20"N 83°29'51.73"W"""
field_br = """42°24'36.68"N 83°29'51.26"W"""
field_bl = """42°24'36.52"N 83°29'53.40"W"""

field_mid = (42.4106462, -83.4982341)

print(convert_to_dec_degrees(field_tl))

#field_width = 49.15 #m
#field_height = 109.82 #m

'''
#tests align_coordinates
print(field_tl)
aligned_tr = align_coordinates(field_tl, field_tr, theta)
print(aligned_tr)

aligned_br = align_coordinates(field_tl, field_br, theta)
print(aligned_br)

aligned_bl = align_coordinates(field_tl, field_bl, theta)
print(aligned_bl)

aligned_mid = align_coordinates(field_tl, field_mid, theta)
print("middle point: ", aligned_mid)

print("\n")

#tests rotate back
orig_tr = rotate_back(field_tl, aligned_tr, theta)
print(orig_tr)
print(field_tr == orig_tr)

orig_br = rotate_back(field_tl, aligned_br, theta)
print(orig_br)
print(field_br == orig_br)

orig_bl = rotate_back(field_tl, aligned_bl, theta)
print(orig_bl)
print(field_bl == orig_bl) 
'''

#need camera GPS position, camera altitude, camera orientation (roll, pitch, yaw), camera focal length & scaling factor

# #Step 1- convert pixel to camera ray
# f = 0 #physical focal length of camera (TODO: replace)
# s = 0 #pixel size scaling factor (TODO: replace)
# # fxy = f/s
# iw = 0 #image width (TODO: replace)
# ih = 0 #image height (TODO: replace)
# cx = iw/2 #normalized camera x-coord
# cy = ih/2 #normalized camera y-coord

# u = 0 #mine/pixel x-coordinate, center of bounding box (TODO: replace)
# v = 0 #mine/pixel y-coordinate, center of bounding box (TODO: replace)
# # xc = (u -cx)/fxy #x-coord in camera
# # yc = (v -cy)/fxy #y-coord in camera

# # r = [xc, yc, 1] #ray in camera space


# #Step 2- rotate ray (tilt adjustment)
# roll = 0 #ϕ (TODO: replace)
# pitch = 0 #θ (TODO: replace)
# yaw = 0 #ψ (TODO: replace)

# Rx = []
# Rx.append([1, 0, 0])
# Rx.append([0, np.cos(roll), -1*np.sin(roll)])
# Rx.append([0, np.sin(roll), -1*np.cos(roll)])
# Ry = []
# Ry.append([1, 0, 0])
# Ry.append([0, np.cos(pitch), -1*np.sin(pitch)])
# Ry.append([0, np.sin(pitch), -1*np.cos(pitch)])
# Rz = []
# Rz.append([np.cos(yaw), -1*np.sin(yaw), 0])
# Rz.append([np.sin(yaw), -1*np.cos(yaw), 0])
# Rz.append([0, 0, 1])
# R = Rz*Ry*Rx
# r_world = R*r


# #Step 3- intersect ray with ground
# H = 0 #camera height (TODO: replace)
# Xc = 0 #X-coord of camera irl (TODO: replace)
# Yc = 0 #Y-coord of camera irl (TODO: replace)
# X = Xc + (H/r_world[2])*r[0] #X-coord of mine irl
# Y = Yc + (H/r_world[2])*r[1] #Y-coord of mine irl


# #Step 4- convert meters to latitude & longitude
# lat_cam = 0 #latitude of camera (TODO: replace)
# long_cam = 0 #longitude of camera (TODO: replace)
# lat = lat_cam + Y/111320
# long = long_cam + X/(111320*np.cos(roll))



'''
TODO: 
need camera GPS position, camera altitude, camera orientation (roll, pitch, yaw), camera focal length & scaling factor
put code into funcs & int main, send output to a txt file
'''

field_tl_1 = """42°24'40.07"N 83°29'53.85"W"""

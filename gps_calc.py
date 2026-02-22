import math
import numpy as np
#import socket
#import json

#aligns a gps coord to the x & y axis according to a pivot point & given the angle to rotate 
#(rotating negatively/counterclockwise)
def align_coordinates(pivot_pt, gps_coord, theta): 
    #subtract the pivot point from the gps coord to treat the pivot as the origin 
    x_shift = (gps_coord[0] - pivot_pt[0])
    y_shift = gps_coord[1] - pivot_pt[1]

    #rotate negatively according to theta to align w x and y axis
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

    #rotate positively according to theta
    x_final = (x_shift*math.cos(-theta) - y_shift*math.sin(-theta))
    y_final = (x_shift*math.sin(-theta) + y_shift*math.cos(-theta))

    #translate back to actual coordinates
    x_final += pivot_pt[0]
    y_final += pivot_pt[1]

    return (x_final, y_final)


field_tl = (42.411131, -83.498292)
field_tr = (42.411169, -83.497703)
field_br = (42.410189, -83.497575)
field_bl = (42.410147, -83.498169)

#field_width = 49.15 #m
#field_height = 109.82 #m

w = field_tr[1] - field_tl[1]
h = field_tr[0] - field_tl[0]
print(w, h)
theta = math.atan(h/w)
print(math.degrees(theta))

#tests align_coordinates
aligned_tr = align_coordinates(field_tl, field_tr, theta)
print(aligned_tr)

aligned_br = align_coordinates(field_tl, field_br, theta)
print(aligned_br)

aligned_bl = align_coordinates(field_tl, field_bl, theta)
print(aligned_bl)

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
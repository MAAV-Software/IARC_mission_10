import math
import numpy as np

#need camera GPS position, camera altitude, camera orientation (roll, pitch, yaw), camera focal length & scaling factor

#Step 1- convert pixel to camera ray
f = 0 #physical focal length of camera (TODO: replace)
s = 0 #pixel size scaling factor (TODO: replace)
fxy = f/s
iw = 0 #image width (TODO: replace)
ih = 0 #image height (TODO: replace)
cx = iw/2 #normalized camera x-coord
cy = ih/2 #normalized camera y-coord

u = 0 #mine/pixel x-coordinate, center of bounding box (TODO: replace)
v = 0 #mine/pixel y-coordinate, center of bounding box (TODO: replace)
xc = (u -cx)/fxy #x-coord in camera
yc = (v -cy)/fxy #y-coord in camera

r = [xc, yc, 1] #ray in camera space


#Step 2- rotate ray (tilt adjustment)
roll = 0 #ϕ (TODO: replace)
pitch = 0 #θ (TODO: replace)
yaw = 0 #ψ (TODO: replace)

Rx = []
Rx.append([1, 0, 0])
Rx.append([0, np.cos(roll), -1*np.sin(roll)])
Rx.append([0, np.sin(roll), -1*np.cos(roll)])
Ry = []
Ry.append([1, 0, 0])
Ry.append([0, np.cos(pitch), -1*np.sin(pitch)])
Ry.append([0, np.sin(pitch), -1*np.cos(pitch)])
Rz = []
Rz.append([np.cos(yaw), -1*np.sin(yaw), 0])
Rz.append([np.sin(yaw), -1*np.cos(yaw), 0])
Rz.append([0, 0, 1])
R = Rz*Ry*Rx
r_world = R*r


#Step 3- intersect ray with ground
H = 0 #camera height (TODO: replace)
Xc = 0 #X-coord of camera irl (TODO: replace)
Yc = 0 #Y-coord of camera irl (TODO: replace)
X = Xc + (H/r_world[2])*r[0] #X-coord of mine irl
Y = Yc + (H/r_world[2])*r[1] #Y-coord of mine irl


#Step 4- convert meters to latitude & longitude
lat_cam = 0 #latitude of camera (TODO: replace)
long_cam = 0 #longitude of camera (TODO: replace)
lat = lat_cam + Y/111320
long = long_cam + X/(111320*np.cos(roll))



'''
TODO: 
need camera GPS position, camera altitude, camera orientation (roll, pitch, yaw), camera focal length & scaling factor
put code into funcs & int main, send output to a txt file
'''
import math
from pyproj import Transformer

def convert_to_dec_degrees(coord1):
    coord1str = coord1
    result_coord = []
    for i in range(0, 2):
        if (coord1str[0] == " "):
            coord1str = coord1str[1:]
        mult_by_neg_one = False
        separator = "°"
        index = coord1str.find(separator)
        D = coord1str[:index]
        coord1str = coord1str.replace(D, '')
        coord1str = coord1str[1:]
        D = float(D)
        separator = "'"
        index = coord1str.find(separator)
        M = coord1str[:index]
        coord1str = coord1str.replace(M, '')
        coord1str = coord1str[1:]
        M = float(M)
        separator = '"'
        index = coord1str.find(separator)
        S = coord1str[:index]
        coord1str = coord1str.replace(S, '')
        coord1str = coord1str[1:]
        S = float(S)
        direction = coord1str[0]
        coord1str = coord1str[1:]

        if ((direction == "S") or (direction == "W")):
            mult_by_neg_one = True
        result = D + M/60 + S/3600
        if (mult_by_neg_one):
            result *= -1

        result_coord.append(result)
    return result_coord

def get_utm_transformer(input_coord):
    lat = float(input_coord[0])
    lon = float(input_coord[1])
    zone = int((lon + 180) / 6) + 1
     
    if lat >= 0:
        epsg = 32600 + zone
    else:
        epsg = 32700 + zone
    return Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)

def convert_to_utm(input_coord, transformer):
    x, y = transformer.transform(input_coord[1], input_coord[0])
    return (x, y)

def convert_from_utm(input_coord, transformer):
    lon, lat = transformer.transform(input_coord[0], input_coord[1], direction="INVERSE")
    return (lat, lon)

def rotate_utm(center_utm, point_utm, theta):
    dx = point_utm[0] - center_utm[0]
    dy = point_utm[1] - center_utm[1]
    x_rot = dx * math.cos(theta) - dy * math.sin(theta)
    y_rot = dx * math.sin(theta) + dy * math.cos(theta)
    return (x_rot + center_utm[0], y_rot + center_utm[1])

def align_to_axes(center_utm, point_utm, theta):
    return rotate_utm(center_utm, point_utm, -theta)

def rotate_back_to_field(center_utm, point_utm, theta):
    return rotate_utm(center_utm, point_utm, +theta)

def calc_center_transformer(tl_corner, tr_corner, bl_corner, br_corner):
    center_x = (tl_corner[0] + tr_corner[0] + bl_corner[0] + br_corner[0]) / 4
    center_y = (tl_corner[1] + tr_corner[1] + bl_corner[1] + br_corner[1]) / 4
    return center_x, center_y

#(separating funcs from main code)
'''
field_tl = """42°24'40.09"N 83°29'53.86"W"""
field_tr = """42°24'40.24"N 83°29'51.74"W"""
field_br = """42°24'36.70"N 83°29'51.28"W"""
field_bl = """42°24'36.55"N 83°29'53.41"W"""''' #northville high school field coordinates

field_tl = """40°46'23.2"N 74°01'10.5"W"""
field_tr = """40°46'22.63"N 74°01'10.05"W"""
field_br = """40°46'21.85"N 74°01'11.71"W"""
field_bl = """40°46'22.36"N 74°01'12.11"W"""
field_rand = """40°46'22.75"N 74°01'11.27"W"""

tl = convert_to_dec_degrees(field_tl)
tr = convert_to_dec_degrees(field_tr)
br = convert_to_dec_degrees(field_br)
bl = convert_to_dec_degrees(field_bl)
field_rand_1 = convert_to_dec_degrees(field_rand)

transformer = get_utm_transformer(tl)
tl_utm = convert_to_utm(tl, transformer)
tr_utm = convert_to_utm(tr, transformer)
br_utm = convert_to_utm(br, transformer)
bl_utm = convert_to_utm(bl, transformer)
field_rand_utm = convert_to_utm(field_rand_1, transformer)

center_utm = calc_center_transformer(tl_utm, tr_utm, bl_utm, br_utm)
theta = math.atan2(tr_utm[1] - tl_utm[1], tr_utm[0] - tl_utm[0])
print("Field tilt: ", math.degrees(theta))



tl_a = align_to_axes(center_utm, tl_utm, theta)
tr_a = align_to_axes(center_utm, tr_utm, theta)
bl_a = align_to_axes(center_utm, bl_utm, theta)
br_a = align_to_axes(center_utm, br_utm, theta)
field_rand_a = align_to_axes(field_rand_utm, br_utm, theta)

print(tl_a)
print(tr_a)
print(bl_a)
print(br_a)

tl_post = convert_from_utm(tl_a, transformer)
tr_post = convert_from_utm(tr_a, transformer)
bl_post = convert_from_utm(bl_a, transformer)
br_post = convert_from_utm(br_a, transformer)

print(tl_post)
print(tr_post)
print(bl_post)
print(br_post)

width_m  = ((tr_a[0] - tl_a[0]) + (br_a[0] - bl_a[0])) / 2
height_m = ((tl_a[1] - bl_a[1]) + (tr_a[1] - br_a[1])) / 2
print("Field width:  ", width_m)
print("Field height: ", height_m)

center_latlon = convert_from_utm(center_utm, transformer)
center_lat = center_latlon[0]
center_lon = center_latlon[1]

meters_per_deg_lat = 111132.0
meters_per_deg_lon = 111132.0 * math.cos(math.radians(center_lat))

half_lat = (height_m / 2) / meters_per_deg_lat
half_lon = (width_m  / 2) / meters_per_deg_lon

tl_final = (center_lat + half_lat, center_lon - half_lon)
tr_final = (center_lat + half_lat, center_lon + half_lon)
bl_final = (center_lat - half_lat, center_lon - half_lon)
br_final = (center_lat - half_lat, center_lon + half_lon)
field_rand_final = convert_from_utm(field_rand_a, transformer)


print(tl_final)
print(tr_final)
print(bl_final)
print(br_final)
print(field_rand_final)


'''
tr_rotated = align_coordinates(tl, tr, theta)
bl_rotated = align_coordinates(tl, bl, theta)
br_rotated = align_coordinates(tl, br, theta)

tl = convert_from_utm(tl, transformer)
tr = convert_from_utm(tr, transformer)
bl = convert_from_utm(bl, transformer)
br = convert_from_utm(br, transformer)

print(tr_rotated)
print(bl_rotated)
print(br_rotated) '''


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

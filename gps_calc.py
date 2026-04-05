import math
from pyproj import Transformer #run pip install pyproj

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

def rotate_point(pivot_utm, point_utm, theta):
    dx = point_utm[0] - pivot_utm[0]
    dy = point_utm[1] - pivot_utm[1]
    x_rot = dx * math.cos(theta) - dy * math.sin(theta)
    y_rot = dx * math.sin(theta) + dy * math.cos(theta)
    return (x_rot + pivot_utm[0], y_rot + pivot_utm[1])

def unrotate_point(pivot_utm, rotated_point_utm, theta):
    return rotate_point(pivot_utm, rotated_point_utm, -theta)

def calc_theta(tl_utm, tr_utm): #meant to be used w top left & top right
    return math.atan2(tr_utm[1] - tl_utm[1], tr_utm[0] - tl_utm[0])

def create_axis_aligned_rectangle(tl_utm, tr_utm, bl_utm, br_utm, theta):
    
    #calc avg width and height from orig corners
    width_m = (math.hypot(tr_utm[0] - tl_utm[0], tr_utm[1] - tl_utm[1]) + 
               math.hypot(br_utm[0] - bl_utm[0], br_utm[1] - bl_utm[1])) / 2
    height_m = (math.hypot(bl_utm[0] - tl_utm[0], bl_utm[1] - tl_utm[1]) + 
                math.hypot(br_utm[0] - tr_utm[0], br_utm[1] - tr_utm[1])) / 2
    
    # Create perfect axis-aligned rectangle
    # TL stays at original position
    # TR is directly east (+x direction)
    # BL is directly south (-y direction)
    tl_rect = tl_utm
    tr_rect = (tl_utm[0] + width_m, tl_utm[1])
    bl_rect = (tl_utm[0], tl_utm[1] - height_m)
    br_rect = (tl_utm[0] + width_m, tl_utm[1] - height_m)
    
    return tl_rect, tr_rect, bl_rect, br_rect, theta, width_m, height_m

def rotate_rectangle(tl_utm, tr_utm, bl_utm, br_utm, pivot_utm, theta):
    tl_rot = rotate_point(pivot_utm, tl_utm, theta)
    tr_rot = rotate_point(pivot_utm, tr_utm, theta)
    bl_rot = rotate_point(pivot_utm, bl_utm, theta)
    br_rot = rotate_point(pivot_utm, br_utm, theta)
    return tl_rot, tr_rot, bl_rot, br_rot

def align_corners_to_latlon(tl_latlon, tr_latlon, bl_latlon):
    #tl is same
    tl_aligned = tl_latlon
    
    #tr is tl's latitude, keeps its own longitude
    tr_aligned = (tl_latlon[0], tr_latlon[1])
    
    #bl is tl's longitude, keeps its own latitude
    bl_aligned = (bl_latlon[0], tl_latlon[1])
    
    #br is bl's latitude and tr's longitude
    br_aligned = (bl_latlon[0], tr_latlon[1])
    
    return tl_aligned, tr_aligned, br_aligned, bl_aligned

#(separating funcs from main code)

field_tl = """42°24'40.09"N 83°29'53.86"W"""
field_tr = """42°24'40.24"N 83°29'51.74"W"""
field_br = """42°24'36.70"N 83°29'51.28"W"""
field_bl = """42°24'36.55"N 83°29'53.41"W""" #northville high school field coordinates

'''field_tl = """40°46'23.2"N 74°01'10.5"W"""
field_tr = """40°46'22.63"N 74°01'10.05"W"""
field_br = """40°46'21.85"N 74°01'11.71"W"""
field_bl = """40°46'22.36"N 74°01'12.11"W"""'''

tl = convert_to_dec_degrees(field_tl)
tr = convert_to_dec_degrees(field_tr)
br = convert_to_dec_degrees(field_br)
bl = convert_to_dec_degrees(field_bl)

transformer = get_utm_transformer(tl)
tl_utm = convert_to_utm(tl, transformer)
tr_utm = convert_to_utm(tr, transformer)
br_utm = convert_to_utm(br, transformer)
bl_utm = convert_to_utm(bl, transformer)

#calc theta from tl-tr side
theta = calc_theta(tl_utm, tr_utm)
print("Field tilt (theta):", math.degrees(theta), " in degrees")

#create axis-aligned rectangle with same dimensions as original
tl_rect, tr_rect, bl_rect, br_rect, field_theta, width_m, height_m = create_axis_aligned_rectangle(tl_utm, tr_utm, bl_utm, br_utm, theta)

print("Field width:  ", width_m)
print("Field height: ", height_m)

print("\nAxis-aligned rectangle")
tl_latlon = convert_from_utm(tl_rect, transformer)
tr_latlon = convert_from_utm(tr_rect, transformer)
bl_latlon = convert_from_utm(bl_rect, transformer)
br_latlon = convert_from_utm(br_rect, transformer)
print(tl_latlon)
print(tr_latlon)
print(br_latlon)
print(bl_latlon)

tl_perf, tr_perf, br_perf, bl_perf = align_corners_to_latlon(tl_latlon, tr_latlon, bl_latlon)
print("Latitude/Longitude aligned corners: ")
print(tl_perf)
print(tr_perf)
print(br_perf)
print(bl_perf)

#test pt
field_rand = """42°24'38.61"N 83°29'51.52"W"""
field_rand_1 = convert_to_dec_degrees(field_rand)
field_rand_utm = convert_to_utm(field_rand_1, transformer)
#rotate
field_rand_rotated = rotate_point(tl_utm, field_rand_utm, theta)
field_rand_rotated_latlon = convert_from_utm(field_rand_rotated, transformer)
#unrotate
field_rand_back = unrotate_point(tl_utm, field_rand_rotated, theta)
field_rand_back_latlon = convert_from_utm(field_rand_back, transformer)
print("\nOriginal:    ", field_rand_1)
print("Rotated: ", field_rand_rotated_latlon)
print("Unrotated: ", field_rand_back_latlon)
print("Match: ", ((field_rand_utm[0] == field_rand_back[0]) and (field_rand_utm[1] == field_rand_back[1])))


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

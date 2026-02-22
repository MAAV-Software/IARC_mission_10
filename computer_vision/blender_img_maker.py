import bpy
import random

stl_filepath = "/Users/swatisahu/Documents/maav_software/IARC_PFM-1_mine.stl"

bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.import_mesh.stl(filepath=stl_filepath)
obj = bpy.context.object
obj.dimensions = [0.12, 0.061, 0.020]

rand_x = random.uniform(-2,2)
rand_y = random.uniform(-1,1)
z = 0.5

obj.location = (rand_x, rand_y, z)

output_filepath = "/Users/swatisahu/Desktop/maav/tutorial-img"
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.context.scene.render.filepath = output_filepath

bpy.ops.render.render(write_still=True)
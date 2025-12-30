import os
import shutil

images_path = "/Users/dervint/Desktop/Clubs/MAAV/pfm1-mines/training_images"
dest_path = "/Users/dervint/Desktop/Clubs/MAAV/networking/Networking_VM/images"

if os.path.exists(dest_path):
    shutil.rmtree(dest_path)
    os.mkdir(dest_path)
    print(f"Directory '{dest_path}' exist and cleard its contents!")
else:
    os.mkdir(dest_path)
    print(f"Directory '{dest_path}' did not exist and we created it now.")

shutil.move(images_path, dest_path)

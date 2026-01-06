import os
import argparse
import tifffile 

parser = argparse.ArgumentParser(description='Check dimensions of a tiff file against expected dimensions.')
parser.add_argument('img_path', type=str, help='Path to the tiff file to check.')

args = parser.parse_args()
img_name = args.img_path

image = tifffile.imread(img_name)
print('Image stack shape: ', image.shape)
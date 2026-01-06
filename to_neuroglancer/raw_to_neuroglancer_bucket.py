
''' Script to upload raw uncompressed image datasets to cloud bucket in neuroglancer-compatible format.

	adapted from https://github.com/seung-lab/cloud-volume/wiki/Example-Single-Machine-Dataset-Upload

'''

import os
# from concurrent.futures import ProcessPoolExecutor
import numpy as np
import tifffile 
from cloudvolume import CloudVolume
import argparse
# from cloudvolume.lib import mkdir, touch

parser = argparse.ArgumentParser(description='Upload raw image dataset to neuroglancer-compatible cloud volume.')
parser.add_argument('--img', type=str, help='Path to the tiff file to upload.')
parser.add_argument('--bucket', type=str, help='Cloud bucket path, e.g. gs://bucket/dataset/layer')
parser.add_argument('--description', type=str, help='Description of the dataset.')

args = parser.parse_args()
bucket_path = args.bucket
stack_description = args.description

# ---- path to raw image
img_name = args.img #'local/path/to/image.tif'

print(f'Uploading image {img_name} to bucket {bucket_path}')

# ---- create neuroglancer info file for dataset
info = CloudVolume.create_new_info(
	num_channels = 1,
	layer_type = 'image', # 'image' or 'segmentation'
	data_type = 'uint8', # can pick any popular uint ### picking uint8 over uint16 here because that's what d erecta is in ? 
	encoding = 'raw', # see: https://github.com/seung-lab/cloud-volume/wiki/Compression-Choices
	resolution = [ 8, 8, 8 ], # X,Y,Z values in nanometers
	voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
	chunk_size = [ 128, 128, 128 ], # rechunk of image X,Y,Z in voxels
	volume_size = [  1250, 1250, 672 ], # X,Y,Z size in voxels
)

# to work with RGB data, set num_channels=3 and data_type='uint8' above. need to also paste some code into neuroglancer 
# rendering box if using RGB, see https://github.com/seung-lab/cloud-volume/wiki/Example-Single-Machine-Dataset-Upload

# ---- create cloud volume object
# If you're using amazon or the local file system, you can replace 'gs' with 's3' or 'file'
vol = CloudVolume(bucket_path, info=info)
vol.provenance.description = stack_description
vol.provenance.owners = ['michael.winding@crick.ac.uk/mwinding']  #['email_address_for_uploader/imager'] # list of contact email addresses

vol.commit_info() # generates gs://bucket/dataset/layer/info json file
vol.commit_provenance() # generates gs://bucket/dataset/layer/provenance json file

# ---- process and upload image stack
# check file is a tif file 
def is_tif(filename):
	return filename.lower().endswith(('.tif', '.tiff'))

if not is_tif(img_name):
	raise ValueError('Input file is not a tiff file: ', img_name)

image = tifffile.imread(img_name)
print('Image stack shape: ', image.shape)

image = np.transpose(image, (2, 1, 0)) # from tif ZYX to neuroglancer XYZ
assert image.shape == (1250, 1250, 672)  # check image stack matches expected volume size above
assert image.dtype == np.uint8  # check image data type matches expected data type above

# upload image stack to cloud volume
vol[:,:,:] = image


# legacy batching for larger files 

# progress_dir = mkdir('progress/') # unlike os.mkdir doesn't crash on prexisting 
# done_files = set([ int(z) for z in os.listdir(progress_dir) ])
# all_files = set(range(vol.bounds.minpt.z, vol.bounds.maxpt.z + 1))

# to_upload = [ int(z) for z in list(all_files.difference(done_files)) ]
# to_upload.sort()

# # upload is stacked into z slices which only works if chunk size has z=1? 
# # so probably just run this once for each chunk, instead of iterating over z slices. 

# ''' Note: need to figgure out here whether we want to split into single z slices and use chunk_size 128 128 1
#  or whether to change code below to upload in chunks of 128 z slices at a time and subdivide the image loaded in earlier.'''

# def process(z):
# 	img_name = 'brain_%06d.tif' % z
# 	print('Processing ', img_name)
#     image = tifffile.imread(os.path.join(direct, img_name))
#     image = np.swapaxes(image, 0, 1)
#     image = image[..., np.newaxis]
#     vol[:,:, z] = image
# 	touch(os.path.join(progress_dir, str(z)))

# with ProcessPoolExecutor(max_workers=8) as executor:
#     executor.map(process, to_upload)

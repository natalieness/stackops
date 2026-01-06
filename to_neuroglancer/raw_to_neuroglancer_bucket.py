
''' Script to upload raw uncompressed image datasets to cloud bucket in neuroglancer-
    compatible format.

adapted from https://github.com/seung-lab/cloud-volume/wiki/Example-Single-Machine-Dataset-Upload
The resumable upload feature works by writing the index of uploaded slices to disk by 
touching filenames in a newly created ./progress/ directory. 
You can easily reset the upload with rm -r ./progress or avoid reuploading files by touching 
e.g. touch progress/5 which would avoid uploading z=5.

A curious feature of this script is that it uses ProcessPoolExecutor as an independent multi-process 
runner rather than using CloudVolume's parallel=True option. This is helpful because it helps 
parallelize the file reading and decoding step. ProcessPoolExecutor is used instead of multiprocessing.
Pool as the original multiprocessing module hangs when a child process dies.

'''

import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import tifffile 

from cloudvolume import CloudVolume
from cloudvolume.lib import mkdir, touch

info = CloudVolume.create_new_info(
	num_channels = 1,
	layer_type = 'image', # 'image' or 'segmentation'
	data_type = 'uint8', # can pick any popular uint ### picking uint8 over uint16 here because that's what d erecta is in ? 
	encoding = 'raw', # see: https://github.com/seung-lab/cloud-volume/wiki/Compression-Choices
	resolution = [ 8, 8, 8 ], # X,Y,Z values in nanometers
	voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
	chunk_size = [ 128, 128, 1 ], # rechunk of image X,Y,Z in voxels
	volume_size = [  1250, 1250, 672 ], # X,Y,Z size in voxels
)

# to work with RGB data, set num_channels=3 and data_type='uint8' above. need to also paste some code into neuroglancer 
# rendering box if using RGB, see https://github.com/seung-lab/cloud-volume/wiki/Example-Single-Machine-Dataset-Upload

# If you're using amazon or the local file system, you can replace 'gs' with 's3' or 'file'
vol = CloudVolume('gs://bucket/dataset/layer', info=info)
vol.provenance.description = "Description of Data"
vol.provenance.owners = ['email_address_for_uploader/imager'] # list of contact email addresses

vol.commit_info() # generates gs://bucket/dataset/layer/info json file
vol.commit_provenance() # generates gs://bucket/dataset/layer/provenance json file

direct = 'local/path/to/images'

progress_dir = mkdir('progress/') # unlike os.mkdir doesn't crash on prexisting 
done_files = set([ int(z) for z in os.listdir(progress_dir) ])
all_files = set(range(vol.bounds.minpt.z, vol.bounds.maxpt.z + 1))

to_upload = [ int(z) for z in list(all_files.difference(done_files)) ]
to_upload.sort()

# upload is stacked into z slices which only works if chunk size has z=1? 
# so probably just run this once for each chunk, instead of iterating over z slices. 

''' Note: need to figgure out here whether we want to split into single z slices and use chunk_size 128 128 1
 or whether to change code below to upload in chunks of 128 z slices at a time and subdivide the image loaded in earlier.'''

def process(z):
	img_name = 'brain_%06d.tif' % z
	print('Processing ', img_name)
    image = tifffile.imread(os.path.join(direct, img_name))
    image = np.swapaxes(image, 0, 1)
    image = image[..., np.newaxis]
    vol[:,:, z] = image
	touch(os.path.join(progress_dir, str(z)))

with ProcessPoolExecutor(max_workers=8) as executor:
    executor.map(process, to_upload)

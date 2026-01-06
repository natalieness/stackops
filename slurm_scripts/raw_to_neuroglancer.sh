#!/bin/bash
#SBATCH --job-name=raw_to_neuroglancer
#SBATCH --ntasks=1
#SBATCH --time=4-00:00:00
#SBATCH --cpus-per-task=4   
#SBATCH --mem=500G
#SBATCH --mail-user=natalie.ness@crick.ac.uk
#SBATCH --mail-type=FAIL,END

ml purge
ml Anaconda3
source ~/.bashrc

conda activate intheclouds

python ../to_neuroglancer/raw_to_neuroglancer_bucket.py "$@" 

# eg:
# sbatch raw_to_neuroglancer.sh --img path/to/image.tif --bucket gs://my-neuroglancer-bucket/dataset/layer --description "My Neuroglancer Dataset"
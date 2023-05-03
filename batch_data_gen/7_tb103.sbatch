#!/bin/bash

#SBATCH --job-name=rs-tb103
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16GB
#SBATCH --time=47:59:59
#SBATCH --mail-user=chris.ick@nyu.edu
#SBATCH --export=NONE
#SBATCH --output="outputs/o_tb103-%j.out"

source ~/.bashrc
module purge
module load anaconda3/2020.07

conda activate s3d_env

cd /home/ci411/synth_data_generator/
python sim_room.py 'tb103' --t-type='linear'
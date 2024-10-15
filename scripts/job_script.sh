#!/bin/bash

#PBS -P ce47
#PBS -q normal
#PBS -l ncpus=144
#PBS -l mem=256GB
#PBS -l jobfs=100GB
#PBS -l walltime=48:00:00
#PBS -l storage=scratch/ce47
#PBS -l wd
 
# Load modules, always specify version number.
module load nci-parallel/1.0.0a

export ncores_per_task=48
export ncores_per_node=48
 
mpirun -np $((PBS_NCPUS/ncores_per_task)) --map-by ppr:$((ncores_per_node/ncores_per_task)):NODE:PE=${ncores_per_task} nci-parallel --input-file cmds.txt


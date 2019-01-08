#!/bin/bash
#SBATCH -J predict
#SBATCH -D /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/mlFramework
#SBATCH -o log_%j.txt

python run_model.py -c $1 

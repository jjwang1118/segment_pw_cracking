#!/bin/bash
#SBATCH --account=mst115223
#SBATCH --job-name=pcfg_h200
#SBATCH --partition=normal2
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=20:00:00
#SBATCH --output=job-%j.out
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=114423002@cc.ncu.edu.tw

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

cd ~/llm_pcfg_cracking
source ~/miniconda3/etc/profile.d/conda.sh
conda activate llm_pcfg_cracking_model
python run_train.py

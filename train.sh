#!/bin/bash
#SBATCH --account=mst115223
#SBATCH --job-name=pcfg_train
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --gpus-per-node=3
#SBATCH --cpus-per-task=4
#SBATCH --time=20:00:00
#SBATCH --output=job-%j.out
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=114423002@cc.ncu.edu.tw

export TMPDIR=/work/u4996812/tmp
export HF_HOME=/work/u4996812/hf_cache
mkdir -p "$TMPDIR" "$HF_HOME"

cd ~/llm_pcfg_cracking
source ~/miniconda3/etc/profile.d/conda.sh
conda activate llm_pcfg_cracking_model
torchrun --nproc_per_node=3 run_train.py

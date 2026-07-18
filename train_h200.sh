#!/bin/bash
#SBATCH --account=mst115223
#SBATCH --job-name=pcfg_h200
#SBATCH --partition=normal2
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=48:00:00
#SBATCH --output=job-%j.out
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=114423002@cc.ncu.edu.tw

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

cd ~/llm_pcfg_cracking
source ~/miniconda3/etc/profile.d/conda.sh
conda activate llm_pcfg_cracking_model

# 若訓練中途被中斷（例如超過 --time 限制），可從最新的 checkpoint 續跑：
#   python run_train.py --resume checkpoints/<model_name>/run_N/checkpoint-XXXX
# 續訓會沿用同一個 run_N 目錄，接續原本的 optimizer/scheduler 狀態與剩餘 steps，
# 不會重新開始或重算 epoch（細節見 util/train.py 的 resume_from_checkpoint 邏輯）。
python run_train.py

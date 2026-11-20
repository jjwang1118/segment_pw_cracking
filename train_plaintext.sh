#!/bin/bash
#SBATCH --account=mst115223
#SBATCH --job-name=pcfg_plaintext
#SBATCH --partition=normal2
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=48:00:00
#SBATCH --output=job-%j.out
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=114423002@cc.ncu.edu.tw

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export TMPDIR=/work/u4996812/tmp
export HF_HOME=/work/u4996812/hf_cache
mkdir -p "$TMPDIR" "$HF_HOME"

cd ~/llm_pcfg_cracking
source ~/miniconda3/etc/profile.d/conda.sh
conda activate llm_pcfg_cracking_model

# 純 plaintext 無條件分布學習 (full fine-tune, 不使用 LoRA)
# 7B 全參數微調建議用單張大卡 (H200 141GB)；plain DDP (torchrun) 會在每張卡
# 複製 optimizer 狀態、無法省顯存，多卡分片需改用 FSDP / DeepSpeed ZeRO。
python run_train_plaintext.py --config config/train_plaintext.yaml

# 續訓：
#   python run_train_plaintext.py --resume checkpoints/Mistral-7B-v0.1-plaintext/run_N/checkpoint-XXXX

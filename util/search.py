## 實作constrative search
## 獨立kv cache

import re
import numpy as np
import torch
import math
import random
import time
import os
from queue import PriorityQueue
from collections import defaultdict,deque
from dataclasses import dataclass, field

import torch
from tqdm import tqdm


from transformers import AutoModelForCausalLM
from transformers.cache_utils import DynamicCache


def _reorder_cache(cache: DynamicCache, beam_idx: torch.Tensor) -> DynamicCache:
    """Reorder KV cache along batch dim (dim=0) according to beam indices."""
    if cache is None:
        return None
    idx = beam_idx.long()
    new = DynamicCache()
    for i, layer in enumerate(cache.layers):
        k = layer.keys.index_select(0, idx.to(layer.keys.device))
        v = layer.values.index_select(0, idx.to(layer.values.device))
        new.update(k, v, layer_idx=i)
    return new


def _expand_cache(cache: DynamicCache, batch_size: int) -> DynamicCache:
    """Broadcast a batch-size-1 KV cache to batch_size using expand (zero-copy view).
    Use instead of _reorder_cache(cache, zeros_tensor) to avoid copying the prompt KV cache
    batch_size times on every forward pass."""
    new = DynamicCache()
    for i, layer in enumerate(cache.layers):
        k = layer.keys.expand(batch_size, -1, -1, -1)
        v = layer.values.expand(batch_size, -1, -1, -1)
        new.update(k, v, layer_idx=i)
    return new


def _merge_cache(cache1: DynamicCache, cache2: DynamicCache) -> DynamicCache:
    """Concatenate two KV caches along batch dim (dim=0)."""
    if cache1 is None:
        return cache2
    new = DynamicCache()
    for i, (l1, l2) in enumerate(zip(cache1.layers, cache2.layers)):
        new.update(torch.cat([l1.keys, l2.keys], dim=0),
                   torch.cat([l1.values, l2.values], dim=0),
                   layer_idx=i)
    return new


def _cache_slice(cache: DynamicCache, indices: torch.Tensor) -> DynamicCache:
    """Slice KV cache along sequence dim (dim=2) using given indices."""
    new = DynamicCache()
    for i, layer in enumerate(cache.layers):
        new.update(layer.keys[:, :, indices, :],
                   layer.values[:, :, indices, :],
                   layer_idx=i)
    return new


def _cache_concat(head: DynamicCache, tail: DynamicCache) -> DynamicCache:
    """Concatenate two KV caches along sequence dim (dim=2)."""
    if tail is None:
        return head
    new = DynamicCache()
    for i, (l1, l2) in enumerate(zip(head.layers, tail.layers)):
        new.update(torch.cat([l1.keys, l2.keys], dim=2),
                   torch.cat([l1.values, l2.values], dim=2),
                   layer_idx=i)
    return new

def remap_logits(vocab, logits: torch.Tensor):
    '''
    vocab: list, custom vocabulary
    logits: tensor, raw model output logits of shape [batch_size, seq_length, primary_vocab_size]
    output: tensor, logits corresponding only to tokens in the provided vocabulary
    '''
    dtype, device = logits.dtype, logits.device
    # Keep only the logits corresponding to characters in the custom vocabulary, ignoring others
    filtered_logits = logits[:, :, vocab].to(device)
    return filtered_logits


@torch.no_grad()
def predict_next(model, vocab, input_ids, past_key_values=None):
    #predict and vocab limit
    #
    outputs = model.forward(
        input_ids=input_ids,
        past_key_values=past_key_values ,
        output_attentions=False,
        output_hidden_states=True,
        use_cache=True
    )
    logits = remap_logits(vocab, outputs.logits)[:, -1, :]
    word_prob = logits.log_softmax(dim=1)

    return word_prob, outputs.past_key_values , outputs.hidden_states




class DBS_Beam:
    """Pure beam search state (no contrastive penalty)."""
    def __init__(self, info_cache: DynamicCache, vocab_tensor: torch.Tensor, device):
        self.info_cache = info_cache
        self.pw_cache = None
        self.pw_idx = torch.empty(1, 0, device=device, dtype=torch.int)
        self.beam_prob = torch.zeros(1, 1, device=device, dtype=torch.double)
        self.search_prob = torch.zeros(1, 1, device=device, dtype=torch.double)
        self.vocab_tensor = vocab_tensor
        self.device = device

    def return_beam_width(self):
        return self.pw_idx.shape[0]

    def update_by_prob(self, beam_width, search_width: int, probs: torch.Tensor, pw_past_key_values):
        tot_probs = (self.beam_prob.reshape(-1, 1) + probs).reshape(-1)

        self.search_prob, search_idx = torch.topk(tot_probs, search_width, largest=True)
        self.beam_prob, _ = torch.topk(tot_probs, beam_width, largest=True)
        self.search_prob = self.search_prob.reshape(-1, 1)
        self.beam_prob = self.beam_prob.reshape(-1, 1)

        self.last_beam_index = search_idx // (self.vocab_tensor.shape[0] - 1)
        word_index = torch.remainder(search_idx, self.vocab_tensor.shape[0] - 1)

        self.pw_idx = torch.cat([
            self.pw_idx[self.last_beam_index],
            self.vocab_tensor[word_index].reshape(-1, 1)
        ], dim=1)

        self.pw_cache = pw_past_key_values


@torch.no_grad()
def dynamic_beam_search(
    model: AutoModelForCausalLM,
    input_ids: torch.Tensor,
    batch_size: int,
    beam_width_list: list,
    vocab: list,
    eos_threshold: float,
    search_width_list: list = [],
    sorted: bool = True,
    min_len: int = 0,
    seg_separator_id: int = None,
):
    """
    Dynamic beam search without contrastive penalty.
    Faster than contrastive_search; suitable for baseline comparison.
    """
    if not search_width_list:
        search_width_list = beam_width_list

    device = model.device
    eos_threshold = torch.tensor(math.log(eos_threshold), device=device)

    input_ids = input_ids.reshape(1, -1).to(device=device)
    reorder_info_cache_index = torch.zeros(batch_size, device=device, dtype=torch.int)

    max_length = len(beam_width_list)
    pw_silce_index = torch.arange(
        input_ids.shape[1], input_ids.shape[1] + max_length, device=device, dtype=torch.int
    )
    vocab_tensor = torch.tensor(vocab, device=device, dtype=torch.int)
    vocab_size = len(vocab)
    
    outputs = model.forward(
        input_ids=input_ids,
        past_key_values=DynamicCache(),
        use_cache=True,
        output_attentions=False,
    )
    logits = remap_logits(vocab_tensor, outputs.logits)[:, -1, :]
    info_cache = outputs.past_key_values
    del outputs

    word_probs = torch.nn.functional.log_softmax(logits, dim=1)
    eos_list = []
    word_probs = word_probs[:, :-1]

    pw_past_key_values = None
    beam = DBS_Beam(info_cache, vocab_tensor, device)
    beam_width_list[0] = min(beam_width_list[0], vocab_size - 1)
    for i in range(1, len(beam_width_list)):
        beam_width_list[i] = min(beam_width_list[i], beam_width_list[i - 1] * (vocab_size - 1))
    search_width_list[0] = min(search_width_list[0], vocab_size - 1)
    for i in range(1, len(search_width_list)):
        search_width_list[i] = min(search_width_list[i], beam_width_list[i - 1] * (vocab_size - 1))
    
    for l in range(max_length):
        reserve_width = max(beam_width_list[l], search_width_list[l])
        forward_num = math.ceil(reserve_width / batch_size)
        beam_forward_num = math.ceil(beam_width_list[l] / batch_size)

        beam.update_by_prob(beam_width_list[l], reserve_width, word_probs, pw_past_key_values)

        print(f"[layer {l+1:>2}/{max_length}] beams={beam_width_list[l]}, found={len(eos_list)}", flush=True)

        word_probs = torch.empty(0, vocab_size - 1, device=device)
        pw_past_key_values = None

        for i in range(forward_num):
            if i < beam_forward_num:
                start, end = i * batch_size, min((i + 1) * batch_size, beam_width_list[l])
            else:
                start = beam_width_list[l] + (i - beam_forward_num) * batch_size
                end = min(beam_width_list[l] + (i - beam_forward_num + 1) * batch_size, reserve_width)

            input_seqs = beam.pw_idx[start:end, :]
            input_ids = beam.pw_idx[start:end, -1:]

            cache = _cache_concat(
                _expand_cache(beam.info_cache, end - start),
                _reorder_cache(beam.pw_cache, beam.last_beam_index[start:end])
            )

            outputs = model.forward(
                input_ids=input_ids,
                past_key_values=cache,
                use_cache=True,
                output_attentions=False,
            )
            del cache
            logits = remap_logits(vocab_tensor, outputs.logits)[:, -1, :]
            batch_word_probs = torch.nn.functional.log_softmax(logits, dim=1)

            if i < beam_forward_num:
                batch_pw_past_key_values = _cache_slice(outputs.past_key_values, pw_silce_index[:l + 1])
                word_probs = torch.cat([word_probs, batch_word_probs[:, :-1]], dim=0)
                pw_past_key_values = _merge_cache(pw_past_key_values, batch_pw_past_key_values)

            del outputs

            batch_eos_over_threshold_index = (
                torch.where(batch_word_probs[:, -1] >= eos_threshold)[0]
                if l >= min_len - 1
                else torch.empty(0, dtype=torch.long, device=device)
            )
            if batch_eos_over_threshold_index.shape[0] != 0:
                eos_seqs = torch.cat([
                    input_seqs[batch_eos_over_threshold_index, :],
                    vocab_tensor[-1].repeat(batch_eos_over_threshold_index.shape[0], 1)
                ], dim=1)

                batch_eos_probs = (
                    beam.search_prob[start:end, :] + batch_word_probs[:, -1:]
                )[batch_eos_over_threshold_index]

                eos_list.extend(zip(eos_seqs, batch_eos_probs))

    if seg_separator_id is not None:
        sep_id = seg_separator_id
        stripped = []
        for seq, prob in eos_list:
            mask = seq != sep_id
            stripped.append((seq[mask], prob))
        eos_list = stripped

    if sorted:
        eos_list.sort(key=lambda x: x[1], reverse=True)

    return eos_list


class DBS_beam_contrastive_search:
    def __init__(self, info_cache: tuple, vocab_tensor: torch.Tensor, device, initial_hidden: torch.Tensor):
        """
        Args:
            info_cache: prompt 的 KV cache
            vocab_tensor: 詞彙表 tensor
            device: 設備
            initial_hidden: 初始 prompt 的 hidden state [1, hidden_dim]
        """
        self.info_cache = info_cache
        self.pw_cache = None
        self.pw_idx = torch.empty(1, 0, device=device, dtype=torch.int)
        self.beam_prob = torch.zeros(1, 1, device=device, dtype=torch.double)
        self.search_prob = torch.zeros(1, 1, device=device, dtype=torch.double)
        self.vocab_tensor = vocab_tensor
        self.device = device
        
        # 每個 beam 獨立的歷史: [beam_width, history_len, hidden_dim]
        # 初始時只有 1 個 beam，歷史長度為 1
        self.acc_hidden_state = initial_hidden.unsqueeze(1)  # [1, 1, hidden_dim]

    def return_beam_width(self):
        return self.pw_idx.shape[0]
    
    def accumulate_hidden(self, hidden_states: torch.Tensor):
        """
        為每個 beam 累積其對應的隱藏狀態
        
        Args:
            hidden_states: 當前步驟所有 beam 的隱藏狀態 [beam_width, hidden_dim]
        """
        # hidden_states: [beam_width, hidden_dim] -> [beam_width, 1, hidden_dim]
        new_hidden = hidden_states.unsqueeze(1)
        # 沿 history 維度拼接: [beam_width, history_len+1, hidden_dim]
        #水平拼接，沿著SEQ增加
        #沿著一為增加，對應自己的歷史紀錄
        self.acc_hidden_state = torch.cat([self.acc_hidden_state, new_hidden], dim=1)
        
    def compute_contrastive_penalty(self, current_hidden: torch.Tensor, beam_indices: torch.Tensor, alpha: float = 0.6):
        """
        基於每個 beam 自己的歷史隱藏狀態計算對比懲罰
        
        Args:
            current_hidden: 當前候選的隱藏狀態 [batch_size, hidden_dim]
            beam_indices: 每個候選對應的父 beam 索引 [batch_size]
            alpha: 對比懲罰權重
            
        Returns:
            penalty: 對比懲罰分數 [batch_size]
        """
        batch_size = current_hidden.shape[0]
        
        if self.acc_hidden_state.shape[1] == 0:
            # 沒有歷史記錄，返回零懲罰
            return torch.zeros(batch_size, device=current_hidden.device)
        
        # 取出每個候選對應的父 beam 的歷史 [batch_size, history_len, hidden_dim]
        beam_histories = self.acc_hidden_state[beam_indices]
        
        # 正規化當前隱藏狀態 [batch_size, hidden_dim]
        current_norm = torch.nn.functional.normalize(current_hidden, p=2, dim=-1)
        
        # 正規化歷史隱藏狀態 [batch_size, history_len, hidden_dim]
        history_norm = torch.nn.functional.normalize(beam_histories, p=2, dim=-1)
        
        # 計算餘弦相似度: [batch_size, hidden_dim] @ [batch_size, hidden_dim, history_len]
        # -> [batch_size, history_len]
        similarity = torch.bmm(
            current_norm.unsqueeze(1),  # [batch_size, 1, hidden_dim]
            history_norm.transpose(1, 2)  # [batch_size, hidden_dim, history_len]
        ).squeeze(1)  # [batch_size, history_len]
        
        # 對每個候選取最大相似度 [batch_size]
        max_similarity = similarity.max(dim=-1)[0]
        
        # 計算懲罰：penalty = alpha * max_similarity
        penalty = alpha * max_similarity
        
        return penalty

    def update_by_prob(self, beam_width, search_width: int, probs: torch.Tensor, pw_past_key_values, hidden_states: torch.Tensor = None):
        """
        Update beam state based on probability
        
        Args:
            beam_width: 保留的 beam 數量
            search_width: 搜索寬度
            probs: 機率分數 [current_beam_width, vocab_size-1]
            pw_past_key_values: KV cache
            hidden_states: 當前步驟的 hidden states [current_beam_width, hidden_dim]
        """

        tot_probs = (self.beam_prob.reshape(-1, 1) + probs).reshape(-1)


        self.search_prob, self.search_idx = torch.topk(tot_probs, search_width, largest=True)
 
        self.beam_prob, self.beam_idx = torch.topk(tot_probs, beam_width, largest=True)
        self.search_prob = self.search_prob.reshape(-1, 1)
        self.beam_prob = self.beam_prob.reshape(-1, 1)

        self.last_beam_index = self.search_idx // (self.vocab_tensor.shape[0] - 1)  # Subtract 1 to remove the EOS token
        word_index = torch.remainder(self.search_idx, self.vocab_tensor.shape[0] - 1)
        
        self.beam_parent_index = self.beam_idx // (self.vocab_tensor.shape[0] - 1)


        self.pw_idx = torch.cat([
            self.pw_idx[self.last_beam_index],
            self.vocab_tensor[word_index].reshape(-1, 1)
        ], dim=1)

        self.pw_cache = pw_past_key_values
        
  
        if hidden_states is not None:

            self.acc_hidden_state = self.acc_hidden_state[self.beam_parent_index]
            
            # 取出被選中的 beam 對應的 hidden states 並累積
            # self.beam_idx 對應到的父節點 
            selected_hidden = hidden_states[self.beam_parent_index]  # [beam_width, hidden_dim]
            self.accumulate_hidden(selected_hidden)
        else:

            self.acc_hidden_state = self.acc_hidden_state.expand(beam_width, -1, -1).clone()
        
@torch.no_grad()
def contrastive_search(
    model: AutoModelForCausalLM,
    input_ids: torch.Tensor,
    batch_size: int,
    beam_width_list: list = None,
    vocab: list = None,
    eos_threshold: float = 0.001,
    threshold: float = None,
    max_length: int = None,
    search_width_list: list = [],
    sorted: bool = True,
    use_contrastive: bool = True,
    contrastive_alpha: float = 0.6,
    top_k: int = None,
    use_prefix_control: bool = False,
    control_id: int = None,
    min_len: int = 0,
    seg_separator_id: int = None,
):
    """
    Contrastive Search: 使用 threshold-based 搜索生成大量候選，再用 contrastive penalty 重新排序。
    
    Args:
        model: 語言模型
        input_ids: prompt 的 input_ids
        batch_size: 批次大小
        beam_width_list: beam 寬度列表 (如果提供，使用 dynamic_beam_search)
        vocab: 詞彙表
        eos_threshold: EOS 閾值
        threshold: 機率閾值 (用於 _width_search，可生成百萬級密碼)
        max_length: 最大長度
        search_width_list: search 寬度列表
        sorted: 是否排序
        use_contrastive: 是否使用 contrastive reranking
        contrastive_alpha: contrastive penalty 強度
        top_k: 只返回前 k 個結果
        use_prefix_control: 是否使用 prefix 控制
        control_id: prefix 控制的 ID
    Returns:
        candidates: 排序後的候選列表
    """
    if not search_width_list:
        search_width_list = beam_width_list

    device = model.device
    eos_threshold = torch.tensor(math.log(eos_threshold), device=device)

    input_ids = input_ids.reshape(1, -1).to(device=device)
    reorder_info_cache_index = torch.zeros(batch_size, device=device, dtype=torch.int)
    prefix_cache = model.get_past_from_prefix([control_id]) if use_prefix_control else None

    # 如果 beam_width_list 為 None，使用 max_length 和預設 beam_width 自動生成
    if beam_width_list is None:
        if max_length is None:
            raise ValueError("beam_width_list 和 max_length 不能同時為 None")
        default_beam_width = 100  # 預設 beam 寬度
        beam_width_list = [default_beam_width] * max_length
        if not search_width_list:
            search_width_list = beam_width_list
    
    max_length = len(beam_width_list)
    #.shape[2] key_0  (batch, heads, prefix_len, head_dim)
    prefix_len = prefix_cache[0][0].shape[2] if use_prefix_control else 0 
    # 注入 prefix 後，info_cache 的序列長度是 prefix_len + prompt_len
    pw_silce_index = torch.arange(
        prefix_len+input_ids.shape[1], prefix_len+input_ids.shape[1] + max_length, device=device, dtype=torch.int
    )
    vocab_tensor = torch.tensor(vocab, device=device, dtype=torch.int)
    vocab_size = len(vocab)
    
    # 調整 beam_width_list：第一層受詞彙表限制，後續層受前一層 beam 數量限制
    # 第0層：最多 vocab_size-1 個候選（去掉 EOS）
    beam_width_list[0] = min(beam_width_list[0], vocab_size - 1)
    
    # 第i層：最多 beam_width[i-1] × (vocab_size-1) 個候選
    for i in range(1, len(beam_width_list)):
        max_candidates = beam_width_list[i-1] * (vocab_size - 1)
        beam_width_list[i] = min(beam_width_list[i], max_candidates)
    
    # 同樣調整 search_width_list
    if search_width_list:
        search_width_list[0] = min(search_width_list[0], vocab_size - 1)
        for i in range(1, len(search_width_list)):
            max_candidates = beam_width_list[i-1] * (vocab_size - 1)
            search_width_list[i] = min(search_width_list[i], max_candidates)


    #Get the auxiliary information  cache
    outputs = model.forward(
        input_ids=input_ids,
        past_key_values=prefix_cache if prefix_cache is not None else DynamicCache(),  # ← 改這行
        use_cache=True,
        output_attentions=False,
        output_hidden_states=True,
    )
    info_cache = outputs.past_key_values
    logits = remap_logits(vocab_tensor, outputs.logits)[:, -1, :]
    
    # 儲存初始 prompt 的 hidden state 用於對比搜索
    initial_hidden = outputs.hidden_states[-1][:, -1, :]
    
    del outputs

    word_probs = torch.nn.functional.log_softmax(logits, dim=1)
    eos_list = []
    word_probs = word_probs[:, :-1]
    pw_past_key_values = None
    
    # 用初始 hidden state 創建 beam
    beam = DBS_beam_contrastive_search(info_cache, vocab_tensor, device, initial_hidden)
    
    # 第一層：使用初始 word_probs 更新 beam
    reserve_width = max(beam_width_list[0], search_width_list[0])
    beam.update_by_prob(beam_width_list[0], reserve_width, word_probs, pw_past_key_values)
    
    for l in range(max_length):
        #Divide the beam width into multiple batches and perform forward passes sequentially.
        reserve_width = max(beam_width_list[l], search_width_list[l])
        #計算總共需要多少個batch
        forward_num = math.ceil(reserve_width / batch_size)
        # 計算需要多少次forward
        beam_forward_num = math.ceil(beam_width_list[l] / batch_size)

        print(f"[layer {l+1:>2}/{max_length}] beams={beam_width_list[l]}, found={len(eos_list)}", flush=True)
        
        word_probs = torch.empty(0, vocab_size - 1, device=device)
        pw_past_key_values = None
        hidden_states_batch = []  # 收集當前步驟的 hidden states
        
        for i in range(forward_num):
            if i < beam_forward_num:
                start, end = i * batch_size, min((i + 1) * batch_size, beam_width_list[l])
            else:
                start = beam_width_list[l] + (i - beam_forward_num) * batch_size
                end = min(beam_width_list[l] + (i - beam_forward_num + 1) * batch_size, reserve_width)

            input_seqs = beam.pw_idx[start:end, :]
            input_ids = beam.pw_idx[start:end, -1:]

            cache_beam_indices = beam.last_beam_index[start:end]
            need_hidden = use_contrastive and i < beam_forward_num

            # Use expand (zero-copy view) for info_cache broadcast instead of
            # index_select with all-zero indices, which would copy the full
            # prompt KV cache batch_size times on every forward pass.
            cache = _cache_concat(
                _expand_cache(beam.info_cache, end - start),
                _reorder_cache(beam.pw_cache, cache_beam_indices)
            )

            outputs = model.forward(
                input_ids=input_ids,
                past_key_values=cache,
                use_cache=True,
                output_attentions=False,
                output_hidden_states=need_hidden,
            )

            del cache

            if need_hidden:
                current_hidden = outputs.hidden_states[-1][:, -1, :]
                current_beam_indices = torch.arange(start, end, device=device)
                penalty = beam.compute_contrastive_penalty(current_hidden, current_beam_indices, contrastive_alpha)
                hidden_states_batch.append(current_hidden)
            else:
                penalty = torch.zeros(end - start, device=device)

            logits = remap_logits(vocab_tensor, outputs.logits)[:, -1, :]
            batch_word_probs = torch.nn.functional.log_softmax(logits, dim=1)
            batch_word_probs[:, :-1] = (1 - contrastive_alpha) * batch_word_probs[:, :-1] - penalty.unsqueeze(1)

            if i < beam_forward_num:
                batch_pw_past_key_values = _cache_slice(outputs.past_key_values, pw_silce_index[:l + 1])
                word_probs = torch.cat([word_probs, batch_word_probs[:, :-1]], dim=0)
                pw_past_key_values = _merge_cache(pw_past_key_values, batch_pw_past_key_values)

            del outputs

            # 未達最小長度時不允許 EOS
            batch_eos_over_threshold_index = (
                torch.where(batch_word_probs[:, -1] >= eos_threshold)[0]
                if l >= min_len - 1
                else torch.empty(0, dtype=torch.long, device=device)
            )
            if batch_eos_over_threshold_index.shape[0] != 0:
                eos_seqs = torch.cat([
                    input_seqs[batch_eos_over_threshold_index, :],
                    vocab_tensor[-1].repeat(batch_eos_over_threshold_index.shape[0], 1)
                ], dim=1)

                batch_eos_probs = (
                    beam.search_prob[start:end, :] + batch_word_probs[:, -1:]
                )[batch_eos_over_threshold_index]

                eos_list.extend(zip(eos_seqs,batch_eos_probs))

        next_l = l + 1
        if next_l < max_length:
            next_beam_width = beam_width_list[next_l]
            next_reserve_width = max(beam_width_list[next_l], search_width_list[next_l])
            if len(hidden_states_batch) > 0:
                all_hidden = torch.cat(hidden_states_batch, dim=0)  # [beam_width, hidden_dim]
                beam.update_by_prob(next_beam_width, next_reserve_width, word_probs, pw_past_key_values, all_hidden)
            else:
                beam.update_by_prob(next_beam_width, next_reserve_width, word_probs, pw_past_key_values)

    # id=4: strip newline segment-separator tokens before returning
    if seg_separator_id is not None:
        sep_id = seg_separator_id
        stripped = []
        for seq, prob in eos_list:
            mask = seq != sep_id
            stripped.append((seq[mask], prob))
        eos_list = stripped

    if sorted:
        eos_list.sort(key=lambda x: x[1], reverse=True)

    return eos_list


# ── Constrained Decoding ──────────────────────────────────────────────────────

def build_step_constraints(tags_str: str, vocab_dict: dict, eos_id: int):
    """
    Parse a pipe-separated Tags string into per-step allowed char token ID lists.

    Supports only backoff structural tags: numberN, charN, specialN, mixedN.
    Each tag is expanded into N identical steps (one per character position).

    Returns:
        (step_char_ids, total_length)
            step_char_ids: List[List[int]] — allowed token IDs at each step (no EOS)
            total_length:  int             — total password character count

        (None, None) if any tag is not a backoff structural tag (pos/semantic tag
        has no encoded length → constrained decoding cannot be applied).

    Args:
        tags_str:   pipe-separated tag string, e.g. "char5|number3|special1"
        vocab_dict: char → tokenizer_id mapping from get_alpa()
        eos_id:     EOS token ID from tokenizer
    """
    digit_ids   = [tid for c, tid in vocab_dict.items() if c.isdigit()]
    alpha_ids   = [tid for c, tid in vocab_dict.items() if c.isalpha()]
    special_ids = [tid for c, tid in vocab_dict.items() if not c.isalnum()]
    any_ids     = list(vocab_dict.values())

    _class_map = {
        'number':  digit_ids,
        'char':    alpha_ids,
        'special': special_ids,
        'mixed':   any_ids,
    }

    step_char_ids = []
    for tag in tags_str.split("|"):
        m = re.fullmatch(r'(number|char|special|mixed)(\d+)', tag)
        if not m:
            return None, None
        kind, n = m.group(1), int(m.group(2))
        step_char_ids.extend([_class_map[kind]] * n)

    return step_char_ids, len(step_char_ids)


@torch.no_grad()
def dynamic_beam_search_Constrained_Decoding(
    model: AutoModelForCausalLM,
    input_ids: torch.Tensor,
    tags_str: str,
    vocab_dict: dict,
    eos_id: int,
    batch_size: int = 1000,
    beam_width: int = 1000,
    search_width: int = None,
    sorted_results: bool = True,
):
    """
    Constrained beam search that hard-enforces character class and exact length.

    At each generation step l, only tokens whose character belongs to the current
    segment's class are admitted into the beam (digit / alpha / special / any).
    EOS is never allowed mid-sequence; at the final step all surviving beams are
    forced to emit EOS, guaranteeing every candidate has exactly the correct length.

    Only works when every tag in tags_str is a backoff structural tag
    (numberN / charN / specialN / mixedN).  Raises ValueError otherwise — the
    caller should fall back to the unconstrained search in that case.

    Args:
        model:          loaded AutoModelForCausalLM
        input_ids:      tokenised prompt  [1, prompt_len]
        tags_str:       pipe-separated Tags field, e.g. "char5|number3|special1"
        vocab_dict:     char → tokenizer_id mapping (from get_alpa())
        eos_id:         tokenizer.eos_token_id
        batch_size:     max beams per forward pass
        beam_width:     target beam width (capped per step by char-class size)
        search_width:   search beam width; defaults to beam_width
        sorted_results: sort output by log-prob descending

    Returns:
        list of (seq_tensor, log_prob_scalar) tuples, sorted by prob descending.
    """
    step_char_ids, total_length = build_step_constraints(tags_str, vocab_dict, eos_id)
    if step_char_ids is None:
        raise ValueError(
            f"Constrained decoding requires all-backoff tags "
            f"(numberN / charN / specialN / mixedN).  Got: {tags_str!r}"
        )

    if search_width is None:
        search_width = beam_width

    device = model.device
    input_ids = input_ids.reshape(1, -1).to(device=device)
    reorder_info_cache_index = torch.zeros(batch_size, device=device, dtype=torch.int)

    # KV-cache slice indices for the password portion (positions after the prompt)
    pw_slice_index = torch.arange(
        input_ids.shape[1], input_ids.shape[1] + total_length,
        device=device, dtype=torch.int
    )

    # Pre-build per-step vocab tensors: [char_ids..., eos_id]
    # EOS lives at index -1 (consistent with unconstrained search convention)
    step_vocab_tensors = [
        torch.tensor(ids + [eos_id], device=device, dtype=torch.int)
        for ids in step_char_ids
    ]

    # Beam / search widths per step, capped by the branching factor at each step.
    # step_bws[l] <= step_bws[l-1] * len(step_char_ids[l])
    step_bws = [min(beam_width,   len(step_char_ids[0]))]
    step_sws = [min(search_width, len(step_char_ids[0]))]
    for l in range(1, total_length):
        n = len(step_char_ids[l])
        step_bws.append(min(beam_width,   step_bws[l - 1] * n))
        step_sws.append(min(search_width, step_bws[l - 1] * n))

    # ── Initial forward pass on prompt ────────────────────────────────────────
    # Predict the first password character using step-0 char-class vocab.
    step0_vtensor = step_vocab_tensors[0]
    outputs = model.forward(
        input_ids=input_ids,
        past_key_values=DynamicCache(),
        use_cache=True,
        output_attentions=False,
    )
    logits     = remap_logits(step0_vtensor, outputs.logits)[:, -1, :]
    info_cache = outputs.past_key_values
    del outputs

    # Exclude EOS column (index -1); shape [1, |step0_chars|]
    word_probs = torch.nn.functional.log_softmax(logits, dim=1)[:, :-1]

    eos_list           = []
    pw_past_key_values = None
    beam = DBS_Beam(info_cache, step0_vtensor, device)

    # ── Main loop ─────────────────────────────────────────────────────────────
    for l in range(total_length):
        cur_vtensor  = step_vocab_tensors[l]
        bw           = step_bws[l]
        sw           = step_sws[l]
        reserve_width    = max(bw, sw)
        forward_num      = math.ceil(reserve_width / batch_size)
        beam_forward_num = math.ceil(bw / batch_size)
        is_last_step     = (l == total_length - 1)

        # Update beam's vocab tensor so index arithmetic in update_by_prob
        # uses the current step's char-class size (vocab_tensor.shape[0] - 1).
        beam.vocab_tensor = cur_vtensor
        beam.update_by_prob(bw, reserve_width, word_probs, pw_past_key_values)

        print(f"[layer {l+1:>2}/{total_length}] beams={bw}, found={len(eos_list)}", flush=True)

        # Prepare accumulators for next step's word_probs (not needed at last step)
        if not is_last_step:
            next_vtensor = step_vocab_tensors[l + 1]
            next_n_chars = len(step_char_ids[l + 1])
            word_probs   = torch.empty(0, next_n_chars, device=device)
        pw_past_key_values = None

        # ── Batch forward passes ──────────────────────────────────────────────
        for i in range(forward_num):
            if i < beam_forward_num:
                start, end = i * batch_size, min((i + 1) * batch_size, bw)
            else:
                start = bw + (i - beam_forward_num) * batch_size
                end   = min(bw + (i - beam_forward_num + 1) * batch_size, reserve_width)

            input_seqs    = beam.pw_idx[start:end, :]    # [batch, l+1]
            fwd_input_ids = beam.pw_idx[start:end, -1:]  # [batch, 1]

            cache = _cache_concat(
                _expand_cache(beam.info_cache, end - start),
                _reorder_cache(beam.pw_cache,  beam.last_beam_index[start:end])
            )
            outputs = model.forward(
                input_ids=fwd_input_ids,
                past_key_values=cache,
                use_cache=True,
                output_attentions=False,
            )
            del cache

            if is_last_step:
                # All beams have generated exactly total_length chars.
                # Force EOS for every surviving beam; use full-vocab log_softmax
                # so P(EOS) is properly normalised for probability-based ranking.
                eos_log_probs = torch.nn.functional.log_softmax(
                    outputs.logits[:, -1, :], dim=-1
                )[:, eos_id]  # [batch]

                eos_seqs = torch.cat([
                    input_seqs,
                    torch.full((input_seqs.shape[0], 1), eos_id,
                               device=device, dtype=torch.int)
                ], dim=1)
                batch_eos_probs = (
                    beam.search_prob[start:end, 0] + eos_log_probs
                ).unsqueeze(1)
                eos_list.extend(zip(eos_seqs, batch_eos_probs))

            else:
                # Remap logits to NEXT step's char-class vocab for continued search.
                # EOS is suppressed: never collected mid-sequence.
                logits = remap_logits(next_vtensor, outputs.logits)[:, -1, :]
                batch_word_probs = torch.nn.functional.log_softmax(logits, dim=1)

                if i < beam_forward_num:
                    batch_pw = _cache_slice(
                        outputs.past_key_values, pw_slice_index[:l + 1]
                    )
                    # Exclude EOS column before accumulating
                    word_probs = torch.cat(
                        [word_probs, batch_word_probs[:, :-1]], dim=0
                    )
                    pw_past_key_values = _merge_cache(pw_past_key_values, batch_pw)

            del outputs

    if sorted_results:
        eos_list.sort(key=lambda x: x[1], reverse=True)

    return eos_list


@torch.no_grad()
def contrastive_search_Constrained_Decoding(
    model: AutoModelForCausalLM,
    input_ids: torch.Tensor,
    tags_str: str,
    vocab_dict: dict,
    eos_id: int,
    batch_size: int = 100,
    beam_width: int = 1000,
    search_width: int = None,
    sorted_results: bool = True,
    use_contrastive: bool = True,
    contrastive_alpha: float = 0.6,
):
    """
    Constrained contrastive beam search: hard-enforces character class and exact password
    length (like dynamic_beam_search_Constrained_Decoding) while applying a per-beam
    hidden-state diversity penalty (like contrastive_search).

    At each step l only tokens from the current segment's class (digit/alpha/special/any)
    are admitted.  EOS is never allowed mid-sequence; at the final step all surviving beams
    are forced to emit EOS so every candidate has exactly the correct length.

    When use_contrastive=False this degrades to dynamic_beam_search_Constrained_Decoding.
    Raises ValueError if tags_str contains any pos/semantic tag.

    Args:
        model:             loaded AutoModelForCausalLM
        input_ids:         tokenised prompt  [1, prompt_len]
        tags_str:          pipe-separated Tags, e.g. "char5|number3|special1"
        vocab_dict:        char → tokenizer_id mapping (from get_alpa())
        eos_id:            tokenizer.eos_token_id
        batch_size:        max beams per forward pass
        beam_width:        target beam width (capped per step by char-class size)
        search_width:      search beam width; defaults to beam_width
        sorted_results:    sort output by log-prob descending
        use_contrastive:   enable hidden-state diversity penalty
        contrastive_alpha: penalty weight α  (score = (1-α)·logP − α·max_cos_sim)
    """
    if not use_contrastive:
        return dynamic_beam_search_Constrained_Decoding(
            model=model, input_ids=input_ids, tags_str=tags_str,
            vocab_dict=vocab_dict, eos_id=eos_id, batch_size=batch_size,
            beam_width=beam_width, search_width=search_width,
            sorted_results=sorted_results,
        )

    step_char_ids, total_length = build_step_constraints(tags_str, vocab_dict, eos_id)
    if step_char_ids is None:
        raise ValueError(
            f"Constrained decoding requires all-backoff tags "
            f"(numberN / charN / specialN / mixedN).  Got: {tags_str!r}"
        )

    if search_width is None:
        search_width = beam_width

    device = model.device
    input_ids = input_ids.reshape(1, -1).to(device=device)

    pw_slice_index = torch.arange(
        input_ids.shape[1], input_ids.shape[1] + total_length,
        device=device, dtype=torch.int
    )

    step_vocab_tensors = [
        torch.tensor(ids + [eos_id], device=device, dtype=torch.int)
        for ids in step_char_ids
    ]

    # Per-step beam/search widths, capped by branching factor
    step_bws = [min(beam_width,   len(step_char_ids[0]))]
    step_sws = [min(search_width, len(step_char_ids[0]))]
    for l in range(1, total_length):
        n = len(step_char_ids[l])
        step_bws.append(min(beam_width,   step_bws[l - 1] * n))
        step_sws.append(min(search_width, step_bws[l - 1] * n))

    # ── Initial forward pass on prompt ────────────────────────────────────────
    step0_vtensor = step_vocab_tensors[0]
    outputs = model.forward(
        input_ids=input_ids,
        past_key_values=DynamicCache(),
        use_cache=True,
        output_attentions=False,
        output_hidden_states=True,
    )
    info_cache    = outputs.past_key_values
    logits        = remap_logits(step0_vtensor, outputs.logits)[:, -1, :]
    initial_hidden = outputs.hidden_states[-1][:, -1, :]  # [1, hidden_dim]
    del outputs

    word_probs = torch.nn.functional.log_softmax(logits, dim=1)[:, :-1]

    eos_list           = []
    pw_past_key_values = None
    beam = DBS_beam_contrastive_search(info_cache, step0_vtensor, device, initial_hidden)

    # Initial beam expansion using step-0 word_probs (no hidden states yet)
    bw0 = step_bws[0]
    sw0 = step_sws[0]
    beam.vocab_tensor = step0_vtensor
    beam.update_by_prob(bw0, max(bw0, sw0), word_probs, None)

    # ── Main loop ─────────────────────────────────────────────────────────────
    for l in range(total_length):
        bw           = step_bws[l]
        sw           = step_sws[l]
        reserve_width    = max(bw, sw)
        forward_num      = math.ceil(reserve_width / batch_size)
        beam_forward_num = math.ceil(bw / batch_size)
        is_last_step     = (l == total_length - 1)

        print(f"[layer {l+1:>2}/{total_length}] beams={bw}, found={len(eos_list)}", flush=True)

        if not is_last_step:
            next_vtensor = step_vocab_tensors[l + 1]
            next_n_chars = len(step_char_ids[l + 1])
            word_probs   = torch.empty(0, next_n_chars, device=device)
        pw_past_key_values = None
        hidden_states_batch = []

        for i in range(forward_num):
            if i < beam_forward_num:
                start, end = i * batch_size, min((i + 1) * batch_size, bw)
            else:
                start = bw + (i - beam_forward_num) * batch_size
                end   = min(bw + (i - beam_forward_num + 1) * batch_size, reserve_width)

            input_seqs    = beam.pw_idx[start:end, :]
            fwd_input_ids = beam.pw_idx[start:end, -1:]
            # Only beam-width batches need hidden states; skip for last step too.
            need_hidden = (i < beam_forward_num) and (not is_last_step)

            cache = _cache_concat(
                _expand_cache(beam.info_cache, end - start),
                _reorder_cache(beam.pw_cache, beam.last_beam_index[start:end])
            )
            outputs = model.forward(
                input_ids=fwd_input_ids,
                past_key_values=cache,
                use_cache=True,
                output_attentions=False,
                output_hidden_states=need_hidden,
            )
            del cache

            if is_last_step:
                # Force EOS for every surviving beam; use full-vocab log_softmax so
                # P(EOS) is properly normalised for probability-based ranking.
                eos_log_probs = torch.nn.functional.log_softmax(
                    outputs.logits[:, -1, :], dim=-1
                )[:, eos_id]
                eos_seqs = torch.cat([
                    input_seqs,
                    torch.full((input_seqs.shape[0], 1), eos_id,
                               device=device, dtype=torch.int)
                ], dim=1)
                batch_eos_probs = (
                    beam.search_prob[start:end, 0] + eos_log_probs
                ).unsqueeze(1)
                eos_list.extend(zip(eos_seqs, batch_eos_probs))
            else:
                # Contrastive penalty (beam batches only)
                if need_hidden:
                    current_hidden = outputs.hidden_states[-1][:, -1, :]
                    current_beam_indices = torch.arange(start, end, device=device)
                    penalty = beam.compute_contrastive_penalty(
                        current_hidden, current_beam_indices, contrastive_alpha
                    )
                    hidden_states_batch.append(current_hidden)
                else:
                    penalty = torch.zeros(end - start, device=device)

                # Remap logits to NEXT step's char-class vocab; EOS is suppressed.
                logits = remap_logits(next_vtensor, outputs.logits)[:, -1, :]
                batch_word_probs = torch.nn.functional.log_softmax(logits, dim=1)

                if need_hidden:
                    batch_word_probs[:, :-1] = (
                        (1 - contrastive_alpha) * batch_word_probs[:, :-1]
                        - penalty.unsqueeze(1)
                    )

                if i < beam_forward_num:
                    batch_pw = _cache_slice(
                        outputs.past_key_values, pw_slice_index[:l + 1]
                    )
                    word_probs = torch.cat(
                        [word_probs, batch_word_probs[:, :-1]], dim=0
                    )
                    pw_past_key_values = _merge_cache(pw_past_key_values, batch_pw)

            del outputs

        # Update beam for the next step
        if not is_last_step:
            next_bw  = step_bws[l + 1]
            next_sw  = step_sws[l + 1]
            next_reserve = max(next_bw, next_sw)
            beam.vocab_tensor = step_vocab_tensors[l + 1]
            if hidden_states_batch:
                all_hidden = torch.cat(hidden_states_batch, dim=0)  # [bw, hidden_dim]
                beam.update_by_prob(next_bw, next_reserve, word_probs,
                                    pw_past_key_values, all_hidden)
            else:
                beam.update_by_prob(next_bw, next_reserve, word_probs,
                                    pw_past_key_values)

    if sorted_results:
        eos_list.sort(key=lambda x: x[1], reverse=True)

    return eos_list

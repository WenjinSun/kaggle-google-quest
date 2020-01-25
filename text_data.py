import numpy as np
import random
import torch
from torch.utils.data import Dataset

from common import N_TARGETS


class TextDataset(Dataset):

    def __init__(self, question_data, answer_data, title_data, category_data, 
                 host_data, use_embeddings, dist_features, idxs, targets=None):
        self.question_data = question_data[idxs].astype(np.long)
        self.answer_data = answer_data[idxs].astype(np.long)
        self.title_data = title_data[idxs].astype(np.long)
        self.category_data = category_data[idxs].astype(np.long)
        self.host_data = host_data[idxs].astype(np.long)
        self.use_embeddings_q = use_embeddings['question_body_embedding'][idxs].astype(np.float32)
        self.use_embeddings_a = use_embeddings['answer_embedding'][idxs].astype(np.float32)
        self.use_embeddings_t = use_embeddings['question_title_embedding'][idxs].astype(np.float32)
        self.dist_features = dist_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.question_data.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        question = self.question_data[idx]
        answer = self.answer_data[idx]
        title = self.title_data[idx]
        category = self.category_data[idx]
        host = self.host_data[idx]
        use_emb_q = self.use_embeddings_q[idx]
        use_emb_a = self.use_embeddings_a[idx]
        use_emb_t = self.use_embeddings_t[idx]
        dist_feature = self.dist_features[idx]
        target = self.targets[idx]

        return (question, answer, title, category, host, use_emb_q, use_emb_a, 
                use_emb_t, dist_feature), target

    def __len__(self):
        return len(self.question_data)

class TextDataset2(Dataset):

    def __init__(self, x_features, x_question_emb, x_answer_emb, x_title_emb, 
                 question_ids, answer_ids, title_ids, idxs, targets=None):
        self.question_ids = question_ids[idxs].astype(np.long)
        self.answer_ids = answer_ids[idxs].astype(np.long)
        self.title_ids = title_ids[idxs].astype(np.long)
        self.x_question_emb = x_question_emb[idxs].astype(np.float32)
        self.x_answer_emb = x_answer_emb[idxs].astype(np.float32)
        self.x_title_emb = x_title_emb[idxs].astype(np.float32)
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_question_emb.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        q_ids = self.question_ids[idx]
        a_ids = self.answer_ids[idx]
        # t_ids = self.title_ids[idx]
        q_att_mask = np.where(q_ids != 0, 1, 0)
        a_att_mask = np.where(a_ids != 0, 1, 0)
        # t_att_mask = np.where(t_ids != 0, 1, 0)
        x_q_emb = self.x_question_emb[idx]
        x_a_emb = self.x_answer_emb[idx]
        x_t_emb = self.x_title_emb[idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, x_q_emb, x_t_emb, x_a_emb, q_ids, a_ids, q_att_mask, 
                a_att_mask), target

    def __len__(self):
        return len(self.question_ids)


def astype(xs, dtype=np.float32):
    if isinstance(xs, tuple) or isinstance(xs, list):
        return [astype(x, dtype) for x in xs]
    else: return xs.astype(dtype)


def array_astype(arr, dtype=np.float32):
    xs = arr[0]
    if isinstance(xs, tuple) or isinstance(xs, list):
        return [[np.array(x).astype(dtype) for x in xs] for xs in arr]
    else:
        return arr.astype(dtype)


class TextDataset3(Dataset):

    def __init__(self, x_features, question_ids, answer_ids, idxs, targets=None):
        self.question_ids = array_astype(question_ids[idxs], np.long)
        self.answer_ids = array_astype(answer_ids[idxs], np.long)
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        q_ids = self.question_ids[idx]
        a_ids = self.answer_ids[idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_ids, a_ids), target

    def __len__(self):
        return len(self.x_features)


class TextDataset4(Dataset):

    def __init__(self, x_features, ids, seg_ids, idxs, targets=None):
        self.ids = ids[idxs].astype(np.long)
        self.seg_ids = seg_ids[idxs].astype(np.long)
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        ids = self.ids[idx]
        seg_ids = self.seg_ids[idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, ids, seg_ids), target

    def __len__(self):
        return len(self.x_features)

    

class AugTextDataset(Dataset):

    def __init__(self, x_features, question_ids, answer_ids, idxs, p_aug=0.5, targets=None):
        self.n_aug = len(question_ids) - 1
        self.p_aug = p_aug
        self.question_ids = [q_ids[idxs].astype(np.long) for q_ids in question_ids]
        self.answer_ids = [a_ids[idxs].astype(np.long) for a_ids in answer_ids]
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        if random.random() < self.p_aug:
            aug_idx = np.random.choice(self.n_aug) + 1
            q_ids = self.question_ids[aug_idx][idx]
            a_ids = self.answer_ids[aug_idx][idx]
        else:
            q_ids = self.question_ids[0][idx]
            a_ids = self.answer_ids[0][idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_ids, a_ids), target

    def __len__(self):
        return len(self.x_features)


class TextDataset5(Dataset):

    def __init__(self, x_features, question_ids, answer_ids, seg_question_ids, 
                 seg_answer_ids, idxs, targets=None):
        self.question_ids = array_astype(question_ids[idxs], np.long)
        self.answer_ids = array_astype(answer_ids[idxs], np.long)
        self.seg_question_ids = array_astype(seg_question_ids[idxs], np.long)
        self.seg_answer_ids = array_astype(seg_answer_ids[idxs], np.long)
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        q_ids = self.question_ids[idx]
        a_ids = self.answer_ids[idx]
        seg_q_ids = self.seg_question_ids[idx]
        seg_a_ids = self.seg_answer_ids[idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_ids, a_ids, seg_q_ids, seg_a_ids), target

    def __len__(self):
        return len(self.x_features)


class TextDataset7(Dataset):

    def __init__(self, x_features, question_ids, answer_ids, idxs, targets=None):
        self.question_ids = array_astype(question_ids[idxs], np.long)
        self.answer_ids = array_astype(answer_ids[idxs], np.long)
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)
        self.longest_idx = np.argmax(
            [len(q_seq) + len(a_seqs) for q_seq, a_seqs in zip(self.question_ids, self.answer_ids)])


    def __getitem__(self, idx):
        q_ids = self.question_ids[idx]
        n_q_seq = len(q_ids)
        if n_q_seq > 1: q_ids = np.vstack(q_ids)
        else: q_ids = q_ids[0]

        a_ids = self.answer_ids[idx]
        n_a_seq = len(a_ids)
        if n_a_seq > 1: a_ids = np.vstack(a_ids)
        else: a_ids = a_ids[0]

        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_ids, a_ids, n_q_seq, n_a_seq), target

    def __len__(self):
        return len(self.x_features)


T = lambda x: torch.tensor(x)


def collate_fn(batch):
    x_feats, q_ids, a_ids, n_q_seq, n_a_seq, targets = [], [], [], [], [], []
    for b in batch:
        (x, q, a, n_q, n_a), t = b
        x_feats.append(x)
        q_ids.append(q)
        a_ids.append(a)
        n_q_seq.append(n_q)
        n_a_seq.append(n_a)
        targets.append(t)

    x_feats = T(np.vstack(x_feats))
    q_ids = T(np.vstack(q_ids))
    a_ids = T(np.vstack(a_ids))
    n_q_seq = T(np.array(n_q_seq))
    n_a_seq = T(np.array(n_a_seq))
    target = T(np.vstack(targets))
    return (x_feats, q_ids, a_ids, n_q_seq, n_a_seq), target


class BertDataset(Dataset):

    def __init__(self, x_features, question_outputs, answer_outputs, idxs, 
                 targets=None):
        self.question_outputs = question_outputs.astype(np.float32)
        self.answer_outputs = answer_outputs.astype(np.float32)
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        q_outputs = self.question_outputs[idx]
        a_outputs = self.answer_outputs[idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_outputs, a_outputs), target

    def __len__(self):
        return len(self.x_features)


def swap_random(seq):
    idx = range(len(seq))
    i1, i2 = random.sample(idx, 2)
    seq[i1], seq[i2] = seq[i2], seq[i1]


def construct_shuffled_seq(original_ids, sentence_ids, max_seq_len=512):
    if len(sentence_ids) > 1:
        sep_id = 102
        ids = original_ids[:original_ids.index(sep_id)+1]
        # random.shuffle(sentence_ids)
        swap_random(sentence_ids)
        for sent_ids in sentence_ids:
            if len(ids) < max_seq_len - 1:
                ids += sent_ids
            else:
                break
        ids = ids[:max_seq_len-1] + [sep_id]
        ids += (max_seq_len - len(ids)) * [0]
        return np.array(ids)
    else:
        return np.array(original_ids)


class AugTextDataset2(Dataset):

    def __init__(self, x_features, question_ids, answer_ids, seg_question_ids, 
                 seg_answer_ids, sent_question_ids, sent_answer_ids, idxs, targets=None):
        self.question_ids = array_astype(question_ids[idxs], np.long)
        self.answer_ids = array_astype(answer_ids[idxs], np.long)
        self.seg_question_ids = array_astype(seg_question_ids[idxs], np.long)
        self.seg_answer_ids = array_astype(seg_answer_ids[idxs], np.long)
        self.sent_question_ids = sent_question_ids
        self.sent_answer_ids = sent_answer_ids
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        if random.uniform(0, 1) > 0.5:
            q_ids = self.question_ids[idx]
        else:
            q_ids = construct_shuffled_seq(list(self.question_ids[idx]), self.sent_question_ids[idx])
        
        if random.uniform(0, 1) > 0.5:
            a_ids = self.answer_ids[idx]
        else:
            a_ids = construct_shuffled_seq(list(self.answer_ids[idx]), self.sent_answer_ids[idx])

        seg_q_ids = self.seg_question_ids[idx]
        seg_a_ids = self.seg_answer_ids[idx]
        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_ids, a_ids, seg_q_ids, seg_a_ids), target

    def __len__(self):
        return len(self.x_features)



class AugTextDataset3(Dataset):

    def __init__(self, x_features, question_ids, answer_ids, seg_question_ids, 
                 seg_answer_ids, aug_question_ids, aug_answer_ids, aug_seg_question_ids, 
                 aug_seg_answer_ids, idxs, targets=None):
        self.question_ids = question_ids[idxs].astype(np.long)
        self.answer_ids = answer_ids[idxs].astype(np.long)
        self.seg_question_ids = seg_question_ids[idxs].astype(np.long)
        self.seg_answer_ids = seg_answer_ids[idxs].astype(np.long)
        self.aug_question_ids = aug_question_ids[idxs]
        self.aug_answer_ids = aug_answer_ids[idxs]
        self.aug_seg_question_ids = aug_seg_question_ids[idxs]
        self.aug_seg_answer_ids = aug_seg_answer_ids[idxs]
        self.x_features = x_features[idxs].astype(np.float32)
        if targets is not None: self.targets = targets[idxs].astype(np.float32)
        else: self.targets = np.zeros((self.x_features.shape[0], N_TARGETS), dtype=np.float32)

    def __getitem__(self, idx):
        if random.uniform(0, 1) > 0.5:
            q_ids = self.question_ids[idx]
            seg_q_ids = self.seg_question_ids[idx]
        else:
            q_ids = self.aug_question_ids[idx].astype(np.long)
            seg_q_ids = self.aug_seg_question_ids[idx].astype(np.long)
        
        if random.uniform(0, 1) > 0.5:
            a_ids = self.answer_ids[idx]
            seg_a_ids = self.seg_answer_ids[idx]
        else:
            a_ids = self.aug_answer_ids[idx]
            seg_a_ids = self.aug_seg_answer_ids[idx]

        x_feats = self.x_features[idx]
        target = self.targets[idx]
        return (x_feats, q_ids, a_ids, seg_q_ids, seg_a_ids), target

    def __len__(self):
        return len(self.x_features)
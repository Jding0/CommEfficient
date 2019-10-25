import os
import argparse
import torch
from datetime import datetime
import ctypes
import numpy as np

def make_logdir(args: dict):
    rows = args.num_rows
    cols = args.num_cols
    k = args.k
    mode = args.mode
    num_local_iters = args.num_local_iters
    sketch_str = f"{mode}: {rows} x {cols}" if mode == "sketch" else f"{mode}"
    k_str = f"k: {k}" if mode in ["sketch", "true_topk", "local_topk"] else f"num_local_iters: {num_local_iters}"
    workers = args.num_workers
    clients = args.num_clients
    clients_str = f"{workers}/{clients}"
    current_time = datetime.now().strftime('%b%d_%H-%M-%S')
    logdir = os.path.join(
        'runs', current_time + '_' + clients_str + '_' + sketch_str + '_' + k_str)
    return logdir

def parse_args(default_lr):
    parser = argparse.ArgumentParser()

    # meta-args
    parser.add_argument("--test", action="store_true", dest="do_test")
    modes = ["sketch", "true_topk", "local_topk", "localSGD"]
    parser.add_argument("--mode", choices=modes, default="sketch")

    # data/model args
    parser.add_argument("--static_datasets", action="store_true")
    parser.add_argument("--num_classes", type=int, default=10)
    parser.add_argument("--num_data", type=int, default=50000)
    parser.add_argument("--model", default="resnet9")
    parser.add_argument("--num_results_train", type=int, default=2)
    parser.add_argument("--num_results_val", type=int, default=2)
    parser.add_argument("--supervised", action="store_true",
                        dest="is_supervised")
    parser.add_argument("--dataset_path", type=str, default="",
                        help=("Path or url of the dataset."
                              " If empty, download from the internet."))
    parser.add_argument("--dataset_cache", type=str,
                        default='./dataset_cache',
                        help="Path or url of the dataset cache")

    # compression args
    parser.add_argument("--k", type=int, default=50000)
    parser.add_argument("--num_cols", type=int, default=500000)
    parser.add_argument("--num_rows", type=int, default=5)
    parser.add_argument("--num_blocks", type=int, default=20)
    parser.add_argument("--topk_down", action="store_true",
                        dest="do_topk_down")

    # optimization args
    parser.add_argument("--batch_size", type=int, default=512)
    parser.add_argument("--nesterov", action="store_true",
                        dest="do_nesterov")
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--weight_decay", type=float, default=5e-4)
    parser.add_argument("--num_epochs", type=int, default=24,
                        help="Number of training epochs")
    momentum_types = ["none", "local", "virtual"]
    parser.add_argument("--momentum_type", choices=momentum_types,
                        default="none")
    error_types = momentum_types
    parser.add_argument("--error_type", choices=error_types,
                        default="none")
    reductions = ["mean", "median"]
    parser.add_argument("--grad_reduction",
                        choices=reductions,
                        default="mean",
                        help="How to combine gradients from workers")
    parser.add_argument("--lr_scale", type=float, default=default_lr)
    parser.add_argument("--pivot_epoch", type=int, default=5)

    # parallelization args
    parser.add_argument("--num_clients", type=int, default=1)
    parser.add_argument("--participation", type=float, default=1.0)
    parser.add_argument("--balancedness", type=float, default=1.0)
    default_device = "cuda" if torch.cuda.is_available() else "cpu"
    parser.add_argument("--device", type=str, choices=["cpu", "cuda"],
                        default=default_device,
                        help="Device (cuda or cpu)")
    parser.add_argument("--num_devices", type=int,
                        default=1,
                        help="Number of gpus")
    parser.add_argument("--num_local_iters", type=int, default=1)
    parser.add_argument("--local_sched", action="store_true", dest="use_local_sched")
    parser.add_argument("--share_ps_gpu", action="store_true")

    # GPT2 args
    parser.add_argument("--num_dialogs", type=int, default=1)
    parser.add_argument("--model_checkpoint", type=str, default="gpt2",
                        help="Path, url or short name of the model")
    parser.add_argument("--num_candidates", type=int, default=2,
                        help="Number of candidates for training")
    parser.add_argument("--max_history", type=int, default=2,
                        help=("Number of previous exchanges to keep"
                              " in history"))
    parser.add_argument("--train_batch_size", type=int, default=8,
                        help="Batch size for training")
    parser.add_argument("--valid_batch_size", type=int, default=8,
                        help="Batch size for validation")
    parser.add_argument("--num_train_batch_shards", type=int,
                        default=4,
                        help=("Split up each batch into shards"
                              " to save memory"))
    parser.add_argument("--num_val_batch_shards", type=int,
                        default=4,
                        help=("Split up each batch into shards"
                              " to save memory"))
    parser.add_argument("--lm_coef", type=float, default=1.0,
                        help="LM loss coefficient")
    parser.add_argument("--mc_coef", type=float, default=1.0,
                        help="Multiple-choice loss coefficient")
    parser.add_argument("--max_norm", type=float, default=1.0,
                        help="Clipping gradient norm, is per-worker")
    parser.add_argument("--personality_permutations", type=int, default=1,
                        help=("Number of permutations of personality"
                              " sentences"))
    parser.add_argument("--eval_before_start", action='store_true',
                        help=("If true start with a first evaluation"
                              " before training"))
    parser.add_argument("--fp16", type=str, default="",
                        help=("Set to O0, O1, O2 or O3 for fp16 training"
                              " (see apex documentation)"))

    # Differential Privacy args
    parser.add_argument("--dp", action="store_true", dest="do_dp", help=("Whether to do differentially private training)"))
    parser.add_argument("--ledger", action="store_true", help=("Whether to use a ledger for DP"))
    parser.add_argument("--l2_norm_clip", type=float, default=1.0, help=("What value to clip the l2 norm to"))
    parser.add_argument("--noise_multiplier", type=float, default=0.0, help=("Sigma squared, i.e. standard dev of noise"))
    parser.add_argument("--num_microbatches", type=int, default=1, help=("Number of microbatches to divide each megabatch into"))


    args = parser.parse_args()
    args.num_workers = int(args.num_clients * args.participation)
    args.weight_decay = args.weight_decay
    args.iid = args.num_classes == 10

    return args

def _topk(vec, k):
    """ Return the largest k elements (by magnitude) of vec"""
    ret = torch.zeros_like(vec)
    # on a gpu, sorting is faster than pytorch's topk method
    #topkIndices = torch.sort(vec**2)[1][-k:]
    # however, torch.topk is more space efficient
    topkIndices = torch.topk(vec**2, k, sorted=False)[1]
    ret[topkIndices] = vec[topkIndices]
    return ret

def get_grad(model, weights, args):
    grad_vec = get_grad_vec(model)
    if args.weight_decay != 0:
        grad_vec.add_(args.weight_decay / args.num_workers, weights)
    return grad_vec.to(args.device)

def get_grad_vec(model):
    grad_vec = []
    with torch.no_grad():
        # flatten
        for p in model.parameters():
            if p.grad is None:
                grad_vec.append(torch.zeros_like(p.data.view(-1)))
            else:
                grad_vec.append(p.grad.data.view(-1).float())
        # concat into a single vector
        grad_vec = torch.cat(grad_vec)
    return grad_vec

def zero_grad(model):
    for p in model.parameters():
        if p.grad is not None:
            p.grad.detach_()
            p.grad.zero_()

def get_param_vec(model, device):
    return torch.cat([p.data.view(-1) for p in model.parameters()]).to(device)
    param_vec = []
    for p in model.parameters():
        param_vec.append(p.data.view(-1))
    return torch.cat(param_vec).to(device)

def set_param_vec(model, param_vec):
    start = 0
    for p in model.parameters():
        end = start + p.numel()
        p.data.zero_()
        p.data.add_(param_vec[start:end].view(p.size()))
        start = end

def sm2np(sm, shape, dtype=ctypes.c_float):
    # convert from shared memory object/buffer to numpy array
    nparray = np.ndarray(shape, dtype=dtype, buffer=sm)
    assert(nparray.base is sm)
    return nparray

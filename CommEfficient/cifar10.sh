#OMP_NUM_THREADS=8 python -m cProfile -o profile/cifar_fedsampler.pstats fed_train.py \

OMP_NUM_THREADS=8 python cv_train.py \
    --dataset_dir /data/ashwineep/datasets/ \
    --local_batch_size 512 \
    --dataset_name CIFAR10 \
    --local_momentum 0.0 \
    --virtual_momentum 0.9 \
    --error_type virtual \
    --share_ps_gpu \
    --mode uncompressed \
    --num_devices 4 \
    --num_workers 4 \
    --iid \
    --num_clients 4 \
    --k 50000 \
    --num_rows 3 \
    --num_cols 1000000 \
    --supervised \
    --malicious \
    --mal_targets 100 \
    --mal_boost 1.0 \

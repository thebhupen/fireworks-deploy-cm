"""LoRA SFT of Nemotron 3.5 Lightning on the teacher's passing runs, with Fireworks' Training API cookbook
(github.com/fw-ai/cookbook, training/). The dataset stays local: the recipe tokenizes it here and streams batches to
a dedicated Fireworks trainer, then promotes the final adapter as a model on the account.

    FIREWORKS_API_KEY=... third_party/fw-cookbook/training/.venv/bin/python train_fireworks.py [--output-model ID]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from training.recipes.sft_loop import Config, main

HERE = Path(__file__).resolve().parent


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=HERE / "sft" / "train.jsonl")
    parser.add_argument("--output-model", default="nemotron-lightning-rlu-v1")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--lora-rank", type=int, default=16)
    parser.add_argument("--max-seq-len", type=int, default=65536)
    args = parser.parse_args()

    main(
        Config(
            log_path=str(HERE / "sft" / args.output_model),
            base_model="accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b",
            dataset=str(args.dataset),
            tokenizer_model="nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16",
            max_seq_len=args.max_seq_len,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            lora_rank=args.lora_rank,
            output_model_id=args.output_model,
        )
    )


if __name__ == "__main__":
    run()

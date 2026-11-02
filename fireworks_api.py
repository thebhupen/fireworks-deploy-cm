"""Fireworks REST calls for the fine-tune, so firectl is not needed. The key comes from FIREWORKS_API_KEY.

python fireworks_api.py dataset <dataset_id> <file.jsonl>
python fireworks_api.py sft <job_id> <dataset_id> <base_model> <output_model> [--epochs 3 --lora-rank 16 ...]
python fireworks_api.py job <job_id>
python fireworks_api.py get <path under /v1/accounts/<account>/, e.g. models/<id>>
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "https://api.fireworks.ai/v1"


def call(method: str, url: str, body: bytes | None = None, content_type: str | None = None) -> dict:
    headers = {"Authorization": "Bearer " + os.environ["FIREWORKS_API_KEY"]}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            text = response.read().decode()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"{method} {url}: HTTP {error.code}: {error.read().decode()[:1000]}") from None
    return json.loads(text) if text else {}


def account() -> str:
    return call("GET", f"{BASE}/accounts")["accounts"][0]["name"]  # "accounts/<id>"


def create_dataset(dataset_id: str, path: Path) -> None:
    acct = account()
    count = sum(1 for line in path.open(encoding="utf-8") if line.strip())
    body = {"datasetId": dataset_id, "dataset": {"userUploaded": {}, "format": "CHAT", "exampleCount": str(count)}}
    print(json.dumps(call("POST", f"{BASE}/{acct}/datasets", json.dumps(body).encode(), "application/json"))[:500])
    boundary = uuid.uuid4().hex
    form = (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            "Content-Type: application/jsonl\r\n\r\n"
        ).encode()
        + path.read_bytes()
        + f"\r\n--{boundary}--\r\n".encode()
    )
    upload_url = f"{BASE}/{acct}/datasets/{dataset_id}:upload"
    result = call("POST", upload_url, form, f"multipart/form-data; boundary={boundary}")
    print(json.dumps(result)[:500])
    print(json.dumps(call("GET", f"{BASE}/{acct}/datasets/{dataset_id}"))[:800])


def create_sft(args: argparse.Namespace) -> None:
    acct = account()
    body = {
        "baseModel": args.base_model,
        "dataset": f"{acct}/datasets/{args.dataset_id}",
        "outputModel": f"{acct}/models/{args.output_model}",
        "displayName": args.job_id,
        "epochs": args.epochs,
        "loraRank": args.lora_rank,
        "maxContextLength": args.max_context_length,
    }
    if args.learning_rate:
        body["learningRate"] = args.learning_rate
    url = f"{BASE}/{acct}/supervisedFineTuningJobs?supervisedFineTuningJobId={args.job_id}"
    print(json.dumps(call("POST", url, json.dumps(body).encode(), "application/json"), indent=1)[:2000])


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    dataset = sub.add_parser("dataset")
    dataset.add_argument("dataset_id")
    dataset.add_argument("path", type=Path)
    sft = sub.add_parser("sft")
    sft.add_argument("job_id")
    sft.add_argument("dataset_id")
    sft.add_argument("base_model")
    sft.add_argument("output_model")
    sft.add_argument("--epochs", type=int, default=3)
    sft.add_argument("--lora-rank", type=int, default=16)
    sft.add_argument("--max-context-length", type=int, default=65536)
    sft.add_argument("--learning-rate", type=float)
    job = sub.add_parser("job")
    job.add_argument("job_id")
    get = sub.add_parser("get")
    get.add_argument("path")
    args = parser.parse_args()

    if args.command == "dataset":
        create_dataset(args.dataset_id, args.path)
    elif args.command == "sft":
        create_sft(args)
    elif args.command == "job":
        print(json.dumps(call("GET", f"{BASE}/{account()}/supervisedFineTuningJobs/{args.job_id}"), indent=1)[:3000])
    else:
        print(json.dumps(call("GET", f"{BASE}/{account()}/{args.path}"), indent=1)[:3000])


if __name__ == "__main__":
    main()

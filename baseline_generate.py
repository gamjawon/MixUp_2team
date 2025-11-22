import os
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from prompts import baseline_prompt
from system_prompts import BASELINE_SYSTEM_PROMPT

# Load environment variables
load_dotenv()


def call_with_retry(client, model, messages, max_retries=5, base_wait=1.0):
    """
    Rate limit(429) 등 에러가 날 때 자동으로 backoff 하면서 재시도하는 함수.
    """
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                # reasoning_effort="high",
                # top_p=0.1,
            )
            return resp
        except Exception as e:
            msg = str(e).lower()
            # Upstage에서 오는 에러 메시지에 맞춰서 조건을 조금 더 좁힐 수도 있음
            is_rate_limit = "rate limit" in msg or "429" in msg
            if is_rate_limit and attempt < max_retries - 1:
                wait = min(base_wait * (2**attempt), 30.0)  # 1,2,4,8,... 최대 30초
                print(f"[RateLimit] retry {attempt + 1}/{max_retries} in {wait:.1f}s")
                time.sleep(wait)
                continue
            # rate limit가 아니거나 마지막 재시도면 그대로 에러 올리기
            raise


def process_batch(batch_id, start, end, df, model, request_delay, base_wait):
    """
    하나의 배치(행 구간)를 처리하는 함수.
    ThreadPoolExecutor 안에서 병렬로 실행됨.
    """
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise ValueError("UPSTAGE_API_KEY not found in environment variables")

    client = OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1")

    batch_df = df.iloc[start:end].copy()

    results = []
    desc = f"Batch {batch_id} ({start}-{end - 1})"

    for _, row in tqdm(
        batch_df.iterrows(),
        total=len(batch_df),
        desc=desc,
        leave=False,
    ):
        text = str(row["original_sentence"])
        row_id = row["id"]
        orig_idx = row.name  # 원래 인덱스 보존해서 나중에 정렬용으로 사용

        prompt = baseline_prompt.format(text=text)
        messages = [
            {
                "role": "system",
                "content": BASELINE_SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ]

        try:
            resp = call_with_retry(
                client,
                model=model,
                messages=messages,
                max_retries=5,
                base_wait=base_wait,
            )
            corrected = resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Batch {batch_id}] Error processing: {text[:40]}... - {e}")
            # 실패 시 원문 그대로 사용
            corrected = text

        results.append(
            {
                "_idx": orig_idx,
                "id": row_id,
                "original_sentence": text,
                "answer_sentence": corrected,
            }
        )

        # 🔹 요청 사이에 soft delay (딜레이) 넣어줌
        if request_delay > 0:
            time.sleep(request_delay)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate modified sentences using Upstage API (parallel version)"
    )
    # 👉 원래대로 data/train_dataset.csv를 기본값으로 사용
    parser.add_argument(
        "--input",
        default="data/train_dataset.csv",
        help="Input CSV path (must contain 'id' and 'original_sentence' columns)",
    )
    parser.add_argument(
        "--output",
        default="submission.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--model",
        default="solar-pro2",
        help="Model name (default: solar-pro2)",
    )
    # 🔥 병렬 & 배치 관련 옵션
    parser.add_argument(
        "--batch_size",
        type=int,
        default=100,
        help="Number of rows per batch (default: 100)",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=3,
        help="병렬로 돌릴 배치(worker) 수 (default: 3)",
    )
    parser.add_argument(
        "--request_delay",
        type=float,
        default=0.1,
        help="각 요청 사이에 넣을 딜레이 (초). rate limit 여유 있으면 0으로 줄여도 됨.",
    )
    parser.add_argument(
        "--base_wait",
        type=float,
        default=1.0,
        help="rate limit 발생 시 backoff의 기본 대기 시간 (초)",
    )
    parser.add_argument(
        "--experiment-name", default=None, help="Experiment name for organizing results"
    )

    args = parser.parse_args()

    # 입력 파일 로드
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input)

    if "original_sentence" not in df.columns:
        raise ValueError("Input CSV must contain 'original_sentence' column")
    if "id" not in df.columns:
        raise ValueError("Input CSV must contain 'id' column")

    total_rows = len(df)
    print(f"Loaded {total_rows} rows from {args.input}")
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"Batch size: {args.batch_size}, max_workers: {args.max_workers}")
    print(f"Request delay: {args.request_delay}s, base_wait: {args.base_wait}s\n")

    # 배치 나누기
    batch_ranges = []
    batch_id = 0
    for start in range(0, total_rows, args.batch_size):
        end = min(start + args.batch_size, total_rows)
        batch_ranges.append((batch_id, start, end))
        batch_id += 1

    print("Planned batches:")
    for bid, s, e in batch_ranges:
        print(f"  - Batch {bid}: rows {s} ~ {e - 1} (size={e - s})")

    all_results = []

    # 🔥 병렬 실행 (ThreadPoolExecutor)
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = []
        for bid, s, e in batch_ranges:
            fut = executor.submit(
                process_batch,
                bid,
                s,
                e,
                df,
                args.model,
                args.request_delay,
                args.base_wait,
            )
            futures.append(fut)

        # 완료되는 순서대로 결과 수집
        for fut in as_completed(futures):
            batch_results = fut.result()
            all_results.extend(batch_results)

    # 원래 순서대로 정렬 후 저장
    if not all_results:
        raise RuntimeError("No results were generated.")

    out_df = pd.DataFrame(all_results)
    out_df = out_df.sort_values("_idx").drop(columns=["_idx"])
    out_df.to_csv(args.output, index=False)
    print(f"\n✅ All done. Processed {len(out_df)} rows → {args.output}")

    # Save to experiments folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_name = args.experiment_name or f"exp_{timestamp}"
    exp_dir = os.path.join("experiments", exp_name)
    os.makedirs(exp_dir, exist_ok=True)

    # Save submission
    submission_path = os.path.join(exp_dir, "submission.csv")
    out_df.to_csv(submission_path, index=False)

    # Save prompt
    prompt_path = os.path.join(exp_dir, "prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write("# Baseline Prompt\n\n")
        f.write(baseline_prompt)

    # Save metadata
    metadata_path = os.path.join(exp_dir, "metadata.txt")
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(f"Experiment: {exp_name}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Model: {args.model}\n")
        f.write(f"Input: {args.input}\n")
        f.write(f"Total samples: {len(out_df)}\n")
        f.write(f"Batch size: {args.batch_size}\n")
        f.write(f"Max workers: {args.max_workers}\n")
        f.write(f"Request delay: {args.request_delay}s\n")
        f.write(f"Base wait: {args.base_wait}s\n")

    print(f"\n✅ 실험 결과가 저장되었습니다: {exp_dir}/")
    print(f"   - submission.csv")
    print(f"   - prompt.txt")
    print(f"   - metadata.txt")


if __name__ == "__main__":
    main()

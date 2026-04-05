import argparse
import random
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import List, Optional

import requests

API_BASE_URL = "http://localhost:8000"
LIKE_ENDPOINT = f"{API_BASE_URL}/like"
COMMENT_ENDPOINT = f"{API_BASE_URL}/comment"


@dataclass
class Stats:
    success: int = 0
    failures: int = 0
    latencies: List[float] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record_success(self, latency: float):
        with self.lock:
            self.success += 1
            self.latencies.append(latency)

    def record_failure(self):
        with self.lock:
            self.failures += 1

    def get_stats(self):
        with self.lock:
            latencies = sorted(self.latencies)
            count = len(latencies)
            if count == 0:
                return {
                    "success": self.success,
                    "failures": self.failures,
                    "total": self.success + self.failures,
                    "avg_latency_ms": 0,
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                }

            avg = sum(latencies) / count
            p50 = latencies[int(count * 0.50)]
            p95 = latencies[int(count * 0.95)]
            p99 = latencies[int(count * 0.99)]

            return {
                "success": self.success,
                "failures": self.failures,
                "total": self.success + self.failures,
                "avg_latency_ms": round(avg * 1000, 2),
                "p50_ms": round(p50 * 1000, 2),
                "p95_ms": round(p95 * 1000, 2),
                "p99_ms": round(p99 * 1000, 2),
            }


def send_like(stats: Stats, user_range: tuple, post_range: tuple):
    user_id = random.randint(*user_range)
    post_id = random.randint(*post_range)

    start = time.time()
    try:
        resp = requests.post(
            LIKE_ENDPOINT,
            json={"user_id": user_id, "post_id": post_id},
            timeout=5,
        )
        latency = time.time() - start
        if resp.status_code == 202:
            stats.record_success(latency)
        else:
            stats.record_failure()
    except Exception:
        stats.record_failure()


def send_comment(stats: Stats, user_range: tuple, post_range: tuple):
    user_id = random.randint(*user_range)
    post_id = random.randint(*post_range)
    content = f"Comment {uuid.uuid4().hex[:8]}"

    start = time.time()
    try:
        resp = requests.post(
            COMMENT_ENDPOINT,
            json={"user_id": user_id, "post_id": post_id, "content": content},
            timeout=5,
        )
        latency = time.time() - start
        if resp.status_code == 202:
            stats.record_success(latency)
        else:
            stats.record_failure()
    except Exception:
        stats.record_failure()


def worker_thread(
    stats: Stats,
    thread_id: int,
    num_requests: int,
    user_range: tuple,
    post_range: tuple,
    rps: float,
    like_ratio: float,
):
    delay = 1.0 / rps if rps > 0 else 0
    for i in range(num_requests):
        if random.random() < like_ratio:
            send_like(stats, user_range, post_range)
        else:
            send_comment(stats, user_range, post_range)

        if delay > 0:
            time.sleep(delay)


def run_load_test(
    threads: int,
    requests_per_thread: int,
    rps: float,
    like_ratio: float,
    user_range: tuple,
    post_range: tuple,
):
    stats = Stats()
    print(
        f"Starting load test: threads={threads}, requests_per_thread={requests_per_thread}, "
        f"rps={rps}, like_ratio={like_ratio}"
    )
    print(f"User range: {user_range}, Post range: {post_range}")
    print(f"API: {API_BASE_URL}")
    print("-" * 60)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for t in range(threads):
            f = executor.submit(
                worker_thread,
                stats,
                t,
                requests_per_thread,
                user_range,
                post_range,
                rps,
                like_ratio,
            )
            futures.append(f)

        for f in futures:
            f.result()

    elapsed = time.time() - start_time

    print("-" * 60)
    print("Load test complete")
    print(f"Elapsed time: {elapsed:.2f}s")
    print(f"Throughput: {(stats.success + stats.failures) / elapsed:.2f} req/s")

    results = stats.get_stats()
    print("\nResults:")
    print(f"  Total requests:  {results['total']}")
    print(f"  Success:         {results['success']}")
    print(f"  Failures:        {results['failures']}")
    print(f"  Success rate:    {results['success'] / results['total'] * 100:.1f}%")
    print(f"  Avg latency:     {results['avg_latency_ms']:.2f}ms")
    print(f"  P50 latency:     {results['p50_ms']:.2f}ms")
    print(f"  P95 latency:     {results['p95_ms']:.2f}ms")
    print(f"  P99 latency:     {results['p99_ms']:.2f}ms")


def main():
    parser = argparse.ArgumentParser(description="Multi-threaded notification load test client")
    parser.add_argument(
        "-t", "--threads", type=int, default=10, help="Number of threads (default: 10)"
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=100,
        help="Requests per thread (default: 100)",
    )
    parser.add_argument(
        "-r", "--rps", type=float, default=0, help="Target requests per second per thread (default: unlimited)"
    )
    parser.add_argument(
        "-l",
        "--like-ratio",
        type=float,
        default=0.7,
        help="Ratio of likes vs comments (default: 0.7)",
    )
    parser.add_argument(
        "-u",
        "--user-range",
        type=str,
        default="1,10000",
        help="User ID range as 'min,max' (default: 1,10000)",
    )
    parser.add_argument(
        "-p",
        "--post-range",
        type=str,
        default="1,1000",
        help="Post ID range as 'min,max' (default: 1,1000)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )

    args = parser.parse_args()

    global API_BASE_URL, LIKE_ENDPOINT, COMMENT_ENDPOINT
    API_BASE_URL = args.api_url
    LIKE_ENDPOINT = f"{API_BASE_URL}/like"
    COMMENT_ENDPOINT = f"{API_BASE_URL}/comment"

    user_range = tuple(map(int, args.user_range.split(",")))
    post_range = tuple(map(int, args.post_range.split(",")))

    run_load_test(
        threads=args.threads,
        requests_per_thread=args.requests,
        rps=args.rps,
        like_ratio=args.like_ratio,
        user_range=user_range,
        post_range=post_range,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Benchmark Generator for Distributed Transaction System

Generates transaction sequences with configurable parameters:
- ro_percent: Read-only vs read-write transaction ratio
- cross_shard_percent: Intra-shard vs cross-shard transaction ratio
- skew: Zipfian skew for hotspot distribution (0=uniform, 1=highly skewed)
"""

import argparse
import csv
import random
import math
from typing import List, Tuple, Optional


# Shard boundaries (matching paxos_p3.da)
SHARDS = {
    1: (1, 3000),
    2: (3001, 6000),
    3: (6001, 9000),
}

ALL_NODES = "[n1, n2, n3, n4, n5, n6, n7, n8, n9]"


class BenchmarkGenerator:
    """Generate transaction workloads for testing."""

    def __init__(
        self,
        ro_percent: float = 0.0,
        cross_shard_percent: float = 0.0,
        skew: float = 0.0,
        num_transactions: int = 100,
        seed: Optional[int] = None,
    ):
        """
        Initialize the benchmark generator.

        Args:
            ro_percent: Percentage of read-only transactions (0-100)
            cross_shard_percent: Percentage of cross-shard transactions (0-100)
            skew: Zipfian skew parameter (0=uniform, closer to 1=more skewed)
            num_transactions: Total number of transactions to generate
            seed: Random seed for reproducibility
        """
        self.ro_percent = ro_percent / 100.0
        self.cross_shard_percent = cross_shard_percent / 100.0
        self.skew = skew
        self.num_transactions = num_transactions

        if seed is not None:
            random.seed(seed)

        # Precompute Zipfian weights for each shard
        self._zipf_weights = {}
        for shard_id, (lo, hi) in SHARDS.items():
            n = hi - lo + 1
            if skew > 0:
                weights = [1.0 / ((i + 1) ** skew) for i in range(n)]
            else:
                weights = [1.0] * n
            total = sum(weights)
            self._zipf_weights[shard_id] = [w / total for w in weights]

    def _sample_key(self, shard_id: int) -> int:
        """Sample a key from the given shard using Zipfian distribution."""
        lo, hi = SHARDS[shard_id]
        n = hi - lo + 1
        offset = random.choices(range(n), weights=self._zipf_weights[shard_id], k=1)[0]
        return lo + offset

    def _generate_ro_tx(self) -> Tuple[int]:
        """Generate a read-only (balance query) transaction."""
        shard_id = random.choice(list(SHARDS.keys()))
        key = self._sample_key(shard_id)
        return (key,)

    def _generate_rw_intra_tx(self) -> Tuple[int, int, int]:
        """Generate a read-write intra-shard transaction."""
        shard_id = random.choice(list(SHARDS.keys()))
        src = self._sample_key(shard_id)
        dst = self._sample_key(shard_id)
        # Ensure src != dst
        while dst == src:
            dst = self._sample_key(shard_id)
        amt = random.randint(1, 5)
        return (src, dst, amt)

    def _generate_rw_cross_tx(self) -> Tuple[int, int, int]:
        """Generate a read-write cross-shard transaction."""
        shards = list(SHARDS.keys())
        src_shard = random.choice(shards)
        dst_shard = random.choice([s for s in shards if s != src_shard])
        src = self._sample_key(src_shard)
        dst = self._sample_key(dst_shard)
        amt = random.randint(1, 5)
        return (src, dst, amt)

    def generate(self) -> List[Tuple]:
        """Generate the transaction list based on parameters."""
        transactions = []

        for _ in range(self.num_transactions):
            # Decide read-only vs read-write
            if random.random() < self.ro_percent:
                tx = self._generate_ro_tx()
            else:
                # Decide intra-shard vs cross-shard
                if random.random() < self.cross_shard_percent:
                    tx = self._generate_rw_cross_tx()
                else:
                    tx = self._generate_rw_intra_tx()
            transactions.append(tx)

        return transactions

    def to_csv(self, filename: str, set_number: int = 1):
        """Write transactions to CSV file in test format."""
        transactions = self.generate()

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Set Number", "Transactions", "Live Nodes"])

            for i, tx in enumerate(transactions):
                tx_str = str(tx).replace(" ", "")
                if i == 0:
                    writer.writerow([set_number, tx_str, ALL_NODES])
                else:
                    writer.writerow(["", tx_str, ""])

        print(f"Generated {len(transactions)} transactions to {filename}")
        self._print_stats(transactions)

    def _print_stats(self, transactions: List[Tuple]):
        """Print statistics about the generated workload."""
        ro_count = sum(1 for tx in transactions if len(tx) == 1)
        rw_count = len(transactions) - ro_count

        cross_count = 0
        intra_count = 0
        for tx in transactions:
            if len(tx) == 3:
                src, dst, _ = tx
                src_shard = self._get_shard(src)
                dst_shard = self._get_shard(dst)
                if src_shard != dst_shard:
                    cross_count += 1
                else:
                    intra_count += 1

        print(f"\n=== Workload Statistics ===")
        print(f"Total transactions: {len(transactions)}")
        print(f"Read-only: {ro_count} ({100*ro_count/len(transactions):.1f}%)")
        print(f"Read-write: {rw_count} ({100*rw_count/len(transactions):.1f}%)")
        if rw_count > 0:
            print(f"  Intra-shard: {intra_count} ({100*intra_count/rw_count:.1f}% of RW)")
            print(f"  Cross-shard: {cross_count} ({100*cross_count/rw_count:.1f}% of RW)")
        print(f"Skew parameter: {self.skew}")

    @staticmethod
    def _get_shard(key: int) -> int:
        """Get shard ID for a key."""
        if key <= 3000:
            return 1
        if key <= 6000:
            return 2
        return 3


def main():
    parser = argparse.ArgumentParser(
        description="Generate benchmark workload for distributed transaction system"
    )
    parser.add_argument(
        "--ro",
        type=float,
        default=0,
        help="Percentage of read-only transactions (0-100)",
    )
    parser.add_argument(
        "--cross",
        type=float,
        default=0,
        help="Percentage of cross-shard transactions (0-100)",
    )
    parser.add_argument(
        "--skew",
        type=float,
        default=0.0,
        help="Zipfian skew (0=uniform, closer to 1=more hotspots)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of transactions to generate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="benchmark.csv",
        help="Output CSV filename",
    )
    parser.add_argument(
        "--set",
        type=int,
        default=1,
        help="Set number in the output CSV",
    )

    args = parser.parse_args()

    generator = BenchmarkGenerator(
        ro_percent=args.ro,
        cross_shard_percent=args.cross,
        skew=args.skew,
        num_transactions=args.count,
        seed=args.seed,
    )

    generator.to_csv(args.output, set_number=args.set)


if __name__ == "__main__":
    main()

## 2PC + Multi-Paxos Sharded Transaction System (DistAlgo)

This project implements a fault-tolerant sharded banking datastore:
- **3+ clusters**, each cluster is a shard replicated on **all nodes in the cluster**
- **Intra-shard transfers** replicated via **Multi-Paxos**
- **Cross-shard transfers** executed via **2PC on top of Multi-Paxos**
- **Read-only balance** queries with optional consistency flags
- **Offline Reshard** based on recent transaction history (balanced partition heuristic) with key migration

### Files
- `paxos_p3.da`: main DistAlgo implementation (Driver + Node)
- `CSE535-F25-Project-3-Testcases.csv`: provided testcases
- `benchmark_generator.py`: workload generator (configurable)
- `bonus1_ryw_cross_test.csv`, `bonus1_eventual_read_test.csv`: Bonus1 tests
- `bonus2_test.csv`: Bonus2 (configurable clusters) test

---

## Running

### Default (3 clusters × 3 nodes/cluster, 9000 keys)

```bash
py -3.7 -m da paxos_p3.da CSE535-F25-Project-3-Testcases.csv
```

### Configurable clusters (Bonus 2)

```bash
py -3.7 -m da paxos_p3.da bonus2_test.csv --clusters 4 --nodes-per-cluster 3 --total-keys 120
```

Notes:
- For **f=1** fault tolerance you need **3 nodes/cluster** (majority = 2).
- With **2 nodes/cluster**, the system is **f=0** (cannot commit if any node fails).

---

## Interactive prompts

By default prompts are enabled **only when running interactively in a terminal** (to avoid hanging when redirecting output).

Environment overrides:
- `PROMPT_SETS=1/0`: prompt between sets
- `PROMPT_BALANCE=1/0`: post-set command prompt

Post-set commands:
- `PrintBalance(ID)` (format: `nX : bal, nY : bal, ...`)
- `PrintDB`
- `PrintView`
- `Performance` / `perf`
- `Reshard`
- `next` / `n`

---

## Bonus 1: Multiple consistency levels

### RYW (Read-Your-Writes)

```bash
py -3.7 -m da paxos_p3.da bonus1_ryw_cross_test.csv
```

How to confirm it's correct:
- The first transaction is a **cross-shard transfer** `(3002 -> 6001)`. After it commits, the subsequent
  `ryw` reads must observe the write:
  - `(6001, ryw)` should return the **post-write balance** (typically 11 from initial 10).
  - `(6001, linearizable)` should match it.
- This verifies that cross-shard COMMIT replies include the write-set and the Driver updates the RYW cache.

### Eventual read

```bash
py -3.7 -m da paxos_p3.da bonus1_eventual_read_test.csv
```

How to confirm it's correct:
- You should see `('BAL', <value>, 'eventual')` responses for the eventual queries.
- The linearizable query prints `('BAL', <value>)` (without the `'eventual'` tag).

---

## Benchmark generator (configurable)

Generate a workload CSV compatible with `paxos_p3.da`:

```bash
python benchmark_generator.py --ro 20 --cross 50 --skew 0.8 --count 500 \
  --clusters 4 --nodes-per-cluster 3 --total-keys 120 \
  -o bench.csv
```

Then run:

```bash
py -3.7 -m da paxos_p3.da bench.csv --clusters 4 --nodes-per-cluster 3 --total-keys 120
```

---

## Bonus 2: Configurable clusters (how to verify)

Run the provided test:

```bash
py -3.7 -m da paxos_p3.da bonus2_test.csv --clusters 4 --nodes-per-cluster 3 --total-keys 120
```

How to confirm it's correct:
- Startup logs show the **requested configuration** (4 clusters, 3 nodes/cluster, 120 keys) and a 4-way shard map.
- All transactions complete without exceptions.
- `PrintBalance(k)` prints **3 replicas** for the shard that owns `k` (because nodes/cluster=3).



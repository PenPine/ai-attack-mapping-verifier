"""
tests/test_eventid_lookup.py
Tests for the Event ID lookup baseline (evaluation/eventid_lookup.py). No API calls.

Run from the project root:  python -m unittest discover -s tests -t . -v
The tests marked "v3 pool" read results/pool_clean_v3.jsonl and results/baseline_clean_v3.jsonl and are
skipped if those files are missing.
"""
import json
import os
import unittest
from collections import Counter, defaultdict

from evaluation import eventid_lookup as lk

POOL = "results/pool_clean_v3.jsonl"
BASELINE = "results/baseline_clean_v3.jsonl"
HAVE_V3 = os.path.exists(POOL) and os.path.exists(BASELINE)
TIE_CLUSTER = "T1053.005|schtask_create_2020-12-1907003032.json|2020-12-19 12:00"

# small synthetic pool: (cluster_id, technique_label, event_id)
TOY = [("A", "T1", "1"), ("A", "T1", "1"), ("A", "T1", "4"),
       ("B", "T2", "1"), ("B", "T2", "1"),
       ("C", "T2", "1"),
       ("D", "T3", "99")]                       # Event ID 99 occurs only in cluster D


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def v3_rows():
    pool = {p["event_uid"]: p for p in load(POOL)}
    return [(b["cluster_id"], b["technique_label"], str(pool[b["event_uid"]]["event"].get("EventID")))
            for b in load(BASELINE) if "predicted_technique" in b["prediction"]]


def counts_without(rows, cluster):
    """Reference: the lookup table rebuilt from scratch on every row outside `cluster`."""
    out = defaultdict(Counter)
    for cid, label, eid in rows:
        if cid != cluster:
            out[eid][label] += 1
    return out


class WithoutCluster(unittest.TestCase):
    """(a) without_cluster removes every event of the left-out cluster and nothing else."""

    def check(self, rows):
        table = lk.build_table(rows)
        for cid in sorted({r[0] for r in rows}):
            sub = lk.without_cluster(table, rows, cid)
            ref = counts_without(rows, cid)
            with self.subTest(cluster=cid):
                for eid in table:
                    self.assertEqual(+sub[eid], +ref[eid], f"Event ID {eid}")
                removed = sum(table[e][l] - sub[e][l] for e in table for l in table[e])
                self.assertEqual(removed, sum(1 for r in rows if r[0] == cid))

    def test_toy(self):
        self.check(TOY)

    def test_toy_example(self):
        sub = lk.without_cluster(lk.build_table(TOY), TOY, "A")
        self.assertEqual(+sub["1"], Counter({"T2": 3}))
        self.assertEqual(+sub["4"], Counter())
        self.assertEqual(+sub["99"], Counter({"T3": 1}))

    def test_table_not_modified(self):
        table = lk.build_table(TOY)
        before = {e: Counter(c) for e, c in table.items()}
        lk.without_cluster(table, TOY, "B")
        self.assertEqual(table, before)

    @unittest.skipUnless(HAVE_V3, "v3 pool not found")
    def test_v3_pool(self):
        self.check(v3_rows())


class Ties(unittest.TestCase):
    """(b) a 2 vs 2 tie returns NONE, whatever the insertion order."""

    def test_two_two_tie_is_none(self):
        for order in (["T1053.005", "T1059.003"], ["T1059.003", "T1053.005"]):
            c = Counter()
            for label in order:
                c[label] += 2
            with self.subTest(order=order):
                self.assertEqual(lk.pick(c), (lk.NONE, True))
                self.assertEqual(lk.pick(c, truth="T1053.005"), (lk.NONE, True))

    def test_upper_bound_resolves_to_true_label(self):
        c = Counter({"T1059.003": 2, "T1053.005": 2})
        self.assertEqual(lk.pick(c, "T1053.005", tie_rule="upper"), ("T1053.005", True))
        self.assertEqual(lk.pick(c, "T1003.001", tie_rule="upper"), (lk.NONE, True))

    def test_clear_majority_is_not_a_tie(self):
        self.assertEqual(lk.pick(Counter({"T1053.005": 4, "T1059.003": 2})), ("T1053.005", False))

    def test_zero_counts_ignored(self):
        self.assertEqual(lk.pick(Counter({"T1": 2, "T2": 0, "T3": -1})), ("T1", False))

    @unittest.skipUnless(HAVE_V3, "v3 pool not found")
    def test_v3_tie_on_event_id_1(self):
        rows = v3_rows()
        r = lk.evaluate(rows, loo=True)
        self.assertEqual(r["tie_clusters"], 1)
        self.assertEqual(len(r["ties"]), 2)
        for t in r["ties"]:
            self.assertEqual(t["cluster_id"], TIE_CLUSTER)
            self.assertEqual(t["event_id"], "1")
            self.assertEqual(t["counts"], {"T1053.005": 2, "T1059.003": 2})
            self.assertEqual(t["prediction"], lk.NONE)
        self.assertEqual(lk.evaluate(rows, loo=False)["ties"], [])


class UnseenEventId(unittest.TestCase):
    """(c) an Event ID the lookup has not seen returns NONE (counted wrong)."""

    def test_empty_counter(self):
        self.assertEqual(lk.pick(Counter()), (lk.NONE, False))

    def test_only_in_left_out_cluster(self):
        sub = lk.without_cluster(lk.build_table(TOY), TOY, "D")
        self.assertEqual(lk.pick(sub["99"], "T3"), (lk.NONE, False))
        r = lk.evaluate(TOY, loo=True)
        self.assertEqual(r["per_tech"]["T3"], [0.0])

    def test_toy_evaluate(self):
        # LOO: A -> Event ID 1 is T2 (3 vs 0), 4 unseen -> 0/3; B -> 1 is T1:2 vs T2:1 -> 0/2;
        # C -> 1 is T1:2 vs T2:2, a tie -> NONE -> 0/1; D -> 99 unseen -> 0/1
        r = lk.evaluate(TOY, loo=True)
        self.assertEqual((r["event_ok"], r["n_events"], r["n_clusters"]), (0, 7, 4))
        self.assertEqual([t["cluster_id"] for t in r["ties"]], ["C"])
        # in-sample: 1 -> T2 (3 vs 2), 4 -> T1, 99 -> T3: A 1/3, B 2/2, C 1/1, D 1/1
        r = lk.evaluate(TOY, loo=False)
        self.assertEqual(r["event_ok"], 5)
        self.assertAlmostEqual(r["cluster_acc"], (1 / 3 + 1 + 1 + 1) / 4)


@unittest.skipUnless(HAVE_V3, "v3 pool not found")
class V3Numbers(unittest.TestCase):
    """(d) the v3 numbers reported in Table 5."""

    @classmethod
    def setUpClass(cls):
        cls.rows = v3_rows()

    def test_scored(self):
        self.assertEqual(len(self.rows), 288)
        self.assertEqual(len({r[0] for r in self.rows}), 63)

    def test_leave_one_cluster(self):
        r = lk.evaluate(self.rows, loo=True)
        self.assertEqual(round(r["event_acc"] * 100, 1), 86.5)
        self.assertEqual(round(r["cluster_acc"] * 100, 1), 89.1)

    def test_in_sample(self):
        r = lk.evaluate(self.rows, loo=False)
        self.assertEqual(round(r["event_acc"] * 100, 1), 98.3)
        self.assertEqual(round(r["cluster_acc"] * 100, 1), 92.1)

    def test_upper_bound(self):
        r = lk.evaluate(self.rows, loo=True, tie_rule="upper")
        self.assertEqual(round(r["event_acc"] * 100, 1), 87.2)
        self.assertEqual(round(r["cluster_acc"] * 100, 1), 90.7)


if __name__ == "__main__":
    unittest.main()

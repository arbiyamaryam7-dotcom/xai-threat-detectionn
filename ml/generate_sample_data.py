"""Generate a SYNTHETIC CIC-IDS2017-style sample so the pipeline can be run offline.

WARNING: this data is simulated. Metrics computed on it say nothing about real-world
performance. Use the real CIC-IDS2017 CSVs (see data/README.md) for actual results.
"""
import argparse
import numpy as np
import pandas as pd
from config import SAMPLE_CSV, RANDOM_STATE, LABEL_COL

COLS = ["Destination Port", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
        "Total Length of Fwd Packets", "Total Length of Bwd Packets", "Fwd Packet Length Mean",
        "Bwd Packet Length Mean", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean",
        "SYN Flag Count", "RST Flag Count", "ACK Flag Count", "Average Packet Size",
        "Init_Win_bytes_forward", "Init_Win_bytes_backward", "Idle Mean"]

# (ports, duration lognormal, fwd pkts, bwd pkts, fwd len, bwd len, p_syn, p_ack, p_rst, win_f, win_b, idle)
PROFILES = {
    "Benign":     ([80, 443, 53, 8080, 22, 3389], (11, 2), (1.8, 1), (1.6, 1), (4.5, .8), (5, .9), .3, .6, .05, [8192, 29200, 65535], [229, 8192, 28960], (8, 2)),
    "DoS":        ([80, 443], (12, 2.2), (2.2, 1.1), (.9, 1), (3.9, .9), (5.4, 1.1), .15, .7, .1, [256, 8192, 29200], [-1, 235, 8192], (11, 2.5)),
    "PortScan":   (None, (5, 2), (.5, .6), (.3, .6), (1.5, 1.5), (1.2, 1.8), .7, .35, .45, [1024, 29200, 65535], [-1, 0, 229], (0, 0)),
    "BruteForce": ([21, 22], (10.5, 1.5), (2, .7), (1.8, .7), (3.3, .7), (3.8, .8), .25, .8, .05, [8192, 29200], [229, 28960], (7, 1.5)),
    "WebAttack":  ([80, 8080], (11.3, 1.7), (1.9, .9), (1.7, .9), (5, .9), (5.1, 1), .28, .6, .05, [8192, 29200], [229, 8192], (8.3, 2)),
}


RAW_LABELS = {"Benign": "BENIGN", "DoS": "DoS Hulk", "PortScan": "PortScan",
              "BruteForce": "FTP-Patator", "WebAttack": "Web Attack - Brute Force"}


def _make(rng, n, label):
    ports, dur, fp, bp, fl, bl, ps, pa, pr, wf, wb, idle = PROFILES[label]
    ln = lambda p: rng.lognormal(p[0], p[1], n)
    d = {}
    d["Destination Port"] = rng.integers(1, 65535, n) if ports is None else rng.choice(ports, n)
    d["Flow Duration"] = ln(dur)
    d["Total Fwd Packets"] = np.maximum(1, np.round(ln(fp)))
    d["Total Backward Packets"] = np.round(ln(bp)) - 1
    d["Total Backward Packets"] = np.maximum(0, d["Total Backward Packets"])
    d["Fwd Packet Length Mean"] = ln(fl)
    d["Bwd Packet Length Mean"] = ln(bl)
    d["SYN Flag Count"] = rng.binomial(1, ps, n)
    d["ACK Flag Count"] = rng.binomial(1, pa, n)
    d["RST Flag Count"] = rng.binomial(1, pr, n)
    d["Init_Win_bytes_forward"] = rng.choice(wf, n)
    d["Init_Win_bytes_backward"] = rng.choice(wb, n)
    d["Idle Mean"] = ln(idle) if idle[1] else np.zeros(n)
    d["Total Length of Fwd Packets"] = d["Total Fwd Packets"] * d["Fwd Packet Length Mean"]
    d["Total Length of Bwd Packets"] = d["Total Backward Packets"] * d["Bwd Packet Length Mean"]
    secs = np.maximum(d["Flow Duration"], 1) / 1e6
    tot = d["Total Fwd Packets"] + d["Total Backward Packets"]
    d["Flow Bytes/s"] = (d["Total Length of Fwd Packets"] + d["Total Length of Bwd Packets"]) / secs
    d["Flow Packets/s"] = tot / secs
    d["Flow IAT Mean"] = d["Flow Duration"] / np.maximum(tot, 1)
    d["Average Packet Size"] = (d["Fwd Packet Length Mean"] + d["Bwd Packet Length Mean"]) / 2
    df = pd.DataFrame(d)[COLS]
    df[LABEL_COL] = RAW_LABELS[label]  # raw CIC-IDS2017 label text, mapped later by preprocess.map_label
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=12000)
    n = p.parse_args().rows
    rng = np.random.default_rng(RANDOM_STATE)
    mix = {"Benign": .6, "DoS": .12, "PortScan": .12, "BruteForce": .09, "WebAttack": .07}
    df = pd.concat([_make(rng, int(n * f), k) for k, f in mix.items()], ignore_index=True)
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAMPLE_CSV, index=False)
    print(f"Wrote {len(df)} SYNTHETIC rows to {SAMPLE_CSV}\n{df[LABEL_COL].value_counts()}")


if __name__ == "__main__":
    main()

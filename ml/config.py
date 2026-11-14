"""Central configuration for the ML pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ARTIFACTS = ROOT / "ml" / "artifacts"
SAMPLE_CSV = DATA_DIR / "sample_traffic.csv"
LABEL_COL = "Label"
RANDOM_STATE = 42

# Maps raw CIC-IDS2017 labels (matched by lowercase prefix) to coarse classes.
LABEL_RULES = [
    ("benign", "Benign"), ("ddos", "DoS"), ("dos", "DoS"),
    ("portscan", "PortScan"), ("ftp-patator", "BruteForce"),
    ("ssh-patator", "BruteForce"), ("web attack", "WebAttack"),
    ("bot", "Bot"), ("infiltration", "Other"), ("heartbleed", "Other"),
]

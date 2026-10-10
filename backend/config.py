import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR / "samples"
UPLOAD_DIR = BASE_DIR / "uploads"

# Ensure directories exist
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ELA configuration
ELA_QUALITY_1 = 95
ELA_QUALITY_2 = 90
ELA_SCALE_DEFAULT = 15.0
ELA_PATCH_SIZE = 16

# Noise analysis configuration
NOISE_PATCH_SIZE = 32
NOISE_STD_DEV_THRESHOLD = 2.5

# Font & baseline configuration
BASELINE_JUMP_THRESHOLD_PT = 1.5

# CMFD configuration
CMFD_MIN_DIST_PX = 30
CMFD_RATIO_TEST = 0.75

# Ledger validation threshold
LEDGER_TOLERANCE = 0.02

"""Central configuration. Reads from environment / .env for MySQL credentials."""
import os
from pathlib import Path

# ---- Paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

TRAINING_CSV = DATA_DIR / "loan_approval_dataset.csv"
MODEL_PATH = MODEL_DIR / "credit_model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
SQLITE_PATH = DATA_DIR / "credit_app.db"


def _load_dotenv():
    """Minimal .env loader (no external dependency required)."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

# ---- MySQL settings --------------------------------------------------------
MYSQL = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "credit_scoring"),
}

# Force a specific backend: "mysql", "sqlite", or "auto"
DB_BACKEND = os.environ.get("DB_BACKEND", "auto").lower()

# ---- Model / app constants -------------------------------------------------
TARGET = "loan_status"
NUMERIC_FEATURES = [
    "no_of_dependents",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]
CATEGORICAL_FEATURES = ["education", "self_employed"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Number of new user-submitted records that triggers a background retrain
RETRAIN_THRESHOLD = int(os.environ.get("RETRAIN_THRESHOLD", "10"))

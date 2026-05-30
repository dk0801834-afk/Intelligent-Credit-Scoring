"""
Database abstraction layer.

Targets MySQL first. If a MySQL server / driver is unavailable, it transparently
falls back to a local SQLite database so the app always runs. SQL is kept
portable; small dialect differences are handled per-backend.

Tables:
    applications   - every prediction request + result (also used as new
                     training data once an outcome is known / assumed)
    training_runs  - audit log of each (re)training event and its metrics
"""
import sqlite3
import json
import datetime as dt
from contextlib import contextmanager

from . import config

# Try to detect a usable MySQL driver
_MYSQL_DRIVER = None
try:  # pragma: no cover - depends on environment
    import mysql.connector as _mc  # type: ignore
    _MYSQL_DRIVER = "mysql.connector"
except Exception:
    try:
        import pymysql as _pymysql  # type: ignore
        _MYSQL_DRIVER = "pymysql"
    except Exception:
        _MYSQL_DRIVER = None


def _mysql_available() -> bool:
    if config.DB_BACKEND == "sqlite":
        return False
    if _MYSQL_DRIVER is None:
        return False
    try:
        conn = _open_mysql()
        conn.close()
        return True
    except Exception:
        return False


def _open_mysql():
    if _MYSQL_DRIVER == "mysql.connector":
        import mysql.connector as mc
        return mc.connect(
            host=config.MYSQL["host"], port=config.MYSQL["port"],
            user=config.MYSQL["user"], password=config.MYSQL["password"],
            database=config.MYSQL["database"], autocommit=True,
        )
    else:
        import pymysql
        return pymysql.connect(
            host=config.MYSQL["host"], port=config.MYSQL["port"],
            user=config.MYSQL["user"], password=config.MYSQL["password"],
            database=config.MYSQL["database"], autocommit=True,
        )


# Decide backend once at import time
if config.DB_BACKEND == "mysql":
    ACTIVE_BACKEND = "mysql"
elif config.DB_BACKEND == "sqlite":
    ACTIVE_BACKEND = "sqlite"
else:  # auto
    ACTIVE_BACKEND = "mysql" if _mysql_available() else "sqlite"


def backend_name() -> str:
    label = "MySQL" if ACTIVE_BACKEND == "mysql" else "SQLite (fallback)"
    return label


@contextmanager
def get_conn():
    if ACTIVE_BACKEND == "mysql":
        conn = _open_mysql()
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _ph():
    """Parameter placeholder per dialect."""
    return "%s" if ACTIVE_BACKEND == "mysql" else "?"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def init_db():
    auto = (
        "INT AUTO_INCREMENT PRIMARY KEY"
        if ACTIVE_BACKEND == "mysql"
        else "INTEGER PRIMARY KEY AUTOINCREMENT"
    )
    ts = "DATETIME" if ACTIVE_BACKEND == "mysql" else "TEXT"

    applications = f"""
    CREATE TABLE IF NOT EXISTS applications (
        id {auto},
        created_at {ts},
        no_of_dependents INT,
        education VARCHAR(32),
        self_employed VARCHAR(8),
        income_annum BIGINT,
        loan_amount BIGINT,
        loan_term INT,
        cibil_score INT,
        residential_assets_value BIGINT,
        commercial_assets_value BIGINT,
        luxury_assets_value BIGINT,
        bank_asset_value BIGINT,
        predicted_status VARCHAR(16),
        approve_probability DOUBLE,
        risk_band VARCHAR(16),
        actual_status VARCHAR(16),
        used_for_training INT DEFAULT 0
    )
    """
    training_runs = f"""
    CREATE TABLE IF NOT EXISTS training_runs (
        id {auto},
        run_at {ts},
        n_samples INT,
        accuracy DOUBLE,
        roc_auc DOUBLE,
        precision_score DOUBLE,
        recall_score DOUBLE,
        f1 DOUBLE,
        trigger_source VARCHAR(32)
    )
    """
    if ACTIVE_BACKEND == "mysql":
        # Ensure database exists first
        _ensure_mysql_database()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(applications)
        cur.execute(training_runs)


def _ensure_mysql_database():  # pragma: no cover
    import importlib
    driver = importlib.import_module(_MYSQL_DRIVER)
    if _MYSQL_DRIVER == "mysql.connector":
        conn = driver.connect(
            host=config.MYSQL["host"], port=config.MYSQL["port"],
            user=config.MYSQL["user"], password=config.MYSQL["password"],
            autocommit=True,
        )
    else:
        conn = driver.connect(
            host=config.MYSQL["host"], port=config.MYSQL["port"],
            user=config.MYSQL["user"], password=config.MYSQL["password"],
            autocommit=True,
        )
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL['database']}")
    conn.close()


# ---------------------------------------------------------------------------
# Inserts / queries
# ---------------------------------------------------------------------------
def insert_application(record: dict, prediction: dict) -> int:
    p = _ph()
    cols = [
        "created_at", "no_of_dependents", "education", "self_employed",
        "income_annum", "loan_amount", "loan_term", "cibil_score",
        "residential_assets_value", "commercial_assets_value",
        "luxury_assets_value", "bank_asset_value",
        "predicted_status", "approve_probability", "risk_band",
        "actual_status", "used_for_training",
    ]
    vals = [
        dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        record["no_of_dependents"], record["education"], record["self_employed"],
        record["income_annum"], record["loan_amount"], record["loan_term"],
        record["cibil_score"], record["residential_assets_value"],
        record["commercial_assets_value"], record["luxury_assets_value"],
        record["bank_asset_value"],
        prediction["predicted_status"], prediction["approve_probability"],
        prediction["risk_band"], prediction.get("actual_status"), 0,
    ]
    placeholders = ", ".join([p] * len(cols))
    sql = f"INSERT INTO applications ({', '.join(cols)}) VALUES ({placeholders})"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)
        return cur.lastrowid


def count_untrained() -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM applications WHERE used_for_training = 0")
        row = cur.fetchone()
        return int(row[0]) if row else 0


def mark_all_trained():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE applications SET used_for_training = 1 WHERE used_for_training = 0")


def fetch_applications_df():
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM applications ORDER BY id DESC", conn)


def fetch_training_data_df():
    """All stored applications usable as supplementary training rows."""
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM applications", conn)


def log_training_run(metrics: dict, n_samples: int, trigger: str):
    p = _ph()
    sql = (
        f"INSERT INTO training_runs (run_at, n_samples, accuracy, roc_auc, "
        f"precision_score, recall_score, f1, trigger_source) "
        f"VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})"
    )
    vals = [
        dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        n_samples,
        metrics.get("accuracy"), metrics.get("roc_auc"),
        metrics.get("precision"), metrics.get("recall"), metrics.get("f1"),
        trigger,
    ]
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, vals)


def fetch_training_runs_df():
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM training_runs ORDER BY id DESC", conn)

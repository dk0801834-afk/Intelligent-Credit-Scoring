"""
Credit-scoring model: training, evaluation, persistence and inference.

A scikit-learn Pipeline (preprocessing + RandomForest) predicts the probability
that a loan application will be Approved. It combines the base Kaggle-style
training CSV with any new user-submitted records that have a known outcome.
"""
import json
import datetime as dt

import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score,
    recall_score, f1_score, confusion_matrix,
)

from . import config


def _clean_str(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def load_base_dataframe() -> pd.DataFrame:
    """Load the base training CSV (real Kaggle file if present, else synthetic)."""
    df = pd.read_csv(config.TRAINING_CSV)
    df.columns = [c.strip() for c in df.columns]
    for c in config.CATEGORICAL_FEATURES + [config.TARGET]:
        if c in df.columns:
            df[c] = _clean_str(df[c])
    return df


def _combined_training_frame() -> pd.DataFrame:
    """Base CSV + stored applications that carry a known actual_status."""
    base = load_base_dataframe()[config.FEATURES + [config.TARGET]].copy()

    try:
        from . import database
        stored = database.fetch_training_data_df()
    except Exception:
        stored = pd.DataFrame()

    if stored is not None and len(stored):
        stored = stored.copy()
        # Use actual outcome if provided, else fall back to the model's prediction
        status = stored.get("actual_status")
        pred = stored.get("predicted_status")
        if status is None:
            status = pred
        else:
            status = status.where(status.notna() & (status.astype(str) != "None"), pred)
        stored[config.TARGET] = _clean_str(status)
        for c in config.CATEGORICAL_FEATURES:
            if c in stored.columns:
                stored[c] = _clean_str(stored[c])
        keep = [c for c in config.FEATURES + [config.TARGET] if c in stored.columns]
        stored = stored[keep].dropna(subset=[config.TARGET])
        stored = stored[stored[config.TARGET].isin(["Approved", "Rejected"])]
        if len(stored):
            base = pd.concat([base, stored], ignore_index=True)
    return base


def build_pipeline() -> Pipeline:
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    pre = ColumnTransformer([
        ("num", numeric, config.NUMERIC_FEATURES),
        ("cat", categorical, config.CATEGORICAL_FEATURES),
    ])
    clf = RandomForestClassifier(
        n_estimators=250, max_depth=14, min_samples_leaf=3,
        class_weight="balanced", n_jobs=-1, random_state=42,
    )
    return Pipeline([("pre", pre), ("clf", clf)])


def train(trigger: str = "manual", log: bool = True) -> dict:
    """Train (or retrain) the model and persist it + metrics."""
    df = _combined_training_frame().dropna(subset=[config.TARGET])
    X = df[config.FEATURES]
    y = (df[config.TARGET] == "Approved").astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipe = build_pipeline()
    pipe.fit(X_tr, y_tr)

    proba = pipe.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    cm = confusion_matrix(y_te, pred).tolist()

    metrics = {
        "accuracy": float(accuracy_score(y_te, pred)),
        "roc_auc": float(roc_auc_score(y_te, proba)),
        "precision": float(precision_score(y_te, pred, zero_division=0)),
        "recall": float(recall_score(y_te, pred, zero_division=0)),
        "f1": float(f1_score(y_te, pred, zero_division=0)),
        "n_samples": int(len(df)),
        "confusion_matrix": cm,
        "trained_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trigger": trigger,
    }

    # Feature importances mapped back to readable names
    try:
        ohe = pipe.named_steps["pre"].named_transformers_["cat"].named_steps["onehot"]
        cat_names = list(ohe.get_feature_names_out(config.CATEGORICAL_FEATURES))
        names = config.NUMERIC_FEATURES + cat_names
        imps = pipe.named_steps["clf"].feature_importances_
        metrics["feature_importance"] = sorted(
            [{"feature": n, "importance": float(i)} for n, i in zip(names, imps)],
            key=lambda d: d["importance"], reverse=True,
        )
    except Exception:
        metrics["feature_importance"] = []

    joblib.dump(pipe, config.MODEL_PATH)
    config.METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    if log:
        try:
            from . import database
            database.log_training_run(metrics, metrics["n_samples"], trigger)
            database.mark_all_trained()
        except Exception:
            pass
    return metrics


def load_model():
    if not config.MODEL_PATH.exists():
        train(trigger="bootstrap")
    return joblib.load(config.MODEL_PATH)


def load_metrics() -> dict:
    if config.METRICS_PATH.exists():
        return json.loads(config.METRICS_PATH.read_text())
    return {}


def _risk_band(p: float) -> str:
    if p >= 0.75:
        return "Low Risk"
    if p >= 0.5:
        return "Moderate Risk"
    if p >= 0.3:
        return "High Risk"
    return "Very High Risk"


def predict(record: dict) -> dict:
    """Predict approval probability + risk band for one application."""
    model = load_model()
    row = pd.DataFrame([{k: record.get(k) for k in config.FEATURES}])
    for c in config.CATEGORICAL_FEATURES:
        row[c] = _clean_str(row[c])
    proba = float(model.predict_proba(row)[0, 1])
    status = "Approved" if proba >= 0.5 else "Rejected"
    return {
        "approve_probability": proba,
        "predicted_status": status,
        "risk_band": _risk_band(proba),
        "credit_score_points": int(round(300 + proba * 600)),  # mapped 300-900
    }


if __name__ == "__main__":
    m = train(trigger="cli")
    print(json.dumps({k: v for k, v in m.items()
                      if k not in ("feature_importance", "confusion_matrix")}, indent=2))

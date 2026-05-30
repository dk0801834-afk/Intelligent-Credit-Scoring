"""
Risk Assessment: Intelligent Credit Scoring App
================================================
Streamlit + scikit-learn + MySQL (SQLite fallback)

Features
  * Interactive scoring form -> approval probability, mapped credit score & risk band
  * Persists every application to the database
  * Background model retraining triggered automatically as new data accrues
  * Animated, hover-rich, interactive analytics dashboard
"""
import time
import datetime as dt

import pandas as pd
import streamlit as st

import sys
import os

# Add the root directory to the system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st


from src import config, database, model, retrain, charts
from src.styles import CSS

st.set_page_config(
    page_title="Intelligent Credit Scoring",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# One-time bootstrap (DB + model)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def bootstrap():
    database.init_db()
    model.load_model()  # trains a bootstrap model if none exists
    return True


bootstrap()


def risk_badge(band: str) -> str:
    cls = "low" if "Low" in band else ("mod" if "Moderate" in band else "high")
    return f'<span class="badge {cls}">{band}</span>'


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💳 Credit Scoring")
    st.caption("Intelligent Risk Assessment Engine")
    st.divider()

    st.markdown("**System status**")
    st.markdown(f"🗄️ Database: `{database.backend_name()}`")

    pending = database.count_untrained()
    st.markdown(f"🆕 New records pending: `{pending} / {config.RETRAIN_THRESHOLD}`")
    st.progress(min(pending / max(config.RETRAIN_THRESHOLD, 1), 1.0))

    if retrain.is_training():
        st.markdown('<div class="train-banner">🧠 Retraining in background…</div>',
                    unsafe_allow_html=True)
    else:
        if st.button("🔄 Retrain model now", use_container_width=True):
            if retrain.trigger_retrain("manual (sidebar)"):
                st.toast("Background retraining started", icon="🧠")
            else:
                st.toast("A training run is already in progress", icon="⏳")

    st.divider()
    met = model.load_metrics()
    if met:
        st.markdown("**Active model**")
        st.metric("Accuracy", f"{met.get('accuracy', 0)*100:.1f}%")
        st.metric("ROC-AUC", f"{met.get('roc_auc', 0):.3f}")
        st.caption(f"Trained: {met.get('trained_at', '—')}")
        st.caption(f"Samples: {met.get('n_samples', 0):,}")
    st.divider()
    st.caption("Reference schema based on the Kaggle "
               "*Loan Approval Prediction* dataset.")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>Risk Assessment · Intelligent Credit Scoring</h1>
      <p>Predict loan approval probability, map it to a credit score, and let the
      model learn continuously from new applications.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_score, tab_dash, tab_model = st.tabs(
    ["🎯  Score an Application", "📊  Analytics Dashboard", "🧠  Model & Retraining"]
)

# ===========================================================================
# TAB 1 — Score an application
# ===========================================================================
with tab_score:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.subheader("Applicant details")
        with st.form("score_form"):
            c1, c2 = st.columns(2)
            with c1:
                no_of_dependents = st.slider("Number of dependents", 0, 6, 1)
                education = st.selectbox("Education", ["Graduate", "Not Graduate"])
                self_employed = st.selectbox("Self employed", ["No", "Yes"])
                cibil_score = st.slider("CIBIL credit score", 300, 900, 700)
                loan_term = st.select_slider(
                    "Loan term (years)", options=list(range(2, 21, 2)), value=10)
            with c2:
                income_annum = st.number_input(
                    "Annual income", 100000, 100000000, 5000000, step=100000)
                loan_amount = st.number_input(
                    "Loan amount requested", 100000, 200000000, 12000000, step=100000)
                residential_assets_value = st.number_input(
                    "Residential assets", 0, 100000000, 6000000, step=100000)
                commercial_assets_value = st.number_input(
                    "Commercial assets", 0, 100000000, 3000000, step=100000)
                luxury_assets_value = st.number_input(
                    "Luxury assets", 0, 100000000, 9000000, step=100000)
                bank_asset_value = st.number_input(
                    "Bank asset value", 0, 100000000, 4000000, step=100000)

            known = st.checkbox(
                "I know the real outcome (use this row to improve training)")
            actual_status = None
            if known:
                actual_status = st.radio(
                    "Actual outcome", ["Approved", "Rejected"], horizontal=True)

            submitted = st.form_submit_button("⚡ Assess credit risk",
                                              use_container_width=True)

        record = {
            "no_of_dependents": no_of_dependents,
            "education": education,
            "self_employed": self_employed,
            "income_annum": int(income_annum),
            "loan_amount": int(loan_amount),
            "loan_term": int(loan_term),
            "cibil_score": int(cibil_score),
            "residential_assets_value": int(residential_assets_value),
            "commercial_assets_value": int(commercial_assets_value),
            "luxury_assets_value": int(luxury_assets_value),
            "bank_asset_value": int(bank_asset_value),
        }

    with right:
        st.subheader("Risk decision")
        if submitted:
            pred = model.predict(record)
            pred["actual_status"] = actual_status
            database.insert_application(record, pred)
            started = retrain.maybe_retrain()  # background trigger

            good = pred["predicted_status"] == "Approved"
            cls = "good" if good else "bad"
            icon = "✅" if good else "⛔"
            st.markdown(
                f"""
                <div class="result {cls}">
                  <div class="big">{icon} {pred['predicted_status']}</div>
                  <div class="score">{pred['credit_score_points']}</div>
                  <div style="color:var(--muted)">mapped credit score (300–900)</div>
                  <div style="margin-top:10px">{risk_badge(pred['risk_band'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(charts.gauge(pred["approve_probability"]),
                            use_container_width=True, config={"displayModeBar": False})
            if started:
                st.success("Enough new data collected — background retraining started! 🧠")
            st.caption("This application has been saved to the database.")
        else:
            st.info("Fill in the applicant details and click **Assess credit risk** "
                    "to see the probability gauge, mapped score and risk band.")
            met = model.load_metrics()
            st.plotly_chart(charts.feature_importance(met.get("feature_importance", [])),
                            use_container_width=True, config={"displayModeBar": False})

# ===========================================================================
# TAB 2 — Analytics dashboard
# ===========================================================================
with tab_dash:
    base = model.load_base_dataframe()
    apps = database.fetch_applications_df()

    total_apps = len(apps)
    approve_rate = (base["loan_status"].str.strip().eq("Approved").mean() * 100)
    avg_cibil = base["cibil_score"].mean()
    avg_loan = base["loan_amount"].mean()

    k1, k2, k3, k4 = st.columns(4)
    cards = [
        (k1, "Reference records", f"{len(base):,}", "training base"),
        (k2, "Approval rate", f"{approve_rate:.1f}%", "in reference data"),
        (k3, "Avg CIBIL score", f"{avg_cibil:.0f}", "out of 900"),
        (k4, "Live applications", f"{total_apps:,}", "scored in this app"),
    ]
    for col, label, value, sub in cards:
        col.markdown(
            f'<div class="kpi"><div class="label">{label}</div>'
            f'<div class="value">{value}</div><div class="sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    r1c1, r1c2 = st.columns([1, 1.3], gap="large")
    with r1c1:
        st.plotly_chart(charts.approval_donut(base), use_container_width=True)
    with r1c2:
        st.plotly_chart(charts.cibil_hist(base), use_container_width=True)

    st.plotly_chart(charts.income_vs_loan(base), use_container_width=True)

    st.subheader("Recent live applications")
    if total_apps:
        show_cols = ["created_at", "cibil_score", "income_annum", "loan_amount",
                     "predicted_status", "approve_probability", "risk_band"]
        show_cols = [c for c in show_cols if c in apps.columns]
        view = apps[show_cols].head(15).copy()
        if "approve_probability" in view:
            view["approve_probability"] = (view["approve_probability"] * 100).round(1)
        st.dataframe(view, use_container_width=True, hide_index=True)
    else:
        st.info("No live applications yet. Score one in the first tab.")

# ===========================================================================
# TAB 3 — Model & retraining
# ===========================================================================
with tab_model:
    status = retrain.get_status()
    met = model.load_metrics()

    if retrain.is_training():
        st.markdown('<div class="train-banner">🧠 A background retraining run is '
                    'currently in progress…</div>', unsafe_allow_html=True)
        if st.button("↻ Refresh status"):
            st.rerun()

    m1, m2, m3, m4, m5 = st.columns(5)
    for col, label, key, fmt in [
        (m1, "Accuracy", "accuracy", "{:.1%}"),
        (m2, "ROC-AUC", "roc_auc", "{:.3f}"),
        (m3, "Precision", "precision", "{:.1%}"),
        (m4, "Recall", "recall", "{:.1%}"),
        (m5, "F1 score", "f1", "{:.3f}"),
    ]:
        val = met.get(key)
        txt = fmt.format(val) if val is not None else "—"
        col.markdown(
            f'<div class="kpi"><div class="label">{label}</div>'
            f'<div class="value">{txt}</div></div>', unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        runs = database.fetch_training_runs_df()
        st.plotly_chart(charts.metric_history(runs), use_container_width=True)
    with c2:
        st.plotly_chart(charts.confusion(met.get("confusion_matrix")),
                        use_container_width=True)

    st.plotly_chart(charts.feature_importance(met.get("feature_importance", [])),
                    use_container_width=True)

    # st.subheader("How background retraining works")
    # st.markdown(
    #     f"""
    #     - Every scored application is stored in the **{database.backend_name()}** database.
    #     - When **{config.RETRAIN_THRESHOLD}** new records accumulate, a **daemon thread**
    #       retrains the model **without blocking** the interface.
    #     - Rows where you supplied the *real outcome* are used as ground-truth labels;
    #       otherwise the model's own prediction seeds the next round.
    #     - Each run is logged to `training_runs` so you can track performance over time
    #       in the chart above.
    #     """
    # )

    with st.expander("📜 Training run history"):
        runs = database.fetch_training_runs_df()
        if runs is not None and len(runs):
            st.dataframe(runs, use_container_width=True, hide_index=True)
        else:
            st.info("No retraining runs logged yet.")

# Auto-refresh the page lightly while training so users see completion.
if retrain.is_training():
    time.sleep(2)
    st.rerun()

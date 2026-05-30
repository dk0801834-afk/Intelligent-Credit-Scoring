"""Interactive Plotly charts with hover + transition animations, dark themed."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

TEMPLATE = "plotly_dark"
ACCENT = "#6c8cff"
ACCENT2 = "#9b6cff"
GOOD = "#22c55e"
BAD = "#ef4444"
PAPER = "rgba(0,0,0,0)"


def _base(fig, height=340, title=None):
    fig.update_layout(
        template=TEMPLATE, paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        font=dict(family="Inter", color="#e8ecf6"),
        title=dict(text=title, x=0.02, font=dict(size=16)) if title else None,
        hoverlabel=dict(bgcolor="#1b2030", font_size=12, font_family="Inter"),
        transition=dict(duration=600, easing="cubic-in-out"),
    )
    return fig


def gauge(prob: float):
    val = prob * 100
    color = GOOD if val >= 50 else BAD
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=val,
        number={"suffix": "%", "font": {"size": 40}},
        delta={"reference": 50, "increasing": {"color": GOOD}, "decreasing": {"color": BAD}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#9aa6c0"},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "rgba(255,255,255,.04)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "rgba(239,68,68,.25)"},
                {"range": [30, 50], "color": "rgba(245,158,11,.25)"},
                {"range": [50, 75], "color": "rgba(108,140,255,.25)"},
                {"range": [75, 100], "color": "rgba(34,197,94,.25)"},
            ],
            "threshold": {"line": {"color": "#fff", "width": 3}, "thickness": 0.8, "value": 50},
        },
        title={"text": "Approval Probability"},
    ))
    return _base(fig, height=300)


def feature_importance(items):
    if not items:
        return _base(go.Figure(), title="Feature Importance")
    df = pd.DataFrame(items[:10]).sort_values("importance")
    fig = go.Figure(go.Bar(
        x=df["importance"], y=df["feature"], orientation="h",
        marker=dict(color=df["importance"], colorscale=[[0, ACCENT2], [1, ACCENT]],
                    line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.3f}<extra></extra>",
    ))
    return _base(fig, height=380, title="What drives the decision (feature importance)")


def approval_donut(df: pd.DataFrame, col="loan_status"):
    counts = df[col].astype(str).str.strip().value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=.62,
        marker=dict(colors=[GOOD if "Approv" in str(l) else BAD for l in counts.index],
                    line=dict(color="#0f1117", width=2)),
        pull=[0.04] * len(counts),
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
    ))
    fig.update_traces(textinfo="percent+label", textfont_size=13)
    return _base(fig, height=320, title="Approval distribution")


def cibil_hist(df: pd.DataFrame):
    d = df.copy()
    d["loan_status"] = d["loan_status"].astype(str).str.strip()
    fig = px.histogram(
        d, x="cibil_score", color="loan_status", nbins=40, barmode="overlay",
        color_discrete_map={"Approved": GOOD, "Rejected": BAD}, opacity=0.75,
    )
    fig.update_traces(hovertemplate="CIBIL: %{x}<br>Count: %{y}<extra></extra>")
    return _base(fig, height=340, title="CIBIL score vs. outcome")


def income_vs_loan(df: pd.DataFrame):
    d = df.copy()
    d["loan_status"] = d["loan_status"].astype(str).str.strip()
    fig = px.scatter(
        d.sample(min(len(d), 1500), random_state=1),
        x="income_annum", y="loan_amount", color="loan_status",
        size="cibil_score", size_max=14, opacity=0.7,
        color_discrete_map={"Approved": GOOD, "Rejected": BAD},
        labels={"income_annum": "Annual income", "loan_amount": "Loan amount"},
    )
    fig.update_traces(hovertemplate="Income: %{x:,}<br>Loan: %{y:,}<extra></extra>")
    return _base(fig, height=380, title="Income vs. loan amount (bubble = CIBIL)")


def metric_history(runs: pd.DataFrame):
    if runs is None or runs.empty:
        return _base(go.Figure(), title="Model performance over retraining runs")
    d = runs.sort_values("id")
    fig = go.Figure()
    for col, name, color in [
        ("accuracy", "Accuracy", ACCENT),
        ("roc_auc", "ROC-AUC", GOOD),
        ("f1", "F1", ACCENT2),
    ]:
        if col in d.columns:
            fig.add_trace(go.Scatter(
                x=list(range(1, len(d) + 1)), y=d[col], mode="lines+markers",
                name=name, line=dict(width=3, color=color, shape="spline"),
                marker=dict(size=8),
                hovertemplate=f"{name}: %{{y:.3f}}<extra></extra>",
            ))
    fig.update_layout(xaxis_title="Training run", yaxis=dict(range=[0, 1.02]))
    return _base(fig, height=340, title="Model performance over retraining runs")


def confusion(cm):
    if not cm:
        return _base(go.Figure())
    z = np.array(cm)
    labels = ["Rejected", "Approved"]
    fig = go.Figure(go.Heatmap(
        z=z, x=[f"Pred {l}" for l in labels], y=[f"True {l}" for l in labels],
        colorscale=[[0, "#161a26"], [1, ACCENT]], showscale=False,
        text=z, texttemplate="%{text}", textfont={"size": 18},
        hovertemplate="%{y} / %{x}: %{z}<extra></extra>",
    ))
    return _base(fig, height=300, title="Confusion matrix (latest model)")

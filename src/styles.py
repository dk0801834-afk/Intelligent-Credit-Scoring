"""Custom CSS: gradients, hover effects, transitions and entrance animations."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg-1:#0f1117; --bg-2:#161a26; --card:#1b2030; --card-2:#222a3d;
  --accent:#6c8cff; --accent-2:#9b6cff; --good:#22c55e; --warn:#f59e0b;
  --bad:#ef4444; --text:#e8ecf6; --muted:#9aa6c0; --border:#2a3450;
}

html, body, [class*="css"] { font-family:'Inter',sans-serif; }

.stApp {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(108,140,255,.18), transparent 60%),
    radial-gradient(1000px 500px at 100% 0%, rgba(155,108,255,.16), transparent 55%),
    linear-gradient(180deg, var(--bg-1), var(--bg-2));
  color: var(--text);
}

/* ---------- Hero ---------- */
.hero {
  border-radius:22px; padding:30px 34px; margin-bottom:10px;
  background:linear-gradient(120deg, rgba(108,140,255,.22), rgba(155,108,255,.18));
  border:1px solid var(--border);
  box-shadow:0 18px 50px rgba(0,0,0,.45);
  animation:fadeDown .7s cubic-bezier(.2,.7,.2,1) both;
  position:relative; overflow:hidden;
}
.hero::after{
  content:""; position:absolute; inset:0;
  background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.08) 50%,transparent 70%);
  transform:translateX(-100%); animation:shine 4.5s ease-in-out infinite;
}
.hero h1{ font-size:2.0rem; font-weight:800; margin:0;
  background:linear-gradient(90deg,#fff,#c9d4ff); -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;}
.hero p{ color:var(--muted); margin:.4rem 0 0; font-size:1.02rem;}

/* ---------- Metric / KPI cards ---------- */
.kpi{
  background:linear-gradient(160deg,var(--card),var(--card-2));
  border:1px solid var(--border); border-radius:18px; padding:18px 20px;
  transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease;
  animation:fadeUp .6s ease both;
}
.kpi:hover{ transform:translateY(-6px) scale(1.015);
  box-shadow:0 16px 40px rgba(108,140,255,.28); border-color:var(--accent);}
.kpi .label{ color:var(--muted); font-size:.82rem; text-transform:uppercase; letter-spacing:.08em;}
.kpi .value{ font-size:1.85rem; font-weight:800; margin-top:4px;}
.kpi .sub{ color:var(--muted); font-size:.8rem; margin-top:2px;}

/* ---------- Result card ---------- */
.result{
  border-radius:20px; padding:26px; text-align:center; margin-top:6px;
  border:1px solid var(--border);
  animation:pop .6s cubic-bezier(.18,.9,.3,1.2) both;
}
.result.good{ background:linear-gradient(160deg, rgba(34,197,94,.18), rgba(34,197,94,.05)); border-color:rgba(34,197,94,.5);}
.result.bad{ background:linear-gradient(160deg, rgba(239,68,68,.18), rgba(239,68,68,.05)); border-color:rgba(239,68,68,.5);}
.result .big{ font-size:2.4rem; font-weight:800;}
.result .score{ font-size:3.2rem; font-weight:800; letter-spacing:-1px;}

.badge{ display:inline-block; padding:6px 14px; border-radius:999px; font-weight:600;
  font-size:.85rem; border:1px solid var(--border); animation:fadeIn .8s ease both;}
.badge.low{ background:rgba(34,197,94,.15); color:#7ef0a8; border-color:rgba(34,197,94,.4);}
.badge.mod{ background:rgba(245,158,11,.15); color:#fbd27a; border-color:rgba(245,158,11,.4);}
.badge.high{ background:rgba(239,68,68,.15); color:#ff9d9d; border-color:rgba(239,68,68,.4);}

/* ---------- Buttons ---------- */
.stButton>button{
  background:linear-gradient(90deg,var(--accent),var(--accent-2)); color:#fff;
  border:none; border-radius:12px; padding:.6rem 1.2rem; font-weight:600;
  transition:transform .2s ease, box-shadow .2s ease, filter .2s ease;
  box-shadow:0 8px 22px rgba(108,140,255,.35);
}
.stButton>button:hover{ transform:translateY(-2px) scale(1.02); filter:brightness(1.08);
  box-shadow:0 12px 30px rgba(155,108,255,.5);}
.stButton>button:active{ transform:translateY(0) scale(.99);}

/* sidebar */
section[data-testid="stSidebar"]{ background:linear-gradient(180deg,#12151f,#0d1018);
  border-right:1px solid var(--border);}

/* tabs */
.stTabs [data-baseweb="tab"]{ transition:color .2s ease, border-color .2s ease;}
.stTabs [data-baseweb="tab"]:hover{ color:var(--accent);}

/* training banner */
.train-banner{ border-radius:14px; padding:12px 18px; margin:8px 0;
  background:linear-gradient(90deg, rgba(108,140,255,.18), rgba(155,108,255,.12));
  border:1px solid var(--border); animation:pulse 1.8s ease-in-out infinite;}

/* dataframe rounding */
[data-testid="stDataFrame"]{ border-radius:14px; overflow:hidden; border:1px solid var(--border);}

/* ---------- Keyframes ---------- */
@keyframes fadeDown{from{opacity:0;transform:translateY(-18px);}to{opacity:1;transform:none;}}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px);}to{opacity:1;transform:none;}}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
@keyframes pop{0%{opacity:0;transform:scale(.9);}100%{opacity:1;transform:scale(1);}}
@keyframes shine{0%{transform:translateX(-100%);}55%,100%{transform:translateX(120%);}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(108,140,255,.4);}50%{box-shadow:0 0 0 10px rgba(108,140,255,0);}}
</style>
"""

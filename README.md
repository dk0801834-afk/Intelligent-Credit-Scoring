# Intelligent-Credit-Scoring
An intelligent credit scoring and risk evaluation web app built with Streamlit, MySQL, and Machine Learning. Currently in active development.

# 💳 Risk Assessment · Intelligent Credit Scoring App

An interactive credit-risk scoring application built with **Python + Streamlit**,
a **scikit-learn** machine-learning pipeline, and **MySQL** for storage (with an
automatic **SQLite** fallback so it runs anywhere). The model **retrains itself
in the background** as new applications are submitted.

The training schema mirrors the Kaggle
[Loan Approval Prediction dataset](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset).

---

## ✨ Features

| Area | What you get |
|------|--------------|
| **Scoring** | Enter applicant details → approval probability, mapped credit score (300–900) & risk band |
| **Database** | Every application stored in **MySQL** (auto-falls back to **SQLite**) |
| **Background retraining** | A daemon thread retrains the model when enough new records accrue — UI never blocks |
| **Interactive dashboard** | Plotly charts: gauge, donut, histogram, bubble scatter, feature importance, confusion matrix, performance-over-time |
| **UX polish** | Gradient theme, hover lift effects, CSS transitions & entrance animations |
| **Continuous learning** | Rows with a known real outcome become labelled training data |

---

## 🚀 Quick start

```bash
cd credit_scoring_app
pip install -r requirements.txt

# (optional) generate / regenerate synthetic training data
python -m src.generate_data

streamlit run app.py
```

Open the URL Streamlit prints (default http://localhost:8501).

> The app works **out of the box** with no MySQL server — it uses SQLite
> automatically. To use MySQL, see below.

---

## 🗄️ Using MySQL

1. Install a driver (already in `requirements.txt`):
   `mysql-connector-python` or `PyMySQL`.
2. Copy `.env.example` → `.env` and set your credentials:

```env
DB_BACKEND=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=credit_scoring
```

The app creates the database and tables automatically on first run.
Set `DB_BACKEND=auto` to prefer MySQL but gracefully fall back to SQLite.

---

## 📂 Using the real Kaggle data

Download `loan_approval_dataset.csv` from the
[Kaggle dataset](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset)
and drop it into the `data/` folder (replacing the synthetic file). The app
detects identical column names and uses it automatically — then click
**“Retrain model now”** in the sidebar.

---

## 🧠 How background retraining works

1. Each scored application is written to the `applications` table.
2. When `RETRAIN_THRESHOLD` (default **10**) new rows accumulate,
   `retrain.maybe_retrain()` spawns a **daemon thread**.
3. The thread rebuilds the training set (**base CSV + new records**), retrains the
   pipeline, evaluates it, and saves the new model + metrics.
4. A row is appended to `training_runs`, visible in the **Model & Retraining** tab.

A non-blocking lock ensures only one retrain runs at a time.

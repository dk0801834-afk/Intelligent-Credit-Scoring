"""
Generate realistic synthetic training data that mirrors the schema of the Kaggle
"Loan Approval Prediction" dataset:
https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset

Columns (identical to the Kaggle CSV):
    loan_id, no_of_dependents, education, self_employed, income_annum,
    loan_amount, loan_term, cibil_score, residential_assets_value,
    commercial_assets_value, luxury_assets_value, bank_asset_value, loan_status

If you have the real Kaggle file, just drop `loan_approval_dataset.csv` into the
`data/` folder and the app will use it automatically.
"""
import os
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)


def generate(n: int = 4269) -> pd.DataFrame:
    """Create n synthetic loan applications with realistic, learnable structure."""
    no_of_dependents = RNG.integers(0, 6, n)
    education = RNG.choice(["Graduate", "Not Graduate"], n, p=[0.55, 0.45])
    self_employed = RNG.choice(["Yes", "No"], n, p=[0.5, 0.5])

    # Annual income (in currency units, like the Kaggle set: hundreds of thousands)
    income_annum = RNG.integers(200000, 9900000, n)

    # Loan amount loosely correlated with income
    loan_amount = (income_annum * RNG.uniform(0.8, 4.0, n)).astype(int)
    loan_term = RNG.choice([2, 4, 6, 8, 10, 12, 14, 16, 18, 20], n)

    # CIBIL credit score (300-900)
    cibil_score = RNG.integers(300, 900, n)

    residential_assets_value = RNG.integers(-100000, 29000000, n)
    commercial_assets_value = RNG.integers(0, 19400000, n)
    luxury_assets_value = (income_annum * RNG.uniform(0.5, 3.5, n)).astype(int)
    bank_asset_value = RNG.integers(0, 14700000, n)

    total_assets = (
        np.clip(residential_assets_value, 0, None)
        + commercial_assets_value
        + luxury_assets_value
        + bank_asset_value
    )
    # Debt-to-income style ratio
    loan_to_income = loan_amount / np.maximum(income_annum, 1)
    asset_coverage = total_assets / np.maximum(loan_amount, 1)

    # Build a latent "approval score". CIBIL score dominates (as in the real data),
    # plus healthy asset coverage and reasonable loan-to-income help.
    z = (
        0.011 * (cibil_score - 700)
        + 0.45 * (asset_coverage - 1.0)
        - 0.55 * (loan_to_income - 2.5)
        + 0.15 * (education == "Graduate").astype(float)
        - 0.05 * no_of_dependents
        + RNG.normal(0, 1.0, n)
    )
    prob_approve = 1 / (1 + np.exp(-z))
    loan_status = np.where(prob_approve > 0.5, "Approved", "Rejected")

    df = pd.DataFrame(
        {
            "loan_id": np.arange(1, n + 1),
            "no_of_dependents": no_of_dependents,
            "education": [f" {e}" for e in education],  # Kaggle file has leading spaces
            "self_employed": [f" {s}" for s in self_employed],
            "income_annum": income_annum,
            "loan_amount": loan_amount,
            "loan_term": loan_term,
            "cibil_score": cibil_score,
            "residential_assets_value": residential_assets_value,
            "commercial_assets_value": commercial_assets_value,
            "luxury_assets_value": luxury_assets_value,
            "bank_asset_value": bank_asset_value,
            "loan_status": [f" {s}" for s in loan_status],
        }
    )
    return df


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "data", "loan_approval_dataset.csv")
    df = generate()
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows -> {out}")
    print(df["loan_status"].value_counts())

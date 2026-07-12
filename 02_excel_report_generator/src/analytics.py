from dataclasses import dataclass
import pandas as pd

REQUIRED = ["order_id", "date", "customer", "salesperson", "product", "region", "revenue"]

@dataclass(frozen=True)
class Analysis:
    orders: int
    revenue: float
    average_order: float
    highest_sale: float
    lowest_sale: float
    by_product: pd.Series
    by_salesperson: pd.Series
    by_region: pd.Series
    by_month: pd.Series

def load_sales(path):
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing: raise ValueError("Missing required columns: " + ", ".join(missing))
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="raise")
    if df.empty: raise ValueError("Sales data is empty")
    if (df["revenue"] < 0).any(): raise ValueError("Revenue cannot be negative")
    return df.sort_values(["date", "order_id"]).reset_index(drop=True)

def analyse(df):
    revenue = df["revenue"]
    month = df.assign(month=df["date"].dt.strftime("%b %Y")).groupby("month", sort=False)["revenue"].sum()
    return Analysis(len(df), float(revenue.sum()), float(revenue.mean()), float(revenue.max()), float(revenue.min()),
        df.groupby("product")["revenue"].sum().sort_values(ascending=False),
        df.groupby("salesperson")["revenue"].sum().sort_values(ascending=False),
        df.groupby("region")["revenue"].sum().sort_values(ascending=False), month)

"""Shared configuration, data access and helpers for the Cardstel Ops Tracker.

Privacy: no "Job ID" field is stored, shown or exported anywhere in this app.
If an imported CSV contains one, it is dropped on load.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
DATE_FMT = "%d/%m/%y"  # e.g. 13/08/26
VIEWS = ["Daily", "Monthly", "Quarterly", "Yearly"]
SHIFTS = ["Morning", "Afternoon", "Night"]
ATT_STATUS = ["Present", "Late", "Absent", "Leave"]
WORK_STATUS = ["Completed", "In Progress", "Pending"]
ROLES = ["Operator", "Supervisor", "Staff", "Manager"]

# Suggested activities per department (new ones can be typed in the work-log form)
ACTIVITIES = {
    "Business": ["Quotations Issued", "Client Meetings", "Orders Received", "Invoices Raised"],
    "Admin": ["Documents Processed", "Procurement Requests", "Correspondence Handled", "Facility Requests"],
    "QC": ["Inspections Completed", "Samples Tested", "Rejects Logged", "Reports Issued"],
    "Vault": ["Items Received", "Items Issued", "Stock Reconciliations", "Destruction Records"],
    "Fulfillment": ["Orders Packed", "Dispatches Made", "Deliveries Confirmed", "Returns Processed"],
}

# CSV column layout per dataset. In memory, "Production Date" -> "Date" and the
# work log's "Department" -> "Unit" so every dataset can be filtered the same way.
SCHEMA = {
    "production": ["Production Date", "Unit", "Shift Type", "Client", "Product Type",
                   "Quantity Produced", "Machine Used", "Operator Name"],
    "work_log": ["Date", "Department", "Staff Name", "Activity", "Quantity", "Status", "Remarks"],
    "attendance": ["Date", "Staff Name", "Unit", "Status", "Time In", "Time Out", "Remarks"],
    "staff": ["Staff Name", "Unit", "Role"],
    "org": ["Unit", "Type", "Machines", "Output Unit", "Min Operators", "Shifts Per Day"],
    "targets": ["Scope", "Unit", "Name", "Daily Target", "Monthly Target", "Yearly Target"],
}
RENAME = {"production": {"Production Date": "Date"}, "work_log": {"Department": "Unit"}}
NUMERIC = {
    "production": ["Quantity Produced"], "work_log": ["Quantity"],
    "org": ["Min Operators", "Shifts Per Day"],
    "targets": ["Daily Target", "Monthly Target", "Yearly Target"],
}


# ----------------------------------------------------------------------------
# Data access
# ----------------------------------------------------------------------------
def parse_dates(s: pd.Series) -> pd.Series:
    """Parse dd/mm/yy first, then fall back to flexible day-first parsing."""
    raw = s.astype(str).str.strip()
    out = pd.to_datetime(raw, format=DATE_FMT, errors="coerce")
    return out.fillna(pd.to_datetime(raw, dayfirst=True, errors="coerce", format="mixed"))


def clean(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Validate and type-cast a raw dataframe into the in-memory layout."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop(columns=[c for c in df.columns if c.lower().replace(" ", "").replace("_", "") == "jobid"])
    if name == "production" and "Card Type" in df and "Product Type" not in df:
        df = df.rename(columns={"Card Type": "Product Type"})  # legacy file
    ren = RENAME.get(name, {})
    df = df.rename(columns=ren)
    cols = [ren.get(c, c) for c in SCHEMA[name]]
    if name == "production" and "Unit" not in df:
        df["Unit"] = "Card Perso"  # legacy single-unit file
    for col in cols:
        if col not in df:
            df[col] = ""
    df = df[cols].copy()
    for col in cols:
        if col == "Date":
            continue
        if col in NUMERIC.get(name, []):
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce").fillna(0).round().astype(int)
        else:
            df[col] = df[col].fillna("").astype(str).str.strip()
    if "Date" in df:
        df["Date"] = parse_dates(df["Date"])
        df = df.dropna(subset=["Date"]).sort_values("Date")
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read(name: str, path: str, mtime: float) -> pd.DataFrame:
    return clean(name, pd.read_csv(path))


def load(name: str) -> pd.DataFrame:
    """Load a dataset from ./data (cache refreshes whenever the file changes)."""
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        return clean(name, pd.DataFrame(columns=SCHEMA[name]))
    return _read(name, str(path), path.stat().st_mtime)


def csv_frame(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Convert an in-memory frame back to the CSV layout (dd/mm/yy dates)."""
    out = df.copy()
    if "Date" in out:
        out["Date"] = pd.to_datetime(out["Date"]).dt.strftime(DATE_FMT)
    inv = {v: k for k, v in RENAME.get(name, {}).items()}
    return out.rename(columns=inv)[SCHEMA[name]]


def save(name: str, df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    csv_frame(name, df).to_csv(DATA_DIR / f"{name}.csv", index=False)
    st.cache_data.clear()


def append(name: str, rows: list[dict]) -> None:
    save(name, pd.concat([load(name), pd.DataFrame(rows)], ignore_index=True))


def download(df: pd.DataFrame, filename: str, label: str = "⬇️ Download CSV") -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv")


# ----------------------------------------------------------------------------
# Organisation helpers
# ----------------------------------------------------------------------------
def org() -> pd.DataFrame:
    return load("org")


def units_of(kind: str) -> list[str]:
    o = org()
    return o.loc[o["Type"] == kind, "Unit"].tolist()


def machines_of(unit: str) -> list[str]:
    r = org()[org()["Unit"] == unit]
    return [] if r.empty else [m.strip() for m in r.iloc[0]["Machines"].split(";") if m.strip()]


def staff_of(unit: str, role: str | None = None) -> list[str]:
    s = load("staff")
    s = s[s["Unit"] == unit]
    return (s[s["Role"] == role] if role else s)["Staff Name"].tolist()


def coverage_gaps() -> pd.DataFrame:
    """Production units with fewer operators than their minimum."""
    rows = []
    for _, u in org()[org()["Type"] == "Production"].iterrows():
        n = len(staff_of(u["Unit"], "Operator"))
        if n < u["Min Operators"]:
            rows.append({"Unit": u["Unit"], "Operators": n, "Minimum": u["Min Operators"]})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Reporting period (global sidebar selector shared by every page)
# ----------------------------------------------------------------------------
@dataclass
class Period:
    view: str
    start: pd.Timestamp
    end: pd.Timestamp
    label: str

    @property
    def col(self) -> str:  # which target column applies
        return {"Daily": "Daily Target", "Yearly": "Yearly Target"}.get(self.view, "Monthly Target")

    @property
    def mult(self) -> int:  # quarterly = 3 x monthly target
        return 3 if self.view == "Quarterly" else 1

    def mask(self, s: pd.Series) -> pd.Series:
        return (s >= self.start) & (s <= self.end)


def _bounds() -> tuple[pd.Timestamp, pd.Timestamp]:
    ds = [load(n)["Date"] for n in ("production", "work_log", "attendance")]
    ds = [d for d in ds if not d.empty]
    if not ds:
        t = pd.Timestamp(date.today())
        return t, t
    allds = pd.concat(ds)
    return allds.min(), allds.max()


def period_picker() -> Period:
    """Render the sidebar view/date selectors and return the chosen Period."""
    lo, latest = _bounds()
    hi = max(latest, pd.Timestamp(date.today()))
    st.sidebar.subheader("📅 Reporting period")
    view = st.sidebar.radio("View", VIEWS, key="p_view", horizontal=True)
    if view == "Daily":
        d = pd.Timestamp(st.sidebar.date_input("Date", value=latest.date(), min_value=lo.date(),
                                               max_value=hi.date(), key="p_date"))
        return Period(view, d, d, d.strftime("%d %b %Y"))
    y = st.sidebar.selectbox("Year", list(range(hi.year, lo.year - 1, -1)), key="p_year")
    if view == "Yearly":
        return Period(view, pd.Timestamp(y, 1, 1), pd.Timestamp(y, 12, 31), str(y))
    if view == "Monthly":
        m = st.sidebar.selectbox("Month", range(1, 13), index=latest.month - 1, key="p_month",
                                 format_func=lambda m: calendar.month_name[m])
        s = pd.Timestamp(y, m, 1)
        return Period(view, s, s + pd.offsets.MonthEnd(0), f"{calendar.month_name[m]} {y}")
    q = st.sidebar.selectbox("Quarter", [1, 2, 3, 4], index=(latest.month - 1) // 3, key="p_q",
                             format_func=lambda q: f"Q{q}")
    s = pd.Timestamp(y, 3 * q - 2, 1)
    return Period(view, s, s + pd.offsets.MonthEnd(3), f"Q{q} {y}")


def get_period() -> Period:
    return st.session_state["period"]


# ----------------------------------------------------------------------------
# Targets & variance
# ----------------------------------------------------------------------------
def targets_table() -> pd.DataFrame:
    """Saved targets plus blank rows for every unit, machine and operator."""
    t = load("targets")
    rows = []
    for _, u in org().iterrows():
        rows.append(("Unit", u["Unit"], "All"))
        if u["Type"] == "Production":
            rows += [("Machine", u["Unit"], m) for m in machines_of(u["Unit"])]
            rows += [("Operator", u["Unit"], n) for n in staff_of(u["Unit"], "Operator")]
    have = set(zip(t["Scope"], t["Unit"], t["Name"]))
    extra = pd.DataFrame([{"Scope": s, "Unit": un, "Name": n, "Daily Target": 0, "Monthly Target": 0,
                           "Yearly Target": 0} for s, un, n in rows if (s, un, n) not in have])
    return pd.concat([t, extra], ignore_index=True)


def raw_target(tdf, unit, scope, name, col) -> float:
    r = tdf[(tdf["Scope"] == scope) & (tdf["Unit"] == unit) & (tdf["Name"] == name)]
    return float(r[col].iloc[0]) if not r.empty else 0.0


def target_for(tdf, p: Period, unit, scope="Unit", name="All", n=1) -> float:
    """Period target. Machine/operator rows with 0 fall back to an equal share of the unit target."""
    unit_t = raw_target(tdf, unit, "Unit", "All", p.col) * p.mult
    if scope == "Unit":
        return unit_t
    own = raw_target(tdf, unit, scope, name, p.col) * p.mult
    return own if own > 0 else unit_t / max(n, 1)


def pct(actual, target) -> float:
    return round(actual / target * 100, 1) if target else float("nan")


def variance_table(d, tdf, p, unit, scope, names) -> pd.DataFrame:
    """Actual vs target per operator or machine for one production unit."""
    key = "Operator Name" if scope == "Operator" else "Machine Used"
    actual = d.groupby(key)["Quantity Produced"].sum().reindex(names, fill_value=0)
    out = pd.DataFrame({scope: names, "Actual": actual.values})
    out["Target"] = [target_for(tdf, p, unit, scope, n, len(names)) for n in names]
    out["Variance"] = out["Actual"] - out["Target"]
    out["Achievement %"] = [pct(a, t) for a, t in zip(out["Actual"], out["Target"])]
    return out


def fmt_variance(tbl: pd.DataFrame):
    return tbl.style.format({"Actual": "{:,.0f}", "Target": "{:,.0f}", "Variance": "{:+,.0f}",
                             "Achievement %": "{:.1f}%"}, na_rep="-")


# ----------------------------------------------------------------------------
# Attendance maths
# ----------------------------------------------------------------------------
def attendance_summary(a: pd.DataFrame, late_pen=2, abs_pen=5, by=("Staff Name", "Unit")) -> pd.DataFrame:
    """Counts, attendance %, punctuality % and a penalty-based score per group.

    Attendance % = (Present + Late) / (Present + Late + Absent)   [leave excluded]
    Punctuality % = Present / (Present + Late)
    Score = 100 - late_pen x Late - abs_pen x Absent (floor 0)
    """
    by = list(by)
    if a.empty:
        return pd.DataFrame(columns=[*by, *ATT_STATUS, "Attendance %", "Punctuality %", "Score"])
    t = pd.crosstab([a[k] for k in by], a["Status"]).reindex(columns=ATT_STATUS, fill_value=0).reset_index()
    worked = t["Present"] + t["Late"]
    t["Attendance %"] = (worked / (worked + t["Absent"]).replace(0, pd.NA) * 100).astype(float).round(1)
    t["Punctuality %"] = (t["Present"] / worked.replace(0, pd.NA) * 100).astype(float).round(1)
    t["Score"] = (100 - late_pen * t["Late"] - abs_pen * t["Absent"]).clip(lower=0)
    return t


def overall_attendance_rate(a: pd.DataFrame) -> float:
    worked = a["Status"].isin(["Present", "Late"]).sum()
    return pct(worked, worked + (a["Status"] == "Absent").sum())


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
def trend_fig(df, qty, p: Period, tdf, unit) -> go.Figure:
    """Daily output (daily/monthly views) or monthly output (quarterly/yearly) vs target."""
    if p.view in ("Daily", "Monthly"):
        d = df[(df["Date"].dt.year == p.start.year) & (df["Date"].dt.month == p.start.month)]
        s, x = d.groupby("Date")[qty].sum().reset_index(), "Date"
        tgt = raw_target(tdf, unit, "Unit", "All", "Daily Target")
        title = f"Daily output vs daily target - {p.start:%B %Y}"
    else:
        d = df[df["Date"].dt.year == p.start.year]
        if p.view == "Quarterly":
            d = d[p.mask(d["Date"])]
        d = d.assign(Month=d["Date"].dt.to_period("M").dt.to_timestamp())
        s, x = d.groupby("Month")[qty].sum().reset_index(), "Month"
        tgt = raw_target(tdf, unit, "Unit", "All", "Monthly Target")
        title = f"Monthly output vs monthly target - {p.label}"
    fig = go.Figure(go.Scatter(x=s[x], y=s[qty], mode="lines+markers", name="Actual"))
    if tgt > 0 and not s.empty:
        fig.add_trace(go.Scatter(x=s[x], y=[tgt] * len(s), mode="lines", name="Target",
                                 line=dict(dash="dash", color="crimson")))
    fig.update_layout(title=title, xaxis_title=None, yaxis_title="Output", hovermode="x unified")
    return fig

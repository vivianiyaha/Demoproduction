"""Business department: KPI scorecard (lead generation, conversion, revenue, compliance, conduct ...)."""
import pandas as pd
import plotly.express as px
import streamlit as st

import core

p = core.get_period()
UNIT = core.KPI_UNITS[0]
st.title("💼 Business KPIs")
st.caption(f"{p.view} · {p.label} · achievement % = Actual ÷ Target for each KPI")

kpi = core.load("kpi")
u = kpi[kpi["Unit"] == UNIT]
d = u[p.mask(u["Date"])]
staff = sorted(set(core.staff_of(UNIT)) | set(d["Staff Name"]))
sc = core.kpi_scores(d)
pair = core.kpi_scores(d.rename(columns={"KPI": "k"}).assign(KPI=d["Staff Name"] + "|" + d["KPI"]))
if not pair.empty:
    pair[["Staff Name", "KPI"]] = pair["KPI"].str.split("|", n=1, expand=True)
    staff_avg = pair.groupby("Staff Name")["Achievement %"].mean().sort_values(ascending=False)
else:
    staff_avg = pd.Series(dtype=float)

avg = core.avg_achievement(d)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall KPI achievement", f"{avg:.1f}%" if avg == avg else "-")
c2.metric("KPIs at or above target", f"{int((sc['Achievement %'] >= 100).sum())} of {len(core.KPI_DEFS)}")
c3.metric("KPI entries", len(d))
c4.metric("Top performer", staff_avg.index[0] if len(staff_avg) else "-")

t_log, t_score, t_rec = st.tabs(["➕ Log KPI", "📊 Scorecard", "🗂 Records & Export"])

with t_log:
    if st.session_state.pop("saved_kpi", None):
        st.success("KPI entry saved.")
    name = st.selectbox("KPI", list(core.KPI_DEFS))  # outside the form so the default target updates
    measure, default_t = core.KPI_DEFS[name]
    with st.form("kpi_entry", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        dt = f1.date_input("Date", value=p.end.date())
        person = f2.selectbox("Staff Name", staff)
        target = f3.number_input(f"Target ({measure})", min_value=0.0, value=float(default_t), key=f"t_{name}")
        actual = f4.number_input(f"Actual ({measure})", min_value=0.0, value=0.0)
        remarks = st.text_input("Remarks (optional)")
        if st.form_submit_button("Add KPI entry", type="primary"):
            core.append("kpi", [{"Date": pd.Timestamp(dt), "Unit": UNIT, "Staff Name": person, "KPI": name,
                                 "Target": target, "Actual": actual, "Remarks": remarks}])
            st.session_state["saved_kpi"] = True
            st.rerun()
    st.markdown("**Latest entries in the selected period**")
    st.dataframe(core.csv_frame("kpi", d.tail(15)), hide_index=True, width="stretch")

with t_score:
    if d.empty:
        st.info("No KPI entries in the selected period.")
    else:
        sc = sc.assign(Measure=sc["KPI"].map(lambda k: core.KPI_DEFS.get(k, ("",))[0]))
        left, right = st.columns(2)
        fig = px.bar(sc, x="KPI", y="Achievement %", title="Achievement by KPI")
        fig.add_hline(y=100, line_dash="dash", line_color="crimson")
        left.plotly_chart(fig, width="stretch")
        right.plotly_chart(px.bar(staff_avg.reset_index().rename(columns={"Achievement %": "Avg achievement %"}),
                                  x="Avg achievement %", y="Staff Name", orientation="h",
                                  title="Average achievement by staff"), width="stretch")
        heat = pair.pivot(index="Staff Name", columns="KPI", values="Achievement %")
        st.plotly_chart(px.imshow(heat, text_auto=".0f", color_continuous_scale="RdYlGn", color_continuous_midpoint=100,
                                  aspect="auto", title="Staff × KPI achievement %"), width="stretch")
        st.dataframe(sc[["KPI", "Measure", "Actual", "Target", "Achievement %"]].style.format(
            {"Actual": "{:,.1f}", "Target": "{:,.1f}", "Achievement %": "{:.1f}%"}, na_rep="-"),
            hide_index=True, width="stretch")
    yr = u[u["Date"].dt.year == p.start.year].assign(Ach=lambda x: (x["Actual"] / x["Target"].replace(0, pd.NA) * 100).astype(float))
    if not yr.empty:
        tr = yr.groupby(yr["Date"].dt.to_period("M").dt.to_timestamp())["Ach"].mean().reset_index()
        fig = px.line(tr, x="Date", y="Ach", markers=True, title=f"Monthly average KPI achievement - {p.start.year}")
        fig.add_hline(y=100, line_dash="dash", line_color="crimson")
        fig.update_layout(xaxis_title=None, yaxis_title="Achievement %")
        st.plotly_chart(fig, width="stretch")

with t_rec:
    out = core.csv_frame("kpi", d)
    st.dataframe(out, hide_index=True, width="stretch")
    safe = p.label.replace(" ", "_")
    k1, k2, _ = st.columns([1, 1, 2])
    with k1:
        core.download(out, f"business_kpi_{safe}.csv", "⬇️ KPI entries (CSV)")
    with k2:
        core.download(sc, f"business_scorecard_{safe}.csv", "⬇️ Scorecard (CSV)")

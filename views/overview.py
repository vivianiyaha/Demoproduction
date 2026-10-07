"""Company-wide overview: every unit and department on one screen."""
import pandas as pd
import plotly.express as px
import streamlit as st

import core

p = core.get_period()
st.title("🏭 Company Overview")
st.caption(f"{p.view} · {p.label}")

org, prod, work = core.org(), core.load("production"), core.load("work_log")
att, tdf = core.load("attendance"), core.load("targets")
att_p = att[p.mask(att["Date"])]

# One row per unit/department: output vs target + attendance
rows = []
for _, u in org.iterrows():
    src, q = (prod, "Quantity Produced") if u["Type"] == "Production" else (work, "Quantity")
    d = src[(src["Unit"] == u["Unit"]) & p.mask(src["Date"])]
    actual, tgt = int(d[q].sum()), core.target_for(tdf, p, u["Unit"])
    rows.append({"Unit": u["Unit"], "Type": u["Type"], "Output": actual, "Measure": u["Output Unit"],
                 "Target": tgt, "Variance": actual - tgt, "Achievement %": core.pct(actual, tgt)})
sm = pd.DataFrame(rows).merge(
    core.attendance_summary(att_p, by=["Unit"])[["Unit", "Attendance %"]], on="Unit", how="left")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Units reporting output", f"{(sm['Output'] > 0).sum()} of {len(sm)}")
c2.metric("Avg target achievement", f"{sm['Achievement %'].mean():.1f}%" if sm["Achievement %"].notna().any() else "-")
c3.metric("Attendance rate", f"{core.overall_attendance_rate(att_p):.1f}%" if len(att_p) else "-")
c4.metric("Absences recorded", int((att_p["Status"] == "Absent").sum()))

gaps = core.coverage_gaps()
if not gaps.empty:
    st.warning("Operator coverage below minimum: " + ", ".join(
        f"{r.Unit} ({r.Operators}/{r.Minimum})" for r in gaps.itertuples()))

left, right = st.columns(2)
fig = px.bar(sm, x="Unit", y="Achievement %", color="Type", title="Target achievement by unit / department")
fig.add_hline(y=100, line_dash="dash", line_color="crimson")
left.plotly_chart(fig, width="stretch")
fig = px.bar(sm, x="Unit", y="Attendance %", color="Type", title="Attendance rate by unit / department")
fig.update_yaxes(range=[0, 100])
right.plotly_chart(fig, width="stretch")

st.dataframe(sm.style.format({"Output": "{:,.0f}", "Target": "{:,.0f}", "Variance": "{:+,.0f}",
                              "Achievement %": "{:.1f}%", "Attendance %": "{:.1f}%"}, na_rep="-"),
             hide_index=True, width="stretch")
st.caption("Units measure different outputs (cards, sheets, plates...), so compare units by achievement %, not raw totals.")
core.download(sm, f"company_summary_{p.label.replace(' ', '_')}.csv", "⬇️ Download company summary (CSV)")

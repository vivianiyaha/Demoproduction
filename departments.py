"""Departments (Business, Admin, QC, Vault, Fulfillment): work log & KPIs."""
import pandas as pd
import plotly.express as px
import streamlit as st

import core

p = core.get_period()
st.title("🏢 Departments")
unit = st.selectbox("Department", core.units_of("Department"))
meta = core.org().set_index("Unit").loc[unit]
st.caption(f"{p.view} · {p.label} · measured in {meta['Output Unit']}")

work, tdf = core.load("work_log"), core.load("targets")
u = work[work["Unit"] == unit]
d = u[p.mask(u["Date"])]
staff = sorted(set(core.staff_of(unit)) | set(d["Staff Name"]))

total, tgt = int(d["Quantity"].sum()), core.target_for(tdf, p, unit)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Work Completed", f"{total:,}", delta=f"{total - tgt:+,.0f} vs target" if tgt else None)
c2.metric("Target Achievement", f"{core.pct(total, tgt):.1f}%" if tgt else "no target set")
c3.metric("Tasks Marked Completed", f"{(d['Status'] == 'Completed').mean() * 100:.0f}%" if len(d) else "-")
c4.metric("Top Performer", d.groupby("Staff Name")["Quantity"].sum().idxmax() if len(d) else "-")

t_log, t_an, t_rec = st.tabs(["➕ Log Work", "📊 Analytics", "🗂 Records & Export"])

with t_log:
    if st.session_state.pop("saved_work", None):
        st.success("Entry saved.")
    with st.form("work_entry", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        dt = f1.date_input("Date", value=p.end.date())
        person = f2.selectbox("Staff Name", staff)
        acts = sorted(set(core.ACTIVITIES.get(unit, [])) | set(u["Activity"]) - {""})
        activity = f3.selectbox("Activity", acts, accept_new_options=True)
        f4, f5, f6 = st.columns(3)
        qty = f4.number_input(f"Quantity ({meta['Output Unit']})", min_value=0, step=1, value=1)
        status = f5.selectbox("Status", core.WORK_STATUS)
        remarks = f6.text_input("Remarks (optional)")
        if st.form_submit_button("Add entry", type="primary"):
            core.append("work_log", [{"Date": pd.Timestamp(dt), "Unit": unit, "Staff Name": person,
                                      "Activity": activity, "Quantity": int(qty), "Status": status, "Remarks": remarks}])
            st.session_state["saved_work"] = True
            st.rerun()
    st.markdown("**Latest entries in the selected period**")
    st.dataframe(core.csv_frame("work_log", d.tail(15)), hide_index=True, width="stretch")

with t_an:
    if d.empty:
        st.info("No work logged for this department in the selected period.")
    else:
        left, right = st.columns(2)
        by_staff = d.groupby("Staff Name")["Quantity"].sum().sort_values().reset_index()
        left.plotly_chart(px.bar(by_staff, x="Quantity", y="Staff Name", orientation="h", title="Output by Staff"), width="stretch")
        by_act = d.groupby(["Activity", "Status"])["Quantity"].sum().reset_index()
        right.plotly_chart(px.bar(by_act, x="Activity", y="Quantity", color="Status", title="Work by Activity & Status"), width="stretch")
        open_items = d[d["Status"] != "Completed"]
        if not open_items.empty:
            st.markdown("**Open items (in progress / pending)**")
            st.dataframe(core.csv_frame("work_log", open_items), hide_index=True, width="stretch")
    st.plotly_chart(core.trend_fig(u, "Quantity", p, tdf, unit), width="stretch")

with t_rec:
    out = core.csv_frame("work_log", d)
    st.dataframe(out, hide_index=True, width="stretch")
    core.download(out, f"{unit}_work_log_{p.label}.csv".replace(" ", "_"), "⬇️ Work log (CSV)")

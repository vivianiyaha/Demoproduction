"""Setup: units & machines, staff roster, targets."""
import pandas as pd
import streamlit as st

import core

st.title("🛠️ Setup & Targets")
org, staff = core.org(), core.load("staff")
t_org, t_staff, t_tgt = st.tabs(["🏗 Units & Machines", "👥 Staff Roster", "🎯 Targets"])

with t_org:
    st.caption("List a unit's machines separated by semicolons (e.g. PMC-01;PMC-02). Departments have no machines.")
    ed = st.data_editor(org, num_rows="dynamic", hide_index=True, width="stretch", key="org_ed", column_config={
        "Type": st.column_config.SelectboxColumn(options=["Production", "Department"], required=True),
        "Min Operators": st.column_config.NumberColumn(min_value=0, step=1),
        "Shifts Per Day": st.column_config.NumberColumn(min_value=1, max_value=3, step=1)})
    if st.button("💾 Save units", type="primary"):
        core.save("org", ed.dropna(subset=["Unit"]))
        st.success("Units saved.")
        st.rerun()

with t_staff:
    gaps = core.coverage_gaps()
    if gaps.empty:
        st.success("Every production unit meets its minimum operator coverage.")
    else:
        st.warning("Below minimum operators:")
        st.dataframe(gaps, hide_index=True)
    ed = st.data_editor(staff, num_rows="dynamic", hide_index=True, width="stretch", key="staff_ed", column_config={
        "Unit": st.column_config.SelectboxColumn(options=org["Unit"].tolist(), required=True),
        "Role": st.column_config.SelectboxColumn(options=core.ROLES, required=True)})
    if st.button("💾 Save roster", type="primary"):
        core.save("staff", ed.dropna(subset=["Staff Name"]))
        st.success("Roster saved.")
        st.rerun()

with t_tgt:
    st.caption("Unit row = total target for the unit/department. Machine and Operator rows are optional - "
               "0 means an equal share of the unit target. Quarterly target = 3 x monthly. "
               "Business is scored by KPI, so its targets are entered with each KPI entry.")
    unit = st.selectbox("Unit / Department", [u for u in org["Unit"] if u not in core.KPI_UNITS])
    full = core.targets_table()
    order = {"Unit": 0, "Machine": 1, "Operator": 2}
    sub = full[full["Unit"] == unit].sort_values("Scope", key=lambda s: s.map(order), kind="stable")
    ed = st.data_editor(sub, hide_index=True, width="stretch", disabled=["Scope", "Unit", "Name"], key=f"tgt_{unit}",
                        column_config={c: st.column_config.NumberColumn(min_value=0, step=100, format="%d")
                                       for c in core.SCHEMA["targets"][3:]})
    if st.button("💾 Save targets", type="primary"):
        core.save("targets", pd.concat([full[full["Unit"] != unit], ed], ignore_index=True))
        st.success(f"Targets saved for {unit}. Commit data/targets.csv to keep them in GitHub.")

"""Production units: log output, analyse operators/machines, track targets."""
import pandas as pd
import plotly.express as px
import streamlit as st

import core

p = core.get_period()
st.title("⚙️ Production Units")
unit = st.selectbox("Production unit", core.units_of("Production"))
meta = core.org().set_index("Unit").loc[unit]
machines, measure = core.machines_of(unit), meta["Output Unit"]
st.caption(f"{p.view} · {p.label} · {len(machines)} machine(s) · output in {measure}")

prod, tdf = core.load("production"), core.load("targets")
u = prod[prod["Unit"] == unit]
d = u[p.mask(u["Date"])]
operators = sorted(set(core.staff_of(unit, "Operator")) | set(d["Operator Name"]))

total, tgt = int(d["Quantity Produced"].sum()), core.target_for(tdf, p, unit)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Produced", f"{total:,}", delta=f"{total - tgt:+,.0f} vs target" if tgt else None)
c2.metric("Target Achievement", f"{core.pct(total, tgt):.1f}%" if tgt else "no target set")
c3.metric("Shifts Completed", d[["Date", "Shift Type"]].drop_duplicates().shape[0])
c4.metric("Top Operator", d.groupby("Operator Name")["Quantity Produced"].sum().idxmax() if len(d) else "-")

t_log, t_an, t_var, t_rec = st.tabs(["➕ Log Production", "📊 Analytics", "🎯 Targets & Variance", "🗂 Records & Export"])

with t_log:
    if st.session_state.pop("saved", None):
        st.success("Entry saved.")
    if len(operators) < meta["Min Operators"]:
        st.warning(f"{unit} has fewer than {meta['Min Operators']} operators - add staff in Setup.")
    with st.form("prod_entry", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        dt = f1.date_input("Production Date", value=p.end.date())
        shift = f2.selectbox("Shift Type", core.SHIFTS)
        machine = f3.selectbox("Machine Used", machines)
        operator = f4.selectbox("Operator Name", operators)
        f5, f6, f7 = st.columns(3)
        client = f5.selectbox("Client", sorted(set(prod["Client"]) - {""}), accept_new_options=True)
        product = f6.selectbox("Product Type", sorted(set(u["Product Type"]) - {""}), accept_new_options=True)
        qty = f7.number_input(f"Quantity Produced ({measure})", min_value=1, step=100, value=1000)
        if st.form_submit_button("Add entry", type="primary"):
            core.append("production", [{"Date": pd.Timestamp(dt), "Unit": unit, "Shift Type": shift,
                                        "Client": client, "Product Type": product, "Quantity Produced": int(qty),
                                        "Machine Used": machine, "Operator Name": operator}])
            st.session_state["saved"] = True
            st.rerun()
    st.markdown("**Latest entries in the selected period**")
    st.dataframe(core.csv_frame("production", d.tail(15)), hide_index=True, width="stretch")

with t_an:
    if d.empty:
        st.info("No production recorded for this unit in the selected period.")
    else:
        left, right = st.columns(2)
        ops = core.variance_table(d, tdf, p, unit, "Operator", operators)
        fig = px.bar(ops.sort_values("Actual"), x="Actual", y="Operator", orientation="h", text="Actual",
                     title="Output by Operator")
        fig.update_traces(texttemplate="%{text:,}")
        left.plotly_chart(fig, width="stretch")
        by = d.groupby(["Machine Used", "Shift Type"])["Quantity Produced"].sum().reset_index()
        fig = px.bar(by, x="Machine Used", y="Quantity Produced", color="Shift Type", title="Machine Output by Shift",
                     category_orders={"Machine Used": machines, "Shift Type": core.SHIFTS})
        right.plotly_chart(fig, width="stretch")
        # Utilization = distinct shifts a machine ran / shifts available in the period
        avail = d["Date"].nunique() * max(int(meta["Shifts Per Day"]), 1)
        runs = d.drop_duplicates(["Date", "Shift Type", "Machine Used"]).groupby("Machine Used").size()
        util = pd.DataFrame({"Machine": machines})
        util["Shifts Run"] = [int(runs.get(m, 0)) for m in machines]
        util["Utilization %"] = [round(r / avail * 100, 1) for r in util["Shifts Run"]]
        util["Output"] = [int(d.loc[d["Machine Used"] == m, "Quantity Produced"].sum()) for m in machines]
        st.markdown("**Machine utilization**")
        st.dataframe(util, hide_index=True, width="stretch",
                     column_config={"Utilization %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%")})
    st.plotly_chart(core.trend_fig(u, "Quantity Produced", p, tdf, unit), width="stretch")

with t_var:
    st.caption("Machine/operator targets are optional (Setup & Targets). If unset, an equal share of the unit target is used.")
    a, b = st.columns(2)
    a.markdown("**By operator**")
    a.dataframe(core.fmt_variance(core.variance_table(d, tdf, p, unit, "Operator", operators)), hide_index=True, width="stretch")
    b.markdown("**By machine**")
    b.dataframe(core.fmt_variance(core.variance_table(d, tdf, p, unit, "Machine", machines)), hide_index=True, width="stretch")

with t_rec:
    out = core.csv_frame("production", d)
    st.dataframe(out, hide_index=True, width="stretch")
    safe = f"{unit}_{p.label}".replace(" ", "_")
    k1, k2, _ = st.columns([1, 1, 2])
    with k1:
        core.download(out, f"production_{safe}.csv", "⬇️ Production records (CSV)")
    with k2:
        rep = pd.concat([core.variance_table(d, tdf, p, unit, "Operator", operators).rename(columns={"Operator": "Name"}).assign(Level="Operator"),
                         core.variance_table(d, tdf, p, unit, "Machine", machines).rename(columns={"Machine": "Name"}).assign(Level="Machine")])
        core.download(rep.assign(Unit=unit, Period=p.label), f"kpi_report_{safe}.csv", "⬇️ KPI report (CSV)")

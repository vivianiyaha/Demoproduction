"""Attendance: daily register, period summary with scores, records and import."""
import pandas as pd
import plotly.express as px
import streamlit as st

import core

p = core.get_period()
st.title("🕒 Attendance")
st.caption(f"{p.view} · {p.label}")

att, staff, org = core.load("attendance"), core.load("staff"), core.org()
groups = ["All units & departments"] + org["Unit"].tolist()
t_reg, t_sum, t_rec = st.tabs(["📝 Daily Register", "📈 Summary & Scores", "🗂 Records & Import"])

# ---- Daily register: mark the whole roster in one table -------------------
with t_reg:
    c1, c2, c3 = st.columns(3)
    day = pd.Timestamp(c1.date_input("Register date", value=p.end.date(), key="reg_date"))
    grp = c2.selectbox("Unit / Department", groups, key="reg_grp")
    late_after = c3.text_input("Mark Late if Time In is after (HH:MM)", "08:15")
    roster = staff if grp == groups[0] else staff[staff["Unit"] == grp]
    ex = att[att["Date"] == day].drop_duplicates("Staff Name", keep="last").set_index("Staff Name")
    reg = roster[["Staff Name", "Unit"]].reset_index(drop=True)
    for col, default in (("Status", "Present"), ("Time In", "08:00"), ("Time Out", "17:00"), ("Remarks", "")):
        reg[col] = reg["Staff Name"].map(ex[col]).fillna(default)
    edited = st.data_editor(
        reg, hide_index=True, width="stretch", disabled=["Staff Name", "Unit"], key=f"reg_{day:%Y%m%d}_{grp}",
        column_config={"Status": st.column_config.SelectboxColumn(options=core.ATT_STATUS, required=True)})
    if st.button("💾 Save register", type="primary"):
        out = edited.assign(Date=day)
        out.loc[out["Status"].isin(["Absent", "Leave"]), ["Time In", "Time Out"]] = ""
        out.loc[(out["Status"] == "Present") & (out["Time In"].astype(str) > late_after), "Status"] = "Late"
        rest = att[~((att["Date"] == day) & att["Staff Name"].isin(out["Staff Name"]))]
        core.save("attendance", pd.concat([rest, out], ignore_index=True))
        st.success(f"Saved {len(out)} attendance records for {day:%d %b %Y}.")

# ---- Summary & performance score ------------------------------------------
with t_sum:
    c1, c2, c3 = st.columns(3)
    sel = c1.selectbox("Unit / Department", groups, key="sum_grp")
    late_pen = c2.number_input("Penalty points per late", min_value=0, value=2)
    abs_pen = c3.number_input("Penalty points per absence", min_value=0, value=5)
    a = att[p.mask(att["Date"])]
    if sel != groups[0]:
        a = a[a["Unit"] == sel]
    if a.empty:
        st.info("No attendance records for this selection.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Attendance rate", f"{core.overall_attendance_rate(a):.1f}%")
        worked = a["Status"].isin(["Present", "Late"]).sum()
        m2.metric("Punctuality", f"{(a['Status'] == 'Present').sum() / worked * 100:.1f}%" if worked else "-")
        m3.metric("Late arrivals", int((a["Status"] == "Late").sum()))
        m4.metric("Absences", int((a["Status"] == "Absent").sum()))
        by_unit = core.attendance_summary(a, by=["Unit"])
        fig = px.bar(by_unit, x="Unit", y="Attendance %", title="Attendance rate by unit / department")
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, width="stretch")
        per_staff = core.attendance_summary(a, late_pen, abs_pen).sort_values("Score")
        st.dataframe(per_staff, hide_index=True, width="stretch", column_config={
            "Attendance %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            "Punctuality %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")})
        core.download(per_staff, f"attendance_summary_{p.label}.csv".replace(" ", "_"), "⬇️ Summary (CSV)")

# ---- Records & import from the existing attendance app ---------------------
with t_rec:
    rec = core.csv_frame("attendance", att[p.mask(att["Date"])])
    st.dataframe(rec, hide_index=True, width="stretch")
    core.download(rec, f"attendance_records_{p.label}.csv".replace(" ", "_"), "⬇️ Records (CSV)")
    with st.expander("📥 Import from your existing attendance app (CSV export)"):
        up = st.file_uploader("Upload CSV", type="csv", key="att_up")
        if up:
            raw = pd.read_csv(up)
            st.dataframe(raw.head(), hide_index=True, width="stretch")
            opts = ["-"] + list(raw.columns)
            fields = ["Date", "Staff Name", "Unit", "Status", "Time In", "Time Out", "Remarks"]
            cols = st.columns(len(fields))
            m = {f: cl.selectbox(f, opts, key=f"imp_{f}") for f, cl in zip(fields, cols)}
            if st.button("Import records"):
                if "-" in (m["Date"], m["Staff Name"], m["Status"]):
                    st.error("Map at least Date, Staff Name and Status.")
                else:
                    new = pd.DataFrame({f: raw[c] if c != "-" else "" for f, c in m.items()})
                    new["Status"] = new["Status"].astype(str).str.strip().str.title().replace({"On Leave": "Leave"})
                    new = core.clean("attendance", new)
                    bad = ~new["Status"].isin(core.ATT_STATUS)
                    new = new[~bad]
                    merged = pd.concat([att, new]).drop_duplicates(["Date", "Staff Name"], keep="last")
                    core.save("attendance", merged)
                    st.success(f"Imported {len(new)} records ({int(bad.sum())} skipped: unrecognised status).")

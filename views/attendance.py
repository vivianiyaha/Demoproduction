"""Attendance: daily register (one CSV per day), period summary with scores, records and import."""
import re

import pandas as pd
import plotly.express as px
import streamlit as st

import core

p = core.get_period()
st.title("🕒 Attendance")
st.caption(f"{p.view} · {p.label} · Late = Time In after {core.LATE_AFTER}")

att, staff, org = core.load("attendance"), core.load("staff"), core.org()
groups = ["All units & departments"] + org["Unit"].tolist()
t_reg, t_sum, t_rec = st.tabs(["📝 Daily Register", "📈 Summary & Scores", "🗂 Records & Import"])

# ---- Daily register: one file per day in data/attendance/YYYY-MM/ -----------
with t_reg:
    st.caption("Saved as one CSV per day (Date, Staff Name, Time In, Time Out, Remarks). Status is worked out automatically: "
               "Time In filled = Present/Late · Time In blank = Absent · blank + 'Leave' in Remarks = Leave.")
    c1, c2 = st.columns(2)
    day = pd.Timestamp(c1.date_input("Register date", value=p.end.date(), key="reg_date"))
    grp = c2.selectbox("Unit / Department", groups, key="reg_grp")
    roster = staff if grp == groups[0] else staff[staff["Unit"] == grp]
    ex = att[att["Date"] == day].drop_duplicates("Staff Name", keep="last").set_index("Staff Name")
    reg = roster[["Staff Name", "Unit"]].reset_index(drop=True)
    for col, default in (("Time In", "08:00"), ("Time Out", "17:00"), ("Remarks", "")):
        reg[col] = reg["Staff Name"].map(ex[col]).fillna(default)
    edited = st.data_editor(reg, hide_index=True, width="stretch", disabled=["Staff Name", "Unit"],
                            key=f"reg_{day:%Y%m%d}_{grp}")
    if st.button("💾 Save register", type="primary"):
        edited = edited.fillna("")
        ok = lambda t: t == "" or bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(t)))
        bad = edited[~(edited["Time In"].map(ok) & edited["Time Out"].map(ok))]
        if not bad.empty:
            st.error("Use HH:MM (24-hour) for: " + ", ".join(bad["Staff Name"]))
        else:
            core.upsert_attendance(edited.assign(Date=day)[["Date", "Staff Name", "Time In", "Time Out", "Remarks"]])
            now = core.load("attendance")
            now = now[(now["Date"] == day) & now["Staff Name"].isin(edited["Staff Name"])]
            tally = ", ".join(f"{n} {s}" for s, n in now["Status"].value_counts().items())
            st.success(f"Saved {len(edited)} records to {core.att_path(day).relative_to(core.DATA_DIR.parent)} - {tally}")

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
        fig = px.bar(core.attendance_summary(a, by=["Unit"]), x="Unit", y="Attendance %",
                     title="Attendance rate by unit / department")
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
    rec = att[p.mask(att["Date"])]
    rec = rec.assign(Date=rec["Date"].dt.strftime(core.DATE_FMT))[["Date", "Staff Name", "Unit", "Time In", "Time Out", "Status", "Remarks"]]
    st.caption("Unit and Status are shown here for reporting; they are not stored in the daily files.")
    st.dataframe(rec, hide_index=True, width="stretch")
    core.download(rec, f"attendance_records_{p.label}.csv".replace(" ", "_"), "⬇️ Records (CSV)")
    with st.expander("📥 Import from your existing attendance app (CSV export)"):
        st.caption("Rows are split into daily files. If you map a Status column: Absent/Leave clear the times, "
                   "Present/Late rows with no time get 08:00 / 08:30.")
        up = st.file_uploader("Upload CSV", type="csv", key="att_up")
        if up:
            raw = pd.read_csv(up, dtype=str, keep_default_na=False)
            st.dataframe(raw.head(), hide_index=True, width="stretch")
            opts = ["-"] + list(raw.columns)
            fields = ["Date", "Staff Name", "Time In", "Time Out", "Remarks", "Status (optional)"]
            m = {f: cl.selectbox(f, opts, key=f"imp_{f}") for f, cl in zip(fields, st.columns(len(fields)))}
            if st.button("Import records"):
                if "-" in (m["Date"], m["Staff Name"]):
                    st.error("Map at least Date and Staff Name.")
                else:
                    col = lambda f: raw[m[f]] if m[f] != "-" else ""
                    hhmm = lambda s: pd.to_datetime(s.astype(str), errors="coerce", format="mixed").dt.strftime("%H:%M").fillna("") if m_ok(s) else s
                    m_ok = lambda s: isinstance(s, pd.Series)
                    new = pd.DataFrame({"Date": core.parse_dates(raw[m["Date"]]),
                                        "Staff Name": raw[m["Staff Name"]].astype(str).str.strip(),
                                        "Time In": hhmm(col("Time In")), "Time Out": hhmm(col("Time Out")),
                                        "Remarks": col("Remarks")})
                    if m["Status (optional)"] != "-":
                        s = raw[m["Status (optional)"]].astype(str).str.strip().str.title()
                        new.loc[s.isin(["Absent", "Leave", "On Leave"]), ["Time In", "Time Out"]] = ""
                        new.loc[s.isin(["Leave", "On Leave"]), "Remarks"] = "Leave"
                        new.loc[s.eq("Present") & new["Time In"].eq(""), "Time In"] = "08:00"
                        new.loc[s.eq("Late") & new["Time In"].eq(""), "Time In"] = "08:30"
                    new = new.dropna(subset=["Date"])
                    core.upsert_attendance(new)
                    st.success(f"Imported {len(new)} records into {new['Date'].nunique()} daily file(s).")

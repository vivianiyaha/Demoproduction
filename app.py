from datetime import datetime, time
import pandas as pd
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Enterprise Operations & Attendance Portal",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- INITIALIZE SESSION STATE DATA ---
if "staff" not in st.session_state:
  st.session_state.staff = pd.DataFrame([
      # Production - Perso (6 machines)
      {
          "ID": "STF001",
          "Name": "John Doe",
          "Dept": "Production",
          "Unit/Machine": "Perso - Machine 1",
          "Role": "Operator",
      },
      {
          "ID": "STF002",
          "Name": "Jane Smith",
          "Dept": "Production",
          "Unit/Machine": "Perso - Machine 2",
          "Role": "Operator",
      },
      {
          "ID": "STF003",
          "Name": "Mark Lee",
          "Dept": "Production",
          "Unit/Machine": "Perso - Machine 3",
          "Role": "Operator",
      },
      {
          "ID": "STF004",
          "Name": "Sarah Connor",
          "Dept": "Production",
          "Unit/Machine": "Perso - Machine 4",
          "Role": "Operator",
      },
      {
          "ID": "STF005",
          "Name": "David Miller",
          "Dept": "Production",
          "Unit/Machine": "Perso - Machine 5",
          "Role": "Operator",
      },
      {
          "ID": "STF006",
          "Name": "Emma Watson",
          "Dept": "Production",
          "Unit/Machine": "Perso - Machine 6",
          "Role": "Operator",
      },
      # Production - PMC (16 machines sample)
      {
          "ID": "STF007",
          "Name": "Alice Brown",
          "Dept": "Production",
          "Unit/Machine": "PMC - Machine 1",
          "Role": "Operator",
      },
      {
          "ID": "STF008",
          "Name": "Bob White",
          "Dept": "Production",
          "Unit/Machine": "PMC - Machine 2",
          "Role": "Operator",
      },
      {
          "ID": "STF009",
          "Name": "Charlie Green",
          "Dept": "Production",
          "Unit/Machine": "PMC - Machine 3",
          "Role": "Operator",
      },
      {
          "ID": "STF010",
          "Name": "Diana Prince",
          "Dept": "Production",
          "Unit/Machine": "PMC - Machine 4",
          "Role": "Operator",
      },
      # Production - Telco (6 machines)
      {
          "ID": "STF011",
          "Name": "Frank Castle",
          "Dept": "Production",
          "Unit/Machine": "Telco - Machine 1",
          "Role": "Operator",
      },
      {
          "ID": "STF012",
          "Name": "Grace Hopper",
          "Dept": "Production",
          "Unit/Machine": "Telco - Machine 2",
          "Role": "Operator",
      },
      # Production - OC200 (1 machine)
      {
          "ID": "STF013",
          "Name": "Hank Pym",
          "Dept": "Production",
          "Unit/Machine": "OC200 - Machine 1",
          "Role": "Operator",
      },
      {
          "ID": "STF014",
          "Name": "Ian Malcolm",
          "Dept": "Production",
          "Unit/Machine": "OC200 - Machine 1",
          "Role": "Operator",
      },
      # Production - SM74
      {
          "ID": "STF015",
          "Name": "Jack Ryan",
          "Dept": "Production",
          "Unit/Machine": "SM74 Unit",
          "Role": "Operator",
      },
      {
          "ID": "STF016",
          "Name": "Karen Page",
          "Dept": "Production",
          "Unit/Machine": "SM74 Unit",
          "Role": "Operator",
      },
      # Production - Mailer unit
      {
          "ID": "STF017",
          "Name": "Larry Page",
          "Dept": "Production",
          "Unit/Machine": "Mailer Unit",
          "Role": "Operator",
      },
      {
          "ID": "STF018",
          "Name": "Mona Lisa",
          "Dept": "Production",
          "Unit/Machine": "Mailer Unit",
          "Role": "Operator",
      },
      # Production - CTP unit (4 machines)
      {
          "ID": "STF019",
          "Name": "Nancy Wheeler",
          "Dept": "Production",
          "Unit/Machine": "CTP - Machine 1",
          "Role": "Operator",
      },
      {
          "ID": "STF020",
          "Name": "Oscar Isaac",
          "Dept": "Production",
          "Unit/Machine": "CTP - Machine 2",
          "Role": "Operator",
      },
      # Production - IT (Nano 1610 & Nano 9)
      {
          "ID": "STF021",
          "Name": "Peter Parker",
          "Dept": "Production",
          "Unit/Machine": "IT - Nano 1610",
          "Role": "Technician",
      },
      {
          "ID": "STF022",
          "Name": "Quentin Beck",
          "Dept": "Production",
          "Unit/Machine": "IT - Nano 9",
          "Role": "Technician",
      },
      # Business Dept
      {
          "ID": "STF023",
          "Name": "Rachel Zane",
          "Dept": "Business",
          "Unit/Machine": "Sales & Accounts",
          "Role": "Executive",
      },
      {
          "ID": "STF024",
          "Name": "Harvey Specter",
          "Dept": "Business",
          "Unit/Machine": "Strategy",
          "Role": "Manager",
      },
      # Admin Dept
      {
          "ID": "STF025",
          "Name": "Donna Paulsen",
          "Dept": "Admin",
          "Unit/Machine": "Operations",
          "Role": "Admin Officer",
      },
      # QC
      {
          "ID": "STF026",
          "Name": "Louis Litt",
          "Dept": "QC",
          "Unit/Machine": "Quality Assurance",
          "Role": "Inspector",
      },
      # Vault
      {
          "ID": "STF027",
          "Name": "Mike Ross",
          "Dept": "Vault",
          "Unit/Machine": "Secure Storage",
          "Role": "Custodian",
      },
      # Fulfillment
      {
          "ID": "STF028",
          "Name": "Katrina Bennett",
          "Dept": "Fulfillment",
          "Unit/Machine": "Packaging & Dispatch",
          "Role": "Handler",
      },
  ])

if "attendance" not in st.session_state:
  st.session_state.attendance = pd.DataFrame(
      columns=["Date", "Staff ID", "Name", "Department", "Status", "Time In"]
  )

if "jobs" not in st.session_state:
  st.session_state.jobs = pd.DataFrame([
      {
          "Job ID": "JOB-1001",
          "Title": "Batch Card Personalization",
          "Department": "Production",
          "Unit/Machine": "Perso - Machine 1",
          "Assigned To": "John Doe",
          "Status": "In Progress",
          "Priority": "High",
          "Date Assigned": str(datetime.now().date()),
      },
      {
          "Job ID": "JOB-1002",
          "Title": "Client Statement Mail-out",
          "Department": "Production",
          "Unit/Machine": "Mailer Unit",
          "Assigned To": "Larry Page",
          "Status": "Pending",
          "Priority": "Medium",
          "Date Assigned": str(datetime.now().date()),
      },
  ])

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏢 Enterprise Operations")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🕒 Attendance Tracking",
        "📋 Job & Task Tracker",
        "👥 Staff & Unit Directory",
        "📈 Reports & Analytics",
    ],
)

# --- 1. DASHBOARD PAGE ---
if page == "📊 Dashboard":
  st.title("📊 Executive Dashboard")
  st.markdown("Real-time overview of company attendance, active jobs, and assets.")

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Total Staff", len(st.session_state.staff))
  with col2:
    today_str = str(datetime.now().date())
    present_today = len(
        st.session_state.attendance[
            (st.session_state.attendance["Date"] == today_str)
            & (st.session_state.attendance["Status"] == "Present")
        ]
    )
    st.metric("Present Today", present_today)
  with col3:
    active_jobs = len(
        st.session_state.jobs[
            st.session_state.jobs["Status"] != "Completed"
        ]
    )
    st.metric("Active Jobs", active_jobs)
  with col4:
    completed_jobs = len(
        st.session_state.jobs[st.session_state.jobs["Status"] == "Completed"]
    )
    st.metric("Completed Jobs", completed_jobs)

  st.markdown("---")
  col_a, col_b = st.columns(2)

  with col_a:
    st.subheader("Active Jobs Summary")
    if not st.session_state.jobs.empty:
      st.dataframe(
          st.session_state.jobs[
              st.session_state.jobs["Status"] != "Completed"
          ],
          use_container_width=True,
      )
    else:
      st.info("No active jobs found.")

  with col_b:
    st.subheader("Department Breakdown")
    dept_counts = st.session_state.staff["Dept"].value_counts().reset_index()
    dept_counts.columns = ["Department", "Staff Count"]
    st.dataframe(dept_counts, use_container_width=True)

# --- 2. ATTENDANCE TRACKING PAGE ---
elif page == "🕒 Attendance Tracking":
  st.title("🕒 Attendance Management")
  st.markdown("Mark and track daily staff attendance across all units.")

  tab1, tab2 = st.tabs(["Mark Attendance", "View Attendance History"])

  with tab1:
    st.subheader("Daily Attendance Log Form")
    with st.form("attendance_form"):
      att_date = st.date_input("Attendance Date", datetime.now())
      selected_dept = st.selectbox(
          "Filter Department",
          [
              "All",
              "Production",
              "Business",
              "Admin",
              "QC",
              "Vault",
              "Fulfillment",
          ],
      )

      if selected_dept == "All":
        staff_to_mark = st.session_state.staff
      else:
        staff_to_mark = st.session_state.staff[
            st.session_state.staff["Dept"] == selected_dept
        ]

      st.write(f"Marking attendance for **{len(staff_to_mark)}** staff members:")

      attendance_status = {}
      for idx, row in staff_to_mark.iterrows():
        col_s1, col_s2, col_s3 = st.columns([3, 2, 3])
        with col_s1:
          st.text(f"{row['Name']} ({row['ID']})")
        with col_s2:
          st.text(row["Unit/Machine"])
        with col_s3:
          status = st.selectbox(
              f"Status_{row['ID']}",
              ["Present", "Absent", "Late", "On Leave"],
              label_visibility="collapsed",
          )
          attendance_status[row["ID"]] = (row["Name"], row["Dept"], status)

      submit_attendance = st.form_submit_button("Save Attendance Records")

      if submit_attendance:
        current_time = datetime.now().strftime("%H:%M:%S")
        date_str = str(att_date)

        st.session_state.attendance = st.session_state.attendance[
            st.session_state.attendance["Date"] != date_str
        ]

        new_entries = []
        for staff_id, details in attendance_status.items():
          new_entries.append({
              "Date": date_str,
              "Staff ID": staff_id,
              "Name": details[0],
              "Department": details[1],
              "Status": details[2],
              "Time In": current_time if details[2] == "Present" else "-",
          })

        new_df = pd.DataFrame(new_entries)
        st.session_state.attendance = pd.concat(
            [st.session_state.attendance, new_df], ignore_index=True
        )
        st.success(f"Attendance successfully recorded for {date_str}!")

  with tab2:
    st.subheader("Attendance Log Archive")
    if not st.session_state.attendance.empty:
      filter_date = st.date_input(
          "Filter by Date", datetime.now(), key="filter_att_date"
      )
      filtered_att = st.session_state.attendance[
          st.session_state.attendance["Date"] == str(filter_date)
      ]
      st.dataframe(filtered_att, use_container_width=True)
    else:
      st.info("No attendance records found yet.")

# --- 3. JOB & TASK TRACKER PAGE ---
elif page == "📋 Job & Task Tracker":
  st.title("📋 Production & Department Job Tracker")
  st.markdown("Assign tasks, update operational metrics, and track completion.")

  tab_j1, tab_j2 = st.tabs(["Active Job Directory", "Assign New Job"])

  with tab_j1:
    st.subheader("Manage Current Jobs")
    if not st.session_state.jobs.empty:
      status_filter = st.selectbox(
          "Filter by Status", ["All", "Pending", "In Progress", "Completed"]
      )
      df_jobs = st.session_state.jobs
      if status_filter != "All":
        df_jobs = df_jobs[df_jobs["Status"] == status_filter]

      st.dataframe(df_jobs, use_container_width=True)

      st.markdown("---")
      st.subheader("Update Job Status")
      job_to_update = st.selectbox(
          "Select Job ID to Update", st.session_state.jobs["Job ID"].tolist()
      )
      new_status = st.selectbox(
          "New Status", ["Pending", "In Progress", "Completed"]
      )

      if st.button("Update Status"):
        st.session_state.jobs.loc[
            st.session_state.jobs["Job ID"] == job_to_update, "Status"
        ] = new_status
        st.success(f"Job {job_to_update} status updated to {new_status}!")
        st.rerun()
    else:
      st.info("No jobs tracked currently.")

  with tab_j2:
    st.subheader("Create and Assign Job")
    with st.form("new_job_form"):
      job_id = f"JOB-{len(st.session_state.jobs) + 1001}"
      job_title = st.text_input("Job Title / Description")
      job_dept = st.selectbox(
          "Department",
          [
              "Production",
              "Business",
              "Admin",
              "QC",
              "Vault",
              "Fulfillment",
          ],
      )

      if job_dept == "Production":
        unit_machine = st.selectbox(
            "Production Unit / Machine",
            [
                "Perso (Machine 1-6)",
                "PMC (Machine 1-16)",
                "Telco (Machine 1-6)",
                "OC200 (Machine 1)",
                "SM74 Unit",
                "Mailer Unit",
                "CTP (Machine 1-4)",
                "IT - Nano 1610",
                "IT - Nano 9",
            ],
        )
      else:
        unit_machine = st.text_input("Unit / Section Workspace", "General Desk")

      available_staff = st.session_state.staff[
          st.session_state.staff["Dept"] == job_dept
      ]["Name"].tolist()
      assigned_staff = (
          st.selectbox("Assign Operator / Staff", available_staff)
          if available_staff
          else st.text_input("Assignee Name", "Unassigned")
      )

      priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
      submit_job = st.form_submit_button("Deploy Job Assignment")

      if submit_job:
        if job_title:
          new_job = {
              "Job ID": job_id,
              "Title": job_title,
              "Department": job_dept,
              "Unit/Machine": unit_machine,
              "Assigned To": assigned_staff,
              "Status": "Pending",
              "Priority": priority,
              "Date Assigned": str(datetime.now().date()),
          }
          st.session_state.jobs = pd.concat(
              [st.session_state.jobs, pd.DataFrame([new_job])],
              ignore_index=True,
          )
          st.success(
              f"Job {job_id} successfully created and assigned to"
              f" {assigned_staff}!"
          )
          st.rerun()
        else:
          st.error("Please provide a job title.")

# --- 4. STAFF & UNIT DIRECTORY PAGE ---
elif page == "👥 Staff & Unit Directory":
  st.title("👥 Staff Directory & Department Layout")
  st.markdown("Overview of personnel mapping across all production units & departments.")

  st.subheader("Filter Personnel by Department")
  selected_dept_dir = st.selectbox(
      "Choose Department",
      ["All", "Production", "Business", "Admin", "QC", "Vault", "Fulfillment"],
      key="dir_dept",
  )

  if selected_dept_dir == "All":
    st.dataframe(st.session_state.staff, use_container_width=True)
  else:
    st.dataframe(
        st.session_state.staff[
            st.session_state.staff["Dept"] == selected_dept_dir
        ],
        use_container_width=True,
    )

  st.markdown("---")
  with st.expander("➕ Add New Staff Member"):
    with st.form("add_staff_form"):
      st_id = f"STF0{len(st.session_state.staff) + 1:03d}"
      st_name = st.text_input("Full Name")
      st_dept = st.selectbox(
          "Department",
          [
              "Production",
              "Business",
              "Admin",
              "QC",
              "Vault",
              "Fulfillment",
          ],
          key="add_staff_dept",
      )

      if st_dept == "Production":
        st_unit = st.selectbox(
            "Unit/Machine Assignment",
            [
                "Perso - Machine 1",
                "Perso - Machine 2",
                "Perso - Machine 3",
                "Perso - Machine 4",
                "Perso - Machine 5",
                "Perso - Machine 6",
                "PMC - Machine 1",
                "PMC - Machine 2",
                "Telco - Machine 1",
                "Telco - Machine 2",
                "OC200 - Machine 1",
                "SM74 Unit",
                "Mailer Unit",
                "CTP - Machine 1",
                "IT - Nano 1610",
                "IT - Nano 9",
            ],
        )
      else:
        st_unit = st.text_input("Unit / Workspace description")

      st_role = st.text_input("Job Role / Designation", "Operator")
      submit_staff = st.form_submit_button("Register Staff")

      if submit_staff and st_name:
        new_staff_row = {
            "ID": st_id,
            "Name": st_name,
            "Dept": st_dept,
            "Unit/Machine": st_unit,
            "Role": st_role,
        }
        st.session_state.staff = pd.concat(
            [st.session_state.staff, pd.DataFrame([new_staff_row])],
            ignore_index=True,
        )
        st.success(
            f"Successfully registered {st_name} under {st_dept} ({st_unit})!"
        )
        st.rerun()

# --- 5. REPORTS & ANALYTICS PAGE ---
elif page == "📈 Reports & Analytics":
  st.title("📈 Reports & Data Export")
  st.markdown("Download operational reports and check system audit logs.")

  col_r1, col_r2 = st.columns(2)

  with col_r1:
    st.subheader("Download Staff Directory")
    st.dataframe(st.session_state.staff.head(5), use_container_width=True)
    csv_staff = st.session_state.staff.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Staff CSV",
        data=csv_staff,
        file_name="staff_directory.csv",
        mime="text/csv",
    )

  with col_r2:
    st.subheader("Download Job History")
    st.dataframe(st.session_state.jobs.head(5), use_container_width=True)
    csv_jobs = st.session_state.jobs.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Jobs CSV",
        data=csv_jobs,
        file_name="job_tracking_log.csv",
        mime="text/csv",
    )

  st.markdown("---")
  st.subheader("Download Attendance Log")
  if not st.session_state.attendance.empty:
    st.dataframe(st.session_state.attendance, use_container_width=True)
    csv_att = st.session_state.attendance.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Attendance Report CSV",
        data=csv_att,
        file_name="attendance_report.csv",
        mime="text/csv",
    )
  else:
    st.info("No attendance data logged yet for export.")
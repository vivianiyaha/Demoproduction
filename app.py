"""
Cardstel Solutions Ltd - Operations Tracker (multi-page Streamlit app)

Pages: Company Overview | Production Units | Departments | Attendance | Setup & Targets
Run:   streamlit run app.py
"""
import streamlit as st

from core import period_picker

st.set_page_config(page_title="Cardstel Ops Tracker", page_icon="🏭", layout="wide")

nav = st.navigation({
    "Overview": [st.Page("views/overview.py", title="Company Overview", icon="🏭", default=True)],
    "Operations": [st.Page("views/production.py", title="Production Units", icon="⚙️"),
                   st.Page("views/departments.py", title="Departments", icon="🏢")],
    "People": [st.Page("views/attendance.py", title="Attendance", icon="🕒")],
    "Admin": [st.Page("views/settings.py", title="Setup & Targets", icon="🛠️")],
})
# One shared reporting period for every page (kept in the sidebar)
st.session_state["period"] = period_picker()
nav.run()

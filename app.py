import streamlit as st
from database import create_ticket, get_all_tickets

st.set_page_config(page_title="Incident Intelligence Agent", page_icon="🚨", layout="wide")
st.title("🚨 Incident Intelligence Agent")
st.caption("AI-powered Incident Copilot – AWS x Datadog")

# --- Form Input ---
st.header("📝 Create Incident Ticket")

with st.form("incident_form", clear_on_submit=True):
    title = st.text_input("Title", placeholder="e.g. API Gateway 5xx spike")
    severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
    service_affected = st.text_input("Service Affected", placeholder="e.g. payment-service")
    description = st.text_area("Description", placeholder="Describe the incident...")
    submitted = st.form_submit_button("🚀 Submit Ticket")

    if submitted:
        if not title or not service_affected or not description:
            st.error("Please fill in all fields.")
        else:
            create_ticket(title, severity, service_affected, description)
            st.success(f"Ticket '{title}' created successfully!")

# --- Ticket List ---
st.divider()
st.header("📋 Incident Tickets")

tickets = get_all_tickets()

if not tickets:
    st.info("No tickets yet. Create one above!")
else:
    for t in tickets:
        severity_color = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
        icon = severity_color.get(t["severity"], "⚪")
        with st.expander(f"{icon} [{t['severity']}] {t['title']} — {t['service_affected']}"):
            st.text(f"ID: {t['id']}  |  Status: {t['status']}  |  Created: {t['created_at']}")
            st.markdown(f"**Description:**\n\n{t['description']}")

import streamlit as st
from database import create_ticket, get_all_tickets
from bedrock_agent import analyze_incident
from knowledge_base import s3_client, S3_BUCKET

st.set_page_config(page_title="Incident Intelligence Agent", page_icon="🚨", layout="wide")
st.title("🚨 Incident Intelligence Agent")
st.caption("AI-powered Incident Copilot – AWS x Datadog")

# --- Doc Preview Page (via query param) ---
query_params = st.query_params
if "doc" in query_params:
    doc_key = query_params["doc"]
    doc_name = doc_key.replace("docs/", "").replace(".md", "").replace("-", " ").title()
    st.header(f"📖 {doc_name}")
    st.caption(f"Source: s3://{S3_BUCKET}/{doc_key}")
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=doc_key)
        content = response["Body"].read().decode("utf-8")
        st.markdown(content)
    except Exception as e:
        st.error(f"Failed to load document: {e}")
    st.stop()

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

            if st.button(f"🧠 Analyze with AI", key=f"analyze_{t['id']}"):
                with st.spinner("Analyzing incident with Amazon Bedrock..."):
                    try:
                        analysis = analyze_incident(
                            t["title"], t["severity"], t["service_affected"], t["description"]
                        )
                        st.markdown("---")
                        st.markdown("### 🤖 AI Analysis")
                        st.markdown(analysis)
                    except Exception as e:
                        st.error(f"AI Analysis failed: {str(e)}")

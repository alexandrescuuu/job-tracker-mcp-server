import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from server import list_applications, add_application, log_followup, get_pending_followups

st.set_page_config(page_title="MCP Job Tracker Dashboard", layout="wide")

st.title("Job Application Tracker — MCP Server & Live Analytics")
st.markdown(
    "Companion visual dashboard for the **Model Context Protocol (`MCPServer`)** backend (`server.py` + `SQLite` with 2,500+ records)."
)

# Sidebar: Invoke MCP Tools directly
st.sidebar.header("Invoke MCP Tools")
with st.sidebar.form("add_app_form"):
    st.subheader("add_application()")
    company = st.text_input("Company", placeholder="e.g. DeepMind")
    role = st.text_input("Role", placeholder="e.g. Research Intern")
    status = st.selectbox("Status", ["Applied", "Interviewing", "Offer", "Rejected"])
    notes = st.text_input("Notes", placeholder="Applied via referral")
    if st.form_submit_button("Execute MCP Tool"):
        if company and role:
            msg = add_application(company=company, role=role, status=status, notes=notes)
            st.sidebar.success(msg)

with st.sidebar.form("followup_form"):
    st.subheader("log_followup()")
    f_company = st.text_input("Company Name", placeholder="e.g. Mistral AI")
    f_status = st.selectbox("New Status", ["(Keep current)", "Applied", "Interviewing", "Offer", "Rejected"])
    f_note = st.text_input("Follow-up Note", placeholder="Sent follow-up message")
    if st.form_submit_button("Update via MCP"):
        if f_company:
            st_val = None if f_status == "(Keep current)" else f_status
            msg = log_followup(company=f_company, new_status=st_val, note_update=f_note or None)
            st.sidebar.info(msg)

# Fetch live data via MCP tools
all_apps = list_applications()
pending = get_pending_followups(days_threshold=7)
df = pd.DataFrame(all_apps)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tracked Applications", f"{len(df):,}")
col2.metric("Active Interviews", f"{int((df['status'] == 'Interviewing').sum()):,}" if not df.empty else 0)
col3.metric("Offers Received", f"{int((df['status'] == 'Offer').sum()):,}" if not df.empty else 0)
col4.metric("Pending Follow-ups (>7d)", f"{len(pending):,}")

if not df.empty:
    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("Pipeline Breakdown by Status")
        status_counts = df["status"].value_counts()
        colors = {"Applied": "#1f77b4", "Interviewing": "#ff7f0e", "Rejected": "#d62728", "Offer": "#2ca02c"}
        bar_colors = [colors.get(s, "#7f7f7f") for s in status_counts.index]

        fig1, ax1 = plt.subplots(figsize=(5.5, 3.8), dpi=120)
        bars = ax1.bar(status_counts.index, status_counts.values, color=bar_colors)
        ax1.set_ylabel("Number of Applications")
        ax1.set_title("MCP Resource: jobs://summary (N = 2,500+)")
        ax1.grid(True, axis="y", linestyle="--", alpha=0.4)
        for bar in bars:
            h = int(bar.get_height())
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 15, f"{h:,}", ha="center", fontweight="bold")
        ax1.set_ylim(0, max(status_counts.values) * 1.15)
        plt.tight_layout()
        st.pyplot(fig1)

    with c_right:
        st.subheader("Follow-up Latency Distribution")
        today = datetime.now().date()
        df["days_since_contact"] = df["last_contact_date"].apply(
            lambda d: (today - datetime.strptime(d, "%Y-%m-%d").date()).days
        )
        active_df = df[df["status"].isin(["Applied", "Interviewing"])]

        fig2, ax2 = plt.subplots(figsize=(5.5, 3.8), dpi=120)
        on_time = active_df[active_df["days_since_contact"] < 7]["days_since_contact"]
        overdue = active_df[active_df["days_since_contact"] >= 7]["days_since_contact"]

        ax2.hist(on_time, bins=range(0, 8), color="#1f77b4", edgecolor="white", label="Recent (< 7 days)")
        ax2.hist(overdue, bins=range(7, 37, 2), color="#FF4B4B", edgecolor="white", label="Needs Follow-up (≥ 7 days)")
        ax2.axvline(7, color="black", linestyle="--", lw=1.5, label="7-day Threshold")
        ax2.set_xlabel("Days Since Last Contact")
        ax2.set_ylabel("Active Applications")
        ax2.set_title("Active Applications by Days Since Last Contact")
        ax2.legend()
        ax2.grid(True, axis="y", linestyle="--", alpha=0.4)
        plt.tight_layout()
        st.pyplot(fig2)

    st.subheader("Live SQLite Application Tracker (Latest 200 Records)")
    st.dataframe(df.drop(columns=["days_since_contact"], errors="ignore").head(200), use_container_width=True)

import streamlit as st
import openai
from datetime import datetime
import pandas as pd
import requests
import os

# Get password from environment or hardcoded fallback
CORRECT_PASSWORD = os.environ.get("APP_PASSWORD", "faiz2025")

# Set page config (optional: hides menu, sets title)
st.set_page_config(page_title="Real Estate LeadBot", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# If not authenticated, show only password screen
if not st.session_state.authenticated:
    st.markdown("### 🔐 Secure Access Required")
    password = st.text_input("Enter password", type="password")

    if password == CORRECT_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.error("❌ Incorrect password")
    st.stop()  # 👈 Stop everything else from rendering


# --- Streamlit Page Setup ---
st.set_page_config(page_title="Real Estate Lead Bot")
st.title("Real Estate Assistant Bot")

# --- Load OpenAI API Key ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- CSV File for Saving Leads ---
LEADS_FILE = "leads.csv"

# Initialize CSV with capitalized headers if not exists
if not os.path.exists(LEADS_FILE):
    df = pd.DataFrame(columns=["Timestamp", "Name", "City", "Intent", "Type", "Budget", "Phone"])
    df.to_csv(LEADS_FILE, index=False)

# --- Initialize Session State ---
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.lead = {}

# --- Zapier Webhook URL ---
ZAPIER_WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/23665833/u2b4m2h/"  # Replace with your actual Zapier URL

# --- Chatbot Questions ---
steps = [
    ("What is your name?", "name"),
    ("Which city are you looking to buy or rent in?", "city"),
    ("Are you looking to BUY or RENT?", "intent"),
    ("What type of property are you interested in? (House, Plot, Flat, Commercial)", "type"),
    ("What is your budget?", "budget"),
    ("Please share your WhatsApp number:", "phone")
]

# --- Chatbot Interaction Flow ---
def ask_question(question, key):
    return st.text_input(question, key=key)

if st.session_state.step < len(steps):
    question, key = steps[st.session_state.step]
    response = ask_question(question, key)

    if response:
        st.session_state.lead[key] = response
        st.session_state.step += 1
        st.rerun()

else:
    # --- Final Step: Save Lead, Send to Zapier, Show Summary ---
    if "lead" in st.session_state:
        lead_fixed = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": st.session_state.lead.get("name", ""),
            "City": st.session_state.lead.get("city", ""),
            "Intent": st.session_state.lead.get("intent", ""),
            "Type": st.session_state.lead.get("type", ""),
            "Budget": st.session_state.lead.get("budget", ""),
            "Phone": st.session_state.lead.get("phone", "")
        }

        # Save to CSV
        try:
            df = pd.read_csv(LEADS_FILE)
            df = pd.concat([df, pd.DataFrame([lead_fixed])], ignore_index=True)
            df.to_csv(LEADS_FILE, index=False)
        except PermissionError:
            st.warning("⚠️ Could not write to leads.csv — is the file open?")

        # Send to Zapier
        try:
            requests.post(ZAPIER_WEBHOOK_URL, json=lead_fixed)
        except Exception as e:
            st.warning(f"⚠️ Failed to send to Zapier: {e}")

        # Show summary
        st.success("🎉 Thanks! Our property expert will contact you shortly.")
        st.write("Here's what we captured:")
        st.json(lead_fixed)

        # Reset option
        if st.button("Start New Inquiry"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

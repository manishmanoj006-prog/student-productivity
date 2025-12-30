import os
import streamlit as st
import requests
import pandas as pd
import datetime
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501"
DB = "data/database.xlsx"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/fitness.activity.read",
]

st.title("🔗 Google Fit Integration")

EMAIL = st.session_state.get("email")
TODAY = datetime.date.today().strftime("%Y-%m-%d")

# ================= HELPERS =================
def load_auth_table():
    try:
        return pd.read_excel(DB, sheet_name="GoogleFitAuth")
    except:
        return pd.DataFrame(columns=["email", "refresh_token"])

def save_refresh_token(email, refresh_token):
    df = load_auth_table()
    df = df[df["email"] != email]
    df = pd.concat([df, pd.DataFrame([{
        "email": email,
        "refresh_token": refresh_token
    }])], ignore_index=True)

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="GoogleFitAuth", index=False)

def save_steps(email, steps, date):
    try:
        df = pd.read_excel(DB, sheet_name="GoogleFitData")
    except:
        df = pd.DataFrame(columns=["email", "date", "steps"])

    df["date"] = df["date"].astype(str)
    df = df[~((df["email"] == email) & (df["date"] == date))]

    df = pd.concat([df, pd.DataFrame([{
        "email": email,
        "date": date,
        "steps": steps
    }])], ignore_index=True)

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="GoogleFitData", index=False)

def fetch_steps(access_token):
    url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(hours=24)

    body = {
        "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": int(start.timestamp() * 1000),
        "endTimeMillis": int(now.timestamp() * 1000)
    }

    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json=body
    )
    return res.json()

# ================= OAUTH REDIRECT =================
if "code" in st.query_params:
    st.session_state.google_auth_code = st.query_params["code"]

auth_df = load_auth_table()
user_row = auth_df[auth_df["email"] == EMAIL]

# ================= USER ALREADY CONNECTED =================
if not user_row.empty:
    st.success("✅ Google Fit connected")

    if st.button("📥 Fetch Steps"):
        refresh_token = user_row.iloc[0]["refresh_token"]

        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )

        token_data = token_res.json()

        if "access_token" in token_data:
            data = fetch_steps(token_data["access_token"])
            steps = 0
            try:
                steps = data["bucket"][0]["dataset"][0]["point"][0]["value"][0]["intVal"]
            except:
                pass

            st.metric("👣 Steps (last 24h)", steps)
            save_steps(EMAIL, steps, TODAY)
            st.success("✅ Steps saved to dashboard")
        else:
            st.error("❌ Token refresh failed")
            st.write(token_data)

# ================= FIRST TIME USER =================
else:
    if "google_auth_code" in st.session_state:
        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": st.session_state.google_auth_code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )

        token_data = token_res.json()

        if "refresh_token" in token_data:
            save_refresh_token(EMAIL, token_data["refresh_token"])
            st.success("✅ Google Fit connected successfully")
            st.info("Reload this page to fetch steps")
        else:
            st.error("❌ Token error")
            st.write(token_data)

    else:
        if st.button("🔐 Connect Google Fit"):
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [REDIRECT_URI],
                    }
                },
                scopes=SCOPES,
            )

            flow.redirect_uri = REDIRECT_URI
            auth_url, _ = flow.authorization_url(
                prompt="consent",
                access_type="offline"
            )

            st.markdown(f"[👉 Login with Google]({auth_url})")

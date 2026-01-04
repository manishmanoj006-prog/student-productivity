import streamlit as st
import requests
import pandas as pd
import datetime
from google_auth_oauthlib.flow import Flow

DB = "data/database.xlsx"

# ---------- REDIRECT URI ----------
if st.secrets.get("IS_CLOUD", False):
    REDIRECT_URI = "https://student-appuctivity-magaudaxmuwptiwa9ar4dw.streamlit.app"
else:
    REDIRECT_URI = "http://localhost:8501"

CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/fitness.activity.read",
]

st.title("🔗 Google Fit Integration")

EMAIL = st.session_state.get("email")
if not EMAIL:
    st.warning("Please login first")
    st.stop()

TODAY = datetime.date.today().strftime("%Y-%m-%d")

# ---------- HELPERS ----------
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

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name="GoogleFitAuth", index=False)

def save_steps(email, steps):
    try:
        df = pd.read_excel(DB, sheet_name="GoogleFitData")
    except:
        df = pd.DataFrame(columns=["email", "date", "steps"])

    df = df[~((df["email"] == email) & (df["date"] == TODAY))]
    df = pd.concat([df, pd.DataFrame([{
        "email": email,
        "date": TODAY,
        "steps": steps
    }])], ignore_index=True)

    with pd.ExcelWriter(DB, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name="GoogleFitData", index=False)

def fetch_steps(access_token):
    url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(hours=24)

    body = {
        "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": int(start.timestamp() * 1000),
        "endTimeMillis": int(now.timestamp() * 1000),
    }

    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json=body
    )
    return res.json()

def extract_steps(data):
    total_steps = 0
    for bucket in data.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                for val in point.get("value", []):
                    total_steps += val.get("intVal", 0)
    return total_steps

def refresh_and_fetch():
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
    if "access_token" not in token_data:
        st.error("❌ Token refresh failed")
        return

    data = fetch_steps(token_data["access_token"])
    steps = extract_steps(data)

    save_steps(EMAIL, steps)
    st.metric("👣 Steps (last 24h)", steps)

# ---------- OAUTH REDIRECT ----------
if "code" in st.query_params:
    st.session_state.google_auth_code = st.query_params["code"]
    st.query_params.clear()
    st.rerun()

auth_df = load_auth_table()
user_row = auth_df[auth_df["email"] == EMAIL]
is_connected = not user_row.empty

# ---------- CONNECTED ----------
if is_connected:
    st.success("✅ Google Fit connected")
    st.caption("ℹ️ Your Google Fit account is already linked")

    if st.button("🔄 Re-fetch Steps"):
        refresh_and_fetch()

# ---------- NOT CONNECTED ----------
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
            st.success("✅ Google Fit connected")
            st.rerun()
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
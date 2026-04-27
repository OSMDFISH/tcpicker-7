# tcpicker_v2.py
# TCPicker V2 Clean Rebuild
#
# Run:
#   streamlit run tcpicker_v2.py
#
# Install:
#   python -m pip install streamlit pandas openpyxl

from __future__ import annotations

import datetime as dt
import base64
import hashlib
import hmac
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st


APP_NAME = "TCPicker"
APP_VERSION = "2.0-clean"
DEFAULT_RACE = "Kentucky Derby"
DEFAULT_TRACK = "Churchill Downs"
DEFAULT_RACE_DATE = dt.date(2026, 5, 2)
DEFAULT_RACE_NUMBER = 12

LIMITED_TRACKS = {
    "Churchill Downs": {
        "city": "Louisville, KY",
        "triple_crown_race": "Kentucky Derby",
        "default_race_number": 12,
        "default_date": dt.date(2026, 5, 2),
    },
    "Pimlico": {
        "city": "Baltimore, MD",
        "triple_crown_race": "Preakness Stakes",
        "default_race_number": 13,
        "default_date": dt.date(2026, 5, 16),
    },
    "Belmont Park": {
        "city": "Elmont, NY",
        "triple_crown_race": "Belmont Stakes",
        "default_race_number": 12,
        "default_date": dt.date(2026, 6, 6),
    },
}

REQUIRED_COLUMNS = [
    "Horse",
    "Post",
    "Odds",
    "Active",
    "Speed",
    "Recent Form",
    "Class",
    "Distance Fit",
    "Jockey",
    "Trainer",
    "Beyer Estimate",
    "Timeform Estimate",
    "Equibase Estimate",
    "Running Style",
    "Stamina",
    "Wet Track",
    "Notes",
]


DERBY_2026_FIELD = [
    {"Post": 1, "Horse": "Renegade", "Odds": "4-1", "Speed": 94, "Recent Form": 94, "Class": 92, "Distance Fit": 82, "Jockey": 96, "Trainer": 94, "Running Style": "stalker", "Stamina": 84, "Wet Track": 72, "Notes": "Favorite/major contender; rail post risk."},
    {"Post": 2, "Horse": "Albus", "Odds": "30-1", "Speed": 82, "Recent Form": 80, "Class": 79, "Distance Fit": 78, "Jockey": 82, "Trainer": 76, "Running Style": "stalker", "Stamina": 78, "Wet Track": 55, "Notes": "Longshot."},
    {"Post": 3, "Horse": "Intrepido", "Odds": "50-1", "Speed": 76, "Recent Form": 74, "Class": 72, "Distance Fit": 72, "Jockey": 78, "Trainer": 74, "Running Style": "unknown", "Stamina": 72, "Wet Track": 50, "Notes": "Deep longshot."},
    {"Post": 4, "Horse": "Litmus Test", "Odds": "30-1", "Speed": 80, "Recent Form": 78, "Class": 82, "Distance Fit": 76, "Jockey": 80, "Trainer": 96, "Running Style": "speed", "Stamina": 74, "Wet Track": 55, "Notes": "Longshot; strong trainer factor."},
    {"Post": 5, "Horse": "Right to Party", "Odds": "30-1", "Speed": 79, "Recent Form": 77, "Class": 78, "Distance Fit": 79, "Jockey": 72, "Trainer": 82, "Running Style": "closer", "Stamina": 82, "Wet Track": 58, "Notes": "Stamina add-in."},
    {"Post": 6, "Horse": "Commandment", "Odds": "6-1", "Speed": 96, "Recent Form": 97, "Class": 96, "Distance Fit": 90, "Jockey": 92, "Trainer": 95, "Running Style": "stalker", "Stamina": 88, "Wet Track": 72, "Notes": "Top contender."},
    {"Post": 7, "Horse": "Danon Bourbon", "Odds": "20-1", "Speed": 82, "Recent Form": 83, "Class": 80, "Distance Fit": 78, "Jockey": 78, "Trainer": 76, "Running Style": "stalker", "Stamina": 78, "Wet Track": 52, "Notes": "Price horse."},
    {"Post": 8, "Horse": "So Happy", "Odds": "15-1", "Speed": 85, "Recent Form": 87, "Class": 85, "Distance Fit": 82, "Jockey": 90, "Trainer": 82, "Running Style": "speed", "Stamina": 80, "Wet Track": 56, "Notes": "Exotics candidate."},
    {"Post": 9, "Horse": "The Puma", "Odds": "10-1", "Speed": 88, "Recent Form": 88, "Class": 86, "Distance Fit": 84, "Jockey": 91, "Trainer": 80, "Running Style": "stalker", "Stamina": 84, "Wet Track": 58, "Notes": "Contender."},
    {"Post": 10, "Horse": "Wonder Dean", "Odds": "30-1", "Speed": 79, "Recent Form": 79, "Class": 77, "Distance Fit": 76, "Jockey": 78, "Trainer": 75, "Running Style": "unknown", "Stamina": 76, "Wet Track": 50, "Notes": "Longshot."},
    {"Post": 11, "Horse": "Incredibolt", "Odds": "20-1", "Speed": 83, "Recent Form": 84, "Class": 80, "Distance Fit": 80, "Jockey": 76, "Trainer": 76, "Running Style": "stalker", "Stamina": 80, "Wet Track": 54, "Notes": "Fringe/value contender."},
    {"Post": 12, "Horse": "Chief Wallabee", "Odds": "8-1", "Speed": 90, "Recent Form": 89, "Class": 90, "Distance Fit": 88, "Jockey": 88, "Trainer": 94, "Running Style": "stalker", "Stamina": 88, "Wet Track": 62, "Notes": "Strong contender."},
    {"Post": 13, "Horse": "Silent Tactic", "Odds": "20-1", "Speed": 82, "Recent Form": 81, "Class": 81, "Distance Fit": 80, "Jockey": 78, "Trainer": 84, "Running Style": "closer", "Stamina": 82, "Wet Track": 58, "Notes": "Exotic add-in."},
    {"Post": 14, "Horse": "Potente", "Odds": "20-1", "Speed": 84, "Recent Form": 83, "Class": 85, "Distance Fit": 82, "Jockey": 84, "Trainer": 96, "Running Style": "speed", "Stamina": 80, "Wet Track": 56, "Notes": "Underneath use."},
    {"Post": 15, "Horse": "Emerging Market", "Odds": "15-1", "Speed": 86, "Recent Form": 90, "Class": 86, "Distance Fit": 84, "Jockey": 95, "Trainer": 92, "Running Style": "closer", "Stamina": 85, "Wet Track": 57, "Notes": "Value contender."},
    {"Post": 16, "Horse": "Pavlovian", "Odds": "30-1", "Speed": 79, "Recent Form": 78, "Class": 78, "Distance Fit": 76, "Jockey": 76, "Trainer": 82, "Running Style": "speed", "Stamina": 76, "Wet Track": 52, "Notes": "Longshot."},
    {"Post": 17, "Horse": "Six Speed", "Odds": "50-1", "Speed": 76, "Recent Form": 74, "Class": 72, "Distance Fit": 72, "Jockey": 82, "Trainer": 74, "Running Style": "unknown", "Stamina": 72, "Wet Track": 50, "Notes": "Deep longshot."},
    {"Post": 18, "Horse": "Further Ado", "Odds": "6-1", "Speed": 95, "Recent Form": 96, "Class": 94, "Distance Fit": 93, "Jockey": 94, "Trainer": 95, "Running Style": "closer", "Stamina": 94, "Wet Track": 70, "Notes": "Strong late-run/stamina profile."},
    {"Post": 19, "Horse": "Golden Tempo", "Odds": "30-1", "Speed": 80, "Recent Form": 80, "Class": 78, "Distance Fit": 78, "Jockey": 90, "Trainer": 80, "Running Style": "closer", "Stamina": 80, "Wet Track": 54, "Notes": "Longshot."},
    {"Post": 20, "Horse": "Fulleffort", "Odds": "20-1", "Speed": 88, "Recent Form": 90, "Class": 86, "Distance Fit": 91, "Jockey": 88, "Trainer": 95, "Running Style": "closer", "Stamina": 92, "Wet Track": 62, "Notes": "Stamina/exotics horse."},
]


EXPERT_AI_ORDER = {
    "Commandment": 1,
    "Further Ado": 2,
    "Renegade": 3,
    "Chief Wallabee": 4,
    "Emerging Market": 5,
    "The Puma": 6,
    "Fulleffort": 7,
    "So Happy": 8,
    "Potente": 9,
    "Incredibolt": 10,
}


def parse_fractional_odds(odds: str) -> float:
    text = str(odds).strip().lower().replace("/", "-")
    if text in {"even", "evens"}:
        return 1.0
    if "-" not in text:
        return 10.0
    try:
        a, b = text.split("-", 1)
        b_float = float(b)
        return float(a) / b_float if b_float else 10.0
    except Exception:
        return 10.0


def implied_probability(odds: str) -> float:
    value = parse_fractional_odds(odds)
    return 1 / (value + 1)


def estimate_external_ratings(row: pd.Series) -> Tuple[float, float, float]:
    base = (
        float(row["Speed"]) * 0.35
        + float(row["Recent Form"]) * 0.25
        + float(row["Class"]) * 0.20
        + float(row["Distance Fit"]) * 0.10
        + float(row["Stamina"]) * 0.10
    )
    beyer = round(60 + base * 0.45, 1)
    timeform = round(90 + base * 0.38, 1)
    equibase = round(65 + base * 0.42, 1)
    return beyer, timeform, equibase


def normalize_card(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "Horse":
                df[col] = ""
            elif col == "Odds":
                df[col] = "10-1"
            elif col == "Active":
                df[col] = True
            elif col in {"Running Style", "Notes"}:
                df[col] = ""
            else:
                df[col] = 50

    df["Horse"] = df["Horse"].astype(str).str.strip()
    df = df[df["Horse"] != ""].copy()

    df["Active"] = df["Active"].apply(lambda x: str(x).lower() not in {"false", "0", "no", "scratched", "scratch"})

    numeric_cols = [
        "Post",
        "Speed",
        "Recent Form",
        "Class",
        "Distance Fit",
        "Jockey",
        "Trainer",
        "Beyer Estimate",
        "Timeform Estimate",
        "Equibase Estimate",
        "Stamina",
        "Wet Track",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(50).astype(float)

    for idx, row in df.iterrows():
        if row["Beyer Estimate"] <= 0 or row["Timeform Estimate"] <= 0 or row["Equibase Estimate"] <= 0:
            beyer, timeform, equibase = estimate_external_ratings(row)
            df.at[idx, "Beyer Estimate"] = float(beyer)
            df.at[idx, "Timeform Estimate"] = float(timeform)
            df.at[idx, "Equibase Estimate"] = float(equibase)

    df = df.drop_duplicates(subset=["Horse"], keep="first")
    df = df.drop_duplicates(subset=["Post"], keep="first")
    return df[REQUIRED_COLUMNS].sort_values("Post").reset_index(drop=True)


@st.cache_data
def load_derby_card() -> pd.DataFrame:
    df = pd.DataFrame(DERBY_2026_FIELD)
    df["Active"] = True
    df["Beyer Estimate"] = 0.0
    df["Timeform Estimate"] = 0.0
    df["Equibase Estimate"] = 0.0
    return normalize_card(df)


def validate_card(df: pd.DataFrame, race_name: str) -> List[str]:
    warnings = []

    if df is None or df.empty:
        return ["No card loaded."]

    active = df[df["Active"] == True].copy()

    if race_name == "Kentucky Derby" and len(active) != 20:
        warnings.append(f"Kentucky Derby should have exactly 20 active horses. Current active count: {len(active)}.")

    if active["Horse"].duplicated().any():
        warnings.append("Duplicate horse names detected.")

    if active["Post"].duplicated().any():
        warnings.append("Duplicate post positions detected.")

    rating_cols = ["Speed", "Recent Form", "Class", "Distance Fit"]
    means = [active[c].mean() for c in rating_cols]
    if all(45 <= m <= 55 for m in means):
        warnings.append("Core ratings appear to be default placeholder values.")

    return warnings


def score_card(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_card(df)
    active = df[df["Active"] == True].copy()

    if active.empty:
        return pd.DataFrame()

    active["Odds Multiple"] = active["Odds"].apply(parse_fractional_odds)
    active["Market Probability %"] = active["Odds"].apply(lambda x: round(implied_probability(x) * 100, 1))

    active["Beyer Norm"] = ((active["Beyer Estimate"] - 60) / 50 * 100).clip(0, 100)
    active["Timeform Norm"] = ((active["Timeform Estimate"] - 90) / 50 * 100).clip(0, 100)
    active["Equibase Norm"] = ((active["Equibase Estimate"] - 65) / 50 * 100).clip(0, 100)

    active["Public Rating Score"] = (
        active["Beyer Norm"] * 0.40
        + active["Timeform Norm"] * 0.25
        + active["Equibase Norm"] * 0.35
    )

    active["Post Score"] = active["Post"].apply(
        lambda p: 35 if p == 1 else 55 if 2 <= p <= 4 else 80 if 5 <= p <= 14 else 60
    )

    active["Score"] = (
        active["Speed"] * 0.22
        + active["Recent Form"] * 0.18
        + active["Class"] * 0.14
        + active["Distance Fit"] * 0.13
        + active["Public Rating Score"] * 0.18
        + active["Trainer"] * 0.06
        + active["Jockey"] * 0.05
        + active["Post Score"] * 0.04
    ).round(2)

    active = active.sort_values("Score", ascending=False).reset_index(drop=True)
    active.insert(0, "Rank", range(1, len(active) + 1))

    total_score = active["Score"].sum()
    active["Model Win %"] = (active["Score"] / total_score * 100).round(1) if total_score else 0
    active["Edge %"] = (active["Model Win %"] - active["Market Probability %"]).round(1)
    active["Value Label"] = active["Edge %"].apply(lambda x: "Overlay" if x >= 3 else "Underlay" if x <= -3 else "Fair")
    active["Recommendation"] = active["Rank"].apply(
        lambda r: "Best Win Bet" if r == 1 else "Use in Exacta/Trifecta" if r <= 3 else "Exotic Add-In" if r <= 6 else "Watch"
    )

    return active


def build_bets(ranked: pd.DataFrame, base_bet: float, bankroll: float, risk_level: str) -> pd.DataFrame:
    if ranked is None or ranked.empty:
        return pd.DataFrame(columns=["Bet", "Horses", "Reason", "Unit", "Combinations", "Cost"])

    horses = ranked["Horse"].tolist()
    rows = []

    def add(bet: str, horses_list: List[str], reason: str, combos: int, unit: float = None):
        unit = float(base_bet if unit is None else unit)
        cost = round(unit * combos, 2)
        rows.append({
            "Bet": bet,
            "Horses": ", ".join(horses_list),
            "Reason": reason,
            "Unit": unit,
            "Combinations": combos,
            "Cost": cost,
        })

    add("Win", [horses[0]], "Top model horse", 1)

    if len(horses) >= 2:
        add("Exacta Box", horses[:2], "Top two in either order", 2)

    if len(horses) >= 3 and risk_level in {"Balanced", "Aggressive"}:
        add("Trifecta Box", horses[:3], "Top three in any order", 6)

    if len(horses) >= 4 and risk_level == "Aggressive":
        add("Superfecta Box", horses[:4], "Top four in any order", 24)

    bets = pd.DataFrame(rows)

    if not bets.empty and bets["Cost"].sum() > bankroll:
        keep = []
        total = 0.0
        for _, row in bets.sort_values("Cost").iterrows():
            if total + float(row["Cost"]) <= bankroll:
                keep.append(row)
                total += float(row["Cost"])
        bets = pd.DataFrame(keep)

    return bets


def build_expert_ai(ranked: pd.DataFrame) -> pd.DataFrame:
    if ranked is None or ranked.empty:
        return pd.DataFrame()

    rows = []
    for _, row in ranked.iterrows():
        horse = row["Horse"]
        expert_rank = EXPERT_AI_ORDER.get(horse, 99)
        expert_score = max(0, 101 - expert_rank)
        consensus = round(row["Score"] * 0.45 + expert_score * 0.55, 2)
        rows.append({
            "Horse": horse,
            "Model Rank": row["Rank"],
            "Model Score": row["Score"],
            "Expert/AI Rank": expert_rank,
            "Consensus Score": consensus,
            "Odds": row["Odds"],
            "Use": "Win/Key" if expert_rank == 1 else "Exacta/Trifecta" if expert_rank <= 3 else "Exotic Add-In" if expert_rank <= 8 else "Watch",
        })

    out = pd.DataFrame(rows).sort_values("Consensus Score", ascending=False).reset_index(drop=True)
    out.insert(0, "Consensus Rank", range(1, len(out) + 1))
    return out


def health_check(df: pd.DataFrame, ranked: pd.DataFrame, bets: pd.DataFrame, race_name: str) -> Dict[str, object]:
    return {
        "app_version": APP_VERSION,
        "race": race_name,
        "tracks_limited_to": list(LIMITED_TRACKS.keys()),
        "horses_loaded": int(len(df)) if df is not None else 0,
        "active_horses": int(len(df[df["Active"] == True])) if df is not None and not df.empty else 0,
        "rankings_rows": int(len(ranked)) if ranked is not None else 0,
        "bet_rows": int(len(bets)) if bets is not None else 0,
        "warnings": validate_card(df, race_name),
    }



def render_rankings_terms_help():
    """Popup/help section explaining ranking terms."""
    terms = {
        "Rank": "Overall model order after sorting by Score. Rank 1 is the top model pick.",
        "Horse": "Horse name.",
        "Post": "Starting gate position. Very inside or very outside posts can affect trip difficulty.",
        "Odds": "Market odds. Example: 6-1 means a $2 win bet returns $12 profit plus stake if successful.",
        "Score": "TCPicker's combined model score using speed, recent form, class, distance fit, ratings, jockey/trainer, and post position.",
        "Model Win %": "Estimated share of winning strength based on model score. It is not a guaranteed probability.",
        "Beyer Estimate": "Estimated Beyer-style speed figure. Official Beyer figures are DRF-owned/paid data; this app uses an estimate unless you import official figures.",
        "Timeform Estimate": "Estimated Timeform-style rating. Higher is better.",
        "Equibase Estimate": "Estimated Equibase-style speed/rating number. Higher is better.",
        "Public Rating Score": "Normalized blend of Beyer, Timeform, and Equibase estimates on a 0-100 scale.",
        "Edge %": "Model Win % minus market implied probability from odds. Positive values may indicate value.",
        "Value Label": "Overlay means model likes the horse more than the odds suggest; Underlay means odds may be too short; Fair means close.",
        "Recommendation": "Simple model guidance: win candidate, exotics use, or watch.",
    }

    try:
        with st.popover("❓ Ranking Terms"):
            for term, meaning in terms.items():
                st.markdown(f"**{term}** — {meaning}")
    except Exception:
        with st.expander("❓ Ranking Terms", expanded=False):
            for term, meaning in terms.items():
                st.markdown(f"**{term}** — {meaning}")



def calculate_win_place_show(stake: float, odds: str, bet_type: str) -> Dict[str, float]:
    """Estimate win/place/show payout from fractional odds."""
    odds_multiple = parse_fractional_odds(odds)

    if bet_type == "Win":
        profit = stake * odds_multiple
    elif bet_type == "Place":
        profit = stake * odds_multiple * 0.45
    elif bet_type == "Show":
        profit = stake * odds_multiple * 0.25
    else:
        profit = 0.0

    return {
        "Stake": round(stake, 2),
        "Estimated Profit": round(profit, 2),
        "Estimated Return": round(stake + profit, 2),
    }


def exotic_combinations(bet_type: str, horse_count: int) -> int:
    """Calculate combinations for common boxed exotic bets."""
    if bet_type == "Exacta Box":
        return horse_count * (horse_count - 1) if horse_count >= 2 else 0
    if bet_type == "Trifecta Box":
        return horse_count * (horse_count - 1) * (horse_count - 2) if horse_count >= 3 else 0
    if bet_type == "Superfecta Box":
        return horse_count * (horse_count - 1) * (horse_count - 2) * (horse_count - 3) if horse_count >= 4 else 0
    return 0


def calculate_exotic_cost(bet_type: str, horse_count: int, unit: float) -> Dict[str, float]:
    combos = exotic_combinations(bet_type, horse_count)
    return {
        "Combinations": combos,
        "Unit": round(unit, 2),
        "Total Cost": round(combos * unit, 2),
    }


def odds_to_probability_percent(odds: str) -> float:
    return round(implied_probability(odds) * 100, 2)


def bankroll_recommendation(bankroll: float, risk_level: str) -> Dict[str, float]:
    if risk_level == "Conservative":
        low, high = 0.01, 0.02
    elif risk_level == "Aggressive":
        low, high = 0.05, 0.10
    else:
        low, high = 0.02, 0.05

    return {
        "Low Suggested Risk": round(bankroll * low, 2),
        "High Suggested Risk": round(bankroll * high, 2),
    }



# -----------------------------
# Login / encrypted credential repository
# -----------------------------

CREDENTIAL_DIR = Path.home() / "Documents" / "TCPicker"
CREDENTIAL_FILE = CREDENTIAL_DIR / "tcpicker_credentials.json"
DEFAULT_USERNAME = "TRIPLE CROWN"
DEFAULT_PASSWORD = "RACE#2026!"
MAX_FAILED_LOGIN_ATTEMPTS = 10


def _make_salt() -> str:
    return base64.b64encode(os.urandom(16)).decode("utf-8")


def _hash_password(password: str, salt: str) -> str:
    """PBKDF2 password hash. Passwords are never stored in plain text."""
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        250_000,
    )
    return base64.b64encode(key).decode("utf-8")




def _normalize_phone(phone: str) -> str:
    """Keep phone number simple and SMS-provider-friendly."""
    phone = str(phone or "").strip()
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return phone


def _generate_mfa_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _send_sms_code(phone: str, code: str) -> Tuple[bool, str]:
    """
    Send SMS using Twilio if environment variables are configured.
    Required environment variables:
      TWILIO_ACCOUNT_SID
      TWILIO_AUTH_TOKEN
      TWILIO_FROM_NUMBER

    If Twilio is not configured, the app uses demo mode and displays the code on screen.
    """
    phone = _normalize_phone(phone)

    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.environ.get("TWILIO_FROM_NUMBER", "").strip()

    if not sid or not token or not from_number:
        return False, "SMS provider not configured. Demo mode will display the MFA code."

    try:
        from twilio.rest import Client  # type: ignore

        client = Client(sid, token)
        client.messages.create(
            body=f"Your TCPicker verification code is: {code}",
            from_=from_number,
            to=phone,
        )
        return True, f"SMS sent to {phone}."
    except Exception as e:
        return False, f"SMS send failed: {e}. Demo mode will display the MFA code."


def _start_mfa_challenge(username: str, phone: str) -> None:
    code = _generate_mfa_code()
    sent, message = _send_sms_code(phone, code)

    st.session_state["pending_mfa"] = True
    st.session_state["pending_mfa_username"] = username
    st.session_state["mfa_code_hash"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
    st.session_state["mfa_code_expires"] = time.time() + 300
    st.session_state["mfa_send_message"] = message
    st.session_state["mfa_demo_code"] = "" if sent else code


def _verify_mfa_code(code: str) -> Tuple[bool, str]:
    if not st.session_state.get("pending_mfa", False):
        return False, "No MFA challenge is pending."

    if time.time() > float(st.session_state.get("mfa_code_expires", 0)):
        return False, "MFA code expired. Please log in again."

    expected_hash = st.session_state.get("mfa_code_hash", "")
    actual_hash = hashlib.sha256(str(code).strip().encode("utf-8")).hexdigest()

    if hmac.compare_digest(actual_hash, expected_hash):
        return True, "MFA verified."

    return False, "Invalid MFA code."


def _clear_mfa_state() -> None:
    for key in [
        "pending_mfa",
        "pending_mfa_username",
        "mfa_code_hash",
        "mfa_code_expires",
        "mfa_send_message",
        "mfa_demo_code",
    ]:
        st.session_state.pop(key, None)


def _load_credential_repo() -> Dict:
    CREDENTIAL_DIR.mkdir(parents=True, exist_ok=True)

    if not CREDENTIAL_FILE.exists():
        repo = {
            "version": 1,
            "users": {},
        }
        _save_credential_repo(repo)
        _add_or_update_user(DEFAULT_USERNAME, DEFAULT_PASSWORD, role="admin", phone="", mfa_enabled=False, force=True)
        return _load_credential_repo()

    try:
        return json.loads(CREDENTIAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "users": {}}


def _save_credential_repo(repo: Dict) -> None:
    CREDENTIAL_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIAL_FILE.write_text(json.dumps(repo, indent=2), encoding="utf-8")




def _record_failed_login(username: str) -> None:
    """Increment failed login attempts and lock account at threshold."""
    username = str(username).strip().upper()
    if not username:
        return

    repo = _load_credential_repo()
    users = repo.setdefault("users", {})

    if username not in users:
        return

    user = users[username]
    failed = int(user.get("failed_attempts", 0)) + 1
    user["failed_attempts"] = failed
    user["last_failed_login"] = dt.datetime.now().isoformat(timespec="seconds")

    if failed >= MAX_FAILED_LOGIN_ATTEMPTS:
        user["locked"] = True
        user["locked_at"] = dt.datetime.now().isoformat(timespec="seconds")

    _save_credential_repo(repo)


def _clear_failed_login(username: str) -> None:
    """Clear failed login count after successful login or admin unlock."""
    username = str(username).strip().upper()
    repo = _load_credential_repo()
    users = repo.setdefault("users", {})

    if username in users:
        users[username]["failed_attempts"] = 0
        users[username]["locked"] = False
        users[username]["locked_at"] = ""
        _save_credential_repo(repo)


def _unlock_user(username: str) -> Tuple[bool, str]:
    username = str(username).strip().upper()
    repo = _load_credential_repo()
    users = repo.setdefault("users", {})

    if username not in users:
        return False, "User not found."

    users[username]["failed_attempts"] = 0
    users[username]["locked"] = False
    users[username]["locked_at"] = ""
    _save_credential_repo(repo)
    return True, f"User {username} unlocked."


def _add_or_update_user(username: str, password: str, role: str = "user", phone: str = "", mfa_enabled: bool = False, force: bool = False) -> Tuple[bool, str]:
    username = str(username).strip().upper()

    if not username:
        return False, "Username is required."

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."

    repo = _load_credential_repo()
    users = repo.setdefault("users", {})

    if username in users and not force:
        return False, "User already exists. Use Reset Password to update."

    existing = users.get(username, {})
    salt = _make_salt()
    users[username] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "role": role,
        "active": existing.get("active", True),
        "phone": _normalize_phone(phone or existing.get("phone", "")),
        "mfa_enabled": bool(mfa_enabled),
        "failed_attempts": int(existing.get("failed_attempts", 0)),
        "locked": bool(existing.get("locked", False)),
        "locked_at": existing.get("locked_at", ""),
        "created": existing.get("created", dt.datetime.now().isoformat(timespec="seconds")),
        "updated": dt.datetime.now().isoformat(timespec="seconds"),
    }

    _save_credential_repo(repo)
    return True, f"User {username} saved."


def _delete_user(username: str) -> Tuple[bool, str]:
    username = str(username).strip().upper()

    if username == DEFAULT_USERNAME:
        return False, "Default admin user cannot be deleted."

    repo = _load_credential_repo()
    users = repo.setdefault("users", {})

    if username not in users:
        return False, "User not found."

    del users[username]
    _save_credential_repo(repo)
    return True, f"User {username} deleted."


def _set_user_active(username: str, active: bool) -> Tuple[bool, str]:
    username = str(username).strip().upper()

    if username == DEFAULT_USERNAME and not active:
        return False, "Default admin user cannot be disabled."

    repo = _load_credential_repo()
    users = repo.setdefault("users", {})

    if username not in users:
        return False, "User not found."

    users[username]["active"] = bool(active)
    _save_credential_repo(repo)
    return True, f"User {username} updated."


def _verify_login(username: str, password: str) -> Tuple[bool, str]:
    username = str(username).strip().upper()
    repo = _load_credential_repo()
    users = repo.get("users", {})

    if username not in users:
        return False, "Invalid username or password."

    user = users[username]

    if user.get("locked", False):
        return False, "Account is locked after too many failed login attempts. Contact an admin."

    if not user.get("active", True):
        return False, "User is disabled."

    salt = user.get("salt", "")
    expected = user.get("password_hash", "")
    actual = _hash_password(password, salt)

    if hmac.compare_digest(actual, expected):
        _clear_failed_login(username)
        return True, user.get("role", "user")

    _record_failed_login(username)

    # Reload to see if the failed attempt locked the account.
    repo = _load_credential_repo()
    user = repo.get("users", {}).get(username, {})
    if user.get("locked", False):
        return False, "Account locked after 10 failed login attempts. Contact an admin."

    attempts = int(user.get("failed_attempts", 0))
    remaining = max(0, MAX_FAILED_LOGIN_ATTEMPTS - attempts)
    return False, f"Invalid username or password. Attempts remaining before lockout: {remaining}."




def _get_user_record(username: str) -> Dict:
    username = str(username).strip().upper()
    repo = _load_credential_repo()
    return repo.get("users", {}).get(username, {})


def _list_users_for_display() -> pd.DataFrame:
    repo = _load_credential_repo()
    rows = []

    for username, info in repo.get("users", {}).items():
        rows.append({
            "Username": username,
            "Role": info.get("role", "user"),
            "Active": info.get("active", True),
            "Phone": info.get("phone", ""),
            "MFA Enabled": info.get("mfa_enabled", False),
            "Failed Attempts": info.get("failed_attempts", 0),
            "Locked": info.get("locked", False),
            "Locked At": info.get("locked_at", ""),
            "Created": info.get("created", ""),
        })

    return pd.DataFrame(rows)


def require_login() -> None:
    """Stop the app until the user logs in."""
    _load_credential_repo()

    if st.session_state.get("authenticated", False):
        return

    st.title("🔐 TCPicker Login")
    # Default credentials hidden for security

    with st.form("login_form"):
        username = st.text_input("Username", value="")
        password = st.text_input("Password", type="password", value="")
        submitted = st.form_submit_button("Login")

    if submitted:
        ok, result = _verify_login(username, password)
        if ok:
            clean_username = username.strip().upper()
            user_record = _get_user_record(clean_username)
            if user_record.get("mfa_enabled", False):
                phone = user_record.get("phone", "")
                if not phone:
                    st.error("MFA is enabled for this user, but no cell number is stored. Contact an admin.")
                    st.stop()
                _start_mfa_challenge(clean_username, phone)
                st.session_state["pre_mfa_role"] = result
                st.rerun()
            else:
                st.session_state["authenticated"] = True
                st.session_state["username"] = clean_username
                st.session_state["role"] = result
                _clear_mfa_state()
                st.rerun()
        else:
            st.error(result)

    if st.session_state.get("pending_mfa", False):
        st.divider()
        st.subheader("MFA Verification")
        st.info(st.session_state.get("mfa_send_message", "Enter your 6-digit code."))
        if st.session_state.get("mfa_demo_code"):
            st.warning(f"Demo mode MFA code: {st.session_state['mfa_demo_code']}")

        with st.form("mfa_form"):
            mfa_code = st.text_input("6-digit code", max_chars=6)
            verify_submitted = st.form_submit_button("Verify Code")

        if verify_submitted:
            ok_mfa, msg_mfa = _verify_mfa_code(mfa_code)
            if ok_mfa:
                clean_username = st.session_state.get("pending_mfa_username", "")
                st.session_state["authenticated"] = True
                st.session_state["username"] = clean_username
                st.session_state["role"] = st.session_state.get("pre_mfa_role", "user")
                _clear_mfa_state()
                st.success("MFA verified.")
                st.rerun()
            else:
                st.error(msg_mfa)

        if st.button("Cancel Login"):
            _clear_mfa_state()
            st.rerun()

    st.stop()


def render_user_admin_tab():
    st.subheader("👤 User Maintenance")

    current_user = st.session_state.get("username", "")
    current_role = st.session_state.get("role", "user")

    st.write(f"Logged in as: **{current_user}**")
    st.write(f"Role: **{current_role}**")
    st.caption(f"Encrypted credential repository: {CREDENTIAL_FILE}")

    if current_role != "admin":
        st.warning("Only admin users can maintain users.")
        return

    st.markdown("### Existing Users")
    users_df = _list_users_for_display()
    if users_df.empty:
        st.info("No users found.")
    else:
        st.dataframe(users_df, use_container_width=True, hide_index=True)

    st.markdown("### Add New User")
    with st.form("add_user_form"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        new_role = st.selectbox("Role", ["user", "admin"])
        new_phone = st.text_input("Cell Number for MFA", help="Use format like +15551234567 for real SMS.")
        new_mfa_enabled = st.checkbox("Require MFA for this user", value=False)
        add_submitted = st.form_submit_button("Add User")

    if add_submitted:
        ok, msg = _add_or_update_user(new_username, new_password, role=new_role, phone=new_phone, mfa_enabled=new_mfa_enabled, force=False)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("### Reset Password")
    existing_users = users_df["Username"].tolist() if not users_df.empty else []
    if existing_users:
        with st.form("reset_password_form"):
            reset_user = st.selectbox("Select User", existing_users, key="reset_user")
            reset_password = st.text_input("New Password", type="password", key="reset_password")
            reset_submitted = st.form_submit_button("Reset Password")

        if reset_submitted:
            user_role = "admin" if reset_user == DEFAULT_USERNAME else "user"
            repo = _load_credential_repo()
            existing = repo.get("users", {}).get(reset_user, {})
            user_role = existing.get("role", user_role)
            ok, msg = _add_or_update_user(
                reset_user,
                reset_password,
                role=user_role,
                phone=existing.get("phone", ""),
                mfa_enabled=existing.get("mfa_enabled", False),
                force=True,
            )
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)


    st.markdown("### MFA Settings")
    if existing_users:
        with st.form("mfa_settings_form"):
            mfa_user = st.selectbox("Select User for MFA", existing_users, key="mfa_user")
            repo = _load_credential_repo()
            existing = repo.get("users", {}).get(mfa_user, {})
            mfa_phone = st.text_input("Cell Number", value=existing.get("phone", ""), help="Use +15551234567 for real SMS.")
            mfa_enabled = st.checkbox("Require MFA", value=bool(existing.get("mfa_enabled", False)))
            mfa_submitted = st.form_submit_button("Save MFA Settings")

        if mfa_submitted:
            repo = _load_credential_repo()
            user = repo.get("users", {}).get(mfa_user, {})
            if not user:
                st.error("User not found.")
            else:
                user["phone"] = _normalize_phone(mfa_phone)
                user["mfa_enabled"] = bool(mfa_enabled)
                user["updated"] = dt.datetime.now().isoformat(timespec="seconds")
                _save_credential_repo(repo)
                st.success(f"MFA settings saved for {mfa_user}.")
                st.rerun()

        test_user = st.selectbox("Send Test MFA Code To", existing_users, key="test_mfa_user")
        if st.button("Send Test MFA Code", use_container_width=True):
            repo = _load_credential_repo()
            user = repo.get("users", {}).get(test_user, {})
            phone = user.get("phone", "")
            if not phone:
                st.error("No phone number stored for this user.")
            else:
                code = _generate_mfa_code()
                sent, message = _send_sms_code(phone, code)
                st.info(message)
                if not sent:
                    st.warning(f"Demo mode test code: {code}")



    st.markdown("### Account Lockout")
    if existing_users:
        unlock_user = st.selectbox("User to Unlock", existing_users, key="unlock_user")
        if st.button("Unlock User / Clear Failed Attempts", use_container_width=True):
            ok, msg = _unlock_user(unlock_user)
            st.success(msg) if ok else st.error(msg)
            st.rerun()


    st.markdown("### Enable / Disable / Delete User")
    if existing_users:
        action_user = st.selectbox("User", existing_users, key="action_user")
        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("Enable User", use_container_width=True):
                ok, msg = _set_user_active(action_user, True)
                st.success(msg) if ok else st.error(msg)
                st.rerun()

        with c2:
            if st.button("Disable User", use_container_width=True):
                ok, msg = _set_user_active(action_user, False)
                st.success(msg) if ok else st.error(msg)
                st.rerun()

        with c3:
            if st.button("Delete User", use_container_width=True):
                ok, msg = _delete_user(action_user)
                st.success(msg) if ok else st.error(msg)
                st.rerun()



def build_estimated_payout_table(ranked: pd.DataFrame, stake: float) -> pd.DataFrame:
    """Build win/place/show estimated payout table from current odds."""
    if ranked is None or ranked.empty:
        return pd.DataFrame()

    rows = []
    for _, row in ranked.iterrows():
        odds = row["Odds"]
        win = calculate_win_place_show(stake, odds, "Win")
        place = calculate_win_place_show(stake, odds, "Place")
        show = calculate_win_place_show(stake, odds, "Show")
        rows.append({
            "Rank": row.get("Rank", ""),
            "Horse": row["Horse"],
            "Post": row.get("Post", ""),
            "Odds": odds,
            "Implied Probability %": odds_to_probability_percent(odds),
            "Win Profit": win["Estimated Profit"],
            "Win Return": win["Estimated Return"],
            "Place Est. Return": place["Estimated Return"],
            "Show Est. Return": show["Estimated Return"],
        })
    return pd.DataFrame(rows)


def build_exotic_cost_table(max_horses: int, unit: float) -> pd.DataFrame:
    """Show exacta/trifecta/superfecta box costs by number of horses."""
    rows = []
    for n in range(2, max_horses + 1):
        for bet_type in ["Exacta Box", "Trifecta Box", "Superfecta Box"]:
            needed = {"Exacta Box": 2, "Trifecta Box": 3, "Superfecta Box": 4}[bet_type]
            if n >= needed:
                result = calculate_exotic_cost(bet_type, n, unit)
                rows.append({
                    "Bet Type": bet_type,
                    "Horses Used": n,
                    "Combinations": result["Combinations"],
                    "Unit": result["Unit"],
                    "Total Cost": result["Total Cost"],
                })
    return pd.DataFrame(rows)



def estimate_exotic_payout(total_cost: float, bankroll: float, bet_type: str) -> Dict[str, float]:
    """
    Simple planning estimate for exotic bets.
    This is NOT an official pari-mutuel payout. Actual payout depends on pool, takeout, odds, and winning tickets.
    """
    if bet_type == "Exacta Box":
        multiplier_low, multiplier_mid, multiplier_high = 3, 8, 20
    elif bet_type == "Trifecta Box":
        multiplier_low, multiplier_mid, multiplier_high = 8, 25, 75
    elif bet_type == "Superfecta Box":
        multiplier_low, multiplier_mid, multiplier_high = 20, 80, 250
    else:
        multiplier_low, multiplier_mid, multiplier_high = 1, 1, 1

    return {
        "Low Estimate": round(total_cost * multiplier_low, 2),
        "Middle Estimate": round(total_cost * multiplier_mid, 2),
        "High Estimate": round(total_cost * multiplier_high, 2),
        "Risk % of Bankroll": round((total_cost / bankroll * 100), 2) if bankroll else 0.0,
    }


st.set_page_config(page_title=APP_NAME, page_icon="🏇", layout="wide")
require_login()

st.title("🏇 TCPicker V2")
st.caption("Clean rebuild: limited tracks, Derby default, model rankings, expert/AI tab, betting page, and health checks.")

if "card" not in st.session_state:
    st.session_state.card = load_derby_card()

with st.sidebar:
    st.write(f"Logged in: **{st.session_state.get('username', '')}**")
    if st.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.session_state["role"] = ""
        st.rerun()

    st.header("Race Setup")

    race_choice = st.selectbox(
        "Race",
        ["Kentucky Derby", "Preakness Stakes", "Belmont Stakes", "Pick Custom Race"],
        index=0,
    )

    if race_choice == "Kentucky Derby":
        default_track = "Churchill Downs"
    elif race_choice == "Preakness Stakes":
        default_track = "Pimlico"
    elif race_choice == "Belmont Stakes":
        default_track = "Belmont Park"
    else:
        default_track = DEFAULT_TRACK

    track = st.selectbox(
        "Track",
        list(LIMITED_TRACKS.keys()),
        index=list(LIMITED_TRACKS.keys()).index(default_track),
    )

    race_date = st.date_input("Race Date", LIMITED_TRACKS[track]["default_date"])
    race_number = st.number_input("Race Number", 1, 20, LIMITED_TRACKS[track]["default_race_number"])

    st.divider()
    base_bet = st.number_input("Base Bet / Unit", 0.10, 1000.00, 2.00, 0.50, format="%.2f")
    bankroll = st.number_input("Bankroll", 1.00, 100000.00, 100.00, 10.00, format="%.2f")
    risk_level = st.selectbox("Risk Level", ["Conservative", "Balanced", "Aggressive"], index=1)

    st.divider()
    if st.button("Reset to Official Derby Field", use_container_width=True):
        st.session_state.card = load_derby_card()
        st.success("Derby field reset.")

card = normalize_card(st.session_state.card)
ranked = score_card(card)
bets = build_bets(ranked, base_bet, bankroll, risk_level)
expert_ai = build_expert_ai(ranked)

if "last_wps_result" not in st.session_state:
    st.session_state["last_wps_result"] = None

if "last_exotic_result" not in st.session_state:
    st.session_state["last_exotic_result"] = None


tabs = st.tabs([
    "🏇 Picks",
    "💰 Bets",
    "📊 Rankings",
    "🧠 Experts + AI",
    "📝 Edit Card",
    "👤 Users",
    "⚙️ Health / Export",
])

with tabs[0]:
    warnings = validate_card(card, race_choice)
    if warnings:
        for warning in warnings:
            st.warning(warning)

    if ranked.empty:
        st.error("No rankings available. Click Reset to Official Derby Field.")
    else:
        top = ranked.iloc[0]
        value = ranked[ranked["Value Label"] == "Overlay"]
        best_value = value.iloc[0]["Horse"] if not value.empty else top["Horse"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏆 Top Pick", top["Horse"])
        c2.metric("Model Score", top["Score"])
        c3.metric("Best Value", best_value)
        c4.metric("Field Size", len(ranked))

        st.subheader("Quick Bet Plan")
        st.dataframe(bets, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Betting Page")
    st.markdown("### Estimated Payouts Based on Current Odds")
    payout_stake = st.number_input(
        "Payout table stake",
        min_value=0.10,
        value=float(base_bet),
        step=0.50,
        format="%.2f",
        key="payout_table_stake",
    )
    payout_table = build_estimated_payout_table(ranked, payout_stake)
    if payout_table.empty:
        st.warning("No current odds payout table available.")
    else:
        st.dataframe(payout_table, use_container_width=True, hide_index=True, height=420)
        st.download_button(
            "Download Estimated Payouts CSV",
            data=payout_table.to_csv(index=False).encode("utf-8"),
            file_name="tcpicker_estimated_payouts.csv",
            mime="text/csv",
            key="download_estimated_payouts_csv",
        )

    with st.expander("Exotic Box Cost Table", expanded=False):
        exotic_unit_for_table = st.number_input(
            "Exotic cost table unit",
            min_value=0.10,
            value=float(base_bet),
            step=0.50,
            format="%.2f",
            key="exotic_cost_table_unit",
        )
        max_horses_for_table = st.slider("Max horses in box", 2, 8, 5, key="max_horses_exotic_table")
        st.dataframe(
            build_exotic_cost_table(max_horses_for_table, exotic_unit_for_table),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("❓ Bet Calculator Terms", expanded=False):
        st.markdown("**Win** — horse must finish 1st.  **Place** — horse finishes 1st or 2nd.  **Show** — horse finishes 1st, 2nd, or 3rd.")
        st.markdown("**Exacta Box** — selected horses must finish 1st and 2nd in any order.")
        st.markdown("**Trifecta Box** — selected horses must finish 1st, 2nd, and 3rd in any order.")
        st.markdown("**Superfecta Box** — selected horses must finish 1st, 2nd, 3rd, and 4th in any order.")
        st.markdown("**Implied Probability** — odds converted to a rough market probability.")
        st.markdown("**Estimated Payouts** — uses current fractional odds from the race card. Place/Show are estimates only because actual pari-mutuel payouts depend on pools.")

    if bets.empty:
        st.warning("No bets available.")
    else:
        total_cost = bets["Cost"].sum()
        st.metric("Total Ticket Cost", f"${total_cost:,.2f}")

        # Estimated payout planning for the generated ticket plan.
        est_low = 0.0
        est_mid = 0.0
        est_high = 0.0
        for _, b in bets.iterrows():
            bet_name = str(b.get("Bet", ""))
            cost = float(b.get("Cost", 0))
            if bet_name == "Win":
                horse_name = str(b.get("Horses", "")).split(",")[0].strip()
                match = ranked[ranked["Horse"] == horse_name]
                if not match.empty:
                    odds = match.iloc[0]["Odds"]
                    win_est = calculate_win_place_show(cost, odds, "Win")
                    est_low += win_est["Estimated Return"]
                    est_mid += win_est["Estimated Return"]
                    est_high += win_est["Estimated Return"]
            else:
                p = estimate_exotic_payout(cost, bankroll, bet_name)
                est_low += p["Low Estimate"]
                est_mid += p["Middle Estimate"]
                est_high += p["High Estimate"]

        st.markdown("#### Estimated Payout Range for Recommended Plan")
        rp1, rp2, rp3 = st.columns(3)
        rp1.metric("Low Estimate", f"${est_low:,.2f}")
        rp2.metric("Middle Estimate", f"${est_mid:,.2f}")
        rp3.metric("High Estimate", f"${est_high:,.2f}")
        st.caption("Plan payout estimates are rough planning numbers only; actual payouts depend on pari-mutuel pools and final odds.")

        st.dataframe(bets, use_container_width=True, hide_index=True)

    st.subheader("Auto Bet Calculator")

    calc_tab1, calc_tab2, calc_tab3 = st.tabs(["Win / Place / Show", "Exacta / Trifecta / Superfecta", "Odds + Bankroll"])

    with calc_tab1:
        c1, c2, c3 = st.columns(3)

        with c1:
            wps_type = st.selectbox("Bet Type", ["Win", "Place", "Show"], key="wps_type")
        with c2:
            wps_horse = st.selectbox("Horse", ranked["Horse"].tolist(), key="wps_horse")
        with c3:
            wps_stake = st.number_input("Stake", min_value=0.10, value=float(base_bet), step=0.50, format="%.2f", key="wps_stake")

        if st.button("Calculate Win / Place / Show Payout", use_container_width=True, key="btn_calculate_wps_payout"):
            horse_row = ranked[ranked["Horse"] == wps_horse].iloc[0]
            payout = calculate_win_place_show(wps_stake, horse_row["Odds"], wps_type)
            st.session_state["last_wps_result"] = {
                "horse": wps_horse,
                "bet_type": wps_type,
                "odds": horse_row["Odds"],
                "probability": odds_to_probability_percent(horse_row["Odds"]),
                "profit": payout["Estimated Profit"],
                "return": payout["Estimated Return"],
            }

        if st.session_state.get("last_wps_result"):
            result = st.session_state["last_wps_result"]
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Odds", result["odds"])
            p2.metric("Implied Probability", f"{result['probability']}%")
            p3.metric("Estimated Profit", f"${result['profit']:,.2f}")
            p4.metric("Estimated Return", f"${result['return']:,.2f}")

    with calc_tab2:
        e1, e2, e3 = st.columns(3)

        with e1:
            exotic_type = st.selectbox("Exotic Bet", ["Exacta Box", "Trifecta Box", "Superfecta Box"], key="exotic_type")
        with e2:
            exotic_unit = st.number_input("Unit Amount", min_value=0.10, value=float(base_bet), step=0.50, format="%.2f", key="exotic_unit")
        with e3:
            st.metric("Bankroll", f"${bankroll:,.2f}")

        default_count = {"Exacta Box": 2, "Trifecta Box": 3, "Superfecta Box": 4}[exotic_type]
        selected_exotic = st.multiselect(
            "Select Horses",
            ranked["Horse"].tolist(),
            default=ranked["Horse"].tolist()[:default_count],
            key="selected_exotic_horses",
        )

        if st.button("Calculate Exotic Bet Cost", use_container_width=True, key="btn_calculate_exotic_cost"):
            result = calculate_exotic_cost(exotic_type, len(selected_exotic), exotic_unit)
            st.session_state["last_exotic_result"] = {
                "bet_type": exotic_type,
                "horses": selected_exotic,
                "combinations": result["Combinations"],
                "unit": result["Unit"],
                "total_cost": result["Total Cost"],
            }

        if st.session_state.get("last_exotic_result"):
            result = st.session_state["last_exotic_result"]

            ec1, ec2, ec3 = st.columns(3)
            ec1.metric("Combinations", result["combinations"])
            ec2.metric("Unit", f"${result['unit']:,.2f}")
            ec3.metric("Total Cost", f"${result['total_cost']:,.2f}")

            st.markdown("#### Estimated Payout Range")
            payout_est = estimate_exotic_payout(result["total_cost"], bankroll, result["bet_type"])
            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("Low Estimate", f"${payout_est['Low Estimate']:,.2f}")
            pc2.metric("Middle Estimate", f"${payout_est['Middle Estimate']:,.2f}")
            pc3.metric("High Estimate", f"${payout_est['High Estimate']:,.2f}")
            pc4.metric("Risk % Bankroll", f"{payout_est['Risk % of Bankroll']}%")
            st.caption("Exotic payout range is a planning estimate only. Actual pari-mutuel payouts depend on the pool, takeout, odds, and winning tickets.")

            if result["total_cost"] > bankroll:
                st.error("This ticket costs more than your bankroll.")
            elif result["total_cost"] > bankroll * 0.10:
                st.warning("This is an aggressive ticket relative to bankroll.")
            else:
                st.success("Ticket cost is within bankroll range.")

            if result["horses"]:
                st.write("Selected horses: **" + ", ".join(result["horses"]) + "**")

    with calc_tab3:
        st.markdown("### Odds to Probability")
        odds_choice = st.selectbox("Horse Odds", ranked["Horse"].tolist(), key="odds_probability_horse")
        odds_row = ranked[ranked["Horse"] == odds_choice].iloc[0]

        op1, op2, op3 = st.columns(3)
        op1.metric("Horse", odds_choice)
        op2.metric("Odds", odds_row["Odds"])
        op3.metric("Implied Probability", f"{odds_to_probability_percent(odds_row['Odds'])}%")

        st.markdown("### Bankroll Strategy")
        bank = bankroll_recommendation(bankroll, risk_level)

        b1, b2, b3 = st.columns(3)
        b1.metric("Risk Level", risk_level)
        b2.metric("Low Suggested Race Risk", f"${bank['Low Suggested Risk']:,.2f}")
        b3.metric("High Suggested Race Risk", f"${bank['High Suggested Risk']:,.2f}")

        st.info(
            "Conservative: 1–2% per race. Balanced: 2–5%. Aggressive: 5–10%. "
            "This is bankroll planning only, not a guarantee."
        )

with tabs[2]:
    st.subheader("Model Rankings")
    render_rankings_terms_help()
    display_cols = [
        "Rank", "Horse", "Post", "Odds", "Score", "Model Win %",
        "Beyer Estimate", "Timeform Estimate", "Equibase Estimate",
        "Public Rating Score", "Edge %", "Value Label", "Recommendation", "Notes",
    ]
    st.dataframe(ranked[display_cols], use_container_width=True, hide_index=True, height=600)
    st.caption("Tip: Click ❓ Ranking Terms above for definitions of Score, Edge %, Overlay, Beyer Estimate, Timeform Estimate, and Equibase Estimate.")

with tabs[3]:
    st.subheader("Expert + AI Consensus")
    st.info("This tab is separate from model rankings. It blends expert/AI ordering with the model score.")
    st.dataframe(expert_ai, use_container_width=True, hide_index=True, height=600)

with tabs[4]:
    st.subheader("Edit Race Card")

    uploaded = st.file_uploader("Import CSV or Excel", type=["csv", "xlsx", "xls"])
    if uploaded:
        try:
            if uploaded.name.lower().endswith(".csv"):
                imported = pd.read_csv(uploaded)
            else:
                imported = pd.read_excel(uploaded)
            st.session_state.card = normalize_card(imported)
            st.success("Imported card.")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

    edited = st.data_editor(
        card,
        num_rows="dynamic",
        use_container_width=True,
        height=600,
        column_config={
            "Active": st.column_config.CheckboxColumn("Active"),
            "Post": st.column_config.NumberColumn("Post", min_value=1, max_value=24),
            "Speed": st.column_config.NumberColumn("Speed", min_value=0, max_value=120),
            "Recent Form": st.column_config.NumberColumn("Recent Form", min_value=0, max_value=120),
            "Class": st.column_config.NumberColumn("Class", min_value=0, max_value=120),
            "Distance Fit": st.column_config.NumberColumn("Distance Fit", min_value=0, max_value=120),
            "Jockey": st.column_config.NumberColumn("Jockey", min_value=0, max_value=120),
            "Trainer": st.column_config.NumberColumn("Trainer", min_value=0, max_value=120),
            "Beyer Estimate": st.column_config.NumberColumn("Beyer Estimate", min_value=0, max_value=150),
            "Timeform Estimate": st.column_config.NumberColumn("Timeform Estimate", min_value=0, max_value=170),
            "Equibase Estimate": st.column_config.NumberColumn("Equibase Estimate", min_value=0, max_value=150),
        },
    )

    if st.button("Save Edited Card", use_container_width=True):
        st.session_state.card = normalize_card(edited)
        st.success("Saved.")
        st.rerun()


with tabs[5]:
    render_user_admin_tab()

with tabs[6]:
    st.subheader("Health Check")
    st.json(health_check(card, ranked, bets, race_choice))

    st.subheader("Export")
    st.download_button(
        "Download Rankings CSV",
        data=ranked.to_csv(index=False).encode("utf-8"),
        file_name="tcpicker_rankings.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download Bets CSV",
        data=bets.to_csv(index=False).encode("utf-8"),
        file_name="tcpicker_bets.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download Race Card CSV",
        data=card.to_csv(index=False).encode("utf-8"),
        file_name="tcpicker_race_card.csv",
        mime="text/csv",
    )

st.warning("For entertainment and planning only. No rating estimate or recommendation guarantees wagering results.")

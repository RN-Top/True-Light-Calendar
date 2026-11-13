"""
True Light Calendar vs Today's Calendar - Streamlit app.

Run locally:   streamlit run app.py
Deploy:        push this folder to GitHub, then "New app" on share.streamlit.io
               and point it at app.py.
"""

from datetime import date, datetime, timedelta, timezone

import streamlit as st

from calendar_engine import drew_year, drew_year_for
from visuals import (BASE_CSS, BG, CYAN, compare_strip, day_cards,
                     events_table, hero, month_grids, thread_key, year_wheel)

st.set_page_config(page_title="True Light Calendar vs Today's Calendar",
                   page_icon="🌙", layout="wide")

# ---- global look: dark, neon, big text -----------------------------------
st.markdown(f"""
<style>
{BASE_CSS}
html, body, [data-testid="stAppViewContainer"] {{ background:{BG}; }}
[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top: 1.2rem; max-width: 1300px; }}
h2, h3 {{ font-family:'Orbitron',sans-serif !important; color:{CYAN} !important;
  letter-spacing:.06em; text-shadow: 0 0 10px {CYAN}66; }}
p, label, .stMarkdown, .stRadio label, .stSelectbox label {{ font-size:19px !important; }}
.stTabs [data-baseweb="tab"] p {{ font-family:'Orbitron',sans-serif; font-size:16px !important;
  font-weight:700; }}
.stTabs [aria-selected="true"] p {{ color:{CYAN} !important; }}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Reading the moon...")
def get_year(label: int, tz: float, rule: str, anchor: str):
    return drew_year(label, tz, rule, anchor)


@st.cache_data
def get_year_for(d: date, tz: float, rule: str, anchor: str):
    return drew_year_for(d, tz, rule, anchor)


st.html(hero())

# ---- settings ------------------------------------------------------------
with st.expander("⚙️  SETTINGS", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        tz = st.number_input("Your time zone (hours from UTC)", -12.0, 14.0, -5.0, 0.5,
                             help="Naples, FL = -5 in winter, -4 in summer")
        rule = st.radio("A month starts on…",
                        ["new", "crescent"],
                        format_func=lambda x: {"new": "the dark new moon",
                                               "crescent": "the first sliver (day after)"}[x])
    with c2:
        anchor = st.radio("Month 1 is…", ["after", "nearest"],
                          format_func=lambda x: {
                              "after": "first new moon AFTER the spring equinox (always spring)",
                              "nearest": "the new moon NEAREST the spring equinox"}[x])

now_local = datetime.now(timezone.utc) + timedelta(hours=tz)
today = now_local.date()

picked = st.date_input("📅  Pick any day to compare (defaults to today)",
                       value=today, min_value=date(1902, 1, 1),
                       max_value=date(2099, 12, 31))

y_sel = get_year_for(picked, tz, rule, anchor)

st.markdown("## ◉ THIS DAY, BOTH CALENDARS")
st.html(day_cards(y_sel, picked))

st.markdown("## ◉ THE TWO YEARS")
year_options = list(range(1902, 2099))
year_label = st.selectbox("True Light year (starts in the spring of…)", year_options,
                          index=year_options.index(y_sel.label))
y = get_year(year_label, tz, rule, anchor)
st.html(compare_strip(y))

tab1, tab2, tab3, tab4 = st.tabs(["🗓  MONTH BY MONTH", "🌀  YEAR WHEEL",
                                  "★  KEY DAYS", "📜  THE THREAD"])
with tab1:
    st.html(month_grids(y, picked))
with tab2:
    st.html(year_wheel(y, picked))
with tab3:
    st.html(events_table(y))
with tab4:
    st.html(thread_key())
    st.caption("This is a visual of the model in the Nov 12, 2026 thread with Drew — "
               "built to see it, not as a claim that it's the true calendar. "
               "Moon, equinox and Venus positions are calculated (Meeus / JPL formulas).")

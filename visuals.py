"""
visuals.py - builds the HTML/SVG for each section of the app.

Every function returns a self-contained HTML string (its own <style> block),
so it renders the same in Streamlit (st.html) or in a plain browser.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from html import escape

from calendar_engine import (DREW_WEEKDAYS, TODAY_WEEKDAYS, DrewYear,
                             moon_emoji)

# ---- palette: dark background, high-contrast neon ------------------------
BG = "#05060f"
PANEL = "#0d1024"
CYAN = "#00f0ff"      # Drew's calendar
MAGENTA = "#ff2bd6"   # today's calendar
LIME = "#b6ff00"      # spring / up
ORANGE = "#ff8a00"    # fall / down
YELLOW = "#ffe600"    # marked days
WHITE = "#ffffff"
GREY = "#8a90b8"
VIOLET = "#a78bff"    # Venus

FONTS = ("@import url('https://fonts.googleapis.com/css2?"
         "family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');")

BASE_CSS = f"""
{FONTS}
.dc * {{ box-sizing: border-box; }}
.dc {{ font-family: 'Rajdhani', 'Segoe UI', sans-serif; color: {WHITE}; }}
.dc .orb {{ font-family: 'Orbitron', 'Rajdhani', sans-serif; letter-spacing: .06em; }}
.dc .glow-c {{ color: {CYAN}; text-shadow: 0 0 10px {CYAN}88; }}
.dc .glow-m {{ color: {MAGENTA}; text-shadow: 0 0 10px {MAGENTA}88; }}
.dc .glow-y {{ color: {YELLOW}; text-shadow: 0 0 10px {YELLOW}88; }}
"""

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def _fmt(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _half_color(half: str) -> str:
    return LIME if half == "SPRING" else ORANGE


def _half_label(half: str) -> str:
    return "SPRING ↑ UP · vowel" if half == "SPRING" else "FALL ↓ DOWN · consonant"


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
def hero() -> str:
    return f"""
<style>{BASE_CSS}
.dc.hero {{ text-align:center; padding: 18px 8px 6px; }}
.dc.hero h1 {{ margin:0; font-size: clamp(30px, 7vw, 64px); font-weight:900;
   line-height:1.05; }}
.dc.hero .vs {{ font-size: clamp(18px, 4vw, 30px); color:{WHITE}; margin: 6px 0; }}
.dc.hero p {{ color:{GREY}; font-size: clamp(16px, 3.6vw, 20px); margin: 10px auto 0;
   max-width: 760px; }}
</style>
<div class="dc hero">
  <h1 class="orb glow-c">TRUE LIGHT CALENDAR</h1>
  <div class="orb vs">⟷ vs ⟷</div>
  <h1 class="orb glow-m">TODAY'S CALENDAR</h1>
  <p>Drew's True Light model, from the Nov 12 thread: the year starts in spring,
     months follow the moon, Sunday is Day 1, and January 1 is the Fall.</p>
</div>"""


# --------------------------------------------------------------------------
# Today / selected-day dual card
# --------------------------------------------------------------------------
def day_cards(y: DrewYear, d: date) -> str:
    dd = y.by_date[d]
    m = y.months[dd.month - 1]
    hc = _half_color(dd.half)
    iso_wd = d.weekday()          # 0 = Monday
    moon_pct = round(dd.illum * 100)
    venus_txt = {"MORNING": "MORNING STAR · it rises",
                 "EVENING": "EVENING STAR",
                 "INVISIBLE": "INVISIBLE · overshadowed by the sun"}[dd.venus]
    marks = "".join(f'<div class="mark orb">★ {escape(x)}</div>' for x in dd.marks)
    day_of_year_greg = (d - date(d.year, 1, 1)).days + 1
    day_of_year_drew = (d - y.start).days + 1
    return f"""
<style>{BASE_CSS}
.dc.cards {{ display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin: 8px 0 4px; }}
@media (max-width: 640px) {{ .dc.cards {{ grid-template-columns: 1fr; }} }}
.dc .card {{ background:{PANEL}; border-radius:18px; padding:18px 18px 16px; }}
.dc .card.drew {{ border:3px solid {CYAN}; box-shadow: 0 0 24px {CYAN}55; }}
.dc .card.today {{ border:3px solid {MAGENTA}; box-shadow: 0 0 24px {MAGENTA}55; }}
.dc .card .tag {{ font-size:15px; letter-spacing:.18em; color:{GREY}; }}
.dc .card .big {{ font-size: clamp(34px, 8vw, 52px); font-weight:900; line-height:1.05;
   margin: 6px 0 2px; }}
.dc .card .mid {{ font-size: 24px; font-weight:700; }}
.dc .card .row {{ font-size: 21px; margin-top:6px; }}
.dc .card .pill {{ display:inline-block; padding:3px 12px; border-radius:999px;
   font-weight:700; font-size:18px; color:{BG}; margin-top:8px; }}
.dc .mark {{ margin-top:10px; color:{BG}; background:{YELLOW}; border-radius:10px;
   padding:6px 10px; font-size:16px; font-weight:700; box-shadow:0 0 14px {YELLOW}88; }}
</style>
<div class="dc cards">
  <div class="card drew">
    <div class="tag orb">TRUE LIGHT CALENDAR</div>
    <div class="big orb glow-c">MONTH {dd.month} · DAY {dd.day}</div>
    <div class="mid">{escape(m.old_name)} · year of spring {y.label}</div>
    <div class="row">Week: <b class="glow-c">{DREW_WEEKDAYS[dd.weekday_drew - 1]}</b></div>
    <div class="row">Moon: <span style="font-size:28px">{moon_emoji(dd.moon_age)}</span>
         {moon_pct}% lit · moon day {int(dd.moon_age) + 1}</div>
    <div class="row">Venus: <b style="color:{VIOLET}">{venus_txt}</b></div>
    <div class="row">Day {day_of_year_drew} of the year</div>
    <span class="pill orb" style="background:{hc}">{_half_label(dd.half)}</span>
    {marks}
  </div>
  <div class="card today">
    <div class="tag orb">TODAY'S CALENDAR</div>
    <div class="big orb glow-m">{TODAY_WEEKDAYS[iso_wd].upper()} · {MONTHS[d.month-1].upper()} {d.day}</div>
    <div class="mid">{MONTHS_LONG[d.month-1]} {d.day}, {d.year}</div>
    <div class="row">Week: <b class="glow-m">Day {iso_wd + 1} ({TODAY_WEEKDAYS[iso_wd]})</b>
         · Monday = Day 1</div>
    <div class="row">Month {d.month} of 12 · fixed length, not the moon</div>
    <div class="row">New Year: <b>January 1</b></div>
    <div class="row">Day {day_of_year_greg} of the year</div>
  </div>
</div>"""


# --------------------------------------------------------------------------
# Big comparison stats
# --------------------------------------------------------------------------
def compare_strip(y: DrewYear) -> str:
    n_days = (y.end - y.start).days + 1
    greg_days = 366 if (y.label % 4 == 0 and (y.label % 100 != 0 or y.label % 400 == 0)) else 365
    rows = [
        ("NEW YEAR", _fmt(y.start) + " · spring", "January 1 · winter"),
        ("MONTHS", f"{len(y.months)} moons", "12 fixed"),
        ("YEAR LENGTH", f"{n_days} days", f"{greg_days} days"),
        ("WEEK STARTS", "SUNDAY = Day 1", "MONDAY = Day 1"),
        ("MONTH STARTS", "new moon", "the 1st"),
        ("JANUARY 1", "THE FALL · the end", "celebrated as new"),
    ]
    body = "".join(
        f'<div class="lab orb">{a}</div><div class="c">{b}</div><div class="m">{c}</div>'
        for a, b, c in rows)
    return f"""
<style>{BASE_CSS}
.dc.cmp {{ display:grid; grid-template-columns: 1.1fr 1.3fr 1.3fr; gap:8px 12px;
   background:{PANEL}; border-radius:18px; padding:16px; border:2px solid #2a2f5a;
   align-items:center; margin: 10px 0; }}
.dc.cmp .h {{ font-size:15px; letter-spacing:.14em; }}
.dc.cmp .lab {{ font-size:14px; color:{GREY}; letter-spacing:.1em; }}
.dc.cmp .c {{ font-size:21px; font-weight:700; color:{CYAN}; }}
.dc.cmp .m {{ font-size:21px; font-weight:700; color:{MAGENTA}; }}
@media (max-width: 640px) {{ .dc.cmp .c, .dc.cmp .m {{ font-size:18px; }}
   .dc.cmp .lab {{ font-size:12px; }} }}
</style>
<div class="dc cmp">
  <div></div><div class="h orb glow-c">TRUE LIGHT</div><div class="h orb glow-m">TODAY</div>
  {body}
</div>"""


# --------------------------------------------------------------------------
# Month grids: every cell = Drew day (big) + today's date (small)
# --------------------------------------------------------------------------
def month_grids(y: DrewYear, selected: date | None = None) -> str:
    css = f"""
<style>{BASE_CSS}
.dc.months {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
   gap:16px; }}
.dc .mon {{ background:{PANEL}; border-radius:16px; padding:12px; border:2px solid #23284d; }}
.dc .mon .top {{ display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; }}
.dc .mon .num {{ font-size:34px; font-weight:900; }}
.dc .mon .nm {{ font-size:22px; font-weight:700; }}
.dc .mon .half {{ font-size:13px; font-weight:700; color:{BG}; padding:2px 9px;
   border-radius:999px; }}
.dc .mon .range {{ color:{MAGENTA}; font-size:18px; font-weight:700; margin:2px 0 8px; }}
.dc .grid {{ display:grid; grid-template-columns: repeat(7, 1fr); gap:4px; }}
.dc .wd {{ text-align:center; font-size:12px; color:{GREY}; font-weight:700; }}
.dc .wd.sun {{ color:{CYAN}; }}
.dc .cell {{ position:relative; border-radius:9px; min-height:52px; padding:3px 2px;
   text-align:center; border:1px solid #1d2142; }}
.dc .cell .dn {{ font-family:'Orbitron',sans-serif; font-size:19px; font-weight:900;
   color:{CYAN}; line-height:1.1; }}
.dc .cell .gd {{ font-size:13px; font-weight:700; color:{MAGENTA}; line-height:1.1; }}
.dc .cell .mo {{ font-size:12px; line-height:1; }}
.dc .cell.sun {{ border:1px solid {CYAN}99; }}
.dc .cell.mk {{ border:2px solid {YELLOW}; box-shadow:0 0 10px {YELLOW}aa; }}
.dc .cell.sel {{ outline:3px solid {WHITE}; outline-offset:1px; }}
.dc .cell.jan1 {{ border:2px solid {ORANGE}; box-shadow:0 0 12px {ORANGE}; }}
.dc .marks {{ margin-top:8px; font-size:16px; line-height:1.35; }}
.dc .marks b {{ color:{YELLOW}; }}
</style>"""
    blocks = []
    for m in y.months:
        hc = _half_color(m.half)
        head = "".join(
            f'<div class="wd{" sun" if i == 0 else ""}">{w}</div>'
            for i, w in enumerate(["D1 Su", "D2 Mo", "D3 Tu", "D4 We",
                                   "D5 Th", "D6 Fr", "D7 Sa"]))
        cells = []
        lead = m.days[0].weekday_drew - 1
        cells += ['<div></div>'] * lead
        marks_txt = []
        for dd in m.days:
            a = 0.04 + 0.34 * dd.illum
            bg = f"rgba(110,130,255,{a:.2f})" if dd.illum > 0.02 else "#000"
            cls = ["cell"]
            if dd.weekday_drew == 1:
                cls.append("sun")
            if dd.marks:
                cls.append("mk")
                marks_txt.append(
                    f'<b>Day {dd.day}</b> ({MONTHS[dd.greg.month-1]} {dd.greg.day}): '
                    + " · ".join(escape(x) for x in dd.marks))
            if dd.greg.month == 1 and dd.greg.day == 1:
                cls.append("jan1")
            if selected and dd.greg == selected:
                cls.append("sel")
            gd = (f"{MONTHS[dd.greg.month-1]} {dd.greg.day}"
                  if dd.greg.day == 1 or dd.day == 1 else str(dd.greg.day))
            tip = (f"True Light M{dd.month} D{dd.day} = {_fmt(dd.greg)} · "
                   f"moon {round(dd.illum*100)}% · Venus {dd.venus.lower()}")
            cells.append(
                f'<div class="{" ".join(cls)}" style="background:{bg}" title="{escape(tip)}">'
                f'<div class="dn" style="text-shadow:0 0 6px #000,0 0 2px #000">{dd.day}</div>'
                f'<div class="gd" style="text-shadow:0 0 4px #000">{gd}</div>'
                f'<div class="mo">{moon_emoji(dd.moon_age) if dd.day in (1,) or (m.full_moon == dd.greg) else ""}</div>'
                f'</div>')
        rng = f"{MONTHS[m.start.month-1]} {m.start.day} – {MONTHS[m.end.month-1]} {m.end.day}, {m.end.year}"
        blocks.append(f"""
<div class="mon" style="border-color:{hc}66">
  <div class="top">
    <span class="num orb glow-c">M{m.number}</span>
    <span class="nm">{escape(m.old_name)}</span>
    <span class="half orb" style="background:{hc}">{"SPRING ↑" if m.half == "SPRING" else "FALL ↓"}</span>
  </div>
  <div class="range">Today's calendar: {rng} · {m.length} days</div>
  <div class="grid">{head}{"".join(cells)}</div>
  <div class="marks">{"<br>".join(marks_txt)}</div>
</div>""")
    legend = f"""
<div class="dc" style="font-size:17px;margin:4px 0 12px;line-height:1.5">
  <span class="orb glow-c" style="font-weight:900">BIG NUMBER</span> = True Light day ·
  <span class="glow-m" style="font-weight:700">small number</span> = today's date ·
  brighter blue cell = fuller moon ·
  <span style="color:{CYAN}">blue edge</span> = Sunday (Day 1) ·
  <span class="glow-y">yellow</span> = marked day ·
  <span style="color:{ORANGE}">orange</span> = Jan 1, the Fall
</div>"""
    return css + legend + f'<div class="dc months">{"".join(blocks)}</div>'


# --------------------------------------------------------------------------
# Year wheel: inner ring = Drew's moons, outer ring = today's months
# --------------------------------------------------------------------------
def _arc(cx, cy, r1, r2, a0, a1) -> str:
    """Annular sector path, angles in degrees, 0 = top, clockwise."""
    def pt(r, a):
        t = math.radians(a - 90)
        return cx + r * math.cos(t), cy + r * math.sin(t)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    x1, y1 = pt(r2, a0); x2, y2 = pt(r2, a1)
    x3, y3 = pt(r1, a1); x4, y4 = pt(r1, a0)
    return (f"M{x1:.1f},{y1:.1f} A{r2},{r2} 0 {large} 1 {x2:.1f},{y2:.1f} "
            f"L{x3:.1f},{y3:.1f} A{r1},{r1} 0 {large} 0 {x4:.1f},{y4:.1f} Z")


def year_wheel(y: DrewYear, selected: date | None = None) -> str:
    W = 1000
    cx = cy = W / 2
    total = (y.end - y.start).days + 1

    def ang(d: date) -> float:
        return (d - y.start).days / total * 360

    parts = []

    def pt(r, a):
        t = math.radians(a - 90)
        return cx + r * math.cos(t), cy + r * math.sin(t)

    # Outer ring: today's (Gregorian) months
    d = date(y.start.year, y.start.month, 1)
    while d <= y.end:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        s, e = max(d, y.start), min(nxt - timedelta(days=1), y.end)
        a0, a1 = ang(s), ang(e) + 360 / total
        shade = MAGENTA if d.month % 2 else "#b0179a"
        parts.append(f'<path d="{_arc(cx, cy, 400, 470, a0, a1)}" fill="{shade}" '
                     f'stroke="{BG}" stroke-width="3"/>')
        if a1 - a0 > 12:
            x, yy = pt(435, (a0 + a1) / 2)
            parts.append(f'<text x="{x:.0f}" y="{yy:.0f}" class="ml">{MONTHS[d.month-1].upper()}</text>')
        d = nxt

    # Middle ring: Drew's months (moons)
    for m in y.months:
        a0, a1 = ang(m.start), ang(m.end) + 360 / total
        col = CYAN if m.number % 2 else "#00a7b3"
        parts.append(f'<path d="{_arc(cx, cy, 290, 390, a0, a1)}" fill="{col}" '
                     f'stroke="{BG}" stroke-width="3"/>')
        x, yy = pt(352, (a0 + a1) / 2)
        parts.append(f'<text x="{x:.0f}" y="{yy:.0f}" class="dl">M{m.number}</text>')
        x, yy = pt(318, (a0 + a1) / 2)
        if m.full_moon:
            fx, fy = pt(318, ang(m.full_moon) + 0.5)
            parts.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="11" fill="{WHITE}" '
                         f'style="filter:drop-shadow(0 0 6px #fff)"/>')

    # Spring/fall half ring
    if len(y.months) >= 7:
        mid = ang(y.months[6].start)
        parts.append(f'<path d="{_arc(cx, cy, 255, 282, 0, mid)}" fill="{LIME}"/>')
        parts.append(f'<path d="{_arc(cx, cy, 255, 282, mid, 359.99)}" fill="{ORANGE}"/>')

    # Venus ring
    days = [dd for m in y.months for dd in m.days]
    vcol = {"MORNING": VIOLET, "EVENING": "#5b49b8", "INVISIBLE": "#1a1a2e"}
    run_start = days[0]
    for prev, cur in zip(days, days[1:] + [None]):
        if cur is None or cur.venus != run_start.venus:
            a0, a1 = ang(run_start.greg), ang(prev.greg) + 360 / total
            parts.append(f'<path d="{_arc(cx, cy, 170, 195, a0, a1)}" '
                         f'fill="{vcol[run_start.venus]}"/>')
            if cur is not None:
                run_start = cur

    # Marker needles
    def needle(d: date, color: str, label: str, r_text: float = 518, width=5):
        a = ang(d)
        x1, y1 = pt(160, a)
        x2, y2 = pt(478, a)
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                     f'stroke="{color}" stroke-width="{width}" '
                     f'style="filter:drop-shadow(0 0 6px {color})"/>')
        tx, ty = pt(r_text, a)
        anchor = "start" if 2 < a < 178 else ("end" if 182 < a < 358 else "middle")
        parts.append(f'<text x="{tx:.0f}" y="{ty:.0f}" fill="{color}" class="nl" '
                     f'text-anchor="{anchor}">{label}</text>')

    needle(y.start, LIME, "SPRING NEW YEAR")
    for yr in (y.start.year, y.start.year + 1):
        j1 = date(yr, 1, 1)
        if y.start <= j1 <= y.end:
            needle(j1, ORANGE, "JAN 1 = FALL")
    if len(y.months) >= 7:
        needle(y.months[6].start, ORANGE, "FALL NEW YEAR", width=3)
    if selected and y.start <= selected <= y.end:
        needle(selected, WHITE, "YOU ARE HERE", width=4)

    center = f"""
<text x="{cx}" y="{cy-30}" class="c1">TRUE LIGHT YEAR</text>
<text x="{cx}" y="{cy+22}" class="c2">{y.label}–{str(y.label+1)[-2:]}</text>
<text x="{cx}" y="{cy+62}" class="c3">{len(y.months)} MOONS · {total} DAYS</text>
<text x="{cx}" y="{cy-85}" class="hl" fill="{LIME}">▲ SPRING</text>
<text x="{cx}" y="{cy+105}" class="hl" fill="{ORANGE}">▼ FALL</text>"""

    svg = f"""
<svg viewBox="-190 -60 {W+380} {W+120}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;max-width:820px;display:block;margin:0 auto">
<style>
 text {{ font-family:'Orbitron','Rajdhani',sans-serif; text-anchor:middle;
        dominant-baseline:middle; font-weight:900; }}
 .ml {{ fill:{WHITE}; font-size:26px; }}
 .dl {{ fill:{BG}; font-size:32px; }}
 .hl {{ font-size:26px; }}
 .nl {{ font-size:32px; }}
 .c1 {{ fill:{CYAN}; font-size:44px; }}
 .c2 {{ fill:{WHITE}; font-size:52px; }}
 .c3 {{ fill:{GREY}; font-size:22px; }}
</style>
{"".join(parts)}{center}
</svg>"""
    legend = f"""
<div class="dc" style="display:flex;flex-wrap:wrap;gap:10px 18px;justify-content:center;
     font-size:18px;font-weight:700;margin-top:8px">
  <span><span style="color:{MAGENTA}">■</span> Outer: today's months</span>
  <span><span style="color:{CYAN}">■</span> Middle: True Light moons (M1–M{len(y.months)})</span>
  <span><span style="color:{WHITE}">●</span> full moon</span>
  <span><span style="color:{LIME}">■</span>/<span style="color:{ORANGE}">■</span> spring up / fall down</span>
  <span><span style="color:{VIOLET}">■</span> Venus morning star ·
        <span style="color:#5b49b8">■</span> evening · <span style="color:#555">■</span> invisible</span>
</div>"""
    return f"<style>{BASE_CSS}</style>" + svg + legend


# --------------------------------------------------------------------------
# Key events list, both calendars side by side
# --------------------------------------------------------------------------
def events_table(y: DrewYear) -> str:
    rows = []
    for d, title, desc in y.events:
        dd = y.by_date[d]
        rows.append(f"""
<div class="ev">
  <div class="t orb glow-y">{escape(title)}</div>
  <div class="both"><span class="glow-c">M{dd.month} · Day {dd.day}</span>
     <span class="eq">=</span>
     <span class="glow-m">{TODAY_WEEKDAYS[d.weekday()]} {_fmt(d)}</span></div>
  <div class="ds">{escape(desc)}</div>
</div>""")
    return f"""
<style>{BASE_CSS}
.dc.evs {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(300px,1fr)); gap:12px; }}
.dc .ev {{ background:{PANEL}; border-left:6px solid {YELLOW}; border-radius:12px; padding:12px 14px; }}
.dc .ev .t {{ font-size:19px; font-weight:900; }}
.dc .ev .both {{ font-size:22px; font-weight:700; margin:4px 0; }}
.dc .ev .eq {{ color:{GREY}; margin: 0 6px; }}
.dc .ev .ds {{ font-size:17px; color:#c9cdf0; }}
</style>
<div class="dc evs">{"".join(rows)}</div>"""


# --------------------------------------------------------------------------
# The key: what each rule in the thread became in the app
# --------------------------------------------------------------------------
THREAD_RULES = [
    ("New year is always spring.", "Month 1 begins at the first new moon of spring."),
    ("I feel like the moon ... an alloted and measured amount.",
     "Every month is one moon: new moon to new moon, 29 or 30 days."),
    ("True spring comes after two 7 day cycles.",
     "Month 1, Day 15 = TRUE SPRING (Day 14 = PASS OVER)."),
    ("Two New Years: spring (Month 1) and the 7th new moon.",
     "Month 7, Day 1 = FALL NEW YEAR. Months 1–6 = spring/up, 7–13 = fall/down."),
    ("We celebrate it in Jan ... what we are celebrating is the end.",
     "January 1 is marked THE FALL / THE END in orange."),
    ("So Jan is equivalent to Fall — Yes. The fall. Gravity. Lucifer.",
     "January 1 sits in the FALL half of the True Light year."),
    ("It's an inverted Passover. It's taking our joy.",
     "Jan 1 card carries the inverted-Passover note."),
    ("Sundays is actually the first day of the week, not Monday.",
     "True Light weeks: Sunday = Day 1. Today's calendar: Monday = Day 1."),
    ("Venus ... it rises. But it's overshadowed by the sun. It's there but invisible.",
     "Venus track: MORNING STAR (rises) / EVENING / INVISIBLE near the sun."),
    ("When one thing becomes visible another becomes invisible.",
     "Venus switch days are marked on the calendar."),
    ("Black to black ... Black Friday ... accumulating deadly sins.",
     "Black Friday is marked."),
    ("Jesu was a mocking term. April fools.",
     "April 1 is marked APRIL FOOLS — the spring new year that got mocked."),
    ("Supposed to be fall and spring. Down and up. Spring = vowel, consonants = fall.",
     "Spring half = UP / vowel. Fall half = DOWN / consonant."),
]


def thread_key() -> str:
    rows = "".join(
        f'<div class="q">“{escape(a)}”</div><div class="a">→ {escape(b)}</div>'
        for a, b in THREAD_RULES)
    return f"""
<style>{BASE_CSS}
.dc.key {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px 16px;
   background:{PANEL}; border-radius:16px; padding:16px; border:2px solid {CYAN}55; }}
@media (max-width: 640px) {{ .dc.key {{ grid-template-columns: 1fr; }}
   .dc.key .a {{ margin-bottom:10px; }} }}
.dc.key .q {{ font-size:19px; font-style:italic; color:{WHITE}; }}
.dc.key .a {{ font-size:19px; font-weight:700; color:{CYAN}; }}
</style>
<div class="dc key">{rows}</div>"""

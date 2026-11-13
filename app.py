"""
TRUE LIGHT CALENDAR - one-file Streamlit app.
Drew's True Light model (spring new year, moon months, Sunday = Day 1,
Jan 1 = the Fall) side by side with today's calendar.

Everything is in this one file. requirements.txt only needs: streamlit>=1.36
"""


from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

SYNODIC = 29.530588861
J2000 = 2451545.0
DELTA_T_DAYS = 69.0 / 86400.0  # TT -> UT, close enough for this era


# --------------------------------------------------------------------------
# Julian day helpers
# --------------------------------------------------------------------------
def jd_to_datetime_utc(jde: float) -> datetime:
    """Julian Ephemeris Day -> naive UTC datetime."""
    return datetime(2000, 1, 1, 12) + timedelta(days=jde - J2000 - DELTA_T_DAYS)


def datetime_to_jd(dt: datetime) -> float:
    return J2000 + (dt - datetime(2000, 1, 1, 12)).total_seconds() / 86400.0


def _sin(deg: float) -> float:
    return math.sin(math.radians(deg))


def _cos(deg: float) -> float:
    return math.cos(math.radians(deg))


# --------------------------------------------------------------------------
# Moon phases (Meeus ch. 49)
# --------------------------------------------------------------------------
def _moon_phase_jde(k: float) -> float:
    """k integer = new moon, k + 0.5 = full moon."""
    T = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T**2
           - 0.000000150 * T**3 + 0.00000000073 * T**4)
    E = 1 - 0.002516 * T - 0.0000074 * T**2
    M = 2.5534 + 29.10535670 * k - 0.0000014 * T**2 - 0.00000011 * T**3
    Mp = (201.5643 + 385.81693528 * k + 0.0107582 * T**2
          + 0.00001238 * T**3 - 0.000000058 * T**4)
    F = (160.7108 + 390.67050284 * k - 0.0016118 * T**2
         - 0.00000227 * T**3 + 0.000000011 * T**4)
    Om = 124.7746 - 1.56375588 * k + 0.0020672 * T**2 + 0.00000215 * T**3

    full = abs((k % 1) - 0.5) < 1e-9
    if not full:
        c = [-0.40720, 0.17241, 0.01608, 0.01039, 0.00739, -0.00514, 0.00208]
    else:
        c = [-0.40614, 0.17302, 0.01614, 0.01043, 0.00734, -0.00515, 0.00209]

    corr = (c[0] * _sin(Mp) + c[1] * E * _sin(M) + c[2] * _sin(2 * Mp)
            + c[3] * _sin(2 * F) + c[4] * E * _sin(Mp - M)
            + c[5] * E * _sin(Mp + M) + c[6] * E * E * _sin(2 * M)
            - 0.00111 * _sin(Mp - 2 * F) - 0.00057 * _sin(Mp + 2 * F)
            + 0.00056 * E * _sin(2 * Mp + M) - 0.00042 * _sin(3 * Mp)
            + 0.00042 * E * _sin(M + 2 * F) + 0.00038 * E * _sin(M - 2 * F)
            - 0.00024 * E * _sin(2 * Mp - M) - 0.00017 * _sin(Om)
            - 0.00007 * _sin(Mp + 2 * M) + 0.00004 * _sin(2 * Mp - 2 * F)
            + 0.00004 * _sin(3 * M) + 0.00003 * _sin(Mp + M - 2 * F)
            + 0.00003 * _sin(2 * Mp + 2 * F) - 0.00003 * _sin(Mp + M + 2 * F)
            + 0.00003 * _sin(Mp - M + 2 * F) - 0.00002 * _sin(Mp - M - 2 * F)
            - 0.00002 * _sin(3 * Mp + M) + 0.00002 * _sin(4 * Mp))

    A = [299.77 + 0.107408 * k - 0.009173 * T**2, 251.88 + 0.016321 * k,
         251.83 + 26.651886 * k, 349.42 + 36.412478 * k, 84.66 + 18.206239 * k,
         141.74 + 53.303771 * k, 207.14 + 2.453732 * k, 154.84 + 7.306860 * k,
         34.52 + 27.261239 * k, 207.19 + 0.121824 * k, 291.34 + 1.844379 * k,
         161.72 + 24.198154 * k, 239.56 + 25.513099 * k, 331.55 + 3.592518 * k]
    Ac = [325, 165, 164, 126, 110, 62, 60, 56, 47, 42, 40, 37, 35, 23]
    add = sum(a * 1e-6 * _sin(x) for a, x in zip(Ac, A))
    return jde + corr + add


def _k_near(dt: datetime) -> int:
    years = (dt - datetime(2000, 1, 6)).days / 365.2425
    return int(math.floor(years * 12.3685))


def new_moons_between(start: datetime, end: datetime) -> list[datetime]:
    k = _k_near(start) - 2
    out = []
    while True:
        t = jd_to_datetime_utc(_moon_phase_jde(k))
        if t > end:
            break
        if t >= start:
            out.append(t)
        k += 1
    return out


def full_moons_between(start: datetime, end: datetime) -> list[datetime]:
    k = _k_near(start) - 2
    out = []
    while True:
        t = jd_to_datetime_utc(_moon_phase_jde(k + 0.5))
        if t > end:
            break
        if t >= start:
            out.append(t)
        k += 1
    return out


# --------------------------------------------------------------------------
# Equinoxes & solstices (Meeus ch. 27, valid 1000-3000 AD)
# --------------------------------------------------------------------------
_SEASON_TERMS = [
    (485, 324.96, 1934.136), (203, 337.23, 32964.467), (199, 342.08, 20.186),
    (182, 27.85, 445267.112), (156, 73.14, 45036.886), (136, 171.52, 22518.443),
    (77, 222.54, 65928.934), (74, 296.72, 3034.906), (70, 243.58, 9037.513),
    (58, 119.81, 33718.147), (52, 297.17, 150.678), (50, 21.02, 2281.226),
    (45, 247.54, 29929.562), (44, 325.15, 31555.956), (29, 60.93, 4443.417),
    (18, 155.12, 67555.328), (17, 288.79, 4562.452), (16, 198.04, 62894.029),
    (14, 199.76, 31436.921), (12, 95.39, 14577.848), (12, 287.11, 31931.756),
    (12, 320.81, 34777.259), (9, 227.73, 1222.114), (8, 15.45, 16859.074),
]


def season_utc(year: int, which: str) -> datetime:
    """which: 'march', 'june', 'september', 'december'."""
    Y = (year - 2000) / 1000.0
    base = {
        "march": (2451623.80984, 365242.37404, 0.05169, -0.00411, -0.00057),
        "june": (2451716.56767, 365241.62603, 0.00325, 0.00888, -0.00030),
        "september": (2451810.21715, 365242.01767, -0.11575, 0.00337, 0.00078),
        "december": (2451900.05952, 365242.74049, -0.06223, -0.00823, 0.00032),
    }[which]
    jde0 = base[0] + base[1] * Y + base[2] * Y**2 + base[3] * Y**3 + base[4] * Y**4
    T = (jde0 - J2000) / 36525.0
    W = 35999.373 * T - 2.47
    dl = 1 + 0.0334 * _cos(W) + 0.0007 * _cos(2 * W)
    S = sum(a * _cos(b + c * T) for a, b, c in _SEASON_TERMS)
    return jd_to_datetime_utc(jde0 + 0.00001 * S / dl)


# --------------------------------------------------------------------------
# Venus: morning star / evening star / invisible  (JPL approx. elements)
# --------------------------------------------------------------------------
_ELEMENTS = {
    # a, e, I, L, long.peri, long.node  (+ rates per century)
    "venus": ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
              (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    "earth": ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
              (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
}


def _helio_xyz(planet: str, T: float) -> tuple[float, float, float]:
    e0, rate = _ELEMENTS[planet]
    a, e, I, L, wbar, node = (x + r * T for x, r in zip(e0, rate))
    w = wbar - node
    M = (L - wbar) % 360
    Mr = math.radians(M)
    E = Mr + e * math.sin(Mr)
    for _ in range(8):
        E = E - (E - e * math.sin(E) - Mr) / (1 - e * math.cos(E))
    xp = a * (math.cos(E) - e)
    yp = a * math.sqrt(1 - e * e) * math.sin(E)
    cw, sw = _cos(w), _sin(w)
    cO, sO = _cos(node), _sin(node)
    cI, sI = _cos(I), _sin(I)
    x = (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp
    y = (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp
    z = (sw * sI) * xp + (cw * sI) * yp
    return x, y, z


def venus_elongation(dt: datetime) -> float:
    """Signed elongation of Venus from the Sun in degrees.
    Positive = east of Sun (EVENING star), negative = west (MORNING star, rises
    before the Sun)."""
    T = (datetime_to_jd(dt) - J2000) / 36525.0
    vx, vy, vz = _helio_xyz("venus", T)
    ex, ey, ez = _helio_xyz("earth", T)
    gx, gy, gz = vx - ex, vy - ey, vz - ez          # Earth -> Venus
    sx, sy, sz = -ex, -ey, -ez                      # Earth -> Sun
    lam_v = math.degrees(math.atan2(gy, gx))
    lam_s = math.degrees(math.atan2(sy, sx))
    d = (lam_v - lam_s + 180) % 360 - 180
    dot = gx * sx + gy * sy + gz * sz
    ang = math.degrees(math.acos(max(-1, min(1, dot / (
        math.sqrt(gx*gx + gy*gy + gz*gz) * math.sqrt(sx*sx + sy*sy + sz*sz))))))
    return ang if d >= 0 else -ang


def venus_state(elong: float, hidden_below: float = 10.0) -> str:
    if abs(elong) < hidden_below:
        return "INVISIBLE"          # "overshadowed by the sun ... there but invisible"
    return "MORNING" if elong < 0 else "EVENING"


# --------------------------------------------------------------------------
# Drew's calendar
# --------------------------------------------------------------------------
DREW_WEEKDAYS = ["Day 1 (Sun)", "Day 2 (Mon)", "Day 3 (Tue)", "Day 4 (Wed)",
                 "Day 5 (Thu)", "Day 6 (Fri)", "Day 7 (Sat)"]
TODAY_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # ISO: Monday first

# Old names for the month numbers (Hebrew counting from the spring month)
OLD_MONTH_NAMES = {1: "Nisan", 2: "Iyar", 3: "Sivan", 4: "Tammuz", 5: "Av",
                   6: "Elul", 7: "Tishrei", 8: "Cheshvan", 9: "Kislev",
                   10: "Tevet", 11: "Shevat", 12: "Adar", 13: "Adar II"}


@dataclass
class DrewDay:
    greg: date
    month: int                  # 1..13
    day: int                    # 1..30
    weekday_drew: int           # 1 = Sunday
    moon_age: float             # days since new moon (at local noon)
    illum: float                # 0..1
    half: str                   # "SPRING" (up / vowel) or "FALL" (down / consonant)
    venus: str                  # MORNING / EVENING / INVISIBLE
    venus_elong: float
    marks: list[str] = field(default_factory=list)


@dataclass
class DrewMonth:
    number: int
    old_name: str
    start: date
    end: date
    length: int
    new_moon_utc: datetime
    full_moon: date | None
    half: str
    days: list[DrewDay] = field(default_factory=list)


@dataclass
class DrewYear:
    label: int                  # Gregorian year in which this Drew year begins
    start: date
    end: date
    equinox: date
    months: list[DrewMonth]
    by_date: dict[date, DrewDay]
    events: list[tuple[date, str, str]]   # (date, short title, description)


def _local(dt_utc: datetime, tz_hours: float) -> datetime:
    return dt_utc + timedelta(hours=tz_hours)


def drew_year(spring_year: int, tz_hours: float = -5.0,
              start_rule: str = "new", anchor: str = "after") -> DrewYear:
    """Build the Drew year that begins in the spring of `spring_year`.

    start_rule: 'new'      -> Month starts on the day of the dark new moon
                'crescent' -> Month starts the day after (first sliver seen)
    anchor:     'after'    -> Month 1 = first new moon ON/AFTER the spring
                              equinox (strict "new year is always spring")
                'nearest'  -> Month 1 = the new moon NEAREST the equinox
    """
    shift = 1 if start_rule == "crescent" else 0

    eq = _local(season_utc(spring_year, "march"), tz_hours)
    eq_next = _local(season_utc(spring_year + 1, "march"), tz_hours)

    def month_starts_after(eqx: datetime) -> list[tuple[date, datetime]]:
        nms = new_moons_between(eqx - timedelta(days=40), eqx + timedelta(days=440))
        res = []
        for nm in nms:
            loc = _local(nm, tz_hours)
            res.append((loc.date() + timedelta(days=shift), nm))
        return res

    starts_all = month_starts_after(eq - timedelta(days=0))
    # first new moon on/after the spring equinox
    def pick(eqx: datetime) -> int:
        if anchor == "nearest":
            return min(range(len(starts_all)), key=lambda i: abs(
                (_local(starts_all[i][1], tz_hours) - eqx).total_seconds()))
        return next(i for i, (_, nm) in enumerate(starts_all)
                    if _local(nm, tz_hours) >= eqx)

    first_idx = pick(eq)
    next_idx = pick(eq_next)
    starts = starts_all[first_idx:next_idx + 1]

    fulls = [(_local(f, tz_hours)).date() for f in full_moons_between(
        eq - timedelta(days=10), eq + timedelta(days=430))]

    # all new moons for moon age calculation
    nm_list = [_local(n, tz_hours) for n in
               new_moons_between(eq - timedelta(days=60), eq + timedelta(days=450))]

    months: list[DrewMonth] = []
    by_date: dict[date, DrewDay] = {}
    n_months = len(starts) - 1
    for i in range(n_months):
        s, nm = starts[i]
        e = starts[i + 1][0] - timedelta(days=1)
        num = i + 1
        half = "SPRING" if num <= 6 else "FALL"
        old = OLD_MONTH_NAMES[num] if not (n_months == 12 and num == 12) else "Adar"
        if n_months == 13 and num == 12:
            old = "Adar I"
        fm = next((f for f in fulls if s <= f <= e), None)
        m = DrewMonth(num, old, s, e, (e - s).days + 1, nm, fm, half)
        d = s
        dn = 1
        while d <= e:
            noon = datetime(d.year, d.month, d.day, 12)
            prev_nm = max(x for x in nm_list if x <= noon)
            age = (noon - prev_nm).total_seconds() / 86400.0
            illum = (1 - math.cos(2 * math.pi * age / SYNODIC)) / 2
            el = venus_elongation(noon - timedelta(hours=tz_hours))
            wd = (d.weekday() + 1) % 7 + 1      # Sunday -> 1
            day = DrewDay(d, num, dn, wd, age, illum, half,
                          venus_state(el), el)
            m.days.append(day)
            by_date[d] = day
            d += timedelta(days=1)
            dn += 1
        months.append(m)

    events: list[tuple[date, str, str]] = []

    def add(dt: date, title: str, desc: str):
        if dt in by_date:
            by_date[dt].marks.append(title)
            events.append((dt, title, desc))

    m1 = months[0]
    add(m1.start, "SPRING NEW YEAR",
        "Month 1, Day 1. 'New year is always spring.'")
    add(m1.start + timedelta(days=13), "PASS OVER",
        "Month 1, Day 14. 'The leaf of an apple is Passover.'")
    add(m1.start + timedelta(days=14), "TRUE SPRING",
        "Month 1, Day 15. 'True spring comes after two 7 day cycles.'")
    if len(months) >= 7:
        add(months[6].start, "FALL NEW YEAR",
            "Month 7, Day 1 - the 7th new moon. The second new year.")
    for eqd in (eq.date(), eq_next.date()):
        add(eqd, "SPRING EQUINOX", "Sun crosses into spring (astronomical).")
    for yy in (spring_year, spring_year + 1):
        add(date(yy, 1, 1), "THE FALL / THE END",
            "Jan 1. 'We celebrate it in Jan... What we are celebrating is the end.' "
            "'So Jan is equivalent to Fall' - 'Yes. The fall. Gravity. Lucifer.' "
            "'It's an inverted Passover. It's taking our joy.'")
        add(date(yy, 4, 1), "APRIL FOOLS",
            "Apr 1 - the old spring new year, mocked once the count moved to Jan 1. "
            "'Jesu was a mocking term. April fools.'")
        # Black Friday: day after 4th Thursday of November
        nov1 = date(yy, 11, 1)
        first_thu = nov1 + timedelta(days=(3 - nov1.weekday()) % 7)
        add(first_thu + timedelta(days=22), "BLACK FRIDAY",
            "'Black to black. Account back in black. Fade to black. Black Friday. "
            "Accumulating deadly sins.'")
        for which, title in (("june", "SUMMER SOLSTICE"),
                             ("september", "FALL EQUINOX"),
                             ("december", "WINTER SOLSTICE")):
            add(_local(season_utc(yy, which), tz_hours).date(), title,
                "Astronomical season marker.")

    # Venus: mark the day it switches state
    all_days = [d for m in months for d in m.days]
    for prev, cur in zip(all_days, all_days[1:]):
        if prev.venus != cur.venus:
            if cur.venus == "MORNING":
                add(cur.greg, "VENUS RISES",
                    "Venus reappears as the morning star - 'And it rises.' (Lucifer)")
            elif cur.venus == "INVISIBLE":
                add(cur.greg, "VENUS INVISIBLE",
                    "Lost in the sun's glare - 'Overshadowed by the sun. It's there "
                    "but invisible. The invisible god.'")
            elif cur.venus == "EVENING":
                add(cur.greg, "VENUS EVENING STAR",
                    "Venus reappears after sunset. 'When one thing becomes visible "
                    "another becomes invisible.'")

    events.sort(key=lambda x: x[0])
    return DrewYear(spring_year, months[0].start, months[-1].end, eq.date(),
                    months, by_date, events)


def drew_year_for(d: date, tz_hours: float = -5.0, start_rule: str = "new",
                  anchor: str = "after") -> DrewYear:
    """Return the Drew year that contains date d."""
    y = drew_year(d.year, tz_hours, start_rule, anchor)
    if d < y.start:
        y = drew_year(d.year - 1, tz_hours, start_rule, anchor)
    return y


def moon_emoji(age: float) -> str:
    f = (age % SYNODIC) / SYNODIC
    icons = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
    return icons[int((f * 8) + 0.5) % 8]


# ==========================================================================
# VISUALS
# ==========================================================================



import math
from datetime import date, timedelta
from html import escape


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


# ==========================================================================
# THE APP
# ==========================================================================


from datetime import date, datetime, timedelta, timezone

import streamlit as st


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

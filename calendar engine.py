"""
calendar_engine.py
------------------
All the date math for the app, in plain Python (no extra libraries).

It builds "Drew's calendar" - the model from Erin & Drew's Nov 12 2026 thread -
and lines it up day-by-day against today's (Gregorian) calendar.

DREW'S RULES (from the thread)
  * "New year is always spring."        -> Year starts at the first new moon
                                            on/after the spring equinox.
  * Months follow the moon               -> each month = new moon to new moon
    ("I feel like the moon ...             (an "allotted and measured amount").
     an alloted and measured amount")
  * "True spring comes after two         -> Day 15 of Month 1 = TRUE SPRING
     7 day cycles"                          (Day 14 = Passover / pass over).
  * Two New Years: Month 1 (spring) and  -> Month 7 = the 7th new moon =
    the 7th new moon (fall)                 Fall New Year.
  * "We celebrate it in Jan ... What we  -> Jan 1 is marked THE FALL / THE END /
     are celebrating is the end"            INVERTED PASSOVER.
    "So Jan is equivalent to Fall" "Yes"
  * "Sunday is actually the first day"   -> Drew weeks run Sunday = Day 1.
  * Venus "rises", "overshadowed by the  -> Venus track: morning star (rising) /
     sun ... there but invisible"           evening star / invisible (near sun).
  * "Black to black ... Black Friday"    -> Black Friday marked.
  * "Jesu was a mocking term. April fools" -> April 1 marked APRIL FOOLS.
  * "Supposed to be fall and spring,     -> Months 1-6 = SPRING / UP (vowel),
     down and up" "Spring = vowel,          months 7-12/13 = FALL / DOWN
     consonants = fall"                     (consonant).

Astronomy: Jean Meeus, "Astronomical Algorithms" (moon phases ch.49,
equinoxes/solstices ch.27) and JPL approximate planetary elements for Venus.
Times are accurate to minutes for moon phases and seasons; Venus to a few days.
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

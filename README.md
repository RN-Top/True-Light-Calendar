# True Light Calendar

A neon, big-text Streamlit app that visualizes Drew's True Light calendar model from the
Nov 12, 2026 thread with Drew, and lines it up day-by-day against today's
(Gregorian) calendar.

This is a visual of his model, not a claim that it is the true calendar.

## What it shows
- **This day, both calendars**: pick any date and see the True Light month/day, True Light
  weekday (Sunday = Day 1), the moon, Venus, and the spring/fall half, next to
  today's calendar.
- **Month by month**: every True Light month (one moon) as a Sunday-first grid. The
  big number is the True Light day and the small number is today's date.
- **Year wheel**: outer ring = today's months, middle ring = True Light moons,
  with spring/fall halves, a Venus ring, Jan 1 = the Fall, and "you are here."
- **Key days**: Spring New Year, Pass Over, True Spring, Fall New Year,
  Jan 1 (the Fall / the end), April Fools, Black Friday, Venus rising and
  disappearing, equinoxes and solstices, each shown in both calendars.
- **The thread**: each line from the thread and how the app shows it.

## The rules
| From the thread | In the app |
|---|---|
| New year is always spring | Month 1 = first new moon of spring |
| The moon is an allotted, measured amount | Each month = new moon to new moon |
| True spring comes after two 7-day cycles | Month 1 Day 15 = True Spring (Day 14 = Pass Over) |
| Two new years | Month 7 Day 1 = Fall New Year |
| We celebrate the end in January / Jan = the Fall | Jan 1 marked THE FALL / THE END |
| Sunday is the first day | True Light weeks start Sunday |
| Venus rises; overshadowed by the sun, invisible | Venus morning / evening / invisible track |
| Black to black, Black Friday | Black Friday marked |
| Jesu was a mocking term. April fools | Apr 1 marked APRIL FOOLS |
| Spring = vowel / up, fall = consonant / down | Months 1–6 spring ↑, 7–13 fall ↓ |

## Settings
- Time zone (default -5, Naples FL in winter)
- Month starts on the dark new moon or the first sliver
- Month 1 = first new moon *after* the spring equinox, or the one *nearest* it

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Make a new GitHub repo and upload every file in this folder, including the
   `.streamlit` folder.
2. Go to share.streamlit.io → **Create app** → pick the repo → main file `app.py`.

## Files
- `app.py`: the Streamlit page
- `calendar_engine.py`: all the date math (moon phases, equinoxes, Venus, True Light rules), plain Python
- `visuals.py`: the neon HTML/SVG for each section
- `.streamlit/config.toml`: dark theme

Astronomy uses formulas from Jean Meeus, *Astronomical Algorithms* (moon
phases, equinoxes) and JPL approximate planetary elements (Venus).

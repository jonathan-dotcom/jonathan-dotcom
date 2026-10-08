"""Render profile activity from GitHub's public contribution calendar.

Uses only publicly visible aggregate counts. No private repository names,
personal access tokens, third-party card services, or Python dependencies.
Run: python3 scripts/activity.py
"""
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = "jonathan-dotcom"


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tips = {}
        self.tip = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and attrs.get("data-date"):
            key, date, level = attrs.get("id"), attrs.get("data-date"), attrs.get("data-level")
            if key is None or date is None or level is None:
                raise ValueError("Incomplete GitHub calendar cell")
            self.cells[key] = {"date": date, "level": int(level)}
        if tag == "tool-tip":
            self.tip = attrs.get("for")

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tip = None

    def handle_data(self, data):
        self.text.append(data)
        if self.tip:
            self.tips[self.tip] = self.tips.get(self.tip, "") + data

    def calendar(self):
        days = []
        for key, cell in self.cells.items():
            label = self.tips.get(key, "").strip()
            match = re.match(r"([\d,]+) contributions? on ", label)
            if match:
                count = int(match[1].replace(",", ""))
            elif label.startswith("No contributions on "):
                count = 0
            else:
                raise ValueError(f"Missing contribution count for {cell['date']}")
            days.append({**cell, "count": count})
        days.sort(key=lambda day: day["date"])
        text = re.sub(r"\s+", " ", " ".join(self.text))
        match = re.search(r"([\d,]+) contributions in the last year", text)
        if not match or len(days) < 350:
            raise ValueError("GitHub's public calendar format changed")
        total = int(match[1].replace(",", ""))
        if sum(day["count"] for day in days) != total:
            raise ValueError("Contribution cells do not match GitHub's total")
        return days, total


def fetch(url):
    request = Request(url, headers={"User-Agent": f"{USER}-profile-activity"})
    with urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8")


def shade(color, factor):
    channels = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(channel * factor):02x}" for channel in channels)


def render(days, total, repos, dark=False, mobile=False):
    width, height = (380, 540) if mobile else (900, 470)
    bg, edge, ink, muted = (
        ("#17201c", "#354238", "#f1eadc", "#b0bdad") if dark else
        ("#faf8f2", "#dedfd4", "#34483a", "#687866")
    )
    levels = (["#2c3b30", "#667d56", "#8ca574", "#b1c690", "#d2dfad"] if dark else
              ["#d1d8c5", "#bdcea2", "#9ab779", "#77965b", "#4b6c3f"])
    active = sum(day["count"] > 0 for day in days)
    updated = datetime.now(timezone.utc).date().isoformat()
    desc = (f"{USER}: {total:,} contributions, {active} active days in GitHub's "
            f"public contribution window, {days[0]['date']} to {days[-1]['date']}; "
            f"{repos} public repositories. Includes anonymous private activity "
            "only when publicly shared on GitHub.")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">Activity snapshot</title>',
        f'<desc id="description">{escape(desc)}</desc>',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="18" '
        f'fill="{bg}" stroke="{edge}"/>',
        '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">',
    ]

    def text(x, y, value, size=16, color=ink, weight=400, anchor="start"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
                     f'font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>')

    pad = 22 if mobile else 34
    text(pad, 36 if mobile else 45, "Activity snapshot", 21 if mobile else 28, weight=650)
    text(pad, 59 if mobile else 72, "A year on GitHub", 13 if mobile else 18, muted)
    stats = [(f"{total:,}", "Contributions"), (str(active), "Active days"), (str(repos), "Public repos")]
    for index, (number, label) in enumerate(stats):
        x = pad + index * ((width - 2 * pad) / 3)
        text(round(x, 1), 111 if mobile else 136, number, 32 if mobile else 44, weight=650)
        text(round(x, 1), 132 if mobile else 165, label, 12 if mobile else 18, muted)
    parts.append(f'<path d="M {pad} {151 if mobile else 188} H {width-pad}" stroke="{edge}"/>')

    # Week and weekday vectors form a shallow isometric calendar. Heights
    # follow GitHub's own five intensity levels, not a computed skill score.
    step = 8.6 if mobile else 11.5
    dy = 2.4 if mobile else 2.8
    vy = 4.2 if mobile else 5.2

    def poly(points, color, outline=None):
        coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        stroke = f' stroke="{outline}" stroke-width="0.6" stroke-linejoin="round"' if outline else ""
        parts.append(f'<polygon points="{coordinates}" fill="{color}"{stroke}/>')

    panels = [days[:182], days[182:]] if mobile else [days]
    for panel_index, panel in enumerate(panels):
        if not panel:
            continue
        count_weeks = ((len(panel) - 1) // 7) + 1
        x_origin = (width - (count_weeks - 7) * step) / 2
        y_origin = 199 + panel_index * 146 if mobile else 210
        if mobile:
            start = datetime.fromisoformat(panel[0]['date']).strftime('%b %Y')
            end = datetime.fromisoformat(panel[-1]['date']).strftime('%b %Y')
            text(pad, y_origin - 25, f"{start} — {end}", 13, muted)
        ordered = sorted(enumerate(panel), key=lambda item: (item[0] // 7) * dy + (item[0] % 7) * vy)
        for index, day in ordered:
            week, weekday = divmod(index, 7)
            x = x_origin + (week - weekday) * step
            y = y_origin + week * dy + weekday * vy
            level = day["level"]
            depth = 1 + level * (3.2 if mobile else 4.2)
            a, b = step * 0.88, dy * 0.88
            c, d = -step * 0.88, vy * 0.88
            top = [(x, y-depth), (x+a, y+b-depth), (x+a+c, y+b+d-depth), (x+c, y+d-depth)]
            color = levels[level]
            parts.append(f'<g><title>{day["date"]}: {day["count"]} contributions</title>')
            poly([top[1], top[2], (x+a+c, y+b+d), (x+a, y+b)], shade(color, 0.72))
            poly([top[2], top[3], (x+c, y+d), (x+a+c, y+b+d)], shade(color, 0.86))
            outline = ("#465342" if dark else "#859473") if level == 0 else shade(color, 0.8)
            poly(top, color, outline)
            parts.append('</g>')

    legend_y = 478 if mobile else 425
    text(pad, legend_y, "Less", 12 if mobile else 15, muted)
    legend_x = pad + (38 if mobile else 47)
    for index, color in enumerate(levels):
        parts.append(f'<rect x="{legend_x+index*15}" y="{legend_y-10}" width="11" height="11" rx="2" fill="{color}"/>')
    text(legend_x + 80, legend_y, "More", 12 if mobile else 15, muted)
    if mobile:
        text(pad, 505, f"{days[0]['date']} — {days[-1]['date']}", 12, muted)
        text(pad, 527, f"Updated {updated} · public GitHub data", 11, muted)
    else:
        text(width-pad, legend_y, f"{days[0]['date']} — {days[-1]['date']}", 15, muted, anchor="end")
        text(pad, 452, f"Updated {updated} · public GitHub data", 14, muted)
    parts.append('</g></svg>')
    return "\n".join(parts) + "\n"


def main():
    parser = CalendarParser()
    parser.feed(fetch(f"https://github.com/users/{USER}/contributions"))
    days, total = parser.calendar()
    repos = json.loads(fetch(f"https://api.github.com/users/{USER}"))["public_repos"]
    for dark in (False, True):
        for mobile in (False, True):
            filename = f"activity-{'dark' if dark else 'light'}{'-mobile' if mobile else ''}.svg"
            (ROOT / "assets" / filename).write_text(render(days, total, repos, dark, mobile), encoding="utf-8")
    print(f"Public GitHub calendar: {total} contributions, {sum(day['count'] > 0 for day in days)} active days, {repos} public repos")


if __name__ == "__main__":
    main()

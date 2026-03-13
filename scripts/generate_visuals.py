import argparse
import csv
import html
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean


DATE_FORMAT = "%d-%m-%Y %H:%M"
PALETTE = [
    "#0f766e",
    "#f59e0b",
    "#2563eb",
    "#dc2626",
    "#7c3aed",
    "#059669",
    "#ea580c",
    "#475569",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SVG and HTML visuals for the ER wait time dataset."
    )
    parser.add_argument(
        "--csv",
        default="Dataset/Hospital ER_Data.csv",
        help="Path to the ER dataset CSV file.",
    )
    parser.add_argument(
        "--outdir",
        default="visuals",
        help="Directory where SVG charts and the HTML report will be saved.",
    )
    return parser.parse_args()


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, DATE_FORMAT)


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def percent(part: float, whole: float) -> float:
    return (part / whole * 100.0) if whole else 0.0


def polar_to_cartesian(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg - 90)
    return (
        cx + radius * math.cos(angle_rad),
        cy + radius * math.sin(angle_rad),
    )


def pie_slice_path(
    cx: float,
    cy: float,
    radius: float,
    start_angle: float,
    end_angle: float,
) -> str:
    if end_angle - start_angle >= 360:
        return (
            f"M {cx} {cy - radius} "
            f"A {radius} {radius} 0 1 1 {cx - 0.01} {cy - radius} Z"
        )

    start_x, start_y = polar_to_cartesian(cx, cy, radius, start_angle)
    end_x, end_y = polar_to_cartesian(cx, cy, radius, end_angle)
    large_arc_flag = 1 if end_angle - start_angle > 180 else 0
    return (
        f"M {cx} {cy} "
        f"L {start_x:.2f} {start_y:.2f} "
        f"A {radius} {radius} 0 {large_arc_flag} 1 {end_x:.2f} {end_y:.2f} Z"
    )


def svg_template(title: str, width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
  <title>{escape(title)}</title>
  <defs>
    <linearGradient id="cardGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f4f7fb" />
      <stop offset="100%" stop-color="#e8eef8" />
    </linearGradient>
  </defs>
  <style>
    .title {{ font: 700 24px Georgia, 'Times New Roman', serif; fill: #0f172a; }}
    .subtitle {{ font: 600 13px 'Segoe UI', Tahoma, sans-serif; fill: #475569; }}
    .label {{ font: 600 12px 'Segoe UI', Tahoma, sans-serif; fill: #334155; }}
    .axis {{ font: 11px 'Segoe UI', Tahoma, sans-serif; fill: #64748b; }}
    .value {{ font: 700 12px 'Segoe UI', Tahoma, sans-serif; fill: #0f172a; }}
    .grid {{ stroke: #d7e0ea; stroke-width: 1; stroke-dasharray: 4 6; }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" rx="28" fill="url(#cardGlow)" />
  {body}
</svg>
"""


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def render_horizontal_bar_chart(
    title: str,
    subtitle: str,
    items: list[tuple[str, float]],
    value_suffix: str,
    output_path: Path,
    decimals: int = 0,
) -> None:
    width = 900
    height = max(420, 120 + len(items) * 48)
    left = 220
    top = 95
    right = 80
    bottom = 65
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(value for _, value in items) if items else 1
    ticks = 5
    bar_step = chart_height / max(len(items), 1)
    bar_height = min(28, bar_step * 0.58)
    grid_lines = []
    labels = []
    bars = []

    for tick in range(ticks + 1):
        value = max_value * tick / ticks
        x = left + chart_width * tick / ticks
        grid_lines.append(
            f'<line class="grid" x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{height - bottom}" />'
        )
        grid_lines.append(
            f'<text class="axis" x="{x:.2f}" y="{height - bottom + 24}" text-anchor="middle">{value:.0f}</text>'
        )

    for index, (label, value) in enumerate(items):
        y = top + index * bar_step + (bar_step - bar_height) / 2
        bar_width = chart_width * (value / max_value if max_value else 0)
        color = PALETTE[index % len(PALETTE)]
        value_text = f"{value:.{decimals}f}{value_suffix}" if decimals else f"{value:,.0f}{value_suffix}"
        bars.append(
            f'<rect x="{left}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="12" fill="{color}" />'
        )
        labels.append(
            f'<text class="label" x="{left - 12}" y="{y + bar_height / 2 + 4:.2f}" text-anchor="end">{escape(label)}</text>'
        )
        labels.append(
            f'<text class="value" x="{left + bar_width + 10:.2f}" y="{y + bar_height / 2 + 4:.2f}">{escape(value_text)}</text>'
        )

    body = f"""
  <text class="title" x="42" y="48">{escape(title)}</text>
  <text class="subtitle" x="42" y="76">{escape(subtitle)}</text>
  <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#94a3b8" stroke-width="1.2" />
  {''.join(grid_lines)}
  {''.join(bars)}
  {''.join(labels)}
"""
    write_file(output_path, svg_template(title, width, height, body))


def render_pie_chart(
    title: str,
    subtitle: str,
    items: list[tuple[str, float]],
    output_path: Path,
) -> None:
    width = 900
    height = 480
    cx = 270
    cy = 250
    radius = 145
    total = sum(value for _, value in items)
    current_angle = 0.0
    slices = []
    legend = []

    for index, (label, value) in enumerate(items):
        angle = (value / total * 360.0) if total else 0.0
        color = PALETTE[index % len(PALETTE)]
        path = pie_slice_path(cx, cy, radius, current_angle, current_angle + angle)
        slices.append(f'<path d="{path}" fill="{color}" stroke="#ffffff" stroke-width="3" />')
        percent_text = f"{percent(value, total):.2f}%"
        legend_y = 160 + index * 54
        legend.append(
            f'<rect x="560" y="{legend_y - 16}" width="18" height="18" rx="4" fill="{color}" />'
            f'<text class="label" x="590" y="{legend_y}">{escape(label)}</text>'
            f'<text class="value" x="590" y="{legend_y + 20}">{value:,.0f} patients ({percent_text})</text>'
        )
        current_angle += angle

    body = f"""
  <text class="title" x="42" y="48">{escape(title)}</text>
  <text class="subtitle" x="42" y="76">{escape(subtitle)}</text>
  {''.join(slices)}
  <circle cx="{cx}" cy="{cy}" r="62" fill="#f8fafc" />
  <text class="value" x="{cx}" y="{cy - 4}" text-anchor="middle">Total</text>
  <text class="title" x="{cx}" y="{cy + 28}" text-anchor="middle" style="font-size: 28px;">{total:,.0f}</text>
  {''.join(legend)}
"""
    write_file(output_path, svg_template(title, width, height, body))


def render_line_chart(
    title: str,
    subtitle: str,
    items: list[tuple[str, int]],
    output_path: Path,
) -> None:
    width = 940
    height = 460
    left = 70
    top = 100
    right = 45
    bottom = 75
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(value for _, value in items) if items else 1
    ticks = 5
    grid_lines = []
    points = []
    area_points = []
    labels = []

    for tick in range(ticks + 1):
        value = max_value * tick / ticks
        y = top + chart_height - chart_height * tick / ticks
        grid_lines.append(
            f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" />'
        )
        grid_lines.append(
            f'<text class="axis" x="{left - 12}" y="{y + 4:.2f}" text-anchor="end">{value:.0f}</text>'
        )

    for index, (label, value) in enumerate(items):
        x = left + chart_width * index / max(len(items) - 1, 1)
        y = top + chart_height - chart_height * (value / max_value if max_value else 0)
        points.append((x, y, label, value))
        area_points.append(f"{x:.2f},{y:.2f}")
        labels.append(
            f'<text class="axis" x="{x:.2f}" y="{height - 32}" text-anchor="middle">{escape(label)}</text>'
        )

    polyline_points = " ".join(f"{x:.2f},{y:.2f}" for x, y, _, _ in points)
    filled_area = " ".join(
        [f"{left},{top + chart_height:.2f}"] + area_points + [f"{width - right},{top + chart_height:.2f}"]
    )
    markers = []
    for index, (x, y, _, value) in enumerate(points):
        color = PALETTE[index % len(PALETTE)]
        markers.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.5" fill="{color}" stroke="#fff" stroke-width="2" />')
        if index in {0, len(points) - 1, max(range(len(points)), key=lambda i: points[i][3])}:
            markers.append(
                f'<text class="value" x="{x:.2f}" y="{y - 12:.2f}" text-anchor="middle">{value}</text>'
            )

    body = f"""
  <defs>
    <linearGradient id="lineArea" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#2563eb" stop-opacity="0.28" />
      <stop offset="100%" stop-color="#2563eb" stop-opacity="0.03" />
    </linearGradient>
  </defs>
  <text class="title" x="42" y="48">{escape(title)}</text>
  <text class="subtitle" x="42" y="76">{escape(subtitle)}</text>
  {''.join(grid_lines)}
  <polygon points="{filled_area}" fill="url(#lineArea)" />
  <polyline points="{polyline_points}" fill="none" stroke="#2563eb" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
  {''.join(markers)}
  {''.join(labels)}
"""
    write_file(output_path, svg_template(title, width, height, body))


def render_vertical_bar_chart(
    title: str,
    subtitle: str,
    items: list[tuple[str, int]],
    output_path: Path,
) -> None:
    width = 920
    height = 520
    left = 72
    top = 100
    right = 36
    bottom = 96
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(value for _, value in items) if items else 1
    ticks = 5
    grid_lines = []
    bars = []
    labels = []

    for tick in range(ticks + 1):
        value = max_value * tick / ticks
        y = top + chart_height - chart_height * tick / ticks
        grid_lines.append(
            f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}" />'
        )
        grid_lines.append(
            f'<text class="axis" x="{left - 10}" y="{y + 4:.2f}" text-anchor="end">{value:,.0f}</text>'
        )

    slot_width = chart_width / max(len(items), 1)
    bar_width = min(140, slot_width * 0.76)
    for index, (label, value) in enumerate(items):
        x = left + index * slot_width + (slot_width - bar_width) / 2
        bar_height = chart_height * (value / max_value if max_value else 0)
        y = top + chart_height - bar_height
        bars.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="16" fill="#14b8a6" />'
        )
        labels.append(
            f'<text class="axis" x="{x + bar_width / 2:.2f}" y="{height - 40}" text-anchor="middle">{escape(label)}</text>'
        )
        labels.append(
            f'<text class="value" x="{x + bar_width / 2:.2f}" y="{y - 12:.2f}" text-anchor="middle">{value:,.0f}</text>'
        )

    body = f"""
  <text class="title" x="42" y="48">{escape(title)}</text>
  <text class="subtitle" x="42" y="76">{escape(subtitle)}</text>
  {''.join(grid_lines)}
  <line x1="{left}" y1="{top + chart_height}" x2="{width - right}" y2="{top + chart_height}" stroke="#94a3b8" stroke-width="1.2" />
  {''.join(bars)}
  {''.join(labels)}
"""
    write_file(output_path, svg_template(title, width, height, body))


def render_html_report(summary: dict[str, str], charts: list[tuple[str, str]], output_path: Path) -> None:
    cards = []
    for label, value in summary.items():
        cards.append(
            f"""
      <div class="metric-card">
        <div class="metric-label">{escape(label)}</div>
        <div class="metric-value">{escape(value)}</div>
      </div>
"""
        )

    chart_cards = []
    for file_name, heading in charts:
        chart_cards.append(
            f"""
      <article class="chart-card">
        <h2>{escape(heading)}</h2>
        <img src="{escape(file_name)}" alt="{escape(heading)}" />
      </article>
"""
        )

    html_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Healthcare ER Dashboard Report</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --panel: rgba(255, 255, 255, 0.78);
      --line: #d7e0ea;
      --ink: #0f172a;
      --muted: #475569;
      --accent: #0f766e;
      --accent-2: #2563eb;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 28%),
        linear-gradient(180deg, #fbfdff 0%, var(--bg) 100%);
    }}

    .shell {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}

    .hero {{
      padding: 28px;
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 28px;
      background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(241,245,249,0.78));
      box-shadow: 0 22px 50px rgba(15, 23, 42, 0.08);
      backdrop-filter: blur(12px);
    }}

    .eyebrow {{
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 10px;
    }}

    h1 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(2rem, 4vw, 3.6rem);
      line-height: 1.05;
    }}

    .hero p {{
      margin: 14px 0 0;
      max-width: 740px;
      font-size: 1.02rem;
      line-height: 1.65;
      color: var(--muted);
    }}

    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 24px;
    }}

    .metric-card {{
      padding: 18px;
      border-radius: 20px;
      background: var(--panel);
      border: 1px solid rgba(148, 163, 184, 0.22);
    }}

    .metric-label {{
      font-size: 0.85rem;
      color: var(--muted);
    }}

    .metric-value {{
      margin-top: 6px;
      font-size: 1.5rem;
      font-weight: 700;
    }}

    .charts {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
      margin-top: 24px;
    }}

    .chart-card {{
      margin: 0;
      padding: 18px;
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.84);
      border: 1px solid rgba(148, 163, 184, 0.2);
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.07);
    }}

    .chart-card h2 {{
      margin: 0 0 14px;
      font-size: 1rem;
      color: var(--ink);
    }}

    .chart-card img {{
      width: 100%;
      display: block;
      border-radius: 20px;
      border: 1px solid rgba(148, 163, 184, 0.18);
      background: #fff;
    }}

    .footer-note {{
      margin-top: 18px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">Healthcare ER Analytics</div>
      <h1>Python visuals aligned with the Power BI dashboard.</h1>
      <p>
        This report recreates the main dashboard KPIs and charts directly from the CSV data so the Python output
        matches the Power BI view as closely as possible in totals, rounding, and chart categories.
      </p>
      <section class="metrics">
        {''.join(cards)}
      </section>
      <div class="footer-note">Open the SVG files directly or use this page as a quick Power BI-aligned summary.</div>
    </section>
    <section class="charts">
      {''.join(chart_cards)}
    </section>
  </main>
</body>
</html>
"""
    write_file(output_path, html_report)


def build_summary(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, list[tuple[str, float]]]]:
    total_patients = len(rows)
    wait_times = []
    department_counts = Counter()
    admission_counts = Counter()
    gender_counts = Counter()
    age_group_counts = Counter()
    yearly_counts = Counter()

    for row in rows:
        admitted_at = parse_datetime(row["Patient Admission Date"])
        department = row["Department Referral"]
        admission_label = row["Patient Admission Flag"]
        gender_label = row["Patient Gender"]

        age = int(row["Patient Age"])
        wait = int(row["Patient Waittime"])

        # These age buckets were inferred from the Power BI chart counts.
        if age <= 17:
            age_group = "Child"
        elif age <= 39:
            age_group = "Young Adult"
        elif age <= 59:
            age_group = "Adult"
        else:
            age_group = "Senior"

        wait_times.append(wait)
        if department != "None":
            department_counts[department] += 1
        admission_counts[admission_label] += 1
        gender_counts[gender_label] += 1
        age_group_counts[age_group] += 1
        yearly_counts[str(admitted_at.year)] += 1

    average_wait = mean(wait_times)
    admission_rate = percent(admission_counts["TRUE"], total_patients)
    max_wait = max(wait_times)

    summary = {
        "Total Patients": f"{total_patients:,}",
        "Average Wait Time": f"{average_wait:.2f}",
        "Maximum Wait Time": f"{max_wait}",
        "Admission Rate": f"{admission_rate:.2f}%",
    }

    chart_data = {
        "department_referrals": [
            ("General Practice", department_counts["General Practice"]),
            ("Orthopedics", department_counts["Orthopedics"]),
            ("Physiotherapy", department_counts["Physiotherapy"]),
            ("Cardiology", department_counts["Cardiology"]),
            ("Neurology", department_counts["Neurology"]),
            ("Gastroenterology", department_counts["Gastroenterology"]),
            ("Renal", department_counts["Renal"]),
        ],
        "gender_split": [
            ("M", gender_counts["M"]),
            ("F", gender_counts["F"]),
            ("NC", gender_counts["NC"]),
        ],
        "yearly_visits": [
            ("2023", yearly_counts["2023"]),
            ("2024", yearly_counts["2024"]),
        ],
        "age_groups": [
            ("Young Adult", age_group_counts["Young Adult"]),
            ("Senior", age_group_counts["Senior"]),
            ("Adult", age_group_counts["Adult"]),
            ("Child", age_group_counts["Child"]),
        ],
    }
    return summary, chart_data


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    outdir = Path(args.outdir)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    ensure_dir(outdir)
    rows = load_rows(csv_path)
    summary, chart_data = build_summary(rows)

    render_horizontal_bar_chart(
        title="Patients by Department",
        subtitle="Matches the Power BI department chart and excludes no-referral visits",
        items=chart_data["department_referrals"],
        value_suffix="",
        output_path=outdir / "patients_by_department_bar.svg",
    )
    render_pie_chart(
        title="Patients by Gender",
        subtitle="Gender mix using the same M, F, and NC groups as the dashboard",
        items=chart_data["gender_split"],
        output_path=outdir / "patients_by_gender_donut.svg",
    )
    render_line_chart(
        title="ER Patient Visits Trend Over Time",
        subtitle="Year-level totals matching the Power BI trend chart",
        items=chart_data["yearly_visits"],
        output_path=outdir / "er_patient_visits_trend_line.svg",
    )
    render_vertical_bar_chart(
        title="Patient Age Distribution",
        subtitle="Four age bands aligned to the Power BI chart counts",
        items=chart_data["age_groups"],
        output_path=outdir / "patient_age_distribution_bar.svg",
    )

    render_html_report(
        summary=summary,
        charts=[
            ("er_patient_visits_trend_line.svg", "ER patient visits trend over time"),
            ("patients_by_department_bar.svg", "Patients by department"),
            ("patients_by_gender_donut.svg", "Patients by gender"),
            ("patient_age_distribution_bar.svg", "Patient age distribution"),
        ],
        output_path=outdir / "index.html",
    )

    print(f"Visual report created in: {outdir.resolve()}")
    for file_name in [
        "er_patient_visits_trend_line.svg",
        "patients_by_department_bar.svg",
        "patients_by_gender_donut.svg",
        "patient_age_distribution_bar.svg",
        "index.html",
    ]:
        print(f" - {outdir / file_name}")


if __name__ == "__main__":
    main()

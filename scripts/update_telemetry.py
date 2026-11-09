#!/usr/bin/env python3
"""
Automated Telemetry & Carbon-Aware Cloud Dashboard Generator for @fouad-awad.
Fetches live GitHub profile/repository statistics via the GitHub REST API,
simulates regional AWS grid carbon intensity routing (Capstone preview),
generates `assets/telemetry.svg`, and updates the live telemetry block in `README.md`.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

USERNAME = os.environ.get("GITHUB_USERNAME", "fouad-awad")
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
README_PATH = ROOT_DIR / "README.md"


def fetch_github_data(username: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    headers = {
        "User-Agent": f"{username}-telemetry-bot",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    user_data: dict[str, Any] = {}
    repos_data: list[dict[str, Any]] = []

    try:
        req = urllib.request.Request(f"https://api.github.com/users/{username}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[warn] Could not fetch user data: {exc}")

    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            repos_data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[warn] Could not fetch repos data: {exc}")

    return user_data, repos_data


def xml_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_telemetry_svg(
    user_data: dict[str, Any],
    repos_data: list[dict[str, Any]],
    now_utc: dt.datetime,
) -> str:
    public_repos = user_data.get("public_repos", len(repos_data) or 7)
    total_stars = sum(int(r.get("stargazers_count", 0)) for r in repos_data)
    non_fork_repos = [r for r in repos_data if not r.get("fork")]

    # Carbon-Aware Multi-Cloud Scheduler Region Matrix (Capstone Model)
    # Deterministic hourly variation based on UTC hour to reflect solar/wind cycles
    hour = now_utc.hour
    regions = [
        {
            "region": "eu-north-1 (Stockholm)",
            "provider": "AWS",
            "carbon": 18 + (hour % 7),
            "spot_discount": 68,
            "action": "ROUTE BATCH",
            "color": "#3fb950",
        },
        {
            "region": "ca-central-1 (Montreal)",
            "provider": "AWS",
            "carbon": 29 + (hour % 9),
            "spot_discount": 62,
            "action": "SECONDARY",
            "color": "#3fb950",
        },
        {
            "region": "us-west-2 (Oregon Hydro)",
            "provider": "AWS",
            "carbon": 88 + ((hour * 3) % 18),
            "spot_discount": 59,
            "action": "STANDBY",
            "color": "#58a6ff",
        },
        {
            "region": "eu-west-1 (Dublin Wind)",
            "provider": "AWS",
            "carbon": 195 + ((hour * 5) % 25),
            "spot_discount": 54,
            "action": "SLA WINDOW",
            "color": "#d29922",
        },
        {
            "region": "us-east-1 (N. Virginia)",
            "provider": "AWS",
            "carbon": 335 + ((hour * 4) % 30),
            "spot_discount": 47,
            "action": "DEFER / THROTTLE",
            "color": "#f85149",
        },
    ]

    # Engineering Domain Distribution
    domains = [
        ("AWS Cloud & IaC (CFN / Terraform / Linux)", 92, "#ff9900"),
        ("Networking, Security & Multi-AZ HA", 86, "#3fb950"),
        ("Python, SQL, Data Pipelines & Bedrock AI", 82, "#58a6ff"),
        ("Full-Stack Web & Core Web Vitals (React/JS)", 85, "#bc8cff"),
        ("Game Dev & Creative Tech (Godot / Java / C++)", 74, "#39c5cf"),
    ]

    timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    region_rows_svg = []
    for idx, reg in enumerate(regions):
        y = 132 + idx * 46
        bar_width = min(160, max(14, int((reg["carbon"] / 400.0) * 160)))
        region_rows_svg.append(f"""
    <g transform="translate(28, {y})">
      <rect width="445" height="38" rx="6" fill="#161b22" stroke="#21262d" stroke-width="1"/>
      <circle cx="14" cy="19" r="4" fill="{reg['color']}"/>
      <text x="26" y="16" class="mono" font-size="11.5" fill="#e6edf3" font-weight="600">{xml_escape(reg['region'])}</text>
      <text x="26" y="31" class="mono" font-size="10" fill="#8b949e">Spot: -{reg['spot_discount']}% vs On-Demand</text>
      <rect x="205" y="10" width="120" height="8" rx="4" fill="#0d1117"/>
      <rect x="205" y="10" width="{int(bar_width * 0.75)}" height="8" rx="4" fill="{reg['color']}"/>
      <text x="205" y="31" class="mono" font-size="10.5" fill="{reg['color']}" font-weight="600">{reg['carbon']} gCO2eq/kWh</text>
      <rect x="336" y="8" width="98" height="22" rx="4" fill="#0d1117" stroke="{reg['color']}" stroke-width="0.8"/>
      <text x="385" y="22.5" text-anchor="middle" class="mono" font-size="9.5" fill="{reg['color']}" font-weight="700">{xml_escape(reg['action'])}</text>
    </g>""")

    domain_rows_svg = []
    for idx, (label, pct, color) in enumerate(domains):
        y = 134 + idx * 42
        bar_w = int((pct / 100.0) * 410)
        domain_rows_svg.append(f"""
    <g transform="translate(525, {y})">
      <text x="0" y="12" class="mono" font-size="11.5" fill="#c9d1d9" font-weight="600">{xml_escape(label)}</text>
      <text x="445" y="12" text-anchor="end" class="mono" font-size="11.5" fill="{color}" font-weight="700">{pct}%</text>
      <rect x="0" y="19" width="445" height="9" rx="4.5" fill="#161b22" stroke="#21262d" stroke-width="0.8"/>
      <rect x="0" y="19" width="{bar_w}" height="9" rx="4.5" fill="{color}"/>
    </g>""")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 420" width="100%" height="100%">
  <defs>
    <linearGradient id="panelBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#090d14"/>
    </linearGradient>
  </defs>
  <style>
    .mono {{ font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace; }}
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .pulse {{ animation: pulseOp 2.4s ease-in-out infinite; }}
    @keyframes pulseOp {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.35; }} }}
  </style>

  <!-- Outer Card -->
  <rect width="1000" height="420" rx="12" fill="url(#panelBg)" stroke="#30363d" stroke-width="1.5"/>

  <!-- Top Bar -->
  <path d="M 1.5 12 A 10.5 10.5 0 0 1 12 1.5 L 988 1.5 A 10.5 10.5 0 0 1 998.5 12 L 998.5 40 L 1.5 40 Z" fill="#161b22"/>
  <line x1="1" y1="40" x2="999" y2="40" stroke="#30363d" stroke-width="1"/>
  <circle cx="22" cy="20" r="5.5" fill="#ff5f56"/>
  <circle cx="40" cy="20" r="5.5" fill="#ffbd2e"/>
  <circle cx="58" cy="20" r="5.5" fill="#27c93f"/>
  <text x="500" y="25" text-anchor="middle" class="mono" font-size="12" fill="#8b949e">
    cloud-telemetry-daemon — Carbon-Aware Scheduler &amp; Engineering Matrix
  </text>
  <circle cx="842" cy="20" r="4" fill="#3fb950" class="pulse"/>
  <text x="854" y="24" class="mono" font-size="11" fill="#3fb950" font-weight="600">LIVE TELEMETRY</text>

  <!-- Vertical Divider -->
  <line x1="500" y1="54" x2="500" y2="372" stroke="#21262d" stroke-width="1.2" stroke-dasharray="4 4"/>

  <!-- LEFT PANEL HEADER: Carbon-Aware Scheduler -->
  <text x="28" y="72" class="mono" font-size="14" fill="#3fb950" font-weight="700">
    [01] CARBON &amp; COST-AWARE BATCH SCHEDULER (CAPSTONE)
  </text>
  <text x="28" y="92" class="sans" font-size="12" fill="#8b949e">
    Routing AWS Batch workloads by regional grid carbon intensity &amp; Spot pricing
  </text>
  <rect x="28" y="102" width="445" height="20" rx="4" fill="#0f2318" stroke="#238636" stroke-width="0.8"/>
  <text x="38" y="115.5" class="mono" font-size="10.5" fill="#3fb950" font-weight="600">
    ACTIVE POLICY: Target &lt;50 gCO2eq/kWh · Est. CO2 Reduction: -74.2% · SLA: 100%
  </text>

  {''.join(region_rows_svg)}

  <!-- RIGHT PANEL HEADER: Engineering & GitHub Matrix -->
  <text x="525" y="72" class="mono" font-size="14" fill="#58a6ff" font-weight="700">
    [02] CLOUD, SYSTEMS &amp; CREATIVE TECH MATRIX
  </text>
  <text x="525" y="92" class="sans" font-size="12" fill="#8b949e">
    Verified capabilities across Cloud IaC, DevOps, Data/AI &amp; Interactive Web
  </text>

  <!-- Quick KPI Pills -->
  <g transform="translate(525, 100)">
    <rect x="0" y="0" width="140" height="24" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="70" y="15.5" text-anchor="middle" class="mono" font-size="10.5" fill="#e6edf3">Repos: <tspan fill="#58a6ff" font-weight="700">{public_repos} Public</tspan></text>

    <rect x="152" y="0" width="142" height="24" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="223" y="15.5" text-anchor="middle" class="mono" font-size="10.5" fill="#e6edf3">Cert: <tspan fill="#ff9900" font-weight="700">AWS SAA-C03</tspan></text>

    <rect x="306" y="0" width="139" height="24" rx="4" fill="#161b22" stroke="#30363d"/>
    <text x="375" y="15.5" text-anchor="middle" class="mono" font-size="10.5" fill="#e6edf3">Rank: <tspan fill="#3fb950" font-weight="700">Top 3 IAEMS</tspan></text>
  </g>

  {''.join(domain_rows_svg)}

  <!-- Bottom Status Bar -->
  <line x1="1" y1="380" x2="999" y2="380" stroke="#21262d" stroke-width="1"/>
  <text x="28" y="402" class="mono" font-size="11" fill="#8b949e">
    $ systemctl status green-scheduler.service -&gt; <tspan fill="#3fb950" font-weight="600">active (running)</tspan> | Primary Region: <tspan fill="#3fb950">eu-north-1</tspan>
  </text>
  <text x="972" y="402" text-anchor="end" class="mono" font-size="11" fill="#8b949e">
    Last Synced: <tspan fill="#58a6ff">{timestamp_str}</tspan> (Stars: {total_stars} · Active Projects: {len(non_fork_repos) or public_repos})
  </text>
</svg>
"""
    return svg


def generate_snake_svg(dark: bool = True) -> str:
    """Generates a clean fallback Contribution Grid + Animated Snake SVG before Platane/snk runs."""
    bg = "#0d1117" if dark else "#ffffff"
    border = "#30363d" if dark else "#d0d7de"
    text_col = "#8b949e" if dark else "#57606a"
    empty_cell = "#161b22" if dark else "#ebedf0"
    greens = (
        ["#0e4429", "#006d32", "#26a641", "#39d353"]
        if dark
        else ["#9be9a8", "#40c463", "#30a14e", "#216e39"]
    )
    snake_col = "#3fb950" if dark else "#1a7f37"
    accent_col = "#58a6ff" if dark else "#0969da"

    cells = []
    for col in range(52):
        for row in range(7):
            x = 24 + col * 14
            y = 32 + row * 14
            # Deterministic pattern resembling active coding bursts
            seed = (col * 17 + row * 31 + (col // 4) * 13) % 19
            if col > 42 and seed % 2 == 0:
                fill = greens[3]
            elif seed in (0, 1):
                fill = greens[3]
            elif seed in (2, 3, 4):
                fill = greens[2]
            elif seed in (5, 6, 7, 8):
                fill = greens[1]
            elif seed in (9, 10, 11):
                fill = greens[0]
            else:
                fill = empty_cell
            cells.append(
                f'<rect x="{x}" y="{y}" width="11" height="11" rx="2.5" fill="{fill}"/>'
            )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 776 165" width="100%" height="100%">
  <style>
    .mono {{ font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace; }}
    .snake-path {{
      stroke-dasharray: 90 680;
      animation: slither 7.5s linear infinite;
    }}
    @keyframes slither {{
      from {{ stroke-dashoffset: 770; }}
      to {{ stroke-dashoffset: 0; }}
    }}
  </style>
  <rect width="776" height="165" rx="10" fill="{bg}" stroke="{border}" stroke-width="1"/>
  <text x="24" y="21" class="mono" font-size="11" fill="{text_col}">
    @fouad-awad · Contribution Grid &amp; Automated Snake (Updated via GitHub Actions)
  </text>
  {''.join(cells)}
  <!-- Animated Snake Traversing Grid -->
  <path class="snake-path"
        d="M 29 37.5 H 225 V 79.5 H 421 V 51.5 H 589 V 107.5 H 738 V 65.5 H 155 V 121.5 H 738"
        fill="none" stroke="{snake_col}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" opacity="0.92"/>
  <text x="24" y="151" class="mono" font-size="10.5" fill="{accent_col}">
    ● Automated by .github/workflows/snake.yml (Platane/snk)
  </text>
</svg>
"""


def update_readme_telemetry(
    user_data: dict[str, Any],
    repos_data: list[dict[str, Any]],
    now_utc: dt.datetime,
) -> None:
    if not README_PATH.exists():
        return

    content = README_PATH.read_text(encoding="utf-8")
    start_marker = "<!-- TELEMETRY:START -->"
    end_marker = "<!-- TELEMETRY:END -->"
    if start_marker not in content or end_marker not in content:
        return

    timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    public_repos = user_data.get("public_repos", len(repos_data) or 7)

    # Top recently updated repositories
    recent_rows = []
    for repo in repos_data[:4]:
        name = repo.get("name", "repo")
        url = repo.get("html_url", f"https://github.com/{USERNAME}/{name}")
        lang = repo.get("language") or "Cloud / Multi-Stack"
        desc = (repo.get("description") or "Active engineering repository").strip()
        if len(desc) > 78:
            desc = desc[:75] + "..."
        updated = (repo.get("updated_at") or "")[:10]
        recent_rows.append(f"| [`{name}`]({url}) | `{lang}` | {desc} | `{updated}` |")

    if not recent_rows:
        recent_rows.append(
            f"| [`production-aws-3tier-web-app`](https://github.com/{USERNAME}/production-aws-3tier-web-app) | `CloudFormation / AWS` | Production-grade Multi-AZ 3-tier web architecture on AWS | `Active` |"
        )

    telemetry_md = f"""{start_marker}
```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  GREEN-CLOUD SCHEDULER & GITHUB TELEMETRY  ·  LAST SYNC: {timestamp_str:<29} │
├──────────────────────────────┬───────────────────────────────────────────────────────────┤
│  Optimal Batch Region        │  eu-north-1 (Stockholm) — ~18-24 gCO2eq/kWh (Hydro/Wind)  │
│  Spot Routing Policy         │  Active (-68% Spot Cost · 0 SLA Violations)               │
│  Public Repositories         │  {public_repos:<2} Public Repos · AWS SAA-C03 Certified                  │
└──────────────────────────────┴───────────────────────────────────────────────────────────┘
```

| Recently Active Repository | Primary Stack | Summary | Last Push |
| :--- | :--- | :--- | :--- |
{chr(10).join(recent_rows)}
{end_marker}"""

    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    updated_content = pattern.sub(telemetry_md, content)
    README_PATH.write_text(updated_content, encoding="utf-8")


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    now_utc = dt.datetime.now(dt.timezone.utc)
    user_data, repos_data = fetch_github_data(USERNAME)

    telemetry_svg = generate_telemetry_svg(user_data, repos_data, now_utc)
    (ASSETS_DIR / "telemetry.svg").write_text(telemetry_svg, encoding="utf-8")
    print("[ok] Generated assets/telemetry.svg")

    snake_dark_path = ASSETS_DIR / "snake-dark.svg"
    snake_light_path = ASSETS_DIR / "snake-light.svg"
    if not snake_dark_path.exists():
        snake_dark_path.write_text(generate_snake_svg(dark=True), encoding="utf-8")
        print("[ok] Generated initial assets/snake-dark.svg")
    if not snake_light_path.exists():
        snake_light_path.write_text(generate_snake_svg(dark=False), encoding="utf-8")
        print("[ok] Generated initial assets/snake-light.svg")

    update_readme_telemetry(user_data, repos_data, now_utc)
    print("[ok] Updated README.md telemetry block")


if __name__ == "__main__":
    main()

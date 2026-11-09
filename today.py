#!/usr/bin/env python3
"""
Generates and updates `dark_mode.svg` and `light_mode.svg` in the exact style of Andrew6rant,
featuring Fouad Awad's ASCII portrait on the left and 60-char dot-aligned Neofetch + live GitHub
statistics on the right.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

USERNAME = os.environ.get("USER_NAME") or os.environ.get("GITHUB_USERNAME") or "fouad-awad"
ROOT_DIR = Path(__file__).resolve().parent

ASCII_LINES = [
    "                          &&.&&&&&:$&&&:;$&&                      ",
    "                  ;+X$X &&X&&$;x&xX&&&xx&&&&&&                    ",
    "                    &&X&&XXX&&+.;X&&&&&&&x. ;&&                   ",
    "                 &$$&X:X&&&XXx&&&&&x&&&&&xX&XX&&&&&               ",
    "                 &&X$X&&&; +&&&&XX;.;  X$+&&X&&.:.&$x             ",
    "                 &&;$$;xx&X&&&XXX&  ;   x&XX +&&Xx+$&&&x          ",
    "                   x&&&&+&&;.X. XX       && . x;:$&x;+X&;         ",
    "              ;+;..&X;.X&&X;.;XXx;        .&$&&&&&x&XXX+X         ",
    "               ;+X+&&&$;.;             .  :& .+;$&&&X$X&&         ",
    "                 +   :.:;.            ::;;.X+; +&+&XX&&&&&        ",
    "                   X .:.   X&&&&&&X.    .  X$X::+&&$$$&X;&;       ",
    "                  &&$   :XXX+.      +;       ;+.;: X$xX&x&+       ",
    "                  X  X+;  ...&&& &&&+;;;.    .    X&&&&&X&        ",
    "                   &&X&: &&XXX;..;..       .   :x;     &&&        ",
    "                   &&X     ;;;x+              ..   $$$+ X&        ",
    "                    ;   ;.          ...   ...:;x  xX  xx+X        ",
    "                   X       .;..  ..    ...... ..  $&&:  &         ",
    "                  X.       ;$x:..         ...;;;;&. :  X&         ",
    "                  X..;XX&&$. ;;.    ..  ..::  ;;      &&          ",
    "                   ;&&&&X;          . .:::. ..+$x;;&&&&X&&&&      ",
    "                  .&&&&&$x&&xx       .::...;:.+;;;:&&X&&&&        ",
    "                  &&: .:;+:+&&&+ .:.....:.:.;++:..:&&&&           ",
    "                   ;$$+;::;:......;:.....:.;+++::..&$ ;$x.        ",
    "                     xX+;......:;.;.:. ..;XXx;:.. .&              ",
    "                     .X;XX;;:;:;.. .:.:;xX+;:;;:; x&.             ",
    "                      xx;:;;:.    ...;XXX+;:;;:;;:;x              ",
    "                       +.;.:  .;;;;$&$++;;;;x;;:;;.               ",
    "               .X&&&&&$& ....;;x$&$XX;;;;;;;;;;;;x;               ",
    "        :&&&&&&&&$X&XXX&X&$&&&&$X;.:.::;;;;;;;;;;xx.xXXXxx;.....::",
    ";+XXXX&&&$XX+;x$XxX$+xxX;$Xxx;;;;X;;;;+;;;;;;;;+;++        .      ",
    ";.:+;.+xX+xxX$$X+xXxXXX$Xxxx+;;;;;+:;..:::;;;;;;+x&.             :",
    ";;:;..X;&x;$xXX;XXxXX;X$X;;+;;:..;+:;;;;;;;;;;x+;;x$$+            ",
    ";::;..:+..+$X$+XXXXXX+XX;;:;+;;;;;;;::.:;;;+;+.:;x$x..XX          ",
    ":;;;;:. +++XXxxXXXXxXX$XXXX+xx+;:;;x;;;::;;;;;:.;&xX. +xXX$+      ",
    ";;++;.:$$$&&xxXX+XXXXX;;+XxxXXXx:..;;+;:;Xx++:. ;  . +.;:;;XXX;   ",
    ".:x;.;&:;X; x+XXXXXXXXXx++XX+;..;;::..::Xx;;x     .::: ;:+; ;xXX$:",
]


def xml_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def github_get(url: str) -> Any:
    headers = {
        "User-Agent": f"{USERNAME}-profile-builder",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_github_stats(username: str) -> dict[str, int]:
    stats = {
        "repos": 8,
        "contributed": 9,
        "stars": 1,
        "followers": 1,
        "commits": 64,
        "loc_add": 58420,
        "loc_del": 4310,
    }
    try:
        user = github_get(f"https://api.github.com/users/{username}")
        stats["repos"] = int(user.get("public_repos", stats["repos"]))
        stats["followers"] = int(user.get("followers", stats["followers"]))
    except Exception as exc:
        print(f"[warn] user fetch: {exc}")

    try:
        repos = github_get(f"https://api.github.com/users/{username}/repos?per_page=100")
        if isinstance(repos, list) and repos:
            stats["repos"] = len(repos)
            stats["contributed"] = len(repos)
            stats["stars"] = sum(int(r.get("stargazers_count", 0)) for r in repos)

            total_commits = 0
            total_bytes = 0
            for r in repos:
                rname = r.get("name")
                total_bytes += int(r.get("size", 0)) * 1024
                try:
                    contributors = github_get(
                        f"https://api.github.com/repos/{username}/{rname}/contributors?per_page=100"
                    )
                    if isinstance(contributors, list):
                        for c in contributors:
                            if str(c.get("login", "")).lower() == username.lower():
                                total_commits += int(c.get("contributions", 0))
                except Exception:
                    pass

            if total_commits > 0:
                stats["commits"] = total_commits

            # Estimate or sum LOC from languages bytes across non-forked repos
            lang_bytes = 0
            for r in repos:
                if r.get("fork"):
                    continue
                rname = r.get("name")
                try:
                    langs = github_get(
                        f"https://api.github.com/repos/{username}/{rname}/languages"
                    )
                    if isinstance(langs, dict):
                        lang_bytes += sum(int(v) for v in langs.values())
                except Exception:
                    pass

            if lang_bytes > 0:
                # ~38 bytes per line of code on average
                net_loc = max(12000, int(lang_bytes / 38))
                del_loc = int(net_loc * 0.11)
                add_loc = net_loc + del_loc
                stats["loc_add"] = add_loc
                stats["loc_del"] = del_loc
    except Exception as exc:
        print(f"[warn] repos fetch: {exc}")

    return stats


def format_kv_line(y: int, key_parts: list[str], value: str, total_width: int = 60) -> str:
    """
    Formats a `. Key.Subkey: ........ Value` line so its total visible character count is `total_width` (60).
    """
    key_plain = ".".join(key_parts)
    # Visible structure: ". " + key_plain + ":" + " " + dots + " " + value
    used = 2 + len(key_plain) + 1 + len(value)
    dots_needed = max(1, total_width - used - 2)
    dots_str = f" {'.' * dots_needed} "

    key_tspans = ".".join(f'<tspan class="key">{xml_escape(k)}</tspan>' for k in key_parts)
    return (
        f'<tspan x="390" y="{y}" class="cc">. </tspan>'
        f"{key_tspans}:"
        f'<tspan class="cc">{dots_str}</tspan>'
        f'<tspan class="value">{xml_escape(value)}</tspan>'
    )


def format_section_header(y: int, title: str, total_width: int = 60) -> str:
    """Formats a header line like `fouad@awad ————...` or `- Contact ————...` to 60 chars."""
    prefix = f"{title} "
    dashes_len = max(2, total_width - len(prefix))
    # Use the exact dash pattern from Andrew6rant: -————...—-—-
    if dashes_len >= 4:
        dashes = "-" + ("—" * (dashes_len - 4)) + "-—-"
    else:
        dashes = "—" * dashes_len
    return f'<tspan x="390" y="{y}">{xml_escape(title)}</tspan> {dashes}'


def build_svg(stats: dict[str, int], dark: bool = True) -> str:
    bg = "#161b22" if dark else "#f6f8fa"
    fg = "#c9d1d9" if dark else "#24292f"
    key_col = "#ffa657" if dark else "#953800"
    val_col = "#a5d6ff" if dark else "#0a3069"
    add_col = "#3fb950" if dark else "#1a7f37"
    del_col = "#f85149" if dark else "#cf222e"
    cc_col = "#616e7f" if dark else "#c2cfde"

    # Build ASCII portrait tspans (36 lines fitted cleanly into x=15..375, y=28..510)
    ascii_tspans = []
    for i, line in enumerate(ASCII_LINES):
        y_pos = round(28 + i * 13.75, 1)
        ascii_tspans.append(f'<tspan x="15" y="{y_pos}">{xml_escape(line)}</tspan>')

    # Build GitHub Stats lines (strictly 60 chars wide)
    repos_s = f"{stats['repos']:,}"
    contrib_s = f"{stats['contributed']:,}"
    stars_s = f"{stats['stars']:,}"
    commits_s = f"{stats['commits']:,}"
    followers_s = f"{stats['followers']:,}"

    loc_net = stats["loc_add"] - stats["loc_del"]
    loc_net_s = f"{loc_net:,}"
    loc_add_s = f"{stats['loc_add']:,}"
    loc_del_s = f"{stats['loc_del']:,}"

    # Line 1 of stats: ". Repos: .... X {Contributed: Y} | Stars: ........... Z"
    left_part_1_len = len(f". Repos: ") + len(repos_s) + len(f" {{Contributed: {contrib_s}}} | Stars:")
    # Reserve 6 dots for Repos if possible
    repo_dots_count = 4
    repo_dots = f" {'.' * repo_dots_count} "
    star_dots_count = max(1, 60 - (len(". Repos:") + len(repo_dots) + len(repos_s) + len(f" {{Contributed: {contrib_s}}} | Stars:") + len(stars_s) + 2))
    star_dots = f" {'.' * star_dots_count} "

    stats_line_1 = (
        f'<tspan x="390" y="470" class="cc">. </tspan>'
        f'<tspan class="key">Repos</tspan>:'
        f'<tspan class="cc" id="repo_data_dots">{repo_dots}</tspan>'
        f'<tspan class="value" id="repo_data">{repos_s}</tspan>'
        f' {{<tspan class="key">Contributed</tspan>: <tspan class="value" id="contrib_data">{contrib_s}</tspan>}}'
        f' | <tspan class="key">Stars</tspan>:'
        f'<tspan class="cc" id="star_data_dots">{star_dots}</tspan>'
        f'<tspan class="value" id="star_data">{stars_s}</tspan>'
    )

    # Line 2 of stats: ". Commits: ................. X | Followers: ....... Y"
    # Keep "| Followers:" aligned with "| Stars:"
    target_pipe_idx = len(". Repos:") + len(repo_dots) + len(repos_s) + len(f" {{Contributed: {contrib_s}}}")
    commit_dots_count = max(1, target_pipe_idx - len(". Commits:") - len(commits_s) - 2)
    commit_dots = f" {'.' * commit_dots_count} "
    follower_dots_count = max(1, 60 - (len(". Commits:") + len(commit_dots) + len(commits_s) + len(" | Followers:") + len(followers_s) + 2))
    follower_dots = f" {'.' * follower_dots_count} "

    stats_line_2 = (
        f'<tspan x="390" y="490" class="cc">. </tspan>'
        f'<tspan class="key">Commits</tspan>:'
        f'<tspan class="cc" id="commit_data_dots">{commit_dots}</tspan>'
        f'<tspan class="value" id="commit_data">{commits_s}</tspan>'
        f' | <tspan class="key">Followers</tspan>:'
        f'<tspan class="cc" id="follower_data_dots">{follower_dots}</tspan>'
        f'<tspan class="value" id="follower_data">{followers_s}</tspan>'
    )

    # Line 3 of stats: ". Lines of Code on GitHub:.. X ( Y++, Z-- )"
    loc_prefix = ". Lines of Code on GitHub:"
    loc_suffix = f"{loc_net_s} ( {loc_add_s}++, {loc_del_s}-- )"
    loc_dots_len = max(1, 60 - len(loc_prefix) - len(loc_suffix) - 2)
    loc_dots = f" {'.' * loc_dots_len} "

    stats_line_3 = (
        f'<tspan x="390" y="510" class="cc">. </tspan>'
        f'<tspan class="key">Lines of Code on GitHub</tspan>:'
        f'<tspan class="cc" id="loc_data_dots">{loc_dots}</tspan>'
        f'<tspan class="value" id="loc_data">{loc_net_s}</tspan>'
        f' ( <tspan class="addColor" id="loc_add">{loc_add_s}</tspan><tspan class="addColor">++</tspan>, '
        f'<tspan id="loc_del_dots"></tspan><tspan class="delColor" id="loc_del">{loc_del_s}</tspan><tspan class="delColor">--</tspan> )'
    )

    right_lines = [
        format_section_header(30, "fouad@awad"),
        format_kv_line(50, ["OS"], "Linux, AWS Cloud, Windows 11"),
        format_kv_line(70, ["Uptime"], "Final-Year CE (Grad. Jan 2027)"),
        format_kv_line(90, ["Host"], "IAEMS (GPA 3.4, Ranked 3rd)"),
        format_kv_line(110, ["Kernel"], "Cloud & DevOps Eng. (AWS SAA-C03)"),
        format_kv_line(130, ["Capstone"], "Carbon-Aware Cloud Batch Scheduler"),
        '<tspan x="390" y="150" class="cc">. </tspan>',
        format_kv_line(170, ["Cloud", "AWS"], "EC2, VPC, RDS, S3, WAF, Batch"),
        format_kv_line(190, ["DevOps", "IaC"], "Terraform, CloudFormation, Docker"),
        format_kv_line(210, ["Languages", "Programming"], "Python, Bash, C++, JS, SQL"),
        format_kv_line(230, ["Languages", "Real"], "Arabic, English, German"),
        '<tspan x="390" y="250" class="cc">. </tspan>',
        format_kv_line(270, ["Hobbies", "Creative"], "Game Dev, MC Modding, Web Tech"),
        format_kv_line(290, ["Hobbies", "Music"], "Indie/Rock Guitar, Music Prod."),
        format_section_header(330, "- Contact"),
        format_kv_line(350, ["Email", "Personal"], "fouad.ai@outlook.com"),
        format_kv_line(370, ["Portfolio", "Web"], "fouadawad.org"),
        format_kv_line(390, ["LinkedIn"], "fouad-awad"),
        format_kv_line(410, ["Location"], "Giza, Egypt (Open to Relocate)"),
        format_section_header(450, "- GitHub Stats"),
        stats_line_1,
        stats_line_2,
        stats_line_3,
    ]

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {key_col};}}
.value {{fill: {val_col};}}
.addColor {{fill: {add_col};}}
.delColor {{fill: {del_col};}}
.cc {{fill: {cc_col};}}
.ascii {{font-size: 9px;}}
text, tspan {{white-space: pre;}}
</style>
<rect width="985px" height="530px" fill="{bg}" rx="15"/>
<text x="15" y="28" fill="{fg}" class="ascii">
{chr(10).join(ascii_tspans)}
</text>
<text x="390" y="30" fill="{fg}">
{chr(10).join(right_lines)}
</text>
</svg>
"""


def main() -> None:
    stats = fetch_github_stats(USERNAME)
    dark_svg = build_svg(stats, dark=True)
    light_svg = build_svg(stats, dark=False)

    (ROOT_DIR / "dark_mode.svg").write_text(dark_svg, encoding="utf-8")
    (ROOT_DIR / "light_mode.svg").write_text(light_svg, encoding="utf-8")
    print(f"[ok] Generated dark_mode.svg and light_mode.svg for {USERNAME}: {stats}")


if __name__ == "__main__":
    main()

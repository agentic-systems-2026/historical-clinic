"""Disposable component: Export audit log.

Renders the redacted conversation log as an HTML transcript.
Input:  redacted_log (list[tuple[str, str]]) of (speaker, text), already
        de-identified; out_dir (str or Path) for the file
Output: path to the HTML file (Path)

The file name holds only a timestamp, never patient text. Patient lines are
shown in red; bracketed system notes (such as similarity scores) in small type.
"""
import datetime
import html
from pathlib import Path

STYLE = """
body { font-family: Arial, sans-serif; color: #222; margin: 2em; max-width: 50em; }
h1 { font-size: 1.3em; }
.speaker { font-weight: bold; margin-top: 1em; }
.patient { color: #c00; }
.note { font-size: 0.85em; color: #555; margin-left: 1.5em; }
"""


def export_audit_log(redacted_log, out_dir="audit_logs"):
    if not isinstance(redacted_log, list):
        raise ValueError("redacted_log must be a list of (speaker, text) pairs")
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="UTF-8">',
        "<title>Historical clinic audit log</title>",
        f"<style>{STYLE}</style></head><body>",
        "<h1>Historical clinic audit log (de-identified)</h1>",
    ]
    for speaker, text in redacted_log:
        speaker_text, body_text = html.escape(str(speaker)), html.escape(str(text))
        if str(text).startswith("["):
            lines.append(f'<div class="note">{body_text}</div>')
            continue
        css = "patient" if str(speaker).lower() == "patient" else ""
        lines.append(f'<div class="speaker {css}">{speaker_text}:</div>')
        lines.append(f'<div class="{css}">{body_text}</div>')
    lines.append("</body></html>")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    path = out_dir / f"audit_log_{stamp}.html"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

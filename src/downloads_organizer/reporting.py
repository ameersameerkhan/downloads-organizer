"""Generate a local HTML report without mutating organised files."""

from collections import Counter
from pathlib import Path

from jinja2 import Environment, select_autoescape


def generate_html_report(report_data, output_path):
    template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Downloads Organizer — Organization Report</title>
  <style>
    :root { color-scheme:light; --ink:#171717; --muted:#696969; --line:#e7e4de; --paper:#f7f5f0; --card:#fff; --accent:#3c5d50; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--paper); color:var(--ink); font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    main { width:min(1120px,calc(100% - 40px)); margin:auto; padding:64px 0 72px; }
    header { display:flex; justify-content:space-between; gap:32px; align-items:flex-end; padding-bottom:30px; border-bottom:1px solid var(--line); }
    .eyebrow { margin:0 0 8px; font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); }
    h1 { margin:0; font-size:clamp(32px,5vw,56px); line-height:1; letter-spacing:-.045em; font-weight:650; }
    .local { max-width:340px; margin:0; color:var(--muted); text-align:right; }
    .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:1px; margin:28px 0 36px; background:var(--line); border:1px solid var(--line); }
    .metric { background:var(--card); padding:22px; min-height:112px; }
    .metric strong { display:block; font-size:30px; line-height:1; letter-spacing:-.03em; margin-bottom:12px; }
    .metric span { color:var(--muted); }
    .grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
    .panel,.table-wrap { background:var(--card); border:1px solid var(--line); padding:24px; }
    .panel h2,.table-wrap h2 { margin:0 0 22px; font-size:17px; }
    .bar-row { display:grid; grid-template-columns:110px 1fr 42px; gap:12px; align-items:center; margin:15px 0; }
    .bar-label { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .track { height:9px; background:#ece9e3; overflow:hidden; }
    .fill { height:100%; background:var(--accent); min-width:2px; }
    .bar-value { text-align:right; color:var(--muted); font-variant-numeric:tabular-nums; }
    .table-wrap { margin-top:24px; overflow:auto; }
    table { width:100%; border-collapse:collapse; min-width:680px; }
    th,td { padding:12px 10px; border-bottom:1px solid var(--line); text-align:left; }
    th { font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600; }
    td:nth-child(2),td:nth-child(3) { color:var(--muted); }
    .details { display:grid; grid-template-columns:1fr 1fr; gap:14px 36px; margin-top:24px; padding:24px; border-top:1px solid var(--line); color:var(--muted); }
    .details b { color:var(--ink); font-weight:600; }
    footer { margin-top:34px; color:var(--muted); font-size:13px; }
    @media (max-width:800px) { .metrics,.grid { grid-template-columns:1fr 1fr; } header { align-items:flex-start; flex-direction:column; } .local { text-align:left; } }
    @media (max-width:520px) { main { width:min(100% - 24px,1120px); padding-top:32px; } .metrics,.grid,.details { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<main>
  <header>
    <div><p class="eyebrow">Downloads Organizer</p><h1>Organisation report</h1></div>
    <p class="local">Generated locally. No file contents or report data are uploaded by Downloads Organizer.</p>
  </header>
  <section class="metrics">
    <div class="metric"><strong>{{ metadata.total_files_processed }}</strong><span>Files organised</span></div>
    <div class="metric"><strong>{{ "%.2f"|format(metadata.total_size_mb) }} MB</strong><span>Data processed</span></div>
    <div class="metric"><strong>{{ category_rows|length }}</strong><span>Categories</span></div>
    <div class="metric"><strong>{{ metadata.duplicates_found }}</strong><span>Duplicates detected</span></div>
  </section>
  <section class="grid">
    <div class="panel"><h2>Category distribution</h2>{% for row in category_rows %}<div class="bar-row"><div class="bar-label">{{ row.label }}</div><div class="track"><div class="fill" style="width:{{ row.percent }}%"></div></div><div class="bar-value">{{ row.count }}</div></div>{% endfor %}</div>
    <div class="panel"><h2>Files by modification month</h2>{% for row in month_rows %}<div class="bar-row"><div class="bar-label">{{ row.label }}</div><div class="track"><div class="fill" style="width:{{ row.percent }}%"></div></div><div class="bar-value">{{ row.count }}</div></div>{% endfor %}</div>
  </section>
  <section class="table-wrap"><h2>Largest files</h2><table><thead><tr><th>File</th><th>Size</th><th>Category</th><th>Destination</th></tr></thead><tbody>{% for file in largest_files %}<tr><td>{{ file.name }}</td><td>{{ "%.2f"|format(file.size_mb) }} MB</td><td>{{ file.category }}</td><td>{{ file.new_path }}</td></tr>{% endfor %}</tbody></table></section>
  <section class="table-wrap"><h2>Oldest files</h2><table><thead><tr><th>File</th><th>Modified</th><th>Category</th><th>Destination</th></tr></thead><tbody>{% for file in oldest_files %}<tr><td>{{ file.name }}</td><td>{{ file.modified[:10] }}</td><td>{{ file.category }}</td><td>{{ file.new_path }}</td></tr>{% endfor %}</tbody></table></section>
  <section class="details"><div><b>Source</b><br>{{ metadata.source_folder }}</div><div><b>Destination</b><br>{{ metadata.target_folder }}</div><div><b>Duplicates removed</b><br>{{ metadata.duplicates_deleted }}</div><div><b>Run duration</b><br>{{ "%.2f"|format(metadata.duration_seconds) }} seconds</div></section>
  <footer>Fully local report. No scripts, remote assets, telemetry, or network requests are required.</footer>
</main>
</body>
</html>
"""

    all_files = report_data.get("all_files", [])
    metadata = {
        "total_files_processed": len(all_files),
        "total_size_mb": sum(file.get("size_mb", 0) for file in all_files),
        "duplicates_found": 0,
        "duplicates_deleted": 0,
        "source_folder": "",
        "target_folder": "",
        "duration_seconds": 0,
        **report_data.get("metadata", {}),
    }

    category_counts = report_data.get("category_stats", {})
    category_max = max(category_counts.values(), default=1)
    category_rows = [
        {"label": label, "count": count, "percent": round(count / category_max * 100, 2)}
        for label, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    month_counts = Counter(file["modified"][:7] for file in all_files)
    month_max = max(month_counts.values(), default=1)
    month_rows = [
        {"label": month, "count": count, "percent": round(count / month_max * 100, 2)}
        for month, count in sorted(month_counts.items())
    ]

    environment = Environment(autoescape=select_autoescape(default=True))
    html = environment.from_string(template_str).render(
        metadata=metadata,
        category_rows=category_rows,
        month_rows=month_rows,
        largest_files=report_data.get("largest_files", [])[:10],
        oldest_files=report_data.get("oldest_files", [])[:10],
    )
    Path(output_path).write_text(html)

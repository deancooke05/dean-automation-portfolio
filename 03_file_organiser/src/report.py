from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from .engine import OrganisationPlan


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def build_html_report(plan: OrganisationPlan, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = datetime.fromisoformat(plan.created_at).strftime("%d %B %Y at %H:%M UTC")
    category_rows = "".join(f"<tr><td>{escape(category)}</td><td>{count}</td></tr>" for category, count in plan.categories.items())
    action_rows = "".join(
        f"<tr><td>{escape(Path(action.source).name)}</td><td>{escape(action.category)}</td>"
        f"<td>{action.size_bytes:,}</td><td><span class='status'>{escape(action.status)}</span></td>"
        f"<td>{'Renamed safely' if action.collision else '—'}</td></tr>" for action in plan.actions
    )
    html = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>Smart File Organiser Report</title><style>
:root{{--navy:#142b3a;--gold:#b79a62;--pearl:#f8fafb;--steel:#50697a;--line:#d8e0e5}}
*{{box-sizing:border-box}}body{{margin:0;background:#eef2f4;color:#1b2730;font:15px Aptos,Inter,Arial,sans-serif}}
.hero{{background:var(--navy);color:white;padding:54px 7vw 46px}}.brand{{display:flex;align-items:center;gap:13px;color:var(--gold)}}.brand svg{{width:42px;height:42px;flex:0 0 auto}}.brand b,.brand small{{display:block;letter-spacing:.16em}}.brand b{{font-size:12px;color:white}}.brand small{{font-size:8px;margin-top:4px;color:#c8d3da}}
h1{{font-size:42px;margin:16px 0 8px;font-weight:600}}.subtitle{{color:#c8d3da;font-size:17px}}
main{{max-width:1180px;margin:-22px auto 50px;padding:0 24px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.card,.panel{{background:white;border:1px solid var(--line);border-radius:14px;padding:24px}}.label{{color:var(--steel);font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase}}
.value{{font-size:30px;color:var(--navy);font-weight:700;margin-top:10px}}.grid{{display:grid;grid-template-columns:1fr 2fr;gap:18px;margin-top:18px}}
h2{{font-size:18px;color:var(--navy);margin:0 0 18px}}table{{width:100%;border-collapse:collapse}}th{{background:var(--navy);color:white;text-align:left;padding:12px}}
td{{padding:12px;border-bottom:1px solid var(--line)}}.status{{color:#2f6f55;font-weight:700}}footer{{color:var(--steel);text-align:right;margin-top:18px}}
@media(max-width:800px){{.cards,.grid{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.cards,.grid{{grid-template-columns:1fr}}}}
</style></head><body><header class='hero'><div class='brand'><svg viewBox='0 0 64 64' aria-hidden='true'><path d='M32 3 61 32 32 61 3 32Z' fill='none' stroke='currentColor' stroke-width='2.4'/><path d='M41 20A16 16 0 1 0 41 44' fill='none' stroke='currentColor' stroke-width='3.4' stroke-linecap='round'/></svg><span><b>COOKE</b><small>AUTOMATION SYSTEMS</small></span></div><h1>Smart File Organiser</h1>
<div class='subtitle'>Organisation plan • {escape(plan.mode.title())} mode • {escape(generated)}</div></header><main>
<section class='cards'><div class='card'><div class='label'>Files reviewed</div><div class='value'>{len(plan.actions)}</div></div>
<div class='card'><div class='label'>Data volume</div><div class='value'>{format_size(plan.total_bytes)}</div></div>
<div class='card'><div class='label'>Categories</div><div class='value'>{len(plan.categories)}</div></div>
<div class='card'><div class='label'>Collisions handled</div><div class='value'>{sum(a.collision for a in plan.actions)}</div></div></section>
<section class='grid'><div class='panel'><h2>Category summary</h2><table><tr><th>Category</th><th>Files</th></tr>{category_rows}</table></div>
<div class='panel'><h2>Audit trail</h2><table><tr><th>File</th><th>Category</th><th>Bytes</th><th>Status</th><th>Safety</th></tr>{action_rows}</table></div></section>
<footer>Generated locally by Cooke Automation Systems • Product 003 v1.1</footer></main></body></html>"""
    path.write_text(html, encoding="utf-8")
    return path

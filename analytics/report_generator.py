import os
import datetime
import webbrowser
from storage.db import (
    get_connection, fatigue_to_focus_score,
    get_streak_count, get_today_deep_work_stats
)


def generate_executive_html_report() -> str:
    """Generates a standalone executive HTML report and returns its absolute path."""
    os.makedirs("data/reports", exist_ok=True)
    report_filename = f"CognitiveAI_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.abspath(os.path.join("data", "reports", report_filename))

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Total lifetime / 7-day stats
    cursor.execute("""
        SELECT COALESCE(SUM(duration_sec), 0), COUNT(*), COALESCE(AVG(fatigue_score), 0)
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
    """)
    w_row = cursor.fetchone()
    weekly_sec = w_row[0] or 0
    weekly_hours = weekly_sec / 3600.0
    weekly_sessions = w_row[1] or 0
    avg_fatigue = w_row[2] or 0.0
    avg_focus = fatigue_to_focus_score(avg_fatigue)

    # 2. Category distribution
    cursor.execute("""
        SELECT category, SUM(duration_sec) as total
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
        GROUP BY category
        ORDER BY total DESC
    """)
    cat_rows = cursor.fetchall()
    total_cat_sec = sum(r[1] for r in cat_rows) or 1

    # 3. Top apps
    cursor.execute("""
        SELECT app_name, category, SUM(duration_sec) as total, AVG(fatigue_score)
        FROM sessions
        WHERE timestamp >= datetime('now', '-7 days', 'localtime')
        GROUP BY app_name
        ORDER BY total DESC
        LIMIT 6
    """)
    app_rows = cursor.fetchall()

    conn.close()

    streak = get_streak_count()
    today_stats = get_today_deep_work_stats()
    today_deep_h = today_stats.get("deep_work_sec", 0) / 3600.0
    today_distract = today_stats.get("distraction_count", 0)

    # Build category bars HTML
    cat_html = ""
    colors = ["#7EE7C6", "#7B7DFF", "#FBBF24", "#FF7A90", "#93C5FD", "#C084FC"]
    for i, (cat, dur) in enumerate(cat_rows):
        pct = int((dur / total_cat_sec) * 100)
        h = dur // 3600
        m = (dur % 3600) // 60
        c = colors[i % len(colors)]
        cat_html += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                <span><strong>{cat}</strong></span>
                <span>{h}h {m}m ({pct}%)</span>
            </div>
            <div style="background: rgba(255,255,255,0.06); height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: {c}; width: {pct}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
        """

    # Build app table rows HTML
    app_html = ""
    for r in app_rows:
        aname = r[0]
        acat = r[1]
        adur = r[2]
        afoc = fatigue_to_focus_score(r[3])
        ah = adur // 3600
        am = (adur % 3600) // 60
        app_html += f"""
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
            <td style="padding: 12px 14px; font-weight: 600;">{aname}</td>
            <td style="padding: 12px 14px; color: #A0A5B5;">{acat}</td>
            <td style="padding: 12px 14px;">{ah}h {am}m</td>
            <td style="padding: 12px 14px; color: {'#7EE7C6' if afoc >= 75 else '#FBBF24'}; font-weight: 700;">{afoc}%</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cognitive AI — Executive Telemetry Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #080A0F;
            color: #F4F6FB;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 24px;
            margin-bottom: 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .brand {{
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(135deg, #7EE7C6, #7B7DFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .card {{
            background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
        }}
        .card-title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: rgba(224,229,240,0.6);
            margin-bottom: 8px;
        }}
        .card-val {{
            font-size: 28px;
            font-weight: 850;
            color: #FFFFFF;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            color: #FFFFFF;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}
        th {{
            padding: 10px 14px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: rgba(224,229,240,0.5);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="brand">Cognitive AI</div>
                <div style="color: #A0A5B5; font-size: 13px; margin-top: 4px;">Executive Productivity & Wellbeing Audit</div>
            </div>
            <div style="text-align: right; color: #7B7DFF; font-size: 13px; font-weight: 600;">
                Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">7-Day Tracked Time</div>
                <div class="card-val">{weekly_hours:.1f}h</div>
            </div>
            <div class="card">
                <div class="card-title">Stamina Focus Score</div>
                <div class="card-val" style="color: #7EE7C6;">{avg_focus}%</div>
            </div>
            <div class="card">
                <div class="card-title">Active Focus Streak</div>
                <div class="card-val" style="color: #FBBF24;">{streak} Days</div>
            </div>
            <div class="card">
                <div class="card-title">Today's Deep Work</div>
                <div class="card-val" style="color: #7B7DFF;">{today_deep_h:.1f}h</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px;">
            <div class="card">
                <div class="section-title">Attention Allocation by Category</div>
                {cat_html}
            </div>
            <div class="card">
                <div class="section-title">Cognitive Hygiene Recommendations</div>
                <ul style="color: #E2E2E8; font-size: 14px; line-height: 1.8; padding-left: 20px;">
                    <li><strong>Peak Flow Window:</strong> Guard your morning 9:00 AM - 11:30 AM block for complex architecture and coding tasks.</li>
                    <li><strong>Context Switching Tax:</strong> Today accumulated {today_distract} distraction switches. Maintain minimum 25-minute sprints.</li>
                    <li><strong>Circadian Pacing:</strong> Schedule light reviews and administrative communication between 1:30 PM - 3:30 PM.</li>
                    <li><strong>Active Recovery:</strong> Take a 5-minute movement or 4-7-8 breathing break every 90 minutes of continuous screen work.</li>
                </ul>
            </div>
        </div>

        <div class="card">
            <div class="section-title">Primary Tool Telemetry</div>
            <table>
                <thead>
                    <tr>
                        <th>Application</th>
                        <th>Classified Category</th>
                        <th>Duration</th>
                        <th>Focus Stamina</th>
                    </tr>
                </thead>
                <tbody>
                    {app_html}
                </tbody>
            </table>
        </div>

        <div style="text-align: center; margin-top: 40px; color: rgba(224,229,240,0.4); font-size: 12px;">
            Cognitive AI • 100% Local-First & On-Device Telemetry • Confidential
        </div>
    </div>
</body>
</html>"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return report_path

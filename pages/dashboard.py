from dash import html, dcc, Input, Output, callback, no_update
import plotly.graph_objects as go
from sqlalchemy import func, select, case, desc
from models import SessionLocal, Student, Course, Session as DBSession, Attendance, Grade
import time
from datetime import datetime, timedelta

# ── Cache ───────────────────────────────────────────────────────────────────
_stats_cache = {"data": None, "ts": 0}
_CACHE_TTL = 30  # Reduced to 30s for better interactivity

def get_stats(force_refresh=False):
    now = time.monotonic()
    if not force_refresh and _stats_cache["data"] and (now - _stats_cache["ts"]) < _CACHE_TTL:
        return _stats_cache["data"]

    db = SessionLocal()
    try:
        # ── KPIs ─────────────────────────────────────────────────────────────
        total_students = db.query(func.count(Student.id)).scalar() or 0
        total_courses  = db.query(func.count(Course.id)).scalar() or 0
        avg_grade = db.query(func.avg(Grade.note)).scalar() or 0
        
        # Attendance Rate (Total non-absent / Total)
        total_att = db.query(func.count(Attendance.id)).scalar() or 0
        presents = db.query(func.count(Attendance.id)).filter(Attendance.absent == False).scalar() or 0
        att_rate = (presents / total_att * 100) if total_att > 0 else 100

        # ── Grade Distribution (Optimized SQL) ──────────────────────────────
        # SQL CASE allows us to get the histogram bins in one query
        bins = [
            case((Grade.note < 5, "0-5"), else_=None),
            case(((Grade.note >= 5) & (Grade.note < 10), "5-10"), else_=None),
            case(((Grade.note >= 10) & (Grade.note < 12), "10-12"), else_=None),
            case(((Grade.note >= 12) & (Grade.note < 14), "12-14"), else_=None),
            case(((Grade.note >= 14) & (Grade.note < 16), "14-16"), else_=None),
            case((Grade.note >= 16, "16-20"), else_=None),
        ]
        # This is a slightly complex query, let's stick to a simpler count group by floor
        # or just fetch values if N is small, but let's do it robustly.
        dist_query = db.query(
            case(
                (Grade.note < 10, "Insuffisant"),
                (Grade.note < 12, "Passable"),
                (Grade.note < 14, "Assez Bien"),
                (Grade.note < 16, "Bien"),
                else_="Très Bien"
            ).label("level"),
            func.count(Grade.id)
        ).group_by("level").all()
        grade_dist = {row[0]: row[1] for row in dist_query}

        # ── Attendance Trend (Last 30 days) ──────────────────────────────────
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        trend_query = db.query(
            DBSession.date,
            func.count(Attendance.id).label("total"),
            func.sum(case((Attendance.absent == False, 1), else_=0)).label("presents")
        ).join(Attendance).filter(DBSession.date >= thirty_days_ago).group_by(DBSession.date).order_by(DBSession.date).all()
        
        att_trend = [
            {"date": row[0].strftime("%d/%m"), "rate": (row[2]/row[1]*100) if row[1] > 0 else 100}
            for row in trend_query
        ]

        # ── Performance par Matière ──────────────────────────────────────────
        course_perf = db.query(
            Course.code,
            func.avg(Grade.note).label("avg")
        ).join(Grade).group_by(Course.code).all()
        subject_perf = [{"code": r[0], "avg": round(r[1], 1)} for r in course_perf]

        # ── Course Progression ───────────────────────────────────────────────
        heures_row = dict(db.query(DBSession.course_id, func.sum(DBSession.duree)).group_by(DBSession.course_id).all())
        courses_raw = db.query(Course).limit(4).all()
        progression = []
        for c in courses_raw:
            h = heures_row.get(c.id, 0.0) or 0.0
            prog = min(100, (h / c.volume_horaire * 100)) if c.volume_horaire else 0
            progression.append({"code": c.code, "libelle": c.libelle, "pct": round(prog), "current": h, "total": c.volume_horaire})

        # ── Recent Activity ──────────────────────────────────────────────────
        recent_sessions = db.query(DBSession).order_by(DBSession.date.desc()).limit(3).all()
        activity = [
            {"theme": s.theme, "date": s.date.strftime("%d %b"), "course": s.course.code if s.course else "???"}
            for s in recent_sessions
        ]

        data = {
            "kpis": {
                "students": total_students,
                "courses": total_courses,
                "attendance": round(att_rate, 1),
                "avg_grade": round(avg_grade, 2)
            },
            "grade_dist": grade_dist,
            "att_trend": att_trend,
            "subject_perf": subject_perf,
            "progression": progression,
            "activity": activity
        }
        _stats_cache["data"] = data
        _stats_cache["ts"] = now
        return data
    finally:
        db.close()

# ── Charts ───────────────────────────────────────────────────────────────────

def make_dist_chart(data):
    # Labels in order
    labels = ["Insuffisant", "Passable", "Assez Bien", "Bien", "Très Bien"]
    values = [data.get(l, 0) for l in labels]
    colors = ["#f87171", "#fbbf24", "#60a5fa", "#34d399", "#10b981"]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=values, textposition="auto",
        marker_line_width=0,
    ))
    fig.update_layout(
        margin=dict(t=10, b=20, l=10, r=10),
        height=220,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#64748b")),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=10, color="#64748b")),
    )
    return fig

def make_trend_chart(trend_data):
    if not trend_data:
        trend_data = [{"date": "N/A", "rate": 100}]
    
    x = [d["date"] for d in trend_data]
    y = [d["rate"] for d in trend_data]
    
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="lines+markers",
        line=dict(color="#3b82f6", width=3, shape="spline"),
        marker=dict(size=6, color="#fff", line=dict(color="#3b82f6", width=2)),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.1)"
    ))
    fig.update_layout(
         margin=dict(t=5, b=5, l=5, r=5),
         height=180,
         plot_bgcolor="rgba(0,0,0,0)",
         paper_bgcolor="rgba(0,0,0,0)",
         xaxis=dict(showgrid=False, visible=False),
         yaxis=dict(showgrid=False, visible=False, range=[0, 105]),
    )
    return fig

def make_subject_chart(subject_data):
    if not subject_data:
        return go.Figure()
    
    codes = [d["code"] for d in subject_data]
    avgs = [d["avg"] for d in subject_data]
    
    fig = go.Figure(go.Bar(
        y=codes, x=avgs, orientation="h",
        marker_color="rgba(139, 92, 246, 0.7)",
        marker_line_width=0,
        width=0.6
    ))
    fig.update_layout(
        margin=dict(t=5, b=20, l=60, r=10),
        height=220,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 20], gridcolor="#f1f5f9", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#475569")),
    )
    return fig

# ── Layout ───────────────────────────────────────────────────────────────────

def layout():
    return html.Div([
        dcc.Interval(id="dash-refresh", interval=100, max_intervals=1),
        
        # Header / Search row or similar can go here, but let's jump to KPIs
        html.Div(id="dash-content", children=layout_skeleton())
    ])

def layout_skeleton():
    return html.Div([
        # KPI ROW
        html.Div(className="dash-kpi-grid", style={
            "display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
            "gap": "1rem", "marginBottom": "1.5rem"
        }, children=[_kpi_skeleton() for _ in range(4)]),
        
        # CHARTS ROW
        html.Div(style={"display": "grid", "gridTemplateColumns": "1.5fr 1fr", "gap": "1.5rem", "marginBottom": "1.5rem"}, children=[
             html.Div(className="sga-card", children=[_skeleton(h="300px")]),
             html.Div(className="sga-card", children=[_skeleton(h="300px")]),
        ])
    ])

# ── Callbacks ────────────────────────────────────────────────────────────────

@callback(
    Output("dash-content", "children"),
    Input("dash-refresh", "n_intervals")
)
def refresh_dashboard(n):
    if n is None: return no_update
    s = get_stats()
    
    return html.Div([
        # KPIs
        html.Div(className="dash-kpi-grid", style={
            "display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
            "gap": "1rem", "marginBottom": "1.5rem"
        }, children=[
            _kpi("group", s["kpis"]["students"], "Étudiants", "+12%", "blue"),
            _kpi("library_books", s["kpis"]["courses"], "Cours", "Stable", "purple"),
            _kpi("event_available", f"{s['kpis']['attendance']}%", "Présences", "-0.5%", "green"),
            _kpi("school", f"{s['kpis']['avg_grade']}", "Moyenne", "+0.2", "amber"),
        ]),

        # MAIN CHARTS
        html.Div(style={"display": "grid", "gridTemplateColumns": "1.2fr 1fr", "gap": "1.25rem", "marginBottom": "1.5rem"}, children=[
            # Attendance Trend
            html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "1rem"}, children=[
                    html.H3("Tendance des Présences (30j)", style={"margin": 0, "fontSize": "1rem", "fontWeight": "700"}),
                    html.Span("Dernière mise à jour: Aujourd'hui", style={"fontSize": ".75rem", "color": "#94a3b8"})
                ]),
                dcc.Graph(figure=make_trend_chart(s["att_trend"]), config={"displayModeBar": False}),
            ]),
            # Quick Actions / Info
            html.Div(className="sga-card", style={"padding": "1.25rem", "background": "linear-gradient(135deg, #1e293b, #0f172a)", "color": "white"}, children=[
                html.H3("Actions Rapides", style={"margin": "0 0 1.25rem 0", "fontSize": "1rem", "color": "white"}),
                html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".75rem"}, children=[
                    _dash_action("add_circle", "Nouvelle Séance", "/sessions", "rgba(59, 130, 246, 0.2)"),
                    _dash_action("upload", "Importer Notes", "/grades", "rgba(139, 92, 246, 0.2)"),
                    _dash_action("person_add", "Inscrire Étudiant", "/students", "rgba(16, 185, 129, 0.2)"),
                ])
            ]),
        ]),

        # SECONDARY CHARTS
        html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))", "gap": "1.25rem", "marginBottom": "1.5rem"}, children=[
            # Distribution
            html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
                html.H3("Répartition des Notes", style={"margin": "0 0 1rem 0", "fontSize": "1rem", "fontWeight": "700"}),
                dcc.Graph(figure=make_dist_chart(s["grade_dist"]), config={"displayModeBar": False}),
            ]),
            # Subject Perf
            html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
                html.H3("Performance par Matière", style={"margin": "0 0 1rem 0", "fontSize": "1rem", "fontWeight": "700"}),
                dcc.Graph(figure=make_subject_chart(s["subject_perf"]), config={"displayModeBar": False}),
            ]),
            # Progress
            html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
                html.H3("Progression des Modules", style={"margin": "0 0 1rem 0", "fontSize": "1rem", "fontWeight": "700"}),
                html.Div([
                    _prog_row(p) for p in s["progression"]
                ])
            ]),
        ]),

        # BOTTOM ROW: RECENT ACTIVITY
        html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
            html.H3("Dernières Séances Enregistrées", style={"margin": "0 0 1rem 0", "fontSize": "1rem", "fontWeight": "700"}),
            html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(280px, 1fr))", "gap": "1rem"}, children=[
                _activity_item(a) for a in s["activity"]
            ])
        ])
    ], className="animate-fade-up")

# ── Helper UI Components ─────────────────────────────────────────────────────

def _kpi(icon, value, label, trend, color_key):
    colors = {
        "blue": {"bg": "#eff6ff", "text": "#3b82f6"},
        "purple": {"bg": "#f5f3ff", "text": "#8b5cf6"},
        "green": {"bg": "#ecfdf5", "text": "#10b981"},
        "amber": {"bg": "#fffbeb", "text": "#f59e0b"},
    }
    c = colors[color_key]
    return html.Div(className="sga-card", style={"padding": "1.25rem", "display": "flex", "alignItems": "center", "gap": "1rem"}, children=[
        html.Div(className="material-symbols-outlined", children=icon, style={
            "fontSize": "1.5rem", "padding": ".75rem", "borderRadius": "12px",
            "background": c["bg"], "color": c["text"]
        }),
        html.Div([
            html.Div(label, style={"fontSize": ".75rem", "color": "#94a3b8", "fontWeight": "600", "textTransform": "uppercase"}),
            html.Div(str(value), style={"fontSize": "1.5rem", "fontWeight": "800", "color": "#1e293b"}),
            html.Div(trend, style={"fontSize": ".7rem", "color": "#10b981" if "+" in trend else "#ef4444", "fontWeight": "700"})
        ])
    ])

def _dash_action(icon, label, href, bg):
    return html.A(href=href, style={"textDecoration": "none", "color": "white"}, children=[
        html.Div(style={
            "display": "flex", "alignItems": "center", "gap": ".75rem",
            "padding": ".85rem", "borderRadius": "12px", "background": bg,
            "border": "1px solid rgba(255,255,255,0.05)", "transition": "transform 0.2s"
        }, children=[
            html.Span(icon, className="material-symbols-outlined", style={"fontSize": "1.25rem"}),
            html.Span(label, style={"fontSize": ".85rem", "fontWeight": "600"}),
            html.Span("arrow_forward", className="material-symbols-outlined", style={"marginLeft": "auto", "fontSize": "1rem", "opacity": 0.5})
        ])
    ])

def _prog_row(p):
    return html.Div(style={"marginBottom": "1rem"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "fontSize": ".8rem", "marginBottom": ".25rem"}, children=[
            html.Span(f"{p['code']} - {p['libelle'][:20]}...", style={"fontWeight": "600"}),
            html.Span(f"{p['pct']}%", style={"fontWeight": "700", "color": "#3b82f6"})
        ]),
        html.Div(style={"height": "6px", "background": "#f1f5f9", "borderRadius": "3px", "overflow": "hidden"}, children=[
            html.Div(style={"width": f"{p['pct']}%", "height": "100%", "background": "#3b82f6", "borderRadius": "3px"})
        ])
    ])

def _activity_item(a):
    return html.Div(style={"display": "flex", "gap": ".75rem", "alignItems": "center", "padding": ".75rem", "border": "1px solid #f1f5f9", "borderRadius": "12px"}, children=[
        html.Div(a["date"], style={
            "display": "flex", "flexDirection": "column", "alignItems": "center", "padding": ".4rem .6rem",
            "background": "#f8fafc", "borderRadius": "8px", "fontSize": ".7rem", "fontWeight": "700", "minWidth": "50px"
        }),
        html.Div([
            html.Div(a["theme"][:40] + "...", style={"fontSize": ".85rem", "fontWeight": "600", "color": "#1e293b"}),
            html.Div(a["course"], style={"fontSize": ".75rem", "color": "#64748b"})
        ])
    ])

# ── Skeleton Components ──────────────────────────────────────────────────────

def _skeleton(h="40px", w="100%", radius="12px"):
    return html.Div(className="skeleton", style={"height": h, "width": w, "borderRadius": radius})

def _kpi_skeleton():
    return html.Div(className="sga-card", style={"padding": "1.25rem", "height": "90px"}, children=[
        _skeleton(h="100%", w="100%")
    ])

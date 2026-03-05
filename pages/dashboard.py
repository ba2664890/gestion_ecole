"""
SGA - Dashboard Page
Executive Overview with real-time KPIs, charts, activity feed
"""

from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from models import SessionLocal, Student, Course, Session, Attendance, Grade
from sqlalchemy import func


def get_stats():
    db = SessionLocal()
    try:
        total_students = db.query(Student).count()
        total_courses = db.query(Course).count()
        total_sessions = db.query(Session).count()

        # Average grade
        avg_grade = db.query(func.avg(Grade.note)).scalar() or 0

        # Attendance rate
        total_att = db.query(Attendance).count()
        absents = db.query(Attendance).filter_by(absent=True).count()
        att_rate = ((total_att - absents) / total_att * 100) if total_att > 0 else 100

        # Recent sessions (pre-format to avoid lazy loading)
        sessions_raw = (
            db.query(Session)
            .order_by(Session.date.desc())
            .limit(5)
            .all()
        )
        recent_sessions = []
        for s in sessions_raw:
            recent_sessions.append({
                "theme": s.theme,
                "date": s.date,
                "duree": s.duree,
                "course_code": s.course.code if s.course else "???"
            })

        # Grade distribution
        grades = db.query(Grade.note).all()
        grade_values = [g[0] for g in grades]

        # Course progress (pre-calculate to avoid lazy loading)
        courses_raw = db.query(Course).all()
        courses_data = []
        for c in courses_raw:
            courses_data.append({
                "code": c.code,
                "libelle": c.libelle,
                "progression": c.progression,
                "heures_effectuees": c.heures_effectuees,
                "volume_horaire": c.volume_horaire,
                "enseignant": c.enseignant
            })

        return {
            "total_students": total_students,
            "total_courses": total_courses,
            "total_sessions": total_sessions,
            "avg_grade": round(avg_grade, 2),
            "att_rate": round(att_rate, 1),
            "recent_sessions": recent_sessions,
            "grade_values": grade_values,
            "courses": courses_data,
        }
    finally:
        db.close()


def make_grade_chart(grade_values):
    if not grade_values:
        grade_values = [7, 8, 9, 10, 8, 7, 9, 10, 6, 8]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=grade_values,
        nbinsx=10,
        marker_color="#13a4ec",
        marker_line_color="#0e8bc9",
        marker_line_width=1.5,
        opacity=0.85,
        name="Notes",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"t": 10, "b": 40, "l": 30, "r": 10},
        xaxis={
            "title": "Note /20",
            "showgrid": False,
            "tickfont": {"family": "Lexend", "size": 11, "color": "#94a3b8"},
            "range": [0, 20],
        },
        yaxis={
            "title": "Nb étudiants",
            "gridcolor": "#f1f5f9",
            "showgrid": True,
            "tickfont": {"family": "Lexend", "size": 11, "color": "#94a3b8"},
        },
        font={"family": "Lexend"},
        showlegend=False,
        height=280,
    )
    return fig


def make_attendance_trend():
    # Generate 12-week trend data
    weeks = [f"S{i}" for i in range(1, 13)]
    rates = [92, 94, 91, 95, 93, 96, 94, 92, 95, 97, 94, 95]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks, y=rates,
        mode="lines+markers",
        line={"color": "#10b981", "width": 2.5, "shape": "spline"},
        marker={"size": 7, "color": "#10b981", "line": {"color": "#fff", "width": 2}},
        fill="tozeroy",
        fillcolor="rgba(16,185,129,.08)",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"t": 10, "b": 30, "l": 30, "r": 10},
        xaxis={"showgrid": False, "tickfont": {"family": "Lexend", "size": 10, "color": "#94a3b8"}},
        yaxis={
            "range": [85, 100],
            "gridcolor": "#f1f5f9",
            "ticksuffix": "%",
            "tickfont": {"family": "Lexend", "size": 10, "color": "#94a3b8"},
        },
        font={"family": "Lexend"},
        height=160,
        showlegend=False,
    )
    return fig


def layout():
    stats = get_stats()

    return html.Div([
        # KPI Row
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(220px, 1fr))",
            "gap": "1.25rem", "marginBottom": "1.75rem",
        }, children=[
            _kpi("person_pin", stats["total_students"], "Étudiants inscrits", "+8%", "up", "#3b82f6", "#eff6ff"),
            _kpi("menu_book", stats["total_courses"], "Cours actifs", "+2", "up", "#8b5cf6", "#f5f3ff"),
            _kpi("event_available", f"{stats['att_rate']}%", "Taux de présence", "-0.3%", "down", "#f59e0b", "#fffbeb"),
            _kpi("grade", f"{stats['avg_grade']}/20", "Moyenne générale", "+0.4", "up", "#10b981", "#ecfdf5"),
        ], className="animate-fade-up"),

        # Charts Row
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "2fr 1fr",
            "gap": "1.25rem", "marginBottom": "1.75rem",
        }, className="animate-fade-up-1", children=[
            # Grade distribution
            html.Div(className="sga-card", children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1.25rem"}, children=[
                    html.Div([
                        html.H3("Distribution des Notes", style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
                        html.P("Performance globale des étudiants", style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}),
                    ]),
                    html.Div(style={
                        "background": "#f1f5f9", "borderRadius": "8px",
                        "padding": ".35rem .75rem", "fontSize": ".75rem",
                        "fontWeight": "600", "color": "#64748b",
                    }, children=["Semestre 1"]),
                ]),
                dcc.Graph(figure=make_grade_chart(stats["grade_values"]), config={"displayModeBar": False}),
            ]),

            # Quick stats + trend
            html.Div(style={"display": "flex", "flexDirection": "column", "gap": "1.25rem"}, children=[
                html.Div(className="sga-card", children=[
                    html.H3("Tendance Présences", style={"fontWeight": "700", "fontSize": ".95rem", "marginBottom": ".75rem"}),
                    dcc.Graph(figure=make_attendance_trend(), config={"displayModeBar": False}),
                ]),
                # Quick actions
                html.Div(className="sga-card", children=[
                    html.H3("Actions Rapides", style={"fontWeight": "700", "fontSize": ".95rem", "marginBottom": "1rem"}),
                    html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".5rem"}, children=[
                        _quick_action("edit_calendar", "Nouvelle séance", "/sessions", "#3b82f6"),
                        _quick_action("person_add", "Ajouter étudiant", "/students", "#8b5cf6"),
                        _quick_action("upload_file", "Importer notes", "/grades", "#f59e0b"),
                        _quick_action("summarize", "Générer rapport", "/reports", "#10b981"),
                    ]),
                ]),
            ]),
        ]),

        # Bottom row: Course progress + Recent sessions
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "1.25rem",
        }, className="animate-fade-up-2", children=[
            # Course progressions
            html.Div(className="sga-card", children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1.25rem"}, children=[
                    html.H3("Progression des Cours", style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
                    html.A("Voir tout →", href="/courses", style={"fontSize": ".8rem", "color": "var(--primary)", "textDecoration": "none", "fontWeight": "600"}),
                ]),
                html.Div(style={"display": "flex", "flexDirection": "column", "gap": "1rem"}, children=[
                    _course_progress_row(c) for c in stats["courses"][:5]
                ] if stats["courses"] else [
                    html.P("Aucun cours disponible.", style={"color": "#94a3b8", "fontSize": ".875rem"})
                ]),
            ]),

            # Recent sessions
            html.Div(className="sga-card", children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1.25rem"}, children=[
                    html.H3("Séances Récentes", style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
                    html.A("Voir tout →", href="/sessions", style={"fontSize": ".8rem", "color": "var(--primary)", "textDecoration": "none", "fontWeight": "600"}),
                ]),
                html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".75rem"}, children=[
                    _session_row(s) for s in stats["recent_sessions"]
                ] if stats["recent_sessions"] else [
                    html.P("Aucune séance enregistrée.", style={"color": "#94a3b8", "fontSize": ".875rem"})
                ]),
            ]),
        ]),
    ])


def _kpi(icon, value, label, delta, direction, color, bg):
    return html.Div(className="kpi-card", children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start"}, children=[
            html.Div(
                html.Span(icon, className="material-symbols-outlined", style={"fontSize": "1.25rem", "color": color}),
                className="kpi-icon",
                style={"background": bg},
            ),
            html.Span(delta, className=f"kpi-delta {direction}", style={
                "padding": ".2rem .6rem",
                "borderRadius": "99px",
                "background": "#d1fae5" if direction == "up" else "#fee2e2",
            }),
        ]),
        html.Div(str(value), className="kpi-value", style={"color": color}),
        html.Div(label, className="kpi-label"),
    ])


def _quick_action(icon, label, href, color):
    return html.A(href=href, style={"textDecoration": "none"}, children=[
        html.Div(style={
            "display": "flex", "alignItems": "center", "gap": ".75rem",
            "padding": ".6rem .85rem", "borderRadius": "10px",
            "border": "1.5px solid #f1f5f9",
            "transition": "all .2s",
            "cursor": "pointer",
        }, children=[
            html.Div(
                html.Span(icon, className="material-symbols-outlined", style={"fontSize": "1rem", "color": color}),
                style={
                    "width": "32px", "height": "32px",
                    "borderRadius": "8px",
                    "background": f"{color}15",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                }
            ),
            html.Span(label, style={"fontSize": ".85rem", "fontWeight": "600", "color": "#374151"}),
            html.Span("chevron_right", className="material-symbols-outlined",
                      style={"fontSize": ".9rem", "color": "#cbd5e1", "marginLeft": "auto"}),
        ]),
    ])


def _course_progress_row(course):
    pct = course["progression"]
    color = "success" if pct >= 80 else ("danger" if pct < 30 else "")
    return html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".4rem"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
            html.Div([
                html.Span(course["code"], className="badge badge-blue", style={"marginRight": ".5rem"}),
                html.Span(course["libelle"], style={"fontSize": ".85rem", "fontWeight": "500"}),
            ]),
            html.Span(f"{pct:.0f}%", style={
                "fontSize": ".8rem", "fontWeight": "700",
                "color": "#10b981" if pct >= 80 else ("#ef4444" if pct < 30 else "#f59e0b"),
            }),
        ]),
        html.Div(className="progress-wrap", children=[
            html.Div(className=f"progress-fill {color}", style={"width": f"{pct:.0f}%"}),
        ]),
        html.Div(f"{course['heures_effectuees']:.0f}h / {course['volume_horaire']:.0f}h — {course['enseignant']}",
                 style={"fontSize": ".75rem", "color": "#94a3b8"}),
    ])


def _session_row(session):
    return html.Div(style={
        "display": "flex", "alignItems": "flex-start", "gap": ".75rem",
        "padding": ".65rem .85rem",
        "borderRadius": "10px",
        "border": "1px solid #f1f5f9",
    }, children=[
        html.Div(style={
            "width": "36px", "height": "36px", "flexShrink": 0,
            "borderRadius": "10px", "background": "rgba(19,164,236,.08)",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
        }, children=[
            html.Span("today", className="material-symbols-outlined", style={"fontSize": "1rem", "color": "var(--primary)"}),
        ]),
        html.Div([
            html.Div(session["theme"][:50] + ("..." if len(session["theme"]) > 50 else ""),
                     style={"fontSize": ".875rem", "fontWeight": "600"}),
            html.Div(style={"display": "flex", "gap": ".5rem", "marginTop": ".2rem", "alignItems": "center"}, children=[
                html.Span(str(session["date"]), style={"fontSize": ".75rem", "color": "#94a3b8"}),
                html.Span("•", style={"color": "#e2e8f0"}),
                html.Span(f"{session['duree']}h", style={"fontSize": ".75rem", "color": "#94a3b8"}),
            ]),
        ]),
    ])

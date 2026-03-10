"""
SGA - Analytics Page
Advanced charts: grade distribution, attendance trends, course comparisons
"""

from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
from models import SessionLocal, Student, Course, Grade, Attendance, Session
from sqlalchemy import func
from collections import defaultdict


CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font={"family": "Lexend", "color": "#374151"},
    margin={"t": 20, "b": 40, "l": 40, "r": 20},
    xaxis={"gridcolor": "#f1f5f9", "showgrid": True},
    yaxis={"gridcolor": "#f1f5f9", "showgrid": True},
    legend={"bgcolor": "rgba(0,0,0,0)"},
    height=320,
)

PRIMARY = "#6366f1"
COLORS = ["#6366f1", "#8b5cf6", "#10b981", "#f59e0b", "#f43f5e", "#475569"]


def get_analytics_data():
    db = SessionLocal()
    try:
        # Grades per course
        grades = db.query(Grade).all()
        students = db.query(Student).all()
        courses = db.query(Course).all()

        # Grade distribution
        all_notes = [g.note for g in grades]

        # Per-course averages
        course_avgs = {}
        for c in courses:
            notes = [g.note for g in grades if g.course_id == c.id]
            course_avgs[c.code] = sum(notes) / len(notes) if notes else 0

        # Attendance per session
        sessions = db.query(Session).order_by(Session.date).all()
        att_data = []
        for s in sessions:
            total = len(s.attendances)
            absent = sum(1 for a in s.attendances if a.absent)
            if total > 0:
                att_data.append({
                    "date": str(s.date),
                    "rate": round((total - absent) / total * 100, 1),
                    "course": s.course.code if s.course else "—",
                })

        # Student grade distribution brackets
        brackets = {"0-5": 0, "5-8": 0, "8-10": 0, "10-12": 0, "12-14": 0, "14-16": 0, "16-20": 0}
        for n in all_notes:
            if n < 5: brackets["0-5"] += 1
            elif n < 8: brackets["5-8"] += 1
            elif n < 10: brackets["8-10"] += 1
            elif n < 12: brackets["10-12"] += 1
            elif n < 14: brackets["12-14"] += 1
            elif n < 16: brackets["14-16"] += 1
            else: brackets["16-20"] += 1

        return {
            "all_notes": all_notes,
            "course_avgs": course_avgs,
            "att_data": att_data,
            "brackets": brackets,
            "n_students": len(students),
            "n_courses": len(courses),
            "n_grades": len(grades),
        }
    finally:
        db.close()


def make_histogram(notes):
    if not notes:
        notes = []
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=notes, nbinsx=20,
        marker_color=PRIMARY, marker_line_color="#4f46e5", marker_line_width=1,
        opacity=0.85, name="Étudiants",
        hovertemplate="Note: %{x}<br>Étudiants: %{y}<extra></extra>",
    ))
    # Add normal distribution curve overlay
    if notes:
        import statistics
        mean = statistics.mean(notes)
        std = statistics.stdev(notes) if len(notes) > 1 else 1
        x_range = [i/4 for i in range(0, 81)]
        import math
        y_normal = [
            len(notes) * (1 / (std * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mean) / std) ** 2)
            for x in x_range
        ]
        fig.add_trace(go.Scatter(
            x=x_range, y=y_normal, mode="lines",
            line={"color": "#8b5cf6", "width": 2.5, "dash": "dot"},
            name="Distribution normale", opacity=0.6,
        ))
        # Add mean line
        fig.add_vline(x=mean, line_dash="dash", line_color="#f43f5e",
                      annotation_text=f"Moy: {mean:.1f}", annotation_position="top right")

    layout = {**CHART_LAYOUT, "height": 300}
    layout["xaxis"] = {**layout.get("xaxis", {}), "title": "Note /20", "range": [0, 20]}
    layout["yaxis"] = {**layout.get("yaxis", {}), "title": "Nb étudiants"}
    
    fig.update_layout(
        **layout,
        bargap=0.05,
    )
    return fig


def make_course_comparison(course_avgs):
    if not course_avgs:
        return go.Figure()
    codes = list(course_avgs.keys())
    avgs = list(course_avgs.values())

    colors_list = [PRIMARY if a >= 10 else "#f43f5e" for a in avgs]

    fig = go.Figure(go.Bar(
        x=codes, y=avgs,
        marker_color=colors_list,
        marker_line_color="#fff", marker_line_width=1.5,
        text=[f"{a:.1f}" for a in avgs],
        textposition="outside",
        hovertemplate="%{x}: %{y:.1f}/20<extra></extra>",
    ))
    fig.add_hline(y=10, line_dash="dot", line_color="#f59e0b",
                  annotation_text="Seuil 10/20", annotation_position="right")
    layout = {**CHART_LAYOUT}
    layout["xaxis"] = {**layout.get("xaxis", {}), "title": "Cours", "gridcolor": "rgba(0,0,0,0)"}
    layout["yaxis"] = {**layout.get("yaxis", {}), "title": "Moyenne /20", "range": [0, 21]}
    
    fig.update_layout(
        **layout,
        showlegend=False,
    )
    return fig


def make_attendance_line(att_data):
    if not att_data:
        return go.Figure()

    dates = [d["date"] for d in att_data]
    rates = [d["rate"] for d in att_data]
    courses = [d["course"] for d in att_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=rates,
        mode="lines+markers",
        line={"color": "#10b981", "width": 2.5, "shape": "spline"},
        marker={"size": 8, "color": "#10b981", "line": {"color": "#fff", "width": 2}},
        fill="tozeroy", fillcolor="rgba(16,185,129,.06)",
        name="Taux présence",
        text=courses,
        hovertemplate="Date: %{x}<br>Taux: %{y:.1f}%<br>Cours: %{text}<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dot", line_color="#f59e0b",
                  annotation_text="Seuil 90%", annotation_position="right")
    layout = {**CHART_LAYOUT}
    layout["xaxis"] = {**layout.get("xaxis", {}), "title": "Date"}
    layout["yaxis"] = {**layout.get("yaxis", {}), "title": "Taux (%)", "range": [60, 101], "ticksuffix": "%"}
    
    fig.update_layout(**layout)
    return fig


def make_bracket_pie(brackets):
    labels = list(brackets.keys())
    values = list(brackets.values())
    colors = ["#f43f5e", "#fb7185", "#f59e0b", "#fbbf24", "#34d399", "#10b981", "#059669"]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker={"colors": colors, "line": {"color": "#fff", "width": 2}},
        hole=0.5,
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} étudiant(s)<extra></extra>",
    ))
    # On copie CHART_LAYOUT pour pouvoir modifier la légende et les marges sans conflit
    layout = {**CHART_LAYOUT, "height": 300}
    layout["legend"] = {"orientation": "v", "x": 1.05, "bgcolor": "rgba(0,0,0,0)"}
    layout["margin"] = {"t": 20, "b": 20, "l": 20, "r": 100}
    
    fig.update_layout(
        **layout,
        showlegend=True,
    )
    return fig


def layout():
    data = get_analytics_data()

    return html.Div([
        # Header
        html.Div(style={"marginBottom": "1.5rem"}, className="animate-fade-up", children=[
            html.H2("Analytique Académique", style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
            html.P(f"Analyse de {data['n_grades']} notes · {data['n_students']} étudiants · {data['n_courses']} cours",
                   style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
        ]),

        # Summary stats strip
        html.Div(style={
            "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "1rem", "marginBottom": "1.5rem",
        }, className="animate-fade-up-1", children=[
            _stat_card("Nb de notes saisies", str(data["n_grades"]), "grade", "#6366f1"),
            _stat_card("Moyenne globale",
                       f"{(sum(data['all_notes'])/len(data['all_notes'])):.1f}/20" if data['all_notes'] else "—",
                       "bar_chart", "#8b5cf6"),
            _stat_card("Taux présence moyen",
                       f"{(sum(d['rate'] for d in data['att_data'])/len(data['att_data'])):.1f}%" if data['att_data'] else "—",
                       "event_available", "#10b981"),
            _stat_card("Cours analysés", str(len(data["course_avgs"])), "auto_stories", "#f59e0b"),
        ]),

        # Row 1: Histogram + Pie
        html.Div(style={"display": "grid", "gridTemplateColumns": "3fr 2fr", "gap": "1.25rem", "marginBottom": "1.25rem"}, className="animate-fade-up-2", children=[
            html.Div(className="sga-card", children=[
                html.H3("Distribution des Notes", style={"fontWeight": "700", "fontSize": "1rem", "marginBottom": "1rem"}),
                dcc.Graph(figure=make_histogram(data["all_notes"]), config={"displayModeBar": False}),
            ]),
            html.Div(className="sga-card", children=[
                html.H3("Répartition par Tranche", style={"fontWeight": "700", "fontSize": "1rem", "marginBottom": "1rem"}),
                dcc.Graph(figure=make_bracket_pie(data["brackets"]), config={"displayModeBar": False}),
            ]),
        ]),

        # Row 2: Course comparison + Attendance
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1.25rem"}, className="animate-fade-up-3", children=[
            html.Div(className="sga-card", children=[
                html.H3("Comparaison des Moyennes par Cours", style={"fontWeight": "700", "fontSize": "1rem", "marginBottom": "1rem"}),
                dcc.Graph(figure=make_course_comparison(data["course_avgs"]), config={"displayModeBar": False}),
            ]),
            html.Div(className="sga-card", children=[
                html.H3("Évolution du Taux de Présence", style={"fontWeight": "700", "fontSize": "1rem", "marginBottom": "1rem"}),
                dcc.Graph(figure=make_attendance_line(data["att_data"]), config={"displayModeBar": False}),
            ]),
        ]),
    ])


def _stat_card(label, value, icon, color):
    return html.Div(className="kpi-card", children=[
        html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem"}, children=[
            html.Div(
                html.Span(icon, className="material-symbols-outlined", style={"fontSize": "1.1rem", "color": color}),
                style={"width": "38px", "height": "38px", "borderRadius": "10px",
                       "background": f"{color}15", "display": "flex", "alignItems": "center", "justifyContent": "center"}
            ),
            html.Div([
                html.Div(label, style={"fontSize": ".75rem", "color": "#64748b", "fontWeight": "500"}),
                html.Div(value, style={"fontSize": "1.3rem", "fontWeight": "800", "color": color}),
            ]),
        ]),
    ])

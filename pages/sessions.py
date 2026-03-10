"""
SGA - Sessions & Attendance Page
Digital roll call, session recording, history
"""

from dash import html, dcc, Input, Output, State, callback, no_update, ctx, ALL
import json
from datetime import date
from models import SessionLocal, Session as DBSession, Course, Student, Attendance


def get_courses_options():
    db = SessionLocal()
    try:
        courses = db.query(Course).order_by(Course.libelle).all()
        return [{"label": f"{c.code} – {c.libelle}", "value": c.id} for c in courses]
    finally:
        db.close()


from sqlalchemy.orm import joinedload

def get_sessions_history():
    db = SessionLocal()
    try:
        sessions = db.query(DBSession).options(
            joinedload(DBSession.course),
            joinedload(DBSession.attendances)
        ).order_by(DBSession.date.desc()).limit(30).all()
        
        result = []
        for s in sessions:
            absent_count = sum(1 for a in s.attendances if a.absent)
            total = len(s.attendances)
            result.append({
                "id": s.id,
                "course_code": s.course.code if s.course else "—",
                "course_libelle": s.course.libelle if s.course else "—",
                "date": str(s.date),
                "duree": s.duree,
                "theme": s.theme,
                "absent_count": absent_count,
                "total": total,
            })
        return result
    finally:
        db.close()


def get_students_for_course(course_id):
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        return [{"id": s.id, "name": f"{s.prenom} {s.nom}"} for s in students]
    finally:
        db.close()


def layout():
    course_opts = get_courses_options()
    sessions = get_sessions_history()

    return html.Div([
        # Two-column layout
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1.5fr",
            "gap": "1.5rem",
            "alignItems": "flex-start",
        }, children=[

            # Left: New Session Form
            html.Div(className="animate-fade-up", children=[
                html.Div(className="sga-card", children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.5rem"}, children=[
                        html.Div(style={
                            "width": "40px", "height": "40px", "borderRadius": "10px",
                            "background": "rgba(99,102,241,.1)",
                            "display": "flex", "alignItems": "center", "justifyContent": "center",
                        }, children=[
                            html.Span("edit_calendar", className="material-symbols-outlined",
                                      style={"color": "var(--primary)", "fontSize": "1.2rem"}),
                        ]),
                        html.Div([
                            html.H3("Nouvelle Séance", style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
                            html.P("Enregistrer une séance de cours", style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}),
                        ]),
                    ]),

                    # Course selection
                    html.Div(style={"marginBottom": "1rem"}, children=[
                        html.Label("Cours *", className="sga-label"),
                        dcc.Dropdown(
                            id="session-course-select",
                            options=course_opts,
                            placeholder="Sélectionner un cours...",
                            style={"fontSize": ".875rem"},
                        ),
                    ]),

                    # Date + Duration
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1rem", "marginBottom": "1rem"}, children=[
                        html.Div([
                            html.Label("Date de séance *", className="sga-label"),
                            dcc.DatePickerSingle(id="session-date", date=date.today(),
                                      className="sga-input", style={"width": "100%"}),
                        ]),
                        html.Div([
                            html.Label("Durée (heures) *", className="sga-label"),
                            dcc.Input(id="session-duree", type="number", value=1.5, min=0.5, max=8, step=0.5,
                                      className="sga-input", style={"width": "100%"}),
                        ]),
                    ]),

                    # Theme
                    html.Div(style={"marginBottom": "1.25rem"}, children=[
                        html.Label("Thème / Contenu abordé *", className="sga-label"),
                        dcc.Textarea(
                            id="session-theme",
                            placeholder="Décrivez le contenu pédagogique de la séance...",
                            className="sga-textarea",
                            style={"width": "100%", "height": "80px", "resize": "vertical"},
                        ),
                    ]),

                    # Separator
                    html.Div(style={
                        "display": "flex", "alignItems": "center", "gap": ".75rem",
                        "margin": "1.25rem 0", "color": "#94a3b8",
                    }, children=[
                        html.Div(style={"flex": 1, "height": "1px", "background": "#f1f5f9"}),
                        html.Span("Appel Numérique", style={"fontSize": ".75rem", "fontWeight": "700", "whiteSpace": "nowrap"}),
                        html.Div(style={"flex": 1, "height": "1px", "background": "#f1f5f9"}),
                    ]),

                    # Student attendance checklist
                    html.Div(id="attendance-checklist-container", children=[
                        html.P("← Sélectionnez un cours pour afficher la liste des étudiants",
                               style={"color": "#94a3b8", "fontSize": ".875rem", "textAlign": "center", "padding": "1.5rem"}),
                    ]),

                    html.Div(id="session-form-feedback"),

                    html.Button([
                        html.Span("save", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                        "Enregistrer la Séance",
                    ], id="save-session-btn", n_clicks=0, className="btn-primary",
                    style={"width": "100%", "justifyContent": "center", "marginTop": "1.25rem", "padding": ".85rem"}),
                ]),
            ]),

            # Right: History
            html.Div(className="animate-fade-up-1", children=[
                html.Div(className="sga-card", style={"padding": 0, "overflow": "hidden"}, children=[
                    html.Div(style={
                        "padding": "1.25rem 1.5rem",
                        "borderBottom": "1px solid #f1f5f9",
                        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                    }, children=[
                        html.Div([
                            html.H3("Historique des Séances", style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
                            html.P(f"{len(sessions)} séances enregistrées", style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}),
                        ]),
                        html.Div(style={"display": "flex", "gap": ".5rem"}, children=[
                            dcc.Dropdown(
                                id="history-filter-course",
                                options=[{"label": "Tous les cours", "value": "all"}] + [
                                    {"label": o["label"], "value": o["value"]} for o in get_courses_options()
                                ],
                                value="all",
                                clearable=False,
                                style={"minWidth": "200px", "fontSize": ".8rem"},
                            ),
                        ]),
                    ]),
                    html.Div(id="sessions-history-table", children=[_render_history(sessions)]),
                ]),
            ]),
        ]),

        # Store for absent student IDs
        dcc.Store(id="absent-students-store", data=[]),
    ])


def _render_checklist(students, absent_ids=None):
    absent_ids = absent_ids or []
    if not students:
        return html.P("Aucun étudiant inscrit.", style={"color": "#94a3b8", "fontSize": ".875rem"})

    items = []
    for s in students:
        is_absent = s["id"] in absent_ids
        items.append(
            html.Div(
                id={"type": "student-check", "index": s["id"]},
                className=f"custom-checklist-item {'checked' if is_absent else ''}",
                n_clicks=0,
                children=[
                    html.Div(style={
                        "width": "20px", "height": "20px", "borderRadius": "5px",
                        "border": f"2px solid {'#f43f5e' if is_absent else '#e2e8f0'}",
                        "background": "#fff1f2" if is_absent else "#fff",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "flexShrink": 0, "transition": "all .15s",
                    }, children=[
                        html.Span("close", className="material-symbols-outlined",
                                  style={"fontSize": ".85rem", "color": "#ef4444", "display": "block" if is_absent else "none"}),
                    ]),
                    html.Span(s["name"], style={"fontSize": ".875rem", "fontWeight": "500"}),
                    html.Span("Absent", style={
                        "marginLeft": "auto", "fontSize": ".7rem", "fontWeight": "700",
                        "color": "#f43f5e", "display": "block" if is_absent else "none",
                    }),
                ],
            )
        )
    return html.Div([
        html.Div(style={
            "display": "flex", "justifyContent": "space-between",
            "marginBottom": ".75rem", "alignItems": "center",
        }, children=[
            html.Span(f"{len(students)} étudiants", style={"fontSize": ".8rem", "color": "#64748b", "fontWeight": "600"}),
            html.Span(f"{len(absent_ids)} absent(s)", style={"fontSize": ".8rem", "color": "#f43f5e", "fontWeight": "700"}),
        ]),
        html.Div(className="custom-checklist", style={"maxHeight": "280px", "overflowY": "auto"}, children=items),
        html.P("Cliquez pour marquer absent", style={"fontSize": ".7rem", "color": "#94a3b8", "marginTop": ".75rem", "textAlign": "center"}),
    ])


def _render_history(sessions, filter_course=None):
    if filter_course and filter_course != "all":
        # filter_course is course_id
        pass  # done via DB filter

    if not sessions:
        return html.Div(style={"padding": "2.5rem", "textAlign": "center", "color": "#94a3b8"}, children=[
            html.Span("history", className="material-symbols-outlined", style={"fontSize": "2.5rem", "display": "block"}),
            html.P("Aucune séance enregistrée.", style={"marginTop": ".75rem"}),
        ])

    return html.Div(style={"maxHeight": "600px", "overflowY": "auto"}, children=[
        html.Table(className="sga-table", children=[
            html.Thead(html.Tr([
                html.Th("Cours"),
                html.Th("Date"),
                html.Th("Durée"),
                html.Th("Thème"),
                html.Th("Présences"),
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(html.Div([
                        html.Span(s["course_code"], className="badge badge-blue"),
                    ])),
                    html.Td(s["date"], style={"fontSize": ".8rem", "color": "#64748b", "whiteSpace": "nowrap"}),
                    html.Td(f"{s['duree']}h", style={"fontSize": ".8rem", "fontWeight": "600"}),
                    html.Td(html.Span(s["theme"][:45] + ("…" if len(s["theme"]) > 45 else ""),
                                     style={"fontSize": ".8rem"})),
                    html.Td(html.Span(
                        f"{s['total'] - s['absent_count']}/{s['total']}",
                        style={
                            "fontSize": ".8rem", "fontWeight": "700",
                            "color": "#f43f5e" if s["absent_count"] > 0 else "#10b981",
                        }
                    )),
                ])
                for s in sessions
            ]),
        ]),
    ])


# ─── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("attendance-checklist-container", "children"),
    Output("absent-students-store", "data"),
    Input("session-course-select", "value"),
)
def load_students(course_id):
    if not course_id:
        return html.P("← Sélectionnez un cours", style={"color": "#94a3b8", "fontSize": ".875rem", "textAlign": "center", "padding": "1.5rem"}), []
    students = get_students_for_course(course_id)
    return _render_checklist(students, []), []


@callback(
    Output({"type": "student-check", "index": ALL}, "className"),
    Output({"type": "student-check", "index": ALL}, "children"),
    Output("absent-students-store", "data", allow_duplicate=True),
    Input({"type": "student-check", "index": ALL}, "n_clicks"),
    State({"type": "student-check", "index": ALL}, "id"),
    State("absent-students-store", "data"),
    prevent_initial_call=True,
)
def toggle_absent(n_clicks_list, ids, absent_ids):
    absent_ids = absent_ids or []
    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update, no_update

    student_id = triggered["index"]
    if student_id in absent_ids:
        absent_ids = [x for x in absent_ids if x != student_id]
    else:
        absent_ids = absent_ids + [student_id]

    classnames = []
    children_list = []
    for id_obj in ids:
        sid = id_obj["index"]
        is_absent = sid in absent_ids
        classnames.append(f"custom-checklist-item {'checked' if is_absent else ''}")
        children_list.append([
            html.Div(style={
                "width": "20px", "height": "20px", "borderRadius": "5px",
                "border": f"2px solid {'#ef4444' if is_absent else '#e2e8f0'}",
                "background": "#fee2e2" if is_absent else "#fff",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "flexShrink": 0,
            }, children=[
                html.Span("close", className="material-symbols-outlined",
                          style={"fontSize": ".85rem", "color": "#ef4444", "display": "block" if is_absent else "none"}),
            ]),
            html.Span(f"ID: {sid}", style={"fontSize": ".875rem", "fontWeight": "500"}),
            html.Span("Absent", style={
                "marginLeft": "auto", "fontSize": ".7rem", "fontWeight": "700",
                "color": "#ef4444", "display": "block" if is_absent else "none",
            }),
        ])

    return classnames, children_list, absent_ids


@callback(
    Output("session-form-feedback", "children"),
    Output("sessions-history-table", "children", allow_duplicate=True),
    Input("save-session-btn", "n_clicks"),
    State("session-course-select", "value"),
    State("session-date", "date"),
    State("session-duree", "value"),
    State("session-theme", "value"),
    State("absent-students-store", "data"),
    prevent_initial_call=True,
)
def save_session(n, course_id, sess_date, duree, theme, absent_ids):
    if not n:
        return no_update, no_update
    if not course_id or not sess_date or not theme:
        return html.Div("Veuillez remplir tous les champs obligatoires.", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update

    db = SessionLocal()
    try:
        from datetime import date as dt_date
        new_session = DBSession(
            course_id=course_id,
            date=dt_date.fromisoformat(sess_date),
            duree=float(duree or 1.5),
            theme=theme,
        )
        db.add(new_session)
        db.flush()

        # Record attendance for all students
        all_students = db.query(Student).all()
        for s in all_students:
            att = Attendance(
                session_id=new_session.id,
                student_id=s.id,
                absent=s.id in (absent_ids or []),
            )
            db.add(att)

        db.commit()
        feedback = html.Div("✓ Séance enregistrée avec succès.", style={"color": "#10b981", "fontSize": ".875rem", "fontWeight": "600"})
    except Exception as e:
        db.rollback()
        feedback = html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"})
    finally:
        db.close()

    return feedback, _render_history(get_sessions_history())


@callback(
    Output("sessions-history-table", "children"),
    Input("history-filter-course", "value"),
)
def filter_history(course_filter):
    db = SessionLocal()
    try:
        q = db.query(DBSession).order_by(DBSession.date.desc())
        if course_filter and course_filter != "all":
            q = q.filter_by(course_id=int(course_filter))
        sessions = q.limit(30).all()
        result = []
        for s in sessions:
            absent_count = sum(1 for a in s.attendances if a.absent)
            total = len(s.attendances)
            result.append({
                "id": s.id,
                "course_code": s.course.code if s.course else "—",
                "course_libelle": s.course.libelle if s.course else "—",
                "date": str(s.date),
                "duree": s.duree,
                "theme": s.theme,
                "absent_count": absent_count,
                "total": total,
            })
        return _render_history(result)
    finally:
        db.close()

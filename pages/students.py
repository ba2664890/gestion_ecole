"""
SGA - Students Page
CRUD for students + individual dashboard + grade/attendance overview
"""

from dash import html, dcc, Input, Output, State, callback, no_update, ctx
import pandas as pd
from datetime import date
from models import SessionLocal, Student, Attendance, Grade, Session, Course
from sqlalchemy import func


# ─── Helpers ────────────────────────────────────────────────────────────────────
def get_students():
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.nom).all()
        result = []
        for s in students:
            # Absence rate
            total_att = db.query(Attendance).join(Attendance.session).filter(Attendance.student_id == s.id).count()
            absences = db.query(Attendance).filter_by(student_id=s.id, absent=True).count()
            abs_rate = (absences / total_att * 100) if total_att > 0 else 0

            # Average grade
            avg = db.query(func.avg(Grade.note)).filter_by(student_id=s.id).scalar() or 0

            result.append({
                "id": s.id, "nom": s.nom, "prenom": s.prenom,
                "email": s.email,
                "date_naissance": str(s.date_naissance) if s.date_naissance else "—",
                "abs_rate": round(abs_rate, 1),
                "avg_grade": round(avg, 2),
            })
        return result
    finally:
        db.close()


def layout():
    students = get_students()
    return html.Div([
        # Header actions
        html.Div(style={
            "display": "flex", "justifyContent": "space-between", "alignItems": "center",
            "marginBottom": "1.5rem",
        }, className="animate-fade-up", children=[
            html.Div([
                html.H2("Étudiants", style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
                html.P(f"{len(students)} étudiants inscrits", style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
            ]),
            html.Div(style={"display": "flex", "gap": ".75rem"}, children=[
                html.Button([
                    html.Span("upload_file", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                    "Importer Excel",
                ], id="open-import-modal", className="btn-secondary", n_clicks=0),
                html.Button([
                    html.Span("person_add", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                    "Nouvel Étudiant",
                ], id="open-add-student-modal", className="btn-primary", n_clicks=0),
            ]),
        ]),

        # Search + filter bar
        html.Div(className="sga-card animate-fade-up-1", style={"marginBottom": "1.25rem", "padding": "1rem 1.25rem"}, children=[
            html.Div(style={"display": "flex", "gap": "1rem", "alignItems": "center"}, children=[
                html.Div(style={"position": "relative", "flex": 1}, children=[
                    html.Span("search", className="material-symbols-outlined", style={
                        "position": "absolute", "left": "12px", "top": "50%",
                        "transform": "translateY(-50%)", "color": "#94a3b8", "fontSize": "1rem",
                    }),
                    dcc.Input(id="student-search", placeholder="Rechercher un étudiant...",
                              className="sga-input", style={"paddingLeft": "2.5rem", "width": "100%"},
                              debounce=True),
                ]),
                html.Div(style={"color": "#64748b", "fontSize": ".8rem", "fontWeight": "600", "whiteSpace": "nowrap"}, children=[
                    html.Span(id="student-count-label", children=f"{len(students)} résultats"),
                ]),
            ]),
        ]),

        # Students table
        html.Div(className="sga-card animate-fade-up-2", style={"padding": 0, "overflow": "hidden"}, children=[
            html.Div(id="students-table-container", children=[_render_table(students)]),
        ]),

        # Modal: Add/Edit Student
        html.Div(id="student-modal-overlay", style={"display": "none"}, children=[
            html.Div(style={
                "position": "fixed", "inset": 0, "background": "rgba(0,0,0,.4)",
                "zIndex": 1000, "display": "flex", "alignItems": "center", "justifyContent": "center",
            }, id="student-modal-backdrop", children=[
                html.Div(className="sga-card animate-fade-up", style={
                    "width": "100%", "maxWidth": "520px",
                    "boxShadow": "0 20px 60px rgba(0,0,0,.15)",
                }, children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1.5rem"}, children=[
                        html.H3(id="modal-student-title", children="Nouvel Étudiant", style={"fontWeight": "700", "fontSize": "1.1rem", "margin": 0}),
                        html.Button("✕", id="close-student-modal", n_clicks=0, style={
                            "background": "none", "border": "none", "fontSize": "1.2rem",
                            "cursor": "pointer", "color": "#64748b",
                        }),
                    ]),
                    dcc.Store(id="editing-student-id"),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1rem"}, children=[
                        html.Div([html.Label("Nom", className="sga-label"),
                                  dcc.Input(id="s-nom", placeholder="Nom de famille", className="sga-input")]),
                        html.Div([html.Label("Prénom", className="sga-label"),
                                  dcc.Input(id="s-prenom", placeholder="Prénom", className="sga-input")]),
                    ]),
                    html.Div(style={"marginTop": "1rem"}, children=[
                        html.Label("Email académique", className="sga-label"),
                        dcc.Input(id="s-email", placeholder="email@etablissement.edu", className="sga-input", style={"width": "100%"}),
                    ]),
                    html.Div(style={"marginTop": "1rem"}, children=[
                        html.Label("Date de naissance", className="sga-label"),
                        dcc.Input(id="s-dob", type="date", className="sga-input", style={"width": "100%"}),
                    ]),
                    html.Div(id="student-form-feedback", style={"marginTop": "1rem"}),
                    html.Div(style={"display": "flex", "gap": ".75rem", "marginTop": "1.5rem", "justifyContent": "flex-end"}, children=[
                        html.Button("Annuler", id="cancel-student-btn", n_clicks=0, className="btn-secondary"),
                        html.Button("Enregistrer", id="save-student-btn", n_clicks=0, className="btn-primary"),
                    ]),
                ]),
            ]),
        ]),

        # Delete confirmation
        dcc.Store(id="delete-student-id"),
        html.Div(id="delete-confirm-overlay", style={"display": "none"}, children=[
            html.Div(style={
                "position": "fixed", "inset": 0, "background": "rgba(0,0,0,.4)",
                "zIndex": 1001, "display": "flex", "alignItems": "center", "justifyContent": "center",
            }, children=[
                html.Div(className="sga-card animate-fade-up", style={"maxWidth": "400px", "textAlign": "center"}, children=[
                    html.Div(style={
                        "width": "56px", "height": "56px", "borderRadius": "50%",
                        "background": "#fee2e2", "display": "flex", "alignItems": "center",
                        "justifyContent": "center", "margin": "0 auto 1rem",
                    }, children=[html.Span("delete", className="material-symbols-outlined", style={"color": "#ef4444", "fontSize": "1.5rem"})]),
                    html.H3("Supprimer l'étudiant ?", style={"fontWeight": "700", "marginBottom": ".5rem"}),
                    html.P("Cette action est irréversible. Toutes les données associées seront supprimées.", style={"color": "#64748b", "fontSize": ".875rem", "marginBottom": "1.5rem"}),
                    html.Div(style={"display": "flex", "gap": ".75rem", "justifyContent": "center"}, children=[
                        html.Button("Annuler", id="cancel-delete-btn", n_clicks=0, className="btn-secondary"),
                        html.Button("Supprimer", id="confirm-delete-btn", n_clicks=0, className="btn-danger"),
                    ]),
                ]),
            ]),
        ]),

        # Notification
        html.Div(id="student-notification"),
    ])


def _render_table(students, search=""):
    if search:
        search = search.lower()
        students = [s for s in students if search in s["nom"].lower() or search in s["prenom"].lower() or search in s["email"].lower()]

    if not students:
        return html.Div(style={"padding": "3rem", "textAlign": "center", "color": "#94a3b8"}, children=[
            html.Span("person_search", className="material-symbols-outlined", style={"fontSize": "3rem", "display": "block", "marginBottom": "1rem"}),
            html.P("Aucun étudiant trouvé."),
        ])

    def grade_color(g):
        if g >= 14: return "#10b981"
        if g >= 10: return "#f59e0b"
        return "#ef4444"

    return html.Table(className="sga-table", style={"width": "100%"}, children=[
        html.Thead(html.Tr([
            html.Th("Étudiant"),
            html.Th("Email"),
            html.Th("Naissance"),
            html.Th("Taux Absences"),
            html.Th("Moyenne"),
            html.Th("Actions", style={"textAlign": "right"}),
        ])),
        html.Tbody([
            html.Tr([
                html.Td(html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem"}, children=[
                    html.Div(f"{s['prenom'][0]}{s['nom'][0]}", style={
                        "width": "36px", "height": "36px", "borderRadius": "50%",
                        "background": "var(--primary)", "color": "#fff",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "fontSize": ".75rem", "fontWeight": "700", "flexShrink": 0,
                    }),
                    html.Div([
                        html.Div(f"{s['prenom']} {s['nom']}", style={"fontWeight": "600", "fontSize": ".875rem"}),
                        html.Div(f"ID: {s['id']}", style={"fontSize": ".75rem", "color": "#94a3b8"}),
                    ]),
                ])),
                html.Td(html.Span(s["email"], style={"fontSize": ".825rem", "color": "#64748b"})),
                html.Td(s["date_naissance"], style={"fontSize": ".825rem", "color": "#64748b"}),
                html.Td(html.Div([
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": ".5rem"}, children=[
                        html.Div(className="progress-wrap", style={"flex": 1, "height": "6px"}, children=[
                            html.Div(className=f"progress-fill {'danger' if s['abs_rate'] > 20 else ''}",
                                     style={"width": f"{min(s['abs_rate'], 100)}%",
                                            "background": "#ef4444" if s["abs_rate"] > 20 else "#f59e0b" if s["abs_rate"] > 10 else "#10b981"}),
                        ]),
                        html.Span(f"{s['abs_rate']}%", style={"fontSize": ".75rem", "fontWeight": "600",
                                                                "color": "#ef4444" if s["abs_rate"] > 20 else "#64748b"}),
                    ]),
                ])),
                html.Td(html.Span(f"{s['avg_grade']}/20", style={
                    "fontWeight": "700", "fontSize": ".875rem",
                    "color": grade_color(s["avg_grade"]),
                })),
                html.Td(html.Div(style={"display": "flex", "gap": ".5rem", "justifyContent": "flex-end"}, children=[
                    html.Button(
                        html.Span("edit", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                        id={"type": "edit-student-btn", "index": s["id"]},
                        n_clicks=0,
                        style={
                            "padding": ".4rem", "background": "#f1f5f9", "border": "none",
                            "borderRadius": "8px", "cursor": "pointer", "color": "#64748b",
                        },
                    ),
                    html.Button(
                        html.Span("delete", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                        id={"type": "delete-student-btn", "index": s["id"]},
                        n_clicks=0,
                        style={
                            "padding": ".4rem", "background": "#fef2f2", "border": "none",
                            "borderRadius": "8px", "cursor": "pointer", "color": "#ef4444",
                        },
                    ),
                ])),
            ])
            for s in students
        ]),
    ])


# ─── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("students-table-container", "children"),
    Output("student-count-label", "children"),
    Input("student-search", "value"),
)
def filter_students(search):
    students = get_students()
    search = search or ""
    if search:
        sl = search.lower()
        filtered = [s for s in students if sl in s["nom"].lower() or sl in s["prenom"].lower() or sl in s["email"].lower()]
    else:
        filtered = students
    return _render_table(filtered), f"{len(filtered)} résultat(s)"


@callback(
    Output("student-modal-overlay", "style"),
    Output("editing-student-id", "data"),
    Output("s-nom", "value"),
    Output("s-prenom", "value"),
    Output("s-email", "value"),
    Output("s-dob", "value"),
    Output("modal-student-title", "children"),
    Input("open-add-student-modal", "n_clicks"),
    Input("close-student-modal", "n_clicks"),
    Input("cancel-student-btn", "n_clicks"),
    Input("save-student-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(open_n, close_n, cancel_n, save_n):
    tid = ctx.triggered_id
    if tid == "open-add-student-modal":
        return {"display": "block"}, None, "", "", "", "", "Nouvel Étudiant"
    return {"display": "none"}, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("student-form-feedback", "children"),
    Output("students-table-container", "children", allow_duplicate=True),
    Input("save-student-btn", "n_clicks"),
    State("s-nom", "value"),
    State("s-prenom", "value"),
    State("s-email", "value"),
    State("s-dob", "value"),
    State("editing-student-id", "data"),
    prevent_initial_call=True,
)
def save_student(n, nom, prenom, email, dob, edit_id):
    if not n:
        return no_update, no_update
    if not nom or not prenom or not email:
        return html.Div("Veuillez remplir tous les champs obligatoires.", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update

    db = SessionLocal()
    try:
        if edit_id:
            s = db.query(Student).filter_by(id=edit_id).first()
            if s:
                s.nom = nom; s.prenom = prenom; s.email = email
                if dob: s.date_naissance = dob
        else:
            if db.query(Student).filter_by(email=email).first():
                return html.Div("Un étudiant avec cet email existe déjà.", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update
            s = Student(nom=nom, prenom=prenom, email=email,
                        date_naissance=dob if dob else None)
            db.add(s)
        db.commit()
    except Exception as e:
        db.rollback()
        return html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update
    finally:
        db.close()
    return html.Div("✓ Enregistré avec succès.", style={"color": "#10b981", "fontSize": ".85rem"}), _render_table(get_students())

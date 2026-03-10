"""
SGA - Students Page
CRUD for students + individual dashboard + grade/attendance overview
"""

from dash import html, dcc, Input, Output, State, callback, no_update, ctx, ALL
import pandas as pd
from datetime import date
from models import SessionLocal, Student, Attendance, Grade, Session, Course
from sqlalchemy import func


# ─── Helpers ────────────────────────────────────────────────────────────────────
def get_students():
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.nom).all()
        
        # Récupération globale du nombre d'absences par étudiant
        absences = db.query(Attendance.student_id, func.count(Attendance.id)).filter_by(absent=True).group_by(Attendance.student_id).all()
        absences_map = {row[0]: row[1] for row in absences}
        
        # Récupération globale du nombre total de présences (sessions) par étudiant
        total_att = db.query(Attendance.student_id, func.count(Attendance.id)).group_by(Attendance.student_id).all()
        total_att_map = {row[0]: row[1] for row in total_att}
        
        # Récupération globale des moyennes par étudiant
        avgs = db.query(Grade.student_id, func.avg(Grade.note)).group_by(Grade.student_id).all()
        avgs_map = {row[0]: row[1] for row in avgs}

        result = []
        for s in students:
            # Calcul du taux d'absence en mémoire
            t_att = total_att_map.get(s.id, 0)
            abs_count = absences_map.get(s.id, 0)
            abs_rate = (abs_count / t_att * 100) if t_att > 0 else 0

            # Moyenne en mémoire
            avg = avgs_map.get(s.id) or 0

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

        # Import Excel Modal
        html.Div(id="import-modal-overlay", style={"display": "none"}, children=[
            html.Div(style={
                "position": "fixed", "inset": 0, "background": "rgba(0,0,0,.4)",
                "zIndex": 1002, "display": "flex", "alignItems": "center", "justifyContent": "center",
            }, children=[
                html.Div(className="sga-card animate-fade-up", style={"width": "100%", "maxWidth": "480px"}, children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1.25rem"}, children=[
                        html.H3("Importer des Étudiants (Excel)", style={"fontWeight": "700", "fontSize": "1.1rem", "margin": 0}),
                        html.Button("✕", id="close-import-modal", n_clicks=0, style={
                            "background": "none", "border": "none", "fontSize": "1.2rem", "cursor": "pointer", "color": "#64748b",
                        }),
                    ]),
                    html.P("Votre fichier Excel doit contenir les colonnes : Nom, Prenom, Email, Date_Naissance (YYYY-MM-DD).",
                           style={"fontSize": ".85rem", "color": "#64748b", "marginBottom": "1rem"}),
                    dcc.Upload(
                        id="upload-students-excel",
                        children=html.Div(className="upload-zone", children=[
                            html.Span("cloud_upload", className="material-symbols-outlined",
                                      style={"fontSize": "2.5rem", "color": "#94a3b8", "display": "block", "marginBottom": ".75rem"}),
                            html.P("Glissez votre fichier ici", style={"fontWeight": "600", "marginBottom": ".25rem"}),
                            html.P("ou cliquez pour parcourir (.xlsx)", style={"color": "#94a3b8", "fontSize": ".8rem"}),
                        ]),
                        accept=".xlsx,.xls",
                        multiple=False,
                    ),
                    html.Div(id="import-students-feedback", style={"marginTop": "1rem"}),
                ]),
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
                        dcc.Input(id="s-dob", type="text", placeholder="YYYY-MM-DD", className="sga-input", style={"width": "100%"}),
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
        if g >= 14: return "#10b981" # Emerald
        if g >= 10: return "#f59e0b" # Amber
        return "#f43f5e" # Rose

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
                        html.Div(className="progress-wrap", style={"flex": 1, "height": "8px"}, children=[
                            html.Div(className=f"progress-fill {'danger' if s['abs_rate'] > 20 else 'warning' if s['abs_rate'] > 10 else 'success'}",
                                     style={"width": f"{min(s['abs_rate'], 100)}%"}),
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
    Input({"type": "edit-student-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def toggle_modal(open_n, close_n, cancel_n, save_n, edit_clicks):
    tid = ctx.triggered_id
    if tid == "open-add-student-modal":
        return {"display": "block"}, None, "", "", "", "", "Nouvel Étudiant"
    if isinstance(tid, dict) and tid.get("type") == "edit-student-btn":
        # Guard: only open if an actual click happened (n_clicks > 0)
        triggered_clicks = ctx.triggered[0]["value"] if ctx.triggered else 0
        if not triggered_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        student_id = tid["index"]
        db = SessionLocal()
        try:
            s = db.query(Student).filter_by(id=student_id).first()
            if s:
                dob_str = str(s.date_naissance) if s.date_naissance else ""
                return {"display": "block"}, student_id, s.nom, s.prenom, s.email, dob_str, "Modifier l'Étudiant"
        finally:
            db.close()
    return {"display": "none"}, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("delete-confirm-overlay", "style"),
    Output("delete-student-id", "data"),
    Input({"type": "delete-student-btn", "index": ALL}, "n_clicks"),
    Input("cancel-delete-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_delete_modal(delete_clicks, cancel_n):
    tid = ctx.triggered_id
    if isinstance(tid, dict) and tid.get("type") == "delete-student-btn":
        # Guard: only open if an actual click happened (n_clicks > 0)
        triggered_clicks = ctx.triggered[0]["value"] if ctx.triggered else 0
        if not triggered_clicks:
            return no_update, no_update
        student_id = tid["index"]
        return {"display": "block"}, student_id
    # cancel button or any other trigger → close
    return {"display": "none"}, no_update


@callback(
    Output("students-table-container", "children", allow_duplicate=True),
    Output("student-notification", "children"),
    Output("delete-confirm-overlay", "style", allow_duplicate=True),
    Input("confirm-delete-btn", "n_clicks"),
    State("delete-student-id", "data"),
    prevent_initial_call=True,
)
def confirm_delete_student(n, student_id):
    if not n or not student_id:
        return no_update, no_update, no_update
    db = SessionLocal()
    try:
        s = db.query(Student).filter_by(id=student_id).first()
        if s:
            db.delete(s)
            db.commit()
            return (
                _render_table(get_students()),
                html.Div("✓ Étudiant supprimé.", style={"color": "#10b981", "fontSize": ".85rem", "marginTop": ".5rem"}),
                {"display": "none"},
            )
    except Exception as e:
        db.rollback()
        return no_update, html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update
    finally:
        db.close()
    return no_update, no_update, no_update


@callback(
    Output("import-modal-overlay", "style"),
    Input("open-import-modal", "n_clicks"),
    Input("close-import-modal", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_import_modal(open_n, close_n):
    tid = ctx.triggered_id
    if tid == "open-import-modal":
        return {"display": "block"}
    return {"display": "none"}


@callback(
    Output("import-students-feedback", "children"),
    Output("students-table-container", "children", allow_duplicate=True),
    Input("upload-students-excel", "contents"),
    State("upload-students-excel", "filename"),
    prevent_initial_call=True,
)
def import_students_excel(contents, filename):
    if not contents:
        return no_update, no_update
    import base64, io
    try:
        import pandas as pd
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        required = ["Nom", "Prenom", "Email"]
        for col in required:
            if col not in df.columns:
                return html.Div(f"Colonne manquante: {col}", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update
        db = SessionLocal()
        added, errors = 0, []
        try:
            for _, row in df.iterrows():
                email = str(row["Email"]).strip()
                if db.query(Student).filter_by(email=email).first():
                    errors.append(f"{email} existe déjà")
                    continue
                dob = None
                if "Date_Naissance" in df.columns and pd.notna(row["Date_Naissance"]):
                    try:
                        dob = date.fromisoformat(str(row["Date_Naissance"])[:10])
                    except Exception:
                        pass
                s = Student(nom=str(row["Nom"]).strip(), prenom=str(row["Prenom"]).strip(),
                            email=email, date_naissance=dob)
                db.add(s)
                added += 1
            db.commit()
        finally:
            db.close()
        msg = [html.Div(f"✓ {added} étudiant(s) importé(s).", style={"color": "#10b981", "fontWeight": "600", "fontSize": ".85rem"})]
        if errors:
            msg.append(html.Div(f"⚠ {len(errors)} ignoré(s): {', '.join(errors[:3])}", style={"color": "#f59e0b", "fontSize": ".8rem"}))
        return html.Div(msg), _render_table(get_students())
    except Exception as e:
        return html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update


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

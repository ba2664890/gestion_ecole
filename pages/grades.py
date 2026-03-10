"""
SGA - Grades & Evaluations Page
Excel template download, grade upload, manual entry
"""

from dash import html, dcc, Input, Output, State, callback, no_update, ALL
import base64, io
from models import SessionLocal, Student, Course, Grade
from sqlalchemy import func


def get_courses_options():
    db = SessionLocal()
    try:
        return [{"label": f"{c.code} – {c.libelle}", "value": c.id}
                for c in db.query(Course).order_by(Course.libelle).all()]
    finally:
        db.close()


def get_grades_summary(course_id=None):
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.nom).all()
        courses = db.query(Course).all()
        course_map = {c.id: c for c in courses}

        # Récupération globale des notes
        if course_id:
            all_grades = db.query(Grade).filter_by(course_id=course_id).all()
        else:
            all_grades = db.query(Grade).all()

        # Groupement des notes par étudiant en mémoire
        from collections import defaultdict
        grades_by_student = defaultdict(list)
        for g in all_grades:
            grades_by_student[g.student_id].append(g)

        result = []
        for s in students:
            grades = grades_by_student.get(s.id, [])

            if course_id:
                note = grades[0].note if grades else None
                coef = grades[0].coefficient if grades else 1
                result.append({
                    "student_id": s.id,
                    "name": f"{s.prenom} {s.nom}",
                    "course_id": course_id,
                    "note": note,
                    "coefficient": coef,
                })
            else:
                if grades:
                    avg = sum(g.note * g.coefficient for g in grades) / sum(g.coefficient for g in grades)
                else:
                    avg = None
                result.append({
                    "student_id": s.id,
                    "name": f"{s.prenom} {s.nom}",
                    "nb_grades": len(grades),
                    "moyenne": round(avg, 2) if avg is not None else None,
                })
        return result, course_map
    finally:
        db.close()


def layout():
    course_opts = get_courses_options()
    summary, _ = get_grades_summary()

    return html.Div([
        # Header
        html.Div(style={
            "display": "flex", "justifyContent": "space-between", "alignItems": "flex-start",
            "marginBottom": "1.5rem",
        }, className="animate-fade-up", children=[
            html.Div([
                html.H2("Notes & Évaluations", style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
                html.P("Gestion des notes par matière avec import/export Excel",
                       style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
            ]),
        ]),

        # Tab Navigation
        html.Div(className="tab-nav animate-fade-up-1", children=[
            html.Button("📊 Vue Globale", id="tab-global", className="tab-btn active", n_clicks=0),
            html.Button("📝 Saisie par Cours", id="tab-course", className="tab-btn", n_clicks=0),
            html.Button("📥 Import Excel", id="tab-import", className="tab-btn", n_clicks=0),
        ]),

        # Tab content
        html.Div(id="grades-tab-content", className="animate-fade-up-2",
                 children=[_tab_global(summary)]),

        dcc.Store(id="active-grade-tab", data="global"),
    ])


def _tab_global(summary):
    def grade_badge(g):
        if g is None:
            return html.Span("—", style={"color": "#94a3b8"})
        color = "#10b981" if g >= 14 else ("#f59e0b" if g >= 10 else "#f43f5e")
        return html.Span(f"{g}/20", style={"fontWeight": "700", "color": color})

    return html.Div(className="sga-card", style={"padding": 0, "overflow": "hidden"}, children=[
        html.Div(style={"padding": "1rem 1.5rem", "borderBottom": "1px solid #f1f5f9"}, children=[
            html.H3("Récapitulatif des Moyennes", style={"fontWeight": "700", "margin": 0, "fontSize": "1rem"}),
        ]),
        html.Table(className="sga-table", children=[
            html.Thead(html.Tr([
                html.Th("Étudiant"),
                html.Th("Nb de notes"),
                html.Th("Moyenne Générale"),
                html.Th("Mention"),
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(html.Div(style={"display": "flex", "alignItems": "center", "gap": ".65rem"}, children=[
                        html.Div(s["name"][:2].upper(), style={
                            "width": "32px", "height": "32px", "borderRadius": "50%",
                            "background": "var(--primary)", "color": "#fff",
                            "display": "flex", "alignItems": "center", "justifyContent": "center",
                            "fontSize": ".7rem", "fontWeight": "700", "flexShrink": 0,
                        }),
                        html.Span(s["name"], style={"fontWeight": "600", "fontSize": ".875rem"}),
                    ])),
                    html.Td(html.Span(str(s["nb_grades"]), className="badge badge-blue")),
                    html.Td(grade_badge(s["moyenne"])),
                    html.Td(_mention(s["moyenne"])),
                ])
                for s in summary
            ]),
        ]) if summary else html.Div(style={"padding": "2rem", "textAlign": "center", "color": "#94a3b8"}, children=[
            html.P("Aucune note saisie.")
        ]),
    ])


def _mention(g):
    if g is None: return html.Span("—", style={"color": "#94a3b8"})
    if g >= 16: m, c = "Très Bien", "badge-green"
    elif g >= 14: m, c = "Bien", "badge-blue"
    elif g >= 12: m, c = "Assez Bien", "badge-gray"
    elif g >= 10: m, c = "Passable", "badge-orange"
    else: m, c = "Insuffisant", "badge-red"
    return html.Span(m, className=f"badge {c}")


def _tab_course(course_opts):
    return html.Div(style={"display": "flex", "flexDirection": "column", "gap": "1.25rem"}, children=[
        # Course picker
        html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
            html.Label("Sélectionner un cours", className="sga-label"),
            dcc.Dropdown(id="grades-course-picker", options=course_opts,
                         placeholder="Choisir un cours...", style={"fontSize": ".875rem"}),
        ]),
        # Grade entry table
        html.Div(id="course-grade-table"),
    ])


def _tab_import(course_opts):
    return html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1.25rem"}, children=[
        # Download template
        html.Div(className="sga-card", children=[
            html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.25rem"}, children=[
                html.Div(style={
                    "width": "44px", "height": "44px", "borderRadius": "12px",
                    "background": "#d1fae5", "display": "flex", "alignItems": "center", "justifyContent": "center",
                }, children=[html.Span("download", className="material-symbols-outlined", style={"color": "#059669"})]),
                html.Div([
                    html.H3("Télécharger Template", style={"fontWeight": "700", "fontSize": ".95rem", "margin": 0}),
                    html.P("Fichier Excel pré-rempli avec les étudiants", style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}),
                ]),
            ]),
            html.Label("Sélectionner un cours", className="sga-label"),
            dcc.Dropdown(id="template-course-select", options=course_opts,
                         placeholder="Cours...", style={"fontSize": ".875rem", "marginBottom": "1rem"}),
            html.Button(
                [html.Span("download", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                 "Télécharger le Template Excel"],
                id="download-template-link",
                n_clicks=0,
                className="btn-primary",
                style={"display": "inline-flex", "alignItems": "center", "gap": ".5rem"},
            ),
            dcc.Download(id="download-template"),
        ]),

        # Upload grades
        html.Div(className="sga-card", children=[
            html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.25rem"}, children=[
                html.Div(style={
                    "width": "44px", "height": "44px", "borderRadius": "12px",
                    "background": "#eff6ff", "display": "flex", "alignItems": "center", "justifyContent": "center",
                }, children=[html.Span("upload_file", className="material-symbols-outlined", style={"color": "#6366f1"})]),
                html.Div([
                    html.H3("Importer les Notes", style={"fontWeight": "700", "fontSize": ".95rem", "margin": 0}),
                    html.P("Fichier Excel complété avec les notes", style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}),
                ]),
            ]),
            dcc.Upload(
                id="upload-grades",
                children=html.Div(className="upload-zone", children=[
                    html.Span("cloud_upload", className="material-symbols-outlined",
                              style={"fontSize": "2.5rem", "color": "#94a3b8", "display": "block", "marginBottom": ".75rem"}),
                    html.P("Glissez votre fichier Excel ici", style={"fontWeight": "600", "marginBottom": ".25rem"}),
                    html.P("ou cliquez pour parcourir", style={"color": "#94a3b8", "fontSize": ".8rem"}),
                    html.P(".xlsx · Max 10 MB", style={"color": "#cbd5e1", "fontSize": ".75rem", "marginTop": ".5rem"}),
                ]),
                accept=".xlsx,.xls",
                multiple=False,
            ),
            html.Div(id="upload-feedback"),
        ]),
    ])


# ─── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("grades-tab-content", "children"),
    Output("tab-global", "className"),
    Output("tab-course", "className"),
    Output("tab-import", "className"),
    Output("active-grade-tab", "data"),
    Input("tab-global", "n_clicks"),
    Input("tab-course", "n_clicks"),
    Input("tab-import", "n_clicks"),
    State("active-grade-tab", "data"),
    prevent_initial_call=True,
)
def switch_tab(g, c, i, current):
    from dash import ctx
    tid = ctx.triggered_id
    course_opts = get_courses_options()
    summary, _ = get_grades_summary()

    if tid == "tab-global":
        return _tab_global(summary), "tab-btn active", "tab-btn", "tab-btn", "global"
    elif tid == "tab-course":
        return _tab_course(course_opts), "tab-btn", "tab-btn active", "tab-btn", "course"
    else:
        return _tab_import(course_opts), "tab-btn", "tab-btn", "tab-btn active", "import"


@callback(
    Output("course-grade-table", "children"),
    Input("grades-course-picker", "value"),
)
def load_course_grades(course_id):
    if not course_id:
        return html.P("Sélectionnez un cours pour afficher les notes.",
                      style={"color": "#94a3b8", "textAlign": "center", "padding": "1.5rem"})
    summary, course_map = get_grades_summary(course_id)
    course = course_map.get(course_id)

    rows = []
    for s in summary:
        rows.append(html.Tr([
            html.Td(s["name"], style={"fontWeight": "600", "fontSize": ".875rem"}),
            html.Td(dcc.Input(
                id={"type": "grade-input", "index": s["student_id"]},
                type="number", min=0, max=20, step=0.5,
                value=s.get("note"),
                placeholder="Note /20",
                className="sga-input",
                style={"width": "110px", "padding": ".45rem .75rem"},
            )),
            html.Td(dcc.Input(
                id={"type": "coef-input", "index": s["student_id"]},
                type="number", min=0.5, max=5, step=0.5,
                value=s.get("coefficient", 1),
                className="sga-input",
                style={"width": "80px", "padding": ".45rem .75rem"},
            )),
        ]))

    return html.Div([
        html.Div(className="sga-card", style={"padding": 0, "overflow": "hidden"}, children=[
            html.Div(style={"padding": "1rem 1.5rem", "borderBottom": "1px solid #f1f5f9",
                            "display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
                html.Div([
                    html.H3(f"Notes – {course.libelle if course else ''}", style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
                    html.P(f"{len(summary)} étudiants", style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}),
                ]),
                html.Button([html.Span("save", className="material-symbols-outlined", style={"fontSize": "1rem"}), "Enregistrer"],
                            id="save-course-grades-btn", n_clicks=0, className="btn-primary",
                            style={"padding": ".5rem 1rem", "fontSize": ".85rem"}),
            ]),
            html.Table(className="sga-table", children=[
                html.Thead(html.Tr([html.Th("Étudiant"), html.Th("Note /20"), html.Th("Coefficient")])),
                html.Tbody(rows),
            ]),
        ]),
        html.Div(id="course-grade-save-feedback", style={"marginTop": "1rem"}),
        dcc.Store(id="selected-course-id-store", data=course_id),
    ])


@callback(
    Output("download-template", "data"),
    Input("download-template-link", "n_clicks"),
    State("template-course-select", "value"),
    prevent_initial_call=True,
)
def download_template(n, course_id):
    if not n or not course_id:
        return no_update

    import pandas as pd
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.nom).all()
        course = db.query(Course).filter_by(id=course_id).first()
        df = pd.DataFrame([{
            "ID": s.id, "Nom": s.nom, "Prenom": s.prenom,
            "Email": s.email, "Note": "", "Coefficient": 1.0,
            "Type_Evaluation": "Examen"
        } for s in students])

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Notes")
        buf.seek(0)
        course_code = course.code if course else "cours"
        return dcc.send_bytes(buf.getvalue(), f"notes_{course_code}.xlsx")
    finally:
        db.close()


@callback(
    Output("upload-feedback", "children"),
    Input("upload-grades", "contents"),
    State("upload-grades", "filename"),
    prevent_initial_call=True,
)
def process_upload(contents, filename):
    if not contents:
        return no_update
    if not filename.endswith((".xlsx", ".xls")):
        return html.Div("Format de fichier non supporté. Utilisez .xlsx ou .xls",
                        style={"color": "#f43f5e", "fontSize": ".875rem", "marginTop": "1rem"})
    try:
        import pandas as pd
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))

        required = ["ID", "Note"]
        for col in required:
            if col not in df.columns:
                return html.Div(f"Colonne manquante: {col}", style={"color": "#f43f5e", "fontSize": ".875rem", "marginTop": "1rem"})

        db = SessionLocal()
        updated, errors = 0, []
        try:
            for _, row in df.iterrows():
                try:
                    student_id = int(row["ID"])
                    note = float(row["Note"])
                    if note < 0 or note > 20:
                        errors.append(f"Note invalide pour ID {student_id}")
                        continue
                    coef = float(row.get("Coefficient", 1.0))
                    course_id_val = int(row["Course_ID"]) if "Course_ID" in row else None

                    if course_id_val:
                        existing = db.query(Grade).filter_by(student_id=student_id, course_id=course_id_val).first()
                        if existing:
                            existing.note = note; existing.coefficient = coef
                        else:
                            g = Grade(student_id=student_id, course_id=course_id_val, note=note, coefficient=coef)
                            db.add(g)
                        updated += 1
                except Exception as e:
                    errors.append(str(e))
            db.commit()
        finally:
            db.close()

        msg = [html.Div(f"✓ {updated} note(s) importée(s) avec succès.",
                        style={"color": "#10b981", "fontWeight": "600", "fontSize": ".875rem", "marginTop": "1rem"})]
        if errors:
            msg.append(html.Div(f"⚠ {len(errors)} erreur(s): {', '.join(errors[:3])}",
                                style={"color": "#f59e0b", "fontSize": ".8rem"}))
        return html.Div(msg)

    except Exception as e:
        return html.Div(f"Erreur lors du traitement: {e}",
                        style={"color": "#ef4444", "fontSize": ".875rem", "marginTop": "1rem"})


@callback(
    Output("course-grade-save-feedback", "children"),
    Input("save-course-grades-btn", "n_clicks"),
    State({"type": "grade-input", "index": ALL}, "value"),
    State({"type": "grade-input", "index": ALL}, "id"),
    State({"type": "coef-input", "index": ALL}, "value"),
    State("selected-course-id-store", "data"),
    prevent_initial_call=True,
)
def save_course_grades(n, notes, note_ids, coefs, course_id):
    if not n or not course_id:
        return no_update
    db = SessionLocal()
    saved, errors = 0, []
    try:
        for id_obj, note, coef in zip(note_ids, notes, coefs):
            if note is None:
                continue
            student_id = id_obj["index"]
            try:
                note_val = float(note)
                coef_val = float(coef) if coef else 1.0
                if note_val < 0 or note_val > 20:
                    errors.append(f"Note hors intervalle pour ID {student_id}")
                    continue
                existing = db.query(Grade).filter_by(student_id=student_id, course_id=course_id, type_evaluation="Examen").first()
                if existing:
                    existing.note = note_val
                    existing.coefficient = coef_val
                else:
                    db.add(Grade(student_id=student_id, course_id=course_id,
                                 note=note_val, coefficient=coef_val, type_evaluation="Examen"))
                saved += 1
            except Exception as e:
                errors.append(str(e))
        db.commit()
    except Exception as e:
        db.rollback()
        return html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"})
    finally:
        db.close()
    msg = [html.Div(f"✓ {saved} note(s) enregistrée(s).", style={"color": "#10b981", "fontWeight": "600", "fontSize": ".875rem"})]
    if errors:
        msg.append(html.Div(f"⚠ {len(errors)} erreur(s): {', '.join(errors[:3])}", style={"color": "#f59e0b", "fontSize": ".8rem"}))
    return html.Div(msg)

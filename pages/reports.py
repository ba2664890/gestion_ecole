"""
SGA - Reports & Exports Page
Generate PDF bulletins, attendance reports, Excel exports
"""

from dash import html, dcc, Input, Output, State, callback, no_update
from models import SessionLocal, Student, Course, Grade, Attendance, Session
from sqlalchemy import func
import io
import base64


def get_students_options():
    db = SessionLocal()
    try:
        return [{"label": f"{s.prenom} {s.nom}", "value": s.id}
                for s in db.query(Student).order_by(Student.nom).all()]
    finally:
        db.close()


def get_courses_options():
    db = SessionLocal()
    try:
        return [{"label": f"{c.code} – {c.libelle}", "value": c.id}
                for c in db.query(Course).order_by(Course.libelle).all()]
    finally:
        db.close()


def layout():
    student_opts = get_students_options()
    course_opts = get_courses_options()

    return html.Div([
        # Header
        html.Div(style={"marginBottom": "1.5rem"}, className="animate-fade-up", children=[
            html.H2("Rapports & Exports", style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
            html.P("Génération de bulletins PDF, rapports de présence et exports Excel",
                   style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
        ]),

        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1.25rem"}, children=[

            # Bulletin de notes PDF
            html.Div(className="sga-card animate-fade-up-1", children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.5rem"}, children=[
                    html.Div(style={
                        "width": "48px", "height": "48px", "borderRadius": "12px",
                        "background": "#eff6ff", "display": "flex", "alignItems": "center", "justifyContent": "center",
                    }, children=[html.Span("picture_as_pdf", className="material-symbols-outlined", style={"color": "#3b82f6", "fontSize": "1.5rem"})]),
                    html.Div([
                        html.H3("Bulletin de Notes", style={"fontWeight": "700", "margin": 0}),
                        html.P("Export PDF individuel avec toutes les notes et absences",
                               style={"color": "#64748b", "fontSize": ".8rem", "margin": 0}),
                    ]),
                ]),
                html.Label("Étudiant", className="sga-label"),
                dcc.Dropdown(id="bulletin-student", options=student_opts, placeholder="Choisir un étudiant...",
                             style={"fontSize": ".875rem", "marginBottom": "1.25rem"}),
                html.Div(style={"marginBottom": "1.25rem"}, children=[
                    html.Label("Établissement (optionnel)", className="sga-label"),
                    dcc.Input(id="bulletin-etab", value="Établissement Académique", className="sga-input", style={"width": "100%"}),
                ]),
                html.Button([
                    html.Span("download", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                    "Générer Bulletin PDF",
                ], id="generate-bulletin-btn", n_clicks=0, className="btn-primary",
                style={"width": "100%", "justifyContent": "center"}),
                html.Div(id="bulletin-feedback", style={"marginTop": "1rem"}),
                dcc.Download(id="download-bulletin"),
            ]),

            # Rapport de présences
            html.Div(className="sga-card animate-fade-up-2", children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.5rem"}, children=[
                    html.Div(style={
                        "width": "48px", "height": "48px", "borderRadius": "12px",
                        "background": "#f0fdf4", "display": "flex", "alignItems": "center", "justifyContent": "center",
                    }, children=[html.Span("event_note", className="material-symbols-outlined", style={"color": "#22c55e", "fontSize": "1.5rem"})]),
                    html.Div([
                        html.H3("Rapport de Présences", style={"fontWeight": "700", "margin": 0}),
                        html.P("Export Excel du taux de présence par cours",
                               style={"color": "#64748b", "fontSize": ".8rem", "margin": 0}),
                    ]),
                ]),
                html.Label("Cours", className="sga-label"),
                dcc.Dropdown(id="rapport-course", options=course_opts, placeholder="Tous les cours",
                             style={"fontSize": ".875rem", "marginBottom": "1.25rem"}),
                html.Button([
                    html.Span("table_chart", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                    "Exporter Excel Présences",
                ], id="export-attendance-btn", n_clicks=0, className="btn-primary",
                style={"width": "100%", "justifyContent": "center", "background": "#22c55e",
                       "boxShadow": "0 4px 12px rgba(34,197,94,.25)"}),
                html.Div(id="attendance-export-feedback", style={"marginTop": "1rem"}),
                dcc.Download(id="download-attendance"),
            ]),

            # Export global notes
            html.Div(className="sga-card animate-fade-up-3", children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.5rem"}, children=[
                    html.Div(style={
                        "width": "48px", "height": "48px", "borderRadius": "12px",
                        "background": "#fdf4ff", "display": "flex", "alignItems": "center", "justifyContent": "center",
                    }, children=[html.Span("grid_on", className="material-symbols-outlined", style={"color": "#a855f7", "fontSize": "1.5rem"})]),
                    html.Div([
                        html.H3("Export Global des Notes", style={"fontWeight": "700", "margin": 0}),
                        html.P("Toutes les notes de tous les étudiants",
                               style={"color": "#64748b", "fontSize": ".8rem", "margin": 0}),
                    ]),
                ]),
                html.Button([
                    html.Span("download", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                    "Exporter toutes les notes (.xlsx)",
                ], id="export-all-grades-btn", n_clicks=0, className="btn-primary",
                style={"width": "100%", "justifyContent": "center", "background": "#a855f7",
                       "boxShadow": "0 4px 12px rgba(168,85,247,.25)"}),
                dcc.Download(id="download-all-grades"),
            ]),

            # Stats card
            html.Div(className="sga-card animate-fade-up-4", children=[
                html.H3("Synthèse Rapide", style={"fontWeight": "700", "marginBottom": "1.25rem"}),
                html.Div(id="quick-stats-report", children=[_render_quick_stats()]),
            ]),
        ]),
    ])


def _render_quick_stats():
    db = SessionLocal()
    try:
        n_students = db.query(Student).count()
        n_courses = db.query(Course).count()
        n_sessions = db.query(Session).count()
        n_grades = db.query(Grade).count()
        avg = db.query(func.avg(Grade.note)).scalar() or 0
        absents = db.query(Attendance).filter_by(absent=True).count()
        total_att = db.query(Attendance).count()
        att_pct = ((total_att - absents) / total_att * 100) if total_att > 0 else 100

        items = [
            ("Étudiants inscrits", str(n_students), "#3b82f6"),
            ("Cours actifs", str(n_courses), "#8b5cf6"),
            ("Séances enregistrées", str(n_sessions), "#f59e0b"),
            ("Notes saisies", str(n_grades), "#10b981"),
            ("Moyenne générale", f"{avg:.2f}/20", "#ef4444" if avg < 10 else "#10b981"),
            ("Taux présence", f"{att_pct:.1f}%", "#ef4444" if att_pct < 85 else "#10b981"),
        ]
        return html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".65rem"}, children=[
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "padding": ".5rem .75rem", "borderRadius": "8px", "background": "#f8fafc",
            }, children=[
                html.Span(label, style={"fontSize": ".85rem", "color": "#64748b"}),
                html.Span(value, style={"fontSize": ".85rem", "fontWeight": "700", "color": color}),
            ])
            for label, value, color in items
        ])
    finally:
        db.close()


# ─── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("download-bulletin", "data"),
    Output("bulletin-feedback", "children"),
    Input("generate-bulletin-btn", "n_clicks"),
    State("bulletin-student", "value"),
    State("bulletin-etab", "value"),
    prevent_initial_call=True,
)
def generate_bulletin(n, student_id, etab):
    if not n or not student_id:
        return no_update, html.Div("Veuillez sélectionner un étudiant.", style={"color": "#ef4444", "fontSize": ".85rem"})

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER

        db = SessionLocal()
        try:
            student = db.query(Student).filter_by(id=student_id).first()
            if not student:
                return no_update, html.Div("Étudiant introuvable.", style={"color": "#ef4444"})

            grades = db.query(Grade).filter_by(student_id=student_id).all()
            attendances = db.query(Attendance).filter_by(student_id=student_id).all()
            total_att = len(attendances)
            absents = sum(1 for a in attendances if a.absent)
            att_rate = ((total_att - absents) / total_att * 100) if total_att > 0 else 100

            if grades:
                avg = sum(g.note * g.coefficient for g in grades) / sum(g.coefficient for g in grades)
            else:
                avg = 0
        finally:
            db.close()

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#13a4ec")
        dark_color = colors.HexColor("#0f172a")
        gray_color = colors.HexColor("#64748b")

        story = []

        # Header
        header_style = ParagraphStyle("header", fontSize=22, fontName="Helvetica-Bold",
                                       textColor=dark_color, alignment=TA_CENTER)
        sub_style = ParagraphStyle("sub", fontSize=10, textColor=gray_color, alignment=TA_CENTER)
        story.append(Paragraph(etab or "Établissement Académique", header_style))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("BULLETIN DE NOTES", ParagraphStyle("title", fontSize=14,
                                                                      fontName="Helvetica-Bold",
                                                                      textColor=primary_color, alignment=TA_CENTER)))
        story.append(HRFlowable(color=primary_color, thickness=2, width="100%"))
        story.append(Spacer(1, 0.5*cm))

        # Student info
        info_data = [
            ["Nom et Prénom:", f"{student.prenom} {student.nom}",
             "Date de naissance:", str(student.date_naissance or "—")],
            ["Email:", student.email, "Taux présence:", f"{att_rate:.1f}%"],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 7*cm, 4*cm, 3*cm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), dark_color),
            ("TEXTCOLOR", (2, 0), (2, -1), dark_color),
            ("TEXTCOLOR", (1, 0), (1, -1), gray_color),
            ("TEXTCOLOR", (3, 0), (3, -1), gray_color),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.8*cm))

        # Grades table
        grade_title = ParagraphStyle("gtitle", fontSize=12, fontName="Helvetica-Bold", textColor=dark_color)
        story.append(Paragraph("Résultats par Matière", grade_title))
        story.append(Spacer(1, 0.3*cm))

        grade_data = [["Matière", "Code", "Note /20", "Coeff.", "Note × Coeff.", "Type"]]
        for g in grades:
            mention = "TB" if g.note >= 16 else ("B" if g.note >= 14 else ("AB" if g.note >= 12 else ("P" if g.note >= 10 else "I")))
            grade_data.append([
                g.course.libelle if g.course else "—",
                g.course.code if g.course else "—",
                f"{g.note:.2f}",
                f"{g.coefficient:.1f}",
                f"{g.note * g.coefficient:.2f}",
                g.type_evaluation,
            ])

        if not grades:
            grade_data.append(["Aucune note disponible", "", "", "", "", ""])

        grade_table = Table(grade_data, colWidths=[7*cm, 2.5*cm, 2.5*cm, 2*cm, 3*cm, 2.5*cm])
        grade_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ]))
        story.append(grade_table)
        story.append(Spacer(1, 0.8*cm))

        # Summary
        mention_text = "Très Bien" if avg >= 16 else ("Bien" if avg >= 14 else ("Assez Bien" if avg >= 12 else ("Passable" if avg >= 10 else "Insuffisant")))
        summary_data = [
            ["MOYENNE GÉNÉRALE", f"{avg:.2f} / 20"],
            ["MENTION", mention_text],
            ["TAUX DE PRÉSENCE", f"{att_rate:.1f}%"],
        ]
        summary_table = Table(summary_data, colWidths=[8*cm, 10.5*cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("TEXTCOLOR", (1, 0), (1, 0), primary_color),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ]))
        story.append(summary_table)

        doc.build(story)
        buf.seek(0)
        filename = f"bulletin_{student.nom}_{student.prenom}.pdf"
        return dcc.send_bytes(buf.getvalue(), filename), html.Div(
            f"✓ Bulletin généré pour {student.prenom} {student.nom}",
            style={"color": "#10b981", "fontWeight": "600", "fontSize": ".875rem"}
        )

    except ImportError:
        return no_update, html.Div("⚠ Module ReportLab non installé. Installez-le avec: pip install reportlab",
                                   style={"color": "#f59e0b", "fontSize": ".85rem"})
    except Exception as e:
        return no_update, html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"})


@callback(
    Output("download-attendance", "data"),
    Output("attendance-export-feedback", "children"),
    Input("export-attendance-btn", "n_clicks"),
    State("rapport-course", "value"),
    prevent_initial_call=True,
)
def export_attendance(n, course_id):
    if not n:
        return no_update, no_update
    try:
        import pandas as pd
        db = SessionLocal()
        try:
            students = db.query(Student).order_by(Student.nom).all()
            sessions = db.query(Session)
            if course_id:
                sessions = sessions.filter_by(course_id=course_id)
            sessions = sessions.order_by(Session.date).all()

            rows = []
            for s in students:
                row = {"Nom": s.nom, "Prénom": s.prenom, "Email": s.email}
                total, absents = 0, 0
                for sess in sessions:
                    att = next((a for a in sess.attendances if a.student_id == s.id), None)
                    present = not att.absent if att else True
                    row[f"{sess.date} ({sess.course.code if sess.course else '?'})"] = "P" if present else "A"
                    total += 1
                    if att and att.absent:
                        absents += 1
                row["Total Séances"] = total
                row["Absences"] = absents
                row["Taux Présence"] = f"{((total-absents)/total*100):.1f}%" if total > 0 else "—"
                rows.append(row)
        finally:
            db.close()

        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Présences")
        buf.seek(0)
        return dcc.send_bytes(buf.getvalue(), "rapport_presences.xlsx"), html.Div(
            "✓ Rapport exporté.", style={"color": "#10b981", "fontWeight": "600", "fontSize": ".875rem"}
        )
    except Exception as e:
        return no_update, html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"})


@callback(
    Output("download-all-grades", "data"),
    Input("export-all-grades-btn", "n_clicks"),
    prevent_initial_call=True,
)
def export_all_grades(n):
    if not n:
        return no_update
    import pandas as pd
    db = SessionLocal()
    try:
        grades = db.query(Grade).all()
        rows = [{
            "Student_ID": g.student_id,
            "Nom": g.student.nom if g.student else "—",
            "Prénom": g.student.prenom if g.student else "—",
            "Course_Code": g.course.code if g.course else "—",
            "Course_Libelle": g.course.libelle if g.course else "—",
            "Note": g.note,
            "Coefficient": g.coefficient,
            "Type": g.type_evaluation,
        } for g in grades]
    finally:
        db.close()

    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Student_ID", "Nom", "Prénom", "Course_Code", "Course_Libelle", "Note", "Coefficient", "Type"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Notes")
    buf.seek(0)
    return dcc.send_bytes(buf.getvalue(), "notes_complet.xlsx")

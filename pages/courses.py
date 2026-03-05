"""
SGA - Courses / Curriculum Page
CRUD + progress tracking per course
"""

from dash import html, dcc, Input, Output, State, callback, no_update, ctx
from models import SessionLocal, Course, Session as DBSession
from sqlalchemy import func


def get_courses():
    db = SessionLocal()
    try:
        courses = db.query(Course).order_by(Course.libelle).all()
        result = []
        for c in courses:
            h_done = sum(s.duree for s in c.sessions)
            pct = min(100, (h_done / c.volume_horaire * 100)) if c.volume_horaire > 0 else 0
            nb_sessions = len(c.sessions)
            result.append({
                "id": c.id, "code": c.code, "libelle": c.libelle,
                "volume_horaire": c.volume_horaire, "enseignant": c.enseignant,
                "description": c.description or "",
                "h_done": h_done, "pct": round(pct, 1),
                "nb_sessions": nb_sessions,
            })
        return result
    finally:
        db.close()


def layout():
    courses = get_courses()

    # Summary stats
    total_vh = sum(c["volume_horaire"] for c in courses)
    total_done = sum(c["h_done"] for c in courses)
    on_track = sum(1 for c in courses if c["pct"] >= 50)

    return html.Div([
        # Header
        html.Div(style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "flex-start", "marginBottom": "1.5rem",
        }, className="animate-fade-up", children=[
            html.Div([
                html.H2("Curriculum & Cours", style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
                html.P(f"{len(courses)} cours · {total_vh:.0f}h planifiées · {total_done:.0f}h effectuées",
                       style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
            ]),
            html.Div(style={"display": "flex", "gap": ".75rem"}, children=[
                html.Button([html.Span("download", className="material-symbols-outlined", style={"fontSize": "1rem"}), "Exporter"],
                            className="btn-secondary", n_clicks=0, id="export-courses-btn"),
                html.Button([html.Span("add", className="material-symbols-outlined", style={"fontSize": "1rem"}), "Ajouter un Cours"],
                            className="btn-primary", n_clicks=0, id="open-add-course-modal"),
            ]),
        ]),

        # KPI summary
        html.Div(style={
            "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "1rem", "marginBottom": "1.5rem",
        }, className="animate-fade-up-1", children=[
            _mini_kpi("import_contacts", "Cours Total", str(len(courses)), "#3b82f6"),
            _mini_kpi("schedule", "Heures Planifiées", f"{total_vh:.0f}h", "#8b5cf6"),
            _mini_kpi("check_circle", "Heures Effectuées", f"{total_done:.0f}h", "#10b981"),
            _mini_kpi("trending_up", "Cours en bonne voie", str(on_track), "#f59e0b"),
        ]),

        # Courses grid
        html.Div(id="courses-grid", children=[_render_courses_grid(courses)], className="animate-fade-up-2"),

        # Add/Edit Modal
        html.Div(id="course-modal-overlay", style={"display": "none"}, children=[
            html.Div(style={
                "position": "fixed", "inset": 0, "background": "rgba(0,0,0,.5)",
                "zIndex": 1000, "display": "flex", "alignItems": "center", "justifyContent": "center",
            }, children=[
                html.Div(className="sga-card animate-fade-up", style={
                    "width": "100%", "maxWidth": "580px",
                    "boxShadow": "0 20px 60px rgba(0,0,0,.15)",
                }, children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "1.5rem"}, children=[
                        html.H3(id="course-modal-title", children="Nouveau Cours", style={"fontWeight": "700", "fontSize": "1.1rem", "margin": 0}),
                        html.Button("✕", id="close-course-modal", n_clicks=0, style={
                            "background": "none", "border": "none", "fontSize": "1.2rem",
                            "cursor": "pointer", "color": "#64748b",
                        }),
                    ]),
                    dcc.Store(id="editing-course-id"),

                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1rem"}, children=[
                        html.Div([html.Label("Code", className="sga-label"),
                                  dcc.Input(id="c-code", placeholder="ex: MATH101", className="sga-input")]),
                        html.Div([html.Label("Volume Horaire (h)", className="sga-label"),
                                  dcc.Input(id="c-vh", type="number", placeholder="ex: 60", className="sga-input")]),
                    ]),
                    html.Div(style={"marginTop": "1rem"}, children=[
                        html.Label("Libellé du cours", className="sga-label"),
                        dcc.Input(id="c-libelle", placeholder="ex: Mathématiques Avancées", className="sga-input", style={"width": "100%"}),
                    ]),
                    html.Div(style={"marginTop": "1rem"}, children=[
                        html.Label("Enseignant responsable", className="sga-label"),
                        dcc.Input(id="c-enseignant", placeholder="ex: Dr. Martin", className="sga-input", style={"width": "100%"}),
                    ]),
                    html.Div(style={"marginTop": "1rem"}, children=[
                        html.Label("Description (optionnel)", className="sga-label"),
                        dcc.Textarea(id="c-description", placeholder="Description du cours...",
                                     className="sga-textarea", style={"width": "100%", "height": "80px", "resize": "vertical"}),
                    ]),
                    html.Div(id="course-form-feedback", style={"marginTop": "1rem"}),
                    html.Div(style={"display": "flex", "gap": ".75rem", "marginTop": "1.5rem", "justifyContent": "flex-end"}, children=[
                        html.Button("Annuler", id="cancel-course-btn", n_clicks=0, className="btn-secondary"),
                        html.Button("Enregistrer", id="save-course-btn", n_clicks=0, className="btn-primary"),
                    ]),
                ]),
            ]),
        ]),

        html.Div(id="course-notification"),
    ])


def _mini_kpi(icon, label, value, color):
    return html.Div(className="sga-card", style={"padding": "1rem 1.25rem"}, children=[
        html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem"}, children=[
            html.Div(
                html.Span(icon, className="material-symbols-outlined", style={"fontSize": "1.1rem", "color": color}),
                style={
                    "width": "38px", "height": "38px", "borderRadius": "10px",
                    "background": f"{color}15",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                }
            ),
            html.Div([
                html.Div(label, style={"fontSize": ".75rem", "color": "#64748b", "fontWeight": "500"}),
                html.Div(value, style={"fontSize": "1.2rem", "fontWeight": "800", "color": color}),
            ]),
        ]),
    ])


def _render_courses_grid(courses):
    if not courses:
        return html.Div(style={"textAlign": "center", "padding": "3rem", "color": "#94a3b8"}, children=[
            html.Span("library_books", className="material-symbols-outlined", style={"fontSize": "3rem", "display": "block"}),
            html.P("Aucun cours. Ajoutez votre premier cours.", style={"marginTop": "1rem"}),
        ])

    return html.Div(style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fill, minmax(320px, 1fr))",
        "gap": "1.25rem",
    }, children=[_course_card(c) for c in courses])


def _course_card(c):
    pct = c["pct"]
    status_color = "#10b981" if pct >= 75 else ("#f59e0b" if pct >= 40 else "#ef4444")
    status_label = "En bonne voie" if pct >= 75 else ("En cours" if pct >= 40 else "En retard")

    return html.Div(className="sga-card", style={"padding": "1.25rem"}, children=[
        # Header
        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "marginBottom": "1rem"}, children=[
            html.Div([
                html.Span(c["code"], className="badge badge-blue", style={"marginBottom": ".5rem", "display": "inline-block"}),
                html.H3(c["libelle"], style={"fontWeight": "700", "fontSize": "1rem", "margin": 0, "lineHeight": 1.3}),
            ]),
            html.Span(status_label, style={
                "padding": ".2rem .7rem", "borderRadius": "99px",
                "fontSize": ".7rem", "fontWeight": "700",
                "background": f"{status_color}15", "color": status_color,
                "whiteSpace": "nowrap",
            }),
        ]),

        # Teacher
        html.Div(style={"display": "flex", "alignItems": "center", "gap": ".5rem", "marginBottom": "1rem"}, children=[
            html.Span("person", className="material-symbols-outlined", style={"fontSize": ".95rem", "color": "#94a3b8"}),
            html.Span(c["enseignant"], style={"fontSize": ".825rem", "color": "#64748b"}),
        ]),

        # Progress
        html.Div(style={"marginBottom": "1rem"}, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": ".5rem"}, children=[
                html.Span("Progression", style={"fontSize": ".75rem", "color": "#94a3b8", "fontWeight": "600"}),
                html.Span(f"{c['h_done']:.0f}h / {c['volume_horaire']:.0f}h",
                          style={"fontSize": ".75rem", "fontWeight": "700", "color": status_color}),
            ]),
            html.Div(className="progress-wrap", children=[
                html.Div(style={
                    "height": "100%", "borderRadius": "99px",
                    "width": f"{pct}%",
                    "background": f"linear-gradient(90deg, {status_color}, {status_color}aa)",
                    "transition": "width .8s cubic-bezier(.4,0,.2,1)",
                }),
            ]),
            html.Div(f"{pct:.1f}% complété · {c['nb_sessions']} séance(s)",
                     style={"fontSize": ".7rem", "color": "#94a3b8", "marginTop": ".4rem"}),
        ]),

        # Actions
        html.Div(style={"display": "flex", "gap": ".5rem", "borderTop": "1px solid #f1f5f9", "paddingTop": "1rem"}, children=[
            html.Button([html.Span("edit", className="material-symbols-outlined", style={"fontSize": ".95rem"}), " Modifier"],
                        id={"type": "edit-course-btn", "index": c["id"]},
                        n_clicks=0, className="btn-secondary",
                        style={"flex": 1, "justifyContent": "center", "padding": ".5rem", "fontSize": ".8rem"}),
            html.Button([html.Span("delete", className="material-symbols-outlined", style={"fontSize": ".95rem"})],
                        id={"type": "delete-course-btn", "index": c["id"]},
                        n_clicks=0, className="btn-danger",
                        style={"padding": ".5rem .75rem", "fontSize": ".8rem"}),
        ]),
    ])


# ─── Callbacks ──────────────────────────────────────────────────────────────────
@callback(
    Output("course-modal-overlay", "style"),
    Output("c-code", "value"),
    Output("c-libelle", "value"),
    Output("c-vh", "value"),
    Output("c-enseignant", "value"),
    Output("c-description", "value"),
    Output("editing-course-id", "data"),
    Output("course-modal-title", "children"),
    Input("open-add-course-modal", "n_clicks"),
    Input("close-course-modal", "n_clicks"),
    Input("cancel-course-btn", "n_clicks"),
    Input("save-course-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_course_modal(open_n, close_n, cancel_n, save_n):
    tid = ctx.triggered_id
    if tid == "open-add-course-modal":
        return {"display": "block"}, "", "", None, "", "", None, "Nouveau Cours"
    return {"display": "none"}, no_update, no_update, no_update, no_update, no_update, no_update, no_update


@callback(
    Output("course-form-feedback", "children"),
    Output("courses-grid", "children", allow_duplicate=True),
    Input("save-course-btn", "n_clicks"),
    State("c-code", "value"),
    State("c-libelle", "value"),
    State("c-vh", "value"),
    State("c-enseignant", "value"),
    State("c-description", "value"),
    State("editing-course-id", "data"),
    prevent_initial_call=True,
)
def save_course(n, code, libelle, vh, enseignant, description, edit_id):
    if not n:
        return no_update, no_update
    if not code or not libelle or not enseignant or not vh:
        return html.Div("Veuillez remplir tous les champs obligatoires.", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update

    db = SessionLocal()
    try:
        if edit_id:
            c = db.query(Course).filter_by(id=edit_id).first()
            if c:
                c.code = code; c.libelle = libelle; c.volume_horaire = float(vh)
                c.enseignant = enseignant; c.description = description
        else:
            if db.query(Course).filter_by(code=code).first():
                return html.Div("Ce code de cours existe déjà.", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update
            c = Course(code=code, libelle=libelle, volume_horaire=float(vh),
                       enseignant=enseignant, description=description)
            db.add(c)
        db.commit()
    except Exception as e:
        db.rollback()
        return html.Div(f"Erreur: {e}", style={"color": "#ef4444", "fontSize": ".85rem"}), no_update
    finally:
        db.close()
    return html.Div("✓ Cours enregistré.", style={"color": "#10b981", "fontSize": ".85rem"}), _render_courses_grid(get_courses())

"""
SGA - Settings Page
System config, user management, database utilities
"""

from dash import html, dcc, Input, Output, State, callback, no_update
import hashlib
from models import SessionLocal, User


def layout():
    db = SessionLocal()
    try:
        users = db.query(User).all()
    finally:
        db.close()

    return html.Div([
        html.Div(style={"marginBottom": "1.5rem"}, className="animate-fade-up", children=[
            html.H2("Paramètres du Système", style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
            html.P("Configuration et gestion des utilisateurs",
                   style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
        ]),

        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1.25rem"}, children=[

            # Gestion utilisateurs
            html.Div(className="sga-card animate-fade-up-1", children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.5rem"}, children=[
                    html.Div(style={"width": "44px", "height": "44px", "borderRadius": "12px",
                                    "background": "rgba(99,102,241,.1)", "display": "flex", "alignItems": "center", "justifyContent": "center"},
                             children=[html.Span("manage_accounts", className="material-symbols-outlined", style={"color": "#6366f1", "fontSize": "1.3rem"})]),
                    html.H3("Gestion des Utilisateurs", style={"fontWeight": "700", "margin": 0}),
                ]),

                html.Table(className="sga-table", style={"marginBottom": "1.5rem"}, children=[
                    html.Thead(html.Tr([html.Th("Utilisateur"), html.Th("Rôle"), html.Th("Email")])),
                    html.Tbody([
                        html.Tr([
                            html.Td(html.Div(style={"display": "flex", "alignItems": "center", "gap": ".5rem"}, children=[
                                html.Div(u.username[:2].upper(), style={
                                    "width": "28px", "height": "28px", "borderRadius": "50%",
                                    "background": "var(--primary)", "color": "#fff", "display": "flex",
                                    "alignItems": "center", "justifyContent": "center", "fontSize": ".65rem", "fontWeight": "700",
                                }),
                                html.Span(u.nom_complet, style={"fontSize": ".85rem", "fontWeight": "600"}),
                            ])),
                            html.Td(html.Span(u.role.upper(), className="badge badge-blue" if u.role == "admin" else "badge badge-gray")),
                            html.Td(html.Span(u.email or "—", style={"fontSize": ".8rem", "color": "#64748b"})),
                        ])
                        for u in users
                    ]),
                ]),

                html.Div([
                    html.H4("Ajouter un utilisateur", style={"fontWeight": "700", "fontSize": ".9rem", "marginBottom": "1rem"}),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": ".75rem", "marginBottom": ".75rem"}, children=[
                        html.Div([html.Label("Nom complet", className="sga-label"),
                                  dcc.Input(id="new-user-nom", className="sga-input", placeholder="Nom...")]),
                        html.Div([html.Label("Identifiant", className="sga-label"),
                                  dcc.Input(id="new-user-username", className="sga-input", placeholder="username...")]),
                    ]),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": ".75rem", "marginBottom": ".75rem"}, children=[
                        html.Div([html.Label("Mot de passe", className="sga-label"),
                                  dcc.Input(id="new-user-pwd", type="password", className="sga-input", placeholder="••••••")]),
                        html.Div([html.Label("Rôle", className="sga-label"),
                                  dcc.Dropdown(id="new-user-role",
                                               options=[{"label": "Admin", "value": "admin"}, {"label": "Enseignant", "value": "teacher"}],
                                               value="teacher", clearable=False, style={"fontSize": ".875rem"})]),
                    ]),
                    html.Div(id="new-user-feedback", style={"marginBottom": ".75rem"}),
                    html.Button("Créer l'utilisateur", id="create-user-btn", n_clicks=0, className="btn-primary",
                                style={"fontSize": ".875rem"}),
                ]),
            ]),

            html.Div(style={"display": "flex", "flexDirection": "column", "gap": "1.25rem"}, children=[

                # DB Info
                html.Div(className="sga-card animate-fade-up-2", children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.25rem"}, children=[
                        html.Div(style={"width": "44px", "height": "44px", "borderRadius": "12px",
                                        "background": "#f0fdf4", "display": "flex", "alignItems": "center", "justifyContent": "center"},
                                 children=[html.Span("storage", className="material-symbols-outlined", style={"color": "#22c55e", "fontSize": "1.3rem"})]),
                        html.H3("Base de Données", style={"fontWeight": "700", "margin": 0}),
                    ]),
                    _db_info_block(),
                ]),

                # About
                html.Div(className="sga-card animate-fade-up-3", children=[
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1.25rem"}, children=[
                        html.Div(style={"width": "44px", "height": "44px", "borderRadius": "12px",
                                        "background": "#fdf4ff", "display": "flex", "alignItems": "center", "justifyContent": "center"},
                                 children=[html.Span("info", className="material-symbols-outlined", style={"color": "#a855f7", "fontSize": "1.3rem"})]),
                        html.H3("À Propos du SGA", style={"fontWeight": "700", "margin": 0}),
                    ]),
                    html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".5rem"}, children=[
                        _info_row("Version", "2.0.0"),
                        _info_row("Framework", "Dash Plotly"),
                        _info_row("Base de données", "PostgreSQL (Neon)"),
                        _info_row("ORM", "SQLAlchemy"),
                        _info_row("Design", "Lexend + Material Icons"),
                        _info_row("Animations", "CSS3 + GSAP"),
                    ]),
                ]),
            ]),
        ]),
    ])


def _db_info_block():
    db = SessionLocal()
    try:
        from models import Student, Course, Session, Attendance, Grade
        items = [
            ("Étudiants", db.query(Student).count(), "person", "#6366f1"),
            ("Cours", db.query(Course).count(), "menu_book", "#8b5cf6"),
            ("Séances", db.query(Session).count(), "calendar_today", "#f59e0b"),
            ("Présences", db.query(Attendance).count(), "how_to_reg", "#10b981"),
            ("Notes", db.query(Grade).count(), "grade", "#f43f5e"),
        ]
        return html.Div(style={"display": "flex", "flexDirection": "column", "gap": ".5rem"}, children=[
            html.Div(style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": ".5rem .75rem", "borderRadius": "8px", "background": "#f8fafc",
            }, children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": ".5rem"}, children=[
                    html.Span(icon, className="material-symbols-outlined", style={"fontSize": ".9rem", "color": color}),
                    html.Span(label, style={"fontSize": ".85rem", "color": "#64748b"}),
                ]),
                html.Span(str(count), style={"fontWeight": "700", "color": color}),
            ])
            for label, count, icon, color in items
        ])
    finally:
        db.close()


def _info_row(label, value):
    return html.Div(style={
        "display": "flex", "justifyContent": "space-between",
        "padding": ".4rem .75rem", "borderRadius": "8px", "background": "#f8fafc",
    }, children=[
        html.Span(label, style={"fontSize": ".85rem", "color": "#64748b"}),
        html.Span(value, style={"fontSize": ".85rem", "fontWeight": "600"}),
    ])


@callback(
    Output("new-user-feedback", "children"),
    Input("create-user-btn", "n_clicks"),
    State("new-user-nom", "value"),
    State("new-user-username", "value"),
    State("new-user-pwd", "value"),
    State("new-user-role", "value"),
    prevent_initial_call=True,
)
def create_user(n, nom, username, pwd, role):
    if not n:
        return no_update
    if not nom or not username or not pwd:
        return html.Div("Veuillez remplir tous les champs.", style={"color": "#f43f5e", "fontSize": ".85rem"})
    db = SessionLocal()
    try:
        if db.query(User).filter_by(username=username).first():
            return html.Div("Ce nom d'utilisateur est déjà pris.", style={"color": "#f43f5e", "fontSize": ".85rem"})
        u = User(
            username=username,
            password_hash=hashlib.sha256(pwd.encode()).hexdigest(),
            role=role,
            nom_complet=nom,
        )
        db.add(u)
        db.commit()
        return html.Div(f"✓ Utilisateur '{username}' créé.", style={"color": "#10b981", "fontWeight": "600", "fontSize": ".85rem"})
    except Exception as e:
        db.rollback()
        return html.Div(f"Erreur: {e}", style={"color": "#f43f5e", "fontSize": ".85rem"})
    finally:
        db.close()

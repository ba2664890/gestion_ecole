"""
SGA - Système de Gestion Académique
Main Application Entry Point with Dash Multi-Page + Auth
"""

import dash
from dash import Dash, html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import flask
from flask import session as flask_session
import hashlib
import os

from models import init_db, SessionLocal, User
from pages import (
    login, dashboard, students, courses, sessions, 
    analytics, reports, settings_page, grades,
    schedule, projects
)

# Init DB on startup
init_db()

# ────────────────────────────────────────────────────────────────────────────────
# App
# ────────────────────────────────────────────────────────────────────────────────
server = flask.Flask(__name__)
server.secret_key = os.environ.get("SECRET_KEY", "sga-secret-key-2024-ultra-secure")

app = Dash(
    __name__,
    server=server,
    use_pages=False,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700;800;900&display=swap",
        "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="SGA – Système de Gestion Académique",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# ────────────────────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────
# Layout
# ────────────────────────────────────────────────────────────────────────────────
def serve_layout():
    return html.Div([

        # Client-side store for auth state
        dcc.Store(id="auth-store", storage_type="session"),
        dcc.Store(id="current-page-store", data="/"),
        
        # UI State stores
        dcc.Store(id="notification-store", data=None),
        dcc.Store(id="global-trigger-store", data=None),

        # URL
        dcc.Location(id="url", refresh=False),

        # Toast notifications container
        html.Div(id="toast-container", className="toast-container"),

        # App shell (rendered conditionally)
        html.Div(id="app-shell"),
    ])


app.layout = serve_layout


# ────────────────────────────────────────────────────────────────────────────────
# Auth routing
# ────────────────────────────────────────────────────────────────────────────────
@callback(
    Output("app-shell", "children"),
    Input("url", "pathname"),
    Input("auth-store", "data"),
)
def route(pathname, auth_data):
    try:
        import dash
        # Si auth_data est None, le sessionStorage n'a pas encore été lu.
        # On vérifie le triggered_id pour savoir si l'input initial est le url ou le store.
        triggered = dash.callback_context.triggered_prop_ids
        
        is_auth = auth_data and auth_data.get("authenticated")

        if not is_auth:
            return login.layout()

        return shell_layout(pathname)
    except Exception as e:
        import traceback
        err_msg = f"Erreur de routage: {e}\n{traceback.format_exc()}"
        print(err_msg)
        return html.Div([
            html.H3("Erreur Critique d'Application", style={"color": "#ef4444"}),
            html.Pre(err_msg, style={"background": "#f8fafc", "padding": "1rem", "borderRadius": "10px"})
        ], style={"padding": "2rem"})


def shell_layout(pathname):
    nav_items = [
        {"icon": "dashboard", "label": "Tableau de Bord", "href": "/"},
        {"icon": "group", "label": "Étudiants", "href": "/students"},
        {"icon": "menu_book", "label": "Cours & Curriculum", "href": "/courses"},
        {"icon": "edit_calendar", "label": "Séances & Présences", "href": "/sessions"},
        {"icon": "grade", "label": "Notes & Évaluations", "href": "/grades"},
        {"icon": "analytics", "label": "Analytique", "href": "/analytics"},
        {"icon": "summarize", "label": "Rapports & Exports", "href": "/reports"},
        {"icon": "calendar_month", "label": "Emploi du Temps", "href": "/schedule"},
        {"icon": "assignment", "label": "Projets & Groupes", "href": "/projects"},
        {"icon": "settings", "label": "Paramètres", "href": "/settings"},
    ]

    sidebar = html.Div(id="sidebar", children=[
        # Logo
        html.Div(id="sidebar-logo", children=[
            html.Div(html.Span("school", className="material-symbols-outlined"), className="logo-icon"),
            html.Div([
                html.Div("SGA", className="logo-text"),
            ])
        ]),
        # Nav
        html.Nav([
            html.Div("PRINCIPAL", className="nav-section-label"),
            *[
                html.A(
                    [
                        html.Span(item["icon"], className="material-symbols-outlined mat-icon"),
                        item["label"]
                    ],
                    href=item["href"],
                    className=f"nav-item {'active' if pathname == item['href'] else ''}",
                    id={"type": "nav-link", "index": item["href"]}
                )
                for item in nav_items[:4]
            ],
            html.Div("ÉVALUATIONS", className="nav-section-label"),
            *[
                html.A(
                    [
                        html.Span(item["icon"], className="material-symbols-outlined mat-icon"),
                        item["label"]
                    ],
                    href=item["href"],
                    className=f"nav-item {'active' if pathname == item['href'] else ''}",
                )
                for item in nav_items[4:6]
            ],
            html.Div("VIE ÉTUDIANTE", className="nav-section-label"),
            *[
                html.A(
                    [
                        html.Span(item["icon"], className="material-symbols-outlined mat-icon"),
                        item["label"]
                    ],
                    href=item["href"],
                    className=f"nav-item {'active' if pathname == item['href'] else ''}",
                )
                for item in nav_items[7:9]
            ],
            html.Div("ADMINISTRATION", className="nav-section-label"),
            *[
                html.A(
                    [
                        html.Span(item["icon"], className="material-symbols-outlined mat-icon"),
                        item["label"]
                    ],
                    href=item["href"],
                    className=f"nav-item {'active' if pathname == item['href'] else ''}",
                )
                for item in [nav_items[6], nav_items[9]]
            ],
        ]),
        # Pomodoro Timer Widget
        html.Div(className="pomodoro-container", children=[
            html.Div("FOCUS MODE", className="pomo-label"),
            html.Div("25:00", id="pomo-display", className="pomo-timer"),
            html.Div(className="pomo-controls", children=[
                html.Button(html.Span("play_arrow", className="material-symbols-outlined"), id="pomo-start-btn", className="pomo-btn", n_clicks=0),
                html.Button(html.Span("refresh", className="material-symbols-outlined"), id="pomo-reset-btn", className="pomo-btn", n_clicks=0),
            ]),
            dcc.Interval(id="pomo-interval", interval=1000, disabled=True),
            dcc.Store(id="pomo-store", data={"seconds": 1500, "active": False})
        ]),

        # Footer
        html.Div(id="sidebar-footer", children=[
            html.Div(id="logout-btn", n_clicks=0, className="nav-item", style={"color": "#ef4444", "cursor": "pointer"}, children=[
                html.Span("logout", className="material-symbols-outlined mat-icon"),
                "Déconnexion"
            ]),
        ]),
    ])

    # Page content routing
    try:
        page_map = {
            "/": dashboard.layout,
            "/students": students.layout,
            "/courses": courses.layout,
            "/sessions": sessions.layout,
            "/grades": grades.layout,
            "/analytics": analytics.layout,
            "/reports": reports.layout,
            "/schedule": schedule.layout,
            "/projects": projects.layout,
            "/settings": settings_page.layout,
        }

        page_fn = page_map.get(pathname, dashboard.layout)
        page_content = page_fn()
    except Exception as e:
        import traceback
        page_content = html.Div([
            html.H3("Erreur de chargement de page", style={"color": "red"}),
            html.Pre(f"{e}\n{traceback.format_exc()}", style={"fontSize": ".8rem", "background": "#fff1f1", "padding": "1rem"})
        ], style={"padding": "2rem"})

    return html.Div([
        sidebar,
        html.Div(id="main-content", children=[
            # Topbar
            html.Div(id="topbar", children=[
                # Mobile menu
                html.Button(
                    html.Span("menu", className="material-symbols-outlined"),
                    id="mobile-menu-btn",
                    style={"background": "none", "border": "none", "cursor": "pointer", "display": "none"}
                ),
                html.Div([
                    html.H2(get_page_title(pathname), style={"fontSize": "1.1rem", "fontWeight": "700", "margin": 0}),
                    html.P(get_page_subtitle(pathname), style={"fontSize": ".8rem", "color": "#64748b", "margin": 0}),
                ]),
                # Actions (Search + Icons)
                html.Div([
                    html.Div(id="topbar-search", children=[
                        html.Span("search", className="material-symbols-outlined", style={"color": "#94a3b8", "fontSize": "1.1rem"}),
                        dcc.Input(placeholder="Rechercher...", style={
                            "border": "none", "background": "none", "outline": "none",
                            "fontSize": ".875rem", "fontFamily": "var(--font)", "width": "180px"
                        }),
                    ], style={
                        "display": "flex", "alignItems": "center", "gap": ".5rem",
                        "padding": ".5rem 1rem", "background": "#fff",
                        "borderRadius": "10px", "border": "1px solid #e2e8f0",
                    }),
                    
                    # Notifications
                    html.Div([
                        html.Div([
                            html.Span("notifications", className="material-symbols-outlined"),
                            html.Span(className="notification-dot pulse"), # Ping effect
                        ], className="notification-wrapper topbar-btn", id="btn-notifications"),
                        
                        html.Div(id="dropdown-notifications", className="topbar-dropdown", children=[
                            html.Div(className="dropdown-header", children=[
                                html.H4("Notifications"),
                                html.Span("3 nouvelles", style={"fontSize": ".7rem", "color": "var(--primary)", "fontWeight": "700"})
                            ]),
                            html.Div(className="dropdown-content", children=[
                                _dropdown_item("Nouvelle Note", "Un étudiant a reçu une nouvelle note en Mathématiques.", "grade", "#6366f1"),
                                _dropdown_item("Absence Signalée", "Awa Diop a été marquée absente ce matin.", "event_busy", "#f43f5e"),
                                _dropdown_item("Rapport Prêt", "Le rapport mensuel de présence est disponible.", "description", "#10b981"),
                            ]),
                            html.Div(className="dropdown-footer", children=[
                                html.A("Voir toutes les notifications", href="#")
                            ])
                        ])
                    ], style={"position": "relative"}),

                    # Account
                    html.Div([
                        html.Div([
                            html.Span("account_circle", className="material-symbols-outlined"),
                        ], className="topbar-btn", id="btn-account"),
                        
                        html.Div(id="dropdown-account", className="topbar-dropdown", children=[
                            html.Div(className="dropdown-header", children=[
                                html.H4("Mon Compte"),
                            ]),
                            html.Div(className="dropdown-content", children=[
                                _dropdown_item("Profil", "Voir vos informations personnelles", "person", "#6366f1"),
                                _dropdown_item("Paramètres", "Gérer votre compte", "settings", "#64748b"),
                                _dropdown_item("Support", "Besoin d'aide ?", "help", "#10b981"),
                            ]),
                            html.Div(className="dropdown-footer", children=[
                                html.A("Déconnexion", href="#", id="account-logout-btn", style={"color": "#f43f5e"})
                            ])
                        ])
                    ], style={"position": "relative"}),
                ], style={"display": "flex", "alignItems": "center", "gap": ".75rem"}),
            ]),
            # Page content
            html.Div(id="page-content", children=[page_content], className="animate-fade-in"),
            
            # Global Floating Action Button (FAB)
            html.Div(className="fab-container", children=[
                html.Div(className="fab-menu", children=[
                    html.Div([
                        html.Span("casino", className="material-symbols-outlined"),
                    ], className="fab-item", id="fab-random-gen", title="Générer Données Aléatoires"),
                    html.Div([
                        html.Span("add_task", className="material-symbols-outlined"),
                    ], className="fab-item", id="fab-new-project", title="Nouveau Projet"),
                ]),
                html.Button([
                    html.Span("add", className="material-symbols-outlined"),
                ], className="fab-main", id="fab-main-btn"),
            ]),
        ])
    ])


def get_page_title(path):
    titles = {
        "/": "Tableau de Bord",
        "/students": "Gestion des Étudiants",
        "/courses": "Curriculum & Cours",
        "/sessions": "Séances & Présences",
        "/grades": "Notes & Évaluations",
        "/analytics": "Analytique Académique",
        "/reports": "Rapports & Exports",
        "/schedule": "Emploi du Temps",
        "/projects": "Projets & Groupes",
        "/settings": "Paramètres",
    }
    return titles.get(path, "SGA")


def get_page_subtitle(path):
    subtitles = {
        "/": "Vue globale de l'établissement",
        "/students": "Gérer les fiches étudiants",
        "/courses": "Gérer les cours et progressions",
        "/sessions": "Appel numérique et cahier de texte",
        "/grades": "Saisie et suivi des évaluations",
        "/analytics": "Graphiques et statistiques",
        "/reports": "Génération et export de documents",
        "/schedule": "Organisation hebdomadaire des cours",
        "/projects": "Suivi des travaux de groupe ENSAE",
        "/settings": "Configuration du système",
    }
    return subtitles.get(path, "")


# ────────────────────────────────────────────────────────────────────────────────
# Logout
# ────────────────────────────────────────────────────────────────────────────────
@callback(
    Output("auth-store", "data", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n):
    if n:
        return {"authenticated": False}
    return no_update


@callback(
    Output("auth-store", "data", allow_duplicate=True),
    Input("account-logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def account_logout(n):
    if n:
        return {"authenticated": False}
    return no_update


@callback(
    Output("dropdown-notifications", "className"),
    Output("btn-notifications", "className"),
    Input("btn-notifications", "n_clicks"),
    State("dropdown-notifications", "className"),
    prevent_initial_call=True,
)
def toggle_notifications(n, current_class):
    if "show" in current_class:
        return "topbar-dropdown", "topbar-btn"
    return "topbar-dropdown show", "topbar-btn active"


@callback(
    Output("dropdown-account", "className"),
    Output("btn-account", "className"),
    Input("btn-account", "n_clicks"),
    State("dropdown-account", "className"),
    prevent_initial_call=True,
)
def toggle_account(n, current_class):
    if "show" in current_class:
        return "topbar-dropdown", "topbar-btn"
    return "topbar-dropdown show", "topbar-btn active"


def _dropdown_item(title, subtitle, icon, color):
    return html.Div(className="dropdown-item", children=[
        html.Div(className="item-icon", style={"color": color}, children=[
            html.Span(icon, className="material-symbols-outlined")
        ]),
        html.Div(className="item-text", children=[
            html.H5(title),
            html.P(subtitle)
        ])
    ])


@callback(
    Output("pomo-store", "data"),
    Output("pomo-interval", "disabled"),
    Output("pomo-start-btn", "children"),
    Output("pomo-start-btn", "className"),
    Input("pomo-start-btn", "n_clicks"),
    Input("pomo-reset-btn", "n_clicks"),
    Input("pomo-interval", "n_intervals"),
    State("pomo-store", "data"),
    prevent_initial_call=True
)
def update_pomo(start_n, reset_n, n_int, data):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered: return no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "pomo-reset-btn":
        return {"seconds": 1500, "active": False}, True, html.Span("play_arrow", className="material-symbols-outlined"), "pomo-btn"
    
    if trigger_id == "pomo-start-btn":
        new_active = not data["active"]
        icon = "pause" if new_active else "play_arrow"
        btn_class = "pomo-btn active" if new_active else "pomo-btn"
        return {"seconds": data["seconds"], "active": new_active}, not new_active, html.Span(icon, className="material-symbols-outlined"), btn_class
        
    if trigger_id == "pomo-interval":
        if data["active"] and data["seconds"] > 0:
            new_secs = data["seconds"] - 1
            return {"seconds": new_secs, "active": True}, False, no_update, no_update
        elif data["seconds"] <= 0:
            return {"seconds": 0, "active": False}, True, html.Span("notifications_active", className="material-symbols-outlined"), "pomo-btn"
            
    return no_update

@callback(
    Output("pomo-display", "children"),
    Output("pomo-display", "className"),
    Input("pomo-store", "data")
)
def display_pomo(data):
    s = data["seconds"]
    mins = s // 60
    secs = s % 60
    display = f"{mins:02d}:{secs:02d}"
    class_name = "pomo-timer pomo-urgent" if s < 60 and s > 0 else "pomo-timer"
    return display, class_name

@callback(
    Output("notification-store", "data"),
    Input("fab-random-gen", "n_clicks"),
    prevent_initial_call=True
)
def trigger_random_gen(n):
    if not n: return no_update
    try:
        from utils.seeding import generate_random_projects, generate_random_schedule
        generate_random_projects(3)
        generate_random_schedule()
        return {"message": "Données aléatoires générées avec succès !", "type": "success"}
    except Exception as e:
        return {"message": f"Erreur lors de la génération : {e}", "type": "error"}

@callback(
    Output("toast-container", "children"),
    Input("notification-store", "data"),
    prevent_initial_call=True
)
def show_toast(data):
    if not data: return no_update
    icon = "check_circle" if data["type"] == "success" else "error"
    return html.Div(className=f"toast {data['type']}", children=[
        html.Span(icon, className="material-symbols-outlined"),
        html.Div(data["message"])
    ])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

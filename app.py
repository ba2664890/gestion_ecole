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
    use_pages=True,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700;800;900&display=swap",
        "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="SGA – Système de Gestion Académique",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# ────────────────────────────────────────────────────────────────────────────────
# Global CSS Injection (design tokens + GSAP-like animations via CSS)
# ────────────────────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
:root {
  --primary: #13a4ec;
  --primary-dark: #0e8bc9;
  --bg-light: #f6f7f8;
  --bg-dark: #101c22;
  --sidebar-w: 260px;
  --font: 'Lexend', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; }

body {
  font-family: var(--font);
  background: var(--bg-light);
  color: #0f172a;
  min-height: 100vh;
  overflow-x: hidden;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }

/* ─── Sidebar ─── */
#sidebar {
  position: fixed; left: 0; top: 0; bottom: 0;
  width: var(--sidebar-w);
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex; flex-direction: column;
  z-index: 100;
  transition: transform .35s cubic-bezier(.4,0,.2,1);
}

#sidebar-logo {
  padding: 1.5rem 1.25rem;
  display: flex; align-items: center; gap: .75rem;
  border-bottom: 1px solid #f1f5f9;
}

#sidebar-logo .logo-icon {
  width: 40px; height: 40px;
  background: var(--primary);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 1.25rem;
}

#sidebar-logo .logo-text {
  font-size: 1.1rem; font-weight: 800;
  color: #0f172a; letter-spacing: -.02em;
}

#sidebar nav { flex: 1; padding: .75rem .75rem; overflow-y: auto; }

.nav-item {
  display: flex; align-items: center; gap: .75rem;
  padding: .65rem 1rem;
  border-radius: 10px;
  font-size: .875rem; font-weight: 500;
  color: #64748b;
  text-decoration: none;
  transition: all .2s ease;
  cursor: pointer;
  border: none; background: none; width: 100%;
  margin-bottom: 2px;
}
.nav-item:hover { background: #f1f5f9; color: #0f172a; }
.nav-item.active { background: rgba(19,164,236,.08); color: var(--primary); font-weight: 600; }
.nav-item .mat-icon { font-size: 1.25rem; }

.nav-section-label {
  font-size: .65rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: #94a3b8;
  padding: .5rem 1rem .25rem;
  margin-top: .5rem;
}

#sidebar-footer {
  padding: .75rem;
  border-top: 1px solid #f1f5f9;
}

.user-card {
  display: flex; align-items: center; gap: .75rem;
  padding: .75rem;
  border-radius: 10px;
  background: #f8fafc;
}

.user-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  font-size: .8rem; flex-shrink: 0;
}

.user-info .user-name { font-size: .8rem; font-weight: 600; }
.user-info .user-role { font-size: .7rem; color: #94a3b8; }

/* ─── Main Content ─── */
#main-content {
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  display: flex; flex-direction: column;
}

#topbar {
  position: sticky; top: 0; z-index: 90;
  background: rgba(246,247,248,.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226,232,240,.8);
  padding: .85rem 2rem;
  display: flex; align-items: center; justify-content: space-between;
}

#page-content { flex: 1; padding: 2rem; }

/* ─── Cards ─── */
.sga-card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
  padding: 1.5rem;
  transition: box-shadow .2s ease;
}
.sga-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.07); }

.kpi-card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  padding: 1.25rem 1.5rem;
  display: flex; flex-direction: column; gap: .5rem;
  transition: transform .2s ease, box-shadow .2s ease;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.08); }

.kpi-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem;
}

.kpi-value { font-size: 2rem; font-weight: 800; letter-spacing: -.03em; }
.kpi-label { font-size: .8rem; color: #64748b; font-weight: 500; }
.kpi-delta { font-size: .75rem; font-weight: 700; }
.kpi-delta.up { color: #10b981; }
.kpi-delta.down { color: #ef4444; }

/* ─── Buttons ─── */
.btn-primary {
  display: inline-flex; align-items: center; gap: .5rem;
  padding: .6rem 1.25rem;
  background: var(--primary);
  color: #fff;
  border: none; border-radius: 10px;
  font-size: .875rem; font-weight: 600;
  font-family: var(--font);
  cursor: pointer;
  transition: all .2s ease;
  box-shadow: 0 4px 12px rgba(19,164,236,.25);
  text-decoration: none;
}
.btn-primary:hover { background: var(--primary-dark); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(19,164,236,.35); }
.btn-primary:active { transform: scale(.97); }

.btn-secondary {
  display: inline-flex; align-items: center; gap: .5rem;
  padding: .6rem 1.25rem;
  background: #fff; color: #374151;
  border: 1px solid #e2e8f0; border-radius: 10px;
  font-size: .875rem; font-weight: 600;
  font-family: var(--font);
  cursor: pointer;
  transition: all .2s ease;
}
.btn-secondary:hover { background: #f8fafc; border-color: #cbd5e1; }

.btn-danger {
  display: inline-flex; align-items: center; gap: .5rem;
  padding: .6rem 1.25rem;
  background: #fff; color: #ef4444;
  border: 1px solid #fecaca; border-radius: 10px;
  font-size: .875rem; font-weight: 600;
  font-family: var(--font);
  cursor: pointer;
  transition: all .2s ease;
}
.btn-danger:hover { background: #fef2f2; }

/* ─── Inputs ─── */
.sga-input, .sga-select, .sga-textarea {
  width: 100%;
  padding: .65rem 1rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: .875rem;
  font-family: var(--font);
  color: #0f172a;
  background: #f8fafc;
  transition: border-color .2s ease, box-shadow .2s ease;
  outline: none;
}
.sga-input:focus, .sga-select:focus, .sga-textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(19,164,236,.1);
  background: #fff;
}
.sga-label { font-size: .8rem; font-weight: 600; color: #374151; margin-bottom: .35rem; display: block; }

/* ─── Table ─── */
.sga-table { width: 100%; border-collapse: collapse; }
.sga-table th {
  padding: .75rem 1rem;
  font-size: .7rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .06em;
  color: #94a3b8;
  border-bottom: 1px solid #f1f5f9;
  text-align: left; white-space: nowrap;
}
.sga-table td {
  padding: .9rem 1rem;
  font-size: .875rem;
  border-bottom: 1px solid #f8fafc;
  color: #374151;
}
.sga-table tbody tr { transition: background .15s; }
.sga-table tbody tr:hover { background: #f8fafc; }
.sga-table tbody tr:last-child td { border-bottom: none; }

/* ─── Badge ─── */
.badge {
  display: inline-flex; align-items: center;
  padding: .2rem .6rem;
  border-radius: 99px;
  font-size: .7rem; font-weight: 700;
}
.badge-blue { background: rgba(19,164,236,.1); color: var(--primary); }
.badge-green { background: #d1fae5; color: #065f46; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-orange { background: #ffedd5; color: #9a3412; }
.badge-gray { background: #f1f5f9; color: #64748b; }

/* ─── Progress Bar ─── */
.progress-wrap { background: #f1f5f9; border-radius: 99px; overflow: hidden; height: 8px; }
.progress-fill {
  height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, var(--primary), #38bdf8);
  transition: width .8s cubic-bezier(.4,0,.2,1);
}
.progress-fill.danger { background: linear-gradient(90deg, #ef4444, #f97316); }
.progress-fill.success { background: linear-gradient(90deg, #10b981, #34d399); }

/* ─── Login Page ─── */
#login-page {
  min-height: 100vh;
  display: flex;
}
.login-left {
  flex: 1;
  background: var(--primary);
  position: relative; overflow: hidden;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 3rem;
}
.login-right {
  width: 480px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  padding: 3rem;
}

/* ─── Animations ─── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes floatA {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-18px) rotate(5deg); }
}
@keyframes floatB {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-12px) rotate(-4deg); }
}
@keyframes pulse-ring {
  0% { transform: scale(1); opacity: .6; }
  100% { transform: scale(1.8); opacity: 0; }
}
@keyframes gradient-shift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes count-up {
  from { opacity: 0; transform: scale(.8); }
  to { opacity: 1; transform: scale(1); }
}

.animate-fade-up { animation: fadeUp .5s ease both; }
.animate-fade-up-1 { animation: fadeUp .5s .1s ease both; }
.animate-fade-up-2 { animation: fadeUp .5s .2s ease both; }
.animate-fade-up-3 { animation: fadeUp .5s .3s ease both; }
.animate-fade-up-4 { animation: fadeUp .5s .4s ease both; }
.animate-fade-in { animation: fadeIn .4s ease both; }
.animate-slide-in { animation: slideIn .4s ease both; }

/* ─── Responsive ─── */
@media (max-width: 768px) {
  #sidebar { transform: translateX(-100%); }
  #sidebar.open { transform: translateX(0); }
  #main-content { margin-left: 0; }
  .login-left { display: none; }
  .login-right { width: 100%; }
  #page-content { padding: 1rem; }
}

/* ─── Dash Overrides ─── */
.dash-dropdown .Select-control { border: 1.5px solid #e2e8f0 !important; border-radius: 10px !important; font-family: var(--font) !important; }
.dash-dropdown .Select-control:hover { border-color: var(--primary) !important; }
._dash-loading { display: none !important; }

/* ─── Upload Zone ─── */
.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  cursor: pointer;
  transition: all .2s ease;
  background: #f8fafc;
}
.upload-zone:hover {
  border-color: var(--primary);
  background: rgba(19,164,236,.03);
}

/* ─── Tab Navigation ─── */
.tab-nav {
  display: flex; gap: .25rem;
  background: #f1f5f9; padding: .25rem;
  border-radius: 12px; margin-bottom: 1.5rem;
}
.tab-btn {
  flex: 1; padding: .6rem 1rem;
  border: none; border-radius: 9px;
  font-family: var(--font); font-size: .8rem; font-weight: 600;
  cursor: pointer; transition: all .2s ease;
  background: transparent; color: #64748b;
}
.tab-btn.active { background: #fff; color: #0f172a; box-shadow: 0 1px 4px rgba(0,0,0,.08); }

/* ─── Notification Toast ─── */
.toast-container { position: fixed; top: 1rem; right: 1rem; z-index: 9999; display: flex; flex-direction: column; gap: .5rem; }
.toast {
  background: #fff; border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
  padding: 1rem 1.25rem;
  display: flex; align-items: center; gap: .75rem;
  animation: fadeUp .3s ease;
  border-left: 4px solid var(--primary);
  min-width: 280px;
}
.toast.success { border-color: #10b981; }
.toast.error { border-color: #ef4444; }
.toast.warning { border-color: #f59e0b; }

/* ─── Hero Video Background ─── */
.hero-video-wrap {
  position: absolute; inset: 0; overflow: hidden;
}
.hero-video-wrap video {
  width: 100%; height: 100%; object-fit: cover;
  opacity: .18;
}
.hero-video-wrap::after {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(19,164,236,.85) 0%, rgba(14,139,201,.7) 100%);
}

/* ─── Stat ring ─── */
.stat-ring {
  position: relative; width: 80px; height: 80px;
}
.stat-ring svg { transform: rotate(-90deg); }
.stat-ring-text {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: .9rem; font-weight: 800;
}

/* ─── Checklist custom ─── */
.custom-checklist { display: flex; flex-direction: column; gap: .5rem; }
.custom-checklist-item {
  display: flex; align-items: center; gap: .75rem;
  padding: .65rem 1rem;
  border-radius: 10px;
  border: 1.5px solid #e2e8f0;
  transition: all .15s ease;
  cursor: pointer;
}
.custom-checklist-item:hover { border-color: var(--primary); background: rgba(19,164,236,.02); }
.custom-checklist-item.checked { border-color: #ef4444; background: #fef2f2; }
"""

# ────────────────────────────────────────────────────────────────────────────────
# Layout
# ────────────────────────────────────────────────────────────────────────────────
def serve_layout():
    return html.Div([
        # Global CSS
        html.Style(GLOBAL_CSS),

        # Client-side store for auth state
        dcc.Store(id="auth-store", storage_type="session"),
        dcc.Store(id="current-page-store", data="/"),

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
    from pages import login, dashboard, students, courses, sessions, analytics, reports, settings_page
    is_auth = auth_data and auth_data.get("authenticated")

    if not is_auth:
        return login.layout()

    return shell_layout(pathname)


def shell_layout(pathname):
    nav_items = [
        {"icon": "dashboard", "label": "Tableau de Bord", "href": "/"},
        {"icon": "group", "label": "Étudiants", "href": "/students"},
        {"icon": "menu_book", "label": "Cours & Curriculum", "href": "/courses"},
        {"icon": "edit_calendar", "label": "Séances & Présences", "href": "/sessions"},
        {"icon": "grade", "label": "Notes & Évaluations", "href": "/grades"},
        {"icon": "analytics", "label": "Analytique", "href": "/analytics"},
        {"icon": "summarize", "label": "Rapports & Exports", "href": "/reports"},
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
                for item in nav_items[6:]
            ],
        ]),
        # Footer
        html.Div(id="sidebar-footer", children=[
            html.Div(id="logout-btn", n_clicks=0, className="nav-item", style={"color": "#ef4444"}, children=[
                html.Span("logout", className="material-symbols-outlined mat-icon"),
                "Déconnexion"
            ]),
        ]),
    ])

    # Page content routing
    from pages import dashboard, students, courses, sessions, grades, analytics, reports, settings_page
    page_map = {
        "/": dashboard.layout,
        "/students": students.layout,
        "/courses": courses.layout,
        "/sessions": sessions.layout,
        "/grades": grades.layout,
        "/analytics": analytics.layout,
        "/reports": reports.layout,
        "/settings": settings_page.layout,
    }

    page_fn = page_map.get(pathname, dashboard.layout)
    try:
        page_content = page_fn()
    except Exception as e:
        page_content = html.Div(f"Erreur: {e}", style={"color": "red", "padding": "2rem"})

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
                    html.Div([
                        html.Span("notifications", className="material-symbols-outlined"),
                    ], style={
                        "width": "38px", "height": "38px", "borderRadius": "10px",
                        "background": "#fff", "border": "1px solid #e2e8f0",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "cursor": "pointer", "color": "#64748b",
                    }),
                ], style={"display": "flex", "alignItems": "center", "gap": ".75rem"}),
            ]),
            # Page content
            html.Div(id="page-content", children=[page_content], className="animate-fade-in"),
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

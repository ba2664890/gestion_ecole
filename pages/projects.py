"""
SGA - Projets & Groupes Page
Premium Kanban board for ENSAE student project tracking with CRUD.
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ALL, no_update
import dash_bootstrap_components as dbc
from models import SessionLocal, Project, Course
from sqlalchemy.orm import joinedload

def get_projects():
    db = SessionLocal()
    try:
        return db.query(Project).options(joinedload(Project.course)).all()
    finally:
        db.close()

def get_courses():
    db = SessionLocal()
    try:
        return db.query(Course).all()
    finally:
        db.close()

def layout():
    all_projects = get_projects()
    courses = get_courses()
    
    projects_to_do = [p for p in all_projects if p.status == "To Do"]
    projects_in_progress = [p for p in all_projects if p.status == "In Progress"]
    projects_done = [p for p in all_projects if p.status == "Done"]

    return html.Div(className="animate-fade-in", children=[
        # Stats Bar (Premium KPIs)
        html.Div(className="kpi-grid", children=[
            _mini_stat("Projets actifs", str(len(projects_to_do) + len(projects_in_progress)), "assignment", "badge-blue"),
            _mini_stat("Urgent", str(sum(1 for p in all_projects if p.priority == "badge-red")), "priority_high", "badge-red"),
            _mini_stat("Membres totaux", str(sum(p.members for p in all_projects)), "group", "badge-purple"),
            _mini_stat("Complétion", f"{len(projects_done)/len(all_projects)*100 if all_projects else 0:.0f}%", "rocket_launch", "badge-green"),
        ]),

        # Kanban Board
        html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "2rem"}, children=[
            _kanban_column("À FAIRE", projects_to_do, "badge-gray", "todo-list"),
            _kanban_column("EN COURS", projects_in_progress, "badge-blue", "progress-list"),
            _kanban_column("TERMINÉ", projects_done, "badge-green", "done-list"),
        ]),

        # Modals
        _project_modal(courses),
        
        # Hidden div for deletion trigger
        html.Div(id="project-delete-trigger", style={"display": "none"}),
        
        # Interval for refresh (optional, but good for real-time feel)
        dcc.Interval(id="projects-refresh-interval", interval=5000, n_intervals=0),
    ])

def _mini_stat(label, value, icon, color_class):
    return html.Div(className="kpi-card-v2", children=[
        html.Div(className=f"kpi-icon-v2 {color_class}", children=[
            html.Span(icon, className="material-symbols-outlined")
        ]),
        html.Div([
            html.Div(label, style={"fontSize": ".8rem", "color": "var(--text-secondary)", "fontWeight": "600"}),
            html.Div(value, style={"fontSize": "1.8rem", "fontWeight": "800", "color": "var(--text-primary)", "lineHeight": "1.2"})
        ])
    ])

def _kanban_column(title, projects, color, list_id):
    return html.Div(className="kanban-column", children=[
        html.Div(className="kanban-header", style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}, children=[
            html.Span(title, style={"fontSize": ".85rem", "fontWeight": "800", "color": "var(--text-primary)"}),
            html.Span(str(len(projects)), className=f"badge {color}", style={"borderRadius": "99px", "padding": "0.4rem 0.8rem"})
        ]),
        html.Div(id=list_id, style={"display": "flex", "flexDirection": "column", "gap": "1rem"}, children=[
            _project_card(p) for p in projects
        ] if projects else [
            html.Div("Aucun projet", style={"textAlign": "center", "padding": "3rem 1rem", "border": "2px dashed var(--border-light)", "borderRadius": "20px", "color": "var(--text-muted)", "fontSize": "0.85rem"})
        ])
    ])

def _project_card(p):
    return html.Div(className="sga-card", style={"padding": "1.25rem", "border": "1px solid rgba(255,255,255,0.8)"}, children=[
        html.Div([
            html.Span(p.status, className=f"badge {p.priority}", style={"fontSize": ".65rem", "padding": "0.3rem 0.6rem"}),
            html.Div(className="card-actions", children=[
                html.Span("edit", id={"type": "edit-p", "index": p.id}, className="material-symbols-outlined", style={"cursor": "pointer", "fontSize": "1.2rem", "color": "var(--text-muted)"}),
                html.Span("delete", id={"type": "delete-p", "index": p.id}, className="material-symbols-outlined", style={"cursor": "pointer", "fontSize": "1.2rem", "color": "var(--danger)", "marginLeft": "8px"}),
            ])
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "0.75rem"}),
        
        html.Div(p.title, style={"fontSize": "1rem", "fontWeight": "800", "color": "var(--text-primary)", "marginBottom": "0.5rem"}),
        html.Div(p.course.libelle if p.course else "", style={"fontSize": "0.75rem", "fontWeight": "600", "color": "var(--text-secondary)", "marginBottom": "1.25rem"}),
        
        # Progress
        html.Div(style={"marginBottom": "1rem"}, children=[
            html.Div(className="progress-wrap", children=[
                html.Div(className="progress-fill", style={"width": f"{p.progress}%"}, children=[
                    html.Div(className="progress-glow")
                ])
            ]),
            html.Div(f"{p.progress}%", style={"textAlign": "right", "fontSize": "0.7rem", "fontWeight": "700", "color": "var(--text-muted)", "marginTop": "4px"})
        ]),
        
        # Footer
        html.Div(style={"display": "flex", "justifyContent": "space-between", "borderTop": "1px solid var(--border-light)", "paddingTop": "0.75rem", "marginTop": "0.25rem"}, children=[
            html.Div([
                html.Span("calendar_today", className="material-symbols-outlined", style={"fontSize": "0.9rem", "verticalAlign": "middle", "marginRight": "4px", "color": "var(--text-muted)"}),
                html.Span(p.deadline, style={"fontSize": "0.75rem", "fontWeight": "700"})
            ]),
            html.Div([
                html.Span("group", className="material-symbols-outlined", style={"fontSize": "0.9rem", "verticalAlign": "middle", "marginRight": "4px", "color": "var(--text-muted)"}),
                html.Span(str(p.members), style={"fontSize": "0.75rem", "fontWeight": "700"})
            ])
        ])
    ])

def _project_modal(courses):
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Détails du Projet", style={"fontWeight": "800", "fontSize": "1.25rem"}), close_button=True, style={"borderBottom": "none", "padding": "1.5rem 1.5rem 0.5rem"}),
        dbc.ModalBody(style={"padding": "0.5rem 1.5rem 1.5rem"}, children=[
            html.Div([
                html.Label("Titre du Projet", className="sga-label"),
                dbc.Input(id="p-title", placeholder="Nom du projet...", className="sga-input mb-3"),
                
                html.Label("Cours associé", className="sga-label"),
                dcc.Dropdown(
                    id="p-course",
                    options=[{"label": c.libelle, "value": c.id} for c in courses],
                    className="sga-select mb-3"
                ),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Statut", className="sga-label"),
                        dcc.Dropdown(
                            id="p-status",
                            options=[{"label": s, "value": s} for s in ["To Do", "In Progress", "Done"]],
                            value="To Do",
                            className="sga-select mb-3"
                        ),
                    ]),
                    dbc.Col([
                        html.Label("Priorité", className="sga-label"),
                        dcc.Dropdown(
                            id="p-priority",
                            options=[
                                {"label": "Urgent", "value": "badge-red"},
                                {"label": "Important", "value": "badge-orange"},
                                {"label": "Normal", "value": "badge-blue"},
                                {"label": "Faible", "value": "badge-green"},
                            ],
                            value="badge-blue",
                            className="sga-select mb-3"
                        ),
                    ]),
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Échéance", className="sga-label"),
                        dbc.Input(id="p-deadline", placeholder="Ex: 25 Mars", className="sga-input mb-3"),
                    ]),
                    dbc.Col([
                        html.Label("Progression (%)", className="sga-label"),
                        dbc.Input(id="p-progress", type="number", min=0, max=100, value=0, className="sga-input mb-3"),
                    ]),
                ]),
                
                html.Label("Membres", className="sga-label"),
                dbc.Input(id="p-members", type="number", min=1, value=1, className="sga-input mb-3"),
                
                dcc.Store(id="editing-p-id", data=None),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Annuler", id="close-p-modal", className="btn-secondary", style={"background": "transparent", "border": "none", "boxShadow": "none", "color": "#64748b"}),
            dbc.Button("Enregistrer", id="save-p-btn", className="btn-primary", style={"borderRadius": "12px", "padding": "0.7rem 2rem", "boxShadow": "0 8px 20px rgba(99, 102, 241, 0.3)"}),
        ], style={"borderTop": "none", "padding": "0.5rem 1.5rem 1.5rem"}),
    ], id="project-modal", is_open=False, centered=True, size="lg")

# ────────────────────────────────────────────────────────────────────────────────
# Callbacks
# ────────────────────────────────────────────────────────────────────────────────

@callback(
    Output("project-modal", "is_open"),
    Output("p-title", "value"),
    Output("p-course", "value"),
    Output("p-status", "value"),
    Output("p-priority", "value"),
    Output("p-deadline", "value"),
    Output("p-progress", "value"),
    Output("p-members", "value"),
    Output("editing-p-id", "data"),
    Input("fab-new-project", "n_clicks"),
    Input({"type": "edit-p", "index": ALL}, "n_clicks"),
    Input("close-p-modal", "n_clicks"),
    Input("save-p-btn", "n_clicks"),
    State("project-modal", "is_open"),
    State("p-title", "value"),
    State("p-course", "value"),
    State("p-status", "value"),
    State("p-priority", "value"),
    State("p-deadline", "value"),
    State("p-progress", "value"),
    State("p-members", "value"),
    State("editing-p-id", "data"),
    prevent_initial_call=True
)
def manage_project_modal(new_n, edit_n, close_n, save_n, is_open, title, course, status, priority, deadline, progress, members, e_id):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0].get("value"): return no_update
    
    tid = ctx.triggered[0]["prop_id"]
    
    if "fab-new-project" in tid:
        return True, "", None, "To Do", "badge-blue", "", 0, 1, None
        
    if "edit-p" in tid:
        pid = int(tid.split(",")[0].split(":")[1])
        db = SessionLocal()
        p = db.query(Project).get(pid)
        db.close()
        if p:
            return True, p.title, p.course_id, p.status, p.priority, p.deadline, p.progress, p.members, p.id
            
    if "close-p-modal" in tid:
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    if "save-p-btn" in tid:
        db = SessionLocal()
        if e_id:
            p = db.query(Project).get(e_id)
            if p:
                p.title = title
                p.course_id = course
                p.status = status
                p.priority = priority
                p.deadline = deadline
                p.progress = progress
                p.members = members
        else:
            p = Project(title=title, course_id=course, status=status, priority=priority, deadline=deadline, progress=progress, members=members)
            db.add(p)
        db.commit()
        db.close()
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    return no_update

@callback(
    Output("project-delete-trigger", "children"),
    Input({"type": "delete-p", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def delete_project_callback(n_clicks):
    if not any(n_clicks): return no_update
    ctx = dash.callback_context
    tid = ctx.triggered[0]["prop_id"]
    pid = int(tid.split(",")[0].split(":")[1])
    
    db = SessionLocal()
    p = db.query(Project).get(pid)
    if p:
        db.delete(p)
        db.commit()
    db.close()
    return f"deleted-{pid}"

@callback(
    Output("todo-list", "children"),
    Output("progress-list", "children"),
    Output("done-list", "children"),
    Input("projects-refresh-interval", "n_intervals"),
    Input("project-delete-trigger", "children"),
    Input("project-modal", "is_open"),
    Input("notification-store", "data"),
    prevent_initial_call=True
)
def refresh_project_board(n, del_trig, is_modal_open, notif):
    if is_modal_open: return no_update
    
    projs = get_projects()
    
    todo = [_project_card(p) for p in projs if p.status == "To Do"]
    in_p = [_project_card(p) for p in projs if p.status == "In Progress"]
    done = [_project_card(p) for p in projs if p.status == "Done"]
    
    empty = html.Div("Aucun projet", style={"textAlign": "center", "padding": "2rem", "border": "2px dashed var(--border-light)", "borderRadius": "20px", "color": "var(--text-muted)", "fontSize": "0.8rem"})
    
    return todo or [empty], in_p or [empty], done or [empty]

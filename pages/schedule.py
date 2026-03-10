"""
SGA - Emploi du Temps Page
Premium interactive weekly calendar with CRUD for ENSAE students.
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ALL, no_update
import dash_bootstrap_components as dbc
from datetime import datetime, date, timedelta
from models import SessionLocal, Session, Course
from sqlalchemy.orm import joinedload

def get_week_range(target_date):
    start = target_date - timedelta(days=target_date.weekday())
    end = start + timedelta(days=6)
    return start, end

def get_schedule_data(start_date, end_date):
    db = SessionLocal()
    try:
        return db.query(Session).options(joinedload(Session.course))\
            .filter(Session.date >= start_date, Session.date <= end_date).all()
    finally:
        db.close()

def get_courses():
    db = SessionLocal()
    try:
        return db.query(Course).all()
    finally:
        db.close()

def layout():
    today = date.today()
    start_week, end_week = get_week_range(today)
    sessions = get_schedule_data(start_week, end_week)
    courses = get_courses()
    
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    hours = list(range(8, 20)) # 8h to 19h

    # Header
    header = html.Div(className="sga-card mb-4 animate-fade-in", children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
            html.Div([
                html.H3(f"Semaine du {start_week.strftime('%d %B')} au {end_week.strftime('%d %B %Y')}", style={"margin": 0, "fontWeight": "800"}),
                html.P("Gestion interactive de l'emploi du temps", className="text-muted", style={"margin": 0, "fontSize": ".85rem"}),
            ]),
            html.Div(style={"display": "flex", "gap": "1rem"}, children=[
                html.Button([
                    html.Span("refresh", className="material-symbols-outlined", style={"fontSize": "1.1rem", "verticalAlign": "middle", "marginRight": "6px"}),
                    "Actualiser"
                ], id="refresh-schedule-btn", style={
                    "background": "#fff", "border": "1px solid #e2e8f0", "color": "#64748b",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.02)", "borderRadius": "10px", "padding": "0.6rem 1.2rem",
                    "fontWeight": "600", "fontSize": "0.85rem", "display": "flex", "alignItems": "center", "cursor": "pointer"
                }),
            ])
        ])
    ])

    return html.Div(className="animate-fade-in", children=[
        header,
        
        # Grid Container
        html.Div(className="sga-card", style={"padding": "0", "overflow": "hidden"}, children=[
            html.Div(id="schedule-grid-container", children=_render_grid(start_week, sessions))
        ]),

        # Modal
        _session_modal(courses),
        
        # Store for delete and refresh
        html.Div(id="session-delete-trigger", style={"display": "none"}),
        dcc.Interval(id="schedule-refresh-interval", interval=10000, n_intervals=0),
    ])

def _render_grid(start_week, sessions):
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    hours = list(range(8, 20))
    
    # Grid Header (Days)
    header_cells = [html.Div(style={"background": "var(--bg-light)", "height": "50px"})] # Corner cell
    for i, day in enumerate(days):
        current_day = start_week + timedelta(days=i)
        header_cells.append(html.Div(className="grid-header-cell", style={
            "background": "var(--bg-light)", "padding": "1rem", "textAlign": "center", 
            "borderLeft": "1px solid var(--border-light)", "display": "flex", 
            "flexDirection": "column", "justifyContent": "center", "borderBottom": "1px solid var(--border-light)"
        }, children=[
            html.Span(day, style={"fontSize": ".85rem", "fontWeight": "800", "color": "var(--text-muted)", "textTransform": "uppercase"}),
            html.Span(current_day.strftime("%d %b"), style={"fontSize": "1.1rem", "fontWeight": "800", "color": "var(--text-primary)"})
        ]))

    # Hourly rows
    grid_body = []
    for h in hours:
        # Hour label
        row = [html.Div(f"{h}:00", style={
            "padding": "1rem .5rem", "fontSize": ".85rem", "fontWeight": "800", 
            "color": "var(--text-primary)", "textAlign": "right", "background": "var(--bg-light)",
            "borderBottom": "1px solid var(--border-light)", "borderRight": "1px solid var(--border-light)",
            "display": "flex", "flexDirection": "column", "justifyContent": "center"
        })]
        
        # Cells for each day
        for day_idx in range(5):
            cell_content = []
            for s in sessions:
                s_day = s.date.weekday()
                try:
                    s_hour = int(s.start_time.split(":")[0])
                except: s_hour = 8
                
                if s_day == day_idx and s_hour == h:
                    cell_content.append(_render_session_block(s))
            
            row.append(html.Div(className="schedule-cell", style={
                "position": "relative", "background": "#fff", "minHeight": "80px",
                "borderLeft": "1px solid var(--border-light)", "borderBottom": "1px solid var(--border-light)"
            }, children=cell_content))
        grid_body.extend(row)

    return html.Div(style={
        "display": "grid", "gridTemplateColumns": "80px repeat(5, 1fr)",
        "background": "var(--border-light)"
    }, children=header_cells + grid_body)

def _render_session_block(s):
    # Determine color based on course
    color_map = {
        "MATH": "badge-blue",
        "INFO": "badge-purple",
        "ECON": "badge-green",
        "PHYS": "badge-red"
    }
    course_code = s.course.code if s.course else ""
    color = "badge-gray"
    for k, v in color_map.items():
        if k in course_code:
            color = v; break
            
    return html.Div(className=f"course-block {color} animate-scale-in", id={"type": "session-block", "index": s.id}, style={
        "position": "absolute", "top": "4px", "left": "4px", "right": "4px",
        "height": f"{s.duree * 80 - 8}px", "zIndex": "10", "padding": "12px",
        "display": "flex", "flexDirection": "column", "gap": "6px",
    }, children=[
        html.Div([
            html.Span(s.course.code if s.course else "COURS", style={"fontWeight": "800", "fontSize": "0.75rem", "opacity": "0.9"}),
            html.Span(f"{s.start_time}", style={"float": "right", "fontSize": "0.75rem", "fontWeight": "800", "opacity": "0.9"})
        ]),
        html.Div(s.theme, style={"fontWeight": "800", "fontSize": ".9rem", "lineHeight": "1.3", "overflow": "hidden", "flexGrow": "1"}),
        html.Div(style={"marginTop": "auto", "display": "flex", "justifyContent": "space-between", "alignItems": "end"}, children=[
            html.Div([
                html.Span("person", className="material-symbols-outlined", style={"fontSize": "1rem", "verticalAlign": "middle"}),
                html.Span(s.course.enseignant if s.course else "Prof", style={"fontSize": ".8rem", "marginLeft": "4px", "fontWeight": "700"})
            ]),
            html.Span("Salle 101", style={"fontSize": ".8rem", "fontWeight": "800"})
        ]),
        html.Div(className="card-actions", style={"position": "absolute", "top": "10px", "right": "10px", "background": "rgba(255,255,255,0.2)", "borderRadius": "8px", "padding": "4px"}, children=[
            html.Span("edit", className="material-symbols-outlined", style={"fontSize": "1rem", "color": "inherit"})
        ])
    ])

def _session_modal(courses):
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Détails de la Séance", style={"fontWeight": "800", "fontSize": "1.25rem", "color": "var(--text-primary)"}), close_button=True, style={"borderBottom": "none", "padding": "1.5rem 1.5rem 0.5rem"}),
        dbc.ModalBody(style={"padding": "0.5rem 1.5rem 1.5rem"}, children=[
            html.Div([
                html.Label("Cours", className="sga-label"),
                dcc.Dropdown(
                    id="s-course",
                    options=[{"label": c.libelle, "value": c.id} for c in courses],
                    className="sga-select mb-3"
                ),
                
                html.Label("Thème / Chapitre", className="sga-label"),
                dbc.Input(id="s-theme", placeholder="Ex: Introduction aux probabilités...", className="sga-input mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Date & Heure", className="sga-label"),
                        html.Div(style={"display": "flex", "gap": "10px"}, children=[
                            dbc.Input(id="s-date", type="date", className="sga-input"),
                            dbc.Input(id="s-start", placeholder="08:00", className="sga-input"),
                        ]),
                    ], width=8),
                    dbc.Col([
                        html.Label("Durée (h)", className="sga-label"),
                        dbc.Input(id="s-duration", type="number", step=0.5, value=2, className="sga-input"),
                    ], width=4),
                ], className="mb-4"),
                
                html.Div(style={"borderTop": "1px solid var(--border-light)", "paddingTop": "1.5rem", "marginTop": "1rem"}, children=[
                    dbc.Button([
                        html.Span("delete", className="material-symbols-outlined", style={"fontSize": "1.1rem", "marginRight": "8px"}),
                        "Supprimer cette séance"
                    ], id="delete-session-btn", color="danger", outline=True, style={"borderRadius": "10px", "fontSize": "0.85rem", "fontWeight": "700", "width": "100%", "borderColor": "rgba(239, 68, 68, 0.2)"}),
                ]),
                
                dcc.Store(id="editing-s-id", data=None),
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Annuler", id="close-s-modal", className="btn-secondary", style={"background": "transparent", "border": "none", "boxShadow": "none", "color": "#64748b"}),
            dbc.Button("Enregistrer", id="save-s-btn", className="btn-primary", style={"borderRadius": "10px", "padding": "0.6rem 1.5rem", "boxShadow": "0 4px 12px rgba(99, 102, 241, 0.3)"}),
        ], style={"borderTop": "none", "padding": "0.5rem 1.5rem 1.5rem"}),
    ], id="session-modal", is_open=False, centered=True)

# ─── Callbacks ───

@callback(
    Output("session-modal", "is_open"),
    Output("s-course", "value"),
    Output("s-theme", "value"),
    Output("s-date", "value"),
    Output("s-start", "value"),
    Output("s-duration", "value"),
    Output("editing-s-id", "data"),
    Input({"type": "session-block", "index": ALL}, "n_clicks"),
    Input("close-s-modal", "n_clicks"),
    Input("save-s-btn", "n_clicks"),
    Input("delete-session-btn", "n_clicks"),
    State("session-modal", "is_open"),
    State("s-course", "value"),
    State("s-theme", "value"),
    State("s-date", "value"),
    State("s-start", "value"),
    State("s-duration", "value"),
    State("editing-s-id", "data"),
    prevent_initial_call=True
)
def handle_session_modal(block_n, close_n, save_n, del_n, is_open, course, theme, s_date, s_start, dur, e_id):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0].get("value"): return no_update
    
    tid = ctx.triggered[0]["prop_id"]
    
    if "session-block" in tid:
        pid = int(tid.split(",")[0].split(":")[1])
        db = SessionLocal()
        s = db.query(Session).get(pid)
        db.close()
        if s:
            return True, s.course_id, s.theme, s.date.isoformat(), s.start_time, s.duree, s.id
            
    if "close-s-modal" in tid:
        return False, no_update, no_update, no_update, no_update, no_update, no_update
        
    if "save-s-btn" in tid:
        db = SessionLocal()
        if e_id:
            s = db.query(Session).get(e_id)
            if s:
                s.course_id = course
                s.theme = theme
                s.date = datetime.fromisoformat(s_date).date()
                s.start_time = s_start
                s.duree = float(dur)
        db.commit()
        db.close()
        return False, no_update, no_update, no_update, no_update, no_update, no_update

    if "delete-session-btn" in tid:
        if e_id:
            db = SessionLocal()
            s = db.query(Session).get(e_id)
            if s:
                db.delete(s)
                db.commit()
            db.close()
        return False, no_update, no_update, no_update, no_update, no_update, no_update
        
    return no_update

@callback(
    Output("schedule-grid-container", "children"),
    Input("schedule-refresh-interval", "n_intervals"),
    Input("refresh-schedule-btn", "n_clicks"),
    Input("session-modal", "is_open"),
    Input("notification-store", "data"), # Catch random gen
    prevent_initial_call=True
)
def refresh_schedule(n, btn_n, is_open, notif):
    if is_open: return no_update
    
    today = date.today()
    start_week, end_week = get_week_range(today)
    sessions = get_schedule_data(start_week, end_week)
    
    return _render_grid(start_week, sessions)

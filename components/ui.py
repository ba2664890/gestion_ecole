"""
SGA – Composants UI réutilisables
Importable depuis n'importe quelle page
"""

from dash import html, dcc


def page_header(title, subtitle, actions=None):
    """En-tête de page standard avec titre, sous-titre et boutons d'action."""
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "flex-start",
            "marginBottom": "1.5rem",
        },
        className="animate-fade-up",
        children=[
            html.Div([
                html.H2(title, style={"fontWeight": "800", "fontSize": "1.35rem", "margin": 0}),
                html.P(subtitle, style={"color": "#64748b", "fontSize": ".875rem", "margin": 0}),
            ]),
            html.Div(
                style={"display": "flex", "gap": ".75rem"},
                children=actions or [],
            ),
        ],
    )


def kpi_card(icon, value, label, delta=None, direction="up", color="#3b82f6", bg=None):
    """Carte KPI avec icône, valeur, label et delta optionnel."""
    if bg is None:
        bg = f"{color}15"

    return html.Div(className="kpi-card", children=[
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start"},
            children=[
                html.Div(
                    html.Span(icon, className="material-symbols-outlined",
                              style={"fontSize": "1.25rem", "color": color}),
                    className="kpi-icon",
                    style={"background": bg},
                ),
                html.Span(delta, className=f"kpi-delta {direction}", style={
                    "padding": ".2rem .6rem",
                    "borderRadius": "99px",
                    "background": "#d1fae5" if direction == "up" else "#fee2e2",
                }) if delta else None,
            ]
        ),
        html.Div(str(value), className="kpi-value", style={"color": color}),
        html.Div(label, className="kpi-label"),
    ])


def badge(text, variant="blue"):
    """Badge coloré."""
    return html.Span(text, className=f"badge badge-{variant}")


def progress_bar(value, max_value=100, variant=""):
    """Barre de progression avec pourcentage."""
    pct = min(100, (value / max_value * 100)) if max_value > 0 else 0
    if not variant:
        variant = "success" if pct >= 75 else ("warning" if pct >= 40 else "danger")
    return html.Div([
        html.Div(className="progress-wrap", children=[
            html.Div(className=f"progress-fill {variant}", style={"width": f"{pct:.1f}%"}),
        ]),
        html.Div(f"{pct:.0f}%", style={"fontSize": ".75rem", "color": "#94a3b8", "marginTop": ".2rem"}),
    ])


def alert(message, type_="info"):
    """Alerte colorée (success, error, warning, info)."""
    configs = {
        "success": ("check_circle", "#10b981", "#d1fae5", "#065f46"),
        "error":   ("error",        "#ef4444", "#fee2e2", "#991b1b"),
        "warning": ("warning",      "#f59e0b", "#fef3c7", "#92400e"),
        "info":    ("info",         "#13a4ec", "#e0f2fe", "#0369a1"),
    }
    icon, border, bg, text = configs.get(type_, configs["info"])
    return html.Div(style={
        "display": "flex", "alignItems": "center", "gap": ".75rem",
        "padding": ".875rem 1rem",
        "background": bg,
        "borderLeft": f"4px solid {border}",
        "borderRadius": "0 8px 8px 0",
        "fontSize": ".875rem", "color": text,
    }, children=[
        html.Span(icon, className="material-symbols-outlined", style={"fontSize": "1.1rem", "flexShrink": 0}),
        html.Span(message),
    ])


def empty_state(icon, title, subtitle="", action=None):
    """État vide avec icône, message et action optionnelle."""
    return html.Div(style={
        "textAlign": "center", "padding": "3rem 2rem", "color": "#94a3b8",
    }, children=[
        html.Span(icon, className="material-symbols-outlined",
                  style={"fontSize": "3.5rem", "display": "block", "marginBottom": "1rem", "opacity": ".5"}),
        html.P(title, style={"fontWeight": "600", "color": "#64748b", "marginBottom": ".5rem"}),
        html.P(subtitle, style={"fontSize": ".875rem"}) if subtitle else None,
        html.Div(action, style={"marginTop": "1.25rem"}) if action else None,
    ])


def confirm_dialog(title, message, confirm_id, cancel_id):
    """Dialog de confirmation de suppression."""
    return html.Div(style={
        "position": "fixed", "inset": 0,
        "background": "rgba(0,0,0,.45)",
        "zIndex": 1001,
        "display": "flex", "alignItems": "center", "justifyContent": "center",
    }, children=[
        html.Div(className="sga-card animate-scale-in", style={
            "maxWidth": "420px", "width": "100%",
            "textAlign": "center",
            "boxShadow": "0 20px 60px rgba(0,0,0,.18)",
        }, children=[
            html.Div(style={
                "width": "60px", "height": "60px", "borderRadius": "50%",
                "background": "#fee2e2",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "margin": "0 auto 1.25rem",
            }, children=[
                html.Span("delete_forever", className="material-symbols-outlined",
                          style={"color": "#ef4444", "fontSize": "1.75rem"}),
            ]),
            html.H3(title, style={"fontWeight": "700", "marginBottom": ".5rem"}),
            html.P(message, style={"color": "#64748b", "fontSize": ".875rem", "marginBottom": "1.5rem"}),
            html.Div(style={"display": "flex", "gap": ".75rem", "justifyContent": "center"}, children=[
                html.Button("Annuler", id=cancel_id, n_clicks=0, className="btn-secondary"),
                html.Button([
                    html.Span("delete", className="material-symbols-outlined", style={"fontSize": "1rem"}),
                    "Supprimer",
                ], id=confirm_id, n_clicks=0, className="btn-danger"),
            ]),
        ]),
    ])


def section_header(title, subtitle=None, right=None):
    """En-tête de section à l'intérieur d'une card."""
    return html.Div(style={
        "display": "flex", "justifyContent": "space-between",
        "alignItems": "center", "marginBottom": "1.25rem",
    }, children=[
        html.Div([
            html.H3(title, style={"fontWeight": "700", "fontSize": "1rem", "margin": 0}),
            html.P(subtitle, style={"color": "#94a3b8", "fontSize": ".8rem", "margin": 0}) if subtitle else None,
        ]),
        right or html.Span(),
    ])


def stat_row(label, value, color="#64748b"):
    """Ligne de statistique label / valeur."""
    return html.Div(style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": ".45rem .75rem", "borderRadius": "8px", "background": "#f8fafc",
    }, children=[
        html.Span(label, style={"fontSize": ".85rem", "color": "#64748b"}),
        html.Span(value, style={"fontSize": ".85rem", "fontWeight": "700", "color": color}),
    ])

"""
SGA - Login Page
Animated background with GSAP-style CSS animations
"""

from dash import html, dcc, Input, Output, State, callback, no_update
import hashlib
from models import SessionLocal, User


def layout():
    return html.Div(id="login-page", style={"minHeight": "100vh"}, children=[
        # Left decorative panel
        html.Div(className="login-left", children=[
            # Video background (university ambiance)
            html.Div(className="hero-video-wrap", children=[
                html.Video(
                    autoPlay=True, loop=True, muted=True,
                    children=[
                        html.Source(
                            src="https://cdn.pixabay.com/video/2022/06/27/121837-726040052_large.mp4",
                            type="video/mp4"
                        )
                    ],
                    style={"width": "100%", "height": "100%", "objectFit": "cover"}
                ),
            ]),

            # Floating decorative circles
            html.Div(style={
                "position": "absolute", "top": "10%", "right": "8%",
                "width": "120px", "height": "120px",
                "borderRadius": "50%",
                "background": "rgba(255,255,255,.07)",
                "backdropFilter": "blur(8px)",
                "animation": "floatA 6s ease-in-out infinite",
            }),
            html.Div(style={
                "position": "absolute", "bottom": "15%", "left": "5%",
                "width": "80px", "height": "80px",
                "borderRadius": "50%",
                "background": "rgba(255,255,255,.05)",
                "animation": "floatB 8s ease-in-out infinite",
            }),
            html.Div(style={
                "position": "absolute", "top": "55%", "right": "3%",
                "width": "50px", "height": "50px",
                "borderRadius": "50%",
                "background": "rgba(255,255,255,.08)",
                "animation": "floatA 5s 1s ease-in-out infinite",
            }),

            # Content overlay
            html.Div(style={
                "position": "relative", "zIndex": 2,
                "color": "#fff", "maxWidth": "440px",
            }, children=[
                # Icon
                html.Div(style={
                    "width": "72px", "height": "72px",
                    "background": "rgba(255,255,255,.15)",
                    "backdropFilter": "blur(12px)",
                    "borderRadius": "20px",
                    "border": "1px solid rgba(255,255,255,.25)",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "marginBottom": "2rem",
                    "animation": "fadeUp .6s ease both",
                }, children=[
                    html.Span("school", className="material-symbols-outlined",
                              style={"fontSize": "2rem", "color": "#fff"})
                ]),

                html.H1("Système de Gestion Académique", style={
                    "fontSize": "2.5rem", "fontWeight": "900",
                    "lineHeight": 1.15, "letterSpacing": "-.03em",
                    "marginBottom": "1.25rem",
                    "animation": "fadeUp .6s .1s ease both",
                }),
                html.P(
                    "Portail haute performance conçu pour l'excellence académique moderne. "
                    "Sécurisé, rapide et intuitif.",
                    style={
                        "fontSize": "1.05rem", "opacity": ".85",
                        "lineHeight": 1.7, "maxWidth": "380px",
                        "animation": "fadeUp .6s .2s ease both",
                    }
                ),

                # Stats preview
                html.Div(style={
                    "display": "flex", "gap": "1.5rem", "marginTop": "2.5rem",
                    "animation": "fadeUp .6s .35s ease both",
                }, children=[
                    _stat_pill("group", "Étudiants", "1 200+"),
                    _stat_pill("menu_book", "Cours", "48"),
                    _stat_pill("grade", "Moyenne", "8.4/10"),
                ]),
            ]),
        ]),

        # Right auth panel
        html.Div(className="login-right", children=[
            html.Div(style={"width": "100%", "maxWidth": "500px"}, children=[

                # Mobile logo
                html.Div(style={"marginBottom": "2rem"}, children=[
                    html.Div([
                        html.Div(html.Span("school", className="material-symbols-outlined"),
                                 style={
                                     "width": "40px", "height": "40px",
                                     "background": "var(--primary)", "borderRadius": "10px",
                                     "display": "flex", "alignItems": "center", "justifyContent": "center",
                                     "color": "#fff", "fontSize": "1.25rem",
                                 }),
                        html.Span("SGA", style={"fontWeight": "800", "fontSize": "1.25rem"}),
                    ], style={"display": "flex", "alignItems": "center", "gap": ".75rem", "marginBottom": "1rem"}),
                ]),

                # Auth card
                html.Div(className="sga-card animate-fade-up", style={
                    "boxShadow": "0 20px 60px rgba(0,0,0,.08)",
                    "padding": "2.5rem",
                }, children=[
                    html.H2("Connexion", style={
                        "fontSize": "1.75rem", "fontWeight": "800",
                        "letterSpacing": "-.02em", "marginBottom": ".5rem",
                    }),
                    html.P("Accédez à votre portail académique.", style={
                        "color": "#64748b", "fontSize": ".9rem", "marginBottom": "1.75rem",
                    }),

                    # Error message
                    html.Div(id="login-error", style={"display": "none"}, children=[
                        html.Div(style={
                            "background": "#fff1f2", "border": "1px solid #fecdd3",
                            "borderRadius": "10px", "padding": ".75rem 1rem",
                            "color": "#f43f5e", "fontSize": ".875rem",
                            "marginBottom": "1rem", "display": "flex",
                            "alignItems": "center", "gap": ".5rem",
                        }, children=[
                            html.Span("error", className="material-symbols-outlined", style={"fontSize": "1.1rem"}),
                            html.Span(id="login-error-msg", children="Identifiants incorrects."),
                        ])
                    ]),

                    # Username
                    html.Div(style={"marginBottom": "1.25rem"}, children=[
                        html.Label("Identifiant", className="sga-label"),
                        html.Div(style={"position": "relative"}, children=[
                            html.Span("person", className="material-symbols-outlined", style={
                                "position": "absolute", "left": "12px", "top": "50%",
                                "transform": "translateY(-50%)", "color": "#94a3b8", "fontSize": "1.1rem",
                            }),
                            dcc.Input(
                                id="login-username",
                                placeholder="Votre identifiant",
                                debounce=False,
                                n_submit=0,
                                className="sga-input",
                                style={"paddingLeft": "2.5rem"},
                            ),
                        ]),
                    ]),

                    # Password
                    html.Div(style={"marginBottom": "1.5rem"}, children=[
                        html.Label("Mot de passe", className="sga-label"),
                        html.Div(style={"position": "relative"}, children=[
                            html.Span("lock", className="material-symbols-outlined", style={
                                "position": "absolute", "left": "12px", "top": "50%",
                                "transform": "translateY(-50%)", "color": "#94a3b8", "fontSize": "1.1rem",
                            }),
                            dcc.Input(
                                id="login-password",
                                placeholder="••••••••",
                                type="password",
                                debounce=False,
                                n_submit=0,
                                className="sga-input",
                                style={"paddingLeft": "2.5rem"},
                            ),
                        ]),
                        html.Div(style={"textAlign": "right", "marginTop": ".5rem"}, children=[
                            html.A("Mot de passe oublié ?", href="#", style={"color": "var(--primary)", "fontSize": ".8rem", "textDecoration": "none"}),
                        ]),
                    ]),

                    # Submit
                    html.Button(
                        [
                            html.Span("Connexion", style={"flex": 1}),
                            html.Span("arrow_forward", className="material-symbols-outlined", style={"fontSize": "1.1rem"}),
                        ],
                        id="login-btn",
                        n_clicks=0,
                        className="btn-primary",
                        style={"width": "100%", "justifyContent": "center", "padding": ".85rem 1.5rem", "fontSize": "1rem"},
                    ),

                    # Demo hint
                    html.Div(style={
                        "marginTop": "1.5rem", "padding": ".75rem 1rem",
                        "background": "rgba(99, 102, 241, 0.08)", "borderRadius": "10px",
                        "border": "1px solid rgba(99, 102, 241, 0.15)",
                    }, children=[
                        html.P("💡 Démo : admin / admin123", style={
                            "fontSize": ".8rem", "color": "var(--primary)", "margin": 0, "fontWeight": "600",
                        })
                    ]),
                ]),

                # Footer
                html.Div(style={
                    "textAlign": "center", "marginTop": "1.5rem",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "gap": ".5rem", "color": "#94a3b8", "fontSize": ".75rem",
                }, children=[
                    html.Span("verified_user", className="material-symbols-outlined", style={"fontSize": ".9rem"}),
                    html.Span("Session chiffrée de bout en bout"),
                ]),
            ])
        ]),
    ])


def _stat_pill(icon, label, value):
    return html.Div(style={
        "display": "flex", "flexDirection": "column", "gap": ".25rem",
        "padding": ".75rem 1.25rem",
        "background": "rgba(255,255,255,.1)",
        "backdropFilter": "blur(8px)",
        "borderRadius": "12px",
        "border": "1px solid rgba(255,255,255,.15)",
    }, children=[
        html.Div(style={"display": "flex", "alignItems": "center", "gap": ".35rem"}, children=[
            html.Span(icon, className="material-symbols-outlined", style={"fontSize": ".9rem", "opacity": ".8"}),
            html.Span(label, style={"fontSize": ".7rem", "opacity": ".8"}),
        ]),
        html.Span(value, style={"fontSize": "1.1rem", "fontWeight": "800"}),
    ])


# ─── Callback ───────────────────────────────────────────────────────────────────
@callback(
    Output("auth-store", "data"),
    Output("login-error", "style"),
    Output("login-error-msg", "children"),
    Input("login-btn", "n_clicks"),
    Input("login-password", "n_submit"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def do_login(n_clicks, n_submit, username, password):
    print(f"DEBUG: do_login called with n_clicks={n_clicks}, n_submit={n_submit}, user={username}")
    if not username or not password:
        return no_update, {"display": "block"}, "Veuillez remplir tous les champs."

    db = SessionLocal()
    try:
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        user = db.query(User).filter_by(username=username).first()
        
        if user and user.password_hash == pw_hash:
            return (
                {"authenticated": True, "username": user.username, "role": user.role, "nom": user.nom_complet},
                {"display": "none"},
                ""
            )
        return no_update, {"display": "block"}, "Identifiant ou mot de passe incorrect."
    finally:
        db.close()

from dash import html, dcc
import os

def layout():
    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        content = f"# Erreur\n\nImpossible de charger le fichier README.md.\n\n`{str(e)}`"

    return html.Div([
        html.Div(className="card", children=[
            html.Div(className="card-body", children=[
                dcc.Markdown(
                    content,
                    className="markdown-body",
                    dangerously_allow_html=True,
                    style={"lineHeight": "1.8", "fontSize": "0.95rem"}
                )
            ])
        ])
    ], className="page-container style-docs")
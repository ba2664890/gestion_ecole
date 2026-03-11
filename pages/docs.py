from dash import html, dcc

def doc_card(icon, title, description, features):
    return html.Div(className="doc-card animate-fade-in", children=[
        html.Div(className="doc-card-header", children=[
            html.Div(className="doc-icon-wrapper", children=[
                html.Span(icon, className="material-symbols-outlined")
            ]),
            html.H3(title, className="doc-card-title")
        ]),
        html.P(description, className="doc-card-desc"),
        html.Ul(className="doc-feature-list", children=[
            html.Li([
                html.Span("check_circle", className="material-symbols-outlined", style={"fontSize": "1rem", "color": "var(--primary)", "marginRight": ".5rem", "verticalAlign": "middle"}),
                html.Span(f)
            ]) for f in features
        ])
    ])

def layout():
    return html.Div(className="page-container style-docs", children=[
        
        # Hero Section
        html.Div(className="docs-hero animate-fade-in", children=[
            html.H1("Centre de Documentation & Aide", className="docs-hero-title"),
            html.P("Découvrez comment utiliser toutes les fonctionnalités du Système de Gestion Académique (SGA) avec notre guide interactif exclusif.", className="docs-hero-subtitle"),
            html.Div(className="docs-search-bar", children=[
                html.Span("search", className="material-symbols-outlined search-icon"),
                dcc.Input(type="text", placeholder="Rechercher un module, une action...", className="docs-search-input")
            ])
        ]),

        # Cards Grid Section
        html.Div(className="docs-section", children=[
            html.H2("Exploration des Modules", className="docs-section-title animate-slide-up"),
            html.Div(className="docs-grid", children=[
                doc_card(
                    "dashboard", 
                    "Tableau de Bord", 
                    "Comprenez les indicateurs clés et naviguez facilement.",
                    ["KPIs en temps réel (effectifs, absences)", "Graphiques interactifs d'évolution", "Notification et Widgets (Pomodoro)"]
                ),
                doc_card(
                    "group", 
                    "Gestion des Étudiants", 
                    "Administrez la base de données des apprenants.",
                    ["Ajout/Modification des fiches", "Suivi individuel (moyennes, absences)", "Recherche et filtrage rapide"]
                ),
                doc_card(
                    "menu_book", 
                    "Curriculum & Cours", 
                    "Gérez l'ensemble des enseignements proposés.",
                    ["Création de nouveaux cours", "Suivi des heures de cours effectuées", "Jauges de progression visuelles"]
                ),
                doc_card(
                    "edit_calendar", 
                    "Séances & Présences", 
                    "Menez vos cours à bien et suivez l'assiduité.",
                    ["Appel numérique instantané", "Cahier de texte par séance", "Historique détaillé des cours réalisés"]
                ),
                doc_card(
                    "grade", 
                    "Notes & Évaluations", 
                    "Centralisez les résultats académiques.",
                    ["Saisie manuelle des bulletins", "Export d'un modèle (Template) Excel", "Import massif pour la correction automatisée"]
                ),
                doc_card(
                    "assignment", 
                    "Projets & Groupes", 
                    "Suivez les travaux pratiques et exposés des étudiants.",
                    ["Tableau Kanban (À faire, En cours, Terminé)", "Barre de progression des rendus", "Statuts et priorités des équipes"]
                ),
                doc_card(
                    "calendar_month", 
                    "Emploi du Temps", 
                    "Organisez la semaine pédagogique.",
                    ["Calendrier dynamique des séances", "Détail par cours (thème, heure)", "Visualisation rapide de la semaine"]
                ),
                doc_card(
                    "analytics", 
                    "Analytique", 
                    "Plongez dans la puissance des statistiques.",
                    ["Répartition des moyennes par cours", "Comparaisons et tendances macroscopiques", "Simulateur de moyenne interactive"]
                ),
                doc_card(
                    "summarize", 
                    "Rapports & Exports", 
                    "Générez systématiquement les relevés officiels.",
                    ["Création des bulletins en PDF", "Export Excel du registre des présences", "Extraction globale au format standard"]
                ),
            ])
        ]),
        
        # FAQ Section
        html.Div(className="docs-section animate-slide-up", style={"animationDelay": "0.3s"}, children=[
            html.H2("Questions Fréquentes (FAQ)", className="docs-section-title"),
            html.Div(className="docs-faq-container", children=[
                html.Details(className="docs-faq-item", children=[
                    html.Summary("Comment importer et mettre à jour les notes par lot ?"),
                    html.Div(className="docs-faq-content", children=[
                        html.P("1. Cliquez sur le module 'Notes & Évaluations' depuis le menu latéral."),
                        html.P("2. Utilisez l'option pour télécharger le modèle de notation officiel Excel."),
                        html.P("3. Saisissez rigoureusement les notes dans la colonne dédiée ('Note')."),
                        html.P("4. Cliquez sur le bouton d'importation via Excel afin d'intégrer le fichier complété au système.")
                    ])
                ]),
                html.Details(className="docs-faq-item", children=[
                    html.Summary("Le mot de passe de l'administrateur peut-il être modifié ?"),
                    html.Div(className="docs-faq-content", children=[
                        "Oui. L'administrateur du portail (profil sécurisé) peut modifier les accès ou rajouter de nouveaux collaborateurs via le panneau 'Paramètres > Portail Administrateur'."
                    ])
                ]),
                html.Details(className="docs-faq-item", children=[
                    html.Summary("Comment les calculs de présence et note moyenne s'actualisent-ils ?"),
                    html.Div(className="docs-faq-content", children=[
                        "Dès qu'un enseignant valide l'appel sur l'outil 'Séances' ou remplit une note sur 'Notes & Évaluations', le total général s'incrémente ou s'ajuste instantanément. C'est l'atout du Dashboard SGA propulsé par SQL et des composants asynchrones Dash."
                    ])
                ]),
            ])
        ])

    ])
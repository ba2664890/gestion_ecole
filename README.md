# SGA - Système de Gestion Académique

Le Système de Gestion Académique (SGA) est une application web complète développée avec le framework Dash (Python). Elle offre une interface moderne et réactive pour faciliter l'administration d'un établissement d'enseignement. Cette plateforme centralise la gestion des étudiants, des cours, des présences, des notes, de l'emploi du temps, et des travaux de groupe.

L'application est connectée à une base de données PostgreSQL hébergée sur Neon, assurant une gestion fiable et persistante des données. L'interface utilisateur bénéficie d'une ergonomie soignée, reposant sur la typographie Lexend et des animations fluides réalisées en CSS et GSAP.

---

## Fonctionnalités Principales

Le système est découpé en plusieurs modules pour couvrir l'ensemble des besoins administratifs et pédagogiques :

- Authentification : Un système de connexion sécurisé avec gestion des sessions via Dash Store.
- Tableau de Bord : Une vue d'ensemble avec des indicateurs clés de performance (KPIs) en temps réel, incluant la distribution des notes, la tendance des présences, et la progression de chaque cours.
- Étudiants : Un espace dédié pour l'ajout, la modification et la consultation des informations des étudiants (CRUD), incluant le calcul automatique de la moyenne et du taux d'absence.
- Cours et Curriculum : Interface pour administrer le catalogue des cours, suivre les heures prévues par rapport aux heures effectuées, et visualiser l'avancement via des barres de progression.
- Séances et Présences : Outil de saisie numérique interactif pour faire l'appel. Ce module sert également de cahier de texte numérique avec un historique complet et filtrable des séances.
- Notes et Évaluations : Saisie sécurisée des notes par matière, avec la possibilité de télécharger des modèles Excel pour la saisie hors ligne, puis de les importer massivement dans l'application.
- Emploi du Temps : Vue hebdomadaire claire et organisée des séances de cours programmées pour l'établissement.
- Projets et Travaux de Groupe : Module de suivi des projets étudiants (type ENSAE) avec un tableau Kanban simplifié, permettant de suivre le statut, la progression, et les dates limites de chaque projet associé à un cours.
- Analytique : Une section dédiée à l'analyse approfondie des données académiques. Elle comporte des distributions statistiques, des comparaisons de cours, des suivis d'évolution, ainsi qu'un simulateur de moyenne interactive.
- Rapports et Exports : Génération automatique de bulletins au format PDF via ReportLab, et exportation de différentes données (présences, notes globales) au format Excel pour une exploitation externe.
- Paramètres : Console d'administration pour la gestion des comptes utilisateurs, la consultation des informations du système et de la base de données.

---

## Déploiement

L'application est conteneurisée à l'aide de Docker, ce qui simplifie grandement son déploiement sur les plateformes Cloud.

### Déploiement automatisé sur Render (Recommandé)

L'utilisation du fichier de configuration fourni permet un déploiement "en un clic".

1. Transférez le code source vers un dépôt GitHub.
   ```bash
   git init
   git add .
   git commit -m "SGA app initiale"
   git remote add origin https://github.com/votre-user/sga-app.git
   git push -u origin main
   ```

2. Rendez-vous sur Render.com.
3. Sélectionnez "New" puis "Blueprint".
4. Liez votre dépôt GitHub et validez. Render utilisera le fichier render.yaml pour configurer automatiquement l'environnement et lancer le déploiement. L'application sera disponible en quelques minutes.

### Déploiement manuel sur Render

Si vous préférez configurer le service web manuellement :

1. Sur Render.com, choisissez "New" puis "Web Service".
2. Connectez votre dépôt GitHub.
3. Définissez le Runtime sur "Docker".
4. Configurez les variables d'environnement indispensables :
   - DATABASE_URL : L'URL de connexion à votre base de données PostgreSQL (ex: postgresql://neondb_owner:...).
   - SECRET_KEY : Une clé secrète robuste pour sécuriser les sessions Flask.
   - PORT : Définissez-le sur 8050.
5. Lancez le déploiement.

---

## Exécution en Local

Pour les tests ou le développement, vous pouvez exécuter le projet localement.

### Utilisation de Docker

La solution la plus fiable pour reproduire l'environnement de production.

```bash
# Construction de l'image Docker locale
docker build -t sga-app .

# Exécution du conteneur en transmettant les variables d'environnement
docker run -p 8050:8050 \
  -e DATABASE_URL="postgresql://neondb_owner:npg_IOEvtGp5oF2B@ep-orange-king-aiiqaabt-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require" \
  -e SECRET_KEY="dev-secret-local" \
  sga-app
```

Accédez à l'application via http://localhost:8050.

### Installation classique (Python VENV)

Si vous ne souhaitez pas utiliser Docker, vous pouvez faire tourner l'application directement avec Python.

```bash
# Installation des dépendances requises
pip install -r requirements.txt

# Lancement du serveur Dash
python app.py
```

Rendez-vous sur http://localhost:8050.

Pour tester l'application directement, vous pouvez utiliser ces accès de démonstration créés par défaut :
Identifiant : admin
Mot de passe : admin123

---

## Architecture et Structure du Projet

Le code est organisé de manière modulaire, chaque fonctionnalité importante possédant sa propre page.

- app.py : Constitue le point d'entrée principal de l'application. Il contient la structure globale (Layout), le système de routage sécurisé, ainsi que la gestion de l'état global et du menu de navigation.
- models.py : Fichier définissant le schéma de base de données à travers l'ORM SQLAlchemy. Il inclut également des fonctions pour initialiser les tables et injecter des données factices (seeding) lors du premier lancement.
- requirements.txt : Liste des bibliothèques Python nécessaires au fonctionnement de l'application.
- Dossier pages/ : Contient un fichier Python pour chaque écran majeur de l'application.
  - login.py : Écran d'authentification avec un design immersif.
  - dashboard.py : Vue de synthèse (KPIs et graphiques).
  - students.py : Gestion des données des étudiants.
  - courses.py : Administration des matières enseignées.
  - sessions.py : Système d'appel et cahier de texte.
  - grades.py : Registre des notes et fonctions d'import.
  - schedule.py : Affichage des séances sous forme de calendrier hebdomadaire.
  - projects.py : Gestion des travaux de groupe et projets.
  - analytics.py : Tableaux de bord avancés et simulateur de notes.
  - reports.py : Générateur de documents (PDF/Excel).
  - settings_page.py : Administration des utilisateurs système.

---

## Choix Techniques et Design

- Interface et Ergonomie : L'application utilise la typographie "Lexend" disponible via Google Fonts, associée aux icônes vectorielles "Material Symbols Outlined". Le code couleur principal s'articule autour d'un bleu distinctif (#13a4ec).
- Animations : Pour dynamiser l'expérience utilisateur, l'interface intègre plusieurs animations CSS spécifiques (apparitions fondues, boutons flottants, transitions de dégradés et effets de pulsation). La page de connexion dispose également d'une vidéo en arrière-plan.
- Base de données : L'architecture des données repose sur PostgreSQL via le service Neon. Les tables principales sont :
  - students : Informations personnelles des étudiants.
  - courses : Catalogue des matières.
  - sessions : Historique des cours dispensés.
  - attendance : Enregistrements détaillés des présences.
  - grades : Archive des résultats d'évaluations.
  - projects : Liste et état d'avancement des projets de groupe.
  - users : Comptes autorisés à se connecter au système.

---

## Configuration Complémentaire

Pour le bon fonctionnement en production, assurez-vous de configurer correctement les variables d'environnement dans votre système d'hébergement :

- DATABASE_URL : Chaîne de connexion complète vers la base PostgreSQL relative à votre compte Neon.
- SECRET_KEY : Chaîne de caractères aléatoire essentielle pour chiffrer les cookies de session des utilisateurs.

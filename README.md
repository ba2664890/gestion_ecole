# SGA – Système de Gestion Académique

Application Dash complète connectée à PostgreSQL (Neon), avec design Lexend + animations CSS/GSAP.

---

## 🚢 Déploiement sur Render (Docker)

### Option A — Via `render.yaml` (recommandé, 1 clic)

```bash
# 1. Initialisez un dépôt Git et poussez sur GitHub
git init
git add .
git commit -m "SGA app initiale"
git remote add origin https://github.com/votre-user/sga-app.git
git push -u origin main
```

Ensuite sur [render.com](https://render.com) :
- **New** → **Blueprint** → connectez votre repo → **Apply**
- Render détecte `render.yaml` et déploie automatiquement ✅
- L'app est live en ~3 minutes sur `https://sga-academique.onrender.com`

### Option B — Déploiement manuel

1. Render → **New** → **Web Service** → connectez votre repo
2. **Runtime** : Docker
3. Variables d'environnement à ajouter :
   | Clé | Valeur |
   |-----|--------|
   | `DATABASE_URL` | `postgresql://neondb_owner:...` (votre URL Neon) |
   | `SECRET_KEY` | Générer (bouton "Generate") |
   | `PORT` | `8050` |
4. **Deploy** ✅

### 🐳 Tester Docker en local

```bash
# Build
docker build -t sga-app .

# Run
docker run -p 8050:8050 \
  -e DATABASE_URL="postgresql://neondb_owner:npg_IOEvtGp5oF2B@ep-orange-king-aiiqaabt-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require" \
  -e SECRET_KEY="dev-secret-local" \
  sga-app

# Ouvrez http://localhost:8050
```

---

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## ▶️ Lancement

```bash
python app.py
```

Ouvrez http://localhost:8050

**Identifiants démo** : `admin` / `admin123`

## 📁 Structure

```
sga_app/
├── app.py              # Point d'entrée, layout global, auth routing
├── models.py           # ORM SQLAlchemy + init DB + seed data
├── requirements.txt
└── pages/
    ├── login.py        # Connexion avec vidéo background animée
    ├── dashboard.py    # KPIs + graphiques exécutifs
    ├── students.py     # CRUD étudiants + taux absence/moyenne
    ├── courses.py      # CRUD cours + barres de progression
    ├── sessions.py     # Appel numérique + cahier de texte
    ├── grades.py       # Notes + import/export Excel
    ├── analytics.py    # Histogrammes, courbes, camemberts
    ├── reports.py      # PDF bulletin, export Excel présences
    └── settings_page.py # Gestion utilisateurs + infos système
```

## 🎨 Design System

- **Police** : Lexend (Google Fonts)
- **Icônes** : Material Symbols Outlined
- **Couleur principale** : `#13a4ec`
- **Animations** : CSS keyframes (fadeUp, floatA/B, gradient-shift, pulse-ring)
- **Fond login** : Vidéo Pixabay (académique) + overlay gradient

## 🗄️ Base de Données (PostgreSQL Neon)

Tables :
- `students` — Étudiants
- `courses` — Cours
- `sessions` — Séances de cours
- `attendance` — Présences/absences
- `grades` — Notes
- `users` — Utilisateurs de l'application

## ✨ Fonctionnalités

| Module | Fonctionnalités |
|--------|----------------|
| Auth | Login sécurisé, session Dash Store, logout |
| Dashboard | KPIs temps réel, histogramme notes, tendance présences, progression cours |
| Étudiants | CRUD complet, avatar, taux absence, moyenne, recherche |
| Cours | CRUD, barre progression, heures effectuées/planifiées |
| Séances | Appel numérique interactif, cahier de texte, historique filtrable |
| Notes | Saisie manuelle, template Excel téléchargeable, import Excel |
| Analytique | Distribution, comparaison cours, évolution présences, camembert |
| Rapports | Bulletin PDF (ReportLab), export Excel présences, export global notes |
| Paramètres | Gestion utilisateurs, infos DB, à propos |

## 🔧 Variables d'environnement

```bash
DATABASE_URL=postgresql://...    # URL Neon (déjà configuré dans models.py)
SECRET_KEY=votre-secret          # Clé Flask session
```
# gestion_ecole

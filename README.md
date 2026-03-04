# ⚡ WattForecast - Smart Energy Advisor

An energy analysis application that provides climate-based insights and visualizations for smart energy planning.

![Astro](https://img.shields.io/badge/Astro-FF5D01?style=for-the-badge&logo=astro&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)

## ✨ Features

- 🌍 **Global Location Search** - Search any city worldwide using Open-Meteo geocoding
- 📊 **Climate Analysis** - Get detailed climate projections for 7-365 days
- 📈 **Visual Charts** - Temperature profile and solar potential visualizations
- 📥 **CSV Export** - Download climate data for further analysis
- 🏠 **User Types** - Tailored advice for homes and industries

---

## 🏗️ Architecture

WattForecast has two operating modes:

### Mode 1 — Frontend-Only (default, no backend required)

```
Browser
  └── Astro Frontend (localhost:4321)
        └── src/lib/climate-service.ts   ← TypeScript service
              ├── Open-Meteo Climate API  (climate-api.open-meteo.com)
              └── Open-Meteo Geocoding API (geocoding-api.open-meteo.com)
```

The `climate-service.ts` library is a full TypeScript port of the Python backend logic. It calls the [Open-Meteo](https://open-meteo.com/) APIs **directly from the browser**, so the application works out of the box without running any backend.

### Mode 2 — Full-Stack (frontend + Python/Flask backend)

```
Browser
  └── Astro Frontend (localhost:4321)
        └── HTTP requests
              └── Flask Backend (localhost:5000)
                    ├── api.py              ← Route definitions (Blueprint)
                    ├── energy_advisor_backend.py  ← Business logic + chart generation
                    └── Open-Meteo Climate & Geocoding APIs
```

The optional Flask backend adds **server-side chart generation** (Matplotlib PNG images returned as base64) and **CSV export** via dedicated REST endpoints.

### Component Interaction

```
index.astro (single page)
  ├── Header.astro          — App title and description
  ├── EnergyForm.astro      — User inputs: location, days, user type
  │     └── LocationSearch.astro  — Live city search (calls geocoding API)
  ├── ResultsSection.astro  — Renders analysis results
  │     ├── MetricsGrid.astro     — Key energy metrics cards
  │     └── ChartsGrid.astro      — Temperature & solar charts (Chart.js)
  ├── Alert.astro           — Error / warning messages
  └── Loading.astro         — Loading spinner overlay
```

---

## 🚀 Local Deployment

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Node.js](https://nodejs.org/) | ≥ 18 | Run Astro frontend |
| [pnpm](https://pnpm.io/) | ≥ 8 | Package manager |
| [Python](https://python.org/) | ≥ 3.10 | Run optional Flask backend |

---

### Option A — Frontend only (recommended for quick start)

This is the fastest way to get the app running at `http://localhost:4321`. No Python or backend needed.

```bash
# 1. Install Node dependencies
pnpm install

# 2. Start the development server
pnpm dev
```

Open **http://localhost:4321** in your browser. The app will call Open-Meteo APIs directly from the browser.

---

### Option B — Full-Stack (frontend + backend)

Run both servers when you need server-side chart generation via the Flask API.

**Step 1 — Start the backend**

```bash
# Navigate to the backend folder
cd backend

# Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install Python dependencies
pip install -r requirements.txt

# Start the Flask server
python energy_advisor_backend.py
```

Backend available at: `http://localhost:5000`

**Step 2 — Start the frontend** (in a separate terminal)

```bash
# From the project root
pnpm install
pnpm dev
```

Frontend available at: `http://localhost:4321`

---

## 📁 Project Structure

```
/
├── public/                   # Static assets served as-is
├── src/
│   ├── assets/               # SVG / image assets used in components
│   │   ├── astro.svg
│   │   └── background.svg
│   ├── components/           # Astro UI components
│   │   ├── Alert.astro       # Error/warning banners
│   │   ├── ChartsGrid.astro  # Chart.js temperature & solar charts
│   │   ├── EnergyForm.astro  # Main analysis form
│   │   ├── Header.astro      # App header / hero
│   │   ├── Loading.astro     # Loading spinner
│   │   ├── LocationSearch.astro  # Autocomplete city search
│   │   ├── MetricsGrid.astro # Energy metrics cards
│   │   ├── ResultsSection.astro  # Results container
│   │   └── Welcome.astro     # Welcome / landing state
│   ├── layouts/
│   │   └── Layout.astro      # Base HTML layout with global styles
│   ├── lib/
│   │   └── climate-service.ts  # TypeScript: Open-Meteo API calls + calculations
│   ├── pages/
│   │   └── index.astro       # Single entry-point page
│   └── styles/
│       └── global.css        # Global Tailwind CSS styles
├── backend/
│   ├── energy_advisor_backend.py  # Flask app + business logic + chart generation
│   ├── api.py                     # REST API routes (Flask Blueprint)
│   └── requirements.txt           # Python dependencies
├── docs/
│   └── API_DOCS.md           # Full backend API reference
├── astro.config.mjs          # Astro + Vite configuration
├── package.json
└── tsconfig.json
```

---

## 📖 API Documentation

See [docs/API_DOCS.md](docs/API_DOCS.md) for the complete backend API reference.

### Quick API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/zones` | GET | List predefined zones |
| `/api/geocode?q=` | GET | Search locations by name |
| `/api/analyze` | POST | Climate analysis + chart generation |
| `/api/export-csv` | POST | Download climate data as CSV |

---

## 🧞 Commands

All commands are run from the **project root**.

| Command | Action |
|---------|--------|
| `pnpm install` | Install frontend dependencies |
| `pnpm dev` | Start frontend dev server at `localhost:4321` |
| `pnpm build` | Build production site to `./dist/` |
| `pnpm preview` | Preview the production build locally |

---

## 🛠️ Tech Stack

**Frontend:**
- [Astro](https://astro.build) v5 — Component-based static site generator
- [Tailwind CSS](https://tailwindcss.com) v4 — Utility-first CSS framework
- [Chart.js](https://www.chartjs.org/) v4 — Interactive data visualization
- TypeScript — Type-safe climate service & utilities

**Backend (optional):**
- [Flask](https://flask.palletsprojects.com/) — Lightweight Python web framework
- [Pandas](https://pandas.pydata.org/) — Tabular data processing
- [Matplotlib](https://matplotlib.org/) — Server-side chart image generation
- [Open-Meteo](https://open-meteo.com/) — Free climate & geocoding APIs (no API key required)

---

## 📄 License

MIT License © 2026 - feel free to use for personal or commercial projects.

## 🙏 Credits

- Climate data provided by [Open-Meteo](https://open-meteo.com/)

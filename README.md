# ⚡ WattForecast - Smart Energy Advisor

An energy analysis application that provides climate-based insights and visualizations for smart energy planning.

![Astro](https://img.shields.io/badge/Astro-FF5D01?style=for-the-badge&logo=astro&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)

## ✨ Features

- 🌍 **Global Location Search** - Search any city worldwide using Open-Meteo geocoding
- 📊 **Climate Analysis** - Get detailed climate projections for 7-365 days
- 📈 **Visual Charts** - Temperature profile and solar potential visualizations
- 📥 **CSV Export** - Download climate data for further analysis
- 🏠 **User Types** - Tailored advice for homes and industries

## 🚀 Quick Start

### Frontend (Astro + Tailwind)

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

Frontend available at: `http://localhost:4321`

### Backend (Python + Flask)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Start server
python energy_advisor_backend.py
```

Backend available at: `http://localhost:5000`

## 📁 Project Structure

```
/
├── public/              # Static assets
├── src/
│   ├── components/      # Astro components
│   │   ├── Alert.astro
│   │   ├── ChartsGrid.astro
│   │   ├── EnergyForm.astro
│   │   ├── Header.astro
│   │   ├── Loading.astro
│   │   ├── LocationSearch.astro
│   │   ├── MetricsGrid.astro
│   │   ├── ResultsSection.astro
│   ├── layouts/
│   │   └── Layout.astro
│   ├── pages/
│   │   └── index.astro
│   └── styles/
│       └── global.css
├── backend/
│   ├── energy_advisor_backend.py
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   └── API_DOCS.md
└── package.json
```

##  API Documentation

See [docs/API_DOCS.md](docs/API_DOCS.md) for complete API reference.

### Quick API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/zones` | GET | List predefined zones |
| `/api/geocode?q=` | GET | Search locations |
| `/api/analyze` | POST | Main analysis endpoint |
| `/api/export-csv` | POST | Download climate CSV |

## 🧞 Commands

| Command | Action |
|---------|--------|
| `pnpm install` | Install frontend dependencies |
| `pnpm dev` | Start frontend dev server at `localhost:4321` |
| `pnpm build` | Build production site to `./dist/` |
| `pnpm preview` | Preview production build |

## 🛠️ Tech Stack

**Frontend:**
- [Astro](https://astro.build) - Static site generator
- [Tailwind CSS](https://tailwindcss.com) - Utility-first CSS
- TypeScript

**Backend:**
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Pandas](https://pandas.pydata.org/) - Data analysis
- [Matplotlib](https://matplotlib.org/) - Chart generation
- [Open-Meteo](https://open-meteo.com/) - Climate data API

## 📄 License

MIT License © 2026 - feel free to use for personal or commercial projects.

## 🙏 Credits

- Climate data provided by [Open-Meteo](https://open-meteo.com/)

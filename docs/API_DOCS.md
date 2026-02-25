# 📘 API Documentation - Energy Advisor

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to backend folder
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy configuration file
cp .env.example .env
```

### 3. Run Server

```bash
python energy_advisor_backend.py
```

Server available at: `http://localhost:5000`

---

## 📋 Available Endpoints

### 1. Health Check

Verify the server is running.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "message": "Energy Advisor Backend active",
  "timestamp": "2025-02-08T10:30:00"
}
```

**cURL Example:**
```bash
curl http://localhost:5000/api/health
```

---

### 2. Get Available Zones

List all available zones for analysis.

**Endpoint:** `GET /api/zones`

**Response:**
```json
{
  "zones": [
    {"id": "new-york", "name": "New York"},
    {"id": "los-angeles", "name": "Los Angeles"},
    {"id": "chicago", "name": "Chicago"},
    {"id": "miami", "name": "Miami"},
    {"id": "seattle", "name": "Seattle"}
  ]
}
```

---

### 3. Geocode Search

Search for any location worldwide.

**Endpoint:** `GET /api/geocode?q={query}`

**Parameters:**
- `q` (string, required): Search term (min 2 characters)

**Response:**
```json
{
  "results": [
    {
      "name": "New York",
      "country": "United States",
      "admin1": "New York",
      "lat": 40.7128,
      "lon": -74.006,
      "tz": "America/New_York",
      "display": "New York, New York - United States"
    }
  ]
}
```

---

### 4. Full Analysis (Main Endpoint)

Generate climate analysis, energy metrics, and charts.

**Endpoint:** `POST /api/analyze`

**Body (JSON):**
```json
{
  "user_type": "home",
  "zona": "new-york",
  "days": 30,
  "lat": 40.7128,
  "lon": -74.006,
  "tz": "America/New_York"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_type` | string | Yes | `"home"` or `"industry"` |
| `zona` | string | Yes | Zone name or custom location name |
| `days` | integer | Yes | Between 7 and 365 |
| `lat` | float | No* | Latitude for custom zones |
| `lon` | float | No* | Longitude for custom zones |
| `tz` | string | No | Timezone (default: auto) |

*Required if zone is not predefined

**Success Response (200):**
```json
{
  "success": true,
  "timestamp": "2025-02-08T10:30:00",
  "parameters": {
    "user_type": "home",
    "zone": "new-york",
    "days": 30
  },
  "metrics": {
    "avg_temp": 22.5,
    "max_temp": 35.2,
    "min_temp": 10.3,
    "cdd_total": 180.5,
    "extreme_heat_days": 8,
    "comfortable_days": 5,
    "avg_radiation": 20.3,
    "avg_solar_potential": 15.8,
    "optimal_solar_days": 22,
    "avg_humidity": 55.2,
    "high_demand_days": 12
  },
  "charts": {
    "temperature": "base64_encoded_image...",
    "solar": "base64_encoded_image..."
  }
}
```

**JavaScript Example:**
```javascript
fetch('http://localhost:5000/api/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_type: 'home',
    zona: 'new-york',
    days: 30
  })
})
.then(response => response.json())
.then(data => {
  console.log('Metrics:', data.metrics);
  
  // Display charts
  document.getElementById('chart-temp').src = 
    `data:image/png;base64,${data.charts.temperature}`;
  document.getElementById('chart-solar').src = 
    `data:image/png;base64,${data.charts.solar}`;
});
```

---

### 5. Export CSV

Download climate data in CSV format.

**Endpoint:** `POST /api/export-csv`

**Body (JSON):**
```json
{
  "zona": "new-york",
  "days": 30
}
```

**Response:** Downloadable CSV file

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/export-csv \
  -H "Content-Type: application/json" \
  -d '{"zona": "new-york", "days": 30}' \
  -o climate_data.csv
```

---

## 📊 Metrics Structure

| Metric | Description |
|--------|-------------|
| `avg_temp` | Average temperature for the period (°C) |
| `max_temp` | Maximum expected temperature (°C) |
| `min_temp` | Minimum expected temperature (°C) |
| `cdd_total` | Cooling Degree Days (AC usage predictor) |
| `extreme_heat_days` | Days with temperature > 35°C |
| `comfortable_days` | Days with temperature < 24°C |
| `avg_radiation` | Average solar radiation (MJ/m²) |
| `avg_solar_potential` | Effective solar energy considering cloud cover |
| `optimal_solar_days` | Days with cloud cover < 40% |
| `avg_humidity` | Average relative humidity (%) |
| `high_demand_days` | Days with high heat + humidity |

---

## 🔧 Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid parameters |
| 500 | Internal server error |

---

## 🚀 Production Deployment

### Option 1: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "energy_advisor_backend.py"]
```

### Option 2: Railway/Render

1. Connect your GitHub repository
2. Deploy automatically

---

## 📝 Important Notes

1. **Cache**: System caches 100 recent queries for optimization
2. **CORS**: Enabled for all origins (adjust in production)
3. **Rate Limiting**: Consider adding Flask-Limiter in production

---

## 🆘 Support

If you encounter issues:
1. Confirm all dependencies are installed
2. Check server logs for specific errors

**Ready to start!** 🚀

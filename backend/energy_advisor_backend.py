"""
BACKEND - Energy Recommendations System
Integration: Open-Meteo API + Gemini AI
"""

from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
load_dotenv()
from flask_cors import CORS
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for server
import matplotlib.pyplot as plt
import google.generativeai as genai
from datetime import datetime, timedelta
import io
import base64
import os
from functools import lru_cache

# ==========================================
# SERVER CONFIGURATION
# ==========================================
app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Configure Gemini (IMPORTANT! Get your key at https://aistudio.google.com/app/apikey)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# CONSTANTS AND CONFIGURATION
# ==========================================
ZONE_COORDINATES = {
    "new-york": {"lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    "los-angeles": {"lat": 34.0522, "lon": -118.2437, "tz": "America/Los_Angeles"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "tz": "America/Chicago"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "tz": "America/New_York"},
    "seattle": {"lat": 47.6062, "lon": -122.3321, "tz": "America/Los_Angeles"},
}

# Default timezone for custom zones
DEFAULT_TIMEZONE = "auto"

# Thermal comfort thresholds
TEMP_COMFORT = 24  # °C
TEMP_EXTREME = 35  # °C

# ==========================================
# HELPER FUNCTIONS
# ==========================================

@lru_cache(maxsize=100)
def get_climate_data(zone, days_ahead, lat=None, lon=None, tz=None):
    """
    Query Open-Meteo API and return DataFrame with climate data
    Cache of 100 recent queries for optimization
    
    Args:
        zone: Zone name (can be predefined or custom)
        days_ahead: Number of days to project
        lat: Latitude (optional, for custom zones)
        lon: Longitude (optional, for custom zones)
        tz: Timezone (optional, for custom zones)
    """
    # If coordinates are provided directly, use them
    if lat is not None and lon is not None:
        coords = {"lat": lat, "lon": lon, "tz": tz or DEFAULT_TIMEZONE}
    elif zone.lower() in ZONE_COORDINATES:
        coords = ZONE_COORDINATES[zone.lower()]
    else:
        raise ValueError(f"Zone '{zone}' not available and no coordinates provided.")
    
    # Calculate dates
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # API parameters
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "start_date": start_date,
        "end_date": end_date,
        "models": "MRI_AGCM3_2_S",
        "daily": [
            "temperature_2m_mean",
            "temperature_2m_max",
            "relative_humidity_2m_mean",
            "shortwave_radiation_sum",
            "cloud_cover_mean",
            "wind_speed_10m_mean"
        ],
        "timezone": coords["tz"]
    }
    
    # API request
    response = requests.get("https://climate-api.open-meteo.com/v1/climate", params=params)
    response.raise_for_status()
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data['daily'])
    df['time'] = pd.to_datetime(df['time'])
    
    # Rename columns
    df.rename(columns={
        'time': 'Date',
        'temperature_2m_mean': 'Avg_Temp',
        'temperature_2m_max': 'Max_Temp',
        'relative_humidity_2m_mean': 'Relative_Humidity',
        'shortwave_radiation_sum': 'Solar_Radiation',
        'cloud_cover_mean': 'Cloud_Cover',
        'wind_speed_10m_mean': 'Wind_Speed'
    }, inplace=True)
    
    return df


def calculate_energy_metrics(df):
    """
    Calculate key indicators for energy analysis
    """
    metrics = {}
    
    # Temperature
    metrics['avg_temp'] = round(df['Avg_Temp'].mean(), 1)
    metrics['max_temp'] = round(df['Max_Temp'].max(), 1)
    metrics['min_temp'] = round(df['Avg_Temp'].min(), 1)
    
    # Cooling Degree Days (CDD) - AC usage predictor
    df['CDD'] = (df['Avg_Temp'] - TEMP_COMFORT).clip(lower=0)
    metrics['cdd_total'] = round(df['CDD'].sum(), 1)
    
    # Critical days
    metrics['extreme_heat_days'] = int((df['Max_Temp'] > TEMP_EXTREME).sum())
    metrics['comfortable_days'] = int((df['Max_Temp'] <= TEMP_COMFORT).sum())
    
    # Solar potential
    df['Solar_Potential'] = df['Solar_Radiation'] * (1 - df['Cloud_Cover']/100)
    metrics['avg_radiation'] = round(df['Solar_Radiation'].mean(), 1)
    metrics['avg_solar_potential'] = round(df['Solar_Potential'].mean(), 1)
    metrics['optimal_solar_days'] = int((df['Cloud_Cover'] < 40).sum())
    
    # Humidity (thermal comfort factor)
    metrics['avg_humidity'] = round(df['Relative_Humidity'].mean(), 1)
    
    # High energy demand days (heat + humidity)
    metrics['high_demand_days'] = int(
        ((df['Max_Temp'] > 32) & (df['Relative_Humidity'] > 60)).sum()
    )
    
    return metrics


def generate_ai_suggestion(metrics, user_type, zone, days):
    """
    Generate personalized suggestion using Gemini AI
    """
    
    # User-specific context
    user_context = {
        "home": """
        Focus on practical actions for families:
        - Efficient use of air conditioning and fans
        - Taking advantage of natural light and ventilation
        - Consideration of residential solar panels
        - Adjusting appliance usage schedules
        """,
        "industry": """
        Focus on industrial optimization:
        - Load shifting to off-peak hours
        - Predictive maintenance of HVAC systems
        - Cogeneration and energy storage
        - Zone-based climate control automation
        """
    }
    
    prompt = f"""
You are a certified energy advisor. Analyze this climate data for {zone.title()} for the next {days} days and generate ONE energy saving suggestion.

**USER TYPE:** {user_type.upper()}
**ZONE:** {zone.title()}
**PERIOD:** {days} days

**CLIMATE DATA:**
- Average temperature: {metrics['avg_temp']}°C
- Maximum expected temperature: {metrics['max_temp']}°C
- Extreme heat days (>35°C): {metrics['extreme_heat_days']}
- Cooling degree days (CDD): {metrics['cdd_total']}
- Average solar radiation: {metrics['avg_radiation']} MJ/m²
- Effective solar potential: {metrics['avg_solar_potential']} MJ/m²
- Optimal solar days: {metrics['optimal_solar_days']}
- High demand days: {metrics['high_demand_days']}
- Average relative humidity: {metrics['avg_humidity']}%

{user_context[user_type]}

**RESPONSE FORMAT (STRICTLY):**

### [Impactful Suggestion Title]

**Analysis:**
[2-3 sentences linking climate data to specific energy impact]

**Recommended Action:**
[Clear and specific description of WHAT to do and HOW to implement it]

**Estimated Savings:**
[Approximate percentage or amount in USD, with justification based on data]

**Priority:** [High/Medium/Low based on impact vs effort]

---
IMPORTANT: 
- Maximum 200 words total
- Use the numerical data provided
- Be specific with measurable actions
- Don't invent data I didn't give you
"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error generating suggestion: {str(e)}\n\nBasic suggestion: Given the projected climate conditions, consider optimizing climate control usage during peak hours."


def generate_charts(df, zone):
    """
    Generate charts in base64 format to send to frontend
    """
    plt.style.use('bmh')
    charts = {}
    
    # CHART 1: Thermal Profile
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.plot(df['Date'], df['Max_Temp'], 
             color='#E74C3C', alpha=0.7, linewidth=2, label='Maximum Temperature')
    ax1.plot(df['Date'], df['Avg_Temp'].rolling(7).mean(), 
             color='#C0392B', linestyle='--', linewidth=2, label='Trend (7 days)')
    
    ax1.axhline(y=TEMP_COMFORT, color='#27AE60', linestyle=':', linewidth=2, 
                label=f'Comfort Threshold ({TEMP_COMFORT}°C)')
    ax1.axhline(y=TEMP_EXTREME, color='#E67E22', linestyle=':', linewidth=2, 
                label=f'Extreme Heat ({TEMP_EXTREME}°C)')
    
    ax1.fill_between(df['Date'], TEMP_COMFORT, df['Max_Temp'], 
                     where=(df['Max_Temp'] > TEMP_COMFORT), 
                     alpha=0.2, color='red', label='High AC Consumption Zone')
    
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Thermal Profile - {zone.title()}: Energy Demand Prediction', 
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert to base64
    buffer1 = io.BytesIO()
    plt.savefig(buffer1, format='png', dpi=100, bbox_inches='tight')
    buffer1.seek(0)
    charts['temperature'] = base64.b64encode(buffer1.read()).decode()
    plt.close()
    
    # CHART 2: Solar Potential
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    
    color_rad = '#F39C12'
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Solar Radiation (MJ/m²)', color=color_rad, fontsize=12, fontweight='bold')
    ax2.plot(df['Date'], df['Solar_Radiation'], 
             color=color_rad, linewidth=2, label='Available Solar Radiation')
    ax2.tick_params(axis='y', labelcolor=color_rad)
    
    # Secondary axis: Cloud cover
    ax3 = ax2.twinx()
    color_cloud = '#7F8C8D'
    ax3.set_ylabel('Cloud Cover (%)', color=color_cloud, fontsize=12, fontweight='bold')
    ax3.fill_between(df['Date'], df['Cloud_Cover'], 
                     color=color_cloud, alpha=0.3, label='Cloud Coverage')
    ax3.tick_params(axis='y', labelcolor=color_cloud)
    
    plt.title(f'Solar Generation Potential - {zone.title()}', 
              fontsize=14, fontweight='bold')
    
    # Combined legend
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buffer2 = io.BytesIO()
    plt.savefig(buffer2, format='png', dpi=100, bbox_inches='tight')
    buffer2.seek(0)
    charts['solar'] = base64.b64encode(buffer2.read()).decode()
    plt.close()
    
    return charts


# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verify the server is running"""
    return jsonify({
        "status": "ok",
        "message": "Energy Advisor Backend active",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/zones', methods=['GET'])
def get_zones():
    """Return available zones"""
    zones = [{"id": k, "name": k.replace("-", " ").title()} for k in ZONE_COORDINATES.keys()]
    return jsonify({"zones": zones})


@app.route('/api/geocode', methods=['GET'])
def geocode():
    """
    Search locations by name using Open-Meteo geocoding API
    
    Query params:
        q: Search term (city name, address, etc.)
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({"results": [], "error": "Search term must have at least 2 characters"}), 400
    
    try:
        # Use Open-Meteo geocoding API
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": query,
                "count": 10,
                "language": "en",
                "format": "json"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "results" in data:
            for r in data["results"]:
                results.append({
                    "name": r.get("name", ""),
                    "country": r.get("country", ""),
                    "admin1": r.get("admin1", ""),  # State/Province
                    "lat": r.get("latitude"),
                    "lon": r.get("longitude"),
                    "tz": r.get("timezone", DEFAULT_TIMEZONE),
                    "display": f"{r.get('name', '')}, {r.get('admin1', '')} - {r.get('country', '')}"
                })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint: Analyze climate data and generate recommendation
    
    Expected body (JSON):
    {
        "user_type": "home" or "industry",
        "zona": "new-york" or custom name,
        "days": 30,
        "lat": 40.7128,  // optional: latitude for custom zone
        "lon": -74.0060,  // optional: longitude for custom zone
        "tz": "America/New_York"  // optional: timezone
    }
    """
    try:
        # Validate input data
        data = request.json
        user_type = data.get('user_type', 'home').lower()
        zone = data.get('zona', 'new-york')
        days = int(data.get('days', 30))
        
        # Optional coordinates for custom zones
        lat = data.get('lat')
        lon = data.get('lon')
        tz = data.get('tz')
        
        if user_type not in ['home', 'industry']:
            return jsonify({"error": "user_type must be 'home' or 'industry'"}), 400
        
        # Validate predefined zone or coordinates
        zone_lower = zone.lower()
        if zone_lower not in ZONE_COORDINATES and (lat is None or lon is None):
            return jsonify({"error": f"Zone '{zone}' is not predefined. Provide coordinates (lat, lon) or search for a location."}), 400
        
        if not 7 <= days <= 365:
            return jsonify({"error": "Days range must be between 7 and 365"}), 400
        
        # 1. Get climate data
        df = get_climate_data(zone, days, lat, lon, tz)
        
        # 2. Calculate metrics
        metrics = calculate_energy_metrics(df)
        
        # 3. Generate AI suggestion
        suggestion = generate_ai_suggestion(metrics, user_type, zone, days)
        
        # 4. Generate charts
        charts = generate_charts(df, zone)
        
        # 5. Prepare response
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "user_type": user_type,
                "zone": zone,
                "days": days
            },
            "metrics": metrics,
            "suggestion": suggestion,
            "charts": {
                "temperature": charts['temperature'],
                "solar": charts['solar']
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """
    Generate and download CSV with climate data
    
    Expected body (JSON):
    {
        "zona": "new-york",
        "days": 30,
        "lat": 40.7128,  // optional
        "lon": -74.0060,  // optional
        "tz": "America/New_York"  // optional
    }
    """
    try:
        data = request.json
        zone = data.get('zona', 'new-york')
        days = int(data.get('days', 30))
        lat = data.get('lat')
        lon = data.get('lon')
        tz = data.get('tz')
        
        # Get data
        df = get_climate_data(zone, days, lat, lon, tz)
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Return as downloadable file
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'climate_data_{zone}_{days}days_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# RUN SERVER
# ==========================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Energy Advisor Backend - Starting server...")
    print("=" * 60)
    print(f"📍 Predefined zones: {list(ZONE_COORDINATES.keys())}")
    print(f"🌍 Global location search: ENABLED")
    print(f"🤖 AI Model: Gemini 2.0 Flash")
    print(f"🌐 Climate API: Open-Meteo")
    print("=" * 60)
    
    # Verify API key
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  WARNING: Configure your GEMINI_API_KEY before production!")
        print("   Get your free key at: https://makersuite.google.com/app/apikey")
        print("=" * 60)
    
    # Development mode
    app.run(debug=True, host='0.0.0.0', port=5000)

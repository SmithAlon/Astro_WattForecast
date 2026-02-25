"""
API ROUTES - Energy Advisor
All endpoint definitions using Flask Blueprint
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import requests
import io

import energy_advisor_backend as backend

# ==========================================
# BLUEPRINT DEFINITION
# ==========================================
api_bp = Blueprint('api', __name__)


# ==========================================
# ENDPOINTS
# ==========================================

@api_bp.route('/api/health', methods=['GET'])
def health_check():
    """Verify the server is running"""
    return jsonify({
        "status": "ok",
        "message": "Energy Advisor Backend active",
        "timestamp": datetime.now().isoformat()
    })


@api_bp.route('/api/zones', methods=['GET'])
def get_zones():
    """Return available zones"""
    zones = [{"id": k, "name": k.replace("-", " ").title()} for k in backend.ZONE_COORDINATES.keys()]
    return jsonify({"zones": zones})


@api_bp.route('/api/geocode', methods=['GET'])
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
                    "admin1": r.get("admin1", ""),
                    "lat": r.get("latitude"),
                    "lon": r.get("longitude"),
                    "tz": r.get("timezone", backend.DEFAULT_TIMEZONE),
                    "display": f"{r.get('name', '')}, {r.get('admin1', '')} - {r.get('country', '')}"
                })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500


@api_bp.route('/api/analyze', methods=['POST'])
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
        data = request.json
        user_type = data.get('user_type', 'home').lower()
        zone = data.get('zona', 'new-york')
        days = int(data.get('days', 30))
        
        lat = data.get('lat')
        lon = data.get('lon')
        tz = data.get('tz')
        
        if user_type not in ['home', 'industry']:
            return jsonify({"error": "user_type must be 'home' or 'industry'"}), 400
        
        zone_lower = zone.lower()
        if zone_lower not in backend.ZONE_COORDINATES and (lat is None or lon is None):
            return jsonify({"error": f"Zone '{zone}' is not predefined. Provide coordinates (lat, lon) or search for a location."}), 400
        
        if not 7 <= days <= 365:
            return jsonify({"error": "Days range must be between 7 and 365"}), 400
        
        # 1. Get climate data
        df = backend.get_climate_data(zone, days, lat, lon, tz)
        
        # 2. Calculate metrics
        metrics = backend.calculate_energy_metrics(df)
        
        # 3. Generate charts
        charts = backend.generate_charts(df, zone)
        
        # 4. Prepare response
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "parameters": {
                "user_type": user_type,
                "zone": zone,
                "days": days
            },
            "metrics": metrics,
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


@api_bp.route('/api/export-csv', methods=['POST'])
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
        
        df = backend.get_climate_data(zone, days, lat, lon, tz)
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
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

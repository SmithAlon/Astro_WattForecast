/**
 * Climate Service - TypeScript port of the Python backend logic
 * Calls Open-Meteo APIs directly from the browser (no backend required)
 */

// ==========================================
// CONSTANTS
// ==========================================

export const ZONE_COORDINATES: Record<string, { lat: number; lon: number; tz: string }> = {
    "new-york": { lat: 40.7128, lon: -74.0060, tz: "America/New_York" },
    "los-angeles": { lat: 34.0522, lon: -118.2437, tz: "America/Los_Angeles" },
    "chicago": { lat: 41.8781, lon: -87.6298, tz: "America/Chicago" },
    "miami": { lat: 25.7617, lon: -80.1918, tz: "America/New_York" },
    "seattle": { lat: 47.6062, lon: -122.3321, tz: "America/Los_Angeles" },
};

const DEFAULT_TIMEZONE = "auto";
const TEMP_COMFORT = 24; // °C
const TEMP_EXTREME = 35; // °C

// ==========================================
// TYPES
// ==========================================

export interface ClimateRow {
    Date: string;
    Avg_Temp: number;
    Max_Temp: number;
    Relative_Humidity: number;
    Solar_Radiation: number;
    Cloud_Cover: number;
    Wind_Speed: number;
}

export interface EnergyMetrics {
    avg_temp: number;
    max_temp: number;
    min_temp: number;
    cdd_total: number;
    extreme_heat_days: number;
    comfortable_days: number;
    avg_radiation: number;
    avg_solar_potential: number;
    optimal_solar_days: number;
    avg_humidity: number;
    high_demand_days: number;
}

export interface LocationResult {
    display: string;
    lat: number;
    lon: number;
    tz: string;
    name: string;
    admin1?: string;
    country: string;
}

// ==========================================
// FETCH CLIMATE DATA
// ==========================================

export async function fetchClimateData(
    zone: string,
    days: number,
    lat?: number | null,
    lon?: number | null,
    tz?: string | null
): Promise<ClimateRow[]> {
    let coords: { lat: number; lon: number; tz: string };

    if (lat != null && lon != null) {
        coords = { lat, lon, tz: tz || DEFAULT_TIMEZONE };
    } else if (zone.toLowerCase() in ZONE_COORDINATES) {
        coords = ZONE_COORDINATES[zone.toLowerCase()];
    } else {
        throw new Error(`Zone '${zone}' not available and no coordinates provided.`);
    }

    const today = new Date();
    const startDate = today.toISOString().split("T")[0];
    const endDate = new Date(today.getTime() + days * 86400000).toISOString().split("T")[0];

    const params = new URLSearchParams({
        latitude: String(coords.lat),
        longitude: String(coords.lon),
        start_date: startDate,
        end_date: endDate,
        models: "MRI_AGCM3_2_S",
        daily: [
            "temperature_2m_mean",
            "temperature_2m_max",
            "relative_humidity_2m_mean",
            "shortwave_radiation_sum",
            "cloud_cover_mean",
            "wind_speed_10m_mean",
        ].join(","),
        timezone: coords.tz,
    });

    const response = await fetch(`https://climate-api.open-meteo.com/v1/climate?${params}`);
    if (!response.ok) throw new Error(`Climate API error: ${response.status}`);
    const data = await response.json();

    const daily = data.daily as Record<string, (string | number)[]>;
    const rows: ClimateRow[] = daily.time.map((date, i) => ({
        Date: String(date),
        Avg_Temp: Number(daily.temperature_2m_mean[i]),
        Max_Temp: Number(daily.temperature_2m_max[i]),
        Relative_Humidity: Number(daily.relative_humidity_2m_mean[i]),
        Solar_Radiation: Number(daily.shortwave_radiation_sum[i]),
        Cloud_Cover: Number(daily.cloud_cover_mean[i]),
        Wind_Speed: Number(daily.wind_speed_10m_mean[i]),
    }));

    return rows;
}

// ==========================================
// CALCULATE ENERGY METRICS
// ==========================================

export function calculateEnergyMetrics(data: ClimateRow[]): EnergyMetrics {
    const avgTemps = data.map((r) => r.Avg_Temp);
    const maxTemps = data.map((r) => r.Max_Temp);
    const humidity = data.map((r) => r.Relative_Humidity);
    const radiation = data.map((r) => r.Solar_Radiation);
    const cloudCover = data.map((r) => r.Cloud_Cover);

    const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;

    const cddValues = avgTemps.map((t) => Math.max(0, t - TEMP_COMFORT));
    const solarPotential = radiation.map((r, i) => r * (1 - cloudCover[i] / 100));

    return {
        avg_temp: Math.round(avg(avgTemps) * 10) / 10,
        max_temp: Math.round(Math.max(...maxTemps) * 10) / 10,
        min_temp: Math.round(Math.min(...avgTemps) * 10) / 10,
        cdd_total: Math.round(cddValues.reduce((a, b) => a + b, 0) * 10) / 10,
        extreme_heat_days: maxTemps.filter((t) => t > TEMP_EXTREME).length,
        comfortable_days: maxTemps.filter((t) => t <= TEMP_COMFORT).length,
        avg_radiation: Math.round(avg(radiation) * 10) / 10,
        avg_solar_potential: Math.round(avg(solarPotential) * 10) / 10,
        optimal_solar_days: cloudCover.filter((c) => c < 40).length,
        avg_humidity: Math.round(avg(humidity) * 10) / 10,
        high_demand_days: data.filter((r) => r.Max_Temp > 32 && r.Relative_Humidity > 60).length,
    };
}

// ==========================================
// SEARCH LOCATIONS
// ==========================================

export async function searchLocations(query: string): Promise<LocationResult[]> {
    if (!query || query.length < 2) return [];

    const params = new URLSearchParams({
        name: query,
        count: "10",
        language: "en",
        format: "json",
    });

    const response = await fetch(`https://geocoding-api.open-meteo.com/v1/search?${params}`);
    if (!response.ok) throw new Error(`Geocoding API error: ${response.status}`);
    const data = await response.json();

    if (!data.results) return [];

    return data.results.map((r: Record<string, string | number>) => ({
        name: String(r.name || ""),
        country: String(r.country || ""),
        admin1: r.admin1 ? String(r.admin1) : undefined,
        lat: Number(r.latitude),
        lon: Number(r.longitude),
        tz: String(r.timezone || DEFAULT_TIMEZONE),
        display: `${r.name || ""}, ${r.admin1 ? r.admin1 + ", " : ""}${r.country || ""}`,
    }));
}

// ==========================================
// ROLLING AVERAGE HELPER
// ==========================================

export function rollingAverage(values: number[], window: number): (number | null)[] {
    const result: (number | null)[] = new Array(window - 1).fill(null);
    let sum = values.slice(0, window).reduce((a, b) => a + b, 0);
    result.push(sum / window);
    for (let i = window; i < values.length; i++) {
        sum += values[i] - values[i - window];
        result.push(sum / window);
    }
    return result;
}

// ==========================================
// CSV EXPORT HELPER
// ==========================================

export function generateCSV(data: ClimateRow[], zone: string, days: number): void {
    const headers = ["Date", "Avg_Temp", "Max_Temp", "Relative_Humidity", "Solar_Radiation", "Cloud_Cover", "Wind_Speed"];
    const rows = data.map((r) =>
        [r.Date, r.Avg_Temp, r.Max_Temp, r.Relative_Humidity, r.Solar_Radiation, r.Cloud_Cover, r.Wind_Speed].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `climate_data_${zone}_${days}days_${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

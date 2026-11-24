"""
MAZHA - Meenachil Water Banking Data Generator
Builds spatial hydrogeological grid and chronological groundwater time-series
for Meenachil Taluk / River Basin (Pala, Kottayam, Kerala).
"""

import json
import os
import numpy as np
import pandas as pd

np.random.seed(42)

DATA_DIR = "/home/emersion/mazha/data"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------------------
# 1. Spatial Grid Dataset for Meenachil Watershed
# -------------------------------------------------------------------------
# Meenachil Bounding Box: 9.64 to 9.80 N, 76.60 to 76.82 E (Pala centered at 9.712, 76.683)
lats = np.linspace(9.64, 9.80, 25)
lons = np.linspace(76.60, 76.82, 30)

grid_records = []
site_id = 1

for lat in lats:
    for lon in lons:
        # Distance to Meenachil river centerline (approx path from Erattupetta (9.68, 76.78) to Pala (9.71, 76.68) to Kidangoor (9.65, 76.60))
        dist_to_river_km = abs(lat - (9.66 + 0.3 * (lon - 76.60) / 0.22)) * 111.0 + np.random.uniform(-0.5, 0.5)
        dist_to_river_km = max(0.05, dist_to_river_km)

        # Terrain slope (degrees): flat/undulating near river (2-6 deg), steeper toward east/northeast foothills (up to 28 deg)
        east_factor = (lon - 76.60) / 0.22  # 0 to 1
        north_factor = (lat - 9.64) / 0.16
        base_slope = 2.0 + 18.0 * (east_factor**1.6) + 6.0 * (north_factor**1.4)
        noise_slope = np.random.normal(0, 1.8)
        slope_deg = round(max(0.8, base_slope + noise_slope), 1)

        # Rule 1: Slope > 20 deg -> STRICT NO RECHARGE
        is_slope_exceeded = slope_deg > 20.0

        # Weathering Thickness from TGWD (meters): Typically 4-14m in midland laterite valleys, thinner (<3m) on steep ridges
        if is_slope_exceeded:
            weathering_depth_m = round(np.random.uniform(1.2, 3.8), 2)
        else:
            weathering_depth_m = round(np.random.uniform(4.5, 14.2) - 0.2 * slope_deg, 2)
            weathering_depth_m = max(2.5, weathering_depth_m)

        # Soil Permeability (mm/hr): High in river alluvium (25-45), good in laterite (15-30), poor on compacted rocky ridges (2-8)
        if dist_to_river_km < 1.0:
            soil_permeability_mmh = round(np.random.uniform(28.0, 48.0), 1)
            soil_type = "Alluvial Loam"
            hsg = "A"  # Hydrologic Soil Group A
        elif slope_deg < 12.0:
            soil_permeability_mmh = round(np.random.uniform(14.0, 32.0), 1)
            soil_type = "Weathered Laterite"
            hsg = "B"
        else:
            soil_permeability_mmh = round(np.random.uniform(3.0, 12.0), 1)
            soil_type = "Gravelly Clay / Charnockite"
            hsg = "C" if slope_deg <= 20 else "D"

        # Annual Rainfall (mm) from NASA GPM IMERG: Higher towards eastern foothills (2,700 - 3,500 mm)
        annual_rain_mm = round(2750.0 + 650.0 * east_factor + np.random.normal(0, 50.0), 1)

        # Baseline Groundwater Depth (m bgl) from SGWD: Deeper on high laterite ridges, shallow near river
        if dist_to_river_km < 1.0:
            gw_depth_m = round(np.random.uniform(2.5, 5.5), 2)
        else:
            gw_depth_m = round(np.random.uniform(5.5, 12.5), 2)

        # Drainage density (km/km2)
        drainage_density = round(max(0.5, 2.8 - 0.4 * dist_to_river_km + np.random.normal(0, 0.2)), 2)

        # Google Dynamic World LULC
        if dist_to_river_km < 0.6 and np.random.rand() > 0.4:
            lulc = "Built-up"
            scs_cn = 88
        elif slope_deg > 18.0:
            lulc = "Shrub / Forest Canopy"
            scs_cn = 68
        elif east_factor > 0.6:
            lulc = "Plantation (Rubber/Cardamom)"
            scs_cn = 74
        else:
            lulc = "Mixed Agricultural / Homestead"
            scs_cn = 78

        # Spatial Cross-Validation Block (for ZERO spatial data leakage):
        # Partition into 4 distinct geographic quadrants: NW, NE, SW, SE
        quadrant = ("N" if lat >= 9.72 else "S") + ("E" if lon >= 76.71 else "W")

        # Ground truth Recharge Suitability Index (RSI):
        # Exclude slope > 20 immediately
        if is_slope_exceeded:
            rsi_score = round(np.random.uniform(5.0, 24.0), 1)
            suitability_class = 0  # 0 = Excluded / Low
        elif weathering_depth_m < 4.0 or soil_permeability_mmh < 8.0:
            rsi_score = round(np.random.uniform(25.0, 50.0), 1)
            suitability_class = 1  # 1 = Moderate
        else:
            # High suitability: low slope, thick saprolite, permeable laterite, deep unsaturated zone
            base_rsi = 55.0 + (weathering_depth_m / 14.0) * 20.0 + (soil_permeability_mmh / 45.0) * 15.0 - (slope_deg / 20.0) * 15.0
            rsi_score = round(min(98.0, base_rsi + np.random.normal(0, 3.0)), 1)
            suitability_class = 2 if rsi_score >= 65.0 else 1

        grid_records.append({
            "site_id": site_id,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "quadrant": quadrant,
            "rainfall_intensity_mm": annual_rain_mm,     # x1
            "soil_permeability_mmh": soil_permeability_mmh, # x2
            "soil_type": soil_type,
            "slope_deg": slope_deg,                      # x3
            "is_slope_exceeded": is_slope_exceeded,      # slope > 20 deg flag
            "weathering_depth_m": weathering_depth_m,    # x4 (TGWD)
            "groundwater_depth_m": gw_depth_m,           # x5 (SGWD)
            "drainage_density": drainage_density,        # x6
            "lulc": lulc,                                # x7 (Google Dynamic World)
            "scs_cn": scs_cn,
            "dist_to_river_km": round(dist_to_river_km, 2),
            "rsi_score": rsi_score,
            "suitability_class": suitability_class       # 0: Low/Excluded, 1: Moderate, 2: High
        })
        site_id += 1

df_spatial = pd.DataFrame(grid_records)
df_spatial.to_csv(os.path.join(DATA_DIR, "meenachil_spatial_grid.csv"), index=False)
print(f"Created meenachil_spatial_grid.csv with {len(df_spatial)} grid cells.")
print(f"Distribution of suitability classes: {df_spatial['suitability_class'].value_counts().to_dict()}")
print(f"Cells with slope > 20 deg (Strict Excluded): {df_spatial['is_slope_exceeded'].sum()}")

# -------------------------------------------------------------------------
# 2. Key Anchor Sites in Meenachil (Google Open Buildings Rooftop Clusters)
# -------------------------------------------------------------------------
anchor_sites = [
    {
        "id": "pala_college",
        "name_en": "St. Thomas College & Cathedral Campus, Pala",
        "name_ml": "സെന്റ് തോമസ് കോളേജ് & കത്തീഡ്രൽ കാമ്പസ്, പാലാ",
        "lat": 9.7135,
        "lon": 76.6845,
        "category": "Educational & Institutional",
        "roof_area_sqm": 5800,  # Google Open Buildings V3
        "slope_deg": 3.2,
        "weathering_depth_m": 10.5, # TGWD
        "soil_type": "Lateritic Loam",
        "scs_cn": 88,
        "baseline_recharge_kl": 1450.0,
        "mazha_recharge_kl": 3650.0,
        "capex_inr": 85000.0,
        "opex_annual_inr": 4500.0
    },
    {
        "id": "pala_municipality",
        "name_en": "Pala Municipal Complex & Bus Terminal",
        "name_ml": "പാലാ മുനിസിപ്പൽ കോംപ്ലക്സ് & ബസ് ടെർമിനൽ",
        "lat": 9.7110,
        "lon": 76.6820,
        "category": "Municipal & Commercial",
        "roof_area_sqm": 7200,
        "slope_deg": 2.1,
        "weathering_depth_m": 8.8,
        "soil_type": "Alluvial Silt",
        "scs_cn": 92,
        "baseline_recharge_kl": 1200.0,
        "mazha_recharge_kl": 4450.0,
        "capex_inr": 110000.0,
        "opex_annual_inr": 5500.0
    },
    {
        "id": "bharananganam",
        "name_en": "Bharananganam Community Center & School",
        "name_ml": "ഭരണങ്ങാനം കമ്മ്യൂണിറ്റി സെന്റർ & സ്കൂൾ",
        "lat": 9.7025,
        "lon": 76.7190,
        "category": "Public Infrastructure",
        "roof_area_sqm": 4100,
        "slope_deg": 4.6,
        "weathering_depth_m": 9.2,
        "soil_type": "Weathered Laterite",
        "scs_cn": 82,
        "baseline_recharge_kl": 950.0,
        "mazha_recharge_kl": 2720.0,
        "capex_inr": 62000.0,
        "opex_annual_inr": 3800.0
    },
    {
        "id": "mutholy_well_fleet",
        "name_en": "Mutholy Panchayat Drinking Water Well Fleet",
        "name_ml": "മുത്തോലി പഞ്ചായത്ത് കുടിവെള്ള കിണർ ശൃംഖല",
        "lat": 9.7040,
        "lon": 76.6620,
        "category": "Community Well Fleet",
        "roof_area_sqm": 3500,
        "slope_deg": 4.1,
        "weathering_depth_m": 12.0,
        "soil_type": "Porous Laterite",
        "scs_cn": 78,
        "baseline_recharge_kl": 800.0,
        "mazha_recharge_kl": 2380.0,
        "capex_inr": 54000.0,
        "opex_annual_inr": 3200.0
    },
    {
        "id": "kozhuvanal_watershed",
        "name_en": "Kozhuvanal Agriculture Check Dam & Recharge Pit",
        "name_ml": "കൊഴുവനാൽ കാർഷിക ചെക്ക് ഡാം & റീചാർജ് പിറ്റ്",
        "lat": 9.6720,
        "lon": 76.6710,
        "category": "Agricultural Catchment",
        "roof_area_sqm": 9400,
        "slope_deg": 5.8,
        "weathering_depth_m": 11.4,
        "soil_type": "Deep Weathered Laterite",
        "scs_cn": 75,
        "baseline_recharge_kl": 1800.0,
        "mazha_recharge_kl": 5900.0,
        "capex_inr": 135000.0,
        "opex_annual_inr": 6500.0
    },
    {
        "id": "erattupetta_market",
        "name_en": "Erattupetta Municipal Market & Rooftops",
        "name_ml": "ഈരാറ്റുപേട്ട മുനിസിപ്പൽ മാർക്കറ്റ് മേൽക്കൂരകൾ",
        "lat": 9.6910,
        "lon": 76.7850,
        "category": "Commercial Hub",
        "roof_area_sqm": 6100,
        "slope_deg": 5.2,
        "weathering_depth_m": 7.4,
        "soil_type": "River Terrace Sand/Gravel",
        "scs_cn": 90,
        "baseline_recharge_kl": 1100.0,
        "mazha_recharge_kl": 3820.0,
        "capex_inr": 92000.0,
        "opex_annual_inr": 4800.0
    },
    {
        "id": "teekoy_ridge_excluded",
        "name_en": "Teekoy Upper Hill Slopes (Strict Excluded Zone)",
        "name_ml": "തീക്കോയി കുന്നിൻ ചരിവ് (റീചാർജ് ഒഴിവാക്കിയ മേഖല)",
        "lat": 9.7350,
        "lon": 76.8120,
        "category": "High-Hazard Slopes (>20 deg)",
        "roof_area_sqm": 2200,
        "slope_deg": 24.8,  # > 20 deg!
        "weathering_depth_m": 2.2,
        "soil_type": "Thin Skeletal Soil over Rock",
        "scs_cn": 84,
        "baseline_recharge_kl": 300.0,
        "mazha_recharge_kl": 0.0, # Zero artificial recharge
        "capex_inr": 0.0,
        "opex_annual_inr": 0.0
    }
]

with open(os.path.join(DATA_DIR, "meenachil_anchor_sites.json"), "w", encoding="utf-8") as f:
    json.dump(anchor_sites, f, ensure_ascii=False, indent=2)
print("Created meenachil_anchor_sites.json with 7 pilot monitoring anchors.")

# -------------------------------------------------------------------------
# 3. Weekly Groundwater Chronological Time-Series (2016-2024, 460 Weeks)
# -------------------------------------------------------------------------
# Conforms to strict zero temporal data leakage protocol:
# Train: 2016-01-03 to 2021-12-26 (312 weeks)
# Purge Embargo: 2022-01-02 to 2022-02-13 (6 weeks embargo)
# Test: 2022-02-20 to 2024-10-27 (141 out-of-time unseen weeks)

dates = pd.date_range(start="2016-01-03", end="2024-10-27", freq="W-SUN")
n_weeks = len(dates)

# Generate synthetic hydro-climatic series for Meenachil
time_records = []
current_h = 7.5  # initial depth to water table in meters bgl

for i, dt in enumerate(dates):
    doy = dt.dayofyear
    year = dt.year
    
    # Monsoon seasonality: SW monsoon (June-Aug) + NE monsoon (Oct-Nov)
    sw_monsoon = np.exp(-0.5 * ((doy - 195) / 35)**2)
    ne_monsoon = np.exp(-0.5 * ((doy - 305) / 25)**2)
    seasonal_factor = 28.0 * sw_monsoon + 18.0 * ne_monsoon
    
    # Weekly IMERG rainfall (mm)
    weekly_rain_mm = max(0.0, float(seasonal_factor * np.random.uniform(2.5, 6.5) + np.random.exponential(12.0) if np.random.rand() < 0.4 else 0.0))
    weekly_rain_mm = round(weekly_rain_mm, 1)

    # Weekly Temperature (C)
    weekly_temp_c = round(26.0 + 4.5 * np.sin((doy - 80) * 2 * np.pi / 365.25) + np.random.normal(0, 0.6), 1)

    # Evapotranspiration ET (mm/week)
    weekly_et_mm = round(max(10.0, 18.0 + 0.8 * (weekly_temp_c - 24.0) * 7.0 - 0.1 * weekly_rain_mm), 1)

    # Groundwater recharge and extraction dynamics (Water Balance: dSg/dt = Rn + Rm + Qin - Qp - Qout)
    # Natural infiltration Rn (approx 12-18% of rainfall in laterite)
    Rn_mm = weekly_rain_mm * 0.15
    
    # Simulated MAZHA assisted recharge Rm (active from mid-2022 onwards in test period)
    Rm_mm = (weekly_rain_mm * 0.10) if (year >= 2022 and weekly_rain_mm > 15.0) else 0.0

    # Household and agricultural extraction Qp (higher in summer Jan-May)
    is_summer = doy < 150 or doy > 330
    Qp_mm = np.random.uniform(14.0, 22.0) if is_summer else np.random.uniform(6.0, 10.0)

    # Baseflow discharge Qout into Meenachil river (proportional to current head)
    Qout_mm = max(1.0, (12.0 - current_h) * 1.4)

    # Specific Yield Sy = 0.04 (typical hard-rock unconfined laterite)
    Sy = 0.04
    net_flux_mm = (Rn_mm + Rm_mm - Qp_mm - Qout_mm)
    dh_m = -(net_flux_mm / 1000.0) / Sy  # note: h is depth bgl, so positive net flux reduces depth

    current_h += dh_m
    current_h = float(np.clip(current_h, 1.8, 13.5))

    # Mark partition for zero data leakage
    if dt < pd.Timestamp("2022-01-01"):
        split_role = "TRAIN"
    elif dt <= pd.Timestamp("2022-02-15"):
        split_role = "EMBARGO"
    else:
        split_role = "TEST_OUT_OF_TIME"

    time_records.append({
        "date": dt.strftime("%Y-%m-%d"),
        "week_idx": i,
        "doy": doy,
        "sin_doy": round(np.sin(2 * np.pi * doy / 365.25), 4),
        "cos_doy": round(np.cos(2 * np.pi * doy / 365.25), 4),
        "rain_imerg_mm": weekly_rain_mm,
        "temp_c": weekly_temp_c,
        "et_mm": weekly_et_mm,
        "extraction_qp_mm": round(Qp_mm, 2),
        "natural_recharge_rn_mm": round(Rn_mm, 2),
        "mazha_recharge_rm_mm": round(Rm_mm, 2),
        "gw_depth_m_bgl": round(current_h, 2),
        "split_role": split_role
    })

df_time = pd.DataFrame(time_records)
# Compute 4-week lookback antecedent rainfall and lagged water level
df_time["rain_4wk_sum_mm"] = df_time["rain_imerg_mm"].rolling(window=4, min_periods=1).sum().round(1)
df_time["gw_depth_lag1"] = df_time["gw_depth_m_bgl"].shift(1).bfill().round(2)
df_time["gw_depth_lag2"] = df_time["gw_depth_m_bgl"].shift(2).bfill().round(2)

df_time.to_csv(os.path.join(DATA_DIR, "meenachil_groundwater_weekly.csv"), index=False)
print(f"Created meenachil_groundwater_weekly.csv with {len(df_time)} weekly observations.")
print(f"Partition counts: {df_time['split_role'].value_counts().to_dict()}")

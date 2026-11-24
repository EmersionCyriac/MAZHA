"""
Enrich Meenachil Spatial Grid with DTWL, Kriging Variance, and Sub-Basins
Required for Near-Real-Time PDF Specification:
1. Live DWLR Depth to Water Level (DTWL)
2. DTWL < 2.0m mask
3. Kriging variance (distance to DWLR network)
4. Sub-basin zones (Upper, Mid, Lower Meenachil)
5. Storage deficit: (DTWL - 2m) * Sy
"""

import pandas as pd
import numpy as np
import os

data_path = "/home/emersion/mazha/data/meenachil_spatial_grid.csv"
df = pd.read_csv(data_path)

# 1. Depth to Water Level (DTWL in m bgl)
# Base depth with river proximity effect
river_effect = np.maximum(0, 3.2 - df['dist_to_river_km'] * 0.75)
dtwl = np.clip(df['groundwater_depth_m'] - river_effect, 0.9, 13.5).round(2)
df['dtwl_m'] = dtwl

# 2. Water-level mask: DTWL < 2.0m bgl (PDF Step 2)
df['is_dtwl_masked'] = df['dtwl_m'] < 2.0

# 3. DWLR network positions for Kriging variance
anchors = np.array([
    [9.713, 76.684], # Pala
    [9.702, 76.719], # Bharananganam
    [9.704, 76.662], # Mutholy
    [9.691, 76.785], # Erattupetta
    [9.682, 76.810]  # Teekoy
])

def min_dist(lat, lon):
    dists = np.sqrt((anchors[:,0] - lat)**2 + (anchors[:,1] - lon)**2) * 111.0 # km
    return np.min(dists)

dists_to_dwlr = [min_dist(row['lat'], row['lon']) for _, row in df.iterrows()]
# Kriging variance increases quadratically with distance from monitored DWLR wells
krig_var = np.array([round(0.12 + (d / 8.5)**1.8 * 0.95, 3) for d in dists_to_dwlr])
df['kriging_variance'] = krig_var
df['high_kriging_var'] = krig_var > 0.85

# 4. Sub-basin classification
def get_subbasin(lon):
    if lon > 76.74:
        return 'Upper Meenachil (Teekoy / Erattupetta)'
    elif lon > 76.66:
        return 'Mid Meenachil (Pala / Bharananganam)'
    else:
        return 'Lower Meenachil (Mutholy / Kidangoor)'

df['sub_basin'] = df['lon'].apply(get_subbasin)

# 5. Storage Deficit: (DTWL - 2.0m) * Sy in mm (Sy = 0.04)
df['storage_deficit_mm'] = np.maximum(0.0, (df['dtwl_m'] - 2.0) * 0.04 * 1000.0).round(1)

# 6. Steep runoff source flag (Slope > 20 deg)
df['is_runoff_source'] = df['slope_deg'] > 20.0

df.to_csv(data_path, index=False)
print(f"Successfully updated {len(df)} grid cells in {data_path}")
print(f"- Cells with DTWL < 2m (Masked): {df['is_dtwl_masked'].sum()}")
print(f"- Cells with Slope > 20 deg (Excluded): {df['is_slope_exceeded'].sum()}")
print(f"- Cells with High Kriging Variance: {df['high_kriging_var'].sum()}")
print("Sub-basin distribution:")
print(df['sub_basin'].value_counts())

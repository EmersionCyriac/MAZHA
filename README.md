# MAZHA (മഴ) • AI-Enabled Water Banking Digital Twin

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FEmersionCyriac%2FMAZHA)

**AI-Enabled Water Banking Digital Twin Platform for Near-Real-Time Vadose-Zone Storage Accounting and Flood-Buffered Managed Aquifer Recharge**  
*Target Basin:* Meenachil River Basin (Pala, Bharananganam, Mutholy, Kozhuvanal, Erattupetta — Kottayam, Kerala)

---

## 🌊 Overview
MAZHA transforms monsoon flash-flood surface runoff into certified, banked groundwater reserves to alleviate post-monsoon summer water scarcity in Kerala's midland-highland transition zone.

- **Satellite Earth Observation Ingestion:** NASA GPM IMERG, Copernicus DEM 30m, Google Open Buildings V3, Google Dynamic World (10m LULC).
- **Physics-Informed Hydrological Engines:** SCS-CN Runoff, FAO-56 Penman-Monteith Evapotranspiration, Water Table Fluctuation (WTF), Master Recession Curve (MRC).
- **Physical Safety Masks:** Hardcoded exclusion on steep landslide slopes ($>20^\circ$) and shallow water tables ($<2\text{ m}$).
- **Corporate Water Stewardship:** Certified WRI Volumetric Water Benefit Accounting (VWBA 2.0) with amortized lifecycle cost under Google Climate Board criteria ($\le ₹50/\text{kL}$, achieving $₹1.41/\text{kL}$).
- **Full Bilingual Localization:** English & മലയാളം toggle across the entire dashboard and downloadable audit certification cards.

---

## 🚀 Running Locally

```bash
# Clone the repository
git clone https://github.com/EmersionCyriac/MAZHA.git
cd MAZHA

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000` in your browser.

---

## ☁️ Deploying to Vercel

This repository is pre-configured for zero-configuration Vercel deployment:
- Entry point: `api/index.py`
- Configuration: `vercel.json`
- Python runtime: `@vercel/python`

Simply import this repository into your [Vercel Dashboard](https://vercel.com/new) or click the **Deploy with Vercel** button above.

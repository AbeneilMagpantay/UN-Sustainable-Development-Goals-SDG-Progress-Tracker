# UN SDG Progress Tracker

[![Python Version](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-1.11-orange)](https://getdbt.com)
[![BigQuery](https://img.shields.io/badge/BigQuery-4285F4?logo=google-cloud)](https://cloud.google.com/bigquery)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An end-to-end data engineering platform tracking global progress toward the United Nations' 17 Sustainable Development Goals across 190+ countries.

The system operates as a complete data pipeline: extracting data from UN and World Bank APIs, transforming it into a star schema using dbt, and generating ML predictions for 2030 SDG achievement.

## Architectural Overview

The project consists of three main components:

1.  **Data Pipeline & Extraction**: 
    - Fetches SDG indicator data from the UN Statistics API.
    - Pulls economic indicators (GDP, population, life expectancy) from World Bank API.
    - Loads raw data into Google BigQuery for warehousing.

2.  **dbt Transformations**:
    - Staging layer cleans and standardizes source data.
    - Mart layer implements a star schema with dimension and fact tables.
    - Calculates year-over-year progress metrics for trend analysis.

3.  **ML Predictions**:
    - Random Forest classifier predicts 2030 SDG achievement likelihood.
    - Features: historical trends, economic indicators, regional data.
    - Exports predictions to BigQuery and CSV for visualization.

## Directory Structure

```bash
├── scripts/              # ETL and utility scripts
│   ├── extract_data.py       # API extraction pipeline
│   ├── data_quality_check.py # Validation scripts
├── dbt_sdg/              # dbt transformation project
│   ├── models/staging/       # Cleaned source data
│   ├── models/marts/         # Star schema (dims + facts)
├── ml/                   # Machine learning
│   ├── train_sdg_predictor.py
├── data/exports/         # CSV outputs for visualization
```

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/AbeneilMagpantay/UN-Sustainable-Development-Goals-SDG-Progress-Tracker.git
cd UN-Sustainable-Development-Goals-SDG-Progress-Tracker
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Configuration

1. Create a GCP project and enable BigQuery API
2. Create a service account with BigQuery Admin role
3. Download JSON key and create `.env` file:

```ini
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-key.json
GCP_PROJECT_ID=your-project-id
```

## Usage

### Data Extraction

```bash
# Test API connectivity
python scripts/test_apis.py

# Extract and load to BigQuery
python scripts/extract_data.py
```

### dbt Transformations

```bash
cd dbt_sdg
dbt debug --profiles-dir .
dbt build --profiles-dir .
```

### ML Predictions

```bash
python ml/train_sdg_predictor.py
```

## Data Model

| Table | Type | Rows | Description |
|-------|------|------|-------------|
| `dim_countries` | Dimension | 460 | Country metadata with region/income |
| `dim_goals` | Dimension | 17 | SDG goals with categories |
| `dim_time` | Dimension | 25 | Time dimension (2000-2024) |
| `fact_sdg_progress` | Fact | 6,800 | SDG progress by country/goal/year |
| `fact_economic_indicators` | Fact | 6,600 | Economic metrics by country/year |
| `ml_sdg_predictions` | ML Output | 1,200+ | 2030 achievement predictions |

## License

MIT License - see [LICENSE](LICENSE) for details.

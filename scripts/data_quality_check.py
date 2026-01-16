"""
Data Quality Check - Verify data integrity and coverage in BigQuery.
"""

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "sdg-tracker-484407")


def run_quality_checks():
    """Run comprehensive data quality checks."""
    print("\n" + "=" * 70)
    print("🔍 SDG PROGRESS TRACKER - DATA QUALITY CHECK")
    print(f"   Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    # ========================================
    # 1. RAW LAYER - Row Counts
    # ========================================
    print("\n" + "-" * 50)
    print("📊 RAW LAYER - Table Row Counts")
    print("-" * 50)
    
    raw_tables = [
        "sdg_goals", "sdg_targets", "sdg_indicators", 
        "sdg_geo_areas", "sdg_indicator_data",
        "wb_countries", "wb_indicators"
    ]
    
    for table in raw_tables:
        query = f"SELECT COUNT(*) as cnt FROM `{GCP_PROJECT_ID}.raw.{table}`"
        try:
            result = client.query(query).to_dataframe()
            print(f"  ✓ {table}: {result['cnt'].iloc[0]:,} rows")
        except Exception as e:
            print(f"  ❌ {table}: Error - {str(e)[:50]}")
    
    # ========================================
    # 2. MART LAYER - Row Counts
    # ========================================
    print("\n" + "-" * 50)
    print("📊 MART LAYER - Table Row Counts")
    print("-" * 50)
    
    mart_tables = [
        "dim_countries", "dim_goals", "dim_time",
        "fact_sdg_progress", "fact_economic_indicators"
    ]
    
    for table in mart_tables:
        query = f"SELECT COUNT(*) as cnt FROM `{GCP_PROJECT_ID}.staging_marts.{table}`"
        try:
            result = client.query(query).to_dataframe()
            print(f"  ✓ {table}: {result['cnt'].iloc[0]:,} rows")
        except Exception as e:
            print(f"  ❌ {table}: Error - {str(e)[:50]}")
    
    # ========================================
    # 3. DIM_GOALS - Check Content
    # ========================================
    print("\n" + "-" * 50)
    print("🎯 DIM_GOALS - Sample Data")
    print("-" * 50)
    
    query = f"""
    SELECT goal_code, goal_title, goal_category
    FROM `{GCP_PROJECT_ID}.staging_marts.dim_goals`
    ORDER BY CAST(goal_code AS INT64)
    """
    df = client.query(query).to_dataframe()
    for _, row in df.iterrows():
        print(f"  Goal {row['goal_code']}: {row['goal_title'][:45]}... [{row['goal_category']}]")
    
    # ========================================
    # 4. FACT_SDG_PROGRESS - Data Coverage
    # ========================================
    print("\n" + "-" * 50)
    print("📈 FACT_SDG_PROGRESS - Coverage Analysis")
    print("-" * 50)
    
    # Countries with data
    query = f"""
    SELECT COUNT(DISTINCT country_code) as countries,
           COUNT(DISTINCT goal_code) as goals,
           COUNT(DISTINCT year) as years,
           MIN(year) as min_year,
           MAX(year) as max_year
    FROM `{GCP_PROJECT_ID}.staging_marts.fact_sdg_progress`
    """
    df = client.query(query).to_dataframe()
    print(f"  Countries with data: {df['countries'].iloc[0]}")
    print(f"  Goals tracked: {df['goals'].iloc[0]}")
    print(f"  Years covered: {df['years'].iloc[0]} ({df['min_year'].iloc[0]} - {df['max_year'].iloc[0]})")
    
    # Data by goal
    print("\n  Data points by Goal:")
    query = f"""
    SELECT goal_code, COUNT(*) as data_points
    FROM `{GCP_PROJECT_ID}.staging_marts.fact_sdg_progress`
    GROUP BY goal_code
    ORDER BY CAST(goal_code AS INT64)
    """
    df = client.query(query).to_dataframe()
    for _, row in df.iterrows():
        bar = "█" * min(int(row['data_points'] / 100), 30)
        print(f"    Goal {row['goal_code']:>2}: {row['data_points']:>5} records {bar}")
    
    # Data by region
    print("\n  Data points by Region:")
    query = f"""
    SELECT COALESCE(region, 'Unknown') as region, COUNT(*) as data_points
    FROM `{GCP_PROJECT_ID}.staging_marts.fact_sdg_progress`
    GROUP BY region
    ORDER BY data_points DESC
    """
    df = client.query(query).to_dataframe()
    for _, row in df.iterrows():
        print(f"    {row['region'][:30]:30}: {row['data_points']:>5} records")
    
    # ========================================
    # 5. NULL CHECK
    # ========================================
    print("\n" + "-" * 50)
    print("⚠️  NULL VALUE CHECK")
    print("-" * 50)
    
    query = f"""
    SELECT 
        SUM(CASE WHEN country_code IS NULL THEN 1 ELSE 0 END) as null_country,
        SUM(CASE WHEN goal_code IS NULL THEN 1 ELSE 0 END) as null_goal,
        SUM(CASE WHEN year IS NULL THEN 1 ELSE 0 END) as null_year,
        SUM(CASE WHEN avg_indicator_value IS NULL THEN 1 ELSE 0 END) as null_value
    FROM `{GCP_PROJECT_ID}.staging_marts.fact_sdg_progress`
    """
    df = client.query(query).to_dataframe()
    print(f"  Null country_code: {df['null_country'].iloc[0]}")
    print(f"  Null goal_code: {df['null_goal'].iloc[0]}")
    print(f"  Null year: {df['null_year'].iloc[0]}")
    print(f"  Null avg_indicator_value: {df['null_value'].iloc[0]}")
    
    # ========================================
    # 6. SAMPLE DATA
    # ========================================
    print("\n" + "-" * 50)
    print("📋 SAMPLE DATA - fact_sdg_progress (10 rows)")
    print("-" * 50)
    
    query = f"""
    SELECT country_name, goal_code, year, region, income_level, 
           ROUND(avg_indicator_value, 2) as avg_value
    FROM `{GCP_PROJECT_ID}.staging_marts.fact_sdg_progress`
    WHERE country_name IS NOT NULL
    ORDER BY avg_indicator_value DESC
    LIMIT 10
    """
    df = client.query(query).to_dataframe()
    print(df.to_string(index=False))
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ DATA QUALITY CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_quality_checks()

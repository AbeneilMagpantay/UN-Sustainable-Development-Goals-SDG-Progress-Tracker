"""
Export BigQuery mart tables to CSV for Tableau Public.
Tableau Public doesn't support direct BigQuery connections, so we export to CSV files.
"""

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables
load_dotenv()

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "sdg-tracker-484407")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")


def export_table_to_csv(client: bigquery.Client, table_name: str, output_path: str):
    """Export a BigQuery table to CSV."""
    query = f"""
    SELECT * FROM `{GCP_PROJECT_ID}.staging_marts.{table_name}`
    """
    
    print(f"  📥 Exporting {table_name}...")
    df = client.query(query).to_dataframe()
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved {len(df)} rows to {output_path}")
    
    return df


def export_all_marts():
    """Export all mart tables for Tableau."""
    print("\n" + "=" * 60)
    print("🚀 EXPORTING BIGQUERY MARTS TO CSV")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize client
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    # Tables to export
    tables = [
        "dim_countries",
        "dim_goals", 
        "dim_time",
        "fact_sdg_progress",
        "fact_economic_indicators"
    ]
    
    exported_files = []
    
    for table in tables:
        output_path = os.path.join(OUTPUT_DIR, f"{table}.csv")
        try:
            export_table_to_csv(client, table, output_path)
            exported_files.append(output_path)
        except Exception as e:
            print(f"  ❌ Error exporting {table}: {str(e)}")
    
    # Also create a combined dataset for easy Tableau import
    print("\n  📊 Creating combined SDG analysis dataset...")
    
    combined_query = f"""
    SELECT 
        f.progress_id,
        f.country_code,
        f.country_name,
        f.goal_code,
        g.goal_title,
        g.goal_category,
        f.year,
        t.development_era,
        f.region,
        f.income_level,
        f.indicators_measured,
        f.avg_indicator_value,
        f.yoy_change,
        e.gdp_per_capita,
        e.population,
        e.life_expectancy,
        e.adult_literacy_rate
    FROM `{GCP_PROJECT_ID}.staging_marts.fact_sdg_progress` f
    LEFT JOIN `{GCP_PROJECT_ID}.staging_marts.dim_goals` g 
        ON f.goal_code = g.goal_code
    LEFT JOIN `{GCP_PROJECT_ID}.staging_marts.dim_time` t 
        ON f.year = t.year
    LEFT JOIN `{GCP_PROJECT_ID}.staging_marts.fact_economic_indicators` e 
        ON f.country_code = e.country_code AND f.year = e.year
    """
    
    df_combined = client.query(combined_query).to_dataframe()
    combined_path = os.path.join(OUTPUT_DIR, "sdg_analysis_combined.csv")
    df_combined.to_csv(combined_path, index=False)
    print(f"  ✓ Saved {len(df_combined)} rows to {combined_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ EXPORT COMPLETE")
    print("=" * 60)
    print(f"\nExported files saved to: {OUTPUT_DIR}")
    print("\nFiles created:")
    for table in tables:
        print(f"  • {table}.csv")
    print(f"  • sdg_analysis_combined.csv (denormalized for Tableau)")
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📊 Next: Open these CSV files in Tableau Public Desktop")
    

if __name__ == "__main__":
    export_all_marts()

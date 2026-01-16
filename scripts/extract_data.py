"""
SDG Data Extractor - Extract data from UN SDG and World Bank APIs.
Loads data into Google BigQuery for analysis.
"""

import os
import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables
load_dotenv()

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "sdg-tracker")
BQ_DATASET_RAW = os.getenv("BQ_DATASET_RAW", "raw")


class SDGExtractor:
    """Extract data from UN SDG API."""
    
    BASE_URL = "https://unstats.un.org/sdgapi/v1/sdg"
    
    def __init__(self):
        self.client = bigquery.Client(project=GCP_PROJECT_ID)
        self._ensure_dataset_exists()
    
    def _ensure_dataset_exists(self):
        """Create raw dataset if it doesn't exist."""
        dataset_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}"
        try:
            self.client.get_dataset(dataset_id)
            print(f"✓ Dataset {dataset_id} exists")
        except Exception:
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = "US"
            self.client.create_dataset(dataset, exists_ok=True)
            print(f"✓ Created dataset {dataset_id}")
    
    def extract_goals(self) -> pd.DataFrame:
        """Extract all 17 SDG goals."""
        print("\n📥 Extracting SDG Goals...")
        url = f"{self.BASE_URL}/Goal/List"
        response = requests.get(url, timeout=30)
        goals = response.json()
        
        df = pd.DataFrame([{
            'goal_code': str(g['code']),
            'goal_title': g['title'],
            'goal_description': g.get('description', ''),
            'extracted_at': datetime.utcnow()
        } for g in goals])
        
        print(f"  ✓ Extracted {len(df)} goals")
        return df
    
    def extract_targets(self) -> pd.DataFrame:
        """Extract all SDG targets."""
        print("\n📥 Extracting SDG Targets...")
        url = f"{self.BASE_URL}/Target/List"
        response = requests.get(url, timeout=30)
        targets = response.json()
        
        df = pd.DataFrame([{
            'target_code': t['code'],
            'goal_code': t['code'].split('.')[0],
            'target_title': t['title'],
            'target_description': t.get('description', ''),
            'extracted_at': datetime.utcnow()
        } for t in targets])
        
        print(f"  ✓ Extracted {len(df)} targets")
        return df
    
    def extract_indicators(self) -> pd.DataFrame:
        """Extract all SDG indicators."""
        print("\n📥 Extracting SDG Indicators...")
        url = f"{self.BASE_URL}/Indicator/List"
        response = requests.get(url, timeout=30)
        indicators = response.json()
        
        df = pd.DataFrame([{
            'indicator_code': i['code'],
            'goal_code': i['code'].split('.')[0],
            'target_code': '.'.join(i['code'].split('.')[:2]),
            'indicator_description': i.get('description', ''),
            'extracted_at': datetime.utcnow()
        } for i in indicators])
        
        print(f"  ✓ Extracted {len(df)} indicators")
        return df
    
    def extract_geo_areas(self) -> pd.DataFrame:
        """Extract all geographic areas (countries)."""
        print("\n📥 Extracting Geographic Areas...")
        url = f"{self.BASE_URL}/GeoArea/List"
        response = requests.get(url, timeout=30)
        areas = response.json()
        
        df = pd.DataFrame([{
            'geo_area_code': str(a['geoAreaCode']),
            'geo_area_name': a['geoAreaName'],
            'extracted_at': datetime.utcnow()
        } for a in areas])
        
        print(f"  ✓ Extracted {len(df)} geographic areas")
        return df
    
    def extract_indicator_data(self, indicator_codes: list = None, 
                                max_indicators: int = 10) -> pd.DataFrame:
        """Extract actual data values for indicators."""
        print("\n📥 Extracting Indicator Data...")
        
        # Get list of indicators if not provided
        if indicator_codes is None:
            url = f"{self.BASE_URL}/Indicator/List"
            response = requests.get(url, timeout=30)
            all_indicators = response.json()
            indicator_codes = [i['code'] for i in all_indicators[:max_indicators]]
        
        all_data = []
        
        for code in tqdm(indicator_codes, desc="  Fetching indicators"):
            try:
                url = f"{self.BASE_URL}/Indicator/Data"
                params = {
                    'indicator': code,
                    'pageSize': 10000
                }
                response = requests.get(url, params=params, timeout=60)
                data = response.json()
                
                if data.get('data'):
                    for record in data['data']:
                        all_data.append({
                            'indicator_code': code,
                            'geo_area_code': str(record.get('geoAreaCode', '')),
                            'geo_area_name': record.get('geoAreaName', ''),
                            'time_period': record.get('timePeriodStart'),
                            'value': record.get('value'),
                            'value_type': record.get('valueType', ''),
                            'unit': record.get('units', ''),
                            'source': record.get('source', ''),
                            'extracted_at': datetime.utcnow()
                        })
            except Exception as e:
                print(f"\n  ⚠ Error fetching {code}: {str(e)}")
                continue
        
        df = pd.DataFrame(all_data)
        print(f"\n  ✓ Extracted {len(df)} data records")
        return df
    
    def load_to_bigquery(self, df: pd.DataFrame, table_name: str):
        """Load DataFrame to BigQuery."""
        table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()  # Wait for completion
        
        print(f"  ✓ Loaded {len(df)} rows to {table_id}")


class WorldBankExtractor:
    """Extract data from World Bank API."""
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    def __init__(self):
        self.client = bigquery.Client(project=GCP_PROJECT_ID)
    
    def extract_countries(self) -> pd.DataFrame:
        """Extract country metadata with region and income level."""
        print("\n📥 Extracting World Bank Countries...")
        url = f"{self.BASE_URL}/country?format=json&per_page=300"
        response = requests.get(url, timeout=30)
        data = response.json()
        
        countries = data[1] if len(data) > 1 else []
        
        df = pd.DataFrame([{
            'country_code': c.get('id', ''),
            'country_name': c.get('name', ''),
            'country_code_iso3': c.get('iso2Code', ''),
            'region': c.get('region', {}).get('value', ''),
            'income_level': c.get('incomeLevel', {}).get('value', ''),
            'capital_city': c.get('capitalCity', ''),
            'longitude': c.get('longitude', ''),
            'latitude': c.get('latitude', ''),
            'extracted_at': datetime.utcnow()
        } for c in countries if c.get('region', {}).get('value')])  # Filter out aggregates
        
        print(f"  ✓ Extracted {len(df)} countries")
        return df
    
    def extract_indicator(self, indicator_code: str, 
                          indicator_name: str) -> pd.DataFrame:
        """Extract data for a specific World Bank indicator."""
        print(f"\n📥 Extracting {indicator_name}...")
        
        all_data = []
        page = 1
        
        while True:
            url = f"{self.BASE_URL}/country/all/indicator/{indicator_code}"
            params = {
                'format': 'json',
                'per_page': 1000,
                'page': page,
                'date': '2000:2024'
            }
            response = requests.get(url, params=params, timeout=60)
            data = response.json()
            
            if len(data) < 2 or not data[1]:
                break
            
            records = data[1]
            for r in records:
                if r.get('value') is not None:
                    all_data.append({
                        'indicator_code': indicator_code,
                        'indicator_name': indicator_name,
                        'country_code': r.get('country', {}).get('id', ''),
                        'country_name': r.get('country', {}).get('value', ''),
                        'year': int(r.get('date', 0)),
                        'value': float(r.get('value')) if r.get('value') else None,
                        'extracted_at': datetime.utcnow()
                    })
            
            # Check if more pages
            total_pages = data[0].get('pages', 1)
            if page >= total_pages:
                break
            page += 1
        
        df = pd.DataFrame(all_data)
        print(f"  ✓ Extracted {len(df)} records for {indicator_name}")
        return df
    
    def load_to_bigquery(self, df: pd.DataFrame, table_name: str):
        """Load DataFrame to BigQuery."""
        table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_RAW}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        job.result()
        
        print(f"  ✓ Loaded {len(df)} rows to {table_id}")


def run_full_extraction():
    """Run the complete data extraction pipeline."""
    print("\n" + "=" * 60)
    print("🚀 SDG PROGRESS TRACKER - DATA EXTRACTION")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize extractors
    sdg = SDGExtractor()
    wb = WorldBankExtractor()
    
    # ========================================
    # Extract SDG Metadata
    # ========================================
    print("\n" + "-" * 40)
    print("PHASE 1: SDG Metadata")
    print("-" * 40)
    
    # Goals
    df_goals = sdg.extract_goals()
    sdg.load_to_bigquery(df_goals, "sdg_goals")
    
    # Targets
    df_targets = sdg.extract_targets()
    sdg.load_to_bigquery(df_targets, "sdg_targets")
    
    # Indicators
    df_indicators = sdg.extract_indicators()
    sdg.load_to_bigquery(df_indicators, "sdg_indicators")
    
    # Geographic Areas
    df_geo = sdg.extract_geo_areas()
    sdg.load_to_bigquery(df_geo, "sdg_geo_areas")
    
    # ========================================
    # Extract SDG Data (sample of indicators)
    # ========================================
    print("\n" + "-" * 40)
    print("PHASE 2: SDG Indicator Data")
    print("-" * 40)
    
    # Extract data for first 20 indicators (to stay within free tier)
    df_data = sdg.extract_indicator_data(max_indicators=20)
    sdg.load_to_bigquery(df_data, "sdg_indicator_data")
    
    # ========================================
    # Extract World Bank Data
    # ========================================
    print("\n" + "-" * 40)
    print("PHASE 3: World Bank Data")
    print("-" * 40)
    
    # Countries
    df_countries = wb.extract_countries()
    wb.load_to_bigquery(df_countries, "wb_countries")
    
    # Key indicators
    indicators = {
        'NY.GDP.PCAP.CD': 'GDP per capita',
        'SP.POP.TOTL': 'Population',
        'SP.DYN.LE00.IN': 'Life expectancy',
        'SE.ADT.LITR.ZS': 'Adult literacy rate',
    }
    
    all_wb_data = []
    for code, name in indicators.items():
        df = wb.extract_indicator(code, name)
        all_wb_data.append(df)
    
    df_wb_indicators = pd.concat(all_wb_data, ignore_index=True)
    wb.load_to_bigquery(df_wb_indicators, "wb_indicators")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 60)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"\nTables created in BigQuery ({GCP_PROJECT_ID}.{BQ_DATASET_RAW}):")
    print("  • sdg_goals")
    print("  • sdg_targets")
    print("  • sdg_indicators")
    print("  • sdg_geo_areas")
    print("  • sdg_indicator_data")
    print("  • wb_countries")
    print("  • wb_indicators")
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_full_extraction()

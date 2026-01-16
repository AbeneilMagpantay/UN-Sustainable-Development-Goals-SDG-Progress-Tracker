"""
API Test Script - Verify UN SDG and World Bank APIs are accessible.
Run this first to ensure all data sources are working.
"""

import requests
import json
from datetime import datetime


def test_un_sdg_api():
    """Test UN SDG API endpoints."""
    print("\n" + "=" * 60)
    print("🌐 Testing UN SDG API")
    print("=" * 60)
    
    endpoints = {
        "Goals": "https://unstats.un.org/sdgapi/v1/sdg/Goal/List",
        "Targets": "https://unstats.un.org/sdgapi/v1/sdg/Target/List",
        "Indicators": "https://unstats.un.org/sdgapi/v1/sdg/Indicator/List",
        "GeoAreas": "https://unstats.un.org/sdgapi/v1/sdg/GeoArea/List",
    }
    
    results = {}
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "N/A"
                print(f"  ✅ {name}: {count} items")
                results[name] = {"status": "OK", "count": count}
            else:
                print(f"  ❌ {name}: HTTP {response.status_code}")
                results[name] = {"status": "ERROR", "code": response.status_code}
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")
            results[name] = {"status": "ERROR", "message": str(e)}
    
    # Test data endpoint (sample query)
    print("\n  Testing Data Endpoint (Indicator 1.1.1 - Poverty)...")
    try:
        data_url = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/Data"
        params = {"indicator": "1.1.1", "pageSize": 10}
        response = requests.get(data_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            total = data.get("totalElements", 0)
            print(f"  ✅ Data Endpoint: {total} total records available")
            results["Data"] = {"status": "OK", "total_records": total}
        else:
            print(f"  ❌ Data Endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ Data Endpoint: {str(e)}")
    
    return results


def test_world_bank_api():
    """Test World Bank API endpoints."""
    print("\n" + "=" * 60)
    print("🏦 Testing World Bank API")
    print("=" * 60)
    
    # Test country list
    try:
        url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            count = data[0]["total"] if len(data) > 0 else 0
            print(f"  ✅ Countries: {count} available")
        else:
            print(f"  ❌ Countries: HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ Countries: {str(e)}")
    
    # Test sample indicators
    indicators = {
        "GDP per capita": "NY.GDP.PCAP.CD",
        "Population": "SP.POP.TOTL",
        "Life expectancy": "SP.DYN.LE00.IN",
        "CO2 emissions": "EN.ATM.CO2E.PC",
    }
    
    print("\n  Testing Sample Indicators...")
    for name, code in indicators.items():
        try:
            url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=1"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                total = data[0]["total"] if len(data) > 0 else 0
                print(f"  ✅ {name} ({code}): {total} records")
            else:
                print(f"  ❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")


def show_sample_data():
    """Display sample data from APIs."""
    print("\n" + "=" * 60)
    print("📊 Sample Data Preview")
    print("=" * 60)
    
    # Get SDG Goals
    print("\n  UN Sustainable Development Goals:")
    print("  " + "-" * 50)
    
    try:
        response = requests.get("https://unstats.un.org/sdgapi/v1/sdg/Goal/List", timeout=30)
        goals = response.json()
        for goal in goals[:5]:  # Show first 5
            print(f"  Goal {goal['code']}: {goal['title'][:50]}...")
        print(f"  ... and {len(goals) - 5} more goals")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    # Get sample country data
    print("\n  Sample Country Data (Philippines - SDG 1.1.1):")
    print("  " + "-" * 50)
    
    try:
        url = "https://unstats.un.org/sdgapi/v1/sdg/Indicator/Data"
        params = {"indicator": "1.1.1", "areaCode": "608", "pageSize": 5}  # 608 = Philippines
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data.get("data"):
            for record in data["data"][:5]:
                year = record.get("timePeriodStart", "N/A")
                value = record.get("value", "N/A")
                print(f"  Year {year}: {value}%")
        else:
            print("  No data available for Philippines on this indicator")
    except Exception as e:
        print(f"  Error: {str(e)}")


def main():
    print("\n" + "=" * 60)
    print("🚀 SDG PROGRESS TRACKER - API TEST SUITE")
    print(f"   Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run tests
    test_un_sdg_api()
    test_world_bank_api()
    show_sample_data()
    
    print("\n" + "=" * 60)
    print("✅ API TESTS COMPLETE")
    print("=" * 60)
    print("\nNext Steps:")
    print("  1. Setup Google Cloud account and BigQuery")
    print("  2. Create service account and download key")
    print("  3. Copy .env.example to .env and configure")
    print("  4. Run: mage start sdg_pipelines")
    print()


if __name__ == "__main__":
    main()

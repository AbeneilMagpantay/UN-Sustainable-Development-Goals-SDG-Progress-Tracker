"""
SDG Progress Predictor - ML model to forecast SDG achievement by 2030.
Uses historical progress trends to predict which countries are on track.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "sdg-tracker-484407")


def load_training_data():
    """Load SDG progress data from BigQuery."""
    print("\n📥 Loading training data from BigQuery...")
    
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    query = f"""
    SELECT 
        f.country_code,
        f.country_name,
        f.goal_code,
        f.year,
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
    LEFT JOIN `{GCP_PROJECT_ID}.staging_marts.fact_economic_indicators` e
        ON f.country_code = e.country_code AND f.year = e.year
    WHERE f.year >= 2000
        AND f.avg_indicator_value IS NOT NULL
    ORDER BY f.country_code, f.goal_code, f.year
    """
    
    df = client.query(query).to_dataframe()
    print(f"  ✓ Loaded {len(df):,} records")
    print(f"  ✓ Countries: {df['country_code'].nunique()}")
    print(f"  ✓ Goals: {df['goal_code'].nunique()}")
    print(f"  ✓ Years: {df['year'].min()} - {df['year'].max()}")
    
    return df


def engineer_features(df):
    """Create features for ML model."""
    print("\n🔧 Engineering features...")
    
    # Sort data
    df = df.sort_values(['country_code', 'goal_code', 'year'])
    
    # Calculate progress metrics per country-goal
    progress_features = df.groupby(['country_code', 'goal_code']).agg({
        'avg_indicator_value': ['mean', 'std', 'min', 'max', 'last'],
        'yoy_change': ['mean', 'sum'],
        'year': ['count', 'max'],
        'indicators_measured': 'mean'
    }).reset_index()
    
    # Flatten column names
    progress_features.columns = [
        'country_code', 'goal_code',
        'value_mean', 'value_std', 'value_min', 'value_max', 'value_latest',
        'avg_yoy_change', 'total_change',
        'data_points', 'latest_year',
        'avg_indicators_measured'
    ]
    
    # Get latest country attributes
    latest_attrs = df.sort_values('year').groupby('country_code').last()[
        ['country_name', 'region', 'income_level', 'gdp_per_capita', 
         'population', 'life_expectancy', 'adult_literacy_rate']
    ].reset_index()
    
    # Merge features
    features = progress_features.merge(latest_attrs, on='country_code', how='left')
    
    # Fill missing values
    features['value_std'] = features['value_std'].fillna(0)
    features['avg_yoy_change'] = features['avg_yoy_change'].fillna(0)
    features['total_change'] = features['total_change'].fillna(0)
    features['gdp_per_capita'] = features['gdp_per_capita'].fillna(features['gdp_per_capita'].median())
    features['population'] = features['population'].fillna(features['population'].median())
    features['life_expectancy'] = features['life_expectancy'].fillna(features['life_expectancy'].median())
    features['adult_literacy_rate'] = features['adult_literacy_rate'].fillna(features['adult_literacy_rate'].median())
    
    # Create target: On track for 2030?
    # Heuristic: If positive YoY change trend and above median progress, likely on track
    median_change = features['avg_yoy_change'].median()
    features['on_track_2030'] = (features['avg_yoy_change'] > median_change).astype(int)
    
    # Encode categorical variables
    le_region = LabelEncoder()
    le_income = LabelEncoder()
    
    features['region_encoded'] = le_region.fit_transform(features['region'].fillna('Unknown'))
    features['income_encoded'] = le_income.fit_transform(features['income_level'].fillna('Unknown'))
    
    print(f"  ✓ Created {len(features)} country-goal feature records")
    print(f"  ✓ On track (positive trend): {features['on_track_2030'].sum()} ({features['on_track_2030'].mean()*100:.1f}%)")
    
    return features, le_region, le_income


def train_model(features):
    """Train Random Forest classifier to predict SDG achievement."""
    print("\n🤖 Training ML model...")
    
    # Select features for model
    feature_cols = [
        'value_mean', 'value_std', 'value_min', 'value_max', 'value_latest',
        'avg_yoy_change', 'total_change', 'data_points', 'avg_indicators_measured',
        'gdp_per_capita', 'population', 'life_expectancy', 'adult_literacy_rate',
        'region_encoded', 'income_encoded'
    ]
    
    X = features[feature_cols].fillna(0)
    y = features['on_track_2030']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"  ✓ Model trained successfully")
    print(f"  ✓ Test Accuracy: {accuracy*100:.1f}%")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n  📊 Top 5 Feature Importance:")
    for _, row in importance.head(5).iterrows():
        bar = "█" * int(row['importance'] * 50)
        print(f"    {row['feature']:25} {row['importance']:.3f} {bar}")
    
    return model, feature_cols


def generate_predictions(model, features, feature_cols):
    """Generate predictions for all country-goal combinations."""
    print("\n🔮 Generating 2030 predictions...")
    
    X = features[feature_cols].fillna(0)
    
    # Get probability of being on track
    predictions = model.predict_proba(X)[:, 1]
    
    features['prediction_2030_probability'] = predictions
    features['prediction_2030_on_track'] = (predictions >= 0.5).astype(int)
    
    # Categorize
    features['prediction_category'] = pd.cut(
        predictions,
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=['Off Track', 'At Risk', 'Moderate Progress', 'On Track']
    )
    
    print(f"  ✓ Generated predictions for {len(features)} country-goal pairs")
    print("\n  📊 Prediction Summary:")
    summary = features['prediction_category'].value_counts()
    for cat, count in summary.items():
        pct = count / len(features) * 100
        print(f"    {cat:20}: {count:4} ({pct:.1f}%)")
    
    return features


def export_to_bigquery(predictions):
    """Export predictions back to BigQuery."""
    print("\n📤 Exporting predictions to BigQuery...")
    
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    # Select columns to export
    export_cols = [
        'country_code', 'country_name', 'goal_code', 'region', 'income_level',
        'value_latest', 'avg_yoy_change', 'data_points',
        'prediction_2030_probability', 'prediction_2030_on_track', 'prediction_category'
    ]
    
    df_export = predictions[export_cols].copy()
    df_export['prediction_category'] = df_export['prediction_category'].astype(str)
    df_export['predicted_at'] = datetime.utcnow()
    
    # Upload to BigQuery
    table_id = f"{GCP_PROJECT_ID}.staging_marts.ml_sdg_predictions"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )
    
    job = client.load_table_from_dataframe(df_export, table_id, job_config=job_config)
    job.result()
    
    print(f"  ✓ Exported {len(df_export)} predictions to {table_id}")


def save_predictions_csv(predictions):
    """Save predictions to CSV for Power BI."""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "ml_sdg_predictions.csv")
    
    export_cols = [
        'country_code', 'country_name', 'goal_code', 'region', 'income_level',
        'value_latest', 'avg_yoy_change', 'data_points',
        'prediction_2030_probability', 'prediction_2030_on_track', 'prediction_category'
    ]
    
    predictions[export_cols].to_csv(output_path, index=False)
    print(f"  ✓ Saved predictions to {output_path}")


def main():
    print("\n" + "=" * 70)
    print("🎯 SDG PROGRESS PREDICTOR - MACHINE LEARNING MODEL")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Load data
    df = load_training_data()
    
    # Engineer features
    features, le_region, le_income = engineer_features(df)
    
    # Train model
    model, feature_cols = train_model(features)
    
    # Generate predictions
    predictions = generate_predictions(model, features, feature_cols)
    
    # Export results
    export_to_bigquery(predictions)
    save_predictions_csv(predictions)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ ML PREDICTION COMPLETE")
    print("=" * 70)
    
    # Top countries on track
    print("\n🏆 Top 10 Countries Most Likely On Track for 2030:")
    top_countries = predictions.groupby('country_name')['prediction_2030_probability'].mean()
    top_countries = top_countries.sort_values(ascending=False).head(10)
    for i, (country, prob) in enumerate(top_countries.items(), 1):
        bar = "█" * int(prob * 30)
        print(f"  {i:2}. {country:30} {prob*100:.1f}% {bar}")
    
    # Bottom countries
    print("\n⚠️  Top 10 Countries Most At Risk:")
    bottom_countries = predictions.groupby('country_name')['prediction_2030_probability'].mean()
    bottom_countries = bottom_countries.sort_values().head(10)
    for i, (country, prob) in enumerate(bottom_countries.items(), 1):
        bar = "░" * int((1-prob) * 30)
        print(f"  {i:2}. {country:30} {prob*100:.1f}% {bar}")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

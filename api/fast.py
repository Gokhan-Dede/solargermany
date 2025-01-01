from fastapi import FastAPI, HTTPException
from google.cloud import storage
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import json
from io import StringIO

app = FastAPI()
client = storage.Client()

# Utility function to load CSV from GCS
def load_csv_from_gcs(bucket_name: str, file_name: str):
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        data = blob.download_as_text()
        return pd.read_csv(StringIO(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading CSV from GCS: {str(e)}")

# Utility function to load GeoJSON from GCS
def load_geojson_from_gcs(bucket_name: str, file_name: str):
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        geojson_data = blob.download_as_text()
        return json.loads(geojson_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading GeoJSON from GCS: {str(e)}")

# Models for request data validation
class SolarDataRequest(BaseModel):
    state: str
    year: int
    city: Optional[str] = None
    administrative_region: Optional[str] = None

# Load data during startup
BUCKET_NAME = "solar_germany"
DATA_FILE = "solar_visualization.csv"
GEOJSON_FILE = "states.geo.json"

try:
    solar_data = load_csv_from_gcs(BUCKET_NAME, DATA_FILE)
    geojson_data = load_geojson_from_gcs(BUCKET_NAME, GEOJSON_FILE)
except Exception as e:
    solar_data = None
    geojson_data = None
    print(f"Error during initialization: {str(e)}")

@app.get("/")
def root():
    return {"message": "SolarGermany API is running!"}

@app.get("/data")
def get_solar_data():
    if solar_data is not None:
        return solar_data.head(10).to_dict(orient="records")
    else:
        raise HTTPException(status_code=500, detail="Solar data is not available.")

@app.get("/geojson")
def get_geojson():
    if geojson_data is not None:
        return geojson_data
    else:
        raise HTTPException(status_code=500, detail="GeoJSON data is not available.")

@app.post("/filter")
def filter_solar_data(request: SolarDataRequest):
    if solar_data is None:
        raise HTTPException(status_code=500, detail="Solar data is not available.")

    filtered_data = solar_data[(solar_data["State"] == request.state) & (solar_data["CommissioningYear"] == request.year)]

    if request.administrative_region:
        filtered_data = filtered_data[filtered_data["Administrative Region"] == request.administrative_region]

    if request.city:
        filtered_data = filtered_data[filtered_data["City"] == request.city]

    if filtered_data.empty:
        raise HTTPException(status_code=404, detail="No data found for the given filters.")

    return filtered_data.to_dict(orient="records")

from pathlib import Path
import pandas as pd
from google.cloud import bigquery
from typing import Optional
from colorama import Fore, Style
from datetime import datetime
from google.cloud import storage
from solar_germany.params import CHUNK_SIZE, GCP_PROJECT, LOCAL_DATA_PATH, BQ_DATASET, COLUMN_NAMES
from fastapi import HTTPException
import json
import streamlit as st
import os


@st.cache_data
def load_geojson_from_gcs(bucket_name: str, geojson_filename: str) -> dict:
    """
    Load a GeoJSON file from Google Cloud Storage.

    :param bucket_name: Name of the GCS bucket.
    :param geojson_filename: The name of the GeoJSON file in the GCS bucket.
    :return: The GeoJSON data as a Python dictionary.
    """
    try:
        # Initialize the Google Cloud Storage client
        client = storage.Client()

        # Fetch the bucket by name (bucket_name must be provided here)
        bucket = client.bucket(bucket_name)  # Correct method call

        # Get the blob (file) from the bucket
        blob = bucket.blob(geojson_filename)

        # Download the file contents as a string
        geojson_data = blob.download_as_text()

        # Parse the JSON data into a Python dictionary
        geojson_dict = json.loads(geojson_data)

        return geojson_dict

    except Exception as e:
        # Raise an HTTPException if the file can't be loaded
        raise HTTPException(status_code=500, detail=f"Failed to load GeoJSON from GCS: {str(e)}")

@st.cache_resource
def preprocess_solar_data(
    min_year: int = 2000,
    max_year: int = 2024,
    chunk_size: int = CHUNK_SIZE,
) -> None:
    """
    Query and preprocess the solar energy dataset iteratively in chunks.
    Save both raw and processed data to local files for re-use.

    - Query data from BigQuery if not available locally.
    - Save raw data to local cache.
    - Preprocess and save processed data iteratively.
    """

    st.spinner("Preprocessing solar panel data...")

    # Paths for local storage
    raw_data_path = Path(LOCAL_DATA_PATH).joinpath(f"raw_solar_data_{min_year}_{max_year}.csv")
    processed_data_path = Path(LOCAL_DATA_PATH).joinpath(f"processed_solar_data_{min_year}_{max_year}.csv")

    # Ensure the directory exists before saving data
    os.makedirs(LOCAL_DATA_PATH, exist_ok=True)

    # SQL query for BigQuery
    query = f"""
        SELECT {",".join(COLUMN_NAMES)}
        FROM `{GCP_PROJECT}.{BQ_DATASET}.SOLAR`
        WHERE CommissioningYear BETWEEN {min_year} AND {max_year}
        ORDER BY CommissioningYear
    """

    # Check if raw data already exists locally
    raw_data_exists = raw_data_path.is_file()

    if raw_data_exists:
        print("Loading raw data from local CSV...")
        chunks = pd.read_csv(raw_data_path, chunksize=chunk_size)
    else:
        print("Querying data from BigQuery...")
        client = bigquery.Client(project=GCP_PROJECT)
        chunks = client.query(query).result(page_size=chunk_size).to_dataframe_iterable()

    for chunk_id, chunk in enumerate(chunks):
        print(f"Processing chunk {chunk_id + 1}... Initial rows: {len(chunk)}")

        # Preprocess chunk
        chunk["Efficiency"] = chunk["GrossPower"] / chunk["NetRatedPower"]  # Example preprocessing
        print(f"After preprocessing chunk {chunk_id + 1}: {len(chunk)} rows")

        # Save processed chunk to local CSV
        print(f"Saving processed chunk {chunk_id + 1} to {processed_data_path}")
        chunk.to_csv(
            processed_data_path,
            mode="a",
            header=not processed_data_path.is_file(),
            index=False,
        )

        # Save raw chunk if not already cached
        if not raw_data_exists:
            print(f"Caching raw chunk {chunk_id + 1} to {raw_data_path}")
            chunk.to_csv(
                raw_data_path,
                mode="a",
                header=not raw_data_path.is_file(),
                index=False,
            )

    print(Fore.GREEN + f"✅ Raw data saved to {raw_data_path}" + Style.RESET_ALL)
    print(Fore.GREEN + f"✅ Processed data saved to {processed_data_path}" + Style.RESET_ALL)
    print(Fore.GREEN + f"✅ Total rows in raw data: {pd.read_csv(raw_data_path).shape[0]}" + Style.RESET_ALL)
    print(Fore.GREEN + f"✅ Total rows in processed data: {pd.read_csv(processed_data_path).shape[0]}" + Style.RESET_ALL)



# Function to load processed data
@st.cache_data
def load_processed_data(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error("Processed data not found. Please preprocess data first.")
        return pd.DataFrame()

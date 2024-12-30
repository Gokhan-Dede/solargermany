from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib

app = FastAPI()


# Load your data once when the API starts
chunksize = 100000
chunks = pd.read_csv('./data/solar_visualization.csv', chunksize=chunksize)
data = pd.concat(chunks)
data['CommissioningYear'] = pd.to_numeric(data['CommissioningYear'], errors='coerce')


@app.get("/data")
async def get_data(year: int = 2024, state: str = 'Bavaria'):
    filtered_data = data[data['CommissioningYear'] == year]
    print(filtered_data)  # For debugging purposes
    state_data = filtered_data[filtered_data['State'] == state]
    return state_data.to_dict(orient='records')


# Load the entire pipeline model (which includes preprocessing and the trained model)
pipeline = joblib.load("./model/xgb_full_pipeline.pkl")

class InputData(BaseModel):
    # Define the fields required for prediction
    State: str
    Administrative_Region: str
    City: str
    MainOrientation: str
    FeedInType: str
    AssignedActivePowerInverter: float
    Location: str
    NumberOfModules: int

@app.post("/predict/")
async def predict(input_data: InputData):
    # Convert input data into a list of features
    input_features = [
        input_data.State,
        input_data.Administrative_Region,
        input_data.City,
        input_data.MainOrientation,
        input_data.FeedInType,
        input_data.AssignedActivePowerInverter,
        input_data.Location,
        input_data.NumberOfModules,
    ]

    try:
        # Use the pipeline to make a prediction (the pipeline handles preprocessing and prediction)
        prediction = pipeline.predict([input_features])  # The pipeline expects a 2D array

    except Exception as e:
        # Error handling
        raise HTTPException(status_code=400, detail=f"Error processing input data: {e}")

    return {"prediction": prediction.tolist()}

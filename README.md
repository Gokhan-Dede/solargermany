# SolarGERMANY

## Overview
This web application allows users to predict the **Net Rated Power (MW)** and **Gross Power (MW)** of solar panels based on various input parameters such as **State**, **Administrative Region**, **Main Orientation**, and **Assigned Active Power Inverter**. The app uses a machine learning model to provide accurate predictions based on historical solar panel data.

It also includes an interactive map that displays solar panel data, helping users visualize key metrics such as **Number of Modules**, **Location**, and **Efficiency** across different regions in Germany.

## Dataset
The data used for this project has been retrieved from the **Marktstammdatenregister (MaStR)**. This dataset is up-to-date as of **01.10.2024** and includes information on **3,246,859 registered solar panels** in Germany.

### Processing
After retrieval, the dataset underwent several preprocessing steps to:
- **Filter Relevant Data**: Extract necessary columns related to solar panel performance and location.
- **Clean and Normalize**: Handle missing values, inconsistencies, and normalize input features.
- **Enhance Usability**: Add calculated metrics such as panel efficiency and prepare it for use with the prediction model.

The processed dataset serves as the foundation for the app's interactive map and prediction tool.

---

## Solar Panel Power Prediction Tool

### Features
- **Interactive Map**: Visualize solar panel data for each state and region in Germany.
- **Solar Panel Power Prediction Tool**: Input parameters and get predictions for **Net Rated Power** and **Gross Power** (in MW).
- **Data Visualization**: View insights and model validation performance metrics such as **Mean Absolute Error (MAE)** and **R² Score**.

### Tech Stack
- **Streamlit**: For building the interactive user interface.
- **XGBoost**: Machine Learning model used for predictions.
- **Google Cloud Storage**: For storing GeoJSON and dataset files.
- **Google BigQuery**: For querying solar panel data.
- **Docker**: For containerizing the application and ensuring portability.
- **Python 3.10+**: Core programming language.

---

### Project Structure
.
├── api
│   ├── fast.py
│   ├── __init__.py
├── app.py                 # Main Streamlit application
├── data
│   └── solar_visualization.csv  # Sample data used for predictions
├── geojson
│   └── states.geo.json    # GeoJSON file containing state map data
├── Dockerfile             # Dockerfile for containerizing the app
├── Makefile               # For automating build processes
├── model
│   └── xgb_full_pipeline.pkl  # Pre-trained machine learning model
├── notebooks
│   ├── model.ipynb        # Jupyter notebook for model training
│   └── solar_dataframe_creation.ipynb
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation (this file)
└── static
    └── images
        └── logo.png       # App logo


### Installation
1. Clone the Repository
Clone this repository to your local machine:

bash
git clone https://github.com/Gokhan-Dede/solargermany.git
cd solar-panel-prediction

2. Create a Virtual Environment
It’s recommended to use a virtual environment to manage dependencies. Run the following command to create one:

bash
python -m venv venv
Activate the virtual environment:

Windows:

bash
venv\Scripts\activate
Mac/Linux:

bash
source venv/bin/activate

3. Install Dependencies
Install the required Python dependencies:

bash
pip install -r requirements.txt

4. Prepare the Model
Ensure that the pre-trained machine learning model (xgb_full_pipeline.pkl) is available in the /model folder. If you don't have the model, you can retrain it using the Jupyter notebooks in the notebooks directory.

5. Set Up Google Cloud Credentials
If you're using Google Cloud for storage and BigQuery, make sure to set up your Google Cloud credentials:

Go to the Google Cloud Console and create a service account.
Download the JSON key file for your service account.
Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to this file:

bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"

6. Running the Application
You can now run the Streamlit app locally using the following command:

bash
streamlit run app.py
This will start a local server at http://localhost:8501, where you can access the app.

### Docker Deployment

1. Build the Docker Image
To deploy the app using Docker, first build the image by running:

bash
docker build -t solar-panel-prediction .

2. Run the Docker Container
Once the image is built, you can run the container locally:

bash
docker run -p 8501:8501 solar-panel-prediction
This will expose the Streamlit app on http://localhost:8501.

3. Push the Docker Image to Docker Hub (Optional)
If you want to deploy the app to a cloud provider (e.g., AWS, Google Cloud, DigitalOcean), you can push the Docker image to Docker Hub or another container registry:

bash
docker tag solar-panel-prediction yourusername/solar-panel-prediction:latest
docker push yourusername/solar-panel-prediction:latest

4. Deploy to Cloud (Optional)
You can deploy the Docker container to any cloud platform that supports Docker, such as AWS ECS, Google Cloud Run, or DigitalOcean.

### Using the App
Step 1: Select Your Region and State

Choose the State, Administrative Region, and City from the dropdown menus.

Step 2: Provide Solar Panel Information

Select the Main Orientation, Feed-In Type, Assigned Active Power Inverter (kW), and Number of Modules using sliders.

Step 3: Predict Solar Panel Power

Click the Predict button to get predictions for Net Rated Power and Gross Power based on the input features.
Interactive Map

Use the map to visualize solar panel data for different regions in Germany.
Contributing

If you would like to contribute to this project, feel free to fork the repository and submit a pull request. Please follow the code style and make sure to write unit tests for any new features.

### License
This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgements
**Streamlit**: For creating an amazing framework for building data apps.
**XGBoost**: For providing the machine learning model used for predictions.
**Google Cloud**: For the cloud services used to store data and models.
**Marktstammdatenregister (MaStR)**: For providing the solar panel data used in this project.

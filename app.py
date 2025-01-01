import streamlit as st
import plotly.express as px
import pandas as pd
import json
import plotly.graph_objects as go
import joblib
import pickle
from PIL import Image
import base64
from io import BytesIO
from pydantic import BaseModel
from google.cloud import storage
import os
from io import StringIO
import dask.dataframe as dd
import shapely
from fastapi import HTTPException
from pathlib import Path
import pandas as pd
from typing import Optional
from colorama import Fore, Style
from datetime import datetime

from solar_germany.params import LOCAL_DATA_PATH, CHUNK_SIZE
from solar_germany.processing import preprocess_solar_data, load_processed_data, load_geojson_from_gcs
from solar_germany.processing import load_geojson_from_gcs



# Card styling for metrics
card_style = """
    <style>
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        text-align: center;
        width: 100%;
    }
    .metric-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #555;
    }
        .info-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        width: 100%;
    }
    .info-card-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .info-card-content {
        font-size: 1rem;
        color: #555;
        line-height: 1.5;
    }
"""



# Load model (ensure that your model path is correct)
model_path = os.getenv("MODEL_PATH", "./model/xgb_full_pipeline.pkl")
model = joblib.load(model_path)

# Streamlit UI setup
st.set_page_config(layout="wide", page_title="SolarGermany - Empowering a Sustainable Future")


# Function to convert an image to base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Image file path
logo_path = "./static/images/logo.png"

# Convert the logo image to base64
logo_base64 = image_to_base64(logo_path)

# CSS Styling for Sidebar Logo and Title
sidebar_style = """
    <style>
    .sidebar-logo-title {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        margin-bottom: 20px;
    }
    .sidebar-logo {
        width: 50px;
        height: auto;
        margin-right: 15px;
    }
    .sidebar-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #333;
    }
    </style>
"""

# Inject the CSS styling into the sidebar
st.markdown(sidebar_style, unsafe_allow_html=True)

# Display logo and title
st.sidebar.markdown(
    f"""
    <div class="sidebar-logo-title">
        <img src="data:image/png;base64,{logo_base64}" alt="SolarGermany Logo" class="sidebar-logo">
        <div class="sidebar-title">SolarGermany</div>
    </div>
    """,
    unsafe_allow_html=True
)





st.markdown("""<style>
            .stButton>button {
                background-color: #f8f8ff;
                box-shadow: 0px 8px 12px rgba(0, 0, 0, 0.2);
                padding: 20px 25px;
                color: black;
                font-weight: bold;
                font-size: 18px;
                border: none;
                border-radius: 10px;
                width: 100%;
                transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #f8f8ff;
                box-shadow: 0px 8px 12px rgba(0, 0, 0, 0.2);
                color: black;
            }
            .stButton>button:active {
                background-color: #f8f8ff;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .card {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
                margin: 10px;
                width: 100%;
            }
            .card .card-title {
                font-size: 22px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            .card .card-content {
                font-size: 28px;
                color: #555;
            }
            </style>
            """, unsafe_allow_html=True)



# Sidebar settings
year_range = st.sidebar.select_slider(
    "Select Year Range",
    options=range(2000, 2025),
    value=(2000, 2024)
)

# Unpack the selected range
min_year, max_year = year_range

# Initialize session state for state
if 'state' not in st.session_state:
    st.session_state.state = "All States"  # Default state value

# Use the stored state
state = st.session_state.state

st.sidebar.markdown(
    "<p style='font-size: 14px;'>Note: Data for 2000–2024 is ready. Custom ranges require retrieval and preprocessing time.</p>",
    unsafe_allow_html=True
)

# Preprocess Data Button
if st.sidebar.button("Retrieve and Preprocess Data"):
    with st.spinner("Preprocessing data..."):
        preprocess_solar_data(min_year=min_year, max_year=max_year, chunk_size=CHUNK_SIZE)
        st.success("Data preprocessing completed!")

# Load GeoJSON data for Germany (static, loaded once)
germany_geojson = load_geojson_from_gcs("solar_germany", "states.geo.json")

# Check if the processed data exists and load it
processed_data_path = Path(LOCAL_DATA_PATH).joinpath(f"processed_solar_data_{min_year}_{max_year}.csv")

# Ensure the data is loaded only after preprocessing
if os.path.exists(processed_data_path):
    data = load_processed_data(processed_data_path)
else:
    data = pd.DataFrame()  # Empty dataframe to avoid further errors


st.markdown("""
    <style>
        /* Target the horizontal rule (---) in the sidebar */
        .stSidebar hr {
            margin-top: 20px;  /* Adjust the space above the horizontal line */
            margin-bottom: 20px;  /* Adjust the space below the horizontal line */
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar separator
st.sidebar.markdown("---")

# Filter data only after it's available
if not data.empty:
    # Year Slider
    year = st.sidebar.slider("Select a Year", min_value=int(min_year), max_value=int(max_year), value=int(max_year))

    # Filter data by year
    filtered_data = data[data['CommissioningYear'] == year]

    # Group data by state
    df_grouped = filtered_data.groupby('State').agg({'NumberOfModules': 'sum'}).reset_index()

    # Sort the states alphabetically
    states_sorted = sorted(df_grouped['State'].unique()) if not df_grouped.empty else []

    # State selection (if there is data)
    state_list = sorted(data['State'].unique()) if not data.empty else []
    state = st.sidebar.selectbox("Select a State", state_list)

    # Filter data for the selected state
    state_data = filtered_data[filtered_data['State'] == state] if state else pd.DataFrame()

    # Administrative Region selection
    administrative_region = None
    if not state_data.empty:
        administrative_regions_sorted = sorted(state_data['AdministrativeRegion'].unique())
        administrative_region = st.sidebar.selectbox("Select an Administrative Region", administrative_regions_sorted)

    # Display city options only when both state and administrative region are selected
    city_sorted = []
    if state and administrative_region:
        city_filtered_data = filtered_data[
            (filtered_data['State'] == state) & (filtered_data['AdministrativeRegion'] == administrative_region)
        ]
        city_sorted = sorted(city_filtered_data['City'].unique())

    city = st.sidebar.selectbox("Select District", options=city_sorted)


st.markdown(
    """
    <style>
    .sidebar-footer {
        font-size: 0.85rem;
        color: #BDC3C7;
        text-align: left;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True
)



# Sidebar separator
st.sidebar.markdown("---")

# Sidebar content with left-aligned and professional formatting
st.sidebar.markdown(
    """
    <div style="font-size: 14px; color: #333;">
        <p><strong>Gökhan Dede, Data Scientist </strong></p>
        <p><a href="mailto:gokhandede.ai@gmail.com" style="text-decoration: none; color: #1f77b4;">gokhandede.ai@gmail.com</a></p>
        <p><a href="https://www.linkedin.com/in/gokhan-dede/" target="_blank" style="text-decoration: none; color: #0077b5;">LinkedIn</a>
        <a>|</a>
        <a href="https://github.com/Gokhan-Dede/solargermany" target="_blank" style="text-decoration: none; color: #0077b5;">GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("""
<style>
    /* Style for the tab list container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; /* Increased space between tabs for better separation */
    }

    /* Style for individual tabs */
    .stTabs [data-baseweb="tab"] {
        height: 55px; /* Slightly taller tabs for a more spacious design */
        white-space: pre-wrap; /* Allow text wrapping */
        background-color: #f8f8ff; /* Subtle light gray background for unselected tabs */
        border-radius: 8px 8px 0px 0px; /* More rounded top corners for a modern look */
        padding: 12px 20px; /* Ample padding for improved spacing */
        font-size: 32px; /* Large font size for better readability */
        font-weight: 600; /* Semi-bold text for a balanced visual weight */
        color: #5A5A5A; /* Neutral dark gray text color */
        text-align: center; /* Center-align text */
        transition: all 0.3s ease-in-out; /* Smooth transition for hover and selection */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Subtle shadow for a lifted appearance */
    }

    /* Highlight style for the selected tab */
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF; /* Crisp white background for selected tab */
        color: #1A1A1A; /* Darker text color for better emphasis */
        border-bottom: 3px solid #FF4B4B; /* Bold accent border for selected tab */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Slightly more prominent shadow */
    }

    /* Hover effect for tabs */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #E8EBF1; /* Gentle hover color for tabs */
        color: #2A2A2A; /* Slightly darker text on hover */
        transform: translateY(-2px); /* Subtle lift effect on hover */
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.1); /* Enhanced shadow for hover effect */
    }
</style>
""", unsafe_allow_html=True)



st.markdown("""
    <style>
        /* Reduce the gap above the main tabs container */
        .stTabs {
            margin-top: -100px;  /* Adjust this value to reduce the gap further */
            padding-top: 0px;  /* Remove any additional padding at the top */
        }

        /* Reduce the gap above the overall main container */
        .main {
            padding-top: 0px !important;  /* Remove the default padding at the top of the page */
        }
    </style>
""", unsafe_allow_html=True)



# Tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "State Insights", "Regional Focus", "Solar Power Forecast"])



# Tab 1: Always visible content
with tab1:
    st.markdown(card_style, unsafe_allow_html=True)

    # Welcome Card (always shown)
    st.markdown("""
        <style>
            .info-card-title h5 {
                margin-top: 10px;
                margin-bottom: 0px !important; /* Completely remove the gap below the heading */
                padding-bottom: 0px;         /* Add a controlled padding if needed */
                font-size: 20px;             /* Adjust font size (optional) */
                color: #333;                 /* Darker text for the heading */
            }
            .info-card-content p {
                margin-top: 0px !important;  /* Remove the gap above the paragraph */
                margin-bottom: 8px;
                line-height: 1.5;            /* Adjust line spacing for better readability */
                font-size: 16px;             /* Paragraph font size */
                color: #555;                 /* Softer gray for content text */
            }
            .info-card-content ul {
                margin-top: 6px;            /* Space above the list */
                margin-bottom: 6px;         /* Space below the list */
                padding-left: 20px;          /* Add some padding to align list items */
            }
        </style>

        <div class="info-card">
            <div class="info-card-title">
                SolarGermany - Empowering a Sustainable Future
            </div>
            <div class="info-card-content">
                <p>
                    Discover Germany's solar energy landscape with <strong>SolarGermany</strong>—an interactive platform designed for researchers, policymakers, and sustainability enthusiasts.
                </p><p>
                    Explore solar panel data across states and regions, uncover trends, and gain actionable insights into the performance and growth of solar energy in Germany.
                </p>
                <ul>
                    <li><strong>Interactive Data Visualization</strong>: Navigate solar panel distributions by state, region, district, and year.</li>
                    <li><strong>In-Depth Insights</strong>: Analyze growth trends, efficiency changes, and key metrics tailored to specific regions.</li>
                    <li><strong>Performance Metrics</strong>: Access data on total modules, gross power generation, and efficiency.</li>
                    <li><strong>Solar Power Prediction</strong>: Estimate energy generation using real-time data and regional parameters.</li>
                </ul>
                <p>
                    Empower your decision-making with a comprehensive view of Germany’s renewable energy progress.
                </p>
                <div class="info-card-title">
                    <h5>Solar Power Forecast</h5>
                </div>
                <p>
                    This web application predicts the <strong>Net Rated Power (MW)</strong> and <strong>Gross Power (MW)</strong> of solar panels using parameters like <em>State</em>, <em>Administrative Region</em>, <em>Main Orientation</em>, and <em>Assigned Active Power Inverter</em>.
                    Powered by a machine learning model, it delivers accurate predictions based on historical solar panel data.
                </p>
                <p>
                    <strong>The dataset, sourced from the <em>Marktstammdatenregister (MaStR)</em> as of 01.10.2024, covers 3,246,859 registered solar panels in Germany.</strong>
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    # How It Works Card (always shown)
    st.markdown("""
        <div class="info-card">
            <div class="info-card-title">How It Works 💡</div>
            <div class="info-card-content">
                <ol>
                    <li><b>Explore State Metrics</b>: Head to the <b>State Insights</b> tab to select a year and state. Visualize solar metrics, including the number of modules and solar capacity.</li>
                    <li><b>Deep Dive into Regions</b>: Use the <b>Regional Focus</b> tab to explore specific districts within a state. View detailed data on gross power, efficiency, and feed-in types.</li>
                    <li><b>Predict Solar Power</b>: In the <b>Power Forecast</b> tab, input solar panel details like orientation and inverter capacity to estimate energy generation potential.</li>
                </ol>
                <strong>Together, let’s explore how solar power is transforming Germany’s journey toward sustainability.</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if data.empty:
        st.warning("No data available. Please click 'Retrieve and Preprocess Data' in the sidebar to load data.")


if data.empty:
    with tab2:
        st.warning("No data available. Please click 'Retrieve and Preprocess Data' in the sidebar to load data.")

else:
    with tab2:

        st.markdown("""""", unsafe_allow_html=True)

        # Summary metrics
        total_modules = filtered_data['NumberOfModules'].sum()
        total_power = filtered_data['GrossPower'].sum()
        avg_efficiency = filtered_data['Efficiency'].mean()


        # Create a styled card for metrics in a three-column layout
        col1, col2, col3 = st.columns(3)


        st.markdown(card_style, unsafe_allow_html=True)

        # Populate each column with a metric card
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Modules over Germany in {year}</div>
                    <div class="metric-value">{total_modules:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Gross Power (MW)</div>
                    <div class="metric-value">{total_power:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Average Efficiency</div>
                    <div class="metric-value">{avg_efficiency:.2%}</div>
                </div>
            """, unsafe_allow_html=True)


        st.subheader("\U0001F5FA\ufe0f Solar Panel Modul Distribution by States")


        # Create a choropleth map with a solar-themed color scale
        fig = px.choropleth(
            df_grouped,
            geojson=germany_geojson,
            locations='State',
            featureidkey='properties.name',
            color='NumberOfModules',
            color_continuous_scale=["white", "gold", "orange"],  # Custom color scale
            title=f"Number of Modules by State in Germany (Year: {year})"
        )



        # Adjust map layout for stability and visibility
        fig.update_geos(
            fitbounds="locations",
            visible=True,
            projection_scale=1,
            countrycolor="white",
            showcoastlines=False,
            showframe=False,
            showland=True,
            landcolor="white",
            showlakes=False,
            showrivers=False,
            showcountries=False,
            subunitcolor="white",
            showsubunits=False
        )


        fig.update_layout(
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            height=700,
            dragmode=False,
            hovermode=False,
        )

        # Highlight the selected state
        if state:
            state_value = df_grouped.loc[df_grouped['State'] == state, 'NumberOfModules'].values[0]

            highlighted_geojson = {
                "type": "FeatureCollection",
                "features": [
                    feature
                    for feature in germany_geojson["features"]
                    if feature["properties"]["name"] == state
                ]
            }

            # Overlay the selected state using its corresponding color from the map's scale
            fig.add_choropleth(
                geojson=highlighted_geojson,
                locations=[state],
                featureidkey="properties.name",
                z=[state_value],  # Match the value from the data
                colorscale=["white", "gold", "orange"],
                zmin=df_grouped['NumberOfModules'].min(),  # Min value for normalization
                zmax=df_grouped['NumberOfModules'].max(),  # Max value for normalization
                marker=dict(line=dict(width=3, color="blue")),  # Blue outline for the selected state
                showscale=False  # Hide the additional scale for this overlay
            )

        # Display the map
        st.plotly_chart(fig, use_container_width=True)



        if state_data.empty:
            st.write("Please select a state to view details.")
        elif administrative_region:
            # Filter data for the selected administrative region
            district_data = state_data[state_data['AdministrativeRegion'] == administrative_region]

            # Key Metrics for the selected region
            total_power_region = district_data['GrossPower'].sum()
            avg_efficiency_region = district_data['Efficiency'].mean()
            total_modules_region = district_data['NumberOfModules'].sum()


        # Data for Germany (Overall)
        germany_data = data.groupby('CommissioningYear').agg({'NumberOfModules': 'sum'}).reset_index()
        germany_data['CumulativeModules'] = germany_data['NumberOfModules'].cumsum()

        # Data for the selected state
        state_data_full = data[data['State'] == state].groupby('CommissioningYear').agg({'NumberOfModules': 'sum'}).reset_index()
        state_data_full['CumulativeModules'] = state_data_full['NumberOfModules'].cumsum()


        # Combined plot for Germany and the selected state
        fig_combined = go.Figure()

        # Germany's data (Annual Number of Modules and Cumulative Trend)
        fig_combined.add_trace(go.Bar(
            x=germany_data['CommissioningYear'],
            y=germany_data['NumberOfModules'],
            name='Germany - Annual Number of Modules',
            marker_color='Orange'  # Blue color for Germany
        ))
        fig_combined.add_trace(go.Scatter(
            x=germany_data['CommissioningYear'],
            y=germany_data['CumulativeModules'],
            mode='lines',
            name='Germany - Cumulative Trend',
            line=dict(color='Orange', width=2)  # Orange line for Germany
        ))

        # State's data (Annual Number of Modules and Cumulative Trend)
        fig_combined.add_trace(go.Bar(
            x=state_data_full['CommissioningYear'],
            y=state_data_full['NumberOfModules'],
            name=f'{state} - Annual Number of Modules',
            marker_color='Gold'  # Green color for selected state
        ))
        fig_combined.add_trace(go.Scatter(
            x=state_data_full['CommissioningYear'],
            y=state_data_full['CumulativeModules'],
            mode='lines',
            name=f'{state} - Cumulative Trend',
            line=dict(color='Gold', width=2)  # Red line for selected state
        ))

        # Update layout for combined plot
        fig_combined.update_layout(
            title=f"Number of Modules Over Time: Germany vs. {state}",
            xaxis_title="Year",
            yaxis_title="Number of Modules",
            barmode='overlay',  # Overlay bars for better comparison
            plot_bgcolor='white',  # White background for clarity
            template='plotly_white',  # Clean white template for aesthetics
            dragmode=False,
            hovermode=False,
            yaxis=dict(
                type='log',  # Apply logarithmic scale to y-axis
                autorange=True,  # Auto range for logarithmic scale
            )
        )

        # Display the combined plot
        st.plotly_chart(fig_combined, use_container_width=True)



if data.empty:
    with tab3:
        st.warning("No data available. Please click 'Retrieve and Preprocess Data' in the sidebar to load data.")


else:
    # Tab 1: Interactive Map
    with tab3:

        st.markdown("""""", unsafe_allow_html=True)

        # City-level metrics table
        city_grouped = district_data.groupby('City').agg({
            'GrossPower': 'sum',
            'NetRatedPower': 'sum',
            'NumberOfModules': 'sum',
            'Efficiency': 'mean',
        }).reset_index()

        # Rename "City" to "District"
        city_grouped.rename(columns={'City': 'District'}, inplace=True)
        city_data=city_grouped[city_grouped['District']==city]


            # Conditional display based on state and district selection
        if state and administrative_region and city:
            city_data = city_filtered_data[city_filtered_data['City'] == city]
            total_power_city = city_data['GrossPower'].sum()
            avg_efficiency_city = city_data['Efficiency'].mean()
            total_modules_city = city_data['NumberOfModules'].sum()
        else:
            city_data = pd.DataFrame()  # No data for city metrics if not selected
            total_power_city = 0
            avg_efficiency_city = 0
            total_modules_city = 0


        # Create a styled card for metrics in a three-column layout
        col1, col2, col3 = st.columns(3)

        st.markdown(card_style, unsafe_allow_html=True)

        # Populate each column with a metric card
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Modules over {administrative_region} in {year}</div>
                    <div class="metric-value">{total_modules_region:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Gross Power (MW)</div>
                    <div class="metric-value">{total_power_region:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Average Efficiency</div>
                    <div class="metric-value">{avg_efficiency_region:.2%}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(card_style, unsafe_allow_html=True)


        # Pie charts for Feed-in Types and Location Distribution
        feed_in_summary = district_data['FeedInType'].value_counts().reset_index()
        feed_in_summary.columns = ['FeedInType', 'Count']
        location_summary = district_data['Location'].value_counts().reset_index()
        location_summary.columns = ['Location', 'Count']


        # Create two columns for side-by-side charts
        col1, col2 = st.columns(2)

        # Feed-In Types Pie Chart
        with col1:
            fig_feed = px.pie(
                feed_in_summary,
                names='FeedInType',
                values='Count',
                title=f"Feed-In Type Distribution for {administrative_region}",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Sunset
            )
            fig_feed.update_traces(textinfo='percent', textfont_size=14)
            fig_feed.update_layout(
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                template="plotly_white",  # Set template for a clean look
                margin=dict(t=40, b=40, l=40, r=40),  # Adjust margins
                showlegend=True,  # Keep legend visible
                hovermode=False,  # Disable hover interaction
                dragmode=False  # Disable zoom and pan
            )
            st.plotly_chart(fig_feed, use_container_width=True)

        # Location Distribution Pie Chart
        with col2:
            fig_location = px.pie(
                location_summary,
                names='Location',
                values='Count',
                title=f"Location Distribution for {administrative_region}",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Sunset
            )
            fig_location.update_traces(textinfo='percent', textfont_size=14)
            fig_location.update_layout(
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.0
                ),
                template="plotly_white",  # Set template for a clean look
                margin=dict(t=40, b=40, l=40, r=40),  # Adjust margins
                showlegend=True,  # Keep legend visible
                hovermode=False,  # Disable hover interaction
                dragmode=False  # Disable zoom and pan
            )

            st.plotly_chart(fig_location, use_container_width=True)



        # Create a styled card for metrics in a three-column layout
        col1, col2, col3 = st.columns(3)

        st.markdown(card_style, unsafe_allow_html=True)

        # Populate each column with a metric card
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Modules over District {city} in {year}</div>
                    <div class="metric-value">{total_modules_city:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Gross Power (MW)</div>
                    <div class="metric-value">{total_power_city:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Average Efficiency</div>
                    <div class="metric-value">{avg_efficiency_city:.2%}</div>
                </div>
            """, unsafe_allow_html=True)


        # Metric selection for the district
        metric = st.selectbox("Select Metric", options=["NumberOfModules", "GrossPower", "NetRatedPower"])

        # Filter data for the selected city and metric
        city_data = data[(data['State'] == state) &
                        (data['AdministrativeRegion'] == administrative_region) &
                        (data['City'] == city)]

        # Group data by CommissioningYear for selected city
        city_data = city_data.groupby('CommissioningYear').agg({metric: 'sum'}).reset_index()
        city_data['CumulativeMetric'] = city_data[metric].cumsum()

        # Data for Germany (Overall) based on selected metric
        germany_data = data.groupby('CommissioningYear').agg({metric: 'sum'}).reset_index()
        germany_data['CumulativeMetric'] = germany_data[metric].cumsum()

        # Data for selected state and region
        state_data = data[data['State'] == state].groupby('CommissioningYear').agg({metric: 'sum'}).reset_index()
        state_data['CumulativeMetric'] = state_data[metric].cumsum()

        region_data = data[data['AdministrativeRegion'] == administrative_region].groupby('CommissioningYear').agg({metric: 'sum'}).reset_index()
        region_data['CumulativeMetric'] = region_data[metric].cumsum()

        # Combined plot for Germany, selected state, region, and city based on the metric
        fig_combined = go.Figure()

        # Apply color scale for bar chart
        color_scale = 'sunset_r'

        # City bar chart for the selected metric
        fig_combined.add_trace(go.Bar(
            x=city_data['CommissioningYear'],
            y=city_data[metric],
            name=f'{city} - Annual {metric}',
            marker=dict(
                color=city_data[metric],
                colorscale=color_scale,
                colorbar=dict(title=metric)
            )
        ))

        # Add cumulative trend as a line
        fig_combined.add_trace(go.Scatter(
            x=city_data['CommissioningYear'],
            y=city_data['CumulativeMetric'],
            mode='lines',
            name=f'{city} - Cumulative Trend',
            line=dict(color='black', width=2)
        ))

        # Layout for the combined plot
        fig_combined.update_layout(
            title=f"{metric} Over Time: {city}",
            xaxis_title="Year",
            yaxis_title=metric,
            barmode='stack',
            plot_bgcolor='white',
            template='plotly_white',
            dragmode=False,
            hovermode=False,
            xaxis=dict(
                tickmode='array',
                tickvals=city_data['CommissioningYear'],
                ticktext=[str(year) for year in city_data['CommissioningYear']]
            ),
            yaxis=dict(
                type='log',  # Logarithmic scale
                autorange=True,
            ),
            coloraxis_colorbar=dict(
                title=metric,
                tickvals=[min(city_data[metric]), max(city_data[metric])],
                ticktext=[f"{min(city_data[metric]):.2f}", f"{max(city_data[metric]):.2f}"]
            ),
            legend=dict(
                orientation='h',
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )

        # Display combined plot
        st.plotly_chart(fig_combined, use_container_width=True)

if data.empty:
    with tab4:
        st.warning("No data available. Please click 'Retrieve and Preprocess Data' in the sidebar to load data.")


else:
    # Tab 1: Interactive Map
    with tab4:
        # Solar Panel Prediction Tool Card
        st.markdown("""
            <div class="info-card">
                <div class="info-card-title">Solar Panel Power Forecast</div>
                <div class="info-card-content">
                    By selecting your <b>State</b>, <b>Administrative Region</b>, and <b>District</b>, you can predict the solar panel power generation for your setup.
                    <br><br>
                    This tool uses advanced models to estimate key performance metrics, including the <b>Net Rated Power (MW)</b> and <b>Gross Power (MW)</b>.
                    <br><br>
                    Follow the steps below to input your system's details and receive an accurate prediction of its energy potential.
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Create a separate dataset for state and administrative region, ignoring the year filter
        state_region_data = data[(data['State'] == state) & (data['AdministrativeRegion'] == administrative_region)] if state and administrative_region else pd.DataFrame()


        if "predict_button_clicked" not in st.session_state:
            st.session_state.predict_button_clicked = False


        # Step 2: Create a 2-column layout for sliders
        col1, col2 = st.columns(2)


        with col1:
            # Step 3: Select Main Orientation
            orientations = sorted(data['MainOrientation'].unique())
            main_orientation_selected = st.selectbox("Select Main Orientation", options=orientations)

            # Step 4: Radio Button for Feed-In Type
            feed_in_type_selected = st.radio(
                "Select Feed-In Type",
                options=["Full Feed-in", "Partial Feed-in"],
                index=0  # Default to "Full Feed-in"
            )

        with col2:
            # Step 5: Input Assigned Active Power Inverter (Slider for range selection)
            assigned_power_min = 0.0  # Fixed min value based on your dataset
            assigned_power_max = 30.0  # Fixed max value based on your dataset

            # Slider for assigned power
            assigned_power = st.slider(
                "Select Assigned Active Power Inverter (kW)",
                min_value=float(assigned_power_min),
                max_value=float(assigned_power_max),
                value=15.0,
                step=0.1,
            )

            # Step 6: Input Number of Modules (Slider for range selection)
            modules_min = 1.0  # Fixed min value based on your dataset
            modules_max = 110.0  # Fixed max value based on your dataset

            num_modules = st.slider(
                "Select Number of Modules",
                min_value=int(modules_min),
                max_value=int(modules_max),
                value=int((modules_min + modules_max) / 2),  # Default to the middle of the range
                step=1
            )

        # Step 7: Select Location Type
        locations = sorted(data['Location'].unique())
        location_selected = st.selectbox("Select Location Type", options=locations)

        # Grouped input feature set for prediction
        input_features = pd.DataFrame({
            'State': [state],
            'Administrative Region': [administrative_region],
            'City': [city],
            'MainOrientation': [main_orientation_selected],
            'FeedInType': [feed_in_type_selected],
            'AssignedActivePowerInverter': [assigned_power],
            'Location': [location_selected],
            'NumberOfModules': [num_modules],
        })

        # Clear Button & Predict Button
        st.markdown('<hr>', unsafe_allow_html=True)


        # Predict Button
        if st.button("Predict", key="predict_button", use_container_width=True):
            st.session_state.predict_button_clicked = True
            st.session_state.active_tab = "tab4"

            with st.spinner("Predicting... Please wait."):
                try:
                    # Load the model (make sure your path is correct)
                    model = joblib.load("./model/xgb_full_pipeline.pkl")
                    predictions = model.predict(input_features)
                    gross_power, net_rated_power = predictions[0]

                    # Display the results (if prediction is successful)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                            <div class="card">
                                <div class="card-title">Net Rated Power (MW)</div>
                                <div class="card-content">{net_rated_power:.2f}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                            <div class="card">
                                <div class="card-title">Gross Power (MW)</div>
                                <div class="card-content">{gross_power:.2f}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Reset the button state after prediction
                    st.session_state.predict_button_clicked = False  # Reset button color after prediction

                except Exception as e:
                    st.error(f"Error during prediction: {e}")


            st.markdown("<hr>", unsafe_allow_html=True)

            st.markdown("""
            <div class="card">
                <div class="card-title">Model Validation Performance</div>
                <div class="card-content" style="font-size: 16px;">Mean Absolute Error (MAE): 0.5435 MW</div>
                <div class="card-content" style="font-size: 16px;">R² Score: 0.9527</div>
                <div class="card-content" style="font-size: 16px;">Note: These metrics are based on offline validation with historical data.</div>
                <div class="card-content" style="font-size: 16px;">An R² score of 0.9527 means that the trained machine learning model explains 95.27% of the variance in the target data.</div>
                <div class="card-content" style="font-size: 16px;">MAE represents the average of the absolute differences between the predicted and actual values.</div>
            </div>
            """, unsafe_allow_html=True)

        # Change button appearance after prediction or reset
        if st.session_state.predict_button_clicked:
            st.markdown("""
                <style>
                .stButton>button {
                    background-color: #d3d3d3;
                    box-shadow: none;
                    color: #a9a9a9;
                    font-weight: normal;
                    font-size: 18px;
                }
                </style>
            """, unsafe_allow_html=True)

import folium
import osmnx as ox
import pandas as pd
import geopandas as gpd
import requests
from folium.plugins import MarkerCluster
import streamlit as st
import csv
from streamlit_folium import st_folium
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score

ox.__version__

# Function to retrieve and plot hospitals and clinics with Folium
def plot_hospitals_and_clinics(place):
    # Download/model a street network for the specified place
    G = ox.graph_from_place(place, network_type="drive", retain_all=True)
    
    # Get center coordinates for the map
    center_lat, center_lon = ox.geocode(place)
    
    # Create a Folium map centered around the place
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # Create a MarkerCluster object
    marker_cluster = MarkerCluster().add_to(m)

    # Plot street network on Folium map
    ox.plot_graph_folium(G, graph_map=m, edge_color="blue", edge_width=0.3, bgcolor="#333333")
    
    # Retrieve hospital and clinic data for the place
    tags = {"amenity": ["hospital", "clinic"]}
    gdf = ox.features_from_place(place, tags)
    
    # Iterate through each hospital or clinic and add markers to the map
    for idx, row in gdf.iterrows():
        try:
            # Check if the hospital or clinic already has a location
            if 'geometry' in row and not row['geometry'].is_empty:
                latitude = row['geometry'].y
                longitude = row['geometry'].x
                # Add marker to the marker cluster
                folium.Marker([latitude, longitude], popup=row['name']).add_to(marker_cluster)
            else:
                print(f"Location not found for {row['name']}")
        except Exception as e:
            print(f"Error processing {row['name']}: {e}")

    # Display the Folium map
    m.save('city_map_with_hospitals_and_clinics.html')

    # Call to render Folium map in Streamlit
    st_data = st_folium(m, width=725)

    print("Map with hospitals and clinics saved as city_map_with_hospitals_and_clinics.html")

# Initialize lists to store data
cities = []
population = []
average_distance = []
average_time = []
number_of_beds = []
bed_to_pop_ratio = []
grades = []

def grade(bed_to_pop_ratio, average_time, average_distance):
    # max 5 points for bed to pop ratio
    # max 3 points for average time
    # max 2 points for average distance
    grade_beds = (6 * bed_to_pop_ratio) / 20.0
    grade_beds = min(grade_beds, 6)  # to avoid grade > 6

    grade_time = (3 * 360.0) / average_time
    grade_time = min(grade_time, 3)  # to avoid grade > 3

    grade_distance = (1 * 1750.0) / average_distance
    grade_distance = min(grade_distance, 1)  # to avoid grade > 1

    return grade_beds + grade_time + grade_distance

# Read the CSV file
with open('hospital_data_ro.csv', 'r', encoding='UTF-8', newline='') as csvfile:
    DictReader = csv.DictReader(csvfile)
    for row in DictReader:
        cities.append(row['city_name'])
        population.append(row['population'])
        average_distance.append(row['average_distance'])
        average_time.append(row['average_time'])
        number_of_beds.append(row['number_of_beds'])
        bed_to_pop_ratio.append(row['bed_population_ratio'])

# Convert lists to DataFrame
data = pd.DataFrame({
    'city_name': cities,
    'population': population,
    'average_distance': average_distance,
    'average_time': average_time,
    'number_of_beds': number_of_beds,
    'bed_population_ratio': bed_to_pop_ratio
})

# Data cleaning: replace empty strings with NaN and drop rows with NaN values
data.replace('', float('nan'), inplace=True)
data.dropna(inplace=True)

# Convert columns to numeric
data['population'] = pd.to_numeric(data['population'])
data['average_distance'] = pd.to_numeric(data['average_distance'])
data['average_time'] = pd.to_numeric(data['average_time'])
data['number_of_beds'] = pd.to_numeric(data['number_of_beds'])
data['bed_population_ratio'] = pd.to_numeric(data['bed_population_ratio'])

# Calculate grades
data['grade'] = data.apply(lambda row: grade(row['bed_population_ratio'], row['average_time'], row['average_distance']), axis=1)

# Split the data into training and testing sets
X = data[['bed_population_ratio', 'average_time', 'average_distance']]
y = data['grade']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Decision Tree Regressor model
model = DecisionTreeRegressor(random_state=42)
model.fit(X_train, y_train)

# Predict on the test set
y_pred = model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# Message for the user
city_input = st.text_input("City Input")

# Searching for the city in the data frame
if city_input:
    if city_input in cities:
        # Get the index of the city
        index = cities.index(city_input)
        
        # Plot hospitals and clinics for the specified city
        plot_hospitals_and_clinics(city_input)
        
        # Retrieve the parameters for grading
        bed_to_pop_ratio_value = float(bed_to_pop_ratio[index])
        average_time_value = float(average_time[index])
        average_distance_value = float(average_distance[index])
        
        # Calculate the healthcare system grade
        healthcare_grade = grade(bed_to_pop_ratio_value, average_time_value, average_distance_value)
        
        # Display the city information in text areas
        st.text_area("City Name", cities[index])
        st.text_area("Population", population[index])
        st.text_area("Average Distance", f"{average_distance_value / 1000:.2f} kms")
        st.text_area("Average Time", f"{average_time_value / 60:.2f} minutes")
        st.text_area("Number of Beds", number_of_beds[index])
        st.text_area("Bed/1000 People Ratio", f"{bed_to_pop_ratio_value:.2f}")
        st.text_area("Healthcare System Grade", f"{healthcare_grade:.2f}")
        
        # Predict the grade using the trained model
        predicted_grade = model.predict([[bed_to_pop_ratio_value, average_time_value, average_distance_value]])[0]
        st.text_area("Predicted Healthcare System Grade", f"{predicted_grade:.2f}")

        # Display the accuracy score in Streamlit
        st.write(f"Model Mean Squared Error: {mse:.2f}")
        st.write(f"Model R^2 Score: {r2:.2f}")    
    else:
        st.write("City not found in the dataset.")
else:
    st.write("Please enter a city.")

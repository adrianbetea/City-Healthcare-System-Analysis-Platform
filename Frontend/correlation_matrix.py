import pandas as pd

# Load the CSV file
data = pd.read_csv('hospital_data_ro.csv')

# Inspect the first few rows to understand the data structure
print(data.head())

# Identify the columns
print(data.columns)

# Convert relevant columns to numeric, handling errors
data['population'] = pd.to_numeric(data['population'], errors='coerce')
data['average_distance'] = pd.to_numeric(data['average_distance'], errors='coerce')
data['average_time'] = pd.to_numeric(data['average_time'], errors='coerce')
data['number_of_beds'] = pd.to_numeric(data['number_of_beds'], errors='coerce')
data['bed_population_ratio'] = pd.to_numeric(data['bed_population_ratio'], errors='coerce')

# Drop rows with NaN values that result from conversion errors
data.dropna(inplace=True)

# Select only the numeric columns for the correlation matrix
numeric_data = data[['population', 'average_distance', 'average_time', 'number_of_beds', 'bed_population_ratio']]

print ("urmeaza matricea de corelare")
# Calculate the correlation matrix
correlation_matrix = numeric_data.corr()

# Print the correlation matrix
print(correlation_matrix)
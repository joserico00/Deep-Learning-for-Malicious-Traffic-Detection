import pandas as pd
import os
import glob

# Define the folder path where your CSV files are stored
folder_path = '.'

# Get a list of all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))


# Print all CSV files found
if csv_files:
    print("Found the following CSV files:")
    for file in csv_files:
        print(file)
else:
    print("No CSV files found in the specified directory!")

# Create an empty list to store DataFrames
dataframes = []

# Loop through the list of CSV files and read each file
for file in csv_files:
    df_temp = pd.read_csv(file, delimiter='|', low_memory=False, na_values=['?', 'NA', 'null', '-']) # Read the CSV file into a DataFrame
    dataframes.append(df_temp)   # Append to the list

# Combine all DataFrames into a single DataFrame
df = pd.concat(dataframes, ignore_index=True)
del dataframes
del df_temp
# Display the combined DataFrame


missing_threshold = 0.2
total_rows = len(df)
columns_to_drop = [col for col in df.columns if df[col].isnull().sum() / total_rows > missing_threshold]
print("\nDropping columns with more than 50% missing values:", columns_to_drop)
df = df.drop(columns=columns_to_drop)



if 'history' in df.columns:
    print("\nDropping rows with missing 'history' values")
    df = df.dropna(subset=['history'])


# Count unique values for each column
unique_counts = df.nunique()


# Display columns with all unique or single unique values
print("Columns with all unique values:")
print(unique_counts[unique_counts == len(df)])  # Likely IDs or timestamps

print("\nColumns with a single unique value:")
print(unique_counts[unique_counts <= 1])  # Not useful


#No need for IPs or UID because of biased
#tunnel parents local resp and local_origen doesnt have anything
irrelevant_cols = ['uid', 'ts', 'id.orig_h', 'id.resp_h']
df.drop(columns=irrelevant_cols, inplace=True)

# Optionally, save the combined DataFrame to a new CSV
df.to_csv('./combined_data.csv', index=False)

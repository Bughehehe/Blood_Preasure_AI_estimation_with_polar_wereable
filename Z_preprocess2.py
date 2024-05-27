import pandas as pd

# Define the path to the pressure.txt file
file_path = 'pressure.txt'

# Initialize empty lists to store data
filenames = []
sys_values = []
dia_values = []

# Read the file line by line and extract data
with open(file_path, 'r') as file:
    for line in file:
        # Split the line into components (Filename, SYS, DIA)
        parts = line.strip().split()
        if len(parts) == 3:  # Ensure there are three parts in each line
            filename = parts[0]
            sys_val = int(parts[1])
            dia_val = int(parts[2])
            # Append data to respective lists
            filenames.append(filename[:-5])
            sys_values.append(sys_val)
            dia_values.append(dia_val)

# Create a DataFrame from the extracted data
data = {
    'Filename': filenames,
    'SYS': sys_values,
    'DIA': dia_values
}

pressure_df = pd.DataFrame(data)

# Step 2: Read merged_df from merged_data.csv
merged_file_path = 'merged_data.csv'
merged_df = pd.read_csv(merged_file_path)

# Step 3: Merge dataframes based on 'Filename' column
final_df = pd.merge(merged_df, pressure_df, on='Filename', how='left')

# Display the final dataframe with SYS and DIA columns added
if 'Unnamed: 0' in final_df.columns:
    final_df = final_df.drop(columns=['Unnamed: 0'])

# Print the DataFrame
final_df.to_csv("data_to_model.csv")

import os
import pandas as pd
from datetime import datetime
import re
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

ECG_PERCEMTAGE_START = 0.8

CUTOFF_FREQ = 25

# ECG_WINDOW = int(130 * 0.6)
# PPG_WINDOW = int(55 * 0.6)

# ECG_WINDOW = 130 * 1
# PPG_WINDOW = 55  * 1

ECG_WINDOW = 130 * 2
PPG_WINDOW = 55  * 2

# ECG_WINDOW = 130 * 4
# PPG_WINDOW = 55 * 4

# ECG_WINDOW = 130 * 9
# PPG_WINDOW = 55  * 9


PPG_CHANNEL = 'channel 0'

# Define function to filter data windows
def filter_data_window(data_window, filtered_window):
    if len(data_window) > filtered_window:
        # Apply filtering to ensure the desired window size
        filtered_data_window = data_window.head(filtered_window)
    else:
        # If the window size is smaller than the desired size, pad with zeros
        padding = filtered_window - len(data_window)
        zeros_df = pd.DataFrame(0, index=range(padding), columns=data_window.columns)
        filtered_data_window = pd.concat([data_window, zeros_df])
    return filtered_data_window

def generate_column_names(ecg_count, ppg_count):
    # Define column names for ECG and PPG
    ecg_columns = [f'ECG_{i}' for i in range(1, ecg_count + 1)]
    ppg_columns = [f'PPG_{i}' for i in range(1, ppg_count + 1)]

    # Combine both lists and prepend 'Filename'
    column_names = ['Filename'] + ecg_columns + ppg_columns

    return column_names

def repair_PPG(file_path):
    # Read the text file
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Remove trailing semicolons and split each line into data fields
    cleaned_data = []
    for line in lines[1:]:  # Skip the header line
        if line.strip():  # Skip empty lines
            fields = line.strip().rstrip(';').split(';')
            cleaned_data.append(fields)
    
    # Create DataFrame from cleaned data
    column_names = lines[0].strip().split(';')  # Extract column names from header
    df = pd.DataFrame(cleaned_data, columns=column_names)

    # Convert columns to appropriate dtypes
    df[['channel 0', 'channel 1', 'channel 2', 'ambient']] = df[['channel 0', 'channel 1', 'channel 2', 'ambient']].apply(pd.to_numeric)

    df['channel 0'] -= df['ambient']
    df['channel 1'] -= df['ambient']
    df['channel 2'] -= df['ambient']

    df['main_channel'] = df[PPG_CHANNEL]

    df = df.drop(columns=["sensor timestamp [ns]", "channel 0", "channel 1", "channel 2", "ambient"])

    df['Phone timestamp'] = pd.to_datetime(df['Phone timestamp'], format='%Y-%m-%dT%H:%M:%S.%f')

    return df

def parse_filename(filename):
    # Use regex to extract date, name, index, and type
    match = re.match(r"(\d{2}_\d{2}_\d{2})_(\w+)_(\d+)_(ECG|PPG)\.txt", filename)
    if match:
        date_str, name, index, type_ = match.groups()
        date = datetime.strptime(date_str, '%d_%m_%y')
        return date, name, int(index), type_
    else:
        # Handle unexpected filename format
        return None

def get_sorted_files(directory):
    if os.path.exists(directory) and os.path.isdir(directory):
        files = [filename for filename in os.listdir(directory) if os.path.isfile(os.path.join(directory, filename))]
        files = [f for f in files if parse_filename(f)]  # Filter out files with unexpected format
        files.sort(key=lambda x: parse_filename(x))
        return files
    return []

# Function to apply Butterworth high-pass filter
def butter_highpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    y = filtfilt(b, a, data)
    return y

# Function to apply thresholding
def apply_threshold(data, threshold):
    data[data > threshold] = 0
    data[data < -threshold] = 0
    return data

# Specify the paths to polar_data directory
polar_data_dir = 'polar_data'

# Get sorted list of filenames from polar_ECG directory
ecg_dir = os.path.join(polar_data_dir, 'polar_ECG')
ecg_files = get_sorted_files(ecg_dir)

# Get sorted list of filenames from polar_PPG directory
ppg_dir = os.path.join(polar_data_dir, 'polar_PPG')
ppg_files = get_sorted_files(ppg_dir)

# Determine the maximum length between ecg_files and ppg_files
max_length = max(len(ecg_files), len(ppg_files))

merged_dataframe_to_save = pd.DataFrame(columns=generate_column_names(ECG_WINDOW, PPG_WINDOW))

# Iterate through both lists simultaneously
for i in range(max_length):

    ################## ECG ##################

    ECG_data = pd.read_csv(f"polar_data/polar_ECG/{ecg_files[i]}", delimiter=";")

    ECG_data = ECG_data.drop(columns=["sensor timestamp [ns]", "timestamp [ms]"])

    ECG_data['Phone timestamp'] = pd.to_datetime(ECG_data['Phone timestamp'], format='%Y-%m-%dT%H:%M:%S.%f')

    # Apply high-pass filter to entire ECG data
    fs_ecg = 130  # Sampling frequency for ECG (Hz)
    cutoff_ecg = CUTOFF_FREQ  # High cutoff frequency for ECG (Hz)
    ECG_data['filtered_ecg'] = butter_highpass_filter(ECG_data['ecg [uV]'], cutoff_ecg, fs_ecg)

    # Extract window from filtered ECG data
    cut_ECG_data = int(ECG_PERCEMTAGE_START * len(ECG_data))
    start_index_ECG = cut_ECG_data
    end_index_ECG = start_index_ECG + ECG_WINDOW
    end_index_ECG = min(end_index_ECG, len(ECG_data))
    ECG_data_window = ECG_data.iloc[start_index_ECG:end_index_ECG]

    ################## PPG ##################
    
    PPG_data = repair_PPG(f"polar_data/polar_PPG/{ppg_files[i]}")
    PPG_data = PPG_data[PPG_data['Phone timestamp'] >= ECG_data_window.iloc[0]["Phone timestamp"]]
    PPG_data_window = PPG_data.head(PPG_WINDOW)
    # main_channel_mean = PPG_data_window['main_channel'].mean()
    # PPG_data_window.loc[:, 'main_channel'] = (PPG_data_window['main_channel'] - main_channel_mean) / 1000
    # PPG_data_window.loc[:, 'main_channel'] = (PPG_data_window['main_channel']) / 100

    # Apply high-pass filter to entire PPG data
    fs_ppg = 55  # Sampling frequency for PPG (Hz)
    cutoff_ppg = CUTOFF_FREQ  # High cutoff frequency for PPG (Hz)
    PPG_data['filtered_main_channel'] = butter_highpass_filter(PPG_data['main_channel'], cutoff_ppg, fs_ppg)

    # Extract window from filtered PPG data
    PPG_data_window = PPG_data.head(PPG_WINDOW)

    # # Apply thresholding to PPG data window
    # threshold_ppg = 600
    # PPG_data_window['filtered_main_channel'] = apply_threshold(PPG_data_window['filtered_main_channel'], threshold_ppg)

    ################## MODIFY DATA ##################

    ECG_data_window = ECG_data_window.drop(columns=["Phone timestamp", "ecg [uV]"])
    ECG_data_window = ECG_data_window.transpose()
    ECG_column_names = [f"ECG_{i+1}" for i in range(len(ECG_data_window.columns))]
    ECG_data_window.columns = ECG_column_names

    PPG_data_window = PPG_data_window.drop(columns=["Phone timestamp", "main_channel"])
    PPG_data_window = PPG_data_window.transpose()
    PPG_column_names = [f"PPG_{i+1}" for i in range(len(PPG_data_window.columns))]
    PPG_data_window.columns = PPG_column_names

    ################## CREATE DATAFRAME ROW ##################
    merged_df_row = pd.DataFrame({**ECG_data_window.iloc[0].to_dict(), **PPG_data_window.iloc[0].to_dict()}, index=[0])
    merged_df_row.insert(0, 'Filename', ecg_files[i][:-8])
    merged_df_row.reset_index(drop=True, inplace=True)
    merged_dataframe_to_save = pd.concat([merged_dataframe_to_save, pd.DataFrame([merged_df_row.iloc[0]])], ignore_index=True)

merged_dataframe_to_save.to_csv("merged_data.csv")

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

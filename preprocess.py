import os
import pandas as pd
from datetime import datetime
import re

ECG_PERCEMTAGE_START = 0.5
ECG_WINDOW = 130 * 4
PPG_WINDOW = 55 * 4

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

    df['mean_channel'] = df[['channel 0', 'channel 1', 'channel 2', 'ambient']].mean(axis=1)
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

    ECG_data = ECG_data.drop(columns=["sensor timestamp [ns]",	"timestamp [ms]"])

    ECG_data['Phone timestamp'] = pd.to_datetime(ECG_data['Phone timestamp'], format='%Y-%m-%dT%H:%M:%S.%f')

    cut_ECG_data = int(ECG_PERCEMTAGE_START * len(ECG_data))
    start_index_ECG = cut_ECG_data
    end_index_ECG  = start_index_ECG + ECG_WINDOW
    end_index_ECG  = min(end_index_ECG , len(ECG_data))
    ECG_data_window = ECG_data.iloc[start_index_ECG:end_index_ECG]
    mean_channel_mean = ECG_data_window['ecg [uV]'].mean()
    ECG_data_window.loc[:, 'ecg [uV]'] = (ECG_data_window['ecg [uV]'] - mean_channel_mean).astype('int64')
    # ECG_data_window.loc[:, 'ecg [uV]'] = ECG_data_window['ecg [uV]'].round(3)

    ################## PPG ##################
    
    PPG_data = repair_PPG(f"polar_data/polar_PPG/{ppg_files[i]}")
    PPG_data = PPG_data[PPG_data['Phone timestamp'] >=  ECG_data_window.iloc[0]["Phone timestamp"]]
    PPG_data_window = PPG_data.head(PPG_WINDOW)
    mean_channel_mean = PPG_data_window['mean_channel'].mean()
    PPG_data_window.loc[:, 'mean_channel'] = (PPG_data_window['mean_channel'] - mean_channel_mean) / 1000
    PPG_data_window.loc[:, 'mean_channel'] = PPG_data_window['mean_channel'].round(3)


    ################## MODIFY DATA ##################

    ECG_data_window = ECG_data_window.drop(columns=["Phone timestamp"])
    ECG_data_window = ECG_data_window.transpose()
    ECG_column_names = [f"ECG_{i+1}" for i in range(len(ECG_data_window.columns))]
    ECG_data_window.columns = ECG_column_names

    PPG_data_window = PPG_data_window.drop(columns=["Phone timestamp"])
    PPG_data_window = PPG_data_window.transpose()
    PPG_column_names = [f"PPG_{i+1}" for i in range(len(PPG_data_window.columns))]
    PPG_data_window.columns = PPG_column_names

    ################## CREATE DATAFRAME ROW ##################
    merged_df_row = pd.DataFrame({**ECG_data_window.iloc[0].to_dict(), **PPG_data_window.iloc[0].to_dict()}, index=[0])
    merged_df_row.insert(0, 'Filename', ecg_files[i][:-8])
    merged_df_row.reset_index(drop=True, inplace=True)
    # break
    merged_dataframe_to_save = pd.concat([merged_dataframe_to_save, pd.DataFrame([merged_df_row.iloc[0]])], ignore_index=True)

merged_dataframe_to_save.to_csv("merged_data.csv")



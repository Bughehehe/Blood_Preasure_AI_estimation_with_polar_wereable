import pandas as pd

# Specify the path to your text file
file_path = 'polar3/Polar_H10_83A00120_20240425_222850_ECG.txt'

# Define the column names based on your file format
columns = ['Phone timestamp', 'sensor timestamp [ns]', 'timestamp [ms]', 'ecg [uV]']

# Read the file into a pandas DataFrame
df = pd.read_csv(file_path, sep=';', header=0, names=columns)

# Convert 'Phone timestamp' column to datetime type
df['Phone timestamp'] = pd.to_datetime(df['Phone timestamp'])

# Calculate time differences in seconds between consecutive timestamps
df['Phone Time Difference (s)'] = (df['Phone timestamp'] - df['Phone timestamp'].shift()).dt.total_seconds()
df['Sensor Time Difference (s)'] = (df['sensor timestamp [ns]'] - df['sensor timestamp [ns]'].shift()) / 1e9
df['Timestamp Time Difference (s)'] = (df['timestamp [ms]'] - df['timestamp [ms]'].shift()) / 1000.0

# Calculate frequencies (reciprocal of time differences)
df['Phone Frequency (Hz)'] = 1 / df['Phone Time Difference (s)']
df['Sensor Frequency (Hz)'] = 1 / df['Sensor Time Difference (s)']
df['Timestamp Frequency (Hz)'] = 1 / df['Timestamp Time Difference (s)']

# Calculate mean frequencies
mean_phone_freq = df['Phone Frequency (Hz)'].mean()
mean_sensor_freq = df['Sensor Frequency (Hz)'].mean()
mean_timestamp_freq = df['Timestamp Frequency (Hz)'].mean()

# Print the mean frequencies
print(f"Mean Phone Timestamp Frequency: {mean_phone_freq:.2f} Hz")
print(f"Mean Sensor Timestamp Frequency: {mean_sensor_freq:.2f} Hz")
print(f"Mean Timestamp Frequency: {mean_timestamp_freq:.2f} Hz")
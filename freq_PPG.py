import pandas as pd

# Path to your text file
file_path = 'polar3/Polar_Sense_9F124324_20240425_222851_PPG_fixed.txt'

# Read the data into a DataFrame
df = pd.read_csv(file_path, delimiter=';', parse_dates=['Phone timestamp'])

# Sort DataFrame by Phone timestamp (if not already sorted)
df.sort_values('Phone timestamp', inplace=True)

# Convert sensor timestamp [ns] to nanoseconds
df['sensor timestamp [ns]'] = pd.to_numeric(df['sensor timestamp [ns]'], errors='coerce')

# Calculate time differences in seconds between Phone timestamp and sensor timestamp
time_diffs_phone = df['Phone timestamp'].diff().dt.total_seconds()
time_diffs_sensor = pd.to_timedelta(df['sensor timestamp [ns]'] - df['sensor timestamp [ns]'].shift()).dt.total_seconds()

# Calculate mean frequency (Hz) based on Phone timestamp
mean_frequency_phone = 1 / time_diffs_phone.mean()

# Calculate mean frequency (Hz) based on sensor timestamp
mean_frequency_sensor = 1 / time_diffs_sensor.mean()

print(f"Mean Frequency (Phone timestamp): {mean_frequency_phone:.2f} Hz")
print(f"Mean Frequency (Sensor timestamp): {mean_frequency_sensor:.2f} Hz")

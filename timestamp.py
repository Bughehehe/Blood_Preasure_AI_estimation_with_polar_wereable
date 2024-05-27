import datetime

# Given timestamp in nanoseconds
timestamp_ns = 599616197116737804

# Convert nanoseconds to seconds
timestamp_s = timestamp_ns / 1_000_000_000

# Define the epoch: January 1, 1989
epoch = datetime.datetime(1989, 1, 1)

# Calculate the final date and time
date_time = epoch + datetime.timedelta(seconds=timestamp_s)

print(date_time)
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime
from collections import defaultdict
import os

def parse_file(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                print(line.strip())
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

def find_word_in_file(file_path, word):
    timestamps = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if word in line:
                    print(f"Found word '{word}' in line: {line.strip()}")  # Log the line where the word is found
                    # Extract timestamp from the beginning of the line
                    timestamp_str = line.split()[0] + ' ' + line.split()[1]
                    # Convert timestamp to datetime object
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    timestamps.append(timestamp)
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return timestamps

def aggregate_timestamps_per_second(timestamps):
    aggregated = defaultdict(int)
    for timestamp in timestamps:
        # Round down to the nearest second
        rounded_timestamp = timestamp.replace(microsecond=0)
        aggregated[rounded_timestamp] += 1
    return aggregated

def plot_fail_timestamps(aggregated_timestamps, color, label):
    if not aggregated_timestamps:
        print(f"No timestamps to plot for {label}.")
        return
    times = list(aggregated_timestamps.keys())
    counts = list(aggregated_timestamps.values())
    plt.plot(times, counts, 'o', color=color, label=label)  # Plot dots for each timestamp

def process_folder(folder_path, word):
    all_timestamps = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # Process only .txt files
        if os.path.isfile(file_path) and file_path.endswith('.txt'):
            print(f"Processing file: {file_path}")  # Log which file is being processed
            timestamps = find_word_in_file(file_path, word)
            all_timestamps.extend(timestamps)
        else:
            print(f"Skipping non-text file: {file_path}")  # Log if non-text file is encountered
    return all_timestamps

if __name__ == "__main__":
    base_folder_path = 'C:\\Users\\abarnes\\Documents\\CustomerArea\\Facebook\\logdog'
    subfolders = ['p10752', 'p10753']
    colors = ['red', 'green']
    word = 'fail'
    
    plt.figure(figsize=(10, 6))
    
    for subfolder, color in zip(subfolders, colors):
        folder_path = os.path.join(base_folder_path, subfolder)
        print(f"\nProcessing all files in folder: {folder_path}")
        all_fail_timestamps = process_folder(folder_path, word)
        
        print(f"Found {len(all_fail_timestamps)} timestamps in {subfolder}.")  # Log the total number of timestamps found
        if all_fail_timestamps:
            aggregated_timestamps = aggregate_timestamps_per_second(all_fail_timestamps)
            print(f"Aggregated Timestamps for {subfolder}: {aggregated_timestamps}")  # Log the aggregated timestamps
            plot_fail_timestamps(aggregated_timestamps, color, subfolder)
        else:
            print(f"No timestamps found for the word 'fail' in {subfolder}.")
    
    plt.xlabel('Timestamp')
    plt.ylabel('Occurrences')
    plt.title('Occurrences of the word "fail" over time')
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))  # Format x-axis to show date and time
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    # Set x-axis limits
    start_time = datetime.strptime('2025-03-03 02:26', '%Y-%m-%d %H:%M')
    end_time = datetime.strptime('2025-03-03 02:28', '%Y-%m-%d %H:%M')
    #plt.xlim(left=start_time, right=end_time)
    plt.legend()
    plt.show()




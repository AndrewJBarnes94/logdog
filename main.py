import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime
from collections import defaultdict
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from Evtx.Evtx import Evtx
from Evtx.Views import evtx_file_xml_view

def find_word_in_file(file_path, word):
    print(f"Processing text file: {file_path}")
    timestamps = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if word in line:
                    print(f"Found '{word}' in line: {line.strip()}")
                    timestamp_str = line.split()[0] + ' ' + line.split()[1]
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    timestamps.append(timestamp)
    except FileNotFoundError:
        print(f"ERROR: File not found - {file_path}")
    except Exception as e:
        print(f"ERROR: {e}")
    return timestamps

def find_errors_in_evtx(file_path):
    print(f"Processing EVTX file: {file_path}")
    timestamps = []
    record_count = 0
    error_count = 0
    max_records = 10000  # Set a limit to prevent excessive processing

    try:
        with Evtx(file_path) as log:
            for record in log.records():
                record_count += 1
                
                # Only process logs with <Level>2</Level> (Error logs)
                xml = record.xml()
                if "<Level>2</Level>" not in xml:
                    continue  # Skip non-error logs

                error_count += 1
                timestamp_str = record.timestamp().isoformat()
                print(f"[ERROR] Log #{error_count}: {timestamp_str}")

                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
                    timestamps.append(timestamp)
                except ValueError:
                    print(f"Skipping invalid timestamp format: {timestamp_str}")

                # Print progress every 1000 records processed
                if record_count % 1000 == 0:
                    print(f"Processed {record_count} total logs, {error_count} errors found.")

                # Stop processing if we hit max_records
                if record_count >= max_records:
                    print(f"Reached max record limit of {max_records}. Stopping early.")
                    break

    except FileNotFoundError:
        print(f"ERROR: File not found - {file_path}")
    except Exception as e:
        print(f"ERROR processing EVTX: {e}")

    print(f"Finished processing {record_count} records, {error_count} errors extracted from {file_path}")
    return timestamps

def aggregate_timestamps_per_second(timestamps):
    print(f"Aggregating {len(timestamps)} timestamps...")
    aggregated = defaultdict(int)
    for timestamp in timestamps:
        rounded_timestamp = timestamp.replace(microsecond=0)
        aggregated[rounded_timestamp] += 1
    return aggregated

def plot_fail_timestamps(aggregated_timestamps, color, label):
    print(f"Plotting {len(aggregated_timestamps)} points for {label}")
    if not aggregated_timestamps:
        print(f"WARNING: No timestamps to plot for {label}.")
        return
    times = list(aggregated_timestamps.keys())
    counts = list(aggregated_timestamps.values())
    plt.plot(times, counts, 'o', color=color, label=label)

def process_folder(folder_path, word, progress_var, total_files, processed_files):
    print(f"Scanning folder: {folder_path}")
    all_timestamps = []
    files = os.listdir(folder_path)
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            if file_path.lower().endswith('.txt'):
                timestamps = find_word_in_file(file_path, word)
            elif file_path.lower().endswith('.evtx'):
                timestamps = find_errors_in_evtx(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path}")
                continue
            all_timestamps.extend(timestamps)
        processed_files += 1
        progress_var.set(processed_files / total_files * 100)
        root.update_idletasks()
    return all_timestamps, processed_files

def plot_data(folders, word, progress_var):
    print("Starting plot data process...")
    plt.figure(figsize=(10, 6))
    
    total_files = sum(len(os.listdir(folder_path)) for folder_path, _, _ in folders)
    print(f"Total files to process: {total_files}")
    processed_files = 0
    
    for folder_info in folders:
        folder_path, color, label = folder_info
        print(f"Processing folder: {folder_path}")
        all_fail_timestamps, processed_files = process_folder(folder_path, word, progress_var, total_files, processed_files)
        
        if all_fail_timestamps:
            aggregated_timestamps = aggregate_timestamps_per_second(all_fail_timestamps)
            plot_fail_timestamps(aggregated_timestamps, color, label)
    
    plt.xlabel('Timestamp')
    plt.ylabel('Occurrences')
    plt.title('Occurrences over time')
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.show()
    print("Plot completed.")

def browse_folder():
    folder_selected = filedialog.askdirectory()
    folder_path_var.set(folder_selected)
    print(f"Selected folder: {folder_selected}")

def add_folder():
    folder_path = folder_path_var.get()
    color = color_var.get()
    label = label_var.get()
    
    if not folder_path or not color or not label:
        messagebox.showerror("Error", "Please fill in all fields for the folder.")
        return
    
    folders.append((folder_path, color, label))
    folder_listbox.insert(tk.END, f"{label} ({color}): {folder_path}")
    print(f"Added folder: {folder_path} (Label: {label}, Color: {color})")
    folder_path_var.set("")
    color_var.set("")
    label_var.set("")

def plot_button_clicked():
    word = word_var.get()
    
    if not folders or not word:
        messagebox.showerror("Error", "Please fill in all fields.")
        return
    
    progress_var.set(0)
    print(f"Starting plot with word: {word}")
    plot_data(folders, word, progress_var)

# Create the main window
root = tk.Tk()
root.title("Log File Plotter")

folders = []

# UI Components
tk.Label(root, text="Folder Path:").grid(row=0, column=0, sticky=tk.W)
folder_path_var = tk.StringVar()
tk.Entry(root, textvariable=folder_path_var, width=50).grid(row=0, column=1)
tk.Button(root, text="Browse", command=browse_folder).grid(row=0, column=2)

tk.Label(root, text="Color:").grid(row=1, column=0, sticky=tk.W)
color_var = tk.StringVar()
tk.Entry(root, textvariable=color_var, width=50).grid(row=1, column=1)

tk.Label(root, text="Label:").grid(row=2, column=0, sticky=tk.W)
label_var = tk.StringVar()
tk.Entry(root, textvariable=label_var, width=50).grid(row=2, column=1)

tk.Button(root, text="Add Folder", command=add_folder).grid(row=3, column=1)

folder_listbox = tk.Listbox(root, width=80, height=10)
folder_listbox.grid(row=4, column=0, columnspan=3)

tk.Label(root, text="Word to Search (for text files):").grid(row=5, column=0, sticky=tk.W)
word_var = tk.StringVar()
tk.Entry(root, textvariable=word_var, width=50).grid(row=5, column=1)

tk.Button(root, text="Plot", command=plot_button_clicked).grid(row=6, column=1)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=7, column=0, columnspan=3, sticky=tk.W+tk.E)

# Run the main loop
print("Starting GUI...")
root.mainloop()

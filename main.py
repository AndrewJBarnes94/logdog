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
import mplcursors

def find_phrases_in_file(file_path, phrases):
    print(f"Processing text file: {file_path}")
    timestamps = []
    lines = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if any(phrase in line for phrase in phrases):
                    print(f"Found one of {phrases} in line: {line.strip()}")
                    timestamp_str = line.split()[0] + ' ' + line.split()[1]
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    timestamps.append(timestamp)
                    lines.append(line.strip())
    except FileNotFoundError:
        print(f"ERROR: File not found - {file_path}")
    except Exception as e:
        print(f"ERROR: {e}")
    return timestamps, lines

def find_errors_in_evtx(file_path):
    print(f"Processing EVTX file: {file_path}")
    timestamps = []
    lines = []
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
                    lines.append(xml)
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
    return timestamps, lines

def plot_fail_timestamps(ax, timestamps, lines, color, label, visible=True):
    print(f"Plotting {len(timestamps)} points for {label}")
    if not timestamps:
        print(f"WARNING: No timestamps to plot for {label}.")
        return
    times = timestamps
    counts = [1] * len(timestamps)  # Set the value to 1 for each timestamp
    scatter = ax.scatter(times, counts, color=color, label=label, visible=visible)
    cursor = mplcursors.cursor(scatter)
    cursor.connect("add", lambda sel: update_text_area(lines[sel.index]))
    return scatter

def update_text_area(text):
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, text)
    text_area.config(state=tk.DISABLED)

def process_folder(folder_path, phrases, progress_var, total_files, processed_files):
    print(f"Scanning folder: {folder_path}")
    all_timestamps = []
    all_lines = []
    files = os.listdir(folder_path)
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            if file_path.lower().endswith('.txt'):
                timestamps, lines = find_phrases_in_file(file_path, phrases)
            elif file_path.lower().endswith('.evtx'):
                timestamps, lines = find_errors_in_evtx(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path}")
                continue
            all_timestamps.extend(timestamps)
            all_lines.extend(lines)
        processed_files += 1
        progress_var.set(processed_files / total_files * 100)
        root.update_idletasks()
    return all_timestamps, all_lines, processed_files

def plot_data(folders, phrases, progress_var):
    print("Starting plot data process...")
    global fig, ax, scatters
    fig, ax = plt.subplots(figsize=(10, 6))
    
    total_files = sum(len(os.listdir(folder_path)) for folder_path, _, _ in folders)
    print(f"Total files to process: {total_files}")
    processed_files = 0
    scatters = []
    
    for folder_info in folders:
        folder_path, color, label = folder_info
        print(f"Processing folder: {folder_path}")
        all_fail_timestamps, all_lines, processed_files = process_folder(folder_path, phrases, progress_var, total_files, processed_files)
        
        if all_fail_timestamps:
            scatter = plot_fail_timestamps(ax, all_fail_timestamps, all_lines, color, label)
            scatters.append((label, scatter))
    
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Occurrences')
    ax.set_ylim(0, 2)  # Set y-axis limits to [0, 2]
    ax.set_title(f"Occurrences of {'; '.join(phrases)} over time")
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.show()
    print("Plot completed.")

def toggle_visibility(label):
    for lbl, scatter in scatters:
        if lbl == label:
            scatter.set_visible(not scatter.get_visible())
    plt.draw()

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
    
    # Add a checkbox for showing/hiding the dataset
    var = tk.BooleanVar(value=True)
    checkbox = tk.Checkbutton(root, text=label, variable=var, command=lambda: toggle_visibility(label))
    checkbox.grid(row=9 + len(folders), column=0, sticky=tk.W)
    checkboxes.append(checkbox)

def plot_button_clicked():
    phrases = [phrase.strip() for phrase in phrase_var.get().split('","')]
    
    if not folders or not phrases:
        messagebox.showerror("Error", "Please fill in all fields.")
        return
    
    progress_var.set(0)
    print(f"Starting plot with phrases: {phrases}")
    plot_data(folders, phrases, progress_var)

# Create the main window
root = tk.Tk()
root.title("Log Dog")
root.geometry("800x600")

folders = []
checkboxes = []

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

tk.Label(root, text="Phrases to Search (comma-separated):").grid(row=5, column=0, sticky=tk.W)
phrase_var = tk.StringVar()
tk.Entry(root, textvariable=phrase_var, width=50).grid(row=5, column=1)

tk.Button(root, text="Plot", command=plot_button_clicked).grid(row=6, column=1)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=7, column=0, columnspan=3, sticky=tk.W+tk.E)

# Text area for displaying information
text_area = tk.Text(root, height=10, width=80, state=tk.DISABLED)
text_area.grid(row=8, column=0, columnspan=3, pady=10)

# Run the main loop
print("Starting GUI...")
root.mainloop()







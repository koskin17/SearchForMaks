import os
import py7zr
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

def search_text_in_edz(archive_path, search_text, progress_bar):
    if not os.path.exists(archive_path):
        return []

    found_files = []
    with py7zr.SevenZipFile(archive_path, mode='r') as zip_ref:
        total_files = len(zip_ref.getnames())
        progress = 0
        for file_info in zip_ref.getnames():
            content = zip_ref.read(file_info)
            if search_text.encode() in content:
                found_files.append(file_info)
            progress += 1
            progress_bar['value'] = int((progress / total_files) * 100)
            progress_bar.update()
    return found_files

def search_in_selected_directory():
    directory = filedialog.askdirectory()
    if directory:
        search_text = entry.get()
        result_text.delete(1.0, tk.END)
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.7z'):
                    archive_path = os.path.join(root, file)
                    found_files = search_text_in_edz(archive_path, search_text, progress_bar)
                    if found_files:
                        result_text.insert(tk.END, f'Found in {archive_path}:\n')
                        for found_file in found_files:
                            result_text.insert(tk.END, f'{found_file}\n')
                        result_text.insert(tk.END, '\n')

root = tk.Tk()
root.title("EDZ Archive Text Search")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Enter text to search:")
label.grid(row=0, column=0, sticky="w")

entry = tk.Entry(frame)
entry.grid(row=0, column=1, padx=5)

search_button = tk.Button(frame, text="Select Directory", command=search_in_selected_directory)
search_button.grid(row=1, columnspan=2, pady=5)

progress_frame = tk.Frame(root)
progress_frame.pack(padx=10, pady=5)

progress_label = tk.Label(progress_frame, text="Progress:")
progress_label.grid(row=0, column=0, sticky="w")

progress_bar = ttk.Progressbar(progress_frame, length=200, mode="determinate")
progress_bar.grid(row=0, column=1, padx=5)

result_text = tk.Text(root, width=50, height=20)
result_text.pack(pady=5)

root.mainloop()

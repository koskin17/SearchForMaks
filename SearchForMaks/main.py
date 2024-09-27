import os
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter.ttk import Progressbar
import py7zr
import re
from function import unzip_target_arc


folder_with_temp_files = ''

class TextSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск текста в XML файлах внутри архивов EDZ")

        """Field for inout text for search"""
        self.search_label = tk.Label(root, text="Введите текст для поиска:")
        self.search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)

        """Button for insert text from clipboard"""
        self.paste_button = tk.Button(root, text="Вставить из буфера", command=self.paste_from_clipboard)
        self.paste_button.grid(row=0, column=2, padx=5, pady=5)

        """Button for select the folder"""
        self.folder_label = tk.Label(root, text="Выберите папку:")
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.folder_entry = tk.Entry(root, width=50)
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(root, text="Обзор", command=self.browse_folder)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        """Button for start searching"""
        self.search_button = tk.Button(root, text="Поиск", command=self.search_text_in_edz_files)
        self.search_button.grid(row=2, column=1, padx=5, pady=5)

        """"Progress bar"""
        self.progress = Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.grid(row=3, column=1, padx=5, pady=5)

        """Window for displaing the results of search"""
        self.results = scrolledtext.ScrolledText(root, width=80, height=20)
        self.results.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_path)

    def paste_from_clipboard(self):
        """Method for paste text from clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()  # getting text fron clipboard
            self.search_entry.delete(0, tk.END)  # clearing the field
            self.search_entry.insert(0, clipboard_text)  # paste text from clipboard
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

    def search_text_in_edz_files(self):
        """Search the input text in EDZ files"""
        folder_path = self.folder_entry.get()
        search_text = self.search_entry.get()

        if not folder_path or not search_text:
            messagebox.showerror("Ошибка", "Пожалуйста, введите текст для поиска и выберите папку.")
            return

        # clearing the previous results
        self.results.delete(1.0, tk.END)

        # counting the number of .edz archives
        edz_files = [f for f in os.listdir(folder_path) if f.endswith('.edz')]
        total_files = len(edz_files)

        if total_files == 0:
            messagebox.showinfo("Результат", "В выбранной папке нет файлов формата .edz.")
            return

        # start searching with progress-bar
        self.progress['value'] = 0
        self.progress['maximum'] = total_files

        for idx, edz_file in enumerate(edz_files):
            edz_path = os.path.join(folder_path, edz_file)
            found_block = self.search_in_edz(edz_path, search_text)
            self.progress['value'] += 1
            self.root.update_idletasks()  # update interface for displaing the progress

            if found_block:
                # saving the found block in an XML file and pack it into an .edz archive
                self.save_to_edz_archive(search_text, found_block)

                self.results.insert(tk.END, f"Текст найден и сохранен в архиве {search_text}.edz из файла {edz_file}\n")
                # messagebox.showinfo("Результат", f"Текст найден и сохранен в архиве {search_text}.edz из файла {edz_file}")
                return  # stop searching after finding the text

        messagebox.showinfo("Результат", "Текст не найден ни в одном архиве.")
        self.results.insert(tk.END, "Текст не найден ни в одном архиве.\n")

    def search_in_edz(self, edz_path, search_text):
        global folder_with_temp_files
        
        try:
            with py7zr.SevenZipFile(edz_path, 'r') as archive:
                # getting all files from the archive
                extracted_files = archive.readall()
                
                for file_name, file_data in extracted_files.items():
                    if file_name.endswith('.xml'):
                        try:
                            # reading content of XML file
                            xml_content = file_data.read().decode('utf-8', errors='replace')  # Decoding with error replacement

                            # looking for a block between the tags <package> and </package> with the specified text
                            package_blocks = re.findall(r'(<package.*?>.*?</package>)', xml_content, re.DOTALL)
                            
                            for block in package_blocks:
                                if search_text in block:
                                    folder_with_temp_files = unzip_target_arc(edz_path, search_text)                                    
                                    
                                    return block  # return the text block if found and file name
                                
                        except Exception as e:
                            self.results.insert(tk.END, f"Ошибка разбора XML файла: {file_name}, ошибка: {e}\n")
        except Exception as e:
            self.results.insert(tk.END, f"Ошибка при работе с архивом {edz_path}: {e}\n")
        return None  # Return None if text not found
    
    def save_to_edz_archive(self, search_text, content):
        # prompt to user to select a folder to save the archive
        global folder_with_temp_files
        
        save_folder = filedialog.askdirectory(title="Выберите папку для сохранения архива")
        if not save_folder:
            messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
            return

        # path to save .edz archive
        archive_path = os.path.join(save_folder, f"{search_text}.edz")
        manifest_filename = "manifest.xml"

        # making the temp file manifest.xml
        manifest_path = os.path.join(save_folder, manifest_filename)
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # making archive EDZ with file manifest.xml
            with py7zr.SevenZipFile(archive_path, 'w') as archive:
                archive.write(manifest_path, manifest_filename)
                print(folder_with_temp_files) 
                archive.writeall('items/')

            # deleting temp file manifest.xml
            os.remove(manifest_path)
            shutil.rmtree('items')

            messagebox.showinfo("Результат", f"Архив сохранен: {archive_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании архива: {e}")



"""Start main programm"""
root = tk.Tk()
app = TextSearchApp(root)
root.mainloop()
print(folder_with_temp_files)

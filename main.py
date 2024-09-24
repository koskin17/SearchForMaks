import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter.ttk import Progressbar
import py7zr
import re

class TextSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск текста в XML файлах внутри архивов EDZ")

        # Поле для ввода текста
        self.search_label = tk.Label(root, text="Введите текст для поиска:")
        self.search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)    # positioning fied by grid

        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)

        # Кнопка для вставки текста из буфера обмена
        self.paste_button = tk.Button(root, text="Вставить из буфера", command=self.paste_from_clipboard)
        self.paste_button.grid(row=0, column=2, padx=5, pady=5)

        # Кнопка для выбора папки
        self.folder_label = tk.Label(root, text="Выберите папку:")
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.folder_entry = tk.Entry(root, width=50)
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(root, text="Обзор", command=self.browse_folder)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        # Кнопка для запуска поиска
        self.search_button = tk.Button(root, text="Поиск", command=self.search_text_in_edz_files)
        self.search_button.grid(row=2, column=1, padx=5, pady=5)

        # Прогресс-бар
        self.progress = Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.grid(row=3, column=1, padx=5, pady=5)

        # Окно для отображения результатов поиска
        self.results = scrolledtext.ScrolledText(root, width=80, height=20)
        self.results.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def browse_folder(self):
        """Method for displaing the window for selecting a folder"""
        folder_path = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_path)

    def paste_from_clipboard(self):
        """Method for paste text from clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()  # Получение текста из буфера обмена
            self.search_entry.delete(0, tk.END)  # Очищаем поле
            self.search_entry.insert(0, clipboard_text)  # Вставляем текст из буфера
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

    def search_text_in_edz_files(self):
        """"Method for getting text from input fields"""
        folder_path = self.folder_entry.get()
        search_text = self.search_entry.get()

        if not folder_path or not search_text:
            messagebox.showerror("Ошибка", "Пожалуйста, введите текст для поиска и выберите папку.")
            return

        """Clearing the previous results"""
        self.results.delete(1.0, tk.END)

        """Counting the number of .edz archives"""
        edz_files = [f for f in os.listdir(folder_path) if f.endswith('.edz')]
        total_files = len(edz_files)

        if total_files == 0:
            messagebox.showinfo("Результат", "В выбранной папке нет файлов формата .edz.")
            return

        """Starting search with progress-bar"""
        self.progress['value'] = 0
        self.progress['maximum'] = total_files

        for idx, edz_file in enumerate(edz_files):
            edz_path = os.path.join(folder_path, edz_file)
            found_block = self.search_in_edz(edz_path, search_text)
            self.progress['value'] += 1
            self.root.update_idletasks()  # Update interface for displaing progress

            if found_block:
                """Save founded blok of text in file"""
                self.save_to_file("manifest.xml", found_block, search_text)
                self.results.insert(tk.END, f"Текст найден и сохранен в файле {search_text}.xml из архива {edz_file}\n")
                
                return  # Stop searching text if it found

        # messagebox.showinfo("Результат", "Текст не найден ни в одном архиве.")
        self.results.insert(tk.END, "Текст не найден ни в одном архиве.\n")

    def search_in_edz(self, edz_path, search_text):
        """Method for searching input text in specified folder"""
        try:
            with py7zr.SevenZipFile(edz_path, 'r') as archive:
                """Getting list of all files in folder"""
                extracted_files = archive.readall()
                print(extracted_files)

                for file_name, file_data in extracted_files.items():
                    if file_name.endswith('.xml'):
                        try:
                            """Reading file XML"""
                            xml_content = file_data.read().decode('utf-8', errors='replace')  # Decoding with replacement errors

                            """Searching blok between tags <package> and <package> with input text""" 
                            package_blocks = re.findall(r'(<package.*?>.*?</package>)', xml_content, re.DOTALL)
                            for block in package_blocks:
                                if search_text in block:
                                    return block  # return block with text if it found
                        except Exception as e:
                            self.results.insert(tk.END, f"Ошибка разбора XML файла: {file_name}, ошибка: {e}\n")
        except Exception as e:
            self.results.insert(tk.END, f"Ошибка при работе с архивом {edz_path}: {e}\n")
        return None  # Return None, if text not found

    def save_to_file(self, filename, content, search_text):
        """Method for saving found text to file "filename".xml and add it to archive .edz"""
        
        folder_path = self.folder_entry.get()
        file_path = os.path.join(folder_path, filename)
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            with py7zr.SevenZipFile(f"{search_text}.edz", 'w') as archive:
                archive.write("manifest.xml")


            os.remove('manifest.xml')

            """Searching file with text in  name from search text"""
            with py7zr.SevenZipFile(folder_path, 'r') as archive:
                """Getting list of all files in folder"""
                extracted_files = archive.readall()
                print(extracted_files)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении файла: {e}")

# Запуск программы
root = tk.Tk()
app = TextSearchApp(root)
root.mainloop()

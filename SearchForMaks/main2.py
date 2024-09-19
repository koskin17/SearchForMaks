import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter.ttk import Progressbar
import py7zr
import xml.etree.ElementTree as ET
import re

class TextSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск текста в XML файлах внутри архивов EDZ")

        # Поле для ввода текста
        self.search_label = tk.Label(root, text="Введите текст для поиска:")
        self.search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

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
        folder_path = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_path)

    def paste_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get()  # Получение текста из буфера обмена
            self.search_entry.delete(0, tk.END)  # Очищаем поле
            self.search_entry.insert(0, clipboard_text)  # Вставляем текст из буфера
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

    def search_text_in_edz_files(self):
        folder_path = self.folder_entry.get()
        search_text = self.search_entry.get()

        if not folder_path or not search_text:
            messagebox.showerror("Ошибка", "Пожалуйста, введите текст для поиска и выберите папку.")
            return

        # Очищаем предыдущие результаты
        self.results.delete(1.0, tk.END)

        # Подсчитываем количество архивов .edz
        edz_files = [f for f in os.listdir(folder_path) if f.endswith('.edz')]
        total_files = len(edz_files)

        if total_files == 0:
            messagebox.showinfo("Результат", "В выбранной папке нет файлов формата .edz.")
            return

        # Начинаем поиск с прогресс-баром
        self.progress['value'] = 0
        self.progress['maximum'] = total_files

        for idx, edz_file in enumerate(edz_files):
            edz_path = os.path.join(folder_path, edz_file)
            found_block = self.search_in_edz(edz_path, search_text)
            self.progress['value'] += 1
            self.root.update_idletasks()  # Обновляем интерфейс для отображения прогресса

            if found_block:
                # Сохраняем найденный блок в файл
                self.save_to_file(search_text, found_block)
                self.results.insert(tk.END, f"Текст найден и сохранен в файле {search_text}.xml из архива {edz_file}\n")
                messagebox.showinfo("Результат", f"Текст найден и сохранен в файле {search_text}.xml из архива {edz_file}")
                return  # Прекращаем поиск после нахождения текста

        messagebox.showinfo("Результат", "Текст не найден ни в одном архиве.")
        self.results.insert(tk.END, "Текст не найден ни в одном архиве.\n")

    def search_in_edz(self, edz_path, search_text):
        try:
            with py7zr.SevenZipFile(edz_path, 'r') as archive:
                # Получаем все файлы из архива
                extracted_files = archive.readall()

                for file_name, file_data in extracted_files.items():
                    if file_name.endswith('.xml'):
                        try:
                            # Читаем содержимое XML файла
                            xml_content = file_data.read().decode('utf-8', errors='replace')  # Исправлено декодирование

                            # Добавляем отладочную информацию в лог
                            self.results.insert(tk.END, f"Проверка файла {file_name} из архива {edz_path}\n")

                            # Ищем блок между тегами <package> и </package>
                            package_block = re.search(r'(<package.*?>.*?</package>)', xml_content, re.DOTALL)
                            if package_block:
                                block_content = package_block.group(1)
                                if search_text in block_content:
                                    return block_content  # Возвращаем блок текста, если найден
                        except Exception as e:
                            self.results.insert(tk.END, f"Ошибка разбора XML файла: {file_name}, ошибка: {e}\n")
        except Exception as e:
            self.results.insert(tk.END, f"Ошибка при работе с архивом {edz_path}: {e}\n")
        return None  # Возвращаем None, если текст не найден

    def save_to_file(self, filename, content):
        folder_path = self.folder_entry.get()
        file_path = os.path.join(folder_path, f"{filename}.xml")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении файла: {e}")

# Запуск программы
root = tk.Tk()
app = TextSearchApp(root)
root.mainloop()

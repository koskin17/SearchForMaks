# Повна версія основної програми з:
# - оновленим прогресбаром, який заповнюється точно по ходу виконання
# - багатопотоковою обробкою архівів
# - індикатором статусу ("Идёт поиск..." / "Готово")

import os
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter.ttk import Progressbar
import py7zr
import re
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from function import unzip_target_arc


class TextSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск текста в XML файлах внутри архивов EDZ")

        self.search_label = tk.Label(root, text="Введите текст для поиска:")
        self.search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_entry.bind('<Control-Key>', self.handle_ctrl_shortcuts)

        self.paste_button = tk.Button(root, text="Вставить из буфера", command=self.paste_from_clipboard)
        self.paste_button.grid(row=0, column=2, padx=5, pady=5)

        self.folder_label = tk.Label(root, text="Выберите папку:")
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.folder_entry = tk.Entry(root, width=50)
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(root, text="Обзор", command=self.browse_folder)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        self.search_button = tk.Button(root, text="Поиск", command=self.start_search_thread)
        self.search_button.grid(row=2, column=1, padx=5, pady=5)

        self.status_label = tk.Label(root, text="Готово", fg="green")
        self.status_label.grid(row=3, column=0, padx=5, pady=5)

        self.progress = Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.grid(row=3, column=1, padx=5, pady=5)

        self.results = scrolledtext.ScrolledText(root, width=80, height=20)
        self.results.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        self.queue = Queue()
        self.root.after(100, self.process_queue)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_path)

    def paste_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get()
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, clipboard_text)
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

    def handle_ctrl_shortcuts(self, event):
        if event.state & 0x4 and event.keycode == 86:
            try:
                clipboard_text = self.root.clipboard_get()
                self.search_entry.delete(0, tk.END)
                self.search_entry.insert(0, clipboard_text)
                return "break"
            except tk.TclError:
                messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

    def start_search_thread(self):
        threading.Thread(target=self.search_text_in_edz_files, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                action = self.queue.get_nowait()
                action()
        except:
            pass
        self.root.after(100, self.process_queue)

    def search_text_in_edz_files(self):
        folder_path = self.folder_entry.get()
        search_text = self.search_entry.get()

        if not folder_path or not search_text:
            self.queue.put(lambda: messagebox.showerror("Ошибка", "Введите текст и выберите папку."))
            return

        self.queue.put(lambda: self.results.delete(1.0, tk.END))
        edz_files = [f for f in os.listdir(folder_path) if f.endswith('.edz')]
        total_files = len(edz_files)

        if total_files == 0:
            self.queue.put(lambda: messagebox.showinfo("Результат", "Файлы .edz не найдены."))
            return

        self.queue.put(lambda: self.progress.configure(value=0, maximum=total_files))
        self.queue.put(lambda: self.status_label.config(text="Идёт поиск...", fg="blue"))

        found_flag = threading.Event()

        def process_single_file(edz_file):
            if found_flag.is_set():
                return
            edz_path = os.path.join(folder_path, edz_file)
            temp_dir = tempfile.mkdtemp()
            found_block = self.search_in_edz(edz_path, search_text, temp_dir)
            if found_block and not found_flag.is_set():
                found_flag.set()
                self.queue.put(lambda: self.save_to_edz_archive(search_text, found_block, temp_dir))
                self.queue.put(lambda: self.results.insert(tk.END,
                    f"Текст найден и сохранен в архиве {search_text}.edz из файла {edz_file}\\n"))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_single_file, edz_file): edz_file for edz_file in edz_files}

            for idx, future in enumerate(as_completed(futures), 1):
                self.queue.put(lambda idx=idx: self.progress.configure(value=idx))

        self.queue.put(lambda: self.status_label.config(text="Готово", fg="green"))
        if not found_flag.is_set():
            self.queue.put(lambda: messagebox.showinfo("Результат", "Текст не найден."))
            self.queue.put(lambda: self.results.insert(tk.END, "Текст не найден ни в одном архиве.\\n"))

    def search_in_edz(self, edz_path, search_text, temp_dir):
        try:
            with py7zr.SevenZipFile(edz_path, 'r') as archive:
                extracted_files = archive.readall()
                for file_name, file_data in extracted_files.items():
                    if file_name.endswith('.xml'):
                        try:
                            xml_content = file_data.read().decode('utf-8', errors='replace')
                            blocks = re.findall(r'(<package.*?>.*?</package>)', xml_content, re.DOTALL)
                            for block in blocks:
                                if search_text in block:
                                    unzip_target_arc(edz_path, search_text, temp_dir)
                                    return block
                        except:
                            pass
        except:
            pass
        return None

    def save_to_edz_archive(self, search_text, content, temp_dir):
        save_folder = filedialog.askdirectory(title="Выберите папку для сохранения архива")
        if not save_folder:
            messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
            return

        archive_path = os.path.join(save_folder, f"{search_text}.edz")
        manifest_filename = "manifest.xml"
        manifest_path = os.path.join(temp_dir, manifest_filename)

        try:
            wrapped_content = f'''<manifest version="2.0">
    <packages>
        {content}
    </packages>
</manifest>'''

            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(wrapped_content)

            with py7zr.SevenZipFile(archive_path, 'w') as archive:
                for root_dir, _, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root_dir, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        archive.write(full_path, rel_path)

            shutil.rmtree(temp_dir, ignore_errors=True)
            messagebox.showinfo("Результат", f"Архив сохранен: {archive_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании архива: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TextSearchApp(root)
    root.mainloop()


# # Ми виконаємо два оновлення:
# # 1. Додамо індикатор статусу ("Идёт поиск..." / "Готово")
# # 2. Обробку кількох архівів зробимо паралельно з ThreadPoolExecutor

# import os
# import shutil
# import tempfile
# import threading
# import tkinter as tk
# from tkinter import filedialog, scrolledtext, messagebox
# from tkinter.ttk import Progressbar
# import py7zr
# import re
# from queue import Queue
# from concurrent.futures import ThreadPoolExecutor
# from function import unzip_target_arc
# from concurrent.futures import ThreadPoolExecutor, as_completed

# class TextSearchApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Поиск текста в XML файлах внутри архивов EDZ")

#         self.search_label = tk.Label(root, text="Введите текст для поиска:")
#         self.search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

#         self.search_entry = tk.Entry(root, width=50)
#         self.search_entry.grid(row=0, column=1, padx=5, pady=5)
#         self.search_entry.bind('<Control-Key>', self.handle_ctrl_shortcuts)

#         self.paste_button = tk.Button(root, text="Вставить из буфера", command=self.paste_from_clipboard)
#         self.paste_button.grid(row=0, column=2, padx=5, pady=5)

#         self.folder_label = tk.Label(root, text="Выберите папку:")
#         self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

#         self.folder_entry = tk.Entry(root, width=50)
#         self.folder_entry.grid(row=1, column=1, padx=5, pady=5)

#         self.browse_button = tk.Button(root, text="Обзор", command=self.browse_folder)
#         self.browse_button.grid(row=1, column=2, padx=5, pady=5)

#         self.search_button = tk.Button(root, text="Поиск", command=self.start_search_thread)
#         self.search_button.grid(row=2, column=1, padx=5, pady=5)

#         self.status_label = tk.Label(root, text="Готово", fg="green")
#         self.status_label.grid(row=3, column=0, padx=5, pady=5)

#         self.progress = Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
#         self.progress.grid(row=3, column=1, padx=5, pady=5)

#         self.results = scrolledtext.ScrolledText(root, width=80, height=20)
#         self.results.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

#         self.queue = Queue()
#         self.root.after(100, self.process_queue)

#     def browse_folder(self):
#         folder_path = filedialog.askdirectory()
#         self.folder_entry.delete(0, tk.END)
#         self.folder_entry.insert(0, folder_path)

#     def paste_from_clipboard(self):
#         try:
#             clipboard_text = self.root.clipboard_get()
#             self.search_entry.delete(0, tk.END)
#             self.search_entry.insert(0, clipboard_text)
#         except tk.TclError:
#             messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

#     def handle_ctrl_shortcuts(self, event):
#         if event.state & 0x4 and event.keycode == 86:
#             try:
#                 clipboard_text = self.root.clipboard_get()
#                 self.search_entry.delete(0, tk.END)
#                 self.search_entry.insert(0, clipboard_text)
#                 return "break"
#             except tk.TclError:
#                 messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

#     def start_search_thread(self):
#         threading.Thread(target=self.search_text_in_edz_files, daemon=True).start()

#     def process_queue(self):
#         try:
#             while True:
#                 action = self.queue.get_nowait()
#                 action()
#         except:
#             pass
#         self.root.after(100, self.process_queue)

#     def search_text_in_edz_files(self):
#         folder_path = self.folder_entry.get()
#         search_text = self.search_entry.get()

#         if not folder_path or not search_text:
#             self.queue.put(lambda: messagebox.showerror("Ошибка", "Введите текст и выберите папку."))
#             return

#         self.queue.put(lambda: self.results.delete(1.0, tk.END))
#         edz_files = [f for f in os.listdir(folder_path) if f.endswith('.edz')]
#         total_files = len(edz_files)

#         if total_files == 0:
#             self.queue.put(lambda: messagebox.showinfo("Результат", "Файлы .edz не найдены."))
#             return

#         self.queue.put(lambda: self.progress.configure(value=0, maximum=total_files))
#         self.queue.put(lambda: self.status_label.config(text="Идёт поиск...", fg="blue"))

#         found_flag = threading.Event()

#         def process_single_file(edz_file):
#             if found_flag.is_set():
#                 return
#             edz_path = os.path.join(folder_path, edz_file)
#             temp_dir = tempfile.mkdtemp()
#             found_block = self.search_in_edz(edz_path, search_text, temp_dir)
#             self.queue.put(lambda edz_file=edz_file: self.progress.step(1))

#             if found_block and not found_flag.is_set():
#                 found_flag.set()
#                 self.queue.put(lambda: self.save_to_edz_archive(search_text, found_block, temp_dir))
#                 self.queue.put(lambda: self.results.insert(tk.END,
#                     f"Текст найден и сохранен в архиве {search_text}.edz из файла {edz_file}\\n"))

#         with ThreadPoolExecutor(max_workers=4) as executor:
#         futures = {executor.submit(process_single_file, edz_file): edz_file for edz_file in edz_files}

#         for idx, future in enumerate(as_completed(futures), 1):
#             self.queue.put(lambda idx=idx: self.progress.configure(value=idx))

#         self.queue.put(lambda: self.status_label.config(text="Готово", fg="green"))
#         if not found_flag.is_set():
#             self.queue.put(lambda: messagebox.showinfo("Результат", "Текст не найден."))
#             self.queue.put(lambda: self.results.insert(tk.END, "Текст не найден ни в одном архиве.\\n"))

#     def search_in_edz(self, edz_path, search_text, temp_dir):
#         try:
#             with py7zr.SevenZipFile(edz_path, 'r') as archive:
#                 extracted_files = archive.readall()
#                 for file_name, file_data in extracted_files.items():
#                     if file_name.endswith('.xml'):
#                         try:
#                             xml_content = file_data.read().decode('utf-8', errors='replace')
#                             blocks = re.findall(r'(<package.*?>.*?</package>)', xml_content, re.DOTALL)
#                             for block in blocks:
#                                 if search_text in block:
#                                     unzip_target_arc(edz_path, search_text, temp_dir)
#                                     return block
#                         except:
#                             pass
#         except:
#             pass
#         return None

#     def save_to_edz_archive(self, search_text, content, temp_dir):
#         save_folder = filedialog.askdirectory(title="Выберите папку для сохранения архива")
#         if not save_folder:
#             messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
#             return

#         archive_path = os.path.join(save_folder, f"{search_text}.edz")
#         manifest_filename = "manifest.xml"
#         manifest_path = os.path.join(temp_dir, manifest_filename)

#         try:
#             wrapped_content = f'''<manifest version="2.0">
#     <packages>
#         {content}
#     </packages>
# </manifest>'''

#             with open(manifest_path, 'w', encoding='utf-8') as f:
#                 f.write(wrapped_content)

#             with py7zr.SevenZipFile(archive_path, 'w') as archive:
#                 for root_dir, _, files in os.walk(temp_dir):
#                     for file in files:
#                         full_path = os.path.join(root_dir, file)
#                         rel_path = os.path.relpath(full_path, temp_dir)
#                         archive.write(full_path, rel_path)

#             shutil.rmtree(temp_dir, ignore_errors=True)
#             messagebox.showinfo("Результат", f"Архив сохранен: {archive_path}")
#         except Exception as e:
#             messagebox.showerror("Ошибка", f"Ошибка при создании архива: {e}")


# if __name__ == "__main__":
#     root = tk.Tk()
#     app = TextSearchApp(root)
#     root.mainloop()

# import os
# import shutil
# import tempfile
# import tkinter as tk
# from tkinter import filedialog, scrolledtext, messagebox
# from tkinter.ttk import Progressbar
# import py7zr
# import re
# from function import unzip_target_arc


# class TextSearchApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Поиск текста в XML файлах внутри архивов EDZ")

#         self.search_label = tk.Label(root, text="Введите текст для поиска:")
#         self.search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

#         self.search_entry = tk.Entry(root, width=50)
#         self.search_entry.grid(row=0, column=1, padx=5, pady=5)

#         self.search_entry.bind('<Control-Key>', self.handle_ctrl_shortcuts)

#         self.paste_button = tk.Button(root, text="Вставить из буфера", command=self.paste_from_clipboard)
#         self.paste_button.grid(row=0, column=2, padx=5, pady=5)

#         self.folder_label = tk.Label(root, text="Выберите папку:")
#         self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

#         self.folder_entry = tk.Entry(root, width=50)
#         self.folder_entry.grid(row=1, column=1, padx=5, pady=5)

#         self.browse_button = tk.Button(root, text="Обзор", command=self.browse_folder)
#         self.browse_button.grid(row=1, column=2, padx=5, pady=5)

#         self.search_button = tk.Button(root, text="Поиск", command=self.search_text_in_edz_files)
#         self.search_button.grid(row=2, column=1, padx=5, pady=5)

#         self.progress = Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
#         self.progress.grid(row=3, column=1, padx=5, pady=5)

#         self.results = scrolledtext.ScrolledText(root, width=80, height=20)
#         self.results.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

#     def browse_folder(self):
#         folder_path = filedialog.askdirectory()
#         self.folder_entry.delete(0, tk.END)
#         self.folder_entry.insert(0, folder_path)

#     def paste_from_clipboard(self):
#         try:
#             clipboard_text = self.root.clipboard_get()
#             self.search_entry.delete(0, tk.END)
#             self.search_entry.insert(0, clipboard_text)
#         except tk.TclError:
#             messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

#     def handle_ctrl_shortcuts(self, event):
#         if event.state & 0x4 and event.keycode == 86:  # Ctrl+V, независимо от раскладки
#             try:
#                 clipboard_text = self.root.clipboard_get()
#                 self.search_entry.delete(0, tk.END)
#                 self.search_entry.insert(0, clipboard_text)
#                 return "break"
#             except tk.TclError:
#                 messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")

#     def search_text_in_edz_files(self):
#         folder_path = self.folder_entry.get()
#         search_text = self.search_entry.get()

#         if not folder_path or not search_text:
#             messagebox.showerror("Ошибка", "Пожалуйста, введите текст для поиска и выберите папку.")
#             return

#         self.results.delete(1.0, tk.END)

#         edz_files = [f for f in os.listdir(folder_path) if f.endswith('.edz')]
#         total_files = len(edz_files)

#         if total_files == 0:
#             messagebox.showinfo("Результат", "В выбранной папке нет файлов формата .edz.")
#             return

#         self.progress['value'] = 0
#         self.progress['maximum'] = total_files

#         for idx, edz_file in enumerate(edz_files):
#             edz_path = os.path.join(folder_path, edz_file)
#             temp_dir = tempfile.mkdtemp()
#             found_block = self.search_in_edz(edz_path, search_text, temp_dir)
#             self.progress['value'] += 1
#             self.root.update_idletasks()

#             if found_block:
#                 self.save_to_edz_archive(search_text, found_block, temp_dir)
#                 self.results.insert(tk.END, f"Текст найден и сохранен в архиве {search_text}.edz из файла {edz_file}\n")
#                 return

#             shutil.rmtree(temp_dir, ignore_errors=True)

#         messagebox.showinfo("Результат", "Текст не найден ни в одном архиве.")
#         self.results.insert(tk.END, "Текст не найден ни в одном архиве.\n")

#     def search_in_edz(self, edz_path, search_text, temp_dir):
#         try:
#             with py7zr.SevenZipFile(edz_path, 'r') as archive:
#                 extracted_files = archive.readall()

#                 for file_name, file_data in extracted_files.items():
#                     if file_name.endswith('.xml'):
#                         try:
#                             xml_content = file_data.read().decode('utf-8', errors='replace')
#                             package_blocks = re.findall(r'(<package.*?>.*?</package>)', xml_content, re.DOTALL)

#                             for block in package_blocks:
#                                 if search_text in block:
#                                     unzip_target_arc(edz_path, search_text, temp_dir)
#                                     return block

#                         except Exception as e:
#                             self.results.insert(tk.END, f"Ошибка разбора XML файла: {file_name}, ошибка: {e}\n")
#         except Exception as e:
#             self.results.insert(tk.END, f"Ошибка при работе с архивом {edz_path}: {e}\n")
#         return None

#     def save_to_edz_archive(self, search_text, content, temp_dir):
#         save_folder = filedialog.askdirectory(title="Выберите папку для сохранения архива")
#         if not save_folder:
#             messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
#             return

#         archive_path = os.path.join(save_folder, f"{search_text}.edz")
#         manifest_filename = "manifest.xml"
#         manifest_path = os.path.join(temp_dir, manifest_filename)

#         try:
#             # Оборачиваем содержимое в manifest/packages
#             wrapped_content = f'''<manifest version="2.0">
#                                         <packages>
#                                             {content}
#                                         </packages>
#                                     </manifest>'''

#             with open(manifest_path, 'w', encoding='utf-8') as f:
#                 f.write(wrapped_content)

#             with py7zr.SevenZipFile(archive_path, 'w') as archive:
#                 for root_dir, _, files in os.walk(temp_dir):
#                     for file in files:
#                         full_path = os.path.join(root_dir, file)
#                         rel_path = os.path.relpath(full_path, temp_dir)
#                         archive.write(full_path, rel_path)

#             shutil.rmtree(temp_dir, ignore_errors=True)
#             messagebox.showinfo("Результат", f"Архив сохранен: {archive_path}")

#         except Exception as e:
#             messagebox.showerror("Ошибка", f"Ошибка при создании архива: {e}")


# """Start main programm"""
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = TextSearchApp(root)
#     root.mainloop()

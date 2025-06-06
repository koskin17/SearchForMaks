# Імпорт бібліотек для GUI, роботи з файлами, архівами та текстом
import tkinter as tk  # Бібліотека Tkinter — базова для створення графічного інтерфейсу
from tkinter import filedialog, scrolledtext, messagebox  # Додаткові компоненти інтерфейсу
import os  # Робота з операційною системою (шляхи, перевірка файлів і папок)
import py7zr  # Бібліотека для читання/запису 7z-архівів (працює і з .edz)
import tempfile  # Для створення тимчасових папок (не використовується, але імпортовано)
# import getpass  # Закоментовано — міг би використовуватись для визначення користувача
import shutil  # Модуль для копіювання і видалення файлів/папок
import re  # Регулярні вирази — зручно для пошуку в тексті

# Клас, який описує GUI-додаток
class TextSearchApp:
    def __init__(self, root):
        self.root = root  # Зберігаємо посилання на головне вікно
        self.root.title("Поиск по тексту в файлах")  # Заголовок вікна

        # === Поле для вводу тексту пошуку ===
        tk.Label(root, text="Введите текст для поиска:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_entry = tk.Entry(root, width=40)  # Створюємо текстове поле
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)  # Розташування поля

        self.paste_button = tk.Button(root, text="Вставить", command=self.paste_from_clipboard)  # Кнопка вставки
        self.paste_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NW)  # Розміщення кнопки

        self.add_context_menu(self.search_entry)  # Додаємо контекстне меню ПКМ
        self.search_entry.bind('<KeyPress>', self.handle_keypress)  # Обробка Ctrl+V (вставка з буфера)

        # === Поле для вибору папки ===
        tk.Label(root, text="Папка с файлами:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_entry = tk.Entry(root, width=50)  # Текстове поле для шляху до папки
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.browse_button = tk.Button(root, text="Обзор...", command=self.browse_folder)  # Кнопка для вибору папки
        self.browse_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.NW)

        # === Кнопка запуску пошуку ===
        self.search_button = tk.Button(root, text="Search", command=self.start_search)
        self.search_button.grid(row=2, column=1, pady=10)

        # === Текстове поле для логів ===
        self.log_text = scrolledtext.ScrolledText(root, width=80, height=20, state='normal')  # Прокручуване поле
        self.log_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    # Метод: додавання контекстного меню (ПКМ -> "Вставить")
    def add_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0)  # Створення меню без "відриву"
        menu.add_command(label="Вставить", command=lambda: self.paste_from_clipboard(None))  # Додаємо пункт меню
        widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))  # Прив’язуємо ПКМ

    # Метод: вставка з буфера обміну
    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.root.clipboard_get()  # Отримуємо текст із буфера
            self.search_entry.delete(0, tk.END)  # Очищаємо поле
            self.search_entry.insert(0, clipboard_text)  # Вставляємо текст
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")  # Повідомлення про помилку

    # Метод: обробка клавіш (Ctrl+V)
    def handle_keypress(self, event):
        if (event.state & 0x4) and event.keycode == 86:  # Перевірка на Ctrl+V
            self.paste_from_clipboard()
            return "break"  # Зупиняємо подальшу обробку

    # Метод: вибір папки
    def browse_folder(self):
        folder = filedialog.askdirectory()  # Відкриваємо діалог вибору папки
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)  # Вставляємо шлях у поле

    # Метод: пошук файлів у вибраній папці
    def start_search(self):
        folder = self.folder_entry.get()  # Отримуємо шлях
        search_text = self.search_entry.get().strip()  # Отримуємо текст пошуку

        # Перевірка вказівки тексту для пошуку та папки для пошуку
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Ошибка", "Укажите корректную папку.")
            return
        if not search_text:
            messagebox.showerror("Ошибка", "Введите текст для поиска.")
            return

        # Лог: початок пошуку
        self.log_text.insert(tk.END, f"🔍 Поиск текста: '{search_text}' в архивах папки: {folder}\n")
        self.log_text.see(tk.END) # Прокручування текстового поля вниз так до того моменту, щоб було видно нове повідомлення

        # Отримуємо список .edz-файлів
        edz_files = [f for f in os.listdir(folder) if f.lower().endswith('.edz')]
        if not edz_files:
            self.log_text.insert(tk.END, "⚠️ В указанной папке нет файлов .edz\n")
            self.log_text.see(tk.END) # Прокручування текстового поля вниз так до того моменту, щоб було видно нове повідомлення
            return
        else:
            self.log_text.insert(tk.END, f"В папке найдены следующие архивы .edz: {', '.join(edz_files)}\n\n")
            self.log_text.see(tk.END) # Прокручування текстового поля вниз так до тог,о моменту, щоб було видно нове повідомлення

        for filename in edz_files:
            self.log_text.insert(tk.END, f"Проверяем архив {filename} на наличие искомого текста...\n\n")
            edz_path = os.path.join(folder, filename).replace("\\", "/")  # Повний шлях до файлу
            self.log_text.insert(tk.END, f"Полный путь к файлу edz_path: {edz_path}\n\n") # TODO УДАЛИТЬ! Путь к файлу выводится
            try:
                with py7zr.SevenZipFile(edz_path, mode='r') as archive:  # Відкриваємо архів
                    manifest_name = next((name for name in archive.getnames() if name.endswith('manifest.xml')), None)

                    if manifest_name:
                        # Читаємо manifest.xml
                        manifest_data = archive.read([manifest_name])[manifest_name].read().decode('utf-8', errors='ignore')

                        # Шукаємо потрібний блок <package>
                        match = re.search(
                            rf'(<package[^>]*?(key|name)="[^"]*{re.escape(search_text)}[^"]*".*?>.*?</package>)',
                            manifest_data,
                            re.DOTALL
                        )

                        if match:
                            self.log_text.insert(tk.END, f"  Искомый текст найден в файле manifest.xml в архиве {filename}\n\n")
                            package_block = match.group(1)  # Отримуємо сам блок <package>

                            # Шукаємо всі <item type="..." locator="...">
                            items = re.findall(r'<item\s+[^>]*type="([^"]+)"[^>]*locator="([^"]+)"', package_block)

                            # Шляхи до файлів
                            file_paths = []
                            for type_, locator in items:
                                normalized_locator = locator.replace('\\', '/')
                                file_paths.append(f"items/{type_}/{normalized_locator}")
                            self.log_text.insert(tk.END, f"  Файлы, которые будут упаковы в архив: {file_paths}\n\n")

                            # Повний manifest.xml (створюємо з одного блоку)
                            full_manifest = f"""<manifest version="2.0">
    <packages>
        {package_block}
    </packages>
</manifest>"""
                            self.log_text.insert(tk.END, f"Новый файл manifest.xml был сформирован.\n\n")

                            # Створюємо тимчасову папку на робочому столі
                            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                            temp_dir = os.path.join(desktop_path, f"temp_{search_text}")
                            os.makedirs(temp_dir, exist_ok=True)
                            self.log_text.insert(tk.END, f"На Рабочем столе была создана временная папка, которая по окончанию работы будет автоматически удалена.\n\n")

                            # Зберігаємо manifest.xml
                            manifest_path = os.path.join(temp_dir, "manifest.xml")
                            with open(manifest_path, 'w', encoding='utf-8') as f:
                                f.write(full_manifest)
                            self.log_text.insert(tk.END, f"Во временной папке был сохранён новый файл manifest.xml.\n\n")

                            self.log_text.insert(tk.END, f"Разархивируем из архива следующие файлы: {file_paths}.\n\n")
                            
                            
                                self.log_text.insert(tk.END, f"Извлекаем файл {file}.\n")  # TODO Удалить!
                                # file_path = os.path.join(folder, filename).replace('\\', '/') # TODO Удалить!
                                # self.log_text.insert(tk.END, f"file_path: {file_path}.\n")  # TODO Удалить!
                                # self.log_text.insert(tk.END, f"edz_path: {edz_path}.\n")  # TODO Удалить!
                                # self.log_text.insert(tk.END, f"File: {file}.\n")  # TODO Удалить!
                                                                                
                                archive.extract(path=temp_dir, targets=[file])
                                self.log_text.insert(tk.END, f"✅ Файл {file} успешно извлечён.\n\n")
                                # except: # TODO Удалить!
                                #     self.log_text.insert(tk.END, f"⚠️ Файл не найден в архиве: {path}\n") # TODO Удалить!
                                #     self.log_text.see(tk.END) # TODO Удалить!
#                             for path in file_paths:
#                                 if path in all_names:
#                                     archive.extract(path=temp_dir, targets=[path])
#                                     extracted_files.append(path)
#                                 else:
#                                     self.log_text.insert(tk.END, f"⚠️ Файл не найден в архиве: {path}\n")
#                                     self.log_text.see(tk.END)

#                             # Створення нового архіву на робочому столі
#                             archive_name = f"{search_text}.edz"
#                             archive_path = os.path.join(desktop_path, archive_name)

#                             # Запис файлів у новий архів
#                             with py7zr.SevenZipFile(archive_path, 'w') as new_archive:
#                                 for root, _, files in os.walk(temp_dir):
#                                     for file in files:
#                                         full_path = os.path.join(root, file)
#                                         rel_path = os.path.relpath(full_path, temp_dir)
#                                         new_archive.write(full_path, rel_path)

#                             # Лог: архів створено
#                             self.log_text.insert(tk.END, f"💾 Архив сохранён на рабочем столе: {archive_name}\n")
#                             self.log_text.see(tk.END)

#                             # Видалення тимчасової папки (опціонально, наразі закоментовано)
#                             # shutil.rmtree(temp_dir, ignore_errors=True)
#                             # self.log_text.insert(tk.END, f"🧹 Временная папка удалена: {temp_dir}\n")
#                             # self.log_text.see(tk.END)

#                             return  # Обробили перший відповідний файл — виходимо

#                         else:
#                             self.log_text.insert(tk.END, f"⛔ Текст не найден в архиве: {filename}\n")
#                             self.log_text.see(tk.END)
#                     else:
#                         self.log_text.insert(tk.END, f"❌ manifest.xml не найден в архиве: {filename}\n")
#                         self.log_text.see(tk.END)

            except Exception as e:
                self.log_text.insert(tk.END, f"❗ Ошибка при обработке {filename}: {e}\n")
                self.log_text.see(tk.END)

# Точка входу: запуск GUI
if __name__ == "__main__":
    root = tk.Tk()  # Створюємо головне вікно
    app = TextSearchApp(root)  # Ініціалізуємо застосунок
    root.mainloop()  # Запускаємо нескінченний цикл подій



# НИЖЕ ОБРЕЗАННЫЙ КОД, КОТОРЫЙ БЫЛ ОБРЕЗАН ПРИ НАПИСАНИИ КОММЕНТАРИЕВ К КАЖДОЙ СТРОКЕ.
# ### 📦 Імпорт необхідних бібліотек:
# import tkinter as tk  # Графічна бібліотека для створення GUI-додатків
# from tkinter import filedialog, scrolledtext, messagebox  # Додаткові компоненти для роботи з файлами, текстом і повідомленнями
# import os  # Модуль для роботи з файловою системою (шляхи, файли, папки)
# import py7zr  # Бібліотека для роботи з архівами .7z (у нашому випадку .edz — це, скоріш за все, теж 7z)
# import tempfile  # Не використовується зараз, але застосовується для створення тимчасових папок
# # import getpass  # Було закоментовано — можна отримати ім’я користувача, але не використовується
# import shutil  # Для копіювання і видалення файлів та папок
# import re  # Регулярні вирази — для пошуку у тексті manifest.xml

# ### 🧩 Клас основного вікна програми:
# class TextSearchApp:
# # > Оголошення класу, який міститиме весь інтерфейс та логіку програми.

# ### 🔧 Ініціалізація вікна (конструктор класу):
#     def __init__(self, root):
#         self.root = root  # Зберігаємо посилання на головне вікно
#         self.root.title("Поиск по тексту в файлах")  # Встановлюємо заголовок вікна

# #### 🎯 Блок вводу тексту для пошуку:
#         tk.Label(root, text="Введите текст для поиска:").grid(...)  # Надпис біля поля вводу
#         self.search_entry = tk.Entry(root, width=40)  # Поле вводу тексту
#         self.search_entry.grid(...)  # Розміщення на сітці

# #### 🧷 Кнопка вставки з буфера обміну:
#         self.paste_button = tk.Button(root, text="Вставить", command=self.paste_from_clipboard)
#         self.paste_button.grid(...)  # Розміщення кнопки праворуч

# #### 🖱 Контекстне меню (ПКМ — вставити):
#         self.add_context_menu(self.search_entry)  # Додає меню правої кнопки миші до поля вводу

# #### ⌨ Обробка натискання клавіш:
#         self.search_entry.bind('<KeyPress>', self.handle_keypress)  # Обробка Ctrl+V (вставка)

# ### 📁 Вибір папки з файлами:
#         tk.Label(root, text="Папка с файлами:").grid(...)  # Пояснення
#         self.folder_entry = tk.Entry(root, width=50)  # Поле для шляху до папки
#         self.folder_entry.grid(...)  # Розміщення
#         self.browse_button = tk.Button(root, text="Обзор...", command=self.browse_folder)  # Кнопка для вибору папки
#         self.browse_button.grid(...)  # Розміщення

# ### ▶ Кнопка запуску пошуку:
#         self.search_button = tk.Button(root, text="Search", command=self.start_search)  # Кнопка запускає метод start_search
#         self.search_button.grid(row=2, column=1, pady=10)

# ### 📜 Текстове поле для логів:
#         self.log_text = scrolledtext.ScrolledText(root, width=80, height=20, state='normal')  # Прокручуваний текстовий блок
#         self.log_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)  # Розтягується на всю ширину

# ### 📋 Метод: додавання контекстного меню "Вставить":
#     def add_context_menu(self, widget):
#         menu = tk.Menu(widget, tearoff=0)  # Створюємо контекстне меню
#         menu.add_command(label="Вставить", command=lambda: self.paste_from_clipboard(None))  # Додаємо команду вставки
#         widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))  # Відкриваємо меню по ПКМ

# ### 📋 Метод: вставка з буфера обміну:
#     def paste_from_clipboard(self, event=None):
#         try:
#             clipboard_text = self.root.clipboard_get()  # Отримуємо текст із буфера
#             self.search_entry.delete(0, tk.END)  # Очищаємо поле
#             self.search_entry.insert(0, clipboard_text)  # Вставляємо
#         except tk.TclError:
#             messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")  # Якщо помилка — показати вікно

# ### ⌨ Метод: обробка натискання Ctrl+V (незалежно від мови):
#     def handle_keypress(self, event):
#         if (event.state & 0x4) and event.keycode == 86:  # Ctrl + V — навіть якщо мова не англійська
#             self.paste_from_clipboard()
#             return "break"  # Перериваємо подальшу обробку події

# ### 📂 Метод: вибір папки:
#     def browse_folder(self):
#         folder = filedialog.askdirectory()  # Відкриває діалог вибору папки
#         if folder:
#             self.folder_entry.delete(0, tk.END)
#             self.folder_entry.insert(0, folder)  # Вставляє вибраний шлях у поле

# ### 🔍 Метод: запуск пошуку:
#     def start_search(self):
#         folder = self.folder_entry.get()  # Отримуємо введену папку
#         search_text = self.search_entry.get().strip()  # Текст для пошуку

# #### 🛑 Перевірка на правильність вводу:
#         if not folder or not os.path.isdir(folder):  # Чи існує така папка
#             messagebox.showerror("Ошибка", "Укажите корректную папку.")
#             return

#         if not search_text:
#             messagebox.showerror("Ошибка", "Введите текст для поиска.")
#             return

# #### 📜 Початок логування:
#         self.log_text.insert(tk.END, f"🔍 Поиск текста: '{search_text}' в архивах папки: {folder}\n")
#         self.log_text.see(tk.END)

# ### 🔍 Пошук .edz файлів:
#         edz_files = [f for f in os.listdir(folder) if f.lower().endswith('.edz')]
#         if not edz_files:
#             self.log_text.insert(tk.END, "⚠️ В указанной папке нет файлов .edz\n")
#             self.log_text.see(tk.END)
#             return

# ### 🔧 Перебір .edz файлів:
#         for filename in edz_files:
#             edz_path = os.path.join(folder, filename)
#             try:
#                 with py7zr.SevenZipFile(edz_path, mode='r') as archive:
# #### 📑 Пошук manifest.xml:
#                     manifest_name = next((name for name in archive.getnames() if name.endswith('manifest.xml')), None)
# #### 📖 Якщо знайшли:
#                     if manifest_name:
#                         manifest_data = archive.read([manifest_name])[manifest_name].read().decode('utf-8', errors='ignore')

# #### 🔎 Пошук потрібного `<package>`:
#                         match = re.search(
#                             rf'(<package[^>]*?(key|name)="[^"]*{re.escape(search_text)}[^"]*".*?>.*?</package>)',
#                             manifest_data,
#                             re.DOTALL
#                         )

# #### ✅ Якщо знайдено:
#                         if match:
#                             package_block = match.group(1)
#                             self.log_text.insert(tk.END, f"✅ Текст найден в архиве: {filename}\n")

# ### 📌 Пошук item-ів:
#                             items = re.findall(r'<item\s+[^>]*type="([^"]+)"[^>]*locator="([^"]+)"', package_block)
#                             self.log_text.insert(tk.END, f"📌 Найденные <item>: {items}\n")
#                             file_paths = [f"items/{type_}/{locator.replace('\\', '/')}" for type_, locator in items]
#                             self.log_text.insert(tk.END, f"📂 Пути к файлам: {file_paths}\n")

# ### 🗂 Створення тимчасової папки:
#                             desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
#                             temp_dir = os.path.join(desktop_path, f"temp_{search_text}")
#                             os.makedirs(temp_dir, exist_ok=True)

# ### 💾 Збереження manifest.xml:
#                             manifest_path = os.path.join(temp_dir, "manifest.xml")
#                             with open(manifest_path, 'w', encoding='utf-8') as f:
#                                 f.write(full_manifest)

# ### 📤 Витягування потрібних файлів:
#                             extracted_files = []
#                             all_names = archive.getnames()
#                             for path in file_paths:
#                                 if path in all_names:
#                                     archive.extract(path=temp_dir, targets=[path])
#                                     extracted_files.append(path)
#                                 else:
#                                     self.log_text.insert(tk.END, f"⚠️ Файл не найден в архиве: {path}\n")
#                                     self.log_text.see(tk.END)

# ### 📦 Створення нового архіву:
#                             archive_name = f"{search_text}.edz"
#                             archive_path = os.path.join(desktop_path, archive_name)

#                             with py7zr.SevenZipFile(archive_path, 'w') as new_archive:
#                                 for root, _, files in os.walk(temp_dir):
#                                     for file in files:
#                                         full_path = os.path.join(root, file)
#                                         rel_path = os.path.relpath(full_path, temp_dir)
#                                         new_archive.write(full_path, rel_path)

# ### 📢 Показ результату:
#                             self.log_text.insert(tk.END, f"💾 Архив сохранён на рабочем столе: {archive_name}\n")
#                             self.log_text.see(tk.END)

# ### 🧹 (Неактивне) Видалення тимчасової папки:
#                             # shutil.rmtree(temp_dir, ignore_errors=True)
#                             # self.log_text.insert(tk.END, f"🧹 Временная папка удалена: {temp_dir}\n")
#                             # self.log_text.see(tk.END)

# ### ⛔ Якщо не знайдено:
#                         else:
#                             self.log_text.insert(tk.END, f"⛔ Текст не найден в архиве: {filename}\n")
#                             self.log_text.see(tk.END)

# ### ❌ Якщо manifest.xml немає:
#                     else:
#                         self.log_text.insert(tk.END, f"❌ manifest.xml не найден в архиве: {filename}\n")
#                         self.log_text.see(tk.END)

# ### ❗ Обробка винятків:
#             except Exception as e:
#                 self.log_text.insert(tk.END, f"❗ Ошибка при обработке {filename}: {e}\n")
#                 self.log_text.see(tk.END)

# ### 🖼 Запуск додатку:
# if __name__ == "__main__":
#     root = tk.Tk()  # Створюємо головне вікно
#     app = TextSearchApp(root)  # Ініціалізуємо наш додаток
#     root.mainloop()  # Запускаємо GUI-петлю

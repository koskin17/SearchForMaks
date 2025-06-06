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
                            file_paths = [f"items/{type_}/{locator.replace('\\', '/')}" for type_, locator in items]
                            self.log_text.insert(tk.END, f"  Файлы, которые будут упаковы в архив: {file_paths}\n\n")
                            self.log_text.see(tk.END)

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
                            self.log_text.insert(tk.END, f"На Рабочем столе была создана временная папка, которая по окончанию работы будет автоатически удалена.\n\n")
                            self.log_text.see(tk.END)

                            # Зберігаємо manifest.xml
                            manifest_path = os.path.join(temp_dir, "manifest.xml")
                            with open(manifest_path, 'w', encoding='utf-8') as f:
                                f.write(full_manifest)
                            self.log_text.insert(tk.END, f"Во временной папке был сохранён новый файл manifest.xml.\n\n")
                            self.log_text.see(tk.END)

                            # Витягуємо зазначені файли
                            # extracted_files = []
                            # # all_names = archive.getnames()
                            self.log_text.insert(tk.END, f"Разархивируем из архива следующие файлы: {file_paths}.\n\n")
                            self.log_text.see(tk.END)
                            
                            # # with py7zr.SevenZipFile(archive, mode='r') as archive:
                            for file in file_paths:
                                self.log_text.insert(tk.END, f"Разархивируем файл: {file}.\n\n")
                                self.log_text.see(tk.END)
                                self.log_text.insert(tk.END, f"Извлекаем файл {file}.\n")
                                self.log_text.see(tk.END)
                                file_path = os.path.join(edz_path, file).replace('\\', '/')
                                archive.extract(path=temp_dir, targets=[file_path])
                                self.log_text.insert(tk.END, f"Файл {file_path} успешно извлечён.\n\n")
                                self.log_text.see(tk.END)

                            # Створення нового архіву на робочому столі
                            archive_name = f"{search_text}.edz"
                            archive_path = os.path.join(desktop_path, archive_name)

                            # Запис файлів у новий архів
                            with py7zr.SevenZipFile(archive_path, 'w') as new_archive:
                                for root, _, files in os.walk(temp_dir):
                                    for file in files:
                                        full_path = os.path.join(root, file)
                                        rel_path = os.path.relpath(full_path, temp_dir)
                                        new_archive.write(full_path, rel_path)

                            # Лог: архів створено
                            self.log_text.insert(tk.END, f"💾 Архив сохранён на рабочем столе: {archive_name}\n")
                            self.log_text.see(tk.END)

                            # Видалення тимчасової папки (опціонально, наразі закоментовано)
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            self.log_text.insert(tk.END, f"🧹 Временная папка удалена: {temp_dir}\n")
                            self.log_text.see(tk.END)

                            return  # Обробили перший відповідний файл — виходимо

                        else:
                            self.log_text.insert(tk.END, f"⛔ Текст не найден в архиве: {filename}\n")
                            self.log_text.see(tk.END)
                    else:
                        self.log_text.insert(tk.END, f"❌ manifest.xml не найден в архиве: {filename}\n")
                        self.log_text.see(tk.END)

            except Exception as e:
                self.log_text.insert(tk.END, f"❗ Ошибка при обработке {filename}: {e}\n")
                self.log_text.see(tk.END)

# Точка входу: запуск GUI
if __name__ == "__main__":
    root = tk.Tk()  # Створюємо головне вікно
    app = TextSearchApp(root)  # Ініціалізуємо застосунок
    root.mainloop()  # Запускаємо нескінченний цикл подій

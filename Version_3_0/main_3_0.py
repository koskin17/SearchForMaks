# Импорт библиотек для GUI, работы с файлами, архивами и текстом
import tkinter as tk  # Библиотека Tkinter — базовая для создания графического интерфейса
from tkinter import filedialog, scrolledtext, messagebox  # Дополнительные компоненты интерфейса
import os  # Работа с операционной системой (пути, проверка файлов и папок)
import py7zr  # Библиотека для чтения/записи 7z-архивов (работает и с .edz)
import shutil  # Модуль для копирования и удаления файлов/папок
import re  # Модуль для копирования и удаления файлов/папок

# Клас, який описує GUI-додаток
class TextSearchApp:
    def __init__(self, root):
        self.root = root  # Класс, описывающий GUI-приложение
        self.root.title("Поиск по тексту в файлах")  # Сохраняем ссылку на главное окно

        # === Поле для вводу тексту пошуку ===
        tk.Label(root, text="Введите текст для поиска:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_entry = tk.Entry(root, width=40)  # Создаем текстовое поле
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)  # Розташування поля

        self.paste_button = tk.Button(root, text="Вставить", command=self.paste_from_clipboard)  # Кнопка вставки
        self.paste_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NW)  # Размещение кнопки

        self.add_context_menu(self.search_entry)  # Додаємо контекстне меню ПКМ
        self.search_entry.bind('<KeyPress>', self.handle_keypress)  # Обработка Ctrl+V (вставка из буфера)

        # === Поле для выбора папки ===
        tk.Label(root, text="Папка с файлами:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.folder_entry = tk.Entry(root, width=50)  # Текстовое поле для пути в папку
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.browse_button = tk.Button(root, text="Обзор...", command=self.browse_folder)  # Кнопка для вибору папки
        self.browse_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.NW)

        # === Кнопка запуска поиска ===
        self.search_button = tk.Button(root, text="Search", command=self.start_search)
        self.search_button.grid(row=2, column=1, pady=10)

        # === Текстовое поле для логов ===
        self.log_text = scrolledtext.ScrolledText(root, width=80, height=20, state='normal')  # Прокручиваемое поле
        self.log_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    # Метод: добавление контекстного меню (ПКМ -> "Вставить")
    def add_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0)  # Создание меню без "отрыва"
        menu.add_command(label="Вставить", command=lambda: self.paste_from_clipboard(None))  # Добавляем пункт меню
        widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))  # Привязываем ПКМ

    # Метод: вставка из буфера обмена
    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.root.clipboard_get()  # Получаем текст из буфера
            self.search_entry.delete(0, tk.END)  # Очищаем поле
            self.search_entry.insert(0, clipboard_text)  # Вставляем текст
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или не содержит текста.")  # Сообщение об ошибке

    # Метод: обработка клавиш (Ctrl+V)
    def handle_keypress(self, event):
        if (event.state & 0x4) and event.keycode == 86:  # Проверка на Ctrl+V
            self.paste_from_clipboard()
            return "break"  # Останавливаем дальнейшую обработку

    # Метод: выбор папки
    def browse_folder(self):
        folder = filedialog.askdirectory()  # Открываем диалог выбора папки
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)  # Вставляем путь в поле

    # Метод: поиск файлов в выбранной папке
    def start_search(self):
        folder = self.folder_entry.get()  # Получаем путь
        search_text = self.search_entry.get().strip()  # Получаем текст поиска

        # Проверка указания текста для поиска и папки для поиска
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Ошибка", "Укажите корректную папку.")
            return
        if not search_text:
            messagebox.showerror("Ошибка", "Введите текст для поиска.")
            return

        # Лог: начало поиска
        self.log_text.insert(tk.END, f"🔍 Поиск текста: '{search_text}' в архивах папки: {folder}\n")
        self.log_text.see(tk.END) # Прокрутка текстового поля вниз до того момента, чтобы было видно новое сообщение

        # Получаем список .edz-файлов
        edz_files = [f for f in os.listdir(folder) if f.lower().endswith('.edz')]
        if not edz_files:
            self.log_text.insert(tk.END, "⚠️ В указанной папке нет файлов .edz\n")
            self.log_text.see(tk.END) # Прокрутка текстового поля вниз до того момента, чтобы было видно новое сообщение
            return
        else:
            self.log_text.insert(tk.END, f"В папке найдены следующие архивы .edz: {', '.join(edz_files)}\n\n")
            self.log_text.see(tk.END) # Прокрутка текстового поля вниз до того момента, чтобы было видно новое сообщение

        for filename in edz_files:
            self.log_text.insert(tk.END, f"Проверяем архив {filename} на наличие искомого текста...\n\n")
            edz_path = os.path.join(folder, filename).replace("\\", "/")  # Полный путь к файлу
            self.log_text.insert(tk.END, f"Полный путь к файлу edz_path: {edz_path}\n\n")
            try:
                with py7zr.SevenZipFile(edz_path, mode='r') as archive:  # Открываем архив
                    manifest_name = next((name for name in archive.getnames() if name.endswith('manifest.xml')), None)

                    if manifest_name:
                        # Читаем manifest.xml
                        manifest_data = archive.read([manifest_name])[manifest_name].read().decode('utf-8', errors='ignore')

                        # Ищем нужный блок <package>
                        match = re.search(
                            rf'(<package[^>]*?(key|name)="[^"]*{re.escape(search_text)}[^"]*".*?>.*?</package>)',
                            manifest_data,
                            re.DOTALL
                        )

                        if match:
                            self.log_text.insert(tk.END, f"  Искомый текст найден в файле manifest.xml в архиве {filename}\n\n")
                            package_block = match.group(1)  # Получаем сам блок <package>

                            # Ищем все <item type="..." locator="...">
                            items = re.findall(r'<item\s+[^>]*type="([^"]+)"[^>]*locator="([^"]+)"', package_block)

                            # Пути к файлам
                            file_paths = []
                            for type_, locator in items:
                                normalized_locator = locator.replace('\\', '/')
                                file_paths.append(f"items/{type_}/{normalized_locator}")
                            self.log_text.insert(tk.END, f"  Файлы, которые будут упаковы в архив: {file_paths}\n\n")

                            # Полный manifest.xml (создаем из одного блока)
                            full_manifest = f"""<manifest version="2.0">
    <packages>
        {package_block}
    </packages>
</manifest>"""
                            self.log_text.insert(tk.END, f"Новый файл manifest.xml был сформирован.\n\n")

                            # Создаем временную папку на рабочем столе
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
                            
                            # Отфильтровываем существующие файлы в архиве (важное исправление)
                            archive_filenames = archive.getnames()
                            matching_files = []
                            for desired_path in file_paths:
                                match = next((f for f in archive_filenames if f.endswith(desired_path)), None)
                                if match:
                                    matching_files.append(match)
                                else:
                                    self.log_text.insert(tk.END, f"⚠️ Файл '{desired_path}' не найден в архиве.\n")

                            self.log_text.insert(tk.END, f"Извлекаем {len(matching_files)} файл(ов):\n")
                            for file in matching_files:
                                self.log_text.insert(tk.END, f"  - {file}\n")
                                
                            archive.extract(path=temp_dir, targets=matching_files)
                            self.log_text.insert(tk.END, f"✅ Все файлы успешно извлечены.\n\n")

                            # Создание нового архива на рабочем столе
                            archive_name = f"{search_text}.edz"
                            archive_path = os.path.join(desktop_path, archive_name)

                            # Запись файлов в новый архив
                            with py7zr.SevenZipFile(archive_path, 'w') as new_archive:
                                for root, _, files in os.walk(temp_dir):
                                    for file in files:
                                        full_path = os.path.join(root, file)
                                        rel_path = os.path.relpath(full_path, temp_dir)
                                        new_archive.write(full_path, rel_path)

                            # Запись файлов в новый архив
                            self.log_text.insert(tk.END, f"💾 Архив сохранён на рабочем столе: {archive_name}\n")
                            self.log_text.see(tk.END)

                            # Удаление временной папки (опционально, закомментировано)
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            self.log_text.insert(tk.END, f"🧹 Временная папка удалена: {temp_dir}\n")
                            self.log_text.see(tk.END)
            except Exception as e:
                self.log_text.insert(tk.END, f"❗ Ошибка при обработке {filename}: {e}\n")
                self.log_text.see(tk.END)

# Точка входа: запуск GUI
if __name__ == "__main__":
    root = tk.Tk()  # Создаем главное окно
    app = TextSearchApp(root)  # Инициализируем приложение
    root.mainloop()  # Запускаем нескончаемый цикл событий
    
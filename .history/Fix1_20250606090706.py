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
        self.log_text.see(tk.END)  # Прокручування текстового поля вниз так до того моменту, щоб було видно нове повідомлення

        # Отримуємо список .edz-файлів
        edz_files = [f for f in os.listdir(folder) if f.lower().endswith('.edz')]
        if not edz_files:
            self.log_text.insert(tk.END, "⚠️ В указанной папке нет файлов .edz\n")
            self.log_text.see(tk.END)
            return
        else:
            self.log_text.insert(tk.END, f"В папке найдены следующие архивы .edz: {', '.join(edz_files)}\n\n")
            self.log_text.see(tk.END)

        for filename in edz_files:
            self.log_text.insert(tk.END, f"Проверяем архив {filename} на наличие искомого текста...\n\n")
            edz_path = os.path.join(folder, filename).replace("\\", "/")  # Повний шлях до файлу
            self.log_text.insert(tk.END, f"Полный путь к файлу edz_path: {edz_path}\n\n")  # TODO УДАЛИТЬ! Путь к файлу выводится

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

                            # Шляхи до файлів (виправлено - замінено .replace у f-рядку)
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

                            # Отфильтровываем существующие файлы в архиве (важное исправление)
                            archive_filenames = archive.getnames()
                            matching_files = []
                            for desired_path in file_paths:
                                match = next((f for f in archive_filenames if f.endswith(desired_path)), None)
                                if match:
                                    matching_files.append(match)
                                else:
                                    self.log_text.insert(tk.END, f"⚠️ Файл '{desired_path}' не найден в архиве.\n")

                            for file in matching_files:
                                self.log_text.insert(tk.END, f"Извлекаем файл {file}.\n")  # TODO Удалить!
                                archive.extract(path=temp_dir, targets=[file])
                                self.log_text.insert(tk.END, f"✅ Файл {file} успешно извлечён.\n\n")

            except Exception as e:
                self.log_text.insert(tk.END, f"❌ Ошибка при обработке архива {filename}: {str(e)}\n\n")

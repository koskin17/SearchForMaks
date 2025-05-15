import py7zr
import os

def unzip_target_arc(edz_path, search_text, dest_path):
    """Распаковывает только те файлы из архива, имя которых содержит искомый текст,
    а также всегда включает файл OMR.manufacturer.xml (если он есть)."""

    files_with_searching_model = set()

    with py7zr.SevenZipFile(edz_path) as archive:
        all_files = archive.getnames()
        total_files = len(all_files)
        print(f"Всего файлов в архиве: {total_files}")

        for idx, file in enumerate(all_files, 1):
            filename_only = os.path.basename(file)

            # Добавляем файл, если имя содержит текст поиска
            if search_text in filename_only:
                files_with_searching_model.add(file)

            # Добавляем OMR.manufacturer.xml всегда (точное имя)
            if filename_only == "OMR.manufacturer.xml":
                files_with_searching_model.add(file)

            # Вывод прогресса каждые 100 файлов
            if idx % 100 == 0 or idx == total_files:
                print(f"Обработано файлов: {idx}/{total_files}")

        if files_with_searching_model:
            archive.extract(path=dest_path, targets=list(files_with_searching_model))
            print(f"Извлечено файлов: {len(files_with_searching_model)}")
        else:
            print("Нет файлов для извлечения.")

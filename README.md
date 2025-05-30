# Extractor subs from mkv

Удобный GUI-скрипт на Python для извлечения субтитров из MKV-файлов с выбором дорожки, формата (txt, srt, ass, docx), имени и папки для сохранения.

## Возможности
- Извлечение субтитров из MKV-файлов (через mkvmerge/mkvextract)
- Выбор дорожки субтитров через выпадающий список
- Поддержка форматов: .txt, .srt, .ass, .docx
- Удобный адаптивный интерфейс на tkinter
- Автоматическая обработка кодировки

## Требования
- Python 3.7+
- mkvmerge, mkvextract (установить [MKVToolNix](https://mkvtoolnix.download/downloads.html))
- pip install chardet python-docx

## Запуск
1. Установите зависимости:
   ```sh
   pip install chardet python-docx
   ```
2. Убедитесь, что mkvmerge и mkvextract доступны в PATH.
3. Запустите GUI:
   ```sh
   python extract_subtitles_gui.py
   ```

## Использование
1. Выберите MKV-файл.
2. Выберите папку и имя для сохранения субтитров.
3. Выберите дорожку субтитров и формат.
4. Нажмите "Извлечь".

## Лицензия
MIT

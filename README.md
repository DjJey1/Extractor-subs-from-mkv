# Extractor subs from mkv

Удобный GUI-скрипт на Python для извлечения субтитров из MKV-файлов с выбором дорожки, формата (txt, srt, ass, docx), имени и папки для сохранения.

## Возможности
- Извлечение субтитров из MKV-файлов (через mkvmerge/mkvextract)
- Выбор дорожки субтитров через выпадающий список
- Поддержка форматов: .txt, .srt, .ass, .docx
- Современный адаптивный интерфейс на Flet (и customtkinter)
- Автоматическая обработка кодировки

## Требования
- Python 3.7+
- mkvmerge, mkvextract (установить [MKVToolNix](https://mkvtoolnix.download/downloads.html))
- pip install flet chardet python-docx

## Запуск (Flet GUI)
1. Установите зависимости:
   ```sh
   pip install flet chardet python-docx
   ```
2. Убедитесь, что mkvmerge и mkvextract доступны в PATH.
3. Запустите Flet GUI:
   ```sh
   python extract_subtitles_gui_flet.py
   ```

## Сборка .exe (Windows)
1. Установите flet:
   ```sh
   pip install flet
   ```
2. Соберите .exe через flet pack:
   ```sh
   flet pack extract_subtitles_gui_flet.py
   ```
   Готовый файл появится в папке `dist` или `output`.

## Использование
1. Выберите MKV-файл.
2. Выберите папку и имя для сохранения субтитров.
3. Выберите дорожку субтитров и формат.
4. Нажмите "Извлечь".

## Лицензия
MIT

import os
import re
import subprocess
import flet as ft
from flet import FilePicker, FilePickerResultEvent, TextField, Dropdown, DropdownOption, ElevatedButton, Text, Row, Column, SnackBar, Page, Container

# Функция извлечения субтитров (только MKV)
def extract_subtitles(mkv_path, output_txt, track_choice=None):
    ext = os.path.splitext(mkv_path)[1].lower()
    if ext != '.mkv':
        return False, 'Поддерживаются только MKV-файлы!'
    try:
        result = subprocess.run(
            ['mkvmerge', '-i', mkv_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
    except Exception as e:
        return False, f'Ошибка запуска mkvmerge: {e}'
    if result.returncode != 0:
        return False, f'Ошибка mkvmerge: {result.stderr}'
    lines = result.stdout.splitlines()
    subtitle_tracks = [line for line in lines if 'subtitles' in line]
    if not subtitle_tracks:
        return False, 'Субтитры не найдены.'
    track_idx = track_choice if track_choice is not None else 0
    if not (0 <= track_idx < len(subtitle_tracks)):
        track_idx = 0
    track_info = subtitle_tracks[track_idx]
    track_num = track_info.split(':')[0].split()[-1]
    temp_file = 'temp_sub.srt'
    subprocess.run(['mkvextract', 'tracks', mkv_path, f'{track_num}:{temp_file}'])
    try:
        import chardet
    except ImportError:
        subprocess.run(['python', '-m', 'pip', 'install', 'chardet'])
        import chardet
    with open(temp_file, 'rb') as f:
        raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected['encoding'] or 'utf-8'
    with open(temp_file, 'r', encoding=encoding, errors='replace') as src, open(output_txt, 'w', encoding='utf-8') as dst:
        for line in src:
            if not line.startswith('Dialogue:'):
                continue
            parts = line.strip().split(',', 9)
            if len(parts) < 10:
                continue
            start = parts[1]
            end = parts[2]
            text = parts[9]
            text = re.sub(r'\{.*?\}', '', text)
            text = text.replace('\\N', ' ').replace('  ', ' ').strip()
            def ass_time_to_srt(t):
                t = t.replace('.', ',')
                if t.count(':') == 1:
                    t = '0:' + t
                return t
            dst.write(f"{ass_time_to_srt(start)} --> {ass_time_to_srt(end)}\n{text}\n\n")
    os.remove(temp_file)
    return True, f'Субтитры сохранены в {output_txt}'

def main(page: Page):
    page.title = "Извлечение субтитров из MKV (Flet)"
    page.window_width = 700
    page.window_height = 400
    page.scroll = "auto"

    mkv_path = TextField(label="MKV видео", expand=True, read_only=True)
    output_dir = TextField(label="Папка для субтитров", expand=True, read_only=True)
    filename = TextField(label="Имя файла", expand=True)
    ext_dropdown = Dropdown(label="Расширение", width=120, options=[DropdownOption(".txt"), DropdownOption(".srt"), DropdownOption(".ass"), DropdownOption(".docx")], value=".txt")
    track_dropdown = Dropdown(label="Дорожка субтитров", expand=True, options=[DropdownOption("Не выбрано")], value="Не выбрано")
    status_text = Text(visible=False)

    def pick_file_result(e: FilePickerResultEvent):
        if e.files:
            mkv_path.value = e.files[0].path
            page.update()
            # Обновить дорожки
            update_tracks()

    def pick_folder_result(e: FilePickerResultEvent):
        if e.path:
            output_dir.value = e.path
            page.update()

    file_picker = FilePicker(on_result=pick_file_result)
    folder_picker = FilePicker(on_result=pick_folder_result)
    page.overlay.extend([file_picker, folder_picker])

    def update_tracks():
        if not mkv_path.value or not mkv_path.value.lower().endswith('.mkv'):
            track_dropdown.options = [DropdownOption("Не выбрано")]
            track_dropdown.value = "Не выбрано"
            page.update()
            return
        try:
            result = subprocess.run(
                ['mkvmerge', '-i', mkv_path.value],
                capture_output=True, text=True, encoding='utf-8', errors='replace'
            )
            lines = result.stdout.splitlines()
            subtitle_tracks = [line for line in lines if 'subtitles' in line]
            if subtitle_tracks:
                display_options = [f"{i+1}: {line}" for i, line in enumerate(subtitle_tracks)]
                track_dropdown.options = [DropdownOption(opt) for opt in display_options]
                track_dropdown.value = display_options[0]
            else:
                track_dropdown.options = [DropdownOption("Не выбрано")]
                track_dropdown.value = "Не выбрано"
        except Exception:
            track_dropdown.options = [DropdownOption("Не выбрано")]
            track_dropdown.value = "Не выбрано"
        page.update()

    def run_extract(e):
        if not mkv_path.value or not output_dir.value or not filename.value:
            page.snack_bar = SnackBar(Text("Выберите видеофайл, папку и имя для сохранения субтитров!"))
            page.snack_bar.open = True
            page.update()
            return
        ext = ext_dropdown.value
        base, user_ext = os.path.splitext(filename.value)
        save_name = filename.value if user_ext else filename.value + ext
        out_path = os.path.join(output_dir.value, save_name)
        # Определяем выбранную дорожку
        if not track_dropdown.options or track_dropdown.value == "Не выбрано":
            track_choice = 0
        else:
            track_choice = track_dropdown.options.index(next(opt for opt in track_dropdown.options if opt.key == track_dropdown.value))
        if ext == '.docx':
            try:
                from docx import Document
            except ImportError:
                subprocess.run(['python', '-m', 'pip', 'install', 'python-docx'])
                from docx import Document
            temp_txt = os.path.splitext(out_path)[0] + '_temp.txt'
            ok, msg = extract_subtitles(mkv_path.value, temp_txt, track_choice)
            if ok:
                doc = Document()
                with open(temp_txt, 'r', encoding='utf-8') as f:
                    for line in f:
                        doc.add_paragraph(line.rstrip())
                doc.save(out_path)
                os.remove(temp_txt)
                page.snack_bar = SnackBar(Text(f'Субтитры сохранены в {out_path}'))
                page.snack_bar.open = True
            else:
                page.snack_bar = SnackBar(Text(msg))
                page.snack_bar.open = True
            page.update()
            return
        ok, msg = extract_subtitles(mkv_path.value, out_path, track_choice)
        page.snack_bar = SnackBar(Text(msg))
        page.snack_bar.open = True
        page.update()

    page.add(
        Column([
            Row([
                mkv_path,
                ElevatedButton("Выбрать файл", on_click=lambda _: file_picker.pick_files(allowed_extensions=["mkv"]))
            ], alignment="end"),
            Row([
                output_dir,
                ElevatedButton("Выбрать папку", on_click=lambda _: folder_picker.get_directory_path())
            ], alignment="end"),
            Row([
                filename,
                ext_dropdown
            ], alignment="end"),
            Row([
                track_dropdown,
                Container(width=120)  # для выравнивания с ext_dropdown
            ], alignment="end"),
            Row([
                ElevatedButton("Извлечь", on_click=run_extract, style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"))
            ], alignment="end"),
            status_text
        ], spacing=10, expand=True)
    )

ft.app(target=main)

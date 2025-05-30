import subprocess
import sys
import os
import re

def extract_subtitles(mkv_path, output_txt, track_choice=None):
    # Получаем список дорожек
    try:
        result = subprocess.run(
            ['mkvmerge', '-i', mkv_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
    except Exception as e:
        print(f"Ошибка запуска mkvmerge: {e}")
        return
    if result.returncode != 0:
        print(f"Ошибка mkvmerge: {result.stderr}")
        return
    lines = result.stdout.splitlines()
    subtitle_tracks = [line for line in lines if 'subtitles' in line]
    if not subtitle_tracks:
        print("Субтитры не найдены.")
        return

    print("Доступные дорожки с субтитрами:")
    for idx, line in enumerate(subtitle_tracks):
        print(f"{idx}: {line}")

    if track_choice is None:
        try:
            user_input = input(f"Введите номер дорожки (0-{len(subtitle_tracks)-1}) или Enter для первой: ")
            track_idx = int(user_input) if user_input.strip() else 0
        except Exception:
            track_idx = 0
    else:
        track_idx = track_choice
    if not (0 <= track_idx < len(subtitle_tracks)):
        print("Некорректный номер дорожки. Используется первая.")
        track_idx = 0

    track_info = subtitle_tracks[track_idx]
    track_num = track_info.split(':')[0].split()[-1]

    # Извлекаем субтитры
    temp_file = 'temp_sub.srt'
    subprocess.run(['mkvextract', 'tracks', mkv_path, f'{track_num}:{temp_file}'])

    # Копируем текст субтитров в .txt с определением кодировки
    try:
        import chardet
    except ImportError:
        print("Устанавливаю chardet для определения кодировки...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'chardet'])
        import chardet

    # Определяем кодировку файла субтитров
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
            # Удаляем все фигурные скобки с эффектами
            text = re.sub(r'\{.*?\}', '', text)
            # Заменяем спецсимвол переноса строки ASS на обычный пробел
            text = text.replace('\\N', ' ').replace('  ', ' ').strip()
            # Преобразуем таймкод в формат 00:00:00.00 --> 00:00:00.00
            def ass_time_to_srt(t):
                t = t.replace('.', ',')
                if t.count(':') == 1:
                    t = '0:' + t
                return t
            dst.write(f"{ass_time_to_srt(start)} --> {ass_time_to_srt(end)}\n{text}\n\n")
    os.remove(temp_file)
    print(f'Субтитры сохранены в {output_txt}')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python extract_subtitles.py <файл.mkv> <выход.txt> [номер_дорожки]")
    else:
        track_choice = int(sys.argv[3]) if len(sys.argv) > 3 else None
        extract_subtitles(sys.argv[1], sys.argv[2], track_choice)

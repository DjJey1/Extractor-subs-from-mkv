import sys
import os
import re
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

def extract_subtitles(mkv_path, output_txt, track_choice=None, track_list=None):
    ext = os.path.splitext(mkv_path)[1].lower()
    # Только MKV поддержка
    if ext != '.mkv':
        messagebox.showerror("Ошибка", "Поддерживаются только MKV-файлы!")
        return
    try:
        result = subprocess.run(
            ['mkvmerge', '-i', mkv_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка запуска mkvmerge: {e}")
        return
    if result.returncode != 0:
        messagebox.showerror("Ошибка", f"Ошибка mkvmerge: {result.stderr}")
        return
    lines = result.stdout.splitlines()
    subtitle_tracks = [line for line in lines if 'subtitles' in line]
    if not subtitle_tracks:
        messagebox.showerror("Ошибка", "Субтитры не найдены.")
        return

    # Выбор дорожки через track_choice (номер из интерфейса)
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
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'chardet'])
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
    messagebox.showinfo("Готово", f'Субтитры сохранены в {output_txt}')

def simple_choice_dialog(title, options):
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry('600x300')
    var = tk.IntVar(value=0)
    for idx, opt in enumerate(options):
        tk.Radiobutton(dialog, text=opt, variable=var, value=idx, anchor='w', justify='left').pack(fill='x', padx=10, pady=2)
    def ok():
        dialog.destroy()
    tk.Button(dialog, text='OK', command=ok).pack(pady=10)
    dialog.grab_set()
    dialog.wait_window()
    return var.get()

def main():
    root = tk.Tk()
    root.title('Извлечение субтитров из MKV')
    root.geometry('700x350')
    root.resizable(True, True)

    mkv_path = tk.StringVar()
    output_dir = tk.StringVar()
    filename_var = tk.StringVar(value='')
    output_path = tk.StringVar()

    def select_mkv():
        file = filedialog.askopenfilename(title='Выберите видеофайл', filetypes=[('Видео файлы', '*.mkv'), ('MKV files', '*.mkv'), ('Все файлы', '*.*')])
        if file:
            mkv_path.set(file)
            if not output_dir.get():
                output_dir.set(os.path.dirname(file))
            update_output_path()

    def select_output_dir():
        dir_ = filedialog.askdirectory(title='Выберите папку для сохранения субтитров')
        if dir_:
            output_dir.set(dir_)
            update_output_path()

    def update_output_path(*args):
        name = filename_var.get()
        ext = ext_var.get()
        # Если пользователь явно указал расширение в имени, используем его
        base, user_ext = os.path.splitext(name)
        if not name:
            output_path.set('')
            return
        if user_ext:
            save_name = name
        else:
            save_name = name + ext
        if output_dir.get() and save_name:
            output_path.set(os.path.join(output_dir.get(), save_name))

    filename_var.trace_add('write', update_output_path)
    output_dir.trace_add('write', update_output_path)

    def run_extract():
        if not mkv_path.get() or not output_path.get():
            messagebox.showerror('Ошибка', 'Выберите видеофайл, папку и имя для сохранения субтитров!')
            return
        ext = os.path.splitext(output_path.get())[1].lower()
        # Определяем выбранную дорожку
        if track_var.get() == 'Не выбрано' or not track_options:
            track_choice = 0
        else:
            # Получаем индекс выбранной дорожки
            for idx, opt in enumerate([f"{i+1}: {line}" for i, line in enumerate(track_options)]):
                if track_var.get() == opt:
                    track_choice = idx
                    break
            else:
                track_choice = 0
        if ext == '.docx':
            try:
                from docx import Document
            except ImportError:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'python-docx'])
                from docx import Document
            # Генерируем docx
            generate_docx_subtitles(mkv_path.get(), output_path.get(), track_choice, track_options)
        else:
            extract_subtitles(mkv_path.get(), output_path.get(), track_choice, track_options)

    def generate_docx_subtitles(mkv_path, output_docx, track_choice, track_list):
        # Временный txt-файл
        temp_txt = os.path.splitext(output_docx)[0] + '_temp.txt'
        extract_subtitles(mkv_path, temp_txt, track_choice, track_list)
        try:
            from docx import Document
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'python-docx'])
            from docx import Document
        doc = Document()
        with open(temp_txt, 'r', encoding='utf-8') as f:
            for line in f:
                doc.add_paragraph(line.rstrip())
        doc.save(output_docx)
        os.remove(temp_txt)
        messagebox.showinfo('Готово', f'Субтитры сохранены в {output_docx}')

    # --- UI Layout ---
    frm = tk.Frame(root)
    frm.pack(fill='both', expand=True, padx=15, pady=10)

    frm.grid_columnconfigure(0, weight=100)
    frm.grid_columnconfigure(1, weight=0)
    for i in range(9):
        frm.grid_rowconfigure(i, weight=1)

    tk.Label(frm, text='MKV видео:').grid(row=0, column=0, sticky='w')
    mkv_entry = tk.Entry(frm, textvariable=mkv_path)
    mkv_entry.grid(row=1, column=0, sticky='ew', padx=(0,20))
    btn_file = tk.Button(frm, text='Выбрать файл', command=select_mkv, width=12, height=1)
    btn_file.grid(row=1, column=1, sticky='e', padx=(0,20))

    tk.Label(frm, text='Папка для субтитров:').grid(row=2, column=0, sticky='w', pady=(10,0))
    outdir_entry = tk.Entry(frm, textvariable=output_dir)
    outdir_entry.grid(row=3, column=0, sticky='ew', padx=(0,20))
    btn_dir = tk.Button(frm, text='Выбрать папку', command=select_output_dir, width=12, height=1)
    btn_dir.grid(row=3, column=1, sticky='e', padx=(0,20))

    tk.Label(frm, text='Имя файла:').grid(row=4, column=0, sticky='w', pady=(10,0))
    fname_entry = tk.Entry(frm, textvariable=filename_var)
    fname_entry.grid(row=5, column=0, sticky='ew', padx=(0,20))
    tk.Label(frm, text='Расширение').grid(row=4, column=1, sticky='e', pady=(10,0), padx=(0,5))
    ext_var = tk.StringVar(value='.txt')
    ext_options = ['.txt', '.srt', '.ass', '.docx']
    ext_menu = tk.OptionMenu(frm, ext_var, *ext_options)
    ext_menu.config(width=12, height=1)
    ext_menu.grid(row=5, column=1, sticky='ew', padx=(0,20))

    # --- Выбор дорожки субтитров ---
    track_var = tk.StringVar(value='Не выбрано')
    track_options = []
    track_menu = None
    track_label = None

    def update_tracks(*args):
        nonlocal track_options, track_menu, track_label
        if not mkv_path.get():
            track_options = []
            if track_menu:
                track_menu.grid_remove()
            if track_label:
                track_label.grid_remove()
            track_var.set('Не выбрано')
            track_label = tk.Label(frm, text='Дорожка субтитров:')
            track_label.grid(row=7, column=0, sticky='w', padx=(0,5), pady=(10,0))
            track_menu = tk.OptionMenu(frm, track_var, 'Не выбрано')
            track_menu.config(width=12)
            track_menu.grid(row=8, column=0, sticky='w', padx=(0,5))
            extract_btn.grid(row=9, column=0, columnspan=2, sticky='e', padx=(10,0), pady=(15,10))
            return
        ext = os.path.splitext(mkv_path.get())[1].lower()
        try:
            if ext == '.mkv':
                result = subprocess.run(
                    ['mkvmerge', '-i', mkv_path.get()],
                    capture_output=True, text=True, encoding='utf-8', errors='replace'
                )
                lines = result.stdout.splitlines()
                track_options = [line for line in lines if 'subtitles' in line]
            else:
                track_options = []
        except Exception:
            track_options = []
        if track_menu:
            track_menu.grid_remove()
        if track_label:
            track_label.grid_remove()
        if track_options:
            display_options = [f"{i+1}: {line}" for i, line in enumerate(track_options)]
            max_len = max([len(opt) for opt in display_options]) if display_options else 10
            track_var.set(display_options[0])
            track_label = tk.Label(frm, text='Дорожка субтитров:')
            track_label.grid(row=7, column=0, sticky='w', padx=(0,5), pady=(10,0))
            track_menu = tk.OptionMenu(frm, track_var, *display_options)
            track_menu.config(width=max_len)
            track_menu.grid(row=8, column=0, sticky='w', padx=(0,5))
            extract_btn.grid(row=9, column=0, columnspan=2, sticky='e', padx=(10,0), pady=(15,10))
        else:
            track_var.set('Не выбрано')
            track_label = tk.Label(frm, text='Дорожка субтитров:')
            track_label.grid(row=7, column=0, sticky='w', padx=(0,5), pady=(10,0))
            track_menu = tk.OptionMenu(frm, track_var, 'Не выбрано')
            track_menu.config(width=12)
            track_menu.grid(row=8, column=0, sticky='w', padx=(0,5))
            extract_btn.grid(row=9, column=0, columnspan=2, sticky='e', padx=(10,0), pady=(15,10))

    mkv_path.trace_add('write', update_tracks)

    filename_var.trace_add('write', update_output_path)
    output_dir.trace_add('write', update_output_path)
    ext_var.trace_add('write', update_output_path)

    extract_btn = tk.Button(frm, text='Извлечь', command=run_extract, bg='#4CAF50', fg='white', width=12, height=1)
    extract_btn.grid(row=9, column=0, columnspan=2, sticky='e', padx=(10,0), pady=(15,10))

    mkv_entry.xview_moveto(0)
    outdir_entry.xview_moveto(0)
    fname_entry.xview_moveto(0)

    root.mainloop()

if __name__ == '__main__':
    main()

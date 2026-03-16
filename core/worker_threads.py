import os, subprocess, shutil
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp

class VideoDownloaderThread(QThread):
    progress_signal = pyqtSignal(object)
    finished_signal = pyqtSignal(str)

    def __init__(self, url, output_path, ffmpeg_path):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        strategies = [
            ("Без куков", {}),
            ("Файл cookies.txt", {'cookiefile': 'cookies.txt'}),
            ("Chrome", {'cookiesfrombrowser': ('chrome', 'default')}),
            ("Edge", {'cookiesfrombrowser': ('edge', 'default')}),
            ("Firefox", {'cookiesfrombrowser': ('firefox', 'default')}),
            ("Opera", {'cookiesfrombrowser': ('opera', 'default')}),
            ("Yandex", {'cookiesfrombrowser': ('yandex', 'default')}),
            ("Vivaldi", {'cookiesfrombrowser': ('vivaldi', 'default')})
        ]

        base_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': self.output_path,
            'ffmpeg_location': self.ffmpeg_path,
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'ignoreerrors': True,  
            'quiet': True,        
            'no_warnings': True
        }

        for name, cookie_opt in strategies:
            if 'cookiefile' in cookie_opt and not os.path.exists(cookie_opt['cookiefile']):
                continue
            self.progress_signal.emit(f"Попытка: {name}...")
            current_opts = {**base_opts, **cookie_opt}
            try:
                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    result = ydl.download([self.url])
                if os.path.exists(self.output_path):
                    f_size = os.path.getsize(self.output_path)
                    if f_size > 50000: # Больше 50 КБ - считаем успехом
                        self.progress_signal.emit(f"Успешно скачано через {name}!")
                        self.finished_signal.emit(self.output_path)
                        return
                    else:
                        os.remove(self.output_path)
            
            except Exception as e:
                self.progress_signal.emit(f"Метод {name} не сработал.")
                continue

        # Если цикл закончился и мы не вышли через return
        self.progress_signal.emit("Не удалось скачать видео ни одним из способов.")
        self.finished_signal.emit(None)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%').replace('%','').strip()
            try:
                p_val = int(float(p_str))
            except:
                p_val = 0
            
            self.progress_signal.emit({
                'percent': p_val,
                'speed': d.get('_speed_str', '---'),
                'eta': d.get('_eta_str', '---')
            })

class VideoConverterThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, input_p, output_p, ffmpeg_p):
        super().__init__()
        self.input_p = input_p
        self.output_p = output_p
        self.ffmpeg_p = ffmpeg_p

    def run(self):
        try:
            cmd = [
                self.ffmpeg_p, "-y", "-i", self.input_p, 
                "-c", "copy", # Сначала пробуем без перекодирования (очень быстро)
                self.output_p
            ]
            
            result = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode != 0:
                cmd_full = [
                    self.ffmpeg_p, "-y", "-i", self.input_p, 
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    self.output_p
                ]
                subprocess.run(cmd_full, creationflags=subprocess.CREATE_NO_WINDOW)
                
            self.finished_signal.emit(self.output_p)
        except:
            self.finished_signal.emit(self.input_p)

# ты лох
        
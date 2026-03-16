import os, shutil
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
from susik_media import SusikMedia  # Импортируем нашу библиотеку

class VideoDownloaderThread(QThread):
    progress_signal = pyqtSignal(object)
    finished_signal = pyqtSignal(str)

    def __init__(self, url, output_path): # Убрали ffmpeg_path
        super().__init__()
        self.url = url
        self.output_path = output_path

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

        # Настройки для yt_dlp. ВАЖНО: Мы убираем ffmpeg_location
        base_opts = {
            'format': 'best', # Берем лучший готовый формат (чтобы избежать нужды в ffmpeg для склейки)
            'outtmpl': self.output_path,
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
                    ydl.download([self.url])
                
                if os.path.exists(self.output_path):
                    f_size = os.path.getsize(self.output_path)
                    if f_size > 50000:
                        self.progress_signal.emit(f"Успешно скачано через {name}!")
                        self.finished_signal.emit(self.output_path)
                        return
                    else:
                        os.remove(self.output_path)
            
            except Exception as e:
                self.progress_signal.emit(f"Метод {name} не сработал.")
                continue

        self.progress_signal.emit("Не удалось скачать видео.")
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

    def __init__(self, input_p, output_p): # Убрали ffmpeg_p
        super().__init__()
        self.input_p = input_p
        self.output_p = output_p

    def run(self):
        """Здесь мы полностью заменили subprocess на SusikMedia."""
        try:
            # Инициализируем наш декодер
            worker = SusikMedia(self.input_p)
            
            # Попытка быстрой конвертации (логика была -c copy)
            success = worker.process_conversion(self.output_p, copy_codec=True)
            
            if not success:
                # Если не вышло, пробуем полное перекодирование (аналог libx264)
                worker.process_conversion(self.output_p, copy_codec=False)
                
            self.finished_signal.emit(self.output_p)
        except Exception:
            self.finished_signal.emit(self.input_p)
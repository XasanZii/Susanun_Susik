import os
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
from susik_media import SusikMedia

class VideoDownloaderThread(QThread):
    # Теперь передаем только словари для единообразия
    progress_signal = pyqtSignal(dict) 
    finished_signal = pyqtSignal(str)

    def __init__(self, url, download_dir):
        super().__init__()
        self.url = url
        self.download_dir = download_dir

    def run(self):
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)

        # Выбираем формат, не требующий склейки внешним ffmpeg
        base_opts = {
            'format': 'best[ext=mp4]/best', 
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if not info:
                    raise Exception("Не удалось получить данные о видео")
                
                title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
                ext = info.get('ext', 'mp4')
                final_path = os.path.join(self.download_dir, f"{title}.{ext}")
                
                ydl.params['outtmpl'] = final_path
                ydl.download([self.url])

            if os.path.exists(final_path):
                self.finished_signal.emit(final_path)
                return

        except Exception as e:
            # Отправляем ошибку в виде словаря, чтобы UI не "сломался"
            self.progress_signal.emit({'status': 'error', 'msg': str(e)})
        
        self.finished_signal.emit(None)

    def progress_hook(self, d):
        # Проверка типа d предотвращает ошибку "string indices must be integers"
        if not isinstance(d, dict):
            return

        if d.get('status') == 'downloading':
            p_str = d.get('_percent_str', '0%').replace('%','').strip()
            try:
                p_val = int(float(p_str))
                self.progress_signal.emit({
                    'status': 'downloading',
                    'percent': p_val,
                    'speed': d.get('_speed_str', '---'),
                    'eta': d.get('_eta_str', '---')
                })
            except (ValueError, TypeError):
                pass

class VideoConverterThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, input_p, output_p):
        super().__init__()
        self.input_p = input_p
        self.output_p = output_p

    def run(self):
        try:
            worker = SusikMedia(self.input_p)
            # Пытаемся быстро перепаковать
            success = worker.process_conversion(self.output_p, copy_codec=True)
            if not success:
                # Если не вышло, пробуем полное перекодирование
                worker.process_conversion(self.output_p, copy_codec=False)
            self.finished_signal.emit(self.output_p)
        except Exception:
            self.finished_signal.emit(self.input_p)
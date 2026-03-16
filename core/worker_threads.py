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

class VideoDownloaderThread(QThread):
    progress_signal = pyqtSignal(object)
    finished_signal = pyqtSignal(str)

    def __init__(self, url, download_dir): # Теперь передаем только папку
        super().__init__()
        self.url = url
        self.download_dir = download_dir

    def run(self):
        # Опции теперь не включают жесткий outtmpl, мы его сформируем динамически
        base_opts = {
            'format': 'best',
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                # 1. Сначала получаем инфо о видео без скачивания
                info = ydl.extract_info(self.url, download=False)
                title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
                ext = info.get('ext', 'mp4')
                
                # 2. Формируем полный путь
                final_filename = f"{title}.{ext}"
                final_path = os.path.join(self.download_dir, final_filename)
                
                # 3. Обновляем настройки и качаем
                ydl.params['outtmpl'] = final_path
                ydl.download([self.url])

            if os.path.exists(final_path):
                self.finished_signal.emit(final_path)
                return

        except Exception as e:
            self.progress_signal.emit(f"Ошибка: {str(e)}")
        
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
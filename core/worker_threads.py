import os, yt_dlp, re
from PyQt6.QtCore import QThread, pyqtSignal
from susik_media import SusikMedia

class VideoDownloaderThread(QThread):
    progress_signal = pyqtSignal(dict) 
    finished_signal = pyqtSignal(str)

    def __init__(self, url, download_dir, use_conversion=True):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        self.use_conversion = use_conversion

    def run(self):
        try:
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir, exist_ok=True)

            self.progress_signal.emit({'status': 'processing', 'msg': 'Сбор информации о видео...'})

            with yt_dlp.YoutubeDL({'quiet': True, 'nocheckcertificate': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
            
            # Временный и финальный пути
            temp_path = os.path.join(self.download_dir, f"raw_{title}.mp4")
            final_path = os.path.join(self.download_dir, f"{title}.mp4")

            self.progress_signal.emit({'status': 'processing', 'msg': f"Название: {title}"})

            opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': temp_path,
                'progress_hooks': [self.progress_hook],
                'quiet': True,
                'nocheckcertificate': True
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])

            if self.use_conversion:
                self.progress_signal.emit({'status': 'processing', 'msg': 'Финализация через Susik Engine...'})
                processor = SusikMedia(temp_path)
                # Remuxing в .mp4
                if processor.process_conversion(final_path, copy_codec=True):
                    if os.path.exists(temp_path): os.remove(temp_path)
                    self.finished_signal.emit(final_path)
                else:
                    self.progress_signal.emit({'status': 'error', 'msg': 'Ошибка SusikMedia. Используем оригинал.'})
                    self.finished_signal.emit(temp_path)
            else:
                if os.path.exists(temp_path):
                    os.rename(temp_path, final_path)
                self.finished_signal.emit(final_path)

        except Exception as e:
            self.progress_signal.emit({'status': 'error', 'msg': f"Сбой потока: {str(e)}"})
            self.finished_signal.emit("")

    def progress_hook(self, d):
        if d.get('status') == 'downloading':
            p_str = d.get('_percent_str', '0%')
            # Очистка от ANSI кодов
            p_str = re.sub(r'\x1b\[[0-9;]*m', '', p_str).replace('%', '').strip()
            try:
                self.progress_signal.emit({
                    'status': 'downloading',
                    'percent': int(float(p_str)),
                    'speed': d.get('_speed_str', '---'),
                    'eta': d.get('_eta_str', '---')
                })
            except: pass
# core/worker_threads.py

import os
import re
import yt_dlp

from PyQt6.QtCore import QThread, pyqtSignal
from core.workers import MediaConverter


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

            os.makedirs(self.download_dir, exist_ok=True)

            self.progress_signal.emit({
                "status": "processing",
                "msg": "Получение информации о видео..."
            })

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": os.path.join(self.download_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [self.progress_hook],
                "quiet": True,
                "nocheckcertificate": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(self.url, download=True)

                # реальный путь скачанного файла
                downloaded_file = ydl.prepare_filename(info)

            self.progress_signal.emit({
                "status": "processing",
                "msg": f"Скачано: {os.path.basename(downloaded_file)}"
            })

            # -----------------------------------------
            # КОНВЕРТАЦИЯ
            # -----------------------------------------

            if self.use_conversion:

                name = os.path.splitext(os.path.basename(downloaded_file))[0]
                final_path = os.path.join(self.download_dir, f"{name}.mp4")

                self.progress_signal.emit({
                    "status": "processing",
                    "msg": "Конвертация через SusikMedia..."
                })

                converter = MediaConverter(downloaded_file)

                ok, result = converter.process(final_path, copy_codec=True)

                if ok:

                    try:
                        os.remove(downloaded_file)
                    except:
                        pass

                    self.finished_signal.emit(final_path)

                else:

                    self.progress_signal.emit({
                        "status": "error",
                        "msg": f"Ошибка конвертации: {result}"
                    })

                    self.finished_signal.emit(downloaded_file)

            else:

                self.finished_signal.emit(downloaded_file)

        except Exception as e:

            self.progress_signal.emit({
                "status": "error",
                "msg": str(e)
            })

            self.finished_signal.emit("")


    def progress_hook(self, d):

        if d.get("status") == "downloading":

            percent = d.get("_percent_str", "0%")
            percent = re.sub(r"\x1b\[[0-9;]*m", "", percent)
            percent = percent.replace("%", "").strip()

            try:

                self.progress_signal.emit({
                    "status": "downloading",
                    "percent": int(float(percent)),
                    "speed": d.get("_speed_str", "---"),
                    "eta": d.get("_eta_str", "---")
                })

            except:
                pass


        if d.get("status") == "finished":

            self.progress_signal.emit({
                "status": "processing",
                "msg": "Скачивание завершено"
            })
# core/worker_threads.py
import os
import re
import traceback
import yt_dlp

from PyQt6.QtCore import QThread, pyqtSignal
from core.workers import MediaConverter


class VideoDownloaderThread(QThread):
    """
    Поток скачивания + (опционально) конвертации.
    Гарантирует, что GUI получит реальный путь к скачанному/сконвертированному файлу.
    """

    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(str)

    def __init__(self, url: str, download_dir: str, use_conversion: bool = True, cookies_path: str | None = None):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        self.use_conversion = use_conversion
        self.cookies_path = cookies_path

    def run(self):
        try:
            os.makedirs(self.download_dir, exist_ok=True)

            self.progress_signal.emit({"status": "processing", "msg": "Инициализация скачивания..."})

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": os.path.join(self.download_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [self.progress_hook],
                "quiet": True,
                "nocheckcertificate": True,
                # for debugging, you can set verbose True temporarily
                # "verbose": True,
            }

            if self.cookies_path:
                ydl_opts["cookiefile"] = self.cookies_path

            downloaded_file = ""
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # extract_info with download=True will download the file synchronously here
                info = ydl.extract_info(self.url, download=True)
                # получаем реальное имя (с расширением)
                downloaded_file = ydl.prepare_filename(info)

            # Иногда файл может иметь нестандартное расширение или оставаться с .part — проверим
            if not os.path.exists(downloaded_file):
                # Попробуем найти файл по префиксу (учёт .part/.tmp и возможных других расширений)
                base = os.path.splitext(os.path.basename(downloaded_file))[0]
                candidates = [f for f in os.listdir(self.download_dir) if f.startswith(base)]
                if candidates:
                    # выберем самый большой по размеру (скорее всего финальный)
                    candidates_full = [os.path.join(self.download_dir, f) for f in candidates]
                    candidates_full.sort(key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0, reverse=True)
                    downloaded_file = candidates_full[0]
                else:
                    self.progress_signal.emit({"status": "error", "msg": f"Файл не найден после скачивания: {downloaded_file}"})
                    self.finished_signal.emit("")
                    return

            self.progress_signal.emit({"status": "processing", "msg": f"Скачано: {os.path.basename(downloaded_file)}"})

            # Конвертация через SusikMedia (опционально)
            if self.use_conversion:
                name = os.path.splitext(os.path.basename(downloaded_file))[0]
                final_path = os.path.join(self.download_dir, f"{name}.mp4")

                self.progress_signal.emit({"status": "processing", "msg": "Запуск конвертации (SusikMedia)..."})
                converter = MediaConverter(downloaded_file)
                ok, result = converter.process(final_path, copy_codec=True)

                if ok:
                    # удаляем оригинал (если он отличается по имени)
                    try:
                        if os.path.abspath(downloaded_file) != os.path.abspath(final_path) and os.path.exists(downloaded_file):
                            os.remove(downloaded_file)
                    except Exception:
                        pass
                    self.progress_signal.emit({"status": "done", "msg": f"Готово: {os.path.basename(final_path)}"})
                    self.finished_signal.emit(final_path)
                else:
                    # если конвертация упала — логируем и возвращаем оригинал
                    self.progress_signal.emit({"status": "error", "msg": f"Ошибка конвертации: {result}"})
                    self.finished_signal.emit(downloaded_file)
            else:
                self.progress_signal.emit({"status": "done", "msg": f"Готово: {os.path.basename(downloaded_file)}"})
                self.finished_signal.emit(downloaded_file)

        except Exception as e:
            tb = traceback.format_exc()
            self.progress_signal.emit({"status": "error", "msg": f"Сбой: {e}\n{tb}"})
            self.finished_signal.emit("")

    def progress_hook(self, d: dict):
        # d can contain status: downloading, finished, error...
        st = d.get("status")
        if st == "downloading":
            percent = d.get("_percent_str", "0%")
            percent = re.sub(r"\x1b\[[0-9;]*m", "", percent).replace("%", "").strip()
            try:
                self.progress_signal.emit({
                    "status": "downloading",
                    "percent": int(float(percent)),
                    "speed": d.get("_speed_str", "---"),
                    "eta": d.get("_eta_str", "---")
                })
            except Exception:
                # не критично — просто шлём прогресс без процентов
                self.progress_signal.emit({
                    "status": "downloading",
                    "percent": 0,
                    "speed": d.get("_speed_str", "---"),
                    "eta": d.get("_eta_str", "---")
                })
        elif st == "finished":
            self.progress_signal.emit({"status": "processing", "msg": "Завершено скачивание, финализация..."})
        elif st == "error":
            self.progress_signal.emit({"status": "error", "msg": d.get("error", "Неизвестная ошибка при скачивании")})
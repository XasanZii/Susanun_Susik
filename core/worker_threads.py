# core/worker_threads.py
import os
import re
import traceback
import yt_dlp
import requests
from urllib.parse import urlparse

from PyQt6.QtCore import QThread, pyqtSignal
from core.workers import MediaConverter


def check_site_accessibility(url: str, timeout: int = 5) -> dict:
    """
    Проверяет доступность сайта по URL.
    
    Args:
        url: URL для проверки
        timeout: Таймаут в секундах
        
    Returns:
        dict: {"accessible": bool, "status_code": int|None, "error": str|None}
    """
    try:
        # Извлекаем домен из URL
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        response = requests.get(domain, timeout=timeout, allow_redirects=True)
        
        if response.ok:  # 200-299
            return {
                "accessible": True,
                "status_code": response.status_code,
                "error": None,
                "message": f"Сайт доступен. Статус: {response.status_code}"
            }
        else:
            return {
                "accessible": False,
                "status_code": response.status_code,
                "error": f"HTTP Error {response.status_code}",
                "message": f"Сайт вернул ошибку. Статус: {response.status_code}"
            }
    except requests.exceptions.Timeout:
        return {
            "accessible": False,
            "status_code": None,
            "error": "Timeout - сервер не ответил",
            "message": f"Таймаут подключения ({timeout}с)"
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "accessible": False,
            "status_code": None,
            "error": f"Connection Error: {str(e)}",
            "message": f"Не удалось подключиться к сайту"
        }
    except Exception as e:
        return {
            "accessible": False,
            "status_code": None,
            "error": str(e),
            "message": f"Ошибка проверки доступности: {str(e)}"
        }


class VideoDownloaderThread(QThread):
    """
    Поток скачивания + (опционально) конвертации.
    Гарантирует, что GUI получит реальный путь к скачанному/сконвертированному файлу.
    """

    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(str)

    def __init__(self, url: str, download_dir: str, use_conversion: bool = True, cookies_path: str | None = None, output_format: str = "mp4", resolution_quality: str = "best", use_browser: str | None = None):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        self.use_conversion = use_conversion
        self.cookies_path = cookies_path
        self.output_format = output_format.lower()  # mp4, mp3, wav, aac, ogg, webm, mkv
        self.resolution_quality = resolution_quality  # best, 1080, 720, 480, 360, 240
        self.use_browser = use_browser  # None для всех браузеров, или конкретный браузер
        self.stop_download = False  # Флаг для остановки загрузки

    def run(self):
        try:
            os.makedirs(self.download_dir, exist_ok=True)

            self.progress_signal.emit({"status": "processing", "msg": "Инициализация скачивания..."})

            # Проверяем доступность сайта перед загрузкой
            self.progress_signal.emit({"status": "processing", "msg": "🔍 Проверка доступности сайта..."})
            site_check = check_site_accessibility(self.url)
            
            if site_check["accessible"]:
                self.progress_signal.emit({"status": "processing", "msg": f"✓ {site_check['message']}"})
            else:
                # Предупреждение, но не критическая ошибка - пробуем продолжить
                self.progress_signal.emit({"status": "processing", "msg": f"⚠️ {site_check['message']} - пытаюсь загрузить видео..."})

            # Выбрать формат видео на основе разрешения с fallback вариантами
            if self.resolution_quality == "best":
                # Для лучшего качества: пробуем video+audio, потом просто best
                format_spec = "bestvideo+bestaudio/best"
            else:
                height = int(self.resolution_quality)
                # Для конкретного разрешения: пробуем video+audio с высотой, потом best с высотой, потом просто best
                format_spec = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"

            ydl_opts = {
                "format": format_spec,
                "outtmpl": os.path.join(self.download_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [self.progress_hook],
                "quiet": True,
                "nocheckcertificate": True,
                "socket_timeout": 30,
            }

            # Настроить браузер для автоматического получения куков
            if self.use_browser:
                # Конкретный браузер
                ydl_opts["cookies_from_browser"] = (self.use_browser,)
            else:
                # Все поддерживаемые браузеры
                ydl_opts["cookies_from_browser"] = (
                    "chrome", "edge", "firefox", "opera", "vivaldi", "yandex", "zen"
                )

            if self.cookies_path:
                ydl_opts["cookiefile"] = self.cookies_path
                ydl_opts.pop("cookies_from_browser", None)  # Исключаем auto-cookies если указан файл

            downloaded_file = ""
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Проверка флага остановки в начале
                if self.stop_download:
                    self.progress_signal.emit({"status": "error", "msg": "Загрузка отменена"})
                    self.finished_signal.emit("")
                    return
                
                try:
                    # extract_info with download=True will download the file synchronously here
                    info = ydl.extract_info(self.url, download=True)
                    # получаем реальное имя (с расширением)
                    downloaded_file = ydl.prepare_filename(info)
                except Exception as e:
                    # Если ошибка связана с неподдерживаемым форматом, пробуем fallback
                    if "format" in str(e).lower() or "not available" in str(e).lower():
                        self.progress_signal.emit({"status": "processing", "msg": f"📌 Ошибка формата на видео - используем fallback вариант (лучший доступный)..."})
                        # Обновляем опции с более простым форматом
                        ydl_opts["format"] = "best"
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl_fallback:
                            info = ydl_fallback.extract_info(self.url, download=True)
                            downloaded_file = ydl_fallback.prepare_filename(info)
                    elif "unable" in str(e).lower() or "connection" in str(e).lower():
                        # Проблема с подключением - проверяем доступность сайта
                        site_check = check_site_accessibility(self.url)
                        if not site_check["accessible"]:
                            error_msg = f"❌ Проблема подключения: {site_check['message']}\nПопробуйте позже или проверьте сетевое соединение."
                            self.progress_signal.emit({"status": "error", "msg": error_msg})
                            self.finished_signal.emit("")
                            return
                        else:
                            raise
                    else:
                        raise

            # Проверка флага остановки после скачивания
            if self.stop_download:
                if os.path.exists(downloaded_file):
                    try:
                        os.remove(downloaded_file)
                    except Exception:
                        pass
                self.progress_signal.emit({"status": "error", "msg": "Загрузка отменена"})
                self.finished_signal.emit("")
                return

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
                
                # Определить параметры конвертации в зависимости от формата
                audio_only_formats = {"mp3", "wav", "aac", "ogg"}
                is_audio_only = self.output_format in audio_only_formats
                
                final_path = os.path.join(self.download_dir, f"{name}.{self.output_format}")
                self.progress_signal.emit({"status": "processing", "msg": f"Конвертация в {self.output_format.upper()}..."})
                
                # Проверка флага остановки перед конвертацией
                if self.stop_download:
                    if os.path.exists(downloaded_file):
                        try:
                            os.remove(downloaded_file)
                        except Exception:
                            pass
                    self.progress_signal.emit({"status": "error", "msg": "Загрузка отменена"})
                    self.finished_signal.emit("")
                    return
                
                # Сначала пробуем безопасное копирование кодека
                converter = MediaConverter(downloaded_file)
                ok, result = converter.process(final_path, copy_codec=True, audio_only=is_audio_only)

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
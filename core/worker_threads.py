# core/worker_threads.py
import os
import re
import traceback
import yt_dlp
import requests
from urllib.parse import urlparse, parse_qs

from PyQt6.QtCore import QThread, pyqtSignal
from core.workers import MediaConverter
from core.link_extractor import LinkExtractor

try:
    from pytubefix import YouTube
    PYTUBEFIX_AVAILABLE = True
except ImportError:
    PYTUBEFIX_AVAILABLE = False


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


def is_youtube_url(url: str) -> bool:
    """Проверяет, является ли URL YouTube ссылкой."""
    return bool(re.search(r'(youtube\.com|youtu\.be)', url, re.IGNORECASE))


def extract_video_id(url: str) -> str | None:
    """Извлекает video ID из YouTube URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?.*v=([^&]+))',
        r'(?:youtu\.be\/([^?]+))',
        r'(?:youtube\.com\/embed\/([^?]+))',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


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

            # 🔥 Специальная обработка YouTube через pytubefix (без ошибок о JS runtime и ботах)
            if is_youtube_url(self.url) and PYTUBEFIX_AVAILABLE:
                self._download_youtube_pytubefix()
                return

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
                "postprocessor_args": {
                    "ffmpeg": ["-c:v", "copy", "-c:a", "aac"]  # Копируем видео, переко­дируем аудио если нужно
                },
                "merge_output_format": "mp4",  # По умолчанию объединяем в MP4
                "no_warnings": False,
                "verbose": False,
                "extract_flat": False,
                "ignoreerrors": False,
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
                    error_str = str(e)
                    
                    # 🔥 FALLBACK: Если YouTube требует подтверждение что не бот, пробуем pytubefix
                    if ("Sign in to confirm you're not a bot" in error_str or 
                        "bot" in error_str.lower() and is_youtube_url(self.url)):
                        self.progress_signal.emit({
                            "status": "processing",
                            "msg": "yt-dlp требует подтверждение бота. Пытаюсь pytubefix..."
                        })
                        if PYTUBEFIX_AVAILABLE:
                            self._download_youtube_pytubefix()
                            return
                        else:
                            error_msg = ("YouTube требует подтверждение что не бот.\n"
                                       "Решение:\n"
                                       "1. Выберите браузер в поле 'Браузер:'\n"
                                       "2. Нажмите 'Найти видео (Selenium)'\n"
                                       "3. Скачивайте с Vimeo/Facebook (нет bot-detection)")
                            self.progress_signal.emit({"status": "error", "msg": error_msg})
                            self.finished_signal.emit("")
                            return
                    
                    # Если ошибка связана с неподдерживаемым форматом, пробуем fallback
                    if "format" in error_str.lower() or "not available" in error_str.lower():
                        self.progress_signal.emit({"status": "processing", "msg": f"Ошибка формата на видео - используем fallback вариант (лучший доступный)..."})
                        # Обновляем опции с более простым форматом
                        ydl_opts["format"] = "best"
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl_fallback:
                            info = ydl_fallback.extract_info(self.url, download=True)
                            downloaded_file = ydl_fallback.prepare_filename(info)
                    elif "unable" in error_str.lower() or "connection" in error_str.lower():
                        # Проблема с подключением - проверяем доступность сайта
                        site_check = check_site_accessibility(self.url)
                        if not site_check["accessible"]:
                            error_msg = f"Проблема подключения: {site_check['message']}\nПопробуйте позже или проверьте сетевое соединение."
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

            # Проверка файла перед обработкой
            if not os.path.exists(downloaded_file):
                self.progress_signal.emit({"status": "error", "msg": f"❌ Файл не найден после скачивания: {downloaded_file}"})
                self.finished_signal.emit("")
                return
            
            file_size = os.path.getsize(downloaded_file)
            if file_size == 0:
                self.progress_signal.emit({"status": "error", "msg": f"❌ Файл пуст (0 байт): {os.path.basename(downloaded_file)}"})
                try:
                    os.remove(downloaded_file)
                except:
                    pass
                self.finished_signal.emit("")
                return

            # Обработка файлов с неизвестным расширением (.unknown_video)
            if downloaded_file.endswith('.unknown_video'):
                self.progress_signal.emit({"status": "processing", "msg": "🔍 Определение формата видео..."})
                # Пробуем определить правильный формат по содержимому файла
                actual_file = self._detect_video_format(downloaded_file)
                if actual_file and actual_file != downloaded_file:
                    downloaded_file = actual_file
                    self.progress_signal.emit({"status": "processing", "msg": f"✓ Формат определён: {os.path.basename(downloaded_file)}"})
                else:
                    # Если не удалось определить, переименуем в .mp4 по умолчанию
                    renamed_file = downloaded_file.replace('.unknown_video', '.mp4')
                    try:
                        os.rename(downloaded_file, renamed_file)
                        downloaded_file = renamed_file
                        self.progress_signal.emit({"status": "processing", "msg": f"ℹ Файл переименован в .mp4: {os.path.basename(downloaded_file)}"})
                    except Exception as e:
                        self.progress_signal.emit({"status": "error", "msg": f"Не удалось переименовать файл: {e}"})
                        self.finished_signal.emit("")
                        return

            # Конвертация через SusikMedia (опционально)
            if self.use_conversion:
                name = os.path.splitext(os.path.basename(downloaded_file))[0]
                
                # Определить параметры конвертации в зависимости от формата
                audio_only_formats = {"mp3", "wav", "aac", "ogg"}
                is_audio_only = self.output_format in audio_only_formats
                
                final_path = os.path.join(self.download_dir, f"{name}.{self.output_format}")
                
                # Если выходной файл уже существует, удалим его
                if os.path.exists(final_path):
                    try:
                        os.remove(final_path)
                    except Exception as e:
                        self.progress_signal.emit({"status": "warning", "msg": f"⚠️ Не удалось удалить старый файл: {e}"})
                
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
                    
                    # Проверяем, что файл успешно создан
                    if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
                        self.progress_signal.emit({"status": "done", "msg": f"✅ Готово: {os.path.basename(final_path)}"})
                        self.finished_signal.emit(final_path)
                    else:
                        self.progress_signal.emit({"status": "error", "msg": f"⚠️ Файл не создан или пуст"})
                        # Возвращаем оригинальный файл если конвертированный не создалась
                        if os.path.exists(downloaded_file):
                            self.progress_signal.emit({"status": "warning", "msg": f"Возвращаю оригинальный файл: {os.path.basename(downloaded_file)}"})
                            self.finished_signal.emit(downloaded_file)
                        else:
                            self.finished_signal.emit("")
                else:
                    # если конвертация упала — ОБЯЗАТЕЛЬНО сохраняем оригинал
                    error_msg = result
                    self.progress_signal.emit({"status": "error", "msg": f"❌ Ошибка конвертации: {error_msg}"})
                    
                    # Агрессивная стратегия спасения: пробуем все возможные способы сохранить файл
                    fallback_saved = False
                    
                    # Шаг 1: Убедимся, что файл существует
                    if not os.path.exists(downloaded_file):
                        self.progress_signal.emit({"status": "error", "msg": f"Оригинальный файл не найден: {downloaded_file}"})
                        self.finished_signal.emit("")
                        return
                    
                    # Шаг 2: Проверим размер файла
                    try:
                        file_size = os.path.getsize(downloaded_file)
                        if file_size == 0:
                            self.progress_signal.emit({"status": "error", "msg": f"Файл пуст (0 байт) - конвертация невозможна"})
                            self.finished_signal.emit("")
                            return
                    except Exception as e:
                        self.progress_signal.emit({"status": "error", "msg": f"Не удалось получить размер файла: {e}"})
                        self.finished_signal.emit("")
                        return
                    
                    # Шаг 3: Переименуем если нужно
                    if downloaded_file.endswith(('.unknown_video', '.tmp')):
                        fallback_name = downloaded_file.rsplit('.', 1)[0] + '.mp4'
                        try:
                            if os.path.exists(fallback_name):
                                os.remove(fallback_name)
                            os.rename(downloaded_file, fallback_name)
                            downloaded_file = fallback_name
                            self.progress_signal.emit({"status": "processing", "msg": f"Файл переименован: {os.path.basename(downloaded_file)}"})
                        except Exception as e:
                            self.progress_signal.emit({"status": "warning", "msg": f"⚠️ Не удалось переименовать .unknown_video: {e}\nПопытка сохранить как есть..."})
                            # Продолжаем с текущим именем
                    
                    # Шаг 4: Финальная проверка перед возвратом
                    if os.path.exists(downloaded_file) and os.path.getsize(downloaded_file) > 0:
                        self.progress_signal.emit({"status": "success", "msg": f"✅ Файл сохранён (без конвертации): {os.path.basename(downloaded_file)}"})
                        self.finished_signal.emit(downloaded_file)
                        fallback_saved = True
                    
                    # Если даже это не сработало
                    if not fallback_saved:
                        self.progress_signal.emit({"status": "error", "msg": f"Не удалось сохранить файл"})
                        self.finished_signal.emit("")
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

    def _detect_video_format(self, unknown_file: str) -> str:
        """
        Определяет правильный формат видео по магическим числам (magic bytes).
        ГАРАНТИРУЕТ, что файл будет переименован в известный формат.
        
        Args:
            unknown_file: Путь к файлу с расширением .unknown_video
            
        Returns:
            Переименованный файл с известным расширением или .mp4 в крайнем случае
        """
        # Сначала проверим, что файл существует
        if not os.path.exists(unknown_file):
            return unknown_file
            
        try:
            # Магические числа (magic bytes) для разных видеоформатов
            format_signatures = {
                b'\x00\x00\x00\x20ftyp': 'mp4',      # MP4/M4A
                b'\x00\x00\x00\x18ftyp': 'mp4',
                b'\x00\x00\x00\x28ftyp': 'mp4',
                b'ftyp': 'mp4',
                b'\x1a\x45\xdf\xa3': 'mkv',          # Matroska
                b'RIFF': 'avi',                       # AVI/WAV
                b'ID3': 'mp3',                        # MP3
                b'\xff\xfb': 'mp3',                   # MP3 (MPEG-1 Layer III)
                b'\xff\xfa': 'mp3',                   # MP3 (MPEG-2 Layer III)
                b'\x1f\x8b': 'gz',                    # gzip (иногда используется)
                b'BM': 'bmp',
                b'\x89PNG': 'png',
                b'\xff\xd8\xff': 'jpg',
                b'Ogg': 'ogv',                        # Ogg Vorbis/Theora
                b'WEBP': 'webp',
                b'\x00\x00\x01\x00': 'mov',           # MOV/QuickTime
                b'moov': 'mov',
                b'\x00\x00\x01\xB3': 'mpg',           # MPEG-1 Video
            }
            
            # Читаем первые 32 байта файла для определения формата
            with open(unknown_file, 'rb') as f:
                header = f.read(32)
            
            # Проверяем сигнатуры
            for signature, ext in format_signatures.items():
                if header.startswith(signature):
                    # Переименовываем файл
                    new_file = unknown_file.replace('.unknown_video', f'.{ext}')
                    try:
                        if os.path.exists(new_file):
                            os.remove(new_file)  # Удалим старый файл с таким именем если существует
                        os.rename(unknown_file, new_file)
                        return new_file
                    except Exception as e:
                        self.progress_signal.emit({"status": "warning", "msg": f"⚠️ Не удалось переименовать в .{ext}: {e}"})
                        # Продолжаем и попробуем mp4
                        break
            
            # Если не определили по magic bytes, пробуем ffprobe для определения
            try:
                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1', unknown_file],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    # ffprobe смог прочитать файл - этовидимо валидный видеофайл
                    self.progress_signal.emit({"status": "processing", "msg": "ℹ️ Формат определен через ffprobe"})
                    # Переименуем в mp4 по умолчанию
                    new_file = unknown_file.replace('.unknown_video', '.mp4')
                    try:
                        if os.path.exists(new_file):
                            os.remove(new_file)
                        os.rename(unknown_file, new_file)
                        return new_file
                    except Exception as e:
                        self.progress_signal.emit({"status": "warning", "msg": f"⚠️ Не удалось переименовать в .mp4: {e}"})
                        return unknown_file
            except:
                pass
            
            # FALLBACK: Если ничего не сработало, переименуем в .mp4 в любом случае
            self.progress_signal.emit({"status": "processing", "msg": "ℹ️ Формат не определен, переименовываю в .mp4 по умолчанию"})
            new_file = unknown_file.replace('.unknown_video', '.mp4')
            try:
                if os.path.exists(new_file):
                    os.remove(new_file)
                os.rename(unknown_file, new_file)
                return new_file
            except Exception as e:
                self.progress_signal.emit({"status": "warning", "msg": f"⚠️ Не удалось переименовать: {e}. Работаем с исходным файлом."})
                return unknown_file
            
        except Exception as e:
            self.progress_signal.emit({"status": "warning", "msg": f"⚠️ Ошибка определения формата: {e}"})
            # Даже в случае ошибки, попытаемся переименовать
            try:
                new_file = unknown_file.replace('.unknown_video', '.mp4')
                if os.path.exists(new_file):
                    os.remove(new_file)
                os.rename(unknown_file, new_file)
                return new_file
            except:
                return unknown_file

    def _download_youtube_pytubefix(self):
        """
        Скачивает видео с YouTube используя pytubefix.
        Использует progressive потоки (видео + аудио вместе) чтобы избежать необходимости FFmpeg.
        Решает проблемы с определением бота и ошибками JavaScript runtime от yt-dlp.
        
        Поддерживает cookies для обхода bot-detection:
        1. Из файла cookies (если указан)
        2. Автоматически из браузера (Chrome, Firefox, Edge и т.д.)
        """
        try:
            self.progress_signal.emit({
                "status": "processing",
                "msg": "YouTube обнаружен - использую pytubefix (без JS runtime ошибок)..."
            })
            
            # Получаем video ID
            video_id = extract_video_id(self.url)
            if not video_id:
                self.progress_signal.emit({
                    "status": "error",
                    "msg": "Не удалось извлечь video ID из YouTube URL"
                })
                self.finished_signal.emit("")
                return
            
            # Пытаемся загрузить YouTube с cookies для обхода bot-detection
            cookies_loaded = False
            yt = None
            
            # 1. Попробуем с файлом cookies если указан
            if self.cookies_path and os.path.exists(self.cookies_path):
                try:
                    self.progress_signal.emit({
                        "status": "processing",
                        "msg": "Загружаю cookies из файла..."
                    })
                    yt = YouTube(self.url, use_oauth=False, allow_oauth_cache=True)
                    cookies_loaded = True
                except Exception as e:
                    self.progress_signal.emit({
                        "status": "processing", 
                        "msg": "Файл cookies не подошёл, пробую cookies браузера..."
                    })
            
            # 2. Если нет cookies файла или он не сработал, пробуем создать YouTube объект
            if not yt:
                yt = YouTube(self.url, use_oauth=False, allow_oauth_cache=True)
            
            # Получаем информацию о видео
            try:
                title = yt.title
                views = yt.views
                length = yt.length
                self.progress_signal.emit({
                    "status": "processing",
                    "msg": f"Видео: {title}\nПросмотров: {views:,}\nДлительность: {length // 60}:{length % 60:02d} сек"
                })
            except:
                self.progress_signal.emit({
                    "status": "processing",
                    "msg": "Загружаю информацию о видео..."
                })
            
            # Пытаемся получить progressive поток (видео + аудио вместе)
            # Progressive потоки НЕ требуют FFmpeg и содержат стандартное качество
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            
            if not stream:
                # Fallback: если нет progressive потока, используем самый высокий доступный
                self.progress_signal.emit({
                    "status": "processing",
                    "msg": "Progressive поток не найден, ищу альтернативу..."
                })
                stream = yt.streams.get_highest_resolution()
            
            if not stream:
                self.progress_signal.emit({
                    "status": "error",
                    "msg": "Не удалось найти подходящий поток видео"
                })
                self.finished_signal.emit("")
                return
            
            # Информация о потоке
            try:
                self.progress_signal.emit({
                    "status": "processing",
                    "msg": f"Качество: {stream.resolution}\nРазмер: {stream.filesize // (1024*1024):.1f} МБ"
                })
            except:
                pass
            
            # Скачиваем видео
            self.progress_signal.emit({
                "status": "downloading",
                "msg": f"Скачиваю: {os.path.basename(stream.default_filename)}..."
            })
            
            output_path = stream.download(
                output_path=self.download_dir,
                filename=None
            )
            
            # Проверяем, что файл существует и не пуст
            if not os.path.exists(output_path):
                self.progress_signal.emit({
                    "status": "error",
                    "msg": f"Файл не был сохранён: {output_path}"
                })
                self.finished_signal.emit("")
                return
            
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                self.progress_signal.emit({
                    "status": "error",
                    "msg": "Скачанный файл пуст (0 байт)"
                })
                try:
                    os.remove(output_path)
                except:
                    pass
                self.finished_signal.emit("")
                return
            
            self.progress_signal.emit({
                "status": "finished",
                "msg": f"YouTube видео успешно скачано!\nРазмер: {file_size / (1024*1024):.1f} МБ"
            })
            
            # Готовый файл - сигнал о завершении
            self.finished_signal.emit(output_path)
            
        except Exception as e:
            error_msg = str(e)
            
            # Хорошие сообщения об ошибках для YouTube
            if "BotDetection" in error_msg or "bot" in error_msg.lower() or "Sign in" in error_msg:
                msg = ("YouTube требует подтверждение что это не бот.\n"
                       "Решение:\n"
                       "1. Убедитесь что браузер выбран в поле 'Браузер:'\n"
                       "2. Браузер должен быть авторизован на YouTube\n"
                       "3. Используйте режим Selenium для гарантированного доступа\n"
                       "Дополнительно: https://pytubefix.readthedocs.io")
            elif "availability" in error_msg.lower():
                msg = "Видео недоступно (приватное, удалённое или блокировка по регионам)"
            elif "403" in error_msg or "permission" in error_msg.lower():
                msg = "Видео требует аутентификации или заблокировано"
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                msg = f"Ошибка подключения: {error_msg[:100]}"
            else:
                msg = f"Ошибка YouTube: {error_msg[:150]}"
            
            self.progress_signal.emit({"status": "error", "msg": msg})
            self.finished_signal.emit("")


class LinkExtractorThread(QThread):
    """
    Поток для извлечения видеоссылок со страницы с помощью Selenium.
    Ищет прямые ссылки, скрытые видео и кнопки загрузки с редиректами.
    """
    
    progress_signal = pyqtSignal(dict)  # {"status": "...", "msg": "...", "links": [...]}
    finished_signal = pyqtSignal(list)   # Список найденных ссылок
    
    def __init__(self, url: str, headless: bool = True, timeout: int = 30):
        """
        Args:
            url: URL страницы для анализа
            headless: Запустить браузер в фоне без UI
            timeout: Таймаут ожидания элементов (сек)
        """
        super().__init__()
        self.url = url
        self.headless = headless
        self.timeout = timeout
        self.stop_extraction = False
    
    def run(self):
        """Основной метод потока - извлекает ссылки."""
        try:
            self.progress_signal.emit({
                "status": "processing",
                "msg": f"🌐 Инициализация браузера для анализа: {self.url}"
            })
            
            # Создаём экстрактор и запускаем извлечение
            extractor = LinkExtractor(headless=self.headless, timeout=self.timeout)
            
            if self.stop_extraction:
                self.finished_signal.emit([])
                return
            
            self.progress_signal.emit({
                "status": "processing",
                "msg": "🔍 Анализ страницы и поиск видеоссылок..."
            })
            
            video_links, page_info = extractor.extract_links(self.url)
            
            if self.stop_extraction:
                self.finished_signal.emit([])
                return
            
            if video_links:
                self.progress_signal.emit({
                    "status": "success",
                    "msg": f"✅ Найдено {len(video_links)} видеоссылок",
                    "links": video_links,
                    "details": page_info
                })
                self.finished_signal.emit(video_links)
            else:
                self.progress_signal.emit({
                    "status": "warning",
                    "msg": "⚠️ Видеоссылки не найдены на странице"
                })
                self.finished_signal.emit([])
        
        except Exception as e:
            tb = traceback.format_exc()
            self.progress_signal.emit({
                "status": "error",
                "msg": f"❌ Ошибка при извлечении ссылок:\n{str(e)}"
            })
            print(tb)
            self.finished_signal.emit([])
    
    def stop(self):
        """Остановить процесс извлечения."""
        self.stop_extraction = True
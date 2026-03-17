# core/workers.py
import os
from typing import Tuple

from susik_media import SusikMedia

class MediaConverter:
    """
    Обёртка над SusikMedia — выделяет ответственность за финализацию/конвертацию.
    Метод process возвращает (True, message_or_path) или (False, error_message).
    """
    def __init__(self, input_path: str):
        self.input_path = input_path

    def process(self, output_path: str, copy_codec: bool = True, audio_only: bool = False) -> Tuple[bool, str]:
        """
        Пытается выполнить процесс конвертации/remux через SusikMedia.
        
        Args:
            output_path: Путь для сохранения
            copy_codec: Копировать оригинальный кодек или конвертировать
            audio_only: Если True, извлекает только аудио (для MP3)
        
        Возвращает (success: bool, message_or_path: str).
        """
        try:
            processor = SusikMedia(self.input_path)
            ok, msg = processor.process_conversion(output_path, copy_codec=copy_codec, audio_only=audio_only)
            if ok:
                return True, output_path
            else:
                return False, msg
        except Exception as e:
            return False, str(e)
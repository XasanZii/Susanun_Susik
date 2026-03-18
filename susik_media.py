# susik_media.py
import av
import os

class SusikMedia:
    def __init__(self, input_p=None):
        self.input_p = input_p

    def validate_input_file(self) -> tuple:
        """
        Проверяет файл на валидность перед конвертацией.
        
        Returns:
            (is_valid: bool, message: str)
        """
        try:
            if not os.path.exists(self.input_p):
                return False, f"Файл не найден: {self.input_p}"
            
            file_size = os.path.getsize(self.input_p)
            if file_size < 1024:  # Меньше 1KB
                return False, f"Файл слишком маленький ({file_size} байт) - возможно повреждён"
            
            # Пробуем открыть файл для проверки
            try:
                container = av.open(self.input_p)
                has_streams = len(container.streams) > 0
                
                if not has_streams:
                    container.close()
                    return False, "Файл не содержит аудио/видео потоков"
                
                # Проверяем, что хотя бы один поток читаемый
                has_readable_stream = False
                for stream in container.streams:
                    if stream.type in ('video', 'audio'):
                        has_readable_stream = True
                        break
                
                container.close()
                
                if not has_readable_stream:
                    return False, "Файл содержит только неизвестные потоки"
                
                return True, "Файл валиден"
            except Exception as e:
                error_str = str(e)
                # Если ошибка о битом входном потоке, возвращаем специальное сообщение
                if "Invalid data" in error_str:
                    return False, f"Входной поток повреждён: {error_str}"
                return False, f"Ошибка чтения файла: {error_str}"
                
        except Exception as e:
            return False, f"Ошибка валидации: {str(e)}"

    def process_conversion(self, output_p, copy_codec=True, audio_only=False):
        """
        Возвращает (True, "Success") или (False, "error message")
        
        Args:
            output_p: Путь сохранения
            copy_codec: Копировать оригинальный кодек
            audio_only: Если True, извлекает только аудио (MP3)
        """
        # Валидация входного файла
        is_valid, validation_msg = self.validate_input_file()
        if not is_valid:
            return False, validation_msg
        
        input_container = None
        output_container = None
        try:
            input_container = av.open(self.input_p)
            output_container = av.open(output_p, mode='w')
            stream_map = {}

            # Выбираем дорожки
            for stream in input_container.streams:
                # Если audio_only, берем только аудио
                if audio_only:
                    if stream.type != 'audio':
                        continue
                else:
                    # Иначе видео и аудио
                    if stream.type not in ('video', 'audio'):
                        continue
                
                try:
                    if copy_codec:
                        out_stream = output_container.add_stream(template=stream)
                    else:
                        if stream.type == 'video':
                            codec = 'libx264'
                            out_stream = output_container.add_stream(codec)
                            out_stream.width = stream.width
                            out_stream.height = stream.height
                            out_stream.pix_fmt = 'yuv420p'
                        else:  # audio
                            codec = 'aac' if not audio_only else 'libmp3lame'
                            out_stream = output_container.add_stream(codec)
                            if audio_only:
                                out_stream.rate = stream.sample_rate
                    
                    stream_map[stream.index] = out_stream
                except Exception:
                    # пропускаем дорожки, которые не лезят в нужный формат
                    continue

            for packet in input_container.demux():
                if packet.stream.index in stream_map:
                    out_stream = stream_map[packet.stream.index]
                    if copy_codec:
                        # Коррекция таймстемпов
                        try:
                            packet.pts = packet.pts
                            packet.dts = packet.dts
                            packet.rescale_ts(out_stream.time_base)
                            packet.stream = out_stream
                            output_container.mux(packet)
                        except Exception as e:
                            # При ошибке копирования пропускаем пакет
                            continue
                    else:
                        try:
                            for frame in packet.decode():
                                packets = out_stream.encode(frame)
                                for out_packet in packets:
                                    output_container.mux(out_packet)
                        except Exception as e:
                            # Если ошибка при перекодировании - пропускаем
                            continue

            if not copy_codec:
                try:
                    for out_stream in stream_map.values():
                        packets = out_stream.encode()
                        for out_packet in packets:
                            output_container.mux(out_packet)
                except Exception:
                    # Финализация может вызвать ошибку - продолжаем
                    pass

            return True, "Success"

        except Exception as e:
            error_str = str(e)
            # Если ошибка кодека и copy_codec=False, пробуем с копированием
            if not copy_codec and ("codec" in error_str.lower() or "Invalid data" in error_str):
                try:
                    # Закрываем текущие контейнеры
                    if output_container:
                        try:
                            output_container.close()
                        except:
                            pass
                    if input_container:
                        try:
                            input_container.close()
                        except:
                            pass
                    
                    # Удаляем неполный выходной файл
                    if os.path.exists(output_p):
                        try:
                            os.remove(output_p)
                        except:
                            pass
                    
                    # Повторяем с copy_codec=True
                    return self.process_conversion(output_p, copy_codec=True, audio_only=audio_only)
                except Exception as retry_error:
                    return False, f"Ошибка конвертации (оба метода): {str(retry_error)}"
            else:
                return False, f"Ошибка конвертации: {error_str}"
        finally:
            if output_container:
                try:
                    output_container.close()
                except Exception:
                    pass
            if input_container:
                try:
                    input_container.close()
                except Exception:
                    pass
import av
import os

class SusikMedia:
    """Библиотека для обработки медиа в проекте Susanun_Susik."""
    
    def __init__(self, input_path):
        self.input_path = input_path
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Файл {input_path} не найден.")

    def convert(self, output_path, video_codec='libx264', audio_codec='aac'):
        """Конвертация видео/аудио в другой формат."""
        input_container = av.open(self.input_path)
        output_container = av.open(output_path, mode='w')

        # Создаем потоки в выходном файле на основе входного
        for stream in input_container.streams:
            if stream.type == 'video':
                template = output_container.add_stream(video_codec)
            elif stream.type == 'audio':
                template = output_container.add_stream(audio_codec)
            else:
                continue # Игнорируем субтитры и прочее для упрощения

            template.width = stream.width if stream.type == 'video' else None
            template.height = stream.height if stream.type == 'video' else None
            template.pix_fmt = 'yuv420p' if stream.type == 'video' else None

        # Кодирование пакетов
        for packet in input_container.demux():
            for frame in packet.decode():
                # Здесь можно добавить фильтры или сжатие
                new_packets = template.encode(frame)
                output_container.mux(new_packets)

        # Сбрасываем буферы
        output_container.mux(template.encode(None))
        input_container.close()
        output_container.close()
        print(f"Готово! Файл сохранен: {output_path}")

    def extract_audio(self, output_path):
        """Извлечение только аудиодорожки."""
        self.convert(output_path, audio_codec='mp3')

# Пример использования:
# decoder = SusikMedia("video.avi")
# decoder.convert("video.mp4")
# decoder.extract_audio("sound.mp3")
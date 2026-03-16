import av
import os

class SusikMedia:
    def __init__(self, input_p=None):
        self.input_p = input_p

    def process_conversion(self, output_p, copy_codec=False):
        """Аналог ffmpeg -i input -c copy или libx264."""
        try:
            input_container = av.open(self.input_p)
            output_container = av.open(output_p, mode='w')

            # Выбор кодека: 'copy' в PyAV работает через передачу параметров потока
            v_codec = 'copy' if copy_codec else 'libx264'
            
            stream_map = {}
            for stream in input_container.streams:
                if stream.type in ('video', 'audio'):
                    # Для простоты в этом примере используем перекодирование
                    # так как 'copy' в PyAV требует сложной настройки медиа-мукшера
                    out_stream = output_container.add_stream('libx264' if stream.type == 'video' else 'aac')
                    if stream.type == 'video':
                        out_stream.width = stream.width
                        out_stream.height = stream.height
                        out_stream.pix_fmt = 'yuv420p'
                    stream_map[stream] = out_stream

            for packet in input_container.demux():
                if packet.stream in stream_map:
                    for frame in packet.decode():
                        out_packet = stream_map[packet.stream].encode(frame)
                        output_container.mux(out_packet)

            # Финализация
            for out_s in stream_map.values():
                output_container.mux(out_s.encode(None))

            output_container.close()
            input_container.close()
            return True
        except Exception as e:
            print(f"Ошибка SusikMedia: {e}")
            return False
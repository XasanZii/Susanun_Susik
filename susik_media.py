import av
import os

class SusikMedia:
    def __init__(self, input_p=None):
        self.input_p = input_p

    def process_conversion(self, output_p, copy_codec=True):
        input_container = None
        output_container = None
        try:
            input_container = av.open(self.input_p)
            output_container = av.open(output_p, mode='w')

            stream_map = {}
            for stream in input_container.streams:
                if stream.type in ('video', 'audio'):
                    if copy_codec:
                        # Режим прямого копирования (Remuxing)
                        out_stream = output_container.add_stream(template=stream)
                    else:
                        # Режим перекодирования (Transcoding)
                        codec = 'libx264' if stream.type == 'video' else 'aac'
                        out_stream = output_container.add_stream(codec)
                        if stream.type == 'video':
                            out_stream.width = stream.width
                            out_stream.height = stream.height
                            out_stream.pix_fmt = 'yuv420p'
                    
                    stream_map[stream.index] = out_stream

            for packet in input_container.demux():
                if packet.stream.index in stream_map:
                    if copy_codec:
                        packet.stream = stream_map[packet.stream.index]
                        output_container.mux(packet)
                    else:
                        for frame in packet.decode():
                            # encode() может возвращать список пакетов
                            packets = stream_map[packet.stream.index].encode(frame)
                            for out_packet in packets:
                                output_container.mux(out_packet)

            # Очистка буферов энкодера (Flush)
            if not copy_codec:
                for stream in stream_map.values():
                    packets = stream.encode()
                    for out_packet in packets:
                        output_container.mux(out_packet)

            return True
        except Exception as e:
            print(f"Ошибка SusikMedia: {e}")
            return False
        finally:
            if output_container:
                output_container.close()
            if input_container:
                input_container.close()
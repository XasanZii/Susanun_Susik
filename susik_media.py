import av

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
            # Выбираем только видео и аудио дорожки
            for stream in input_container.streams:
                if stream.type in ('video', 'audio'):
                    try:
                        if copy_codec:
                            out_stream = output_container.add_stream(template=stream)
                        else:
                            codec = 'libx264' if stream.type == 'video' else 'aac'
                            out_stream = output_container.add_stream(codec)
                            if stream.type == 'video':
                                out_stream.width = stream.width
                                out_stream.height = stream.height
                                out_stream.pix_fmt = 'yuv420p'
                        
                        stream_map[stream.index] = out_stream
                    except Exception:
                        continue # Пропускаем дорожки, которые не лезут в MP4

            for packet in input_container.demux():
                if packet.stream.index in stream_map:
                    out_stream = stream_map[packet.stream.index]
                    
                    if copy_codec:
                        # КОРРЕКЦИЯ ТАЙМСТЕМПОВ (Исправляет вашу ошибку)
                        packet.pts = packet.pts
                        packet.dts = packet.dts
                        packet.rescale_ts(out_stream.time_base)
                        packet.stream = out_stream
                        output_container.mux(packet)
                    else:
                        for frame in packet.decode():
                            packets = out_stream.encode(frame)
                            for out_packet in packets:
                                output_container.mux(out_packet)

            if not copy_codec:
                for out_stream in stream_map.values():
                    packets = out_stream.encode()
                    for out_packet in packets:
                        output_container.mux(out_packet)

            return True, "Success"
        except Exception as e:
            return False, str(e)
        finally:
            if output_container: output_container.close()
            if input_container: input_container.close()
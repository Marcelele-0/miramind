from .stt_stream import RecordingStream, STTStream
import threading
import time


class STTRecStream:
    """
    Class combing recording speech and transcribing it. It combines STTStream and RecordingStream.

    Attributes:
        _rec_stream: RecordingStream instance used for handling recording.
        _stt_stream: STTStream instance used for handling transcriptions.
        buffer: Queue instance used to store transcriptions (shared with stt_stream).
        general_stop_flag: threading.Event used for stopping run method.
    """

    def __init__(self, save_dir):
        """
        Constructor of STTRecStream class.

        Args:
            save_dir: path of directory used to save recordings.
        """
        self._rec_stream = RecordingStream(save_dir=save_dir)
        self._stt_stream = STTStream(target_queue=self._rec_stream.get_file_queue())
        self.buffer = self._stt_stream.get_buffer()
        self.rec_stop_flag = self._rec_stream.get_stop_flag()
        self.stt_stop_flag = self._stt_stream.get_stop_flag()
        self.general_stop_flag = threading.Event()

    def get_stop_flag(self):
        """
        Get general_stop_flag.
        """

        return self.general_stop_flag

    def get_buffer(self):
        """
        Get buffer.
        """

        return self.buffer

    def run(self, **kwargs):
        """
        Method used to run both rec_stream and stt_stream (in separate threads).

        Keyword Args
            duration: duration of a recorded chunk.
            sample_rate: sample rate of recording.

        Returns:
            None
        """

        listening_loop = threading.Thread(target=self._rec_stream.run, kwargs=kwargs)
        transcribing_loop = threading.Thread(target=self._stt_stream.run)
        listening_loop.start()
        transcribing_loop.start()
        while not self.general_stop_flag.is_set():
            time.sleep(0.1)

        self.rec_stop_flag.set()
        listening_loop.join()
        self.stt_stop_flag.set()
        transcribing_loop.join()

<a id="main"></a>

# main

<a id="new_file"></a>

# new\_file

<a id="miramind"></a>

# miramind

<a id="miramind.audio.stt.consts"></a>

# miramind.audio.stt.consts

<a id="miramind.audio.stt.loggers"></a>

# miramind.audio.stt.loggers

<a id="miramind.audio.stt.loggers.get_loggers"></a>

#### get\_loggers

```python
def get_loggers()
```

Get rec_stream_logger and stt_stream_logger.

**Returns**:

  (rec_stream_logger, stt_stream_logger)

<a id="miramind.audio.stt.stt_class"></a>

# miramind.audio.stt.stt\_class

<a id="miramind.audio.stt.stt_class.STT"></a>

## STT Objects

```python
class STT()
```

A class handling transcribing audio files.

**Attributes**:

- `client` - client instance used for API calls.

<a id="miramind.audio.stt.stt_class.STT.__init__"></a>

#### \_\_init\_\_

```python
def __init__(client, logger=None)
```

Constructor of STT class.

**Arguments**:

- `client` - client instance for API calls.
- `logger` - logger instance for logging.

<a id="miramind.audio.stt.stt_class.STT.transcribe_bytes"></a>

#### transcribe\_bytes

```python
def transcribe_bytes(bytes)
```

Transcribe bytes object.

**Arguments**:

- `bytes` - bytes object representing sound to transcribe.


**Returns**:

- `dict[str` - str]: dict containing transcript (with key "transcript")

<a id="miramind.audio.stt.stt_class.STT.transcribe"></a>

#### transcribe

```python
def transcribe(file_path: str) -> dict[str:str]
```

Transcribes an audio file and detects the language of the transcript.

**Arguments**:

- `file_path` _str_ - Path to the audio file to be transcribed.


**Returns**:

  dict[str, str]: A dictionary containing the detected language and the transcribed text.
  Keys are:
  - 'language': The detected language (e.g., 'english', 'german').
  - 'transcript': The transcribed text from the audio.

<a id="miramind.audio.stt.stt_class.LinearListeningSTT"></a>

## LinearListeningSTT Objects

```python
class LinearListeningSTT(STT)
```

Linear speech to text class. Subclass of STT. Main use case is calling run method.

<a id="miramind.audio.stt.stt_class.LinearListeningSTT.run"></a>

#### run

```python
def run(chunk_duration, sample_rate=SAMPLE_RATE)
```

Main functionality of LinearListeningSTT.

**Arguments**:

- `chunk_duration` - duration (in seconds) of listening before transcribing recorded sound.
- `sample_rate` - recording's sample rate (default 44100).

<a id="miramind.audio.stt.stt_stream"></a>

# miramind.audio.stt.stt\_stream

<a id="miramind.audio.stt.stt_stream.get_short_uuid"></a>

#### get\_short\_uuid

```python
def get_short_uuid()
```

Unique id generator.

**Returns**:

  id that is unlikely to have been generated before (str).

<a id="miramind.audio.stt.stt_stream.RecordingStream"></a>

## RecordingStream Objects

```python
class RecordingStream()
```

Class for handling recording speech.

**Attributes**:

- `_file_queue` - Queue instance containing paths to saved files.
- `save_dir` - path to directory where recordings are saved.
- `_stop_flag` - threading.Event instance used to stop run method.

<a id="miramind.audio.stt.stt_stream.RecordingStream.__init__"></a>

#### \_\_init\_\_

```python
def __init__(save_dir: str = None, logger=None)
```

Constructor of RecordingStream class.

**Arguments**:

- `save_dir` - path to directory where recordings are saved. Default depends on .env file.
- `logger` - logging instance used for logging.

<a id="miramind.audio.stt.stt_stream.RecordingStream.get_file_queue"></a>

#### get\_file\_queue

```python
def get_file_queue()
```

Get _file_queue attribute.

<a id="miramind.audio.stt.stt_stream.RecordingStream.get_stop_flag"></a>

#### get\_stop\_flag

```python
def get_stop_flag()
```

Get _stop_flag attribute.

<a id="miramind.audio.stt.stt_stream.RecordingStream.record"></a>

#### record

```python
@staticmethod
def record(path: str = "output.wav", logger: logging.Logger = None, **kwargs)
```

Static method used for recording audio. After running this method program will record from default system microphone.

**Arguments**:

- `path` - path where recording will be saved recording.
- `logger` - object used for logging purposes.


**Arguments**:

- `duration` - duration of recording in seconds.
- `sample_rate` - sample rate of recording.


**Returns**:

  None

<a id="miramind.audio.stt.stt_stream.RecordingStream.run"></a>

#### run

```python
def run(**kwargs)
```

Method used as target function of a Thread. It will record speech in chunks and save recordings to save_dir.
Result of running this method is twofold:
- having recordings in a specified directory,
- having put path of said recordings to file_queue

**Arguments**:

- `duration` - duration of recording in seconds.
- `sample_rate` - sample rate of recording.
- `prompting_func` - function to be called when recording is starting.
- `loop_indicator_func` - function to indicate change of chunks.

  Rest of keyword arguments are specific to prompting_function and loop_indicator_func.


**Returns**:

  None

<a id="miramind.audio.stt.stt_stream.STTStream"></a>

## STTStream Objects

```python
class STTStream()
```

Class for handling transcriptions of recorded files.

**Attributes**:

- `target_queue` - Queue instance containing paths of recordings to transcribe.
- `stt` - STT instance used to transcribe recordings.
- `stop_flag` - threading.Event instance used to stop run method.
- `buffer` - Queue instance where transcripts are put.

<a id="miramind.audio.stt.stt_stream.STTStream.__init__"></a>

#### \_\_init\_\_

```python
def __init__(target_queue, client, logger=None)
```

Constructor of STTStream.

**Arguments**:

- `target_queue` - Queue instance where paths of files to transcribe are stored.
- `client` - client instance used for API calls.
- `logger` - logger instance used for logging.

<a id="miramind.audio.stt.stt_stream.STTStream.get_stop_flag"></a>

#### get\_stop\_flag

```python
def get_stop_flag()
```

Get stop_flag attribute.

<a id="miramind.audio.stt.stt_stream.STTStream.get_buffer"></a>

#### get\_buffer

```python
def get_buffer()
```

Get buffer attribute.

<a id="miramind.audio.stt.stt_stream.STTStream.transcribe"></a>

#### transcribe

```python
def transcribe()
```

Methods that transcribes first file from _target_queue and puts transcript to _buffer.

**Returns**:

  file, transcript: path of transcribed file and transcription

<a id="miramind.audio.stt.stt_stream.STTStream.run"></a>

#### run

```python
def run(verbose=True)
```

Method used as target function of a Thread. The using this method will result in transcribing files enqueued in target_queue,
then transcripts are put into _buffer. It will be stopped when _stop_flag is set.

**Arguments**:

- `verbose` - bool = True: If True then log transcripts.


**Returns**:

  None

<a id="miramind.audio.stt.stt_stream.RecSTTStream"></a>

## RecSTTStream Objects

```python
class RecSTTStream()
```

Class used for creating and running recording and transcription in parallel.

**Attributes**:

- `buffer` - Queue instance where transcripts are stored.
- `rec_thread` - thread responsible for running recording.
- `stt_thread` - thread responsible for creating transcripts.
- `rec_flag` - event used to stop rec_thread.
- `stt_flag` - event used to stop stt_thread.

<a id="miramind.audio.stt.stt_stream.RecSTTStream.__init__"></a>

#### \_\_init\_\_

```python
def __init__(client,
             duration=DURATION,
             sample_rate=SAMPLE_RATE,
             verbose=True,
             stt_logger=None,
             rec_logger=None)
```

Constructor of RecSTTStream.

**Arguments**:

- `client` - client instance used for API calls.
- `duration` - duration of a chunk.
- `sample_rate` - sample rate of a chunk.
- `verbose` - if True, log verbosity increased.
- `rec_stream` - RecordingStream instance used for handling recording.
- `stt_stream` - STTStream instance used for handling transcribing.
- `stt_logger` - logger instance used for logging STT process.
- `rec_logger` - logger instance used for logging recording.

<a id="miramind.audio.stt.stt_stream.RecSTTStream.start"></a>

#### start

```python
def start()
```

Start rec_thread and stt_thread.

**Returns**:

  None

<a id="miramind.audio.stt.stt_stream.RecSTTStream.stop"></a>

#### stop

```python
def stop()
```

Stop rec_thread and stt_thread.

**Returns**:

  buffer

<a id="miramind.audio.stt.stt_threads"></a>

# miramind.audio.stt.stt\_threads

<a id="miramind.audio.stt.stt_threads.ListeningThread"></a>

## ListeningThread Objects

```python
class ListeningThread(threading.Thread)
```

This thread will put recorded audio in form of numpy array to return queue.

<a id="miramind.audio.stt.stt_threads.ListeningThread.__init__"></a>

#### \_\_init\_\_

```python
def __init__(return_queue,
             name=None,
             daemon=None,
             flag=None,
             chunk_duration=DURATION,
             sample_rate=SAMPLE_RATE,
             logger=None,
             prompt=None)
```

Constructor of ListeningThread class.


**Arguments**:

- `return_queue` - queue.Queue instance, where recorded audio (in form of numpy array) is put.
- `name` - name of the thread (as per threading.Thread).
- `daemon` - if True, thread will be daemon.
- `flag` - threading.Event used to stop this thread (if none is provided one is generated, can be obtained by get_flag method).
- `chunk_duration` - duration of a chunk.
- `sample_rate` - recording's sample rate (frames per second).
- `logger` - logger instance used for logging.
- `prompt` - function called on beginning of each chunk (if none is provided iw will be print chunk's nuber).

<a id="miramind.audio.stt.stt_threads.TranscribingBytesThread"></a>

## TranscribingBytesThread Objects

```python
class TranscribingBytesThread(threading.Thread)
```

Thread that transcribes audio saved as numpy array.

<a id="miramind.audio.stt.stt_threads.TranscribingBytesThread.__init__"></a>

#### \_\_init\_\_

```python
def __init__(target_queue,
             stt,
             name=None,
             flag=None,
             buffer=None,
             logger=None,
             daemon=False,
             sample_rate=SAMPLE_RATE,
             timeout=6)
```

Constructor of TranscribingBytesThread.


**Arguments**:

- `target_queue` - queue.Queue instance containing arrays representing sound to transcribe.
- `stt` - STT instance used for transcribing.
- `name` - name of the thread.
- `flag` - threading.Event used to stop this thread (if none is provided one is generated, can be obtained by get_flag method).
- `buffer` - queue.Queue instance where transcripts will be put (if none is provided one will be created and can be accessed by get_buffer method)
- `logger` - logger instance for logging.
- `daemon` - if True this thread will be daemon.
- `sample_rate` - sample rate of recording (this should match sample rate of recordings).
- `timeout` - timeout for queues involved in this thread.

<a id="miramind.audio.stt.stt_threads.timed_listen_and_transcribe"></a>

#### timed\_listen\_and\_transcribe

```python
def timed_listen_and_transcribe(client,
                                duration=10,
                                chunk_duration=5,
                                lag=2,
                                buffer=None,
                                rec_logger=None,
                                stt_logger=None,
                                timeout=10)
```

This function joins main functionality of ListeningThread and TranscribingBytesThread. It will record speech for fixed time and then transcribe it.
The main idea is to employ two listening threads (shifted by lag) to cover all incoming voice, as there is delay between chunks.


**Arguments**:

- `client` - Azure OpenAI client for api calls.
- `duration` - duration of whole recording.
- `chunk_duration` - duration of a recorded chunk.
- `lag` - time between starting second listening thread (note optimal is hardware dependent).
- `buffer` - queue.Queue instance where transcripts will be put.
- `rec_logger` - logger instance that will be passed as a logger of listening thread.
- `stt_logger` - logger instance that will be passed as a logger of transcribing thread.
- `timeout` - timeout for all queues involved.



**Returns**:

  buffer with transcripts (in form of {"transcript": "transcript od audio"}). If buffer arg was provided then it will also put those in buffer else it will return new queue.Queue instance..

<a id="miramind.audio.stt"></a>

# miramind.audio.stt

<a id="miramind.audio.tts.tts_azure"></a>

# miramind.audio.tts.tts\_azure

<a id="miramind.audio.tts.tts_azure.AzureTTSProvider"></a>

## AzureTTSProvider Objects

```python
class AzureTTSProvider(TTSProvider)
```

Azure Cognitive Services Text-to-Speech provider with emotion support.

<a id="miramind.audio.tts.tts_azure.AzureTTSProvider.__init__"></a>

#### \_\_init\_\_

```python
def __init__(subscription_key: str,
             endpoint: str,
             voice_name: str = "en-US-JennyNeural")
```

Initialize Azure TTS provider.

**Arguments**:

- `subscription_key` _str, optional_ - Azure Cognitive Services subscription key
- `endpoint` _str, optional_ - Azure Speech service endpoint URL
- `voice_name` _str_ - Voice to use (default: en-US-JennyNeural - supports 14+ emotion styles as of Feb 2025)

<a id="miramind.audio.tts.tts_azure.AzureTTSProvider.synthesize"></a>

#### synthesize

```python
def synthesize(input_json: str) -> bytes
```

Convert input text and emotion data into synthesized speech audio.

**Arguments**:

- `input_json` _str_ - JSON string containing text and optional emotion data


**Returns**:

- `bytes` - Audio data in WAV format


**Raises**:

- `ValueError` - If input_json is malformed or missing required fields

<a id="miramind.audio.tts.tts_azure.AzureTTSProvider.set_emotion"></a>

#### set\_emotion

```python
def set_emotion(text: str, emotion: str) -> str
```

Apply emotion to text and return SSML markup with emotion styling.

**Arguments**:

- `text` _str_ - The original text to synthesize
- `emotion` _str_ - The emotion to apply


**Returns**:

- `str` - SSML markup with emotion styling applied


**Raises**:

- `ValueError` - If emotion is not supported

<a id="miramind.audio.tts.tts_base"></a>

# miramind.audio.tts.tts\_base

<a id="miramind.audio.tts.tts_base.TTSProvider"></a>

## TTSProvider Objects

```python
class TTSProvider(ABC)
```

Abstract base class for all Text-to-Speech providers.

<a id="miramind.audio.tts.tts_base.TTSProvider.synthesize"></a>

#### synthesize

```python
@abstractmethod
def synthesize(input_json: str) -> bytes
```

Convert input text and emotion data into synthesized speech audio.

**Arguments**:

- `input_json` _str_ - JSON string containing text and optional emotion data.
  Expected format: {"text": "speech text", "emotion": "emotion_name"}


**Returns**:

- `bytes` - Audio data in bytes format (typically MP3 or WAV)


**Raises**:

- `ValueError` - If input_json is malformed or missing required fields
- `NotImplementedError` - If the method is not implemented by subclass

<a id="miramind.audio.tts.tts_base.TTSProvider.set_emotion"></a>

#### set\_emotion

```python
@abstractmethod
def set_emotion(text: str, emotion: str) -> str
```

Apply emotion to text and return properly formatted text for synthesis.

This method should handle emotion application in a provider-specific way:
- For SSML-based providers (Azure): return SSML markup with emotion tags
- For other providers: return modified text or configuration string

**Arguments**:

- `text` _str_ - The original text to synthesize
- `emotion` _str_ - The emotion to apply (e.g., 'happy', 'sad', 'neutral')


**Returns**:

- `str` - Formatted text ready for synthesis (SSML, modified text, etc.)


**Raises**:

- `ValueError` - If emotion is not supported by the provider
- `NotImplementedError` - If the method is not implemented by subclass

<a id="miramind.audio.tts.tts_factory"></a>

# miramind.audio.tts.tts\_factory

<a id="miramind.audio.tts.tts_factory.get_tts_provider"></a>

#### get\_tts\_provider

```python
def get_tts_provider(name: str = "azure") -> TTSProvider
```

Create and return a TTS provider instance based on the specified name.

This factory function encapsulates the logic for instantiating different
TTS providers, making it easy to add new providers without changing
client code.

**Arguments**:

- `name` _str_ - The name of the TTS provider to create (default: "azure")
- `currently_supported` - "azure"


**Returns**:

- `TTSProvider` - An instance of the requested TTS provider


**Raises**:

- `ValueError` - If the specified provider name is not supported


**Example**:

  >>> json_input = '{"text": "Hello world", "emotion": "happy"}'
  >>> provider = get_tts_provider("azure")
  >>> audio = provider.synthesize(json_input)

<a id="miramind.audio.tts"></a>

# miramind.audio.tts

<a id="miramind.audio"></a>

# miramind.audio

<a id="miramind.llm.langgraph.chatbot"></a>

# miramind.llm.langgraph.chatbot

<a id="miramind.llm.langgraph.run_chat"></a>

# miramind.llm.langgraph.run\_chat

<a id="miramind.llm.langgraph.run_chat.process_chat_message"></a>

#### process\_chat\_message

```python
def process_chat_message(user_input_text: str,
                         chat_history: list = [],
                         memory: str = "")
```

Processes a single chat message using the chatbot and saves the response audio.

**Arguments**:

- `user_input_text` - The text message from the user.
- `chat_history` - A list of previous chat turns (optional, for continuity).
- `memory` - A string summarizing persistent user context.


**Returns**:

  A dictionary containing 'response_text', 'audio_file_path', and updated memory.

<a id="miramind.llm.langgraph.subgraphs"></a>

# miramind.llm.langgraph.subgraphs

<a id="miramind.llm.langgraph.utils"></a>

# miramind.llm.langgraph.utils

<a id="miramind.llm"></a>

# miramind.llm

<a id="miramind.shared.azure_utils"></a>

# miramind.shared.azure\_utils

<a id="miramind.shared.azure_utils.get_blob_service_client"></a>

#### get\_blob\_service\_client

```python
def get_blob_service_client(logger=None)
```

Easy way to get blob service client for API calls.

**Arguments**:

  logger instance for logging.


**Returns**:

  blob service client instance

<a id="miramind.shared.azure_utils.upload_file"></a>

#### upload\_file

```python
def upload_file(local_file,
                target_blob,
                container,
                blob_service_client=None,
                logger=None)
```

Upload file to storage acount.

**Arguments**:

- `local_file` - path of file to upload.
- `target_blob` - name of blob, that will represent local_file.
- `container` - container where target blob wil be stored.
- `blob_service_client` - client instance (connected with appropriate storage account). Must have specified container.
- `logger` - logger instance for logging.

<a id="miramind.shared.azure_utils.read_blob"></a>

#### read\_blob

```python
def read_blob(target_blob, container, blob_service_client=None, logger=None)
```

Get content of a blob stored in Azure.

**Arguments**:

- `target_blob` - name of blob that will be read.
- `container` - name of the container with target blob.
- `blob_service_client` - client used for API calls (default is to get a new client).
- `logger` - logger instance for logging.


**Returns**:

  target blob in bytes form.

<a id="miramind.shared.azure_utils.download_blob"></a>

#### download\_blob

```python
def download_blob(target_blob,
                  container,
                  download_path,
                  blob_service_client=None,
                  logger=None)
```

Save result of read_blob to file.

**Arguments**:

- `target_blob` - name of blob that will be read.
- `container` - name of the container with target blob.
- `download_path` - path of saved file.
- `blob_service_client` - client used for API calls (default is to get a new client).
- `logger` - logger instance for logging.

<a id="miramind.shared.logger"></a>

# miramind.shared.logger

<a id="miramind.shared.utils"></a>

# miramind.shared.utils

<a id="miramind.shared"></a>

# miramind.shared

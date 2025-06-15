# miramind

## src

### scr/miramind

#### src/miramind/stt

- STT.transcribe(file) -> dict: returns dictionaty with "transcript" and "language" keywords. 

#### src/miramind/shared
 
 - Myclient.get() -> AzureOpenAi: returns AzureOpenAI client.

 ``` python
client = MyClient.get()
 ```

 - msg(role, message) -> dict: returns dictionary with "role" and "contnent" keywords. role argument should be one of S, U, A constants.
``` python
messages = [msg(S, "system prompt"),
            msg(A, "assistnar response"),
            msg(U, "user input")]
print(messages)
# [{'role': 'system', 'content': 'system prompt'}, {'role': 'assistant', 'content': 'assistnar response'}, {'role': 'user', 'content': 'user input'}]
```

### src/scripts

#### scr/scripts/downloader

CLI tool used to download YouTube videos as audio.
``` bash
ytd -url "example url" -name "output file name"
```
Using such command will result in creating file in tests/stt directory. If you need to use downloder not via command line, you can use
``` python
from downloader import download_yt_audio

download_yt_audio(url="my url", name="output file name")
```


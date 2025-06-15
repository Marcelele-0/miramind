# miramind

## src

### scr/miramind

#### src/miramind/stt

#### src/miramind/shared

##### MyClient
 
 - get() -> AzureOpenAi: (static method) returns AzureOpenAI client.

 ``` python
client = MyClient.get()
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


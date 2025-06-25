# miramind

## src

### scr/miramind

#### src/miramind/stt

- STT.transcribe(file) -> dict: returns dictionary with "transcript" keywords.

#### src/miramind/shared

##### scr/miramind/shared/utils

 - get_azure_openai_client(): return AzureOpenAi client instance for API calls.

 - msg(role, message) -> dict: returns dictionary with "role" and "content" keywords. role argument should be one of S, U, A constants.
``` python
messages = [msg(S, "system prompt"),
            msg(A, "assistnar response"),
            msg(U, "user input")]
print(messages)
# [{'role': 'system', 'content': 'system prompt'}, {'role': 'assistant', 'content': 'assistnar response'}, {'role': 'user', 'content': 'user input'}]
```

#### src/miramind/stt

##### src/miramind/stt/stt_class
 - STT: class for handling transcribing files.

### src/scripts

#### scr/scripts/downloader

CLI tool used to download YouTube videos as audio. Save directory depends on .env.
``` bash
ytd -url "example url" -name "output file name"
```

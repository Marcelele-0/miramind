import json
import azure.cognitiveservices.speech as speechsdk
from typing import Any
from miramind.audio.tts.tts_base import TTSProvider


class AzureTTSProvider(TTSProvider):
    """
    Azure Cognitive Services Text-to-Speech provider with emotion support.
    """

    def __init__(
        self,
        subscription_key: str = None,
        region: str = None,
        endpoint: str = None,
        voice_name: str = "en-US-JennyNeural",
    ):
        """
        Initialize Azure TTS provider.

        Args:
            subscription_key (str, optional): Azure Cognitive Services subscription key
            region (str, optional): Azure region (e.g., 'eastus', 'westeurope')
            endpoint (str, optional): Azure Speech service endpoint URL
            voice_name (str): Voice to use (default: en-US-JennyNeural - supports 14+ emotion styles as of Feb 2025)

        Note: Either (subscription_key + region) OR endpoint must be provided
        """
        self.subscription_key = subscription_key
        self.region = region
        self.endpoint = endpoint
        self.voice_name = voice_name

        # Updated emotion mapping for Azure Neural Voices (Feb 2025)
        # JennyNeural now supports 14 emotion styles + general
        self.emotion_styles = {
            'assistant': 'assistant',
            'cheerful': 'cheerful',
            'chat': 'chat',
            'excited': 'excited',
            'friendly': 'friendly',
            'hopeful': 'hopeful',
            'newscast': 'newscast',
            'sad': 'sad',
            'whispering': 'whispering',
            'scared': 'general',
            'anxious': 'general',
            'neutral': 'general',  # general is the default style
            'happy': 'cheerful',  # mapping for common emotion name
        }

    def synthesize(self, input_json: str) -> bytes:
        """
        Convert input text and emotion data into synthesized speech audio.

        Args:
            input_json (str): JSON string containing text and optional emotion data

        Returns:
            bytes: Audio data in WAV format

        Raises:
            ValueError: If input_json is malformed or missing required fields
        """
        try:
            data = json.loads(input_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in input_json")

        if 'text' not in data:
            raise ValueError("Missing 'text' field in input_json")

        text = data['text']
        emotion = data.get('emotion', 'neutral')

        # Create speech config - updated approach (2025)
        if self.endpoint:
            # Using endpoint (recommended for 2025)
            speech_config = speechsdk.SpeechConfig(
                endpoint=self.endpoint, subscription=self.subscription_key
            )
        else:
            # Fallback to subscription + region
            if not self.subscription_key or not self.region:
                raise ValueError("Either endpoint OR (subscription_key + region) must be provided")
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key, region=self.region
            )

        speech_config.speech_synthesis_voice_name = self.voice_name

        # Create synthesizer with memory stream
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        # Apply emotion and synthesize
        self.set_emotion(synthesizer, emotion)

        # Create SSML with emotion style
        ssml = self._create_ssml(text, emotion)

        # Synthesize speech
        result = synthesizer.speak_ssml_async(ssml).get()

        # Handle results like in C# example
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_msg += f" | ErrorCode: {cancellation_details.error_code}"
                error_msg += f" | ErrorDetails: {cancellation_details.error_details}"
                error_msg += " | Check if speech resource key and endpoint are correct"
            raise RuntimeError(error_msg)
        else:
            raise RuntimeError(f"Speech synthesis failed: {result.reason}")

    def set_emotion(self, engine: Any, emotion: str) -> None:
        """
        Configure the TTS engine to reflect the specified emotion.
        Note: For Azure TTS, emotion is applied via SSML, not engine configuration.

        Args:
            engine (Any): The Azure SpeechSynthesizer instance
            emotion (str): The emotion to apply
        """
        # Azure emotions are applied via SSML, so this method serves as validation
        if emotion not in self.emotion_styles:
            available_emotions = ", ".join(self.emotion_styles.keys())
            raise ValueError(f"Unsupported emotion: '{emotion}'. Available: {available_emotions}")

    def _create_ssml(self, text: str, emotion: str) -> str:
        """
        Create SSML markup with emotion styling.
        Updated for Feb 2025 Azure AI Speech changes.

        Args:
            text (str): Text to synthesize
            emotion (str): Emotion style to apply

        Returns:
            str: SSML markup string
        """
        style = self.emotion_styles.get(emotion, 'general')

        # Updated SSML format for Azure AI Speech (2025)
        ssml = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
               xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{self.voice_name}">
                <mstts:express-as style="{style}">
                    {text}
                </mstts:express-as>
            </voice>
        </speak>
        '''

        return ssml.strip()

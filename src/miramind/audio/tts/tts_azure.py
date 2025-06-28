import json

import azure.cognitiveservices.speech as speechsdk

from ...shared.logger import logger
from .tts_base import TTSProvider


class AzureTTSProvider(TTSProvider):
    """
    Azure Cognitive Services Text-to-Speech provider with emotion support.
    """

    def __init__(
        self,
        subscription_key: str,
        endpoint: str,
        voice_name: str = "en-US-JennyNeural",
    ):
        """
        Initialize Azure TTS provider.

        Args:
            subscription_key (str, optional): Azure Cognitive Services subscription key
            endpoint (str, optional): Azure Speech service endpoint URL
            voice_name (str): Voice to use (default: en-US-JennyNeural - supports 14+ emotion styles as of Feb 2025)
        """
        self.subscription_key = subscription_key
        self.endpoint = endpoint
        self.voice_name = voice_name

        # Define emotion styles mapping
        self.emotion_styles = {
            'angry': 'calm',
            'assistant': 'assistant',
            'cheerful': 'cheerful',
            'chat': 'chat',
            'excited': 'excited',
            'friendly': 'friendly',
            'hopeful': 'hopeful',
            'newscast': 'newscast',
            'sad': 'hopeful',
            'scared': 'calm',
            'terrified': 'calm',
            'unfriendly': 'friendly',
            'whispering': 'whispering',
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
            logger.error("Invalid JSON format in input_json")
            raise ValueError("Invalid JSON format in input_json")

        if 'text' not in data:
            logger.error("Missing 'text' field in input_json")
            raise ValueError("Missing 'text' field in input_json")

        text = data['text']
        emotion = data.get('emotion', 'neutral')

        logger.debug(f"Synthesizing speech for text: '{text[:30]}...' with emotion: '{emotion}'")

        # Create speech config - updated approach (2025)
        if self.endpoint and self.subscription_key:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key, endpoint=self.endpoint
            )

        speech_config.speech_synthesis_voice_name = (
            self.voice_name
        )  # Create synthesizer with memory stream
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        # Apply emotion and get formatted text (SSML)
        formatted_text = self.set_emotion(text, emotion)

        # Synthesize speech using the formatted text
        result = synthesizer.speak_ssml_async(formatted_text).get()

        # Check result status
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.debug("Speech synthesis completed successfully.")
            return result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_msg += f" | ErrorCode: {cancellation_details.error_code}"
                error_msg += f" | ErrorDetails: {cancellation_details.error_details}"
                error_msg += "  | Check if speech resource key and endpoint are correct"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.error(f"Speech synthesis failed: {result.reason}")
            raise RuntimeError(f"Speech synthesis failed: {result.reason}")

    def set_emotion(self, text: str, emotion: str) -> str:
        """
        Apply emotion to text and return SSML markup with emotion styling.

        Args:
            text (str): The original text to synthesize
            emotion (str): The emotion to apply

        Returns:
            str: SSML markup with emotion styling applied

        Raises:
            ValueError: If emotion is not supported
        """
        logger.info(f"Setting emotion '{emotion}'")
        # Validate emotion
        if emotion not in self.emotion_styles:
            available_emotions = ", ".join(self.emotion_styles.keys())
            raise ValueError(f"Unsupported emotion: '{emotion}'. Available: {available_emotions}")

        # Return formatted SSML
        return self._create_ssml(text, emotion)

    def _create_ssml(self, text: str, emotion: str) -> str:
        """
        Create SSML markup with emotion styling.

        Args:
            text (str): Text to synthesize
            emotion (str): Emotion style to apply

        Returns:
            str: SSML markup string
        """
        logger.info(f"Creating SSML for emotion '{emotion}'")
        style = self.emotion_styles.get(emotion, 'general')

        # Support for correct SSML structure
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
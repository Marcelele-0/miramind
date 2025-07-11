"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { useState } from "react";

// Import custom components
import {
  AudioControls,
  AudioVisualizer,
  BotResponse,
  ChatHistory,
  EndCallButton,
  LoadingIndicator,
  ModeToggle,
  StartCallScreen,
  TextInput,
  VoiceInput,
} from "@/components/call";

// Import custom hooks
import { useAudio } from "@/hooks/useAudio";
import { useVoiceRecording } from "@/hooks/useVoiceRecording";

export default function CallPage() {
  const router = useRouter();

  // State management
  const [userInput, setUserInput] = useState("");
  const [botText, setBotText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [recordingMode, setRecordingMode] =
    useState("text");

  // Custom hooks
  const { audioRef, volume, isPlaying, playAudioResponse } =
    useAudio();
  const {
    isRecording,
    recordingTimer,
    startRecording,
    stopRecording,
  } = useVoiceRecording();

  // Handle text input submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    setIsLoading(true);
    setBotText("");

    try {
      const res = await fetch(
        "http://localhost:8000/api/chat/message",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userInput,
            chatHistory,
            sessionId, // Include session ID
          }),
        }
      );

      const data = await res.json();
      console.log("API response:", data);
      console.log("Response text:", data.response_text);
      console.log("Audio file path:", data.audio_file_path);

      const botResponse =
        data.response_text || "No response";
      const audioPath = data.audio_file_path;

      setBotText(botResponse);
      setUserInput("");

      setChatHistory((prevHistory) => [
        ...prevHistory,
        { role: "user", content: userInput },
        { role: "assistant", content: botResponse },
      ]);

      if (audioRef.current && audioPath) {
        // Use the new enhanced audio playback function
        await playAudioResponse(audioPath);
      } else {
        console.log(
          "No audio path provided or audio ref not available"
        );
      }
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartCall = async () => {
    try {
      const res = await fetch(
        "http://localhost:8000/api/chat/start",
        {
          method: "POST",
        }
      );

      const data = await res.json();
      console.log("Chat start:", data);
      setSessionId(data.sessionId); // Store session ID
      setHasStarted(true);
    } catch (err) {
      console.error("Error starting chat:", err);
    }
  };

  // Handle voice recording with custom hook
  const handleStartRecording = async () => {
    try {
      await startRecording();
    } catch (error) {
      console.error("Error starting recording:", error);
    }
  };

  const handleStopRecording = async () => {
    try {
      const audioBlob = await stopRecording();
      if (audioBlob) {
        await processVoiceInput(audioBlob);
      }
    } catch (error) {
      console.error("Error stopping recording:", error);
    }
  };

  const processVoiceInput = async (audioBlob) => {
    setIsLoading(true);
    setBotText("");

    try {
      // Convert audio blob to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64Audio = reader.result.split(",")[1]; // Remove data URL prefix

        // Send to voice chat endpoint
        const res = await fetch(
          "http://localhost:8000/api/voice/chat",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              audioData: base64Audio,
              chatHistory,
              sessionId,
            }),
          }
        );

        const data = await res.json();
        console.log("Voice API response:", data);

        const botResponse =
          data.response_text || "No response";
        const audioPath = data.audio_file_path;
        const transcription =
          data.transcript || "Could not transcribe";

        setBotText(botResponse);

        // Update chat history with transcription as user input
        setChatHistory((prevHistory) => [
          ...prevHistory,
          { role: "user", content: `🎤 ${transcription}` },
          { role: "assistant", content: botResponse },
        ]);

        // Play audio response if available
        if (audioRef.current && audioPath) {
          await playAudioResponse(audioPath);
        }
      };

      reader.readAsDataURL(audioBlob);
    } catch (error) {
      console.error("Error processing voice input:", error);
      setBotText(
        "Sorry, I couldn't process your voice input."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Render start screen if call hasn't started
  if (!hasStarted) {
    return (
      <StartCallScreen onStartCall={handleStartCall} />
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-[#c7afd5]">
      {/* End Call Button */}
      <div className="absolute top-6 left-6">
        <Button
          onClick={() => router.push("/")}
          className="bg-[#e61010] hover:bg-[#b16161] text-white"
        >
          End Call
        </Button>
      </div>

      {/* Audio Visualizer */}
      <AudioVisualizer
        isPlaying={isPlaying}
        volume={volume}
      />

      <Card className="w-full max-w-lg bg-[#dcd3f2]">
        <CardContent className="p-6">
          {/* Mode Toggle */}
          <ModeToggle
            recordingMode={recordingMode}
            onModeChange={setRecordingMode}
          />

          {/* Text Input Mode */}
          {recordingMode === "text" && (
            <TextInput
              userInput={userInput}
              onInputChange={setUserInput}
              onSubmit={handleSubmit}
              isLoading={isLoading}
            />
          )}

          {/* Voice Input Mode */}
          {recordingMode === "voice" && (
            <VoiceInput
              isRecording={isRecording}
              isLoading={isLoading}
              recordingTimer={recordingTimer}
              onStartRecording={handleStartRecording}
              onStopRecording={handleStopRecording}
            />
          )}

          {/* Loading Indicator */}
          <LoadingIndicator isLoading={isLoading} />

          {/* Bot Response */}
          <BotResponse botText={botText} />

          {/* Chat History */}
          <ChatHistory chatHistory={chatHistory} />

          {/* Audio Controls */}
          <AudioControls ref={audioRef} />

          {/* End Call Button */}
          <EndCallButton
            onEndCall={() => router.push("/")}
          />
        </CardContent>
      </Card>
    </main>
  );
}

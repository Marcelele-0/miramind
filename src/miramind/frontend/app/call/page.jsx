"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import audioUtils from "@/lib/audioUtils";
import { useEffect, useRef, useState } from "react";

export default function CallPage() {
  const [userInput, setUserInput] = useState("");
  const [botText, setBotText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [volume, setVolume] = useState(0);
  const [sessionId, setSessionId] = useState(null); // Track current session

  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [recordingTimer, setRecordingTimer] = useState(0);
  const [recordingMode, setRecordingMode] =
    useState("text"); // 'text' or 'voice'

  const audioRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioCtxRef = useRef(null);
  const sourceRef = useRef(null);
  const timerRef = useRef(null);
  const audioElementConnected = useRef(false); // Track if audio element is connected

  const startAudioVisualization = () => {
    try {
      // Ensure we have a valid audio context
      if (!audioCtxRef.current) {
        console.error(
          "No audio context available for visualization"
        );
        return;
      }

      // Create source node only if audio element hasn't been connected before
      if (
        audioRef.current &&
        !audioElementConnected.current
      ) {
        try {
          // Disconnect old source if it exists
          if (sourceRef.current) {
            try {
              sourceRef.current.disconnect();
            } catch (e) {
              console.log(
                "Error disconnecting old source:",
                e
              );
            }
          }

          // Create new source node for the current context
          sourceRef.current =
            audioCtxRef.current.createMediaElementSource(
              audioRef.current
            );
          audioElementConnected.current = true; // Mark as connected
          console.log("Created new audio source node");
        } catch (error) {
          console.error(
            "Error creating MediaElementSource:",
            error
          );

          // If we can't create a source, skip visualization but still allow audio playback
          console.log(
            "Skipping visualization due to MediaElementSource error"
          );
          return;
        }
      } else if (
        audioRef.current &&
        audioElementConnected.current
      ) {
        console.log(
          "Audio element already connected, reusing existing source"
        );

        // If we have an existing source but it's from a different context, we can't use it
        if (
          sourceRef.current &&
          sourceRef.current.context !== audioCtxRef.current
        ) {
          console.log(
            "Source is from different context, skipping visualization"
          );
          return;
        }
      }

      const analyser = audioCtxRef.current.createAnalyser();
      analyser.fftSize = 256;

      const dataArray = new Uint8Array(
        analyser.frequencyBinCount
      );

      // Only connect if we have a valid source for this context
      if (
        sourceRef.current &&
        sourceRef.current.context === audioCtxRef.current
      ) {
        try {
          sourceRef.current.connect(analyser);
          console.log("Connected source to analyser");
        } catch (error) {
          console.error(
            "Error connecting source to analyser:",
            error
          );
          return;
        }
      } else {
        console.log(
          "No valid source for current context, skipping visualization"
        );
        return;
      }

      analyser.connect(audioCtxRef.current.destination);
      analyserRef.current = analyser;

      const update = () => {
        if (
          analyserRef.current &&
          audioCtxRef.current &&
          audioCtxRef.current.state === "running"
        ) {
          analyserRef.current.getByteFrequencyData(
            dataArray
          );
          const avg =
            dataArray.reduce((sum, val) => sum + val, 0) /
            dataArray.length;
          setVolume(avg);
          animationFrameRef.current =
            requestAnimationFrame(update);
        }
      };

      update();
    } catch (error) {
      console.error(
        "Error in startAudioVisualization:",
        error
      );
    }
  };

  // Simplified audio playback function that avoids MediaElementSource issues
  const playAudioResponse = async (audioPath) => {
    try {
      console.log(
        "=== Starting simplified audio playback ==="
      );

      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;

        // Remove all event listeners
        audioRef.current.onended = null;
        audioRef.current.onerror = null;
        audioRef.current.oncanplay = null;
        audioRef.current.onloadeddata = null;
      }

      // Clean up existing audio context and visualization
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }

      if (sourceRef.current) {
        try {
          sourceRef.current.disconnect();
        } catch (e) {
          console.log("Error disconnecting source:", e);
        }
        sourceRef.current = null;
      }

      if (audioCtxRef.current) {
        try {
          if (audioCtxRef.current.state !== "closed") {
            await audioCtxRef.current.close();
          }
        } catch (e) {
          console.log("Error closing audio context:", e);
        }
        audioCtxRef.current = null;
      }

      // Reset states
      setVolume(0);
      setIsPlaying(false);

      // Try loading audio from different endpoints
      const timestamp = Date.now();
      const audioSources = [
        `/output.wav?t=${timestamp}`,
        `/api/audio/output.wav?t=${timestamp}`,
        `/static/output.wav?t=${timestamp}`,
      ];

      let audioLoaded = false;

      for (const src of audioSources) {
        try {
          console.log(
            `Attempting to load audio from: ${src}`
          );

          // Set the source
          audioRef.current.src = src;
          audioRef.current.load();

          // Wait for the audio to be ready
          await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
              reject(new Error("Audio load timeout"));
            }, 5000);

            const onCanPlay = () => {
              clearTimeout(timeout);
              audioRef.current.removeEventListener(
                "canplay",
                onCanPlay
              );
              audioRef.current.removeEventListener(
                "error",
                onError
              );
              audioRef.current.removeEventListener(
                "loadeddata",
                onLoadedData
              );
              resolve();
            };

            const onLoadedData = () => {
              clearTimeout(timeout);
              audioRef.current.removeEventListener(
                "canplay",
                onCanPlay
              );
              audioRef.current.removeEventListener(
                "error",
                onError
              );
              audioRef.current.removeEventListener(
                "loadeddata",
                onLoadedData
              );
              resolve();
            };

            const onError = (error) => {
              clearTimeout(timeout);
              audioRef.current.removeEventListener(
                "canplay",
                onCanPlay
              );
              audioRef.current.removeEventListener(
                "error",
                onError
              );
              audioRef.current.removeEventListener(
                "loadeddata",
                onLoadedData
              );
              reject(error);
            };

            audioRef.current.addEventListener(
              "canplay",
              onCanPlay,
              { once: true }
            );
            audioRef.current.addEventListener(
              "loadeddata",
              onLoadedData,
              { once: true }
            );
            audioRef.current.addEventListener(
              "error",
              onError,
              { once: true }
            );
          });

          console.log(
            `✓ Audio loaded successfully from: ${src}`
          );
          audioLoaded = true;
          break;
        } catch (error) {
          console.log(
            `✗ Failed to load audio from ${src}:`,
            error
          );
          continue;
        }
      }

      if (!audioLoaded) {
        throw new Error(
          "Failed to load audio from any source"
        );
      }

      // Set up simple event handlers (no visualization)
      audioRef.current.onended = () => {
        console.log("Audio playback ended");
        setIsPlaying(false);
        setVolume(0);
      };

      audioRef.current.onerror = (error) => {
        console.error("Audio playback error:", error);
        setIsPlaying(false);
        setVolume(0);
      };

      // Simple volume simulation without WebAudio API
      const simulateVolume = () => {
        if (
          audioRef.current &&
          !audioRef.current.paused &&
          !audioRef.current.ended
        ) {
          // Simulate volume with a simple animation
          const currentTime =
            audioRef.current.currentTime || 0;
          const duration = audioRef.current.duration || 1;
          const progress = currentTime / duration;

          // Create a simple wave-like volume effect
          const simVolume =
            Math.sin(currentTime * 10) * 20 + 30;
          setVolume(Math.abs(simVolume));

          animationFrameRef.current =
            requestAnimationFrame(simulateVolume);
        } else {
          setVolume(0);
        }
      };

      // Play the audio
      console.log("Starting audio playback...");
      await audioRef.current.play();
      setIsPlaying(true);
      console.log("✓ Audio playback started successfully");

      // Start volume simulation
      simulateVolume();
    } catch (error) {
      console.error("Error in playAudioResponse:", error);
      setIsPlaying(false);
      setVolume(0);

      // Clean up on error
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    }
  };

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

  // Voice recording functions
  const startRecording = async () => {
    try {
      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, {
          type: "audio/wav",
        });
        await processVoiceInput(audioBlob);

        // Stop all tracks to stop recording indicator
        stream.getTracks().forEach((track) => track.stop());

        // Reset timer
        clearInterval(timerRef.current);
        setRecordingTimer(0);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordedChunks(chunks);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTimer((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error("Error starting recording:", error);
      alert(
        "Unable to access microphone. Please check permissions."
      );
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorder &&
      mediaRecorder.state !== "inactive"
    ) {
      mediaRecorder.stop();
      setIsRecording(false);
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

  const formatTime = (seconds) =>
    audioUtils.formatTime(seconds);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
      ) {
        mediaRecorder.stop();
      }

      // Clean up audio source
      if (sourceRef.current) {
        try {
          sourceRef.current.disconnect();
        } catch (e) {
          console.log(
            "Error disconnecting source on cleanup:",
            e
          );
        }
        sourceRef.current = null;
      }

      // Reset audio element connection flag
      audioElementConnected.current = false;

      // Clean up audio context
      if (audioCtxRef.current) {
        try {
          if (audioCtxRef.current.state !== "closed") {
            audioCtxRef.current.close();
          }
        } catch (e) {
          console.log(
            "Error closing audio context on cleanup:",
            e
          );
        }
        audioCtxRef.current = null;
      }

      // Clean up animation frame
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }

      setVolume(0);
    };
  }, [mediaRecorder]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  if (!hasStarted) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-[#c7afd5] bg-[url('/images/background.png')] bg-cover bg-center">
        <div className="w-72 h-72 rounded-full bg-[#dcd3f2] mb-10 flex items-center justify-center">
          <img
            src="/images/sound.png"
            alt="sound"
            width={250}
            height={250}
          />
        </div>
        <Button
          onClick={handleStartCall}
          className="mb-4 bg-[#4dff5f] hover:bg-[#468345]"
        >
          Start a Call
        </Button>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-[#c7afd5]">
      <div className="w-72 h-72 rounded-full bg-[#dcd3f2] mb-10 flex items-center justify-center">
        <img
          src="/images/sound.png"
          alt="sound"
          width={250}
          height={250}
          style={{
            transform: `scale(${Math.min(
              1 + volume / 100,
              1.5
            )})`,
            transition: "transform 0.05s linear",
          }}
        />
      </div>

      <Card className="w-full max-w-lg bg-[#dcd3f2]">
        <CardContent className="p-6">
          {/* Mode Toggle */}
          <div className="flex mb-4 space-x-2">
            <Button
              type="button"
              onClick={() => setRecordingMode("text")}
              variant={
                recordingMode === "text"
                  ? "default"
                  : "outline"
              }
              className="flex-1"
            >
              💬 Text
            </Button>
            <Button
              type="button"
              onClick={() => setRecordingMode("voice")}
              variant={
                recordingMode === "voice"
                  ? "default"
                  : "outline"
              }
              className="flex-1"
            >
              🎤 Voice
            </Button>
          </div>

          {/* Text Input Mode */}
          {recordingMode === "text" && (
            <form
              onSubmit={handleSubmit}
              className="flex space-x-2"
            >
              <Input
                type="text"
                placeholder="Type your message..."
                value={userInput}
                onChange={(e) =>
                  setUserInput(e.target.value)
                }
                disabled={isLoading}
              />
              <Button
                type="submit"
                disabled={isLoading}
                className="bg-[#f9c6cd] hover:bg-[#e8b0b5] text-white"
              >
                Send
              </Button>
            </form>
          )}

          {/* Voice Input Mode */}
          {recordingMode === "voice" && (
            <div className="flex flex-col space-y-4">
              <div className="flex items-center justify-center space-x-4">
                {!isRecording ? (
                  <Button
                    onClick={startRecording}
                    disabled={isLoading}
                    className="bg-[#4dff5f] hover:bg-[#468345] text-white px-8 py-4 rounded-full text-lg"
                  >
                    🎤 Start Recording
                  </Button>
                ) : (
                  <div className="flex flex-col items-center space-y-2">
                    <Button
                      onClick={stopRecording}
                      className="bg-red-500 hover:bg-red-600 text-white px-8 py-4 rounded-full text-lg animate-pulse"
                    >
                      ⏹️ Stop Recording
                    </Button>
                    <div className="text-sm text-gray-600">
                      Recording:{" "}
                      {formatTime(recordingTimer)}
                    </div>
                  </div>
                )}
              </div>

              {isRecording && (
                <div className="flex justify-center">
                  <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="ml-2 text-sm text-gray-600">
                    Recording in progress...
                  </span>
                </div>
              )}
            </div>
          )}

          {isLoading && (
            <div className="mt-4 flex justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-sm text-gray-600">
                Processing...
              </span>
            </div>
          )}

          <div className="mt-6 text-white">
            <h3 className="text-lg font-semibold mb-2">
              Bot response:
            </h3>
            <p>{botText}</p>
          </div>

          <div className="mt-6 text-white">
            <h3 className="text-lg font-semibold mb-2">
              Conversation:
            </h3>
            <div className="max-h-60 overflow-y-auto space-y-1">
              {chatHistory.map((entry, index) => (
                <p key={index}>
                  <strong>
                    {entry.role === "user" ? "You" : "Bot"}:
                  </strong>{" "}
                  {entry.content}
                </p>
              ))}
            </div>
          </div>

          <audio
            ref={audioRef}
            controls
            className="mt-6 w-full glassmorphism"
          />
        </CardContent>
      </Card>
    </main>
  );
}

"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useRef, useState } from "react";

export default function CallPage() {
  const [userInput, setUserInput] = useState("");
  const [botText, setBotText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [volume, setVolume] = useState(0);
  const [sessionId, setSessionId] = useState(null);  // Track current session

  const audioRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioCtxRef = useRef(null);
  const sourceRef = useRef(null);

  const startAudioVisualization = () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext ||
        window.webkitAudioContext)();
    }

    if (!sourceRef.current && audioRef.current) {
      sourceRef.current =
        audioCtxRef.current.createMediaElementSource(
          audioRef.current
        );
    }

    const analyser = audioCtxRef.current.createAnalyser();
    analyser.fftSize = 256;

    const dataArray = new Uint8Array(
      analyser.frequencyBinCount
    );

    if (sourceRef.current) {
      sourceRef.current.connect(analyser);
    }
    analyser.connect(audioCtxRef.current.destination);
    analyserRef.current = analyser;

    const update = () => {
      analyser.getByteFrequencyData(dataArray);
      const avg =
        dataArray.reduce((sum, val) => sum + val, 0) /
        dataArray.length;
      setVolume(avg);
      animationFrameRef.current =
        requestAnimationFrame(update);
    };

    update();
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
            sessionId,  // Include session ID
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
        // Try multiple audio endpoints with cache busting
        const timestamp = Date.now();
        const audioSources = [
          `/output.wav?t=${timestamp}`,
          `/api/audio/output.wav?t=${timestamp}`,
          `/static/output.wav?t=${timestamp}`,
        ];

        let audioLoaded = false;

        const tryLoadAudio = async (sources) => {
          for (const src of sources) {
            try {
              console.log(
                `Trying to load audio from: ${src}`
              );
              audioRef.current.src = src;
              audioRef.current.load();

              // Wait for the audio to load or error
              await new Promise((resolve, reject) => {
                const onLoad = () => {
                  audioRef.current.removeEventListener(
                    "canplay",
                    onLoad
                  );
                  audioRef.current.removeEventListener(
                    "error",
                    onError
                  );
                  resolve();
                };

                const onError = (err) => {
                  audioRef.current.removeEventListener(
                    "canplay",
                    onLoad
                  );
                  audioRef.current.removeEventListener(
                    "error",
                    onError
                  );
                  reject(err);
                };

                audioRef.current.addEventListener(
                  "canplay",
                  onLoad
                );
                audioRef.current.addEventListener(
                  "error",
                  onError
                );
              });

              // If we get here, audio loaded successfully
              console.log(
                `✓ Audio loaded successfully from: ${src}`
              );
              audioLoaded = true;
              break;
            } catch (err) {
              console.log(
                `✗ Failed to load audio from ${src}:`,
                err
              );
              continue;
            }
          }
        };

        try {
          await tryLoadAudio(audioSources);

          if (audioLoaded) {
            startAudioVisualization();
            try {
              await audioRef.current.play();
              setIsPlaying(true);
            } catch (err) {
              console.error("Audio play error:", err);
            }

            audioRef.current.onended = () => {
              setIsPlaying(false);
              if (animationFrameRef.current) {
                cancelAnimationFrame(
                  animationFrameRef.current
                );
              }
              setVolume(0);
            };
          } else {
            console.error(
              "Failed to load audio from any source"
            );
          }
        } catch (err) {
          console.error("Error loading audio:", err);
        }
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
      setSessionId(data.sessionId);  // Store session ID
      setHasStarted(true);
    } catch (err) {
      console.error("Error starting chat:", err);
    }
  };

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
          <form
            onSubmit={handleSubmit}
            className="flex space-x-2"
          >
            <Input
              type="text"
              placeholder="Type your message..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
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

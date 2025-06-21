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

  const audioRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  const startAudioVisualization = () => {
    const audioCtx = new (window.AudioContext ||
      window.webkitAudioContext)();
    const source = audioCtx.createMediaElementSource(
      audioRef.current
    );
    const analyser = audioCtx.createAnalyser();
    const dataArray = new Uint8Array(
      analyser.frequencyBinCount
    );

    analyser.fftSize = 256;
    source.connect(analyser);
    analyser.connect(audioCtx.destination);
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
      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userInput,
          chatHistory,
        }),
      });

      const data = await res.json();
      console.log("API response:", data);

      const botResponse =
        data.response_text || "No response";

      setBotText(botResponse);
      setUserInput("");

      setChatHistory((prevHistory) => [
        ...prevHistory,
        { role: "user", content: userInput },
        { role: "assistant", content: botResponse },
      ]);

      if (data.audio_file_path) {
        const audioSrc = `/output.wav?t=${Date.now()}`;
        if (audioRef.current) {
          audioRef.current.src = audioSrc;

          audioRef.current.oncanplay = async () => {
            startAudioVisualization();
            await audioRef.current.play();
            setIsPlaying(true);

            audioRef.current.onended = () => {
              setIsPlaying(false);
              cancelAnimationFrame(
                animationFrameRef.current
              );
              setVolume(0);
            };
          };
        }
      }
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartCall = async () => {
    try {
      const res = await fetch("/api/chat/start", {
        method: "POST",
      });

      const data = await res.json();
      console.log("Chat start:", data);
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
    <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-[#c7afd5] ">
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

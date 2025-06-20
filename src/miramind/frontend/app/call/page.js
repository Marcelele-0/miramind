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
  const audioRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!userInput.trim()) return;

    setIsLoading(true);
    setBotText("");

    try {
      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userInput }), // FIXED: match backend expectation
      });

      const data = await res.json();
      console.log("API response:", data);

      setBotText(data.response_text || "No response");
      setUserInput("");

      if (data.audio_file_path) {
        const audioSrc = `/output.wav?t=${Date.now()}`; // prevent caching
        if (audioRef.current) {
          audioRef.current.src = audioSrc;
          await audioRef.current.play();
          setIsPlaying(true);

          audioRef.current.onended = () => {
            setIsPlaying(false);
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
    } catch (err) {
      console.error("Error starting chat:", err);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24 ">
      <Button onClick={handleStartCall} className="mb-4">
        Start a Call
      </Button>

      <Card className="w-full max-w-lg">
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
            <Button type="submit" disabled={isLoading}>
              Send
            </Button>
          </form>

          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">
              Bot response:
            </h3>
            <p>{botText}</p>
          </div>

          <audio
            ref={audioRef}
            controls
            className="mt-6 w-full"
          />
        </CardContent>
      </Card>
    </main>
  );
}

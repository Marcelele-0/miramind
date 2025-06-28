"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRef, useState } from "react";

export default function CallPage() {
  const [hasStarted, setHasStarted] = useState(false);
  const [userInput, setUserInput] = useState("");
  const [botText, setBotText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const handleStartCall = async () => {
    try {
      const res = await fetch("/api/chat/start", {
        method: "POST",
      });

      const data = await res.json();
      console.log("Start call:", data);
      if (data.message === "Chat started") {
        setHasStarted(true);
      } else {
        console.error("Failed to start chat");
      }
    } catch (err) {
      console.error("Error starting chat:", err);
    }
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
          chatHistory: [], // optional: send history here
        }),
      });

      const data = await res.json();

      if (data.error) {
        console.error("API error:", data.error);
        setBotText("Sorry, something went wrong.");
        setIsPlaying(false);
      } else {
        setBotText(data.response_text || "No response");

        if (data.audio_file_path) {
          audioRef.current.src =
            "/output.wav?" + Date.now();
          audioRef.current
            .play()
            .catch((err) =>
              console.error("Audio play error:", err)
            );
          setIsPlaying(true);
        } else {
          setIsPlaying(false);
        }
      }
    } catch (error) {
      console.error("Fetch error:", error);
      setBotText("Sorry, something went wrong.");
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
      setUserInput("");
    }
  };

  if (!hasStarted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#c7afd5]">
        <Button
          onClick={handleStartCall}
          className="text-white text-xl px-8 py-4 rounded-lg bg-[#4dff5f] hover:bg-[#468345]"
        >
          Start a Call
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#c7afd5]">
      <div className="w-72 h-72 rounded-full bg-[#dcd3f2] mb-10 flex items-center justify-center">
        <img
          src="/images/sound.png"
          alt="sound"
          width={250}
          height={250}
          className={
            isPlaying || isLoading ? "animate-pulse" : ""
          }
        />
      </div>

      {botText && (
        <div className="bg-[#f9c6cd] text-white text-sm font-medium px-6 py-3 rounded-xl mb-6">
          {botText}
        </div>
      )}

      {isLoading && !isPlaying && (
        <div className="bg-[#a09eec] text-white text-sm font-medium px-6 py-3 rounded-xl mb-6">
          Thinking...
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="flex flex-col items-center gap-4 w-full max-w-sm px-4"
      >
        <Input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="Type your message"
          disabled={isLoading}
          className="px-4 py-2 rounded-lg border focus:outline-none text-black w-full"
        />
        <Button
          type="submit"
          disabled={isLoading || !userInput.trim()}
          className="bg-[#7c4dff] text-white w-full px-4 py-2 rounded-lg hover:bg-[#673ab7]"
        >
          {isLoading ? "Sending..." : "Send"}
        </Button>
      </form>

      {isPlaying && (
        <div className="mt-6">
          <audio ref={audioRef} controls />
        </div>
      )}
    </div>
  );
}

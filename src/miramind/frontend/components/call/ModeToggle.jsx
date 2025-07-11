"use client";

import { Button } from "@/components/ui/button";

export default function ModeToggle({
  recordingMode,
  onModeChange,
}) {
  return (
    <div className="flex mb-4 space-x-2">
      <Button
        type="button"
        onClick={() => onModeChange("text")}
        variant={
          recordingMode === "text" ? "default" : "outline"
        }
        className="flex-1"
      >
        💬 Text
      </Button>
      <Button
        type="button"
        onClick={() => onModeChange("voice")}
        variant={
          recordingMode === "voice" ? "default" : "outline"
        }
        className="flex-1"
      >
        🎤 Voice
      </Button>
    </div>
  );
}

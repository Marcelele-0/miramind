"use client";

import { Button } from "@/components/ui/button";
import audioUtils from "@/lib/audioUtils";

export default function VoiceInput({
  isRecording,
  isLoading,
  recordingTimer,
  onStartRecording,
  onStopRecording,
}) {
  const formatTime = (seconds) =>
    audioUtils.formatTime(seconds);

  return (
    <div className="flex flex-col space-y-4">
      <div className="flex items-center justify-center space-x-4">
        {!isRecording ? (
          <Button
            onClick={onStartRecording}
            disabled={isLoading}
            className="bg-[#4dff5f] hover:bg-[#468345] text-white px-8 py-4 rounded-full text-lg"
          >
            🎤 Start Recording
          </Button>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <Button
              onClick={onStopRecording}
              className="bg-red-500 hover:bg-red-600 text-white px-8 py-4 rounded-full text-lg animate-pulse"
            >
              ⏹️ Stop Recording
            </Button>
            <div className="text-sm text-gray-600">
              Recording: {formatTime(recordingTimer)}
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
  );
}

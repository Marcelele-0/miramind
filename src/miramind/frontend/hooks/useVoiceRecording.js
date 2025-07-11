"use client";

import { useEffect, useRef, useState } from "react";

export function useVoiceRecording() {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [recordingTimer, setRecordingTimer] = useState(0);
  const [currentStream, setCurrentStream] = useState(null);

  const timerRef = useRef(null);

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

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordedChunks(chunks);
      setCurrentStream(stream);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTimer((prev) => prev + 1);
      }, 1000);

      return { recorder, chunks, stream };
    } catch (error) {
      console.error("Error starting recording:", error);
      alert(
        "Unable to access microphone. Please check permissions."
      );
      throw error;
    }
  };

  const stopRecording = () => {
    return new Promise((resolve) => {
      if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
      ) {
        const chunks = recordedChunks;

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(chunks, {
            type: "audio/wav",
          });

          // Stop all tracks to stop recording indicator
          if (currentStream) {
            currentStream
              .getTracks()
              .forEach((track) => track.stop());
            setCurrentStream(null);
          }

          // Reset timer
          clearInterval(timerRef.current);
          setRecordingTimer(0);

          resolve(audioBlob);
        };

        mediaRecorder.stop();
        setIsRecording(false);
      } else {
        resolve(null);
      }
    });
  };

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
      ) {
        mediaRecorder.stop();
      }
      if (currentStream) {
        currentStream
          .getTracks()
          .forEach((track) => track.stop());
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [mediaRecorder, currentStream]);

  return {
    isRecording,
    recordingTimer,
    startRecording,
    stopRecording,
  };
}

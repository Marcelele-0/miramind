"use client";

import { useEffect, useRef, useState } from "react";

export function useAudio() {
  const [volume, setVolume] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const audioRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioCtxRef = useRef(null);
  const sourceRef = useRef(null);
  const audioElementConnected = useRef(false);

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
          audioElementConnected.current = true;
          console.log("Created new audio source node");
        } catch (error) {
          console.error(
            "Error creating MediaElementSource:",
            error
          );
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

      // Enhanced volume simulation with more realistic audio-correlated animation
      const simulateVolume = () => {
        if (
          audioRef.current &&
          !audioRef.current.paused &&
          !audioRef.current.ended
        ) {
          const currentTime =
            audioRef.current.currentTime || 0;
          const duration = audioRef.current.duration || 1;

          // Create multiple frequency components for more realistic visualization
          const baseFreq = Math.sin(currentTime * 8) * 25;
          const midFreq = Math.sin(currentTime * 15) * 15;
          const highFreq = Math.sin(currentTime * 25) * 10;

          // Add some randomness to simulate speech patterns
          const speechPattern = Math.random() * 20;

          // Combine frequencies with some decay for natural feel
          const combinedVolume = Math.abs(
            baseFreq + midFreq + highFreq + speechPattern
          );

          // Add slight pulsing effect
          const pulse = Math.sin(currentTime * 3) * 5 + 5;

          setVolume(Math.min(combinedVolume + pulse, 80));

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

  // Cleanup effect
  useEffect(() => {
    return () => {
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
  }, []);

  return {
    audioRef,
    volume,
    isPlaying,
    playAudioResponse,
    startAudioVisualization,
  };
}

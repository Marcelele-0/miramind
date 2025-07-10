/**
 * Audio utilities for voice recording and processing
 */

export const audioUtils = {
  /**
   * Check if the browser supports audio recording
   */
  isRecordingSupported: () => {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia
    );
  },

  /**
   * Convert audio blob to base64
   */
  blobToBase64: (blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result.split(",")[1]; // Remove data URL prefix
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  },

  /**
   * Format recording time
   */
  formatTime: (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds
      .toString()
      .padStart(2, "0")}`;
  },

  /**
   * Get audio recording constraints
   */
  getRecordingConstraints: () => {
    return {
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 44100,
        channelCount: 1,
      },
    };
  },

  /**
   * Create audio recorder with proper settings
   */
  createRecorder: (stream, onDataAvailable, onStop) => {
    const recorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus", // Fallback to other formats if needed
    });

    recorder.ondataavailable = onDataAvailable;
    recorder.onstop = onStop;

    return recorder;
  },

  /**
   * Stop all media tracks
   */
  stopTracks: (stream) => {
    if (stream && stream.getTracks) {
      stream.getTracks().forEach((track) => track.stop());
    }
  },
};

export default audioUtils;

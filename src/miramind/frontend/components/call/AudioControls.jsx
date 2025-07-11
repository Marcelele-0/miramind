"use client";

import { forwardRef } from "react";

const AudioControls = forwardRef(function AudioControls(
  props,
  ref
) {
  return (
    <audio
      ref={ref}
      controls
      className="mt-6 w-full glassmorphism"
    />
  );
});

export default AudioControls;

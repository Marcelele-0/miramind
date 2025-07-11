"use client";

export default function AudioVisualizer({
  isPlaying,
  volume,
}) {
  return (
    <div className="w-72 h-72 rounded-full bg-[#dcd3f2] mb-10 flex items-center justify-center relative overflow-hidden">
      {/* Animated background rings when audio is playing */}
      {isPlaying && (
        <>
          <div
            className="absolute inset-0 rounded-full border-4 border-[#4dff5f] opacity-20"
            style={{
              transform: `scale(${Math.min(
                1 + volume / 150,
                1.3
              )})`,
              transition:
                "transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          />
          <div
            className="absolute inset-2 rounded-full border-2 border-[#f9c6cd] opacity-40"
            style={{
              transform: `scale(${Math.min(
                1 + volume / 200,
                1.2
              )})`,
              transition:
                "transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          />
        </>
      )}

      <img
        src="/images/sound.png"
        alt="sound"
        width={250}
        height={250}
        className="relative z-10"
        style={{
          transform: `scale(${Math.min(
            1 + volume / 120,
            1.4
          )}) rotate(${isPlaying ? volume / 20 : 0}deg)`,
          transition:
            "transform 0.15s cubic-bezier(0.4, 0, 0.2, 1)",
          filter: isPlaying
            ? `brightness(${1 + volume / 300}) saturate(${
                1 + volume / 150
              })`
            : "none",
        }}
      />
    </div>
  );
}

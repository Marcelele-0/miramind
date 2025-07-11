"use client";

export default function BotResponse({ botText }) {
  return (
    <div className="mt-6 text-white">
      <h3 className="text-lg font-semibold mb-2">
        Bot response:
      </h3>
      <p>{botText}</p>
    </div>
  );
}

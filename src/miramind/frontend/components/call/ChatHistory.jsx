"use client";

export default function ChatHistory({ chatHistory }) {
  return (
    <div className="mt-6 text-white">
      <h3 className="text-lg font-semibold mb-2">
        Conversation:
      </h3>
      <div className="max-h-60 overflow-y-auto space-y-1">
        {chatHistory.map((entry, index) => (
          <p key={index}>
            <strong>
              {entry.role === "user" ? "You" : "Bot"}:
            </strong>{" "}
            {entry.content}
          </p>
        ))}
      </div>
    </div>
  );
}

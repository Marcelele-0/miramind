"use client";

import { Button } from "@/components/ui/button";

export default function StartCallScreen({ onStartCall }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-[#c7afd5] bg-[url('/images/background.png')] bg-cover bg-center">
      <div className="w-72 h-72 rounded-full bg-[#dcd3f2] mb-10 flex items-center justify-center">
        <img
          src="/images/sound.png"
          alt="sound"
          width={250}
          height={250}
        />
      </div>
      <Button
        onClick={onStartCall}
        className="mb-4 bg-[#4dff5f] hover:bg-[#468345]"
      >
        Start a Call
      </Button>
    </main>
  );
}

"use client";

import { Button } from "@/components/ui/button";

export default function EndCallButton({ onEndCall }) {
  return (
    <div className="mt-4 flex justify-center">
      <Button
        onClick={onEndCall}
        className="bg-[#e61010] hover:bg-[#b16161] text-white px-4 py-2 rounded-full"
      >
        End Call
      </Button>
    </div>
  );
}

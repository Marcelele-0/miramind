"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function TextInput({
  userInput,
  onInputChange,
  onSubmit,
  isLoading,
}) {
  return (
    <form onSubmit={onSubmit} className="flex space-x-2">
      <Input
        type="text"
        placeholder="Type your message..."
        value={userInput}
        onChange={(e) => onInputChange(e.target.value)}
        disabled={isLoading}
      />
      <Button
        type="submit"
        disabled={isLoading}
        className="bg-[#f9c6cd] hover:bg-[#e8b0b5] text-white"
      >
        Send
      </Button>
    </form>
  );
}

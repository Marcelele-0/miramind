"use client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const router = useRouter();

  return (
    <div className="flex justify-center items-center min-h-screen bg-[#d1bada]">
      <div className="grid grid-cols-5 grid-rows-3 gap-2 p-4 bg-[#d1bada] min-h-screen">
        <Card className="col-span-1 row-span-1 flex items-center justify-center">
          <CardContent className="flex items-center justify-center h-full">
            <Image
              src="/icons/logo.svg"
              alt="logo"
              width={180}
              height={180}
            />
          </CardContent>
        </Card>

        {/* Name Card */}
        <Card className="col-span-2 row-span-1 bg-[#f6b9c5] text-white text-3xl font-semibold flex items-center justify-center">
          <CardContent className="relative flex items-center justify-center w-full h-full px-4">
            <span>Antoś</span>
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>

        {/* Emotion Card */}
        <Card className="col-span-2 row-span-1 bg-[#f6b9c5] text-white flex items-center justify-center">
          <CardContent className="relative flex items-center justify-center w-full h-full px-4">
            <span className="text-lg">
              Let me know about your emotions!
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>

        {/* Catch up */}
        <Card className="col-start-1 row-start-2 col-span-1 row-span-2 bg-[#d6ccf0] text-white flex flex-col items-center justify-between p-4">
          <CardContent className="relative flex flex-col items-center justify-center w-full h-full px-4">
            <span className="text-lg mb-20 asboute">
              Want to catch up?
            </span>
            <Image
              src="/gifs/helicopter.gif"
              alt="Helicopter"
              width={178}
              height={178}
              className="mb-4"
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
              onClick={() => router.push("/call")}
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>

        {/* Recent Calls */}
        <Card className="col-start-2 row-start-2 col-span-2 row-span-1 bg-[#e1dbf9] text-white flex items-center justify-center">
          <CardContent className="relative flex items-center justify-center w-full h-full px-4">
            <span className="text-lg">
              Recent calls transcription
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>

        {/* Notes */}
        <Card className="col-start-2 row-start-3 col-span-2 row-span-1 bg-[#f6b9c5] text-white flex items-center justify-center">
          <CardContent className="relative flex items-center justify-center w-full h-full px-4">
            <span className="text-lg">Your notes</span>
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>

        {/* Wind down */}
        <Card className="col-start-4 row-start-2 col-span-1 row-span-2 bg-[#e1dbf9] text-white flex items-center justify-center">
          <CardContent className="relative flex flex-col items-center justify-center w-full h-full px-4">
            <span className="text-lg mb-20 asboute">
              Wind down story
            </span>
            <Image
              src="/gifs/baloon.gif"
              alt="Baloon"
              width={158}
              height={158}
              className="mb-4"
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>

        {/* Customize */}
        <Card className="col-start-5 row-start-2 row-span-2 bg-[#f6b9c5] text-white flex flex-col items-center justify-between p-4">
          <CardContent className="relative flex flex-col items-center justify-center w-full h-full px-4">
            <span className="text-lg mb-20 asboute">
              Customize
            </span>
            <Image
              src="/gifs/rocket.gif"
              alt="Rocket"
              width={158}
              height={158}
              className="mb-4"
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2"
            >
              <ArrowRight />
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

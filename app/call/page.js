import Image from "next/image";

export default function CallPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#c7afd5]">
      <div className="w-72 h-72 rounded-full bg-[#dcd3f2] mb-10 flex items-center justify-center">
        <Image
          src="/images/sound.png"
          alt="sound"
          width={250}
          height={250}
        />
      </div>

      {/* Message Bubble */}
      <div className="bg-[#f9c6cd] text-white text-sm font-medium px-6 py-3 rounded-xl">
        Hi Antoś! How was your presentation?
      </div>
    </div>
  );
}

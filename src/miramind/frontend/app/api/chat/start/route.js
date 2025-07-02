import { spawn } from "child_process";
import path from "path";

let chatProcess = null;

export async function POST() {
  if (chatProcess) {
    return Response.json({
      message: "Chat already started",
    });
  }

  try {
    const pythonFilePath = path.resolve(
      process.cwd(),
      "..",
      "..",
      "..", 
      "src",
      "miramind",
      "llm",
      "langgraph",
      "run_chat.py"
    );

    console.log(
      "Launching Python file at:",
      pythonFilePath
    );

    chatProcess = spawn("python", [pythonFilePath], {
      cwd: process.cwd(), 
      stdio: ["pipe", "pipe", "pipe"],
    });

    chatProcess.stdout.on("data", (data) => {
      console.log(`stdout: ${data}`);
    });

    chatProcess.stderr.on("data", (data) => {
      console.error(`stderr: ${data}`);
    });

    chatProcess.on("close", (code) => {
      console.log(`Chat process exited with code ${code}`);
      chatProcess = null;
    });

    console.log("Chat process started");
    return Response.json({ message: "Chat started" });
  } catch (error) {
    console.error("Failed to start chat process:", error);
    return Response.json(
      { error: "Failed to start chat process" },
      { status: 500 }
    );
  }
}

export { chatProcess };

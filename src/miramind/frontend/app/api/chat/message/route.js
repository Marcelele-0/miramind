import { spawn } from "child_process";
import { NextResponse } from "next/server";
import path from "path";

export async function POST(req) {
  try {
    const { userInput, chatHistory } = await req.json();

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

    // Prepare JSON input for Python
    const inputData = JSON.stringify({
      text: userInput,
      chat_history: chatHistory || [],
    });

    // Spawn Python process for this message
    const py = spawn(
      "python",
      [pythonFilePath, inputData],
      {
        cwd: process.cwd(),
        stdio: ["ignore", "pipe", "pipe"],
      }
    );

    let stdout = "";
    let stderr = "";

    py.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    py.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    // Wait for process to finish
    const exitCode = await new Promise((resolve) => {
      py.on("close", resolve);
    });

    if (exitCode !== 0) {
      console.error("Python error:", stderr);
      return NextResponse.json(
        { error: "Python process failed", details: stderr },
        { status: 500 }
      );
    }

    // Parse Python output (should be JSON)
    let result;
    try {
      // Find last JSON object in stdout (in case of extra prints)
      const matches = stdout.match(/{[\s\S]*}/g);
      result = matches
        ? JSON.parse(matches[matches.length - 1])
        : {};
    } catch (e) {
      return NextResponse.json(
        {
          error: "Failed to parse Python output",
          raw: stdout,
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      response_text: result.response_text,
      audio_file_path: result.audio_file_path
        ? "output.wav"
        : null,
    });
  } catch (error) {
    console.error("Failed to send message:", error);
    return NextResponse.json(
      { error: "Failed to send message" },
      { status: 500 }
    );
  }
}

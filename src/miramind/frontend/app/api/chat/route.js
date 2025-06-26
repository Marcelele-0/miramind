import { spawn } from "child_process";
import { NextResponse } from "next/server";

export async function POST(req) {
  try {
    const { userInput, chatHistory } = await req.json();

    return new Promise((resolve, reject) => {
      const pythonProcess = spawn("python", [
        "src/miramind/llm/langgraph/run_chat.py",
        JSON.stringify({
          text: userInput,
          chat_history: chatHistory || [],
        }),
      ]);

      let result = "";
      let error = "";

      pythonProcess.stdout.on("data", (data) => {
        result += data.toString();
      });

      pythonProcess.stderr.on("data", (data) => {
        error += data.toString();
      });

      pythonProcess.on("close", (code) => {
        if (code !== 0) {
          console.error(
            `Python script exited with code ${code}`,
            error
          );
          resolve(
            NextResponse.json(
              {
                error: "Python script failed",
                detail: error,
              },
              { status: 500 }
            )
          );
        } else {
          try {
            const parsed = JSON.parse(result);
            resolve(NextResponse.json(parsed));
          } catch (e) {
            console.error(
              "Failed to parse JSON from Python",
              e,
              result
            );
            resolve(
              NextResponse.json(
                { error: "Invalid response from Python" },
                { status: 500 }
              )
            );
          }
        }
      });
    });
  } catch (err) {
    console.error("API route error", err);
    return NextResponse.json(
      { error: "Server error" },
      { status: 500 }
    );
  }
}

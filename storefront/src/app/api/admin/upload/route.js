import { execFile } from "child_process";
import path from "path";
import { promisify } from "util";

const execAsync = promisify(execFile);
const cwd = path.resolve(process.cwd(), '../goal2_sourcing_engine');

export async function POST() {
  try {
    console.log("[API ADMIN UPLOAD POST] Executing storefront_uploader.py...");
    const args = ["storefront_uploader.py"];
    const { stdout, stderr } = await execAsync("python", args, { cwd });

    if (stderr && !stdout) {
      console.error("[API ADMIN UPLOAD POST] Stderr output:", stderr);
    }

    console.log("[API ADMIN UPLOAD POST] Execution complete.");
    return Response.json({ success: true, output: stdout });
  } catch (error) {
    console.error("[API ADMIN UPLOAD POST] Error:", error);
    return Response.json({ success: false, error: 'An internal error occurred.' }, { status: 500 });
  }
}

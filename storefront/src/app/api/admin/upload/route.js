import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);
const cwd = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine";

export async function POST() {
  try {
    const args = ["storefront_uploader.py"];
    // 🛡️ Sentinel: Fixed Command Injection vulnerability by using execFile instead of exec.
    console.log("[API ADMIN UPLOAD POST] Executing storefront_uploader.py...");
    const { stdout, stderr } = await execFileAsync("python", args, { cwd });

    if (stderr && !stdout) {
      console.error("[API ADMIN UPLOAD POST] Stderr output:", stderr);
    }

    console.log("[API ADMIN UPLOAD POST] Execution complete.");
    return Response.json({ success: true, output: stdout });
  } catch (error) {
    console.error("[API ADMIN UPLOAD POST] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

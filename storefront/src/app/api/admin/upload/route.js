import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);
const cwd = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine";

export async function POST(request) {
  try {
    const adminSecret = process.env.ADMIN_SECRET;
    if (!adminSecret) {
      console.error("[API ADMIN UPLOAD POST] Server misconfiguration: ADMIN_SECRET not set.");
      return Response.json({ success: false, error: "Server misconfiguration" }, { status: 500 });
    }

    const authHeader = request.headers.get("authorization");
    if (!authHeader || authHeader !== `Bearer ${adminSecret}`) {
      console.warn("[API ADMIN UPLOAD POST] Unauthorized attempt.");
      return Response.json({ success: false, error: "Unauthorized" }, { status: 401 });
    }

    console.log("[API ADMIN UPLOAD POST] Executing storefront_uploader.py...");
    const { stdout, stderr } = await execFileAsync("python", ["storefront_uploader.py"], { cwd });

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

import { execFile } from "child_process";
import fs from "fs";
import path from "path";
import os from "os";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

export async function POST(request) {
  try {
    const body = await request.json();
    
    // Create temporary file path
    const tempFile = path.join(os.tmpdir(), `temp_checkout_${Date.now()}.json`);
    fs.writeFileSync(tempFile, JSON.stringify(body, null, 2), "utf-8");
    
    // Execute python script
    const cwd = path.resolve(process.cwd(), "..", "goal2_sourcing_engine");
    const pythonCmd = process.platform === "win32" ? "python" : "python3";
    const args = ["order_fulfillment.py", "--checkout-file", tempFile];
    
    console.log(`[API CHECKOUT] Executing: ${pythonCmd} ${args.join(" ")} in ${cwd}`);
    const { stdout, stderr } = await execFileAsync(pythonCmd, args, { cwd });
    
    // Clean up temporary file
    try {
      fs.unlinkSync(tempFile);
    } catch (err) {
      console.error("[API CHECKOUT] Temp file cleanup error:", err);
    }
    
    if (stderr && !stdout) {
      console.error("[API CHECKOUT] Python stderr:", stderr);
      return Response.json({ success: false, error: stderr }, { status: 500 });
    }
    
    // Find SUCCESS_ORDER_ID in stdout
    const match = stdout.match(/SUCCESS_ORDER_ID:(\S+)/);
    if (match) {
      const orderId = match[1].trim();
      console.log(`[API CHECKOUT] Succeeded. Order ID: ${orderId}`);
      return Response.json({ success: true, orderId });
    } else {
      console.error("[API CHECKOUT] Python execution did not output order ID. stdout:", stdout);
      const errMatch = stdout.match(/ERROR:(.+)/);
      const errMsg = errMatch ? errMatch[1].trim() : "Unknown error in fulfillment engine";
      return Response.json({ success: false, error: errMsg }, { status: 500 });
    }
  } catch (error) {
    console.error("[API CHECKOUT] Route handler error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

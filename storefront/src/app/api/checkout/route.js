import { execFile } from "child_process";
import fs from "fs";
import path from "path";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

export async function POST(request) {
  try {
    const body = await request.json();
    
    // Ensure data directory exists
    const ordersDir = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\data\\orders";
    if (!fs.existsSync(ordersDir)) {
      fs.mkdirSync(ordersDir, { recursive: true });
    }
    
    // Create temporary file path
    const tempFile = path.join(ordersDir, `temp_checkout_${Date.now()}.json`);
    fs.writeFileSync(tempFile, JSON.stringify(body, null, 2), "utf-8");
    
    // Execute python script
    const cwd = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine";
    const args = ["order_fulfillment.py", "--checkout-file", tempFile];
    
    console.log(`[API CHECKOUT] Executing: python ${args.join(" ")}`);
    const { stdout, stderr } = await execFileAsync("python", args, { cwd });
    
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

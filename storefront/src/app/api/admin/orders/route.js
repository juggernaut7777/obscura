import { execFile } from "child_process";
import fs from "fs";
import path from "path";
import { promisify } from "util";

const execFileAsync = promisify(execFile);
const activeOrdersPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\data\\orders\\active_orders.json";
const cwd = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine";

export async function GET() {
  try {
    if (!fs.existsSync(activeOrdersPath)) {
      return Response.json([]);
    }
    const data = fs.readFileSync(activeOrdersPath, "utf-8");
    const orders = JSON.parse(data);
    // Return sorted newest first
    orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    return Response.json(orders);
  } catch (error) {
    console.error("[API ADMIN ORDERS GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const { orderId, action, tracking, pipeline } = await request.json();
    if (!orderId || !action) {
      return Response.json({ success: false, error: "Missing orderId or action" }, { status: 400 });
    }

    let args = ["order_fulfillment.py"];
    if (action === "mark-paid") {
      args.push("--mark-paid", orderId);
    } else if (action === "mark-combining") {
      args.push("--mark-combining", orderId);
    } else if (action === "mark-shipped") {
      if (!tracking || !pipeline) {
        return Response.json({ success: false, error: "Missing tracking or pipeline info for shipping" }, { status: 400 });
      }
      args.push("--mark-shipped", orderId, tracking, pipeline);
    } else {
      return Response.json({ success: false, error: "Invalid action" }, { status: 400 });
    }

    console.log(`[API ADMIN ORDERS POST] Executing: python ${args.join(" ")}`);
    const { stdout, stderr } = await execFileAsync("python", args, { cwd });

    if (stderr && !stdout) {
      console.error("[API ADMIN ORDERS POST] Stderr output:", stderr);
    }

    console.log(`[API ADMIN ORDERS POST] Execution complete. Output: ${stdout}`);
    return Response.json({ success: true, output: stdout });
  } catch (error) {
    console.error("[API ADMIN ORDERS POST] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

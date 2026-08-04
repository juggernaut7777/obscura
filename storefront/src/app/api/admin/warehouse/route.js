import fs from "fs";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET(request) {
  try {
    const adminSecret = process.env.ADMIN_SECRET;
    if (!adminSecret) {
      console.error("[API ADMIN WAREHOUSE GET] Server misconfiguration: ADMIN_SECRET not set.");
      return Response.json({ success: false, error: "Server misconfiguration" }, { status: 500 });
    }

    const authHeader = request.headers.get("authorization");
    if (!authHeader || authHeader !== `Bearer ${adminSecret}`) {
      console.warn("[API ADMIN WAREHOUSE GET] Unauthorized attempt.");
      return Response.json({ success: false, error: "Unauthorized" }, { status: 401 });
    }

    if (!fs.existsSync(manualCurationPath)) {
      return Response.json([]);
    }

    const items = [];
    const children = fs.readdirSync(manualCurationPath);

    for (const child of children) {
      const folderPath = path.join(manualCurationPath, child);
      const stat = fs.statSync(folderPath);

      if (stat.isDirectory() && child !== "_rejected") {
        let metadata = { product_name: child };
        const metadataPath = path.join(folderPath, "metadata.json");

        if (fs.existsSync(metadataPath)) {
          try {
            metadata = JSON.parse(fs.readFileSync(metadataPath, "utf-8"));
          } catch (e) {
            console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child}:`, e);
          }
        }

        // Extract thumbnail base64 image
        let thumbnail = null;
        try {
          const files = fs.readdirSync(folderPath);
          const imgFile = files.find(f => f.startsWith("angle_") && /\.(png|jpg|jpeg|webp)$/i.test(f)) ||
                          files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f));
          if (imgFile) {
            const imgData = fs.readFileSync(path.join(folderPath, imgFile));
            const base64 = imgData.toString("base64");
            let ext = path.extname(imgFile).substring(1).toLowerCase();
            if (ext === "jpg") ext = "jpeg";
            thumbnail = `data:image/${ext};base64,${base64}`;
          }
        } catch (e) {
          console.error(`[API WAREHOUSE] Image thumbnail load failed in ${child}:`, e);
        }

        items.push({
          folderName: child,
          metadata,
          thumbnail,
          mtime: stat.mtime
        });
      }
    }

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

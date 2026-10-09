import { promises as fsPromises } from "fs";
import fsSync from "fs";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    // ⚡ Performance optimization
    // Why: Synchronous filesystem operations (fs.readdirSync, fs.readFileSync) in a loop block the Node.js event loop, preventing the server from handling other concurrent requests.
    // What: Replaced sync methods with async fs.promises and used Promise.all to process all folder reads and image conversions concurrently rather than sequentially.
    if (!fsSync.existsSync(manualCurationPath)) {
      return Response.json([]);
    }

    const children = await fsPromises.readdir(manualCurationPath);

    const items = (await Promise.all(
      children.map(async (child) => {
        if (child === "_rejected") return null;

        const folderPath = path.join(manualCurationPath, child);
        const stat = await fsPromises.stat(folderPath);

        if (!stat.isDirectory()) return null;

        let metadata = { product_name: child };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          const metaStat = await fsPromises.stat(metadataPath).catch(() => null);
          if (metaStat) {
            const metaContent = await fsPromises.readFile(metadataPath, "utf-8");
            metadata = JSON.parse(metaContent);
          }
        } catch (e) {
          console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child}:`, e);
        }

        // Extract thumbnail base64 image
        let thumbnail = null;
        try {
          const files = await fsPromises.readdir(folderPath);
          const imgFile = files.find(f => f.startsWith("angle_") && /\.(png|jpg|jpeg|webp)$/i.test(f)) ||
                          files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f));
          if (imgFile) {
            const imgData = await fsPromises.readFile(path.join(folderPath, imgFile));
            const base64 = imgData.toString("base64");
            let ext = path.extname(imgFile).substring(1).toLowerCase();
            if (ext === "jpg") ext = "jpeg";
            thumbnail = `data:image/${ext};base64,${base64}`;
          }
        } catch (e) {
          console.error(`[API WAREHOUSE] Image thumbnail load failed in ${child}:`, e);
        }

        return {
          folderName: child,
          metadata,
          thumbnail,
          mtime: stat.mtime
        };
      })
    )).filter(Boolean);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

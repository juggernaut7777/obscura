import fs from "fs";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    // ⚡ Performance optimization
    // Why: Synchronous fs calls block the single-threaded Node event loop, degrading concurrent performance.
    // What: Replace fs.*Sync methods with asynchronous fs.promises equivalents and process items concurrently using Promise.all.
    try {
      await fs.promises.access(manualCurationPath);
    } catch {
      return Response.json([]);
    }

    const children = await fs.promises.readdir(manualCurationPath);

    const itemsPromises = children.map(async (child) => {
      const folderPath = path.join(manualCurationPath, child);
      const stat = await fs.promises.stat(folderPath);

      if (stat.isDirectory() && child !== "_rejected") {
        let metadata = { product_name: child };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          await fs.promises.access(metadataPath);
          const metadataStr = await fs.promises.readFile(metadataPath, "utf-8");
          metadata = JSON.parse(metadataStr);
        } catch (e) {
          // File doesn't exist or parse failed, stick to default
          if (e.code !== 'ENOENT') {
            console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child}:`, e);
          }
        }

        // Extract thumbnail base64 image
        let thumbnail = null;
        try {
          const files = await fs.promises.readdir(folderPath);
          const imgFile = files.find(f => f.startsWith("angle_") && /\.(png|jpg|jpeg|webp)$/i.test(f)) ||
                          files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f));
          if (imgFile) {
            const imgData = await fs.promises.readFile(path.join(folderPath, imgFile));
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
      }
      return null;
    });

    let items = await Promise.all(itemsPromises);
    items = items.filter(item => item !== null);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

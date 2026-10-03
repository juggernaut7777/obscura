import fs from "fs/promises";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    // ⚡ Performance optimization
    // Why: Synchronous fs.*Sync methods block the single-threaded event loop, preventing the API from serving other concurrent requests while reading directories.
    // What: Refactored route to use fs.promises methods and Promise.all to fetch metadata and images concurrently.
    try {
      await fs.access(manualCurationPath);
    } catch {
      return Response.json([]);
    }

    const children = await fs.readdir(manualCurationPath);

    const itemPromises = children.map(async (child) => {
      const folderPath = path.join(manualCurationPath, child);
      const stat = await fs.stat(folderPath);

      if (stat.isDirectory() && child !== "_rejected") {
        let metadata = { product_name: child };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          await fs.access(metadataPath);
          const data = await fs.readFile(metadataPath, "utf-8");
          metadata = JSON.parse(data);
        } catch (e) {
          if (e.code !== 'ENOENT') {
             console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child}:`, e);
          }
        }

        // Extract thumbnail base64 image
        let thumbnail = null;
        try {
          const files = await fs.readdir(folderPath);
          const imgFile = files.find(f => f.startsWith("angle_") && /\.(png|jpg|jpeg|webp)$/i.test(f)) ||
                          files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f));
          if (imgFile) {
            const imgData = await fs.readFile(path.join(folderPath, imgFile));
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

    let items = await Promise.all(itemPromises);
    items = items.filter(Boolean);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

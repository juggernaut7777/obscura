import fs from "fs";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    if (!fs.existsSync(manualCurationPath)) {
      return Response.json([]);
    }

    // ⚡ Performance optimization
    // Why: Synchronous filesystem operations inside API routes block the Node.js event loop, freezing the application.
    // What: Replaced fs.readdirSync, fs.statSync, and fs.readFileSync with their async fs.promises equivalents and used Promise.all to load warehouse items concurrently, reducing latency in high-volume folders.

    const children = await fs.promises.readdir(manualCurationPath, { withFileTypes: true });

    const tasks = children.map(async (child) => {
      if (child.isDirectory() && child.name !== "_rejected") {
        const folderPath = path.join(manualCurationPath, child.name);

        // We run stat to fetch mtime for sorting, and readdir concurrently
        const [stat, files] = await Promise.all([
          fs.promises.stat(folderPath),
          fs.promises.readdir(folderPath)
        ]);

        let metadata = { product_name: child.name };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          const metadataRaw = await fs.promises.readFile(metadataPath, "utf-8");
          metadata = JSON.parse(metadataRaw);
        } catch (e) {
          if (e.code !== 'ENOENT') {
            console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child.name}:`, e);
          }
        }

        // Extract thumbnail base64 image
        let thumbnail = null;
        try {
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
          console.error(`[API WAREHOUSE] Image thumbnail load failed in ${child.name}:`, e);
        }

        return {
          folderName: child.name,
          metadata,
          thumbnail,
          mtime: stat.mtime
        };
      }
      return null;
    });

    const results = (await Promise.all(tasks)).filter(Boolean);

    // Sort newest staged items first
    results.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(results);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

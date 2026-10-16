import fs from "fs";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    try {
      await fs.promises.access(manualCurationPath);
    } catch {
      return Response.json([]);
    }

    // ⚡ Performance optimization
    // Why: Synchronous file operations block the Node.js event loop, freezing concurrent API requests. Sequential iterations and redundant stat calls scale poorly.
    // What: Replaced blocking fs.*Sync methods with fs.promises.*, used withFileTypes in readdir to prevent N+1 stat calls for directory checks, and parallelized item processing with Promise.all.
    const dirents = await fs.promises.readdir(manualCurationPath, { withFileTypes: true });

    const itemPromises = dirents
      .filter(dirent => dirent.isDirectory() && dirent.name !== "_rejected")
      .map(async (dirent) => {
        const child = dirent.name;
        const folderPath = path.join(manualCurationPath, child);
        const stat = await fs.promises.stat(folderPath);

        let metadata = { product_name: child };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          await fs.promises.access(metadataPath);
          const metadataStr = await fs.promises.readFile(metadataPath, "utf-8");
          metadata = JSON.parse(metadataStr);
        } catch (e) {
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
      });

    const items = await Promise.all(itemPromises);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

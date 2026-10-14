import fs from "fs/promises";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    // ⚡ Performance optimization
    // Why: Synchronous filesystem operations block the Node.js event loop, preventing concurrent request handling. Additionally, calling stat on every child to check if it's a directory causes an N+1 penalty.
    // What: Replaced all fs.*Sync calls with async fs.promises equivalents. Used fs.promises.readdir with { withFileTypes: true } to get Dirent objects directly, skipping the stat check just to identify directories. Item processing is parallelized via Promise.all.
    let children;
    try {
      children = await fs.readdir(manualCurationPath, { withFileTypes: true });
    } catch (err) {
      if (err.code === "ENOENT") {
        return Response.json([]);
      }
      throw err;
    }

    const items = [];
    const processPromises = [];

    for (const childDirent of children) {
      if (childDirent.isDirectory() && childDirent.name !== "_rejected") {
        const child = childDirent.name;
        const folderPath = path.join(manualCurationPath, child);

        processPromises.push((async () => {
          const stat = await fs.stat(folderPath);
          let metadata = { product_name: child };
          const metadataPath = path.join(folderPath, "metadata.json");

          try {
            const metaStr = await fs.readFile(metadataPath, "utf-8");
            metadata = JSON.parse(metaStr);
          } catch (e) {
            if (e.code !== "ENOENT") {
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
        })());
      }
    }

    const resolvedItems = await Promise.all(processPromises);
    items.push(...resolvedItems);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

import fs from "fs";
import { promises as fsp } from "fs";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    try {
      await fsp.access(manualCurationPath);
    } catch {
      return Response.json([]);
    }

    // ⚡ Performance optimization
    // Why: Synchronous file operations block the Node event loop and iterdir without withFileTypes requires N+1 stat calls.
    // What: Replaced fs.readdirSync/statSync with fsp.readdir({withFileTypes: true}) and used Promise.all to load thumbnails asynchronously.
    const children = await fsp.readdir(manualCurationPath, { withFileTypes: true });

    const items = (await Promise.all(children.map(async (dirent) => {
      const child = dirent.name;
      if (!dirent.isDirectory() || child === "_rejected") return null;

      const folderPath = path.join(manualCurationPath, child);
      let stat;
      try {
        stat = await fsp.stat(folderPath);
      } catch (e) {
        return null;
      }

      let metadata = { product_name: child };
      const metadataPath = path.join(folderPath, "metadata.json");

      try {
        await fsp.access(metadataPath);
        try {
          metadata = JSON.parse(await fsp.readFile(metadataPath, "utf-8"));
        } catch (e) {
          console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child}:`, e);
        }
      } catch (e) {
        // metadata.json does not exist
      }

      // Extract thumbnail base64 image
      let thumbnail = null;
      try {
        const files = await fsp.readdir(folderPath);
        const imgFile = files.find(f => f.startsWith("angle_") && /\.(png|jpg|jpeg|webp)$/i.test(f)) ||
                        files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f));
        if (imgFile) {
          const imgData = await fsp.readFile(path.join(folderPath, imgFile));
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
    }))).filter(Boolean);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

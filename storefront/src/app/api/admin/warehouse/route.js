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

    const items = [];
    // ⚡ Performance optimization
    // Why: Synchronous fs operations block the Node.js single-threaded event loop, freezing concurrent requests. Additionally, calling statSync on every child is an N+1 performance penalty.
    // What: Replaced fs.*Sync methods with asynchronous fs.promises and used { withFileTypes: true } to avoid N+1 stat calls.
    const children = await fs.promises.readdir(manualCurationPath, { withFileTypes: true });

    await Promise.all(children.map(async (dirent) => {
      if (dirent.isDirectory() && dirent.name !== "_rejected") {
        const child = dirent.name;
        const folderPath = path.join(manualCurationPath, child);

        let metadata = { product_name: child };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          await fs.promises.access(metadataPath);
          try {
            metadata = JSON.parse(await fs.promises.readFile(metadataPath, "utf-8"));
          } catch (e) {
            console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child}:`, e);
          }
        } catch {
          // File does not exist, ignore
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

        const stat = await fs.promises.stat(folderPath);
        items.push({
          folderName: child,
          metadata,
          thumbnail,
          mtime: stat.mtime
        });
      }
    }));

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

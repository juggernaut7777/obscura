import fsPromises from "fs/promises";
import path from "path";

const manualCurationPath = "c:\\Users\\USER\\ai ugc and sales\\goal2_sourcing_engine\\MANUAL_CURATION";

export async function GET() {
  try {
    // ⚡ Performance optimization
    // Why: fs.existsSync and other Sync methods block the Node.js event loop
    // What: Refactored to use fsPromises.access, readdir (withFileTypes), and Promise.all to map over directories concurrently
    try {
      await fsPromises.access(manualCurationPath);
    } catch {
      return Response.json([]);
    }

    const children = await fsPromises.readdir(manualCurationPath, { withFileTypes: true });

    const itemPromises = children.map(async (child) => {
      if (child.isDirectory() && child.name !== "_rejected") {
        const folderPath = path.join(manualCurationPath, child.name);

        let metadata = { product_name: child.name };
        const metadataPath = path.join(folderPath, "metadata.json");

        try {
          const metaData = await fsPromises.readFile(metadataPath, "utf-8");
          metadata = JSON.parse(metaData);
        } catch (e) {
          if (e.code !== 'ENOENT') {
            console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${child.name}:`, e);
          }
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
          console.error(`[API WAREHOUSE] Image thumbnail load failed in ${child.name}:`, e);
        }

        const stat = await fsPromises.stat(folderPath);
        return {
          folderName: child.name,
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

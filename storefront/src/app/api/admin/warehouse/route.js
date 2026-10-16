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
    // Why: Synchronous fs operations like fs.readdirSync block Node.js's single-threaded event loop. Calling fs.statSync on every file adds an N+1 performance penalty.
    // What: Replaced blocking fs.*Sync methods with fs.promises, parallelized file reads using Promise.all, and used withFileTypes: true to avoid N+1 stat calls.
    const children = await fs.promises.readdir(manualCurationPath, { withFileTypes: true });

    const promises = children.map(async (dirent) => {
      if (dirent.isDirectory() && dirent.name !== "_rejected") {
        const folderPath = path.join(manualCurationPath, dirent.name);

        const statPromise = fs.promises.stat(folderPath);

        const metadataPath = path.join(folderPath, "metadata.json");
        const metadataPromise = fs.promises.readFile(metadataPath, "utf-8")
          .then(data => JSON.parse(data))
          .catch(e => {
            if (e.code !== 'ENOENT') console.error(`[API WAREHOUSE] Failed to parse metadata.json in ${dirent.name}:`, e);
            return { product_name: dirent.name };
          });

        const thumbnailPromise = fs.promises.readdir(folderPath)
          .then(async (files) => {
            const imgFile = files.find(f => f.startsWith("angle_") && /\.(png|jpg|jpeg|webp)$/i.test(f)) ||
                            files.find(f => /\.(png|jpg|jpeg|webp)$/i.test(f));
            if (imgFile) {
              const imgData = await fs.promises.readFile(path.join(folderPath, imgFile));
              const base64 = imgData.toString("base64");
              let ext = path.extname(imgFile).substring(1).toLowerCase();
              if (ext === "jpg") ext = "jpeg";
              return `data:image/${ext};base64,${base64}`;
            }
            return null;
          })
          .catch(e => {
            if (e.code !== 'ENOENT') console.error(`[API WAREHOUSE] Image thumbnail load failed in ${dirent.name}:`, e);
            return null;
          });

        const [stat, metadata, thumbnail] = await Promise.all([statPromise, metadataPromise, thumbnailPromise]);

        return {
          folderName: dirent.name,
          metadata,
          thumbnail,
          mtime: stat.mtime
        };
      }
      return null;
    });

    const items = (await Promise.all(promises)).filter(item => item !== null);

    // Sort newest staged items first
    items.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));

    return Response.json(items);
  } catch (error) {
    console.error("[API WAREHOUSE GET] Error:", error);
    return Response.json({ success: false, error: error.message }, { status: 500 });
  }
}

from fastapi.responses import FileResponse
import os

# ... (previous code) ...

# Explicitly handle root
@app.get("/")
async def serve_root():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"error": "Frontend not built"}

# Mount assets
if os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

# Catch-all for SPA (serve index.html for any other route not matched by API)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Avoid masking API routes if they were somehow missed (though order matters)
    if full_path.startswith("api/"):
        return {"error": "API endpoint not found", "path": full_path}
    
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"error": "Frontend not built"}

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from core.settings import settings as core_settings

logger = logging.getLogger("horus.api")


class ImmutableStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code in {200, 304}:
            response.headers.setdefault(
                "Cache-Control",
                "public, max-age=31536000, immutable",
            )
        return response


def mount_frontend_static(app: FastAPI) -> None:
    frontend_path = core_settings.get_resource_path(os.path.join("frontend", "out"))
    if not os.path.exists(frontend_path):
        return

    app.mount(
        "/_next",
        ImmutableStaticFiles(directory=os.path.join(frontend_path, "_next")),
        name="next-static",
    )

    @app.get("/{rest_of_path:path}")
    @app.head("/{rest_of_path:path}")
    async def serve_frontend(rest_of_path: str):
        normalized_path = rest_of_path.strip("/")
        if normalized_path == "api" or normalized_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        if normalized_path == "ws":
            raise HTTPException(status_code=404, detail="WebSocket route requires a WebSocket upgrade")

        file_path = os.path.join(frontend_path, rest_of_path)

        if not os.path.isfile(file_path) and "__next." in rest_of_path:
            rewritten = rest_of_path.replace(".__PAGE__.txt", "/__PAGE__.txt")
            if rewritten != rest_of_path:
                check_path = os.path.join(frontend_path, rewritten)
                if os.path.isfile(check_path):
                    file_path = check_path

            if not os.path.isfile(file_path) and (rest_of_path.endswith(".txt") or "_head" in rest_of_path):
                return JSONResponse(status_code=200, content={})

        if os.path.isfile(file_path):
            if rest_of_path.endswith(".txt"):
                headers = {
                    "Vary": "RSC, Next-Router-State-Tree, Next-Router-Prefetch",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "X-Nextjs-Cache": "MISS",
                }
                return FileResponse(file_path, media_type="text/x-component", headers=headers)
            return FileResponse(file_path)

        html_path = file_path + ".html"
        if os.path.isfile(html_path):
            return FileResponse(html_path)

        folder_index = os.path.join(file_path, "index.html")
        if os.path.isfile(folder_index):
            return FileResponse(folder_index)

        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})

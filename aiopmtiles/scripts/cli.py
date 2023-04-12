"""aoipmtiles app."""

from dataclasses import dataclass, field
from typing import Dict

import click
import jinja2
import uvicorn
from fastapi import FastAPI, Path, Query
from pmtiles.tile import Compression
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.templating import Jinja2Templates

from aiopmtiles import Reader

templates = Jinja2Templates(
    directory="",
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader("aiopmtiles", "templates")]),
)


@dataclass
class viz:
    """PMTiles viewer."""

    filepath: str

    port: int = 8080
    host: str = "127.0.0.1"

    app: FastAPI = field(default_factory=FastAPI)

    def __post_init__(self):
        """Init Viz."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET"],
            allow_headers=["*"],
        )

        @self.app.get("/metadata")
        async def metadata():
            """get Metadata."""
            async with Reader(self.filepath) as src:
                return await src.metadata()

        @self.app.get("/tiles/{z}/{x}/{y}", response_class=Response)
        async def tiles(
            z: int = Path(ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(description="TMS tiles's column"),
            y: int = Path(description="TMS tiles's row"),
        ):
            """get Tile."""
            headers: Dict[str, str] = {}

            async with Reader(self.filepath) as src:
                data = await src.get_tile(z, x, y)
                if src.header["internal_compression"] == Compression.GZIP:
                    headers["Content-Encoding"] = "gzip"

            return Response(data, media_type="application/x-protobuf", headers=headers)

        @self.app.get("/tilejson.json")
        async def tilejson(request: Request):
            """get TileJSON."""
            tiles_endpoint = str(request.url_for("tiles", z="{z}", x="{x}", y="{y}"))

            async with Reader(self.filepath) as src:
                header = src.header
                meta = await src.metadata()

            bounds = [
                c / 10000000
                for c in [
                    header["min_lon_e7"],
                    header["min_lat_e7"],
                    header["max_lon_e7"],
                    header["max_lat_e7"],
                ]
            ]

            minzoom = header["min_zoom"]
            maxzoom = header["max_zoom"]
            tilejson = {
                "tilejson": "3.0.0",
                "name": "pmtiles",
                "version": "1.0.0",
                "scheme": "xyz",
                "tiles": [tiles_endpoint],
                "minzoom": minzoom,
                "maxzoom": maxzoom,
                "bounds": bounds,
                "center": [
                    (bounds[0] + bounds[2]) / 2,
                    (bounds[1] + bounds[3]) / 2,
                    minzoom,
                ],
            }

            if vector_layers := meta.get("vector_layers"):
                tilejson["vector_layers"] = vector_layers

            return tilejson

        @self.app.get("/", response_class=HTMLResponse)
        @self.app.get("/index.html", response_class=HTMLResponse)
        def viewer(request: Request):
            """Handle /index.html."""
            return templates.TemplateResponse(
                name="index.html",
                context={
                    "request": request,
                    "tilejson_endpoint": str(request.url_for("tilejson")),
                },
                media_type="text/html",
            )

    def start(self):
        """Start tile server."""
        uvicorn.run(app=self.app, host=self.host, port=self.port, log_level="info")

    @property
    def template_url(self) -> str:
        """Get simple app template url."""
        return f"http://{self.host}:{self.port}/index.html"


# The CLI command group.
@click.group(help="Command line interface for the aiopmtiles Python package.")
def cli():
    """Execute the main aiopmtiles command."""


@cli.command()
@click.argument("src_path", type=str, nargs=1, required=True)
@click.option("--port", type=int, default=8080, help="Webserver port (default: 8080)")
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Webserver host url (default: 127.0.0.1)",
)
def serve(src_path, port, host):
    """Viz cli."""
    application = viz(src_path, port=port, host=host)

    click.launch(application.template_url)

    application.start()

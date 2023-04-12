Create a simple FastAPI application to serve tiles from PMTiles

```python
from typing import Dict

from fastapi import FastAPI, Path, Query
from pmtiles.tile import Compression
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aiopmtiles import Reader


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/metadata")
async def metadata(url: str = Query(..., description="PMTiles archive URL.")):
    """get Metadata."""
    async with Reader(url) as src:
        return await src.metadata()

@spp.get("/tiles/{z}/{x}/{y}", response_class=Response)
async def tiles(
    z: int = Path(ge=0, le=30, description="TMS tiles's zoom level"),
    x: int = Path(description="TMS tiles's column"),
    y: int = Path(description="TMS tiles's row"),
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get Tile."""
    headers: Dict[str, str] = {}

    async with Reader(url) as src:
        data = await src.get_tile(z, x, y)
        if src.header["internal_compression"] == Compression.GZIP:
            headers["Content-Encoding"] = "gzip"

    return Response(data, media_type="application/x-protobuf", headers=headers)

@app.get("/tilejson.json")
async def tilejson(
    request: Request,
    url: str = Query(..., description="PMTiles archive URL."),
):
    """get TileJSON."""
    async with Reader(url) as src:
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
        "tiles": [
            str(request.url_for("tiles", z="{z}", x="{x}", y="{y}")) + f"?url={url}"
        ],
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
```

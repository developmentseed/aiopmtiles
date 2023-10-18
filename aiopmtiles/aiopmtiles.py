"""Async version of protomaps/PMTiles."""

import gzip
import json
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol, Tuple

from aiocache import Cache, cached
from pmtiles.tile import (
    Compression,
    TileType,
    deserialize_directory,
    deserialize_header,
    find_tile,
    zxy_to_tileid,
)

from aiopmtiles.io import FileSystem


class _GetBytes(Protocol):
    async def __call__(self, offset: int, length: int) -> bytes:
        ...


@dataclass
class Reader:
    """PMTiles Reader."""

    filepath: str
    options: Optional[Dict] = field(default_factory=dict)

    fs: FileSystem = field(init=False)

    _header: Dict = field(init=False)
    _header_offset: int = field(default=0, init=False)
    _header_length: int = field(default=127, init=False)

    _ctx: AsyncExitStack = field(default_factory=AsyncExitStack)

    async def __aenter__(self):
        """Support using with Context Managers."""
        self.fs = await self._ctx.enter_async_context(
            FileSystem.create_from_filepath(self.filepath, **self.options)
        )

        header_values = await self._get(self._header_offset, self._header_length)
        spec_version = header_values[7]
        assert spec_version == 3, "Only Version 3 of PMTiles specification is supported"

        self._header = deserialize_header(header_values)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Support using with Context Managers."""
        await self._ctx.__aexit__(exc_type, exc_value, traceback)

    @cached(
        cache=Cache.MEMORY,
        key_builder=lambda f, self, offset, length: f"{self.filepath}-{offset}-{length}",
    )
    async def _get(self, offset: int, length: int) -> bytes:
        """Get Bytes."""
        return await self.fs.get(offset, length)

    async def metadata(self) -> Dict:
        """Return PMTiles Metadata."""
        metadata = await self._get(
            self._header["metadata_offset"],
            self._header["metadata_length"] - 1,
        )
        if self._header["internal_compression"] == Compression.GZIP:
            metadata = gzip.decompress(metadata)

        return json.loads(metadata)

    async def get_tile(self, z, x, y) -> Optional[bytes]:
        """Get Tile Data."""
        tile_id = zxy_to_tileid(z, x, y)

        dir_offset = self._header["root_offset"]
        dir_length = self._header["root_length"]
        for _ in range(0, 4):  # max depth
            directory_values = await self._get(dir_offset, dir_length - 1)
            directory = deserialize_directory(directory_values)

            if result := find_tile(directory, tile_id):
                if result.run_length == 0:
                    dir_offset = self._header["leaf_directory_offset"] + result.offset
                    dir_length = result.length

                else:
                    data = await self._get(
                        self._header["tile_data_offset"] + result.offset,
                        result.length - 1,
                    )
                    return data

        return None

    @property
    def minzoom(self) -> int:
        """Return minzoom."""
        return self._header["min_zoom"]

    @property
    def maxzoom(self) -> int:
        """Return maxzoom."""
        return self._header["max_zoom"]

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Return Archive Bounds."""
        return (
            self._header["min_lon_e7"] / 10000000,
            self._header["min_lat_e7"] / 10000000,
            self._header["max_lon_e7"] / 10000000,
            self._header["max_lat_e7"] / 10000000,
        )

    @property
    def center(self) -> Tuple[float, float, int]:
        """Return Archive center."""
        return (
            self._header["center_lon_e7"] / 10000000,
            self._header["center_lat_e7"] / 10000000,
            self._header["center_zoom"],
        )

    @property
    def is_vector(self) -> bool:
        """Return tile type."""
        return self._header["tile_type"] == TileType.MVT

    @property
    def tile_compression(self) -> Compression:
        """Return tile compression type."""
        return self._header["tile_compression"]

    @property
    def tile_type(self) -> TileType:
        """Return tile type."""
        return self._header["tile_type"]

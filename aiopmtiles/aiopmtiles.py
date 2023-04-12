"""Async version of protomaps/PMTiles."""

import gzip
import json
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol

from aiocache import Cache, cached
from pmtiles.tile import (
    Compression,
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

    fs: FileSystem = field(init=False)

    _header: Dict = field(init=False)
    _header_offset: int = field(default=0, init=False)
    _header_length: int = field(default=127, init=False)

    _ctx: AsyncExitStack = field(default_factory=AsyncExitStack)

    async def __aenter__(self):
        """Support using with Context Managers."""
        self.fs = await self._ctx.enter_async_context(
            FileSystem.create_from_filepath(self.filepath)
        )

        header_values = await self._get(self._header_offset, self._header_length)
        spec_version = header_values[7]
        assert spec_version == 3, "Only Version 3 of PMTiles specification is supported"

        self.header = deserialize_header(header_values)

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
            self.header["metadata_offset"],
            self.header["metadata_length"] - 1,
        )
        if self.header["internal_compression"] == Compression.GZIP:
            metadata = gzip.decompress(metadata)

        return json.loads(metadata)

    async def get_tile(self, z, x, y) -> Optional[bytes]:
        """Get Tile Data."""
        tile_id = zxy_to_tileid(z, x, y)
        data = None

        dir_offset = self.header["root_offset"]
        dir_length = self.header["root_length"] - 1
        for _depth in range(0, 4):  # max depth
            directory_values = await self._get(dir_offset, dir_length)
            directory = deserialize_directory(directory_values)

            result = find_tile(directory, tile_id)
            if result:
                if result.run_length == 0:
                    dir_offset = self.header["leaf_directory_offset"] + result.offset
                    dir_length = result.length - 1

                else:
                    data = await self._get(
                        self.header["tile_data_offset"] + result.offset,
                        result.length - 1,
                    )

        return data

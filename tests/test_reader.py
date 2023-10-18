"""Test Reader."""

import os

import pytest

from aiopmtiles import Reader
from aiopmtiles.io import LocalFileSystem

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VECTOR_PMTILES = os.path.join(FIXTURES_DIR, "protomaps(vector)ODbL_firenze.pmtiles")
RASTER_PMTILES = os.path.join(FIXTURES_DIR, "usgs-mt-whitney-8-15-webp-512.pmtiles")
V2_PMTILES = os.path.join(FIXTURES_DIR, "stamen_toner(raster)CC-BY+ODbL_z3.pmtiles")


@pytest.mark.asyncio
async def test_reader_vector():
    """Test Reader with Vector PMTiles."""
    async with Reader(VECTOR_PMTILES) as src:
        assert isinstance(src.fs, LocalFileSystem)
        assert src._header
        assert src._header_offset == 0
        assert src._header_length == 127
        assert src.bounds
        assert src.minzoom == 0
        assert src.maxzoom == 14
        assert src.center[2] == 0
        assert src.is_vector
        assert src.tile_compression.name == "GZIP"
        assert not src.fs.file.closed
        assert src.tile_type.name == "MVT"

        metadata = await src.metadata()
        assert "attribution" in metadata
        assert "tilestats" in metadata

    assert src.fs.file.closed


@pytest.mark.asyncio
async def test_reader_raster():
    """Test Reader with raster PMTiles."""
    async with Reader(RASTER_PMTILES) as src:
        assert isinstance(src.fs, LocalFileSystem)
        assert src._header
        assert src.bounds
        assert src.minzoom == 8
        assert src.maxzoom == 15
        assert src.center[2] == 12
        assert not src.is_vector
        assert src.tile_compression.name == "NONE"
        assert not src.fs.file.closed
        assert src.tile_type.name == "WEBP"

        metadata = await src.metadata()
        assert "attribution" in metadata
        assert "type" in metadata

    assert src.fs.file.closed


@pytest.mark.asyncio
async def test_reader_bad_spec():
    """Should raise an error if not spec == 3."""
    with pytest.raises(AssertionError):
        async with Reader(V2_PMTILES) as src:
            pass

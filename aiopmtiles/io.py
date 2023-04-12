"""FileSystems for PMTiles Reader."""

import abc
import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import aioboto3
import aiofiles
import httpx


@dataclass
class FileSystem(abc.ABC):
    """Filesystem base class"""

    filepath: str

    @abc.abstractmethod
    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        ...

    @abc.abstractmethod
    async def __aenter__(self):
        """Async context management"""
        ...

    @abc.abstractmethod
    async def close(self):
        """close FileSystem."""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async context management"""
        await self.close()

    @classmethod
    def create_from_filepath(cls, filepath: str, **kwargs) -> "FileSystem":
        """Instantiate the appropriate filesystem based on filepath scheme"""
        parsed = urlparse(filepath)

        if parsed.scheme in {"http", "https"}:
            return Http(filepath)

        elif parsed.scheme == "s3":
            return S3(filepath)

        elif parsed.scheme == "file":
            return Local(filepath)

        # Invalid Scheme
        elif parsed.scheme:
            raise ValueError(f"'{parsed.scheme}' is not supported")

        # fallback to FileBackend
        else:
            return Local(filepath)


@dataclass
class Local(FileSystem):
    """Local (disk) filesystem"""

    file: Any = field(init=False)

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        await self.file.seek(offset)
        return await self.file.read(length + 1)

    async def __aenter__(self):
        """Async context management"""
        self.file = await aiofiles.open(self.filepath, "rb")
        return self

    async def close(self):
        """Close file."""
        await self.file.close()


@dataclass
class Http(FileSystem):
    """HTTP filesystem"""

    client: httpx.AsyncClient = field(init=False)

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        range_header = {"Range": f"bytes={offset}-{offset + length}"}
        resp = await self.client.get(self.filepath, headers=range_header)
        resp.raise_for_status()
        return resp.content

    async def __aenter__(self):
        """Async context management"""
        self.client = httpx.AsyncClient()
        return self

    async def close(self):
        """Close Connection."""
        await self.client.aclose()


@dataclass
class S3(FileSystem):
    """S3 filesystem"""

    resource: Any = field(init=False)
    obj: Any = field(init=False)

    async def get(self, offset: int, length: int) -> bytes:
        """Perform a range request"""
        kwargs = {}
        if request_payer := os.getenv("AWS_REQUEST_PAYER"):
            kwargs["RequestPayer"] = request_payer

        req = await self.obj.get(Range=f"bytes={offset}-{offset + length}", **kwargs)

        return await req["Body"].read()

    async def __aenter__(self):
        """Async context management"""
        parsed = urlparse(self.filepath)
        self.resource = await aioboto3.resource("s3").__aenter__()
        self.obj = await self.resource.Object(parsed.netloc, parsed.path.strip("/"))
        return self

    async def close(self):
        """Close resource."""
        await self.resource.close()

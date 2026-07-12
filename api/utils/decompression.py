import io
import gzip
from typing import Generator

class DecompressionLimitExceeded(ValueError):
    """Exception raised when the decompressed payload size exceeds the limit."""
    pass

def stream_decompress_gzip(
    compressed_bytes: bytes,
    max_size: int,
    chunk_size: int = 1024 * 1024
) -> Generator[bytes, None, None]:
    """
    Safely decompress gzip bytes chunk by chunk as a stream.
    Raises DecompressionLimitExceeded if the decompressed size crosses max_size.
    Raises ValueError on corrupted or invalid gzip payload formats.
    """
    if not compressed_bytes:
        return

    bio = io.BytesIO(compressed_bytes)
    total_decompressed = 0

    try:
        with gzip.GzipFile(fileobj=bio, mode="rb") as gf:
            while True:
                # Read at most chunk_size bytes at a time
                chunk = gf.read(chunk_size)
                if not chunk:
                    break
                total_decompressed += len(chunk)
                if total_decompressed > max_size:
                    raise DecompressionLimitExceeded(
                        f"Decompressed payload size limit exceeded (max: {max_size} bytes)."
                    )
                yield chunk
    except DecompressionLimitExceeded:
        raise
    except Exception as ex:
        # Map zlib or gzip OS errors to a standard ValueError for bad archives
        raise ValueError(f"Corrupted or invalid gzip archive: {ex}")

def decompress_gzip_safe(
    compressed_bytes: bytes,
    max_size: int,
    chunk_size: int = 1024 * 1024
) -> bytes:
    """
    Decompress gzip bytes fully while checking size bounds chunk-by-chunk.
    Exposes a clean bytes interface for compatibility with string decoders.
    """
    chunks = []
    for chunk in stream_decompress_gzip(compressed_bytes, max_size, chunk_size):
        chunks.append(chunk)
    return b"".join(chunks)

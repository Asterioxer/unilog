import pytest
import gzip
from api.utils.decompression import decompress_gzip_safe

def test_truncated_gzip_archive():
    # Create valid gzip
    valid = gzip.compress(b"Valid log line payload data details")
    # Truncate it midway
    truncated = valid[:-10]
    
    # Decompression should raise ValueError on truncation
    with pytest.raises(ValueError):
        decompress_gzip_safe(truncated, max_size=1000)

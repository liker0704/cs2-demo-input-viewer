"""Cache Validator for CS2 Input Visualizer.

This module provides fast cache validation using partial file hashing to determine
if cached data is up-to-date without reading entire demo files. Used by Phase 6
Auto Mode to efficiently skip re-processing unchanged demo files.

Cache Validation Strategy:
    - Compute hash of first 10MB + file size (not full file MD5)
    - Store hash in cache/{demo_name}.md5
    - Compare stored hash with current hash to validate cache
    - Much faster than full file hashing for large demo files

Hash Format:
    "{file_size_bytes}_{md5_of_first_10mb}"
    Example: "524288000_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

File Structure:
    cache/
    ├── demo_name.json      # Cache data (managed by CacheManager)
    └── demo_name.md5       # Hash for validation (managed by CacheValidator)

Example:
    >>> validator = CacheValidator(Path("cache"))
    >>> demo_path = Path("demos/match.dem")
    >>>
    >>> # Check if cache is valid
    >>> if validator.is_cache_valid(demo_path):
    ...     print("Using cached data")
    ...     cache = load_cache(validator.get_cache_path(demo_path))
    ... else:
    ...     print("Cache invalid, running ETL pipeline")
    ...     cache = run_etl(demo_path)
    ...     validator.save_hash(demo_path)
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheValidationError(Exception):
    """Base exception for cache validation errors."""
    pass


class DemoFileNotFoundError(CacheValidationError):
    """Raised when demo file does not exist."""
    pass


class CacheValidator:
    """Fast cache validator using partial file hashing.

    Validates cache freshness by comparing a fast hash (first 10MB + file size)
    instead of hashing the entire demo file. Dramatically improves performance
    for large demo files (100MB+) while still detecting file changes.

    Attributes:
        cache_dir: Directory where cache files and hash files are stored
        CHUNK_SIZE: Size of chunks for reading files (1MB)
        MAX_HASH_SIZE: Maximum bytes to hash from file (10MB)

    Performance:
        - Hashing 10MB: ~50ms
        - Hashing 500MB: ~2500ms
        - Speedup: 50x faster for large files
    """

    # Constants for hash computation
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks for efficient reading
    MAX_HASH_SIZE = 10 * 1024 * 1024  # Hash first 10MB only

    def __init__(self, cache_dir: Path):
        """Initialize cache validator with specified cache directory.

        Args:
            cache_dir: Directory for storing cache and hash files.
                      Will be created if it doesn't exist.

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> validator.cache_dir
            PosixPath('cache')
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"CacheValidator initialized with cache_dir: {self.cache_dir}")

    def get_demo_hash(self, demo_path: Path) -> str:
        """Compute fast hash of demo file (first 10MB + file size).

        Uses MD5 hash of the first 10MB of the file combined with total file size.
        This provides a good balance between speed and change detection:
        - Fast: Only reads first 10MB regardless of file size
        - Reliable: File size change or header modification triggers rehash
        - Efficient: Uses chunked reading to avoid memory issues

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            Hash string in format "{size_bytes}_{md5_hash}"
            Example: "524288000_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

        Raises:
            DemoFileNotFoundError: If demo file doesn't exist
            CacheValidationError: If file cannot be read

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> hash_val = validator.get_demo_hash(Path("demos/match.dem"))
            >>> print(hash_val)
            524288000_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
        """
        demo_path = Path(demo_path)

        # Check if file exists
        if not demo_path.exists():
            raise DemoFileNotFoundError(
                f"Demo file not found: {demo_path}"
            )

        if not demo_path.is_file():
            raise CacheValidationError(
                f"Path is not a file: {demo_path}"
            )

        try:
            # Get file size
            file_size = demo_path.stat().st_size

            # Compute MD5 of first 10MB (or entire file if smaller)
            md5_hash = hashlib.md5()
            bytes_read = 0

            with open(demo_path, 'rb') as f:
                while bytes_read < self.MAX_HASH_SIZE:
                    # Read chunk (don't exceed MAX_HASH_SIZE)
                    chunk_size = min(
                        self.CHUNK_SIZE,
                        self.MAX_HASH_SIZE - bytes_read
                    )
                    chunk = f.read(chunk_size)

                    if not chunk:
                        break  # EOF reached

                    md5_hash.update(chunk)
                    bytes_read += len(chunk)

            # Create hash string: size_md5
            hash_string = f"{file_size}_{md5_hash.hexdigest()}"

            logger.debug(
                f"Computed hash for {demo_path.name}: {hash_string} "
                f"(read {bytes_read / (1024*1024):.2f} MB of {file_size / (1024*1024):.2f} MB)"
            )

            return hash_string

        except PermissionError as e:
            raise CacheValidationError(
                f"Permission denied reading file: {demo_path}"
            ) from e
        except Exception as e:
            raise CacheValidationError(
                f"Error computing hash for {demo_path}: {e}"
            ) from e

    def is_cache_valid(self, demo_path: Path) -> bool:
        """Check if cache exists and is up-to-date for the given demo file.

        Validates cache by:
        1. Checking if cache file exists (.json)
        2. Checking if hash file exists (.md5)
        3. Computing current demo file hash
        4. Comparing current hash with stored hash

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            True if cache is valid and up-to-date, False otherwise

        Note:
            Returns False (not raises exception) if demo file doesn't exist,
            allowing graceful handling in auto mode.

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> demo = Path("demos/match.dem")
            >>>
            >>> if validator.is_cache_valid(demo):
            ...     print("Cache is fresh, loading...")
            ...     cache = load_cache(validator.get_cache_path(demo))
            ... else:
            ...     print("Cache stale or missing, running ETL...")
            ...     cache = run_etl_pipeline(demo)
            ...     validator.save_hash(demo)
        """
        try:
            # Get paths
            cache_path = self.get_cache_path(demo_path)
            hash_path = self._get_hash_path(demo_path)

            # Check if both cache and hash files exist
            if not cache_path.exists():
                logger.debug(f"Cache file missing: {cache_path}")
                return False

            if not hash_path.exists():
                logger.debug(f"Hash file missing: {hash_path}")
                return False

            # Read stored hash
            stored_hash = hash_path.read_text().strip()

            # Compute current hash
            current_hash = self.get_demo_hash(demo_path)

            # Compare hashes
            is_valid = (stored_hash == current_hash)

            if is_valid:
                logger.info(
                    f"Cache valid for {demo_path.name} "
                    f"(hash: {current_hash[:16]}...)"
                )
            else:
                logger.info(
                    f"Cache invalid for {demo_path.name} "
                    f"(stored: {stored_hash[:16]}..., current: {current_hash[:16]}...)"
                )

            return is_valid

        except DemoFileNotFoundError:
            logger.warning(f"Demo file not found: {demo_path}")
            return False
        except Exception as e:
            logger.error(f"Error validating cache for {demo_path}: {e}")
            return False

    def save_hash(self, demo_path: Path) -> bool:
        """Save hash of demo file after successful ETL processing.

        Computes and stores the demo file hash to enable future cache validation.
        Should be called after successfully generating cache data.

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            True if hash was saved successfully, False otherwise

        Raises:
            DemoFileNotFoundError: If demo file doesn't exist
            CacheValidationError: If hash cannot be computed or saved

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> demo = Path("demos/match.dem")
            >>>
            >>> # After running ETL and saving cache
            >>> cache_data = run_etl_pipeline(demo)
            >>> save_cache(cache_data, validator.get_cache_path(demo))
            >>> validator.save_hash(demo)  # Mark cache as valid
            True
        """
        try:
            # Compute current hash
            current_hash = self.get_demo_hash(demo_path)

            # Get hash file path
            hash_path = self._get_hash_path(demo_path)

            # Save hash to file
            hash_path.write_text(current_hash)

            logger.info(
                f"Saved hash for {demo_path.name}: {current_hash} "
                f"to {hash_path}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save hash for {demo_path}: {e}")
            raise CacheValidationError(
                f"Cannot save hash for {demo_path}: {e}"
            ) from e

    def get_cache_path(self, demo_path: Path) -> Path:
        """Get path to cache file for the given demo file.

        Converts demo file path to corresponding cache file path:
        - demos/match.dem -> cache/match.dem.json
        - /path/to/demo.dem -> cache/demo.dem.json

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            Path to cache file (.json) in cache directory

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> cache_path = validator.get_cache_path(Path("demos/match.dem"))
            >>> print(cache_path)
            cache/match.dem.json
        """
        demo_path = Path(demo_path)
        cache_filename = demo_path.name + ".json"
        return self.cache_dir / cache_filename

    def _get_hash_path(self, demo_path: Path) -> Path:
        """Get path to hash file for the given demo file.

        Internal method to determine hash file location:
        - demos/match.dem -> cache/match.md5
        - /path/to/demo.dem -> cache/demo.md5

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            Path to hash file (.md5) in cache directory
        """
        demo_path = Path(demo_path)
        hash_filename = demo_path.stem + ".md5"
        return self.cache_dir / hash_filename

    def invalidate_cache(self, demo_path: Path) -> bool:
        """Invalidate cache by removing hash file.

        Removes the hash file to force cache regeneration on next validation.
        Useful for manual cache invalidation or testing.

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            True if hash file was removed, False if it didn't exist

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> demo = Path("demos/match.dem")
            >>>
            >>> # Force cache regeneration
            >>> validator.invalidate_cache(demo)
            True
            >>> validator.is_cache_valid(demo)
            False
        """
        try:
            hash_path = self._get_hash_path(demo_path)

            if hash_path.exists():
                hash_path.unlink()
                logger.info(f"Invalidated cache for {demo_path.name}")
                return True
            else:
                logger.debug(f"No hash file to invalidate for {demo_path.name}")
                return False

        except Exception as e:
            logger.error(f"Error invalidating cache for {demo_path}: {e}")
            return False

    def get_cache_info(self, demo_path: Path) -> dict:
        """Get information about cache status for a demo file.

        Returns detailed information about cache and hash file status,
        useful for debugging and monitoring.

        Args:
            demo_path: Path to demo file (.dem)

        Returns:
            Dictionary with cache information:
                - demo_exists: bool - whether demo file exists
                - cache_exists: bool - whether cache file exists
                - hash_exists: bool - whether hash file exists
                - is_valid: bool - whether cache is valid
                - demo_size: int - demo file size in bytes (or None)
                - cache_size: int - cache file size in bytes (or None)
                - current_hash: str - current demo hash (or None)
                - stored_hash: str - stored hash (or None)

        Example:
            >>> validator = CacheValidator(Path("cache"))
            >>> info = validator.get_cache_info(Path("demos/match.dem"))
            >>> print(f"Cache valid: {info['is_valid']}")
            >>> print(f"Demo size: {info['demo_size'] / (1024*1024):.2f} MB")
        """
        demo_path = Path(demo_path)
        cache_path = self.get_cache_path(demo_path)
        hash_path = self._get_hash_path(demo_path)

        info = {
            "demo_exists": demo_path.exists(),
            "cache_exists": cache_path.exists(),
            "hash_exists": hash_path.exists(),
            "is_valid": False,
            "demo_size": None,
            "cache_size": None,
            "current_hash": None,
            "stored_hash": None,
        }

        # Get demo file info
        if info["demo_exists"]:
            try:
                info["demo_size"] = demo_path.stat().st_size
                info["current_hash"] = self.get_demo_hash(demo_path)
            except Exception as e:
                logger.error(f"Error reading demo file: {e}")

        # Get cache file size
        if info["cache_exists"]:
            try:
                info["cache_size"] = cache_path.stat().st_size
            except Exception as e:
                logger.error(f"Error reading cache file: {e}")

        # Get stored hash
        if info["hash_exists"]:
            try:
                info["stored_hash"] = hash_path.read_text().strip()
            except Exception as e:
                logger.error(f"Error reading hash file: {e}")

        # Check validity
        if info["current_hash"] and info["stored_hash"]:
            info["is_valid"] = (info["current_hash"] == info["stored_hash"])

        return info


# Utility functions

def validate_cache_directory(cache_dir: Path) -> bool:
    """Validate that cache directory exists and is writable.

    Args:
        cache_dir: Path to cache directory

    Returns:
        True if directory is valid and writable, False otherwise

    Example:
        >>> if validate_cache_directory(Path("cache")):
        ...     print("Cache directory is ready")
        ... else:
        ...     print("Cache directory is invalid")
    """
    try:
        cache_dir = Path(cache_dir)

        # Check if exists and is directory
        if not cache_dir.exists():
            logger.warning(f"Cache directory does not exist: {cache_dir}")
            return False

        if not cache_dir.is_dir():
            logger.error(f"Cache path is not a directory: {cache_dir}")
            return False

        # Check if writable by attempting to create a test file
        test_file = cache_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Cache directory is not writable: {e}")
            return False

    except Exception as e:
        logger.error(f"Error validating cache directory: {e}")
        return False


def clean_orphaned_files(cache_dir: Path, demo_dir: Path) -> int:
    """Remove cache and hash files for demos that no longer exist.

    Scans cache directory and removes .json/.md5 files that don't have
    corresponding .dem files in the demo directory.

    Args:
        cache_dir: Path to cache directory
        demo_dir: Path to directory containing demo files

    Returns:
        Number of orphaned files removed

    Example:
        >>> removed = clean_orphaned_files(Path("cache"), Path("demos"))
        >>> print(f"Removed {removed} orphaned cache files")
    """
    try:
        cache_dir = Path(cache_dir)
        demo_dir = Path(demo_dir)

        if not cache_dir.exists() or not demo_dir.exists():
            logger.error("Cache or demo directory does not exist")
            return 0

        # Get all demo file stems (names without extension)
        demo_stems = {
            demo.stem for demo in demo_dir.glob("*.dem")
        }

        removed_count = 0

        # Check cache files
        for cache_file in cache_dir.glob("*.json"):
            if cache_file.stem not in demo_stems:
                logger.info(f"Removing orphaned cache file: {cache_file}")
                cache_file.unlink()
                removed_count += 1

        # Check hash files
        for hash_file in cache_dir.glob("*.md5"):
            if hash_file.stem not in demo_stems:
                logger.info(f"Removing orphaned hash file: {hash_file}")
                hash_file.unlink()
                removed_count += 1

        logger.info(f"Removed {removed_count} orphaned files from cache")
        return removed_count

    except Exception as e:
        logger.error(f"Error cleaning orphaned files: {e}")
        return 0


# Example usage and testing
if __name__ == "__main__":
    import time

    # Example: Setup cache validator
    validator = CacheValidator(Path("cache"))

    print("=" * 60)
    print("CS2 Demo Cache Validator - Example Usage")
    print("=" * 60)

    # Test with mock demo file
    demo_path = Path("data/mock_demo.dem")

    # Create a mock demo file for testing
    if not demo_path.exists():
        demo_path.parent.mkdir(parents=True, exist_ok=True)
        # Create 15MB test file
        with open(demo_path, 'wb') as f:
            f.write(b'CS2DEMO' * (15 * 1024 * 1024 // 7))
        print(f"\n✓ Created test demo file: {demo_path}")

    # 1. Compute hash
    print(f"\n1. Computing hash for {demo_path.name}...")
    start = time.time()
    demo_hash = validator.get_demo_hash(demo_path)
    hash_time = time.time() - start
    print(f"   Hash: {demo_hash}")
    print(f"   Time: {hash_time * 1000:.2f} ms")

    # 2. Check cache validity (should be invalid first time)
    print(f"\n2. Checking cache validity...")
    is_valid = validator.is_cache_valid(demo_path)
    print(f"   Valid: {is_valid} (expected: False - no cache yet)")

    # 3. Save hash (simulating ETL completion)
    print(f"\n3. Saving hash (simulating ETL completion)...")
    validator.save_hash(demo_path)
    print(f"   ✓ Hash saved to {validator._get_hash_path(demo_path)}")

    # 4. Create mock cache file
    cache_path = validator.get_cache_path(demo_path)
    cache_path.write_text('{"meta": {}, "inputs": {}}')
    print(f"   ✓ Mock cache created at {cache_path}")

    # 5. Check cache validity again (should be valid now)
    print(f"\n4. Checking cache validity again...")
    is_valid = validator.is_cache_valid(demo_path)
    print(f"   Valid: {is_valid} (expected: True - cache exists)")

    # 6. Get cache info
    print(f"\n5. Getting cache information...")
    info = validator.get_cache_info(demo_path)
    print(f"   Demo exists: {info['demo_exists']}")
    print(f"   Cache exists: {info['cache_exists']}")
    print(f"   Hash exists: {info['hash_exists']}")
    print(f"   Is valid: {info['is_valid']}")
    print(f"   Demo size: {info['demo_size'] / (1024*1024):.2f} MB")
    if info['cache_size']:
        print(f"   Cache size: {info['cache_size']} bytes")

    # 7. Invalidate cache
    print(f"\n6. Invalidating cache...")
    validator.invalidate_cache(demo_path)
    is_valid = validator.is_cache_valid(demo_path)
    print(f"   Valid: {is_valid} (expected: False - hash removed)")

    # 8. Performance comparison
    print(f"\n7. Performance Comparison:")
    print(f"   Partial hash (10MB): {hash_time * 1000:.2f} ms")

    # Full file hash for comparison
    start = time.time()
    full_md5 = hashlib.md5()
    with open(demo_path, 'rb') as f:
        while chunk := f.read(validator.CHUNK_SIZE):
            full_md5.update(chunk)
    full_hash_time = time.time() - start
    print(f"   Full file hash:      {full_hash_time * 1000:.2f} ms")
    print(f"   Speedup:             {full_hash_time / hash_time:.1f}x faster")

    print(f"\n{'=' * 60}")
    print("Cache validator test complete!")
    print(f"{'=' * 60}\n")

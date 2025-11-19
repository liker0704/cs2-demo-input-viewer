"""CS2 installation path detection utility.

This module provides functionality to automatically detect the Counter-Strike 2
installation directory by checking running processes and common Steam installation paths.
"""

import platform
from pathlib import Path
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


class CS2PathDetector:
    """Detects CS2 installation path for automatic demo file discovery.

    This class attempts to find the CS2 installation directory by:
    1. Checking a user-provided configuration path
    2. Finding the running CS2 process and extracting its executable path
    3. Falling back to standard Steam installation directories

    The detector returns the path to the 'game/csgo' directory where
    demo files (.dem) are stored.

    Example:
        >>> detector = CS2PathDetector()
        >>> csgo_path = detector.find_cs2_path()
        >>> if csgo_path:
        ...     print(f"Found CS2 at: {csgo_path}")
        ...     demo_files = list(csgo_path.glob("*.dem"))
    """

    # Process names to search for (CS2 executable names)
    CS2_PROCESS_NAMES = ["cs2.exe", "cs2"]

    # Standard Steam installation paths by platform
    STEAM_PATHS_WINDOWS = [
        Path("C:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive/game/csgo"),
        Path("C:/Program Files/Steam/steamapps/common/Counter-Strike Global Offensive/game/csgo"),
        Path("C:/Program Files (x86)/Steam/steamapps/common/Counter-Strike 2/game/csgo"),
        Path("C:/Program Files/Steam/steamapps/common/Counter-Strike 2/game/csgo"),
    ]

    STEAM_PATHS_LINUX = [
        Path.home() / ".steam/steam/steamapps/common/Counter-Strike 2/game/csgo",
        Path.home() / ".local/share/Steam/steamapps/common/Counter-Strike 2/game/csgo",
    ]

    def find_cs2_path(self, config_path: Optional[Path] = None) -> Optional[Path]:
        """Find CS2 installation path.

        Attempts to locate the CS2 installation directory using multiple strategies:
        1. Check user-provided config_path if specified
        2. Search for running CS2 process and extract path from executable
        3. Check platform-specific default Steam installation directories

        Args:
            config_path: Optional user-defined path to check first.
                        Should point to the game/csgo directory or CS2 root.

        Returns:
            Path to the game/csgo directory if found, None otherwise.

        Example:
            >>> detector = CS2PathDetector()
            >>> # Try with custom path first
            >>> path = detector.find_cs2_path(Path("/custom/cs2/location"))
            >>> # Or auto-detect
            >>> path = detector.find_cs2_path()
        """
        # Strategy 1: Check user-provided config path
        if config_path is not None:
            validated_path = self._validate_cs2_path(config_path)
            if validated_path:
                return validated_path

        # Strategy 2: Find by running process
        process_path = self._find_by_process()
        if process_path:
            return process_path

        # Strategy 3: Check default Steam installation paths
        default_path = self._check_default_paths()
        if default_path:
            return default_path

        return None

    def _find_by_process(self) -> Optional[Path]:
        """Find CS2 installation path by locating running process.

        Searches for running CS2 process (cs2.exe on Windows, cs2 on Linux)
        and extracts the installation directory from the process executable path.

        Returns:
            Path to game/csgo directory if CS2 process is found, None otherwise.

        Note:
            Requires psutil to be installed. Returns None if psutil is not available.
        """
        if psutil is None:
            return None

        try:
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and proc_name.lower() in [name.lower() for name in self.CS2_PROCESS_NAMES]:
                        exe_path = proc.info['exe']
                        if exe_path:
                            # Extract installation path from executable
                            # Executable is typically at: <install_dir>/game/bin/<platform>/cs2.exe
                            exe_path_obj = Path(exe_path)

                            # Navigate up to find game/csgo directory
                            # From: <install>/game/bin/<platform>/cs2.exe
                            # To:   <install>/game/csgo
                            game_dir = exe_path_obj.parent.parent.parent
                            csgo_dir = game_dir / "csgo"

                            validated_path = self._validate_cs2_path(csgo_dir)
                            if validated_path:
                                return validated_path

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Skip processes we can't access
                    continue

        except Exception:
            # Catch-all for any unexpected psutil errors
            pass

        return None

    def _check_default_paths(self) -> Optional[Path]:
        """Check standard Steam installation paths.

        Checks platform-specific default Steam installation directories where
        CS2 is commonly installed.

        Returns:
            Path to game/csgo directory if found in default locations, None otherwise.
        """
        system = platform.system()

        if system == "Windows":
            paths_to_check = self.STEAM_PATHS_WINDOWS
        elif system == "Linux":
            paths_to_check = self.STEAM_PATHS_LINUX
        else:
            # Unsupported platform (e.g., macOS - CS2 doesn't officially support it)
            return None

        for path in paths_to_check:
            validated_path = self._validate_cs2_path(path)
            if validated_path:
                return validated_path

        return None

    def _validate_cs2_path(self, path: Path) -> Optional[Path]:
        """Validate that a path points to a valid CS2 installation.

        Checks if the provided path exists and appears to be a valid CS2
        game/csgo directory.

        Args:
            path: Path to validate. Can be the game/csgo directory directly
                  or the CS2 root directory.

        Returns:
            Validated Path to game/csgo directory if valid, None otherwise.
        """
        if not path.exists():
            return None

        # If path points to game/csgo directory directly
        if path.name == "csgo" and path.parent.name == "game":
            if path.is_dir():
                return path

        # If path points to CS2 root, try to find game/csgo
        csgo_path = path / "game" / "csgo"
        if csgo_path.exists() and csgo_path.is_dir():
            return csgo_path

        # If path points to game directory, try to find csgo
        if path.name == "game":
            csgo_path = path / "csgo"
            if csgo_path.exists() and csgo_path.is_dir():
                return csgo_path

        return None

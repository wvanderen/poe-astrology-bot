#!/usr/bin/env python3
"""

Download Swiss Ephemeris data files for astrology calculations.

This script downloads the necessary ephemeris files from the official
Swiss Ephemeris GitHub repository. These files are required for accurate
planetary position calculations.

Files downloaded:
- sepl_18.se1: Planetary ephemeris (1800-2400)
- semo_18.se1: Lunar ephemeris (1800-2400)

"""

import os
import urllib.request
import sys

# Base URL for Swiss Ephemeris files
EPHE_BASE_URL = "https://github.com/aloistr/swisseph/raw/master/ephe"

# Required files for basic chart calculations (1800-2400 coverage)
REQUIRED_FILES = [
    "sepl_18.se1",  # Planets
    "semo_18.se1",  # Moon
]

# Alternative: Full asteroid support
OPTIONAL_FILES = [
    "seas_18.se1",  # Main asteroids (Ceres, Pallas, Juno, Vesta)
]


def download_file(url: str, dest_path: str) -> bool:
    """Download a file from URL to destination."""
    try:
        print(f"Downloading {os.path.basename(dest_path)}...")
        urllib.request.urlretrieve(url, dest_path)
        print(f"  ✓ Downloaded to {dest_path}")
        return True
    except Exception as e:
        print(f"  ✗ Error downloading: {e}")
        return False


def setup_ephemeris(ephe_dir: str = "ephe", include_asteroids: bool = False) -> bool:
    """
    Download and setup Swiss Ephemeris files.
    
    Args:
        ephe_dir: Directory to store ephemeris files
        include_asteroids: Whether to include asteroid files
        
    Returns:
        True if all files downloaded successfully
    """
    # Create directory if it doesn't exist
    os.makedirs(ephe_dir, exist_ok=True)
    
    files_to_download = REQUIRED_FILES.copy()
    if include_asteroids:
        files_to_download.extend(OPTIONAL_FILES)
    
    success = True
    for filename in files_to_download:
        url = f"{EPHE_BASE_URL}/{filename}"
        dest_path = os.path.join(ephe_dir, filename)
        
        # Skip if already exists
        if os.path.exists(dest_path):
            print(f"✓ {filename} already exists")
            continue
            
        if not download_file(url, dest_path):
            success = False
    
    return success


def main():
    """Main entry point."""
    ephe_dir = "ephe"
    include_asteroids = "--asteroids" in sys.argv
    
    print("Swiss Ephemeris Setup")
    print("=" * 50)
    print(f"Target directory: {os.path.abspath(ephe_dir)}")
    print(f"Include asteroids: {include_asteroids}")
    print()
    
    if setup_ephemeris(ephe_dir, include_asteroids):
        print()
        print("✓ Setup complete!")
        print()
        print("To use in your code:")
        print(f"  import swisseph as swe")
        print(f"  swe.set_ephe_path('{ephe_dir}')")
        return 0
    else:
        print()
        print("✗ Setup failed. Some files could not be downloaded.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

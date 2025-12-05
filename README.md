# Media Manager

A clean, automated tool to rename Movies and TV Shows for Plex, Jellyfin, and Kodi using The Movie Database (TMDB).

## Features
- Automatically distinguishes between Movies and TV Shows.
- Renames files to industry standards:
  - Movies: "Movie Title (Year).ext"
  - TV: "Show Name - S01E01 - Episode Title.ext"
- Modern dark mode interface.
- Threaded scanning for high performance.

## Installation

### Option 1: Download Executable
Download the latest .exe file from the GitHub Releases page. No installation required.

### Option 2: Run from Source
1. Install Python 3.10 or higher.
2. Install dependencies:
   pip install requests guessit customtkinter
3. Run the application:
   python media_manager.py

## Configuration
The app requires a TMDB API Key to fetch metadata.
1. Create an account at The Movie Database (https://www.themoviedb.org/).
2. Navigate to Settings > API.
3. Copy your key and paste it into the app's input field.
(A default key is provided for testing purposes).

## Building the EXE
If you want to compile the binary yourself:

1. Install PyInstaller:
   pip install pyinstaller

2. Run the build script:
   python build_exe.py

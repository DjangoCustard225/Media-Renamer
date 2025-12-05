<div align="center">

  # 🎬 Media Manager
  
  **The elegant way to organize your media library.**
  
  <br>

  <!-- BADGES -->
  <a href="https://github.com/DjangoCustard225/Media-Renamer/actions">
    <img src="https://img.shields.io/badge/Build-Passing-success?style=for-the-badge&logo=github" alt="Build Status"/>
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Made%20With-Python%203.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  </a>
  <a href="https://github.com/DjangoCustard225/Media-Renamer/releases">
    <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  </a>
  <a href="https://www.themoviedb.org/">
    <img src="https://img.shields.io/badge/Data%20Source-TMDB-01d277?style=for-the-badge&logo=themoviedatabase&logoColor=white" alt="TMDB"/>
  </a>

  <br><br>

 <!-- SCREENSHOT -->
<a href="https://github.com/DjangoCustard225/Media-Renamer">
  <img src="https://raw.githubusercontent.com/DjangoCustard225/Media-Renamer/main/assets/screenshot.png" alt="Media Manager Screenshot" width="850" style="border-radius: 12px; box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.5);">
</a>

  <br><br>
  
  <p align="center">
    <b>Media Manager</b> transforms messy filenames into a clean, curated library compatible with Plex, Jellyfin, and Kodi.
    <br>
    Built with a stunning modern UI and powered by The Movie Database.
  </p>

</div>

---

## ✨ Features

*   **🔍 Smart Detection:** Automatically identifies Movies vs. TV Shows using `guessit` advanced logic.
*   **🎨 Modern Dark UI:** A sleek, responsive interface built with `CustomTkinter` that looks at home on Windows 11.
*   **📂 Flexible Input:** Drag and drop an entire folder or select specific files to process.
*   **🛡️ Safety First:** Review a "Before & After" queue of all changes. Nothing is renamed until you click the red button.
*   **⚡ High Performance:** Threaded scanning ensures the app remains buttery smooth even when processing hundreds of files.

## 🚀 Naming Standard

Your files are renamed to the industry standard for media servers:

| Type | Original File | Renamed Result |
| :--- | :--- | :--- |
| **Movie** | `bullet.train.2022.1080p.webrip.mp4` | `Bullet Train (2022).mp4` |
| **TV Episode** | `the.office.us.s02e03.avi` | `The Office - S02E03 - The Fire.avi` |

## 📥 Installation

### 1. Download Executable (Recommended)
Simply download the latest `.exe` from the **[Releases Page](https://github.com/DjangoCustard225/Media-Renamer/releases)**. No installation required.

### 2. Run from Source
If you prefer to run the Python script directly:

```bash
# Clone the repo
git clone https://github.com/DjangoCustard225/Media-Renamer.git
cd Media-Renamer

# Install requirements
pip install requests guessit customtkinter

# Run the app
python media_manager.py

python build_exe.py


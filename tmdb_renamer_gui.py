import os
import threading
import tkinter as choice
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests
import guessit

# --- CONFIGURATION & BACKEND LOGIC ---
TMDB_API_KEY_DEFAULT = "90133f302432a60ea8a21ce6bfc66302"
BASE_URL = "https://api.themoviedb.org/3"
VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.wmv', '.m4v')

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

class TMDbBackend:
    """Handles the API communication and parsing logic."""
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, filename):
        """Orchestrates the guessit + tmdb search logic."""
        try:
            guess = guessit.guessit(filename)
        except:
            return None, "Parse Error"

        title = guess.get('title')
        year = guess.get('year')
        type_ = guess.get('type') # 'movie' or 'episode'

        if not title:
            return None, "No Title Found"

        if type_ == 'movie':
            return self._handle_movie(title, year)
        elif type_ == 'episode':
            season = guess.get('season')
            episode = guess.get('episode')
            if isinstance(episode, list): episode = episode[0] 
            return self._handle_episode(title, year, season, episode)
        else:
            return None, "Unknown Type"

    def _handle_movie(self, title, year):
        params = {
            'api_key': self.api_key,
            'query': title,
            'include_adult': 'false',
            'year': year
        }
        try:
            res = requests.get(f"{BASE_URL}/search/movie", params=params)
            res.raise_for_status()
            results = res.json().get('results', [])
            if results:
                match = results[0]
                release_date = match.get('release_date', '')
                y = release_date.split('-')[0] if release_date else (str(year) if year else "")
                clean_title = self._sanitize(match['title'])
                return f"{clean_title} ({y})", "Movie Found"
            return None, "Movie Not Found"
        except Exception as e:
            return None, f"API Error"

    def _handle_episode(self, title, year, season, episode):
        if not season or not episode:
            return None, "Missing S/E"

        # 1. Find Show
        params = {'api_key': self.api_key, 'query': title, 'first_air_date_year': year}
        try:
            res = requests.get(f"{BASE_URL}/search/tv", params=params)
            res.raise_for_status()
            results = res.json().get('results', [])
            
            if not results:
                return None, "Show Not Found"
            
            show = results[0]
            show_id = show['id']
            show_name = show['name']

            # 2. Find Episode Name
            ep_url = f"{BASE_URL}/tv/{show_id}/season/{season}/episode/{episode}"
            ep_res = requests.get(ep_url, params={'api_key': self.api_key})
            ep_name = f"Episode {episode}"
            if ep_res.status_code == 200:
                ep_data = ep_res.json()
                if ep_data.get('name'):
                    ep_name = ep_data.get('name')

            clean_show = self._sanitize(show_name)
            clean_ep = self._sanitize(ep_name)
            
            return f"{clean_show} - S{season:02d}E{episode:02d} - {clean_ep}", "Episode Found"

        except Exception as e:
            return None, "API Error"

    def _sanitize(self, name):
        return "".join([c for c in name if c.isalnum() or c in ' .-_()']).strip()

# --- GUI CLASS ---

class FileRow(ctk.CTkFrame):
    """Represents a single file row in the scrollable list."""
    def __init__(self, master, filename, full_path, **kwargs):
        super().__init__(master, **kwargs)
        self.full_path = full_path
        self.filename = filename
        self.new_name = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # Status Indicator (Color Box)
        self.status_indicator = ctk.CTkLabel(self, text="", width=10, height=30, fg_color="gray", corner_radius=5)
        self.status_indicator.grid(row=0, column=0, padx=(5, 5), pady=5)

        # Old Name
        self.lbl_old = ctk.CTkLabel(self, text=filename, anchor="w", text_color="silver")
        self.lbl_old.grid(row=0, column=1, padx=5, sticky="ew")

        # Arrow
        self.lbl_arrow = ctk.CTkLabel(self, text="➜", text_color="gray")
        self.lbl_arrow.grid(row=0, column=2, padx=5)

        # New Name
        self.lbl_new = ctk.CTkLabel(self, text="Pending...", anchor="w", text_color="gray")
        self.lbl_new.grid(row=0, column=3, padx=5, sticky="ew")

    def update_status(self, new_name_res, status_msg, is_success):
        if is_success and new_name_res:
            _, ext = os.path.splitext(self.filename)
            self.new_name = new_name_res + ext
            self.lbl_new.configure(text=self.new_name, text_color="#4CC9F0") # Cyan
            self.status_indicator.configure(fg_color="#06D6A0") # Green
        else:
            self.new_name = None
            self.lbl_new.configure(text=status_msg, text_color="#EF476F") # Red
            self.status_indicator.configure(fg_color="#EF476F")

    def mark_renamed(self):
        self.status_indicator.configure(fg_color="#FFD166") # Yellow/Gold
        self.lbl_old.configure(text_color="gray")
        self.lbl_new.configure(text="Renamed Successfully", text_color="#06D6A0")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TMDB Auto Renamer")
        self.geometry("900x700")
        self.file_rows = []
        
        # --- HEADER ---
        self.frm_header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        self.frm_header.pack(fill="x", padx=20, pady=10)

        self.lbl_title = ctk.CTkLabel(self.frm_header, text="Movie & TV Renamer", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(side="left")

        self.ent_api = ctk.CTkEntry(self.frm_header, width=300, placeholder_text="API Key")
        self.ent_api.insert(0, TMDB_API_KEY_DEFAULT)
        self.ent_api.pack(side="right")
        
        # --- CONTROLS ---
        self.frm_controls = ctk.CTkFrame(self, height=60)
        self.frm_controls.pack(fill="x", padx=20, pady=(0, 10))

        self.btn_browse = ctk.CTkButton(self.frm_controls, text="Select Folder", command=self.select_folder, width=150)
        self.btn_browse.pack(side="left", padx=10, pady=10)

        self.lbl_path = ctk.CTkLabel(self.frm_controls, text="No folder selected", text_color="gray")
        self.lbl_path.pack(side="left", padx=10)

        self.btn_scan = ctk.CTkButton(self.frm_controls, text="Start Scan", state="disabled", command=self.start_scan_thread, fg_color="#7209B7")
        self.btn_scan.pack(side="right", padx=10, pady=10)

        # --- PROGRESS BAR ---
        self.progress = ctk.CTkProgressBar(self, height=10)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=20, pady=(0, 10))
        self.progress.pack_forget() # Hide initially

        # --- FILE LIST (SCROLLABLE) ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Files Found")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- FOOTER ---
        self.frm_footer = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.frm_footer.pack(fill="x", padx=20, pady=10)

        self.lbl_status = ctk.CTkLabel(self.frm_footer, text="Ready", anchor="w")
        self.lbl_status.pack(side="left")

        self.btn_rename = ctk.CTkButton(self.frm_footer, text="RENAME ALL", state="disabled", fg_color="#EF476F", command=self.rename_files_thread)
        self.btn_rename.pack(side="right")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.lbl_path.configure(text=folder)
            self.btn_scan.configure(state="normal")
            
            # Clear previous list
            for row in self.file_rows:
                row.destroy()
            self.file_rows = []
            
            # Populate list immediately with files
            self.files_to_process = []
            for root_dir, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(VIDEO_EXTENSIONS):
                        full_path = os.path.join(root_dir, f)
                        self.files_to_process.append((f, full_path))
                        
                        # Add row to UI
                        row = FileRow(self.scroll_frame, filename=f, full_path=full_path)
                        row.pack(fill="x", padx=5, pady=2)
                        self.file_rows.append(row)
            
            self.lbl_status.configure(text=f"Found {len(self.file_rows)} video files. Click 'Start Scan' to query TMDB.")

    def start_scan_thread(self):
        if not self.file_rows:
            return
        
        api_key = self.ent_api.get().strip()
        if not api_key:
            messagebox.showerror("Error", "API Key is required")
            return
        
        self.backend = TMDbBackend(api_key)
        self.btn_scan.configure(state="disabled")
        self.btn_browse.configure(state="disabled")
        self.progress.pack(fill="x", padx=20, pady=(0, 10))
        self.progress.set(0)
        
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        total = len(self.file_rows)
        processed = 0
        success_count = 0

        for row in self.file_rows:
            # Update Status text
            self.update_status_label(f"Scanning: {row.filename}...")
            
            # Call API
            new_name, msg = self.backend.search(row.filename)
            is_success = new_name is not None
            
            if is_success: success_count += 1
            
            # Update Row UI (Must be done on main thread usually, 
            # but simple CTk configures are often thread-safe-ish. 
            # For strict safety we use after)
            self.after(0, lambda r=row, n=new_name, m=msg, s=is_success: r.update_status(n, m, s))
            
            processed += 1
            self.after(0, lambda p=processed/total: self.progress.set(p))
        
        self.after(0, lambda: self.finish_scan(success_count))

    def update_status_label(self, text):
        self.after(0, lambda: self.lbl_status.configure(text=text))

    def finish_scan(self, success_count):
        self.btn_browse.configure(state="normal")
        self.btn_scan.configure(state="normal")
        self.progress.pack_forget()
        
        if success_count > 0:
            self.btn_rename.configure(state="normal")
            self.update_status_label(f"Scan complete. {success_count} matches found. Ready to rename.")
        else:
            self.update_status_label("Scan complete. No matches found.")

    def rename_files_thread(self):
        if messagebox.askyesno("Confirm Rename", "Are you sure you want to rename these files? This cannot be undone."):
            self.btn_rename.configure(state="disabled")
            threading.Thread(target=self.run_rename, daemon=True).start()

    def run_rename(self):
        for row in self.file_rows:
            if row.new_name:
                old_path = row.full_path
                directory = os.path.dirname(old_path)
                new_path = os.path.join(directory, row.new_name)
                
                try:
                    os.rename(old_path, new_path)
                    self.after(0, lambda r=row: r.mark_renamed())
                except Exception as e:
                    print(f"Error renaming {row.filename}: {e}")
        
        self.update_status_label("Renaming Complete.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
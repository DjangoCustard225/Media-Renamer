import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests
import guessit
import re

# --- CONFIGURATION ---
TMDB_API_KEY_DEFAULT = "90133f302432a60ea8a21ce6bfc66302"
BASE_URL = "https://api.themoviedb.org/3"
VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.wmv', '.m4v')

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- NAMING ENGINE (FileBot Style) ---
class NamingEngine:
    @staticmethod
    def format_string(pattern, data):
        """
        Replaces FileBot style tokens with actual data.
        Supported tokens: {n}, {y}, {t}, {s}, {e}, {s00e00}
        """
        name = data.get('n', '')
        year = str(data.get('y', ''))
        title = data.get('t', '')
        season = data.get('s', 0)
        episode = data.get('e', 0)
        
        # 1. Handle {s00e00} special token
        if "{s00e00}" in pattern:
            s_str = f"S{int(season):02d}E{int(episode):02d}"
            pattern = pattern.replace("{s00e00}", s_str)

        # 2. Simple Replacements
        replacements = {
            "{n}": name,
            "{y}": year,
            "{t}": title,
            "{s}": str(season),
            "{e}": str(episode)
        }
        
        result = pattern
        for token, value in replacements.items():
            result = result.replace(token, value)
            
        # 3. Clean up empty brackets/parentheses if year was missing
        # e.g. "Name ()" -> "Name"
        result = result.replace("()", "").replace("[]", "").strip()
        
        return NamingEngine.sanitize(result)

    @staticmethod
    def sanitize(filename):
        # Remove illegal characters
        clean = "".join([c for c in filename if c.isalnum() or c in ' .-_()'])
        # Remove double spaces
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

class TMDbBackend:
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, filename, movie_fmt, tv_fmt):
        try:
            guess = guessit.guessit(filename)
        except:
            return None, "Parse Error"

        title = guess.get('title')
        year = guess.get('year')
        type_ = guess.get('type')

        if not title:
            return None, "No Title"

        if type_ == 'movie':
            data = self._handle_movie(title, year)
            if not data: return None, "Not Found"
            return NamingEngine.format_string(movie_fmt, data), "Movie Found"
            
        elif type_ == 'episode':
            season = guess.get('season')
            episode = guess.get('episode')
            if isinstance(episode, list): episode = episode[0]
            
            data = self._handle_episode(title, year, season, episode)
            if not data: return None, "Not Found"
            return NamingEngine.format_string(tv_fmt, data), "Episode Found"
            
        else:
            return None, "Skip (Type)"

    def _handle_movie(self, title, year):
        params = {'api_key': self.api_key, 'query': title, 'year': year, 'include_adult': 'false'}
        try:
            res = requests.get(f"{BASE_URL}/search/movie", params=params)
            res.raise_for_status()
            results = res.json().get('results', [])
            if results:
                match = results[0]
                r_date = match.get('release_date', '')
                y = r_date.split('-')[0] if r_date else (str(year) if year else "")
                return {'n': match['title'], 'y': y}
        except: pass
        return None

    def _handle_episode(self, title, year, season, episode):
        if not season or not episode: return None
        
        # 1. Find Show
        params = {'api_key': self.api_key, 'query': title, 'first_air_date_year': year}
        try:
            res = requests.get(f"{BASE_URL}/search/tv", params=params)
            res.raise_for_status()
            results = res.json().get('results', [])
            
            if results:
                show = results[0]
                show_name = show['name']
                show_id = show['id']
                show_year = show.get('first_air_date', '').split('-')[0]

                # 2. Find Episode
                ep_url = f"{BASE_URL}/tv/{show_id}/season/{season}/episode/{episode}"
                ep_res = requests.get(ep_url, params={'api_key': self.api_key})
                ep_name = f"Episode {episode}"
                if ep_res.status_code == 200:
                    ep_data = ep_res.json()
                    if ep_data.get('name'): ep_name = ep_data.get('name')

                return {
                    'n': show_name,
                    'y': show_year,
                    's': season,
                    'e': episode,
                    't': ep_name
                }
        except: pass
        return None

# --- GUI ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Renamer (FileBot Style)")
        self.geometry("1000x800")
        self.file_rows = []

        # --- TOP HEADER ---
        header = ctk.CTkFrame(self, height=60, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(header, text="TMDB Renamer", font=("Roboto", 22, "bold")).pack(side="left")
        self.ent_api = ctk.CTkEntry(header, width=250, placeholder_text="API Key")
        self.ent_api.insert(0, TMDB_API_KEY_DEFAULT)
        self.ent_api.pack(side="right")

        # --- PRESETS AREA ---
        self.frm_presets = ctk.CTkFrame(self)
        self.frm_presets.pack(fill="x", padx=20, pady=5)
        
        # Preset Dropdown
        ctk.CTkLabel(self.frm_presets, text="Preset:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.cb_preset = ctk.CTkComboBox(self.frm_presets, values=["Plex {plex}", "Kodi", "Simple", "Scene"], command=self.apply_preset)
        self.cb_preset.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.cb_preset.set("Plex {plex}")

        # Movie Pattern Input
        ctk.CTkLabel(self.frm_presets, text="Movie Format:").grid(row=0, column=2, padx=10, sticky="e")
        self.ent_fmt_movie = ctk.CTkEntry(self.frm_presets, width=250)
        self.ent_fmt_movie.grid(row=0, column=3, padx=10, sticky="w")

        # TV Pattern Input
        ctk.CTkLabel(self.frm_presets, text="TV Format:").grid(row=0, column=4, padx=10, sticky="e")
        self.ent_fmt_tv = ctk.CTkEntry(self.frm_presets, width=250)
        self.ent_fmt_tv.grid(row=0, column=5, padx=10, sticky="w")
        
        # Apply Default
        self.apply_preset("Plex {plex}")

        # Legend (Help)
        lbl_legend = ctk.CTkLabel(self.frm_presets, text="Legend:  {n}=Name  {y}=Year  {s00e00}=S01E01  {t}=EpTitle", text_color="gray", font=("Arial", 11))
        lbl_legend.grid(row=1, column=0, columnspan=6, pady=(0, 10))

        # --- BROWSE / SCAN ---
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(ctrl_frame, text="Select Folder", command=self.select_folder, width=140).pack(side="left")
        self.lbl_path = ctk.CTkLabel(ctrl_frame, text="No folder selected", text_color="silver")
        self.lbl_path.pack(side="left", padx=15)
        
        self.btn_scan = ctk.CTkButton(ctrl_frame, text="MATCH FILES", command=self.start_scan, state="disabled", fg_color="#7209B7")
        self.btn_scan.pack(side="right")

        # --- PROGRESS ---
        self.progress = ctk.CTkProgressBar(self, height=8, progress_color="#4CC9F0")
        self.progress.pack(fill="x", padx=20, pady=5)
        self.progress.set(0)
        self.progress.pack_forget()

        # --- LIST AREA ---
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Files")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # --- FOOTER ---
        footer = ctk.CTkFrame(self, height=60, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=10)
        
        self.lbl_status = ctk.CTkLabel(footer, text="Ready", text_color="gray")
        self.lbl_status.pack(side="left")
        
        self.btn_rename = ctk.CTkButton(footer, text="RENAME ALL", command=self.rename_thread, state="disabled", fg_color="#E63946")
        self.btn_rename.pack(side="right")

    def apply_preset(self, choice):
        if choice == "Plex {plex}":
            self.ent_fmt_movie.delete(0, 'end'); self.ent_fmt_movie.insert(0, "{n} ({y})")
            self.ent_fmt_tv.delete(0, 'end'); self.ent_fmt_tv.insert(0, "{n} ({y}) - {s00e00} - {t}")
        elif choice == "Kodi":
            self.ent_fmt_movie.delete(0, 'end'); self.ent_fmt_movie.insert(0, "{n} ({y})")
            self.ent_fmt_tv.delete(0, 'end'); self.ent_fmt_tv.insert(0, "{n} - {s00e00} - {t}")
        elif choice == "Simple":
            self.ent_fmt_movie.delete(0, 'end'); self.ent_fmt_movie.insert(0, "{n}")
            self.ent_fmt_tv.delete(0, 'end'); self.ent_fmt_tv.insert(0, "{s00e00} - {t}")
        elif choice == "Scene":
            self.ent_fmt_movie.delete(0, 'end'); self.ent_fmt_movie.insert(0, "{n}.{y}")
            self.ent_fmt_tv.delete(0, 'end'); self.ent_fmt_tv.insert(0, "{n}.{s00e00}.{t}")

    def select_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.lbl_path.configure(text=d)
            for widget in self.scroll.winfo_children(): widget.destroy()
            self.file_rows = []
            
            # Simple recursive find
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(VIDEO_EXTENSIONS):
                        path = os.path.join(root, f)
                        self.create_row(f, path)
            
            self.btn_scan.configure(state="normal")
            self.lbl_status.configure(text=f"Loaded {len(self.file_rows)} files.")

    def create_row(self, filename, path):
        fr = ctk.CTkFrame(self.scroll, height=40)
        fr.pack(fill="x", padx=5, pady=2)
        fr.grid_columnconfigure(1, weight=1)
        
        # Status color bar
        bar = ctk.CTkLabel(fr, text="", width=6, fg_color="gray", corner_radius=0)
        bar.grid(row=0, column=0, sticky="ns", padx=(0,5))
        
        # Old Name
        lbl_old = ctk.CTkLabel(fr, text=filename, anchor="w")
        lbl_old.grid(row=0, column=1, sticky="ew")
        
        # Arrow
        ctk.CTkLabel(fr, text="➜", text_color="gray").grid(row=0, column=2, padx=10)
        
        # New Name
        lbl_new = ctk.CTkLabel(fr, text="...", anchor="w", text_color="gray")
        lbl_new.grid(row=0, column=3, sticky="ew", padx=(0, 10))
        fr.grid_columnconfigure(3, weight=1)
        
        self.file_rows.append({
            'fr': fr, 'bar': bar, 'lbl_new': lbl_new, 
            'path': path, 'name': filename, 'new_name': None
        })

    def start_scan(self):
        self.btn_scan.configure(state="disabled")
        self.progress.pack(fill="x", padx=20, pady=5)
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        api = self.ent_api.get().strip()
        backend = TMDbBackend(api)
        fmt_mov = self.ent_fmt_movie.get()
        fmt_tv = self.ent_fmt_tv.get()
        
        total = len(self.file_rows)
        matches = 0

        for i, row in enumerate(self.file_rows):
            new_name, msg = backend.search(row['name'], fmt_mov, fmt_tv)
            
            # Update UI safely
            self.after(0, lambda r=row, n=new_name, m=msg: self.update_row(r, n, m))
            self.after(0, lambda v=(i+1)/total: self.progress.set(v))
            
            if new_name: matches += 1
        
        self.after(0, lambda: self.finish_scan(matches))

    def update_row(self, row, new_name, msg):
        if new_name:
            ext = os.path.splitext(row['name'])[1]
            full_new = new_name + ext
            row['new_name'] = full_new
            row['lbl_new'].configure(text=full_new, text_color="#4CC9F0")
            row['bar'].configure(fg_color="#06D6A0") # Green
        else:
            row['lbl_new'].configure(text=msg, text_color="#EF476F")
            row['bar'].configure(fg_color="#EF476F") # Red

    def finish_scan(self, matches):
        self.progress.pack_forget()
        self.btn_scan.configure(state="normal")
        self.lbl_status.configure(text=f"Scan complete. {matches} matches found.")
        if matches > 0:
            self.btn_rename.configure(state="normal")

    def rename_thread(self):
        if not messagebox.askyesno("Rename", "Rename matched files now?"): return
        self.btn_rename.configure(state="disabled")
        threading.Thread(target=self.run_rename, daemon=True).start()

    def run_rename(self):
        count = 0
        for row in self.file_rows:
            if row['new_name'] and row['new_name'] != row['name']:
                try:
                    folder = os.path.dirname(row['path'])
                    new_path = os.path.join(folder, row['new_name'])
                    os.rename(row['path'], new_path)
                    
                    self.after(0, lambda r=row: r['bar'].configure(fg_color="#FFD166")) # Gold
                    self.after(0, lambda r=row: r['lbl_new'].configure(text="RENAMED", text_color="#FFD166"))
                    count += 1
                except Exception as e:
                    print(e)
        
        self.after(0, lambda: self.lbl_status.configure(text=f"Finished. Renamed {count} files."))

if __name__ == "__main__":
    app = App()
    app.mainloop()
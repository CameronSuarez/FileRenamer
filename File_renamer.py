import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import re
from pathlib import Path
from datetime import datetime
import csv
import sys

# ---- PyInstaller helper (optional) ----
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---- Optional Drag & Drop support ----
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    dnd_available = True
    BaseClass = TkinterDnD.Tk
except ImportError:
    dnd_available = False
    BaseClass = tk.Tk


class BulkFileRenamer(BaseClass):
    def __init__(self):
        super().__init__()
        self.title("Bulk File Renamer")
        self.geometry("900x650")

        # Data
        self.folder_path = None
        self.file_list = []
        self.preview_data = {}

        # Case transforms
        self.case_transform_map = {
            "None": lambda s: s,
            "lower": lambda s: s.lower(),
            "UPPER": lambda s: s.upper(),
            "Title": lambda s: s.title(),
        }

        self.create_widgets()
        self.update_ui_state()

    # ---------- UI ----------
    def create_widgets(self):
        # Top: folder selection
        top = tk.Frame(self, padx=10, pady=8)
        top.pack(fill=tk.X)
        tk.Label(top, text="Folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar()
        self.folder_entry = tk.Entry(top, textvariable=self.folder_var, state="readonly")
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.browse_btn = tk.Button(top, text="Browse", command=self.browse_folder)
        self.browse_btn.pack(side=tk.LEFT)

        if dnd_available:
            self.folder_entry.drop_target_register(DND_FILES)
            self.folder_entry.dnd_bind("<<Drop>>", self.on_drop)

        # Middle: options + actions
        mid = tk.Frame(self, padx=10, pady=6)
        mid.pack(fill=tk.X)

        # Notebook with two modes
        self.notebook = ttk.Notebook(mid)
        self.notebook.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Parts mode tab ---
        parts_tab = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(parts_tab, text="Build from parts")

        # Row 1: Prefix / Suffix
        r1 = tk.Frame(parts_tab)
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="Prefix:").pack(side=tk.LEFT)
        self.prefix_var = tk.StringVar()
        tk.Entry(r1, textvariable=self.prefix_var, width=18).pack(side=tk.LEFT, padx=6)

        tk.Label(r1, text="Suffix:").pack(side=tk.LEFT)
        self.suffix_var = tk.StringVar()
        tk.Entry(r1, textvariable=self.suffix_var, width=18).pack(side=tk.LEFT, padx=6)

        # Row 2: Find/Replace + Regex
        r2 = tk.Frame(parts_tab)
        r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="Find:").pack(side=tk.LEFT)
        self.find_var = tk.StringVar()
        tk.Entry(r2, textvariable=self.find_var, width=18).pack(side=tk.LEFT, padx=6)

        tk.Label(r2, text="Replace:").pack(side=tk.LEFT)
        self.replace_var = tk.StringVar()
        tk.Entry(r2, textvariable=self.replace_var, width=18).pack(side=tk.LEFT, padx=6)

        self.regex_var = tk.BooleanVar(value=False)
        tk.Checkbutton(r2, text="Regex", variable=self.regex_var).pack(side=tk.LEFT, padx=6)

        # Row 3: Numbering {n}, start & padding
        r3 = tk.Frame(parts_tab)
        r3.pack(fill=tk.X, pady=3)
        tk.Label(r3, text="Start #:").pack(side=tk.LEFT)
        self.start_num_var = tk.IntVar(value=1)
        tk.Spinbox(r3, from_=0, to=1_000_000, textvariable=self.start_num_var, width=8).pack(side=tk.LEFT, padx=6)

        tk.Label(r3, text="Padding:").pack(side=tk.LEFT)
        self.padding_var = tk.IntVar(value=2)
        tk.Spinbox(r3, from_=0, to=10, textvariable=self.padding_var, width=5).pack(side=tk.LEFT, padx=6)

        tk.Label(r3, text="Case:").pack(side=tk.LEFT)
        self.case_var = tk.StringVar(value="None")
        ttk.Combobox(r3, state="readonly", width=10, textvariable=self.case_var,
                     values=list(self.case_transform_map.keys())).pack(side=tk.LEFT, padx=6)

        self.remove_spaces_var = tk.BooleanVar(value=False)
        tk.Checkbutton(r3, text="Remove spaces", variable=self.remove_spaces_var).pack(side=tk.LEFT, padx=6)

        self.keep_ext_var = tk.BooleanVar(value=True)
        tk.Checkbutton(r3, text="Keep extension", variable=self.keep_ext_var).pack(side=tk.LEFT, padx=6)

        # Hint
        tk.Label(parts_tab, fg="#666",
                 text="Tip: use {n} anywhere in Prefix/Suffix to insert numbering. Example: prefix='IMG_{n}_'").pack(anchor="w", pady=(6, 0))

        # --- Pattern mode tab ---
        pattern_tab = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(pattern_tab, text="Pattern")

        r1p = tk.Frame(pattern_tab)
        r1p.pack(fill=tk.X, pady=3)
        tk.Label(r1p, text="Pattern:").pack(side=tk.LEFT)
        self.pattern_var = tk.StringVar(value="{stem}_{n}")
        tk.Entry(r1p, textvariable=self.pattern_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        r2p = tk.Frame(pattern_tab)
        r2p.pack(fill=tk.X, pady=3)
        tk.Label(r2p, text="Start #:").pack(side=tk.LEFT)
        self.pattern_start_num_var = tk.IntVar(value=1)
        tk.Spinbox(r2p, from_=0, to=1_000_000, textvariable=self.pattern_start_num_var, width=8).pack(side=tk.LEFT, padx=6)

        tk.Label(r2p, text="Padding:").pack(side=tk.LEFT)
        self.pattern_padding_var = tk.IntVar(value=2)
        tk.Spinbox(r2p, from_=0, to=10, textvariable=self.pattern_padding_var, width=5).pack(side=tk.LEFT, padx=6)

        tk.Label(r2p, text="Case:").pack(side=tk.LEFT)
        self.pattern_case_var = tk.StringVar(value="None")
        ttk.Combobox(r2p, state="readonly", width=10, textvariable=self.pattern_case_var,
                     values=list(self.case_transform_map.keys())).pack(side=tk.LEFT, padx=6)

        self.pattern_remove_spaces_var = tk.BooleanVar(value=False)
        tk.Checkbutton(r2p, text="Remove spaces", variable=self.pattern_remove_spaces_var).pack(side=tk.LEFT, padx=6)

        self.auto_append_ext_var = tk.BooleanVar(value=True)
        tk.Checkbutton(r2p, text="Auto-append ext if {ext} missing", variable=self.auto_append_ext_var).pack(side=tk.LEFT, padx=6)

        # Pattern help
        help_txt = (
            "Placeholders: {n}, {stem}, {ext}, {parent}, {yyyy}, {mm}, {dd}, {hh}, {mi}, {ss}\n"
            "Example: '{parent}_{yyyy}-{mm}-{dd}_{stem}_{n}'"
        )
        tk.Label(pattern_tab, text=help_txt, fg="#666", justify="left").pack(anchor="w", pady=(6, 0))

        # Actions (right side)
        actions = tk.Frame(mid, padx=10)
        actions.pack(side=tk.RIGHT, anchor="n")
        self.preview_btn = tk.Button(actions, text="Preview", width=14, command=self.preview_rename)
        self.preview_btn.pack(pady=4)
        self.rename_btn = tk.Button(actions, text="Rename", width=14, command=self.perform_rename)
        self.rename_btn.pack(pady=4)
        self.undo_btn = tk.Button(actions, text="Undo (last)", width=14, command=self.undo_rename)
        self.undo_btn.pack(pady=4)

        # Treeview for preview/results
        tv_frame = tk.Frame(self, padx=10, pady=8)
        tv_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("old", "new", "status")
        self.tree = ttk.Treeview(tv_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("old", text="Old Name")
        self.tree.heading("new", text="New Name")
        self.tree.heading("status", text="Status")
        self.tree.column("old", width=360, anchor="w")
        self.tree.column("new", width=360, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tv_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tv_frame.grid_rowconfigure(0, weight=1)
        tv_frame.grid_columnconfigure(0, weight=1)

    # ---------- Folder handling ----------
    def on_drop(self, event):
        folder_path_str = event.data.strip("{}")
        if os.path.isdir(folder_path_str):
            self.set_folder(Path(folder_path_str))
        else:
            messagebox.showwarning("Invalid Drop", "Please drop a folder, not a file.")

    def browse_folder(self):
        folder_path_str = filedialog.askdirectory()
        if folder_path_str:
            self.set_folder(Path(folder_path_str))

    def set_folder(self, folder_path: Path):
        self.folder_path = folder_path
        self.folder_var.set(str(folder_path))
        self.file_list = self.get_files_in_folder()
        self.update_preview_table()
        self.update_ui_state()

    def get_files_in_folder(self):
        if not self.folder_path:
            return []
        files = [p for p in self.folder_path.iterdir() if p.is_file()]

        def natural_sort_key(p: Path):
            return [int(t) if t.isdigit() else t.lower() for t in re.split(r"([0-9]+)", p.name)]

        files.sort(key=natural_sort_key)
        return files

    def update_ui_state(self):
        has_folder = self.folder_path is not None and bool(self.file_list)
        self.preview_btn.config(state=tk.NORMAL if has_folder else tk.DISABLED)
        self.rename_btn.config(state=tk.DISABLED)  # only enabled after preview
        log_files = sorted(self.folder_path.glob("rename_log_*.csv")) if self.folder_path else []
        self.undo_btn.config(state=tk.NORMAL if log_files else tk.DISABLED)

    # ---------- Preview / Rename / Undo ----------
    def update_preview_table(self, new_names=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.file_list:
            return

        if new_names is None:
            self.rename_btn.config(state=tk.DISABLED)
            for path in self.file_list:
                self.tree.insert("", "end", values=(path.name, "", ""))
            return

        self.rename_btn.config(state=tk.NORMAL)
        for old_path, new_name in zip(self.file_list, new_names):
            new_path = old_path.parent / new_name
            if new_path == old_path:
                status = "No Change"
            elif new_path.exists():
                status = "Collision"
            else:
                status = "Ready"
            self.tree.insert("", "end", values=(old_path.name, new_name, status))

    def preview_rename(self):
        if not self.file_list:
            messagebox.showinfo("Info", "Please select a folder with files first.")
            return

        is_parts_mode = self.notebook.tab(self.notebook.select(), "text") == "Build from parts"
        start_num = self.start_num_var.get() if is_parts_mode else self.pattern_start_num_var.get()
        padding = self.padding_var.get() if is_parts_mode else self.pattern_padding_var.get()

        new_names = []
        for i, old_path in enumerate(self.file_list):
            try:
                file_stem = old_path.stem
                file_ext = old_path.suffix
                if is_parts_mode:
                    new_stem = file_stem

                    # find/replace
                    find_text = self.find_var.get()
                    replace_text = self.replace_var.get()
                    if find_text:
                        if self.regex_var.get():
                            new_stem = re.sub(find_text, replace_text, new_stem)
                        else:
                            new_stem = new_stem.replace(find_text, replace_text)

                    prefix = self.prefix_var.get()
                    suffix = self.suffix_var.get()
                    new_name = f"{prefix}{new_stem}{suffix}"

                    if "{n}" in new_name:
                        num_str = str(start_num + i).zfill(padding)
                        new_name = new_name.replace("{n}", num_str)

                    case_func = self.case_transform_map[self.case_var.get()]
                    if self.remove_spaces_var.get():
                        new_name = new_name.replace(" ", "")
                    new_name = case_func(new_name)

                    if self.keep_ext_var.get():
                        new_name += file_ext

                else:
                    pattern = self.pattern_var.get().strip()
                    if not pattern:
                        messagebox.showerror("Error", "Pattern cannot be empty in Pattern mode.")
                        return

                    now = datetime.now()
                    placeholders = {
                        "{n}": str(start_num + i).zfill(padding),
                        "{stem}": file_stem,
                        "{ext}": file_ext,
                        "{parent}": old_path.parent.name,
                        "{yyyy}": now.strftime("%Y"),
                        "{mm}": now.strftime("%m"),
                        "{dd}": now.strftime("%d"),
                        "{hh}": now.strftime("%H"),
                        "{mi}": now.strftime("%M"),
                        "{ss}": now.strftime("%S"),
                    }

                    new_name = pattern
                    for ph, val in placeholders.items():
                        new_name = new_name.replace(ph, val)

                    case_func = self.case_transform_map[self.pattern_case_var.get()]
                    if self.pattern_remove_spaces_var.get():
                        new_name = new_name.replace(" ", "")
                    new_name = case_func(new_name)

                    if self.auto_append_ext_var.get() and file_ext and "{ext}" not in pattern:
                        new_name += file_ext

                new_names.append(new_name)

            except Exception as e:
                messagebox.showerror("Error", f"Could not process file {old_path.name}: {e}")
                self.update_preview_table()
                return

        # collision-proofing against existing files
        final_names = []
        name_counts = {}
        for name in new_names:
            base, ext = os.path.splitext(name)
            candidate = name
            count = 0
            while (self.folder_path / candidate).exists():
                count = name_counts.get(name, 0) + 1
                candidate = f"{base}__{count}{ext}"
                name_counts[name] = count
            final_names.append(candidate)

        self.preview_data = dict(zip(self.file_list, final_names))
        self.update_preview_table(final_names)

    def perform_rename(self):
        if not self.preview_data:
            messagebox.showinfo("Info", "Please run 'Preview' first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Rename",
            "Are you sure you want to rename these files?\nUse Undo to revert using the log."
        )
        if not confirm:
            return

        log_path = self.folder_path / f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        renamed_count = 0

        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Old Path", "New Path"])
            for old_path, new_name in self.preview_data.items():
                new_path = old_path.parent / new_name
                try:
                    if old_path != new_path and not new_path.exists():
                        os.rename(old_path, new_path)
                        writer.writerow([old_path.name, new_path.name])
                        renamed_count += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename {old_path.name}: {e}")

        self.set_folder(self.folder_path)
        messagebox.showinfo("Success", f"Renamed {renamed_count} of {len(self.preview_data)} files.\nLog: {log_path.name}")

    def undo_rename(self):
        if not self.folder_path:
            messagebox.showinfo("Info", "No folder is selected.")
            return

        log_files = sorted(self.folder_path.glob("rename_log_*.csv"))
        if not log_files:
            messagebox.showinfo("Info", "No undo log files found in this folder.")
            return

        last_log = log_files[-1]
        if not messagebox.askyesno("Confirm Undo", f"Undo changes from '{last_log.name}'?"):
            return

        undo_pairs = []
        try:
            with open(last_log, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) == 2:
                        new_path = self.folder_path / row[1]
                        old_path = self.folder_path / row[0]
                        undo_pairs.append((new_path, old_path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read log file {last_log.name}: {e}")
            return

        undone = 0
        for new_path, old_path in reversed(undo_pairs):
            if new_path.exists() and not old_path.exists():
                try:
                    os.rename(new_path, old_path)
                    undone += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to undo rename for {new_path.name}: {e}")

        # Refresh and clean up
        self.set_folder(self.folder_path)
        messagebox.showinfo("Undo Complete", f"Successfully undid {undone} renames.")
        try:
            os.remove(last_log)
        except Exception:
            pass


if __name__ == "__main__":
    app = BulkFileRenamer()
    app.mainloop()

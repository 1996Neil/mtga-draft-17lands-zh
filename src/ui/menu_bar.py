from src.i18n import tr
"""
src/ui/menu_bar.py
Handles the generation of the native OS Menu bar (File, Tools, Theme)
and encapsulates the associated file dialogs and export logic.
"""

import tkinter
import os
import webbrowser
from tkinter import filedialog, messagebox
from src import constants
from src.ui.styles import Theme
from src.configuration import write_configuration
from src.ui.windows.practice_dialog import PracticeDialog


class AppMenuBar:
    def __init__(self, root, app_context):
        self.root = root
        self.app_context = app_context
        self.config = app_context.configuration
        self._setup_menu()

    def notify_app_update(self, version):
        """Offer the official release page once per version, on the UI thread."""
        if getattr(self, "_notified_version", None) == version:
            return
        self._notified_version = version
        if messagebox.askyesno(
            tr("Application Update"),
            tr(f"MTGA Draft Tool {version} is available. Open the release page?"),
            parent=self.root,
        ):
            webbrowser.open("https://github.com/unrealities/MTGA_Draft_17Lands/releases/latest")

    def _setup_menu(self):
        m = tkinter.Menu(self.root)
        self.root.config(menu=m)

        # --- FILE MENU ---
        file_m = tkinter.Menu(m, tearoff=0)
        m.add_cascade(label=tr("File"), menu=file_m)
        file_m.add_command(
            label=tr("Preferences..."), command=self.app_context._open_settings
        )
        file_m.add_separator()
        file_m.add_command(label=tr("Read Draft Log..."), command=self._read_draft_log)
        file_m.add_command(label=tr("Read Player.log..."), command=self._read_player_log)
        file_m.add_command(
            label=tr("Locate MTGA Data Folder..."), command=self._locate_mtga_data
        )
        file_m.add_separator()
        file_m.add_command(label=tr("Export Draft (CSV)"), command=self._export_csv)
        file_m.add_command(label=tr("Export Draft (JSON)"), command=self._export_json)
        file_m.add_separator()
        file_m.add_command(label=tr("Exit"), command=self.app_context._on_close)

        file_m.add_separator()
        file_m.add_checkbutton(label=tr("Simplified Chinese display"),
                              variable=self.app_context.vars["chinese_enabled"],
                              command=lambda: self.app_context._apply_language(
                                  bool(self.app_context.vars["chinese_enabled"].get())))
        file_m.add_command(label=tr("Reload Chinese Names"),
                           command=lambda: self.app_context.controller.sync_display(force=True))

        # --- TOOLS MENU ---
        tools_m = tkinter.Menu(m, tearoff=0)
        m.add_cascade(label=tr("Tools"), menu=tools_m)
        tools_m.add_command(
            label=tr("Practice: Generate Random Sealed Pool"),
            command=lambda: PracticeDialog(
                self.root, self.app_context, is_import=False
            ),
        )
        tools_m.add_command(
            label=tr("Practice: Import Sealed Pool from Clipboard"),
            command=lambda: PracticeDialog(self.root, self.app_context, is_import=True),
        )

        # --- THEME MENU ---
        theme_m = tkinter.Menu(m, tearoff=0)
        m.add_cascade(label=tr("Theme"), menu=theme_m)
        theme_m.add_command(
            label=tr("System (Native)"),
            command=lambda: self._update_theme(new_palette="System"),
        )
        theme_m.add_separator()

        for name in Theme.THEME_MAPPING.keys():
            if name == "System":
                continue
            theme_m.add_command(
                label=tr(f"Mana Flair: {name}"),
                command=lambda n=name: self._update_theme(new_palette=n),
            )

        custom_m = tkinter.Menu(theme_m, tearoff=0)
        theme_m.add_cascade(label=tr("Custom Themes (.tcl)"), menu=custom_m)
        custom_m.add_command(
            label=tr("Browse for .tcl..."), command=self._browse_custom_tcl
        )

        for name, path in Theme.discover_custom_themes().items():
            custom_m.add_command(
                label=tr(name), command=lambda p=path: self._update_theme(new_custom=p)
            )

    def _update_theme(self, new_engine=None, new_palette=None, new_custom=None):
        s = self.config.settings
        if new_engine:
            s.theme_base = new_engine
        if new_palette:
            s.theme = new_palette
        if new_custom:
            s.theme_custom_path = new_custom
        else:
            s.theme_custom_path = ""

        write_configuration(self.config)
        current_scale = constants.UI_SIZE_DICT.get(s.ui_size, 1.0)
        Theme.apply(
            self.root,
            palette=s.theme,
            engine=getattr(s, "theme_base", "clam"),
            custom_path=s.theme_custom_path,
            scale=current_scale,
        )

    def _browse_custom_tcl(self):
        f = filedialog.askopenfilename(
            filetypes=(("Tcl files", "*.tcl"), ("All", "*.*"))
        )
        if f:
            self._update_theme(new_custom=f)

    def _read_draft_log(self):
        f = filedialog.askopenfilename(filetypes=(("Log", "*.log"), ("All", "*.*")))
        if f:
            if hasattr(self.app_context, "loading_overlay"):
                self.app_context.loading_overlay.show("Loading Draft Log")
                self.app_context.loading_overlay.update_status("Queuing file...")
            self.app_context.orchestrator.set_file_and_scan(f)

    def _read_player_log(self):
        f = filedialog.askopenfilename(filetypes=(("Log", "*.log"), ("All", "*.*")))
        if f:
            if hasattr(self.app_context, "loading_overlay"):
                self.app_context.loading_overlay.show("Loading Player.log")
                self.app_context.loading_overlay.update_status("Queuing file...")
            self.app_context.orchestrator.set_file_and_scan(f)

    def _locate_mtga_data(self):
        folder = filedialog.askdirectory(title=tr("Select MTGA_Data Folder"))
        if folder:
            if not folder.endswith("MTGA_Data"):
                if os.path.exists(os.path.join(folder, "MTGA_Data")):
                    folder = os.path.join(folder, "MTGA_Data")

            if os.path.exists(os.path.join(folder, "Downloads", "Raw")):
                self.config.settings.database_location = folder
                write_configuration(self.config)

                if (
                    hasattr(self.app_context, "orchestrator")
                    and self.app_context.orchestrator.scanner
                    and self.app_context.orchestrator.scanner.set_data
                ):
                    self.app_context.orchestrator.scanner.set_data.db_path = folder
                    self.app_context.orchestrator.scanner.set_data.unknown_id_cache.clear()
                    self.app_context.orchestrator.request_math_update()
                    self.app_context._refresh_ui_data()

                messagebox.showinfo(
                    tr("Success"),
                    tr(f"MTGA Data Folder successfully set to:\n{folder}\n\nYou can now download datasets!"),
                )
            else:
                messagebox.showerror(
                    tr("Error"),
                    tr("Could not find 'Downloads/Raw' in the selected folder.\n\nPlease select the valid MTGA_Data folder."),
                )

    def _export_csv(self):
        h = self.app_context.orchestrator.scanner.retrieve_draft_history()
        if not h:
            return
        from src.card_logic import export_draft_to_csv

        data = export_draft_to_csv(
            h,
            self.app_context.orchestrator.scanner.set_data,
            self.app_context.orchestrator.scanner.picked_cards,
        )
        f = filedialog.asksaveasfile(mode="w", defaultextension=".csv")
        if f:
            with f:
                f.write(data)
            messagebox.showinfo(tr("Success"), tr("Export Complete."))

    def _export_json(self):
        h = self.app_context.orchestrator.scanner.retrieve_draft_history()
        if not h:
            return
        from src.card_logic import export_draft_to_json

        data = export_draft_to_json(
            h,
            self.app_context.orchestrator.scanner.set_data,
            self.app_context.orchestrator.scanner.picked_cards,
        )
        f = filedialog.asksaveasfile(mode="w", defaultextension=".json")
        if f:
            with f:
                f.write(data)
            messagebox.showinfo(tr("Success"), tr("Export Complete."))

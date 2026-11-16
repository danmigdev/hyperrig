"""English desktop installation UI; opening it performs no device operations."""
from __future__ import annotations

import ctypes
from datetime import datetime
from functools import partial
import http.server
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import uuid
import webbrowser

from .core import load_release
from .service import InstallWorkflow, interrupted_stock_entry


class EditorServer:
    def __init__(self, bundle):
        folder = Path(bundle) / "editor" / "web"
        if not (folder / "tankmini.html").is_file():
            raise ValueError("The editor is missing from this package")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                # The derived editor's local diagnostic endpoint discards data.
                length = int(self.headers.get("Content-Length", "0"))
                if self.path != "/log" or not 0 <= length <= 1024 * 1024:
                    self.send_error(400)
                    return
                self.rfile.read(length)
                self.send_response(204)
                self.end_headers()

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(folder)))
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/tankmini.html"

    def open(self):
        # Prefer a browser that implements Web Serial, without changing defaults.
        candidates = [Path(os.environ.get(key, "")) / "Microsoft/Edge/Application/msedge.exe"
                      for key in ("ProgramFiles(x86)", "ProgramFiles")]
        edge = next((path for path in candidates if path.is_file()), None)
        if edge is not None:
            subprocess.Popen([str(edge), self.url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            webbrowser.open(self.url)

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def elevate(bundle, backup_directory):
    """Request ordinary Windows elevation once; never change UAC settings."""
    if getattr(sys, "frozen", False):
        executable = sys.executable
        arguments = ["--bundle", str(bundle), "--admin", "--backup-directory", str(backup_directory)]
    else:
        executable = str(Path(sys.executable).with_name("pythonw.exe"))
        if not Path(executable).is_file():
            executable = sys.executable
        launcher = Path(__file__).resolve().parents[2] / "tools" / "launch_mini_installer.py"
        arguments = [str(launcher), "--bundle", str(bundle), "--admin",
                     "--backup-directory", str(backup_directory)]
    shell = ctypes.windll.shell32.ShellExecuteW
    shell.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                      ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
    shell.restype = ctypes.c_void_p
    result = shell(None, "runas", executable, subprocess.list2cmdline(arguments), str(bundle), 0)
    if not result or result <= 32:
        raise OSError("Windows did not grant administrator access. No installation was started.")


class InstallerWindow:
    def __init__(self, bundle, *, backup_directory=None, smoke=False):
        import tkinter as tk
        from tkinter import ttk
        from . import windows
        self.tk, self.ttk, self.windows = tk, ttk, windows
        self.bundle = Path(bundle).resolve()
        self.release = load_release(self.bundle)
        self.smoke = smoke
        self.root = tk.Tk()
        self.root.title("HyperRig MINI Installer")
        self.root.geometry("820x700")
        self.root.minsize(760, 650)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.events = queue.Queue()
        self.workflow = self.editor = None
        self.busy = False
        self.inventory = None
        default_backups = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "HyperRig" / "Backups"
        self.backup_directory = Path(backup_directory or default_backups).resolve()
        self.status = tk.StringVar(value="No device has been accessed. Connect one stock TANK MINI to begin.")
        self.details = tk.StringVar(value="")
        self.backup_label = tk.StringVar(value=str(self.backup_directory))
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="HyperRig MINI Installer", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Developer preview | Stock M-VAVE TANK MINI to HyperRig",
                  font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 12))
        ttk.Label(outer, text="This package has not yet been tested on a fresh stock pedal. Recovery after an\n"
                             "interrupted installation is not verified. Keep power and USB connected.",
                  wraplength=750, foreground="#8a3b12").pack(anchor="w", pady=(0, 14))
        self.access = ttk.Button(outer, text="Enable installation (Windows UAC)", command=self.request_admin)
        self.access.pack(anchor="w", pady=(0, 12))
        if windows.is_admin():
            self.access.configure(text="Administrator access enabled", state="disabled")
        selection = ttk.LabelFrame(outer, text="1. Select the stock MINI", padding=10)
        selection.pack(fill="x")
        self.scan_button = ttk.Button(selection, text="Find connected devices", command=self.find_devices)
        self.scan_button.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(selection, text="MIDI input").grid(row=1, column=0, sticky="w", padx=(0, 12))
        ttk.Label(selection, text="MIDI output").grid(row=2, column=0, sticky="w", padx=(0, 12))
        self.midi_in = ttk.Combobox(selection, state="readonly", width=68)
        self.midi_out = ttk.Combobox(selection, state="readonly", width=68)
        self.midi_in.grid(row=1, column=1, sticky="ew", pady=3)
        self.midi_out.grid(row=2, column=1, sticky="ew", pady=3)
        selection.columnconfigure(1, weight=1)
        backup = ttk.LabelFrame(outer, text="2. Back up this pedal", padding=10)
        backup.pack(fill="x", pady=12)
        ttk.Label(backup, textvariable=self.backup_label, wraplength=580).grid(row=0, column=0, sticky="w")
        self.folder_button = ttk.Button(backup, text="Choose folder", command=self.choose_folder)
        self.folder_button.grid(row=0, column=1, padx=(12, 0))
        self.backup_button = ttk.Button(backup, text="Create and verify backup", command=self.backup, state="disabled")
        self.backup_button.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.continue_button = ttk.Button(backup, text="Continue backup after USB recovery", command=self.continue_backup)
        self.continue_button.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 10))
        self.install_button = ttk.Button(actions, text="3. Install HyperRig", command=self.install, state="disabled")
        self.install_button.pack(side="left")
        self.boot_button = ttk.Button(actions, text="4. Boot HyperRig", command=self.boot, state="disabled")
        self.boot_button.pack(side="left", padx=8)
        self.cancel_button = ttk.Button(actions, text="Return to stock", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left")
        self.progress = ttk.Progressbar(outer, maximum=100)
        self.progress.pack(fill="x", pady=6)
        ttk.Label(outer, textvariable=self.status, wraplength=750).pack(anchor="w", pady=6)
        ttk.Label(outer, textvariable=self.details, wraplength=750, foreground="#555555").pack(anchor="w", pady=4)
        footer = ttk.Frame(outer)
        footer.pack(side="bottom", fill="x", pady=(12, 0))
        self.editor_button = ttk.Button(footer, text="Open HyperRig editor", command=self.open_editor)
        self.editor_button.pack(side="left")
        ttk.Button(footer, text="Report an issue on GitHub", command=self.report).pack(side="right")
        self.root.after(100, self.poll)
        if smoke:
            for button in (self.access, self.scan_button, self.backup_button, self.continue_button, self.editor_button):
                button.configure(state="disabled")

    def error(self, message):
        from tkinter import messagebox
        messagebox.showerror("HyperRig", str(message), parent=self.root)

    def request_admin(self):
        if self.smoke or self.busy or self.workflow:
            return
        try:
            elevate(self.bundle, self.backup_directory)
        except Exception as error:
            self.error(error)
            return
        self.close()

    def choose_folder(self):
        from tkinter import filedialog
        if self.busy or self.workflow:
            return
        selected = filedialog.askdirectory(title="Choose a private local backup folder", parent=self.root)
        if selected:
            self.backup_directory = Path(selected).resolve()
            self.backup_label.set(str(self.backup_directory))

    def run(self, action, fn):
        if self.smoke or self.busy:
            return
        self.busy = True
        self.refresh_buttons()

        def worker():
            try:
                result = fn()
                self.events.put({"action": action, "result": result})
            except Exception as error:
                self.events.put({"action": action, "error": str(error)})
        threading.Thread(target=worker, daemon=False).start()

    def find_devices(self):
        self.status.set("Looking for the stock MINI and available MIDI ports")
        self.run("scan", self.windows.scan)

    def backup(self):
        if not self.windows.is_admin():
            self.error("Enable installation through Windows UAC first.")
            return
        incoming, outgoing = self.midi_in.current(), self.midi_out.current()
        if self.inventory is None or incoming < 0 or outgoing < 0:
            self.error("Select the MIDI input and output belonging to the MINI.")
            return
        selection = {"input_index": incoming, "output_index": outgoing,
                     "input_name": self.inventory["inputs"][incoming],
                     "output_name": self.inventory["outputs"][outgoing]}
        destination = self.backup_directory / (datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])

        def begin():
            self.workflow = InstallWorkflow(self.release, self.windows.WindowsBackend(), destination,
                                            notify=self.events.put)
            return self.workflow.backup(selection)
        self.details.set("The MINI will temporarily leave normal operation. Backups stay on this PC.")
        self.run("backup", begin)

    def install(self):
        from tkinter import messagebox
        if self.workflow is None or self.workflow.phase != "backed_up" or self.busy:
            return
        if messagebox.askyesno("Install HyperRig", "Replace the stock application with HyperRig?\n\n"
                               "Two matching backups have been saved. Keep power and USB connected.\n"
                               "Recovery after an interrupted installation is not verified in this preview.",
                               parent=self.root, default="no"):
            self.run("install", self.workflow.install)

    def continue_backup(self):
        if not self.windows.is_admin():
            self.error("Enable installation through Windows UAC first.")
            return
        entries = []
        if self.workflow is not None:
            try:
                entries.append(interrupted_stock_entry(self.workflow.store.root))
            except (ValueError, OSError, KeyError, TypeError) as error:
                self.error(str(error))
                return
        elif self.backup_directory.is_dir():
            for folder in self.backup_directory.iterdir():
                if not folder.is_dir():
                    continue
                try:
                    entries.append(interrupted_stock_entry(folder))
                except (ValueError, OSError, KeyError, TypeError):
                    continue
        if not entries:
            self.error("No recent interrupted stock entry was found in this backup folder.")
            return
        source = max(entries, key=lambda entry: entry["submitted_unix"])["source_directory"]
        if self.workflow is not None:
            self.workflow.close()
            self.workflow = None
        destination = self.backup_directory / (datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])

        def begin():
            self.workflow = InstallWorkflow(self.release, self.windows.WindowsBackend(), destination,
                                            notify=self.events.put)
            return self.workflow.continue_backup(source)
        self.details.set("Continuing the previous backup in a new private session: " + source)
        self.run("backup", begin)

    def boot(self):
        self.run("boot", self.workflow.boot)

    def cancel(self):
        self.run("cancel", self.workflow.cancel_to_stock)

    def open_editor(self):
        if self.smoke or self.busy:
            return
        try:
            if self.editor is None:
                self.editor = EditorServer(self.bundle)
            self.editor.open()
            self.details.set("Keep this window open while using the editor. Select the MINI in its USB chooser.")
        except Exception as error:
            self.error(error)

    def report(self):
        if not self.smoke:
            webbrowser.open("https://github.com/danmigdev/hyperrig/issues/new/choose")

    def refresh_buttons(self):
        phase = self.workflow.phase if self.workflow else "created"
        idle = not self.busy and not self.smoke
        continuable = self.workflow is None
        if idle and phase == "failed":
            try:
                interrupted_stock_entry(self.workflow.store.root)
                continuable = True
            except (ValueError, OSError, KeyError, TypeError):
                pass
        for button, enabled in (
            (self.scan_button, phase == "created"), (self.folder_button, self.workflow is None),
            (self.backup_button, self.workflow is None and self.inventory is not None),
            (self.continue_button, continuable),
            (self.install_button, phase == "backed_up"), (self.cancel_button, phase == "backed_up"),
            (self.boot_button, phase == "verified"), (self.editor_button, phase in ("created", "usb_detected", "stock_usb_detected")),
        ):
            button.configure(state="normal" if idle and enabled else "disabled")
        for combo in (self.midi_in, self.midi_out):
            combo.configure(state="readonly" if idle and self.workflow is None else "disabled")

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if "action" in event:
                    self.busy = False
                    if "error" in event:
                        self.status.set("Stopped: " + event["error"])
                        if self.workflow:
                            self.details.set("Keep power and USB connected. Retain the private session folder: " + str(self.workflow.store.root))
                    elif event["action"] == "scan":
                        self.inventory = event["result"]
                        for combo, key in ((self.midi_in, "inputs"), (self.midi_out, "outputs")):
                            combo.configure(values=self.inventory[key])
                            if len(self.inventory[key]) == 1:
                                combo.current(0)
                        if len(self.inventory["stock_devices"]) == 1:
                            self.status.set("One stock USB device found. Select its MIDI input and output.")
                        elif self.inventory["hyperrig_ports"]:
                            self.status.set("HyperRig is already present. Use the editor; this installer starts from stock.")
                        else:
                            self.status.set("Connect exactly one stock MINI with a USB data cable.")
                    elif event["action"] == "backup":
                        self.details.set("Verified private backup: " + str(self.workflow.store.root))
                    self.refresh_buttons()
                elif "message" in event:
                    self.status.set(event["message"])
                elif "done" in event:
                    self.progress["value"] = 100 * event["done"] / max(1, event["total"])
                    self.details.set(f"{event['stage']}: {event['done']:,} / {event['total']:,}")
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        from tkinter import messagebox
        if self.busy:
            self.error("An operation is running. Keep this window, power, and USB connected.")
            return
        if self.workflow and self.workflow.phase in ("backed_up", "verified", "failed"):
            if not messagebox.askyesno("Close HyperRig installer", "The pedal has not returned to normal operation.\n"
                                      "Closing does not reset it or restore firmware. Close this window?",
                                      parent=self.root, default="no"):
                return
        try:
            if self.workflow:
                self.workflow.close()
            if self.editor:
                self.editor.close()
        except Exception as error:
            self.error(error)
            return
        self.root.destroy()

    def smoke_report(self, destination):
        self.root.update_idletasks()
        result = {"kind": "offline-installer-window-check", "device_io": False,
                  "window_title": self.root.title(), "language": "en",
                  "install_enabled_before_backup": str(self.install_button["state"]) != "disabled",
                  "boot_enabled_before_verification": str(self.boot_button["state"]) != "disabled"}
        with Path(destination).open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
        self.root.destroy()

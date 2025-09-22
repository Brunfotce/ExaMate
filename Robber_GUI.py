import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from queue import Queue
from Robber_logic import RobberLogic

class RobberGUI:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Robber - Exam Topics Scraper")
        self.top.geometry("800x600")

        self.robber_logic = RobberLogic()
        self.message_queue = Queue()
        self.worker_thread = None

        self.create_widgets()
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.process_queue()

    def create_widgets(self):
        # --- Main Frame ---
        main_frame = ttk.Frame(self.top, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Controls Frame ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=5)
        controls_frame.columnconfigure(1, weight=1)

        # --- Mode Selection ---
        self.mode = tk.StringVar(value="scan")
        ttk.Label(controls_frame, text="Mode:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        scan_radio = ttk.Radiobutton(controls_frame, text="Scan and save links", variable=self.mode, value="scan", command=self.toggle_controls)
        scan_radio.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        download_radio = ttk.Radiobutton(controls_frame, text="Download from links", variable=self.mode, value="download", command=self.toggle_controls)
        download_radio.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # --- Scan Controls ---
        self.scan_frame = ttk.Frame(controls_frame)
        self.scan_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.scan_frame, text="Start ID:").pack(side=tk.LEFT, padx=5)
        self.start_id_entry = ttk.Entry(self.scan_frame, width=10)
        self.start_id_entry.pack(side=tk.LEFT, padx=5)
        self.start_id_entry.insert(0, str(self.robber_logic.get_last_scan_id()))

        # --- Download Controls ---
        self.download_frame = ttk.Frame(controls_frame)
        self.download_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.download_frame, text="Keyword:").pack(side=tk.LEFT, padx=5)
        self.keyword_entry = ttk.Entry(self.download_frame, width=40)
        self.keyword_entry.pack(side=tk.LEFT, padx=5)

        # --- Action Buttons ---
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        self.start_button = ttk.Button(buttons_frame, text="Start", command=self.start_operation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self.stop_operation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # --- Log Viewer ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        self.toggle_controls()

    def toggle_controls(self):
        if self.mode.get() == "scan":
            self.scan_frame.grid()
            self.download_frame.grid_remove()
        else:
            self.scan_frame.grid_remove()
            self.download_frame.grid()

    def update_log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def process_queue(self):
        try:
            message = self.message_queue.get_nowait()
            self.update_log(message)
        except Exception:
            pass
        finally:
            self.top.after(100, self.process_queue)

    def start_operation(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        mode = self.mode.get()
        
        if mode == "scan":
            start_id = self.start_id_entry.get()
            self.worker_thread = threading.Thread(
                target=self.robber_logic.start_scanning,
                args=(start_id, self.queue_update)
            )
        else: # download
            keyword = self.keyword_entry.get()
            self.worker_thread = threading.Thread(
                target=self.robber_logic.start_downloading,
                args=(keyword, self.queue_update)
            )
        
        self.worker_thread.start()
        self.check_thread()

    def stop_operation(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.robber_logic.stop_operation()
            self.stop_button.config(state=tk.DISABLED)

    def queue_update(self, message):
        self.message_queue.put(message)

    def check_thread(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.top.after(100, self.check_thread)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            if not self.robber_logic.stop_event.is_set():
                self.queue_update("-----Operation finished.-----")

    def on_closing(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_operation()
            # Wait a moment for the thread to acknowledge the stop signal
            self.top.after(100, self.on_closing)
            return
        self.robber_logic.close_connection()
        self.top.destroy()

if __name__ == "__main__":
    # This block is for standalone testing of the RobberGUI
    root = tk.Tk()
    root.title("Main App Simulator")
    
    def open_robber_gui():
        app = RobberGUI(root)
        app.top.grab_set() # Make it modal
        root.wait_window(app.top) # Wait until the Toplevel window is destroyed

    tk.Button(root, text="Open Robber GUI", command=open_robber_gui).pack(pady=20, padx=50)
    
    root.mainloop()

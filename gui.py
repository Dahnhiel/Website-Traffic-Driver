import tkinter as tk
from tkinter import messagebox
from index import TrafficGenerator
import threading

class TrafficGeneratorGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Traffic Generator")
        
        # Set default window size (width x height) and disable resizing
        self.master.geometry("500x300")           # Initial size: 500px wide, 300px tall
        self.master.resizable(False, False)       # Prevent window resizing

        # Create widgets
        self.url_label = tk.Label(master, text="Target URL:")
        self.url_label.pack()
        
        # Add the URL input field
        self.url_entry = tk.Entry(master)
        self.url_entry.pack()

        self.sessions_label = tk.Label(master, text="Number of Sessions:")
        self.sessions_label.pack()

        self.sessions_entry = tk.Entry(master)
        self.sessions_entry.pack()

        self.concurrent_label = tk.Label(master, text="Concurrent Sessions:")
        self.concurrent_label.pack()

        self.concurrent_entry = tk.Entry(master)
        self.concurrent_entry.pack()

        self.start_button = tk.Button(master, text="Start", command=self.start_traffic)
        self.start_button.pack()

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_traffic, state=tk.DISABLED)
        self.stop_button.pack()

        self.result_label = tk.Label(master, text="Results will be shown here.")
        self.result_label.pack()

        self.status_label = tk.Label(master, text="Status: Idle", fg="green")
        self.status_label.pack()

        self.traffic_generator = None
        self.traffic_thread = None
        self.num_sessions = 0
        self.max_concurrent = 0

    def start_traffic(self):
        target_url = self.url_entry.get().strip()
        num_sessions_str = self.sessions_entry.get().strip()
        max_concurrent_str = self.concurrent_entry.get().strip()

        if not target_url:
            messagebox.showwarning("Input Error", "Please enter a valid URL.")
            return

        if not num_sessions_str or not max_concurrent_str:
            messagebox.showwarning("Input Error", "Please fill in Number of Sessions and Concurrent Sessions.")
            return

        try:
            self.num_sessions = int(num_sessions_str)
            self.max_concurrent = int(max_concurrent_str)
            if self.num_sessions <= 0 or self.max_concurrent <= 0:
                raise ValueError("Sessions must be positive integers.")
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid input. Enter positive integers for sessions.")
            return

        # Disable the start button and enable the stop button
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Update status
        self.status_label.config(text="Status: Generating Traffic...", fg="blue")
        self.result_label.config(text="Please wait, generating traffic...")

        self.traffic_generator = TrafficGenerator(target_url)

        # Start traffic generation in a thread
        self.traffic_thread = threading.Thread(target=self.run_traffic)
        self.traffic_thread.start()

    def stop_traffic(self):
        if self.traffic_generator:
            self.traffic_generator.stop()
            self.traffic_thread.join()
            self.status_label.config(text="Status: Stopped", fg="red")
            messagebox.showinfo("Stopped", "Traffic generation stopped.")

        # Reset buttons
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run_traffic(self):
        try:
            successful, failed = self.traffic_generator.generate_traffic(
                num_sessions=self.num_sessions,
                max_concurrent=self.max_concurrent
            )
            self.result_label.config(
                text=f"Traffic generation complete!\nSuccessful: {successful}, Failed: {failed}"
            )
            self.status_label.config(text="Status: Completed", fg="green")
        except Exception as e:
            self.result_label.config(text="Traffic generation failed. Check logs.")
            self.status_label.config(text=f"Status: Failed ({str(e)})", fg="red")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = TrafficGeneratorGUI(root)
    root.mainloop()
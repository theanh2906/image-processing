import math
import os
import subprocess
import threading
import json
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk
import numpy as np
import cv2
from pathlib import Path
import time


# --- Helper Functions ---

def format_time(seconds):
    """Converts seconds (float) to HH:MM:SS.ms string"""
    if seconds is None or seconds < 0:
        return "00:00:00.000"
    millisec = int((seconds - int(seconds)) * 1000)
    total_seconds = int(seconds)
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hrs:02}:{mins:02}:{secs:02}.{millisec:03}"

def parse_time(time_str):
    """Converts HH:MM:SS.ms string to seconds (float)"""
    try:
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError("Invalid time format")
        hrs = int(parts[0])
        mins = int(parts[1])
        sec_parts = parts[2].split('.')
        secs = int(sec_parts[0])
        millisec = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        # Clamp milliseconds to 3 digits
        millisec_str = f"{millisec:03}"
        millisec = int(millisec_str[:3])

        total_seconds = float(hrs * 3600 + mins * 60 + secs + millisec / 1000.0)
        return total_seconds
    except Exception:
        # Return None or raise a more specific error if parsing fails
        return None

def get_media_duration(filepath):
    """Gets media duration in seconds using ffprobe"""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filepath
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        return duration
    except FileNotFoundError:
        messagebox.showerror("Error", "FFprobe not found. Please ensure FFmpeg (including ffprobe) is installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error getting duration: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred getting duration: {e}")
        return None


# --- Main Application Class ---

class MediaCutterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Enhanced Media Cutter")
        self.geometry("1000x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.input_file = ""
        self.output_file = ""
        self.duration_seconds = 0.0
        self.start_seconds = 0.0
        self.end_seconds = 0.0
        self.recent_files = []
        self.load_recent_files()

        # --- Input File Selection ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.input_label = ctk.CTkLabel(self.input_frame, text="Input File:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Select a video or audio file...", width=350)
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.input_entry.configure(state="disabled")

        self.browse_input_button = ctk.CTkButton(self.input_frame, text="Browse", command=self.browse_input)
        self.browse_input_button.grid(row=0, column=2, padx=10, pady=10)

        # Recent files dropdown
        self.recent_files_var = ctk.StringVar()
        self.recent_files_dropdown = ctk.CTkOptionMenu(
            self.input_frame,
            values=self.recent_files,
            command=self.load_recent_file,
            variable=self.recent_files_var
        )
        self.recent_files_dropdown.grid(row=0, column=3, padx=10, pady=10)

        # --- Preview Window ---
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Preview")
        self.preview_label.grid(row=0, column=0, padx=10, pady=5)

        self.preview_canvas = ctk.CTkCanvas(self.preview_frame, bg="black")
        self.preview_canvas.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Preview controls
        self.preview_controls = ctk.CTkFrame(self.preview_frame)
        self.preview_controls.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.preview_play_button = ctk.CTkButton(self.preview_controls, text="▶", width=30, command=self.toggle_preview)
        self.preview_play_button.grid(row=0, column=0, padx=5)
        
        self.preview_time_label = ctk.CTkLabel(self.preview_controls, text="00:00:00.000")
        self.preview_time_label.grid(row=0, column=1, padx=5)
        
        self.preview_slider = ctk.CTkSlider(self.preview_controls, from_=0, to=100)
        self.preview_slider.grid(row=0, column=2, padx=5, sticky="ew")
        self.preview_slider.bind("<ButtonRelease-1>", self.update_preview_from_slider)

        # --- Timeline / Time Selection ---
        self.timeline_frame = ctk.CTkFrame(self)
        self.timeline_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.timeline_frame.grid_columnconfigure(1, weight=1)

        # Start Time
        self.start_label = ctk.CTkLabel(self.timeline_frame, text="Start Time:")
        self.start_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.start_slider = ctk.CTkSlider(self.timeline_frame, from_=0, to=100, command=self.update_start_time_from_slider)
        self.start_slider.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.start_slider.set(0)
        self.start_slider.configure(state="disabled")

        self.start_time_entry = ctk.CTkEntry(self.timeline_frame, width=100)
        self.start_time_entry.grid(row=0, column=2, padx=10, pady=5)
        self.start_time_entry.insert(0, "00:00:00.000")
        self.start_time_entry.bind("<FocusOut>", self.update_times_from_entry)
        self.start_time_entry.bind("<Return>", self.update_times_from_entry)
        self.start_time_entry.configure(state="disabled")

        # End Time
        self.end_label = ctk.CTkLabel(self.timeline_frame, text="End Time:")
        self.end_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.end_slider = ctk.CTkSlider(self.timeline_frame, from_=0, to=100, command=self.update_end_time_from_slider)
        self.end_slider.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.end_slider.set(100)
        self.end_slider.configure(state="disabled")

        self.end_time_entry = ctk.CTkEntry(self.timeline_frame, width=100)
        self.end_time_entry.grid(row=1, column=2, padx=10, pady=5)
        self.end_time_entry.insert(0, "00:00:00.000")
        self.end_time_entry.bind("<FocusOut>", self.update_times_from_entry)
        self.end_time_entry.bind("<Return>", self.update_times_from_entry)
        self.end_time_entry.configure(state="disabled")

        # --- Output Settings ---
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1)

        self.output_label = ctk.CTkLabel(self.output_frame, text="Save As:")
        self.output_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.output_entry = ctk.CTkEntry(self.output_frame, placeholder_text="Select output location...", width=350)
        self.output_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.output_entry.configure(state="disabled")

        self.browse_output_button = ctk.CTkButton(self.output_frame, text="Save As...", command=self.browse_output)
        self.browse_output_button.grid(row=0, column=2, padx=10, pady=10)
        self.browse_output_button.configure(state="disabled")

        # Output format selection
        self.format_label = ctk.CTkLabel(self.output_frame, text="Format:")
        self.format_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.format_var = ctk.StringVar(value="Same as input")
        self.format_dropdown = ctk.CTkOptionMenu(
            self.output_frame,
            values=["Same as input", "MP4", "MKV", "AVI", "MOV", "MP3", "WAV"],
            variable=self.format_var
        )
        self.format_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Quality settings
        self.quality_label = ctk.CTkLabel(self.output_frame, text="Quality:")
        self.quality_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.quality_slider = ctk.CTkSlider(self.output_frame, from_=0, to=100)
        self.quality_slider.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.quality_slider.set(80)

        # --- Progress Bar ---
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.progress_label.grid(row=1, column=0, padx=10, pady=5)

        # --- Action Buttons ---
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

        self.cut_button = ctk.CTkButton(self.button_frame, text="Cut Media", command=self.start_cutting_thread)
        self.cut_button.grid(row=0, column=0, padx=10, pady=10)
        self.cut_button.configure(state="disabled")

        self.batch_button = ctk.CTkButton(self.button_frame, text="Batch Process", command=self.browse_batch_files)
        self.batch_button.grid(row=0, column=1, padx=10, pady=10)

        # --- Status Bar ---
        self.status_bar = ctk.CTkLabel(self, text="Status: Load a file to begin.", anchor="w", height=25)
        self.status_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # --- Keyboard Shortcuts ---
        self.bind("<Control-o>", lambda e: self.browse_input())
        self.bind("<Control-s>", lambda e: self.browse_output())
        self.bind("<space>", lambda e: self.toggle_preview())
        self.bind("<Left>", lambda e: self.seek_preview(-1))
        self.bind("<Right>", lambda e: self.seek_preview(1))

        # Preview state
        self.is_preview_playing = False
        self.preview_thread = None
        self.stop_preview = False

    def load_recent_files(self):
        """Load recent files from config file"""
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".media_cutter_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.recent_files = config.get('recent_files', [])
        except Exception as e:
            print(f"Error loading recent files: {e}")

    def save_recent_files(self):
        """Save recent files to config file"""
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".media_cutter_config.json")
            config = {'recent_files': self.recent_files}
            with open(config_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving recent files: {e}")

    def add_recent_file(self, filepath):
        """Add a file to recent files list"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:10]  # Keep only 10 most recent
        self.recent_files_dropdown.configure(values=self.recent_files)
        self.save_recent_files()

    def load_recent_file(self, filepath):
        """Load a file from recent files list"""
        if os.path.exists(filepath):
            self.input_file = filepath
            self.input_entry.configure(state="normal")
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.input_file)
            self.input_entry.configure(state="disabled")
            self.load_media_info()
            self.suggest_output_path()
            self.browse_output_button.configure(state="normal")

    def toggle_preview(self):
        """Toggle preview playback"""
        if not self.input_file:
            return

        if self.is_preview_playing:
            self.stop_preview = True
            self.is_preview_playing = False
            self.preview_play_button.configure(text="▶")
        else:
            self.stop_preview = False
            self.is_preview_playing = True
            self.preview_play_button.configure(text="⏸")
            self.preview_thread = threading.Thread(target=self.preview_loop)
            self.preview_thread.daemon = True
            self.preview_thread.start()

    def preview_loop(self):
        """Main preview playback loop"""
        cap = cv2.VideoCapture(self.input_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_time = 1.0 / fps

        while not self.stop_preview and self.is_preview_playing:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            self.preview_time_label.configure(text=format_time(current_time))
            self.preview_slider.set(current_time / self.duration_seconds * 100)

            # Convert frame to RGB and resize
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 360))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.preview_canvas.create_image(0, 0, image=photo, anchor="nw")
            self.preview_canvas.photo = photo

            # Sleep for frame time
            time.sleep(frame_time)

        cap.release()

    def seek_preview(self, direction):
        """Seek preview forward or backward"""
        if not self.input_file:
            return

        cap = cv2.VideoCapture(self.input_file)
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        new_frame = max(0, current_frame + direction * 30)  # Seek 30 frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
        
        ret, frame = cap.read()
        if ret:
            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            self.preview_time_label.configure(text=format_time(current_time))
            self.preview_slider.set(current_time / self.duration_seconds * 100)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 360))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.preview_canvas.create_image(0, 0, image=photo, anchor="nw")
            self.preview_canvas.photo = photo

        cap.release()

    def update_preview_from_slider(self, event):
        """Update preview when slider is moved"""
        if not self.input_file:
            return

        time_seconds = self.preview_slider.get() / 100.0 * self.duration_seconds
        cap = cv2.VideoCapture(self.input_file)
        cap.set(cv2.CAP_PROP_POS_MSEC, time_seconds * 1000)
        
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 360))
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.preview_canvas.create_image(0, 0, image=photo, anchor="nw")
            self.preview_canvas.photo = photo

        cap.release()

    def browse_batch_files(self):
        """Open file dialog for batch processing"""
        filepaths = filedialog.askopenfilenames(
            title="Select Media Files",
            filetypes=(("Media Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.mp3 *.wav *.ogg *.aac *.flac"),
                       ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv"),
                       ("Audio Files", "*.mp3 *.wav *.ogg *.aac *.flac"),
                       ("All Files", "*.*"))
        )
        if filepaths:
            self.batch_process_files(filepaths)

    def batch_process_files(self, filepaths):
        """Process multiple files with the same settings"""
        if not filepaths:
            return

        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        total_files = len(filepaths)
        processed = 0

        for filepath in filepaths:
            try:
                self.progress_label.configure(text=f"Processing {os.path.basename(filepath)}...")
                self.progress_bar.set(processed / total_files)

                # Generate output path
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                output_format = self.format_var.get()
                if output_format == "Same as input":
                    ext = os.path.splitext(filepath)[1]
                else:
                    ext = f".{output_format.lower()}"
                output_path = os.path.join(output_dir, f"{base_name}_cut{ext}")

                # Run ffmpeg with current settings
                self.run_ffmpeg_cut(
                    filepath,
                    output_path,
                    self.start_seconds,
                    self.end_seconds
                )

                processed += 1
                self.progress_bar.set(processed / total_files)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {filepath}: {str(e)}")

        self.progress_label.configure(text="Batch processing completed")
        messagebox.showinfo("Success", f"Processed {processed} of {total_files} files")

    def run_ffmpeg_cut(self, input_path, output_path, start_time, end_time):
        """Run ffmpeg to cut the media file with progress tracking"""
        duration = end_time - start_time
        quality = int(self.quality_slider.get())

        # Build ffmpeg command with quality settings
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', 'libx264' if output_path.lower().endswith(('.mp4', '.mkv')) else 'copy',
            '-crf', str(31 - (quality * 0.3)),  # Convert quality (0-100) to CRF (0-51)
            '-c:a', 'aac' if output_path.lower().endswith(('.mp4', '.mkv')) else 'copy',
            output_path
        ]

        process = subprocess.Popen(
            command,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if 'time=' in line:
                time_str = line.split('time=')[1].split()[0]
                current_time = parse_time(time_str)
                if current_time is not None:
                    progress = (current_time - start_time) / duration
                    self.progress_bar.set(min(1.0, max(0.0, progress)))

        if process.returncode != 0:
            raise Exception("FFmpeg process failed")

    def browse_input(self):
        """Opens file dialog to select input media file."""
        filepath = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=(("Media Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.mp3 *.wav *.ogg *.aac *.flac"),
                       ("Video Files", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv"),
                       ("Audio Files", "*.mp3 *.wav *.ogg *.aac *.flac"),
                       ("All Files", "*.*"))
        )
        if filepath:
            self.input_file = filepath
            self.input_entry.configure(state="normal")
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.input_file)
            self.input_entry.configure(state="disabled")
            self.status_bar.configure(text="Status: Loading media info...")
            self.load_media_info()
            # Suggest default output path
            self.suggest_output_path()
            self.browse_output_button.configure(state="normal")

    def load_media_info(self):
        """Gets duration and updates UI elements."""
        if not self.input_file:
            return

        duration = get_media_duration(self.input_file)

        if duration is not None:
            self.duration_seconds = duration
            self.status_bar.configure(text=f"Status: Loaded media. Duration: {format_time(self.duration_seconds)}")

            # Configure sliders
            self.start_slider.configure(to=self.duration_seconds, state="normal")
            self.end_slider.configure(to=self.duration_seconds, state="normal")

            # Reset times and UI
            self.start_seconds = 0.0
            self.end_seconds = self.duration_seconds
            self.start_slider.set(self.start_seconds)
            self.end_slider.set(self.end_seconds)

            self.start_time_entry.configure(state="normal")
            self.start_time_entry.delete(0, "end")
            self.start_time_entry.insert(0, format_time(self.start_seconds))

            self.end_time_entry.configure(state="normal")
            self.end_time_entry.delete(0, "end")
            self.end_time_entry.insert(0, format_time(self.end_seconds))

            self.cut_button.configure(state="normal")
            self.status_bar.configure(text="Status: Ready. Adjust start/end times.")
        else:
            self.duration_seconds = 0.0
            self.status_bar.configure(text="Status: Error loading media info.")
            self.start_slider.configure(state="disabled")
            self.end_slider.configure(state="disabled")
            self.start_time_entry.configure(state="disabled")
            self.end_time_entry.configure(state="disabled")
            self.cut_button.configure(state="disabled")

    def suggest_output_path(self):
        """Suggests a default output path based on the input file."""
        if not self.input_file:
            return
        try:
            input_dir = os.path.dirname(self.input_file)
            base_name, ext = os.path.splitext(os.path.basename(self.input_file))
            default_output = os.path.join(input_dir, f"{base_name}_output{ext}")
            self.output_file = default_output
            self.output_entry.configure(state="normal")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, self.output_file)
            self.output_entry.configure(state="disabled")
        except Exception as e:
            print(f"Error suggesting output path: {e}")

    def browse_output(self):
        """Opens file dialog to select output file path."""
        if not self.input_file:
            messagebox.showwarning("Warning", "Please select an input file first.")
            return

        # Get extension from input to suggest for output
        _, input_ext = os.path.splitext(self.input_file)
        if not input_ext: input_ext = ".mp4" # Default if input has no extension

        filepath = filedialog.asksaveasfilename(
            title="Save Cut Media As...",
            initialfile=os.path.basename(self.output_entry.get()), # Use current suggestion
            initialdir=os.path.dirname(self.output_entry.get()),  # Use current suggestion dir
            defaultextension=input_ext,
            filetypes=(("Matching Extension", f"*{input_ext}"),
                       ("All Files", "*.*"))
        )
        if filepath:
            self.output_file = filepath
            self.output_entry.configure(state="normal")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, self.output_file)
            self.output_entry.configure(state="disabled")

    def update_start_time_from_slider(self, value):
        """Updates start time entry when slider moves."""
        self.start_seconds = float(value)
        # Prevent start time from exceeding end time
        if self.start_seconds >= self.end_seconds:
            self.start_seconds = self.end_seconds - 0.001 # Ensure slightly less
            if self.start_seconds < 0: self.start_seconds = 0.0
            self.start_slider.set(self.start_seconds) # Adjust slider visually

        time_str = format_time(self.start_seconds)
        self.start_time_entry.delete(0, "end")
        self.start_time_entry.insert(0, time_str)

    def update_end_time_from_slider(self, value):
        """Updates end time entry when slider moves."""
        self.end_seconds = float(value)
        # Prevent end time from being less than start time
        if self.end_seconds <= self.start_seconds:
            self.end_seconds = self.start_seconds + 0.001 # Ensure slightly more
            if self.end_seconds > self.duration_seconds: self.end_seconds = self.duration_seconds
            self.end_slider.set(self.end_seconds) # Adjust slider visually

        time_str = format_time(self.end_seconds)
        self.end_time_entry.delete(0, "end")
        self.end_time_entry.insert(0, time_str)

    def update_times_from_entry(self, event=None):
        """Updates sliders and internal values when time is entered manually."""
        start_str = self.start_time_entry.get()
        end_str = self.end_time_entry.get()

        new_start = parse_time(start_str)
        new_end = parse_time(end_str)

        valid_start = False
        if new_start is not None and 0 <= new_start <= self.duration_seconds:
            # Don't let manual entry exceed end time directly here, just validate later
            # if new_start < self.end_seconds:
            self.start_seconds = new_start
            self.start_slider.set(self.start_seconds)
            # Reformat entry for consistency
            self.start_time_entry.delete(0, "end")
            self.start_time_entry.insert(0, format_time(self.start_seconds))
            valid_start = True
        else:
            # Revert to last known good value if invalid
            self.start_time_entry.delete(0, "end")
            self.start_time_entry.insert(0, format_time(self.start_seconds))

        valid_end = False
        if new_end is not None and 0 <= new_end <= self.duration_seconds:
            # Don't let manual entry be less than start time directly here, just validate later
            # if new_end > self.start_seconds:
            self.end_seconds = new_end
            self.end_slider.set(self.end_seconds)
            # Reformat entry for consistency
            self.end_time_entry.delete(0, "end")
            self.end_time_entry.insert(0, format_time(self.end_seconds))
            valid_end = True
        else:
            # Revert to last known good value if invalid
            self.end_time_entry.delete(0, "end")
            self.end_time_entry.insert(0, format_time(self.end_seconds))

        # Optional: Add visual feedback if entry was invalid

    def validate_inputs(self):
        """Checks if all inputs are valid before cutting."""
        if not self.input_file or not os.path.exists(self.input_file):
            messagebox.showerror("Error", "Invalid or missing input file.")
            return False

        if not self.output_file:
            # If output field is empty but input is valid, generate default
            self.suggest_output_path()
            if not self.output_file: # Still no output file (edge case)
                messagebox.showerror("Error", "Please specify an output file location.")
                return False

        # Update internal times from entries one last time
        self.update_times_from_entry()

        if self.start_seconds >= self.end_seconds:
            messagebox.showerror("Error", f"Start time ({format_time(self.start_seconds)}) must be before end time ({format_time(self.end_seconds)}).")
            return False

        if self.start_seconds < 0 or self.end_seconds > self.duration_seconds:
            messagebox.showerror("Error", "Start or end time is outside the media duration.")
            return False

        return True

    def set_ui_state(self, state):
        """Enable/disable UI elements during processing."""
        self.browse_input_button.configure(state=state)
        self.browse_output_button.configure(state=state)
        self.cut_button.configure(state=state)
        self.start_slider.configure(state=state)
        self.end_slider.configure(state=state)
        self.start_time_entry.configure(state=state)
        self.end_time_entry.configure(state=state)

    def start_cutting_thread(self):
        """Validates input and starts the ffmpeg process in a separate thread."""
        if not self.validate_inputs():
            return

        self.set_ui_state("disabled")
        self.status_bar.configure(text="Status: Processing... please wait.")

        # Use the internal float values for precision
        start_t = self.start_seconds
        end_t = self.end_seconds

        # Create and start the processing thread
        thread = threading.Thread(
            target=self.run_ffmpeg_cut,
            args=(self.input_file, self.output_file, start_t, end_t),
            daemon=True # Allows closing app even if thread is running (use cautiously)
        )
        thread.start()


# --- Run the Application ---
if __name__ == "__main__":
    app = MediaCutterApp()
    app.mainloop()
import math
import os
import subprocess
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk


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

        self.title("Simple Media Cutter")
        self.geometry("650x450")
        ctk.set_appearance_mode("System") # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1) # Allow timeline section to expand if needed

        self.input_file = ""
        self.output_file = ""
        self.duration_seconds = 0.0
        self.start_seconds = 0.0
        self.end_seconds = 0.0

        # --- Input File Selection ---
        self.input_label = ctk.CTkLabel(self, text="Input File:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.input_entry = ctk.CTkEntry(self, placeholder_text="Select a video or audio file...", width=350)
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.input_entry.configure(state="disabled") # Read-only

        self.browse_input_button = ctk.CTkButton(self, text="Browse", command=self.browse_input)
        self.browse_input_button.grid(row=0, column=2, padx=10, pady=10)

        # --- Duration Display ---
        self.duration_label = ctk.CTkLabel(self, text="Duration: 00:00:00.000")
        self.duration_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

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


        # --- Output File Selection ---
        self.output_label = ctk.CTkLabel(self, text="Save As:")
        self.output_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.output_entry = ctk.CTkEntry(self, placeholder_text="Select output location...", width=350)
        self.output_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.output_entry.configure(state="disabled") # Read-only initially

        self.browse_output_button = ctk.CTkButton(self, text="Save As...", command=self.browse_output)
        self.browse_output_button.grid(row=4, column=2, padx=10, pady=10)
        self.browse_output_button.configure(state="disabled")

        # --- Action Button & Status Bar ---
        self.cut_button = ctk.CTkButton(self, text="Cut Media", command=self.start_cutting_thread)
        self.cut_button.grid(row=5, column=1, padx=10, pady=20)
        self.cut_button.configure(state="disabled")

        self.status_bar = ctk.CTkLabel(self, text="Status: Load a file to begin.", anchor="w", height=25)
        self.status_bar.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")


    # --- Methods ---

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
            self.duration_label.configure(text=f"Duration: {format_time(self.duration_seconds)}")

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
            self.duration_label.configure(text="Duration: Error loading info")
            self.start_slider.configure(state="disabled")
            self.end_slider.configure(state="disabled")
            self.start_time_entry.configure(state="disabled")
            self.end_time_entry.configure(state="disabled")
            self.cut_button.configure(state="disabled")
            self.status_bar.configure(text="Status: Error loading media info.")

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


    def run_ffmpeg_cut(self, input_path, output_path, start_time, end_time):
        """Constructs and runs the ffmpeg command."""
        # Using -to requires calculating duration, -t is simpler if end_time is given
        # duration_cut = end_time - start_time
        # command = [
        #     'ffmpeg',
        #     '-i', input_path,
        #     '-ss', str(start_time),   # Start time in seconds
        #     '-t', str(duration_cut), # Duration to cut
        #     '-c', 'copy',           # Try to copy streams directly (fast, lossless)
        #     '-avoid_negative_ts', 'make_zero', # Helps with some formats
        #     '-y',                   # Overwrite output without asking
        #     output_path
        # ]
        # Alternative using -to
        command = [
            'ffmpeg',
            '-ss', str(start_time),   # Start time MUST come before -i for fast seeking
            '-i', input_path,
            '-to', str(end_time),     # End time
            '-c', 'copy',           # Try to copy streams directly (fast, lossless)
            '-avoid_negative_ts', 'make_zero', # Helps with some formats
            '-y',                   # Overwrite output without asking
            '-hide_banner',         # Cleaner output
            '-loglevel', 'error',     # Show only errors
            output_path
        ]

        success = False
        message = "Status: Processing..."
        try:
            print(f"Running command: {' '.join(command)}") # For debugging
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            print("FFmpeg stdout:", process.stdout)
            print("FFmpeg stderr:", process.stderr)
            success = True
            message = f"Status: Successfully cut media to {os.path.basename(output_path)}"

        except FileNotFoundError:
            message = "Status: Error - FFmpeg not found. Check installation and PATH."
            print(message)
        except subprocess.CalledProcessError as e:
            # If -c copy fails (e.g., format change needed, complex edits), try re-encoding
            message = f"Status: Copy failed (may require re-encoding). Error: {e.stderr[:200]}..."
            print(f"FFmpeg (-c copy) failed: {e.stderr}")
            print("Attempting re-encoding...")
            command_reencode = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', input_path,
                '-to', str(end_time),
                # '-c:v', 'libx264', '-crf', '23', # Example re-encode video (adjust codec/settings)
                # '-c:a', 'aac', '-b:a', '192k', # Example re-encode audio
                '-avoid_negative_ts', 'make_zero',
                '-y',
                '-hide_banner',
                '-loglevel', 'error',
                output_path
            ]
            # Remove '-c', 'copy' if present from original command for re-encoding attempt
            command_reencode.pop(command_reencode.index('-c'))
            command_reencode.pop(command_reencode.index('copy'))

            try:
                print(f"Running re-encode command: {' '.join(command_reencode)}")
                process_reencode = subprocess.run(command_reencode, capture_output=True, text=True, check=True)
                print("FFmpeg (re-encode) stdout:", process_reencode.stdout)
                print("FFmpeg (re-encode) stderr:", process_reencode.stderr)
                success = True
                message = f"Status: Successfully cut (re-encoded) media to {os.path.basename(output_path)}"
            except subprocess.CalledProcessError as e_reencode:
                message = f"Status: Error - Re-encoding failed. FFmpeg stderr: {e_reencode.stderr[:200]}..."
                print(f"FFmpeg (re-encode) failed: {e_reencode.stderr}")
            except Exception as e_reencode_other:
                message = f"Status: Error - Unexpected re-encoding error: {e_reencode_other}"
                print(message)

        except Exception as e:
            message = f"Status: Error - An unexpected error occurred: {e}"
            print(message)
        finally:
            # Schedule GUI update on the main thread
            self.after(0, self.cutting_finished, success, message)


    def cutting_finished(self, success, message):
        """Updates the GUI after the cutting process completes."""
        self.set_ui_state("normal") # Re-enable UI
        # Ensure time entry states are correct if duration was loaded
        if self.duration_seconds > 0:
            self.start_time_entry.configure(state="normal")
            self.end_time_entry.configure(state="normal")
            self.start_slider.configure(state="normal")
            self.end_slider.configure(state="normal")
        else:
            self.start_time_entry.configure(state="disabled")
            self.end_time_entry.configure(state="disabled")
            self.start_slider.configure(state="disabled")
            self.end_slider.configure(state="disabled")
            self.cut_button.configure(state="disabled")
            self.browse_output_button.configure(state="disabled")


        self.status_bar.configure(text=message)
        if success:
            print("Cutting process finished successfully.")
        else:
            print("Cutting process finished with errors.")
            messagebox.showerror("Processing Error", message)


# --- Run the Application ---
if __name__ == "__main__":
    app = MediaCutterApp()
    app.mainloop()
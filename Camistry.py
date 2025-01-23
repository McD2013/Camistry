import tkinter as tk
import cv2
from PIL import Image, ImageTk
import datetime
import numpy as np
import sounddevice as sd
import threading
import time

class VideoCaptureApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Webcam setup
        self.video_source = 0  # Use 0 for the default webcam
        self.vid = cv2.VideoCapture(self.video_source)

        if not self.vid.isOpened():
            print("Error: Could not open video source.")
            self.window.quit()
            return

        self.canvas = tk.Canvas(window, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        # Initialize audio monitoring
        self.sound_threshold = 0.01  # Adjust sensitivity (higher = less sensitive)
        self.beep_duration = 0.2  # Beep sound duration in seconds
        self.beep_flag = False
        self.audio_stream = None
        self.start_audio_monitoring()

        # Start the video update loop
        self.update()

        # Run the GUI
        self.window.mainloop()

    def start_audio_monitoring(self):
        """Start a thread to monitor the microphone."""
        self.audio_thread = threading.Thread(target=self.monitor_audio, daemon=True)
        self.audio_thread.start()

    def monitor_audio(self):
        """Continuously monitor the microphone for sound detection."""
        def callback(indata, frames, time, status):
            """Process the audio input in real time."""
            if status:
                print(status)

            # Calculate the volume of the audio input
            volume_norm = np.linalg.norm(indata) / len(indata)
            if volume_norm > self.sound_threshold:
                self.beep_flag = True
                self.play_beep()
            else:
                self.beep_flag = False

        # Open the audio stream
        with sd.InputStream(callback=callback, channels=1, samplerate=44100):
            while True:
                time.sleep(0.1)

    def play_beep(self):
        """Play a simple beep sound."""
        duration = int(self.beep_duration * 44100)  # Convert duration to samples
        freq = 440.0  # Frequency of the beep in Hz
        t = np.linspace(0, self.beep_duration, duration, endpoint=False)
        beep = 0.5 * np.sin(2 * np.pi * freq * t)
        sd.play(beep, samplerate=44100)
        time.sleep(self.beep_duration)
        sd.stop()

    def update(self):
        # Capture the current frame
        ret, frame = self.vid.read()
        if not ret:
            print("Failed to grab frame.")
            return

        # Get the current time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add the date and time to the frame
        cv2.putText(frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Add visual alert if sound is detected
        if self.beep_flag:
            height, width, _ = frame.shape
            cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), 10)  # Red border

        # Convert the frame to RGB and update the canvas
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
        self.canvas.imgtk = imgtk  # Prevent garbage collection

        # Schedule the next update
        self.window.after(15, self.update)

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
        if self.audio_stream:
            self.audio_stream.close()

# Create the Tkinter application
root = tk.Tk()
app = VideoCaptureApp(root, "Camistry 1.1")

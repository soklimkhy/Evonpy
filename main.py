import sys
import subprocess
import imageio_ffmpeg
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QLineEdit, QMessageBox,
    QSlider, QProgressBar, QGroupBox, QComboBox
)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon

class VideoEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Video Editor (FFmpeg Internal)")
        self.setFixedSize(750, 750)

        self.video_path = ""
        self.audio_path = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.timeline_slider)
        self.timeline_slider.sliderMoved.connect(self.seek_video)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timeline)

        controls_box = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_box)

        # Buttons
        btn_layout = QHBoxLayout()
        self.open_button = QPushButton(QIcon("icons/open.png"), "Open Video")
        self.play_button = QPushButton(QIcon("icons/play.png"), "Play")
        self.audio_button = QPushButton(QIcon("icons/music.png"), "Add Music")
        self.export_button = QPushButton(QIcon("icons/export.png"), "Export")

        self.open_button.clicked.connect(self.open_video)
        self.play_button.clicked.connect(self.play_video)
        self.audio_button.clicked.connect(self.open_audio)
        self.export_button.clicked.connect(self.export_video)

        for b in [self.open_button, self.play_button, self.audio_button, self.export_button]:
            btn_layout.addWidget(b)

        controls_layout.addLayout(btn_layout)

        # Inputs
        self.start_input = QLineEdit(placeholderText="Start (00:00:00)")
        self.end_input = QLineEdit(placeholderText="End (00:00:10)")
        self.crop_input = QLineEdit(placeholderText="Crop (x:y:w:h)")
        self.text_input = QLineEdit(placeholderText="Overlay text")

        for w in [self.start_input, self.end_input, self.crop_input, self.text_input]:
            controls_layout.addWidget(w)

        # Sliders
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        controls_layout.addWidget(QLabel("Brightness"))
        controls_layout.addWidget(self.brightness_slider)

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        controls_layout.addWidget(QLabel("Contrast"))
        controls_layout.addWidget(self.contrast_slider)

        layout.addWidget(controls_box)

        # Progress bar + info
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        # Style
        self.setStyleSheet("""
            QPushButton { padding: 6px; }
            QLineEdit { padding: 4px; }
            QLabel { font-weight: bold; }
        """)
        # Crop preset combo
        self.crop_combo = QComboBox()
        self.crop_combo.addItems(["Original", "16:9", "9:16", "1:1"])
        controls_layout.addWidget(QLabel("Crop Preset"))
        controls_layout.addWidget(self.crop_combo)

        # Resolution combo
        self.res_combo = QComboBox()
        self.res_combo.addItems(["Original", "720p", "1080p", "1440p", "2K", "4K", "8K"])
        controls_layout.addWidget(QLabel("Export Resolution"))
        controls_layout.addWidget(self.res_combo)

        # Audio format combo
        self.audio_combo = QComboBox()
        self.audio_combo.addItems(["AAC", "MP3", "WAV", "FLAC", "OGG"])
        controls_layout.addWidget(QLabel("Audio Format"))
        controls_layout.addWidget(self.audio_combo)


    def open_video(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if f:
            self.video_path = f
            self.player.setSource(QUrl.fromLocalFile(f))
            self.info_label.setText(f"Loaded: {f}")
            self.player.durationChanged.connect(lambda _: self.timer.start(500))

    def play_video(self):
        if self.video_path:
            self.player.play()

    def open_audio(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open Audio", "", "Audio Files (*.mp3 *.wav)")
        if f:
            self.audio_path = f
            QMessageBox.information(self, "Audio", f"Added: {f}")

    def seek_video(self, v):
        if self.player.duration() > 0:
            pos = (v / 100) * self.player.duration()
            self.player.setPosition(int(pos))

    def update_timeline(self):
        if self.player.duration() > 0:
            val = (self.player.position() / self.player.duration()) * 100
            self.timeline_slider.blockSignals(True)
            self.timeline_slider.setValue(int(val))
            self.timeline_slider.blockSignals(False)

    # Update export_video() to use the new options:
    def export_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "No video", "Open a video first.")
            return

        out_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "MP4 Files (*.mp4)")
        if not out_path:
            return

        start = self.start_input.text()
        end = self.end_input.text()
        text = self.text_input.text()
        brightness = self.brightness_slider.value() / 100
        contrast = (self.contrast_slider.value() / 100) + 1

        filters = []

        # Crop preset
        crop_preset = self.crop_combo.currentText()
        if crop_preset == "16:9":
            filters.append("crop=ih*16/9:ih")
        elif crop_preset == "9:16":
            filters.append("crop=iw:iw*16/9")
        elif crop_preset == "1:1":
            filters.append("crop='min(iw,ih)':min(iw,ih)")

        # Custom crop
        if self.crop_input.text():
            filters.append(f"crop={self.crop_input.text()}")

        if text:
            filters.append(f"drawtext=text='{text}':x=10:y=10:fontsize=24:fontcolor=white")
        if brightness != 0 or contrast != 1:
            filters.append(f"eq=brightness={brightness}:contrast={contrast}")

        # Resolution
        res_map = {
            "720p": "1280:720",
            "1080p": "1920:1080",
            "1440p": "2560:1440",
            "2K": "2048:1080",
            "4K": "3840:2160",
            "8K": "7680:4320"
        }
        res = self.res_combo.currentText()
        if res != "Original":
            filters.append(f"scale={res_map[res]}")

        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-i", self.video_path]
        if self.audio_path:
            cmd += ["-i", self.audio_path, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=3"]

        if start:
            cmd += ["-ss", start]
        if end:
            cmd += ["-to", end]
        if filters:
            cmd += ["-vf", ",".join(filters)]
        cmd += ["-c:a", "aac", out_path]

        self.progress.setValue(0)
        self.run_ffmpeg(cmd, out_path)

        # Get selected audio format
        audio_fmt = self.audio_combo.currentText().lower()

        # Update output path extension if necessary
        if not out_path.endswith(f".{audio_fmt}"):
            out_path += f".{audio_fmt}"

        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-i", self.video_path]

        if self.audio_path:
            cmd += ["-i", self.audio_path, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=3"]

        if start:
            cmd += ["-ss", start]
        if end:
            cmd += ["-to", end]
        if filters:
            cmd += ["-vf", ",".join(filters)]

        # Set audio codec
        audio_codec_map = {
            "aac": "aac",
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "flac": "flac",
            "ogg": "libvorbis"
        }
        codec = audio_codec_map.get(audio_fmt, "aac")
        cmd += ["-c:a", codec, out_path]

    def run_ffmpeg(self, cmd, out_path):
        try:
            dur_cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-i", self.video_path]
            result = subprocess.run(dur_cmd, stderr=subprocess.PIPE, text=True)
            m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
            total_sec = 1
            if m:
                h, m_, s = map(float, m.groups())
                total_sec = h * 3600 + m_ * 60 + s

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                print(line.strip())
                t = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                if t:
                    h, m_, s = map(float, t.groups())
                    sec = h * 3600 + m_ * 60 + s
                    percent = int((sec / total_sec) * 100)
                    self.progress.setValue(min(percent, 100))
            p.wait()
            if p.returncode == 0:
                self.progress.setValue(100)
                QMessageBox.information(self, "Done", f"Saved: {out_path}")
            else:
                QMessageBox.critical(self, "Fail", "Export failed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

def main():
    app = QApplication(sys.argv)
    w = VideoEditorApp()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

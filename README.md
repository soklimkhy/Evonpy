# PyQt6 Video Editor (FFmpeg Internal)

A simple desktop video editor built with PyQt6 and FFmpeg, allowing you to trim, crop, adjust brightness/contrast, overlay text, add music, and export videos in various resolutions and audio formats.

## Features

- Open and preview video files (`.mp4`, `.avi`, `.mov`)
- Trim video by start/end time
- Crop video (custom or presets: 16:9, 9:16, 1:1)
- Adjust brightness and contrast
- Overlay custom text
- Add background music (`.mp3`, `.wav`)
- Export with selectable resolution (Original, 720p, 1080p, 1440p, 2K, 4K, 8K)
- Export with selectable audio format (AAC, MP3, WAV, FLAC, OGG)
- Progress bar and status info

## Requirements

- Python 3.8+
- [PyQt6](https://pypi.org/project/PyQt6/)
- [imageio-ffmpeg](https://pypi.org/project/imageio-ffmpeg/)
- FFmpeg (automatically handled by `imageio-ffmpeg`)

Install dependencies:
```sh
pip install PyQt6 imageio-ffmpeg

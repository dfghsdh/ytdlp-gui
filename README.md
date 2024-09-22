# 'ytdlp-gui' (speed paste) **SPONSORBLOCK WORKS**

I wrote this ytdlp gui that has a workaround so SponsorBlock works cuz it doesn't work well using the ytdlp commands 


## Overview

ytdlp-gui is a graphical user interface for yt-dlp, a popular command-line video downloader. This project provides a user-friendly way to download videos from various platforms while incorporating a custom workaround for SponsorBlock functionality.

![image](https://github.com/user-attachments/assets/73db2e42-9cc4-447c-9a52-cbc9da06a32a)

## Features

- Easy-to-use graphical interface for yt-dlp
- Custom SponsorBlock integration for improved ad-skipping
- Easy Link Pasting

## Installation

1. Ensure you have Python installed on your system (version 3.6 or higher).
2. Make sure you have FFmpeg installed on your system. FFmpeg is required for video processing and SponsorBlock functionality. You can download it from the [official FFmpeg website](https://ffmpeg.org/download.html).
3. Clone this repository:
   ```
   git clone https://github.com/yourusername/ytdlp-gui.git
   ```
4. Navigate to the project directory:
   ```
   cd ytdlp-gui
   ```
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```
2. Enter the URL of the video you want to download in the provided field.
3. Select your desired download options.
4. Click the "Download" button to start the process.

## SponsorBlock Workaround

This GUI implements a custom solution to ensure SponsorBlock functionality works correctly, as the standard yt-dlp commands have some limitations in this area. The workaround allows for more reliable ad-skipping in downloaded videos.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for the core downloading functionality
- [SponsorBlock](https://sponsor.ajay.app/) for the ad-skipping capability
- [FFmpeg](https://ffmpeg.org/) for video processing capabilities

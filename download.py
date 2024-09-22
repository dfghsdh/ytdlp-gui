import os
import yt_dlp
from typing import Callable, List
from yt_dlp.utils import DownloadError

def download_video(url: str, output_path: str, format: str, progress_callback: Callable[[str], None] = None) -> str:
    """
    Download a video from YouTube using yt-dlp.
    
    Args:
        url (str): The YouTube video URL.
        output_path (str): The path where the video will be saved.
        format (str): The desired format ('mp3' or 'mp4').
        progress_callback (Callable[[str], None], optional): A callback function to report progress.
    
    Returns:
        str: The path of the downloaded file.
    """
    ydl_opts = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == 'mp3' else [],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'progress_hooks': [lambda d: _progress_hook(d, progress_callback)],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info:
            # It's a playlist
            info = info['entries'][0]
        
        file_extension = 'mp3' if format == 'mp3' else 'mp4'
        filename = f"{info['title']}.{file_extension}"
        return os.path.join(output_path, filename)

def _progress_hook(d: dict, callback: Callable[[str], None] = None):
    if d['status'] == 'downloading':
        percent = d['_percent_str']
        if callback:
            callback(f"Downloading: {percent}")
    elif d['status'] == 'finished':
        if callback:
            callback(f"Download completed. Converting...")

def download_playlist(url: str, output_path: str, format: str, progress_callback: Callable[[str], None] = None) -> List[str]:
    """
    Download all videos from a YouTube playlist.
    
    Args:
        url (str): The YouTube playlist URL.
        output_path (str): The path where the videos will be saved.
        format (str): The desired format ('mp3' or 'mp4').
        progress_callback (Callable[[str], None], optional): A callback function to report progress.
    
    Returns:
        List[str]: A list of paths of the downloaded files.
    """
    ydl_opts = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == 'mp3' else [],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'progress_hooks': [lambda d: _progress_hook(d, progress_callback)],
        'ignoreerrors': True,  # This will make yt-dlp continue downloading even if some videos fail
    }

    downloaded_files = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        try:
                            video_url = entry['webpage_url']
                            ydl.download([video_url])
                            file_extension = 'mp3' if format == 'mp3' else 'mp4'
                            filename = f"{entry['title']}.{file_extension}"
                            file_path = os.path.join(output_path, filename)
                            downloaded_files.append(file_path)
                            if progress_callback:
                                progress_callback(f"Successfully downloaded: {entry['title']}")
                        except DownloadError as e:
                            if progress_callback:
                                progress_callback(f"Error downloading video: {e}. Skipping to next video.")
                            continue
                    else:
                        if progress_callback:
                            progress_callback("Skipped unavailable video")
            else:
                # It's a single video, not a playlist
                ydl.download([url])
                file_extension = 'mp3' if format == 'mp3' else 'mp4'
                filename = f"{info['title']}.{file_extension}"
                file_path = os.path.join(output_path, filename)
                downloaded_files.append(file_path)
        except DownloadError as e:
            if progress_callback:
                progress_callback(f"Error downloading playlist: {e}")

    return downloaded_files

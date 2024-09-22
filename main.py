import os
import subprocess
import re
from typing import List, Optional  # Modified this line
from download import download_video
from sponser import get_sponsor_segments
from cutseg import cut_segments_mp3, cut_segments_mp4

def process_video(url: str, output_path: str, format: str = 'mp4', use_sponsorblock: bool = True, segment_types: Optional[List[str]] = None, progress_callback=None):
    # Extract video ID from URL
    video_id = extract_video_id(url)
    if not video_id:
        print("Invalid YouTube URL. Unable to extract video ID.")
        return None

    # Download the video
    print("Downloading video...")
    video_path = download_video(url, output_path, format, progress_callback=progress_callback)
    
    if not video_path:
        print("Failed to download the video.")
        return None

    # Get sponsor segments
    if use_sponsorblock:
        print("Fetching sponsor segments...")
        sponsor_segments = get_sponsor_segments(video_id, segment_types or [])
        print(sponsor_segments)
        if not sponsor_segments:
            print("No sponsor segments found. The video will remain unedited.")
    else:
        sponsor_segments = []
    
    # Cut the video
    if sponsor_segments:
        print("Cutting out sponsor segments...")
        temp_output_file = os.path.join(output_path, f"temp_{os.path.basename(video_path)}")
        
        if format.lower() == 'mp3':
            success = cut_segments_mp3(video_path, temp_output_file, sponsor_segments)
        elif format.lower() == 'mp4':
            success = cut_segments_mp4(video_path, temp_output_file, sponsor_segments)
        else:
            print(f"Unsupported format: {format}")
            return video_path
        
        if success:
            # Remove the original file and rename the processed file
            os.remove(video_path)
            os.rename(temp_output_file, video_path)
            print(f"Video processing complete. Output file: {video_path}")
            return video_path
        else:
            print("Failed to cut segments. The original video will be kept.")
            if os.path.exists(temp_output_file):
                os.remove(temp_output_file)
            return video_path
    else:
        print("No segments to cut. The original video will be kept.")
        return video_path

def extract_video_id(url: str) -> Optional[str]:
    # Regular expression to match YouTube video IDs
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


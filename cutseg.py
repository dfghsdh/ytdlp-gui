
import subprocess
from typing import List, Tuple

def cut_segments_mp3(input_file: str, output_file: str, segments_to_remove: List[Tuple[float, float]]) -> bool:
    """
    Cut out specific segments from an mp3 file using ffmpeg.

    Args:
        input_file (str): Path to the input file.
        output_file (str): Path to save the output file.
        segments_to_remove (List[Tuple[float, float]]): List of (start, end) timestamps to remove.

    Returns:
        bool: True if successful, False otherwise.
    """
    # Get the duration of the input file
    duration_cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        input_file
    ]
    try:
        duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
    except subprocess.CalledProcessError:
        print(f"Error: Unable to get duration of {input_file}")
        return False

    # Sort segments to remove and merge overlapping segments
    segments_to_remove.sort(key=lambda x: x[0])
    merged_segments = []
    for segment in segments_to_remove:
        if not merged_segments or segment[0] > merged_segments[-1][1]:
            merged_segments.append(segment)
        else:
            merged_segments[-1] = (merged_segments[-1][0], max(merged_segments[-1][1], segment[1]))

    # Calculate segments to keep
    segments_to_keep = []
    last_end = 0
    for start, end in merged_segments:
        if start > last_end:
            segments_to_keep.append((last_end, start))
        last_end = max(last_end, end)
    if last_end < duration:
        segments_to_keep.append((last_end, duration))

    # Prepare ffmpeg filter complex
    filter_complex = []
    for i, (seg_start, seg_end) in enumerate(segments_to_keep):
        filter_complex.append(f"[0:a]atrim=start={seg_start}:end={seg_end},asetpts=PTS-STARTPTS[a{i}]")

    if len(segments_to_keep) > 1:
        filter_complex.append(f"{''.join([f'[a{i}]' for i in range(len(segments_to_keep))])}concat=n={len(segments_to_keep)}:v=0:a=1[outa]")
    else:
        filter_complex.append(f"[a0]anull[outa]")

    filter_complex_str = ';'.join(filter_complex)

    # Prepare ffmpeg command
    command = [
        'ffmpeg',
        '-i', input_file,
        '-filter_complex', filter_complex_str,
        '-map', '[outa]',
        output_file
    ]

    # Execute ffmpeg command
    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE)
        print(f"Successfully cut segments and saved to {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while cutting segments: {e.stderr.decode()}")
        return False

def cut_segments_mp4(input_file: str, output_file: str, segments_to_remove: List[Tuple[float, float]]) -> bool:
    """
    Cut out specific segments from an mp4 file using ffmpeg.

    Args:
        input_file (str): Path to the input file.
        output_file (str): Path to save the output file.
        segments_to_remove (List[Tuple[float, float]]): List of (start, end) timestamps to remove.

    Returns:
        bool: True if successful, False otherwise.
    """
    # Get the duration of the input file
    duration_cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        input_file
    ]
    try:
        duration = float(subprocess.check_output(duration_cmd).decode('utf-8').strip())
    except subprocess.CalledProcessError:
        print(f"Error: Unable to get duration of {input_file}")
        return False

    # Sort segments to remove and merge overlapping segments
    segments_to_remove.sort(key=lambda x: x[0])
    merged_segments = []
    for segment in segments_to_remove:
        if not merged_segments or segment[0] > merged_segments[-1][1]:
            merged_segments.append(segment)
        else:
            merged_segments[-1] = (merged_segments[-1][0], max(merged_segments[-1][1], segment[1]))

    # Calculate segments to keep
    segments_to_keep = []
    last_end = 0
    for start, end in merged_segments:
        if start > last_end:
            segments_to_keep.append((last_end, start))
        last_end = max(last_end, end)
    if last_end < duration:
        segments_to_keep.append((last_end, duration))

    # Prepare ffmpeg filter complex
    filter_complex = []
    for i, (seg_start, seg_end) in enumerate(segments_to_keep):
        filter_complex.append(f"[0:v]trim=start={seg_start}:end={seg_end},setpts=PTS-STARTPTS[v{i}]")
        filter_complex.append(f"[0:a]atrim=start={seg_start}:end={seg_end},asetpts=PTS-STARTPTS[a{i}]")

    if len(segments_to_keep) > 1:
        filter_complex.append(f"{''.join([f'[v{i}]' for i in range(len(segments_to_keep))])}concat=n={len(segments_to_keep)}:v=1:a=0[outv]")
        filter_complex.append(f"{''.join([f'[a{i}]' for i in range(len(segments_to_keep))])}concat=n={len(segments_to_keep)}:v=0:a=1[outa]")
    else:
        filter_complex.append(f"[v0]null[outv]")
        filter_complex.append(f"[a0]anull[outa]")

    filter_complex_str = ';'.join(filter_complex)

    # Prepare ffmpeg command
    command = [
        'ffmpeg',
        '-i', input_file,
        '-filter_complex', filter_complex_str,
        '-map', '[outv]',
        '-map', '[outa]',
        output_file
    ]

    # Execute ffmpeg command
    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE)
        print(f"Successfully cut segments and saved to {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while cutting segments: {e.stderr.decode()}")
        return False

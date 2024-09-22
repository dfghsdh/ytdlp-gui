import sponsorblock as sb
from typing import List, Tuple

def get_sponsor_segments(video_id: str, segment_types: List[str] = ['sponsor']) -> List[Tuple[float, float]]:
    """
    Retrieves specified segment types for a given YouTube video ID using the SponsorBlock API.
    
    Args:
        video_id (str): The YouTube video ID.
        segment_types (List[str]): List of segment types to include. Default is ['sponsor'].
                                   Available types: sponsor, selfpromo, interaction, intro, outro,
                                   preview, music_offtopic, filler
    
    Returns:
        List[Tuple[float, float]]: A list of tuples containing start and end times of specified segments.
    """
    client = sb.Client()
    try:
        segments = client.get_skip_segments(video_id)
        return [(segment.start, segment.end) for segment in segments if segment.category in segment_types]
    except Exception as e:
        print(f"Error fetching sponsor segments: {e}")
        return []

# Example usage:
# print(get_sponsor_segments("UPrkC1LdlLY", ['sponsor', 'intro', 'outro']))
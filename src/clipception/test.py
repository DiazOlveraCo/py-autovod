import unittest
from typing import List, Dict, Tuple, Optional
import re

def parse_clip_data(input_string: str) -> List[Dict]:
    """Robust parser for LLM output with multiple format support."""
    if not input_string:
        return []

    # Normalize line endings and remove empty lines
    lines = [line.strip() for line in input_string.split('\n') if line.strip()]
    normalized_input = '\n'.join(lines)
    
    # Split into individual clip sections
    clip_sections = re.split(r'\d+\.\s*\*\*Clip Name:', normalized_input)
    clips = []

    for section in clip_sections:
        if not section.strip():
            continue

        clip = {}
        
        # Extract name (handle different quote styles)
        name_match = re.search(r'"(.*?)"', section)
        if name_match:
            clip['name'] = name_match.group(1)
        
        # Extract start/end times (handle various formats)
        time_match = re.search(
            r'Start:\s*([\d.]+)\s*s?[,]?\s*End:\s*([\d.]+)\s*s?',
            section, re.IGNORECASE
        )
        if time_match:
            clip['start'] = float(time_match.group(1))
            clip['end'] = float(time_match.group(2))
        
        # Extract score (handle different formats)
        score_match = re.search(r'Score:\s*(\d+)(?:\s*/\s*10)?', section, re.IGNORECASE)
        if score_match:
            clip['score'] = int(score_match.group(1))
        
        # Extract factors (handle multi-line)
        factors_match = re.search(
            r'Factors:\s*(.+?)(?=\n\s*(?:Platforms|Score|$))', 
            section, re.DOTALL | re.IGNORECASE
        )
        if factors_match:
            clip['factors'] = factors_match.group(1).strip()
        
        # Extract platforms (handle different separators)
        platforms_match = re.search(
            r'Platforms:\s*(.+?)(?=\n\s*(?:Factors|Score|$))', 
            section, re.DOTALL | re.IGNORECASE
        )
        if platforms_match:
            platforms = re.sub(r'\s+', ' ', platforms_match.group(1).strip())
            clip['platforms'] = [p.strip() for p in re.split(r'[,/]', platforms) if p.strip()]

        if clip:  # Only add if we found any data
            clips.append(clip)

    return clips

class TestClipParser(unittest.TestCase):
    """Unit tests for the clip parser."""
    
    def test_parser(self):
        test_input = """
        1. **Clip Name: "Exciting Moment"**
        Start: 12.3s, End: 24.5s
        Score: 9
        Factors: High energy, crowd reaction
        Platforms: TikTok, YouTube Shorts

        2. **Clip Name: "Controversial Statement"**
        Platforms: Twitter, Instagram
        Factors: Political content, strong opinions
        Score: 8/10
        Start: 45s End: 52s
        """

        expected = [
            {
                'name': 'Exciting Moment',
                'start': 12.3,
                'end': 24.5,
                'score': 9,
                'factors': 'High energy, crowd reaction',
                'platforms': ['TikTok', 'YouTube Shorts']
            },
            {
                'name': 'Controversial Statement',
                'start': 45.0,
                'end': 52.0,
                'score': 8,
                'factors': 'Political content, strong opinions',
                'platforms': ['Twitter', 'Instagram']
            }
        ]

        result = parse_clip_data(test_input)
        
        for i in range(2):
            for key in expected[i]:
                self.assertEqual(result[i][key], expected[i][key])
        self.assertEqual(True, False)

    def test_empty_input(self):
        self.assertEqual(parse_clip_data(""), [])

    def test_missing_fields(self):
        test_input = """
        1. **Clip Name: "Partial Clip"**
        Start: 10s, End: 20s
        Score: 5
        """
        result = parse_clip_data(test_input)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Partial Clip')
        self.assertNotIn('factors', result[0])


unittest.main(argv=[''], exit=False)

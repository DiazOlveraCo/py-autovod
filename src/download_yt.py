#!/usr/bin/env python3
"""
YouTube Video Downloader

This script downloads YouTube videos from a provided URL.
Usage: python download_yt.py [YouTube URL]
"""

import sys
import os
import argparse
from pathlib import Path

# Import yt-dlp here to avoid import error if not installed
try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp is not installed.")
    print("Please install it using: pip install yt-dlp")
    sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Download YouTube videos")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", help="Output directory", default="downloads")
    parser.add_argument(
        "-f", "--format", help="Video format (default: best)", default="best"
    )
    parser.add_argument(
        "-l", "--list-formats", action="store_true", 
        help="List available formats and exit"
    )
    parser.add_argument(
        "--cookies", help="Path to cookies file (Netscape format)",
        default=None
    )
    parser.add_argument(
        "--cookies-browser", help="Browser to extract cookies from",
        choices=["firefox", "chrome", "chromium", "edge", "safari"],
        default=None
    )
    return parser.parse_args()


def list_formats(url, ydl_opts):
    """List available formats for a video."""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            print(f"\nAvailable formats for: {info.get('title', 'Unknown')}")
            print("-" * 80)
            
            # Group formats by quality
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            
            if video_formats:
                print("\nVideo formats:")
                for f in sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True):
                    print(f"  {f['format_id']:>3} - {f.get('ext', 'unknown'):>4} "
                          f"{f.get('height', 'N/A'):>4}p "
                          f"{f.get('fps', 'N/A'):>3}fps "
                          f"{f.get('vcodec', 'unknown'):>15} "
                          f"{'[DRM]' if f.get('has_drm') else ''}")
            
            if audio_formats:
                print("\nAudio formats:")
                for f in sorted(audio_formats, key=lambda x: x.get('abr', 0), reverse=True):
                    print(f"  {f['format_id']:>3} - {f.get('ext', 'unknown'):>4} "
                          f"{f.get('abr', 'N/A'):>4}kbps "
                          f"{f.get('acodec', 'unknown'):>15}")
            
            return True
    except Exception as e:
        print(f"Error listing formats: {e}")
        return False


def download_video(url, output_dir, format_option, cookies_path=None, cookies_browser=None, list_only=False):
    """
    Args:
        url: YouTube video URL
        output_dir: Directory to save the downloaded video
        format_option: Video format option
        cookies_path: Path to cookies file
        cookies_browser: Browser to extract cookies from
        list_only: If True, only list formats without downloading

    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        # Configure yt-dlp options with multiple fallback strategies
        ydl_opts = {
            # Format selection with multiple fallbacks
            "format": (
                # Try best quality first
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/"
                # Fallback to webm if mp4 not available
                "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/"
                # Try any best video + audio
                "bestvideo+bestaudio/"
                # Fallback to best single file
                "best/"
                # Last resort - any available format
                "bestvideo*+bestaudio*/best*"
            ),
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",  # Ensures final output is MP4
            "quiet": False,
            "progress": True,
            "no_warnings": False,
            "restrictfilenames": True,  # Avoids special characters in filenames
            "retries": 10,             # Add retries and error handling
            "fragment_retries": 10,
            "skip_unavailable_fragments": True,
            # Extractor arguments to try different player clients
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android", "ios"], 
                    "player_skip": ["configs", "webpage"],    # Skip nsig extraction if it fails
                }
            },
            # Workarounds for common issues
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "no_color": False,
            # Add user agent to avoid detection
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Prefer free formats
            "prefer_free_formats": True,
            # Continue on download errors
            "continuedl": True,
            # Use aria2c for better download performance if available
            "external_downloader": {
                "default": "native",
                "dash": "native",
                "m3u8": "native"
            },
        }

        # Add cookies if provided
        if cookies_path:
            ydl_opts["cookiefile"] = cookies_path
        elif cookies_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_browser,)

        # If custom format specified, use it
        if format_option != "best":
            ydl_opts["format"] = format_option

        # List formats if requested
        if list_only:
            return list_formats(url, ydl_opts)

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading video from: {url}")
            print("Note: If you encounter format errors, try running with --list-formats to see available options")
            
            # Extract info first to check for issues
            try:
                info = ydl.extract_info(url, download=False)
                if info.get('is_live'):
                    print("Warning: This appears to be a live stream. Download may not work as expected.")
                
                # Check if DRM protected
                formats = info.get('formats', [])
                drm_formats = [f for f in formats if f.get('has_drm')]
                if drm_formats and len(drm_formats) == len(formats):
                    print("Warning: All formats appear to be DRM protected. Trying alternative methods...")
                    # Add additional fallback options for DRM content
                    ydl_opts["format"] = "best[height<=720]/best"
                    ydl_opts["allow_unplayable_formats"] = True
                
            except Exception as e:
                print(f"Warning during pre-check: {e}")
                print("Continuing with download attempt...")
            
            # Attempt download
            ydl.download([url])

        print(f"Video downloaded successfully to {output_dir}")
        return True

    except yt_dlp.utils.ExtractorError as e:
        error_msg = str(e)
        print(f"Extractor error: {error_msg}")
        
        # Provide specific guidance based on error
        if "format is not available" in error_msg:
            print("\nTip: Try one of these solutions:")
            print("1. Run with --list-formats to see available formats")
            print("2. Use --cookies-browser firefox (or chrome) if you're logged into YouTube")
            print("3. Try a specific format like: -f 'best[height<=720]'")
            print("4. Update yt-dlp: pip install -U yt-dlp")
        elif "DRM protected" in error_msg:
            print("\nThis video appears to be DRM protected. Try:")
            print("1. Using cookies from your browser: --cookies-browser firefox")
            print("2. Downloading a lower quality: -f 'best[height<=480]'")
        elif "nsig extraction failed" in error_msg:
            print("\nThere's an issue with YouTube's signature extraction. Try:")
            print("1. Updating yt-dlp: pip install -U yt-dlp")
            print("2. Using a different format")
        
        return False
        
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False


def main():
    args = parse_arguments()

    if not args.url.startswith(("http://", "https://")):
        print("Error: Please provide a valid URL starting with http:// or https://")
        sys.exit(1)

    # Download the video or list formats
    success = download_video(
        args.url, 
        args.output, 
        args.format,
        args.cookies,
        args.cookies_browser,
        args.list_formats
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

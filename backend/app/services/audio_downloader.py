"""
Audio Downloader Service
Downloads audio from ANY supported URL using yt-dlp.

Supported platforms (1000+):
- YouTube, YouTube Music
- Facebook, Instagram, TikTok
- Twitter/X, Vimeo, Dailymotion
- SoundCloud, Spotify (some)
- Direct MP3/MP4 links
- And many more...

Full list: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
"""

import os
import uuid
import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp

from app.config import TEMP_DIR


class AudioDownloadError(Exception):
    """Custom exception for audio download errors."""
    pass


def _get_ffmpeg_location() -> Optional[str]:
    """
    Find FFmpeg location on the system.
    
    Returns:
        Path to ffmpeg directory or None if not found
    """
    import shutil
    import subprocess
    
    # Try to find ffmpeg in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    
    # Common Windows installation paths
    common_paths = [
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links'),
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages'),
        r'C:\ffmpeg\bin',
        r'C:\Program Files\ffmpeg\bin',
        r'C:\Program Files (x86)\ffmpeg\bin',
        os.path.expanduser('~\\ffmpeg\\bin'),
        os.path.expanduser('~\\scoop\\shims'),
    ]
    
    for path in common_paths:
        ffmpeg_exe = os.path.join(path, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_exe):
            return path
    
    # Try to find in WinGet packages folder
    winget_packages = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages')
    if os.path.exists(winget_packages):
        for folder in os.listdir(winget_packages):
            if 'ffmpeg' in folder.lower():
                bin_path = os.path.join(winget_packages, folder, 'ffmpeg-*-full_build', 'bin')
                # Use glob to find the actual path
                import glob
                matches = glob.glob(os.path.join(winget_packages, folder, '*', 'bin', 'ffmpeg.exe'))
                if matches:
                    return os.path.dirname(matches[0])
    
    return None


def detect_platform(url: str) -> str:
    """
    Detect the platform from URL for logging/analytics.
    
    Args:
        url: The source URL
    
    Returns:
        Platform name string
    """
    url_lower = url.lower()
    
    patterns = {
        'youtube': r'(youtube\.com|youtu\.be)',
        'facebook': r'(facebook\.com|fb\.watch|fb\.com)',
        'instagram': r'instagram\.com',
        'tiktok': r'tiktok\.com',
        'twitter': r'(twitter\.com|x\.com)',
        'vimeo': r'vimeo\.com',
        'soundcloud': r'soundcloud\.com',
        'dailymotion': r'dailymotion\.com',
        'twitch': r'twitch\.tv',
        'reddit': r'reddit\.com',
        'bilibili': r'bilibili\.com',
    }
    
    for platform, pattern in patterns.items():
        if re.search(pattern, url_lower):
            return platform
    
    return 'other'


def get_platform_options(platform: str) -> Dict[str, Any]:
    """
    Get platform-specific yt-dlp options.
    
    Args:
        platform: Detected platform name
    
    Returns:
        Dictionary of yt-dlp options
    """
    base_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            # Lower quality to reduce file size for Cloudflare API (limit ~5MB recommended)
            'preferredquality': '64',
        }],
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': False,
        'no_color': True,
        # FFmpeg location - try common Windows paths
        'ffmpeg_location': _get_ffmpeg_location(),
        # Bypass geo-restrictions
        'geo_bypass': True,
        # Handle age-gated content
        'age_limit': None,
        # Retry on errors
        'retries': 3,
        'fragment_retries': 3,
    }
    
    # Platform-specific options
    if platform == 'instagram':
        base_opts.update({
            # Instagram may need these
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        })
    elif platform == 'facebook':
        base_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        })
    elif platform == 'tiktok':
        base_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        })
    elif platform == 'twitter':
        base_opts.update({
            # Twitter/X specific
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        })
    
    return base_opts


async def download_audio(
    url: str, 
    output_filename: Optional[str] = None,
    cookies_file: Optional[str] = None
) -> tuple[Path, Dict[str, Any]]:
    """
    Download audio from ANY URL and convert to MP3.
    
    Supports 1000+ sites including:
    - YouTube, Facebook, Instagram, TikTok
    - Twitter/X, Vimeo, SoundCloud
    - Direct links to MP3/MP4 files
    
    Args:
        url: The URL to download audio from.
        output_filename: Optional custom filename (without extension).
        cookies_file: Optional path to cookies.txt for private content.
    
    Returns:
        Tuple of (Path to MP3 file, metadata dict with platform info)
    
    Raises:
        AudioDownloadError: If download fails.
    """
    if not output_filename:
        output_filename = str(uuid.uuid4())
    
    output_path = TEMP_DIR / f"{output_filename}.mp3"
    
    # Detect platform
    platform = detect_platform(url)
    
    # Get platform-specific options
    ydl_opts = get_platform_options(platform)
    ydl_opts['outtmpl'] = str(TEMP_DIR / output_filename)
    
    # Add cookies if provided
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
    
    metadata = {
        'platform': platform,
        'url': url,
        'title': None,
        'duration': None,
        'uploader': None,
    }
    
    def _download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Extract metadata
                if info:
                    metadata['title'] = info.get('title', 'Unknown')
                    metadata['duration'] = info.get('duration', 0)
                    metadata['uploader'] = info.get('uploader', 'Unknown')
                    metadata['thumbnail'] = info.get('thumbnail')
                
                return info
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            
            # Provide helpful error messages
            if 'Private video' in error_msg:
                raise AudioDownloadError(
                    "Video is private. Please use a public video or provide cookies."
                )
            elif 'Sign in' in error_msg or 'login' in error_msg.lower():
                raise AudioDownloadError(
                    f"This {platform} content requires login. Please provide cookies."
                )
            elif 'not available' in error_msg.lower():
                raise AudioDownloadError(
                    f"Content not available. It may be geo-restricted or deleted."
                )
            else:
                raise AudioDownloadError(f"Download failed: {error_msg}")
        except Exception as e:
            raise AudioDownloadError(f"Failed to download audio: {str(e)}")
    
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _download)
    
    # Check if file exists (yt-dlp adds .mp3 extension)
    if not output_path.exists():
        # Try to find the downloaded file
        possible_paths = list(TEMP_DIR.glob(f"{output_filename}.*"))
        audio_extensions = ['.mp3', '.m4a', '.webm', '.opus', '.wav', '.aac']
        
        for ext in audio_extensions:
            test_path = TEMP_DIR / f"{output_filename}{ext}"
            if test_path.exists():
                output_path = test_path
                break
        else:
            if possible_paths:
                output_path = possible_paths[0]
            else:
                raise AudioDownloadError(
                    f"Downloaded file not found. Platform: {platform}"
                )
    
    return output_path, metadata


def cleanup_audio_file(file_path: Path) -> bool:
    """
    Clean up a downloaded audio file.
    
    Args:
        file_path: Path to the file to delete.
    
    Returns:
        True if file was deleted, False otherwise.
    """
    try:
        if file_path.exists():
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def get_supported_platforms() -> list[str]:
    """
    Get list of commonly supported platforms.
    
    Returns:
        List of platform names
    """
    return [
        'YouTube',
        'Facebook',
        'Instagram',
        'TikTok',
        'Twitter/X',
        'Vimeo',
        'SoundCloud',
        'Dailymotion',
        'Twitch',
        'Reddit',
        'Bilibili',
        'Direct MP3/MP4 links',
        '1000+ more sites',
    ]


async def download_video(
    url: str, 
    quality: str = "medium",
    format_id: Optional[str] = None,
    output_filename: Optional[str] = None
) -> tuple[Path, Dict[str, Any]]:
    """
    Download video from URL as MP4.
    
    Args:
        url: Video URL
        quality: Video quality (low, medium, high, best) - ignored if format_id provided
        format_id: Specific format ID from get_available_formats
        output_filename: Optional custom filename
    
    Returns:
        Tuple of (Path to MP4 file, metadata dict)
    """
    if not output_filename:
        output_filename = str(uuid.uuid4())
    
    output_path = TEMP_DIR / f"{output_filename}.mp4"
    platform = detect_platform(url)
    
    # For TikTok/Instagram/Facebook - use simpler format selection
    if platform in ['tiktok', 'instagram', 'facebook', 'twitter']:
        # These platforms often have limited formats
        if format_id:
            format_string = format_id
        else:
            # Use best available, let yt-dlp figure it out
            format_string = 'best'
    else:
        # YouTube and others support quality selection
        if format_id:
            format_string = format_id
        else:
            quality_map = {
                'low': 'worst[ext=mp4]/worst',
                'medium': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                'high': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                'best': 'bestvideo+bestaudio/best',
            }
            format_string = quality_map.get(quality, quality_map['medium'])
    
    ydl_opts = {
        'format': format_string,
        'outtmpl': str(TEMP_DIR / f"{output_filename}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': _get_ffmpeg_location(),
        'geo_bypass': True,
        'retries': 3,
        'merge_output_format': 'mp4',
    }
    
    # Add platform-specific headers
    if platform in ['instagram', 'facebook', 'tiktok', 'twitter']:
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    metadata = {
        'platform': platform,
        'url': url,
        'title': None,
        'duration': None,
        'quality': quality,
    }
    
    def _download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    metadata['title'] = info.get('title', 'video')
                    metadata['duration'] = info.get('duration', 0)
                return info
        except Exception as e:
            raise AudioDownloadError(f"Download failed: {str(e)}")
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _download)
    
    # Find the downloaded file
    if not output_path.exists():
        possible_paths = list(TEMP_DIR.glob(f"{output_filename}.*"))
        video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov']
        for ext in video_extensions:
            test_path = TEMP_DIR / f"{output_filename}{ext}"
            if test_path.exists():
                output_path = test_path
                break
        else:
            if possible_paths:
                output_path = possible_paths[0]
            else:
                raise AudioDownloadError("Downloaded file not found")
    
    return output_path, metadata


async def get_available_formats(url: str) -> Dict[str, Any]:
    """
    Get available download formats for a URL.
    
    Args:
        url: Video URL
    
    Returns:
        Dict with formats info including estimated file sizes
    """
    platform = detect_platform(url)
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    
    if platform in ['instagram', 'facebook', 'tiktok', 'twitter']:
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def _get_info():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            raise AudioDownloadError(f"Cannot get video info: {str(e)}")
    
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _get_info)
    
    if not info:
        raise AudioDownloadError("No video info found")
    
    # Parse formats
    formats = info.get('formats', [])
    duration = info.get('duration', 0)
    
    video_formats = []
    audio_formats = []
    
    for fmt in formats:
        format_id = fmt.get('format_id', '')
        ext = fmt.get('ext', '')
        filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
        
        # Calculate estimated size if not available
        if not filesize and duration:
            tbr = fmt.get('tbr', 0)  # Total bitrate in kbps
            if tbr:
                filesize = int(tbr * 1000 * duration / 8)
        
        format_info = {
            'format_id': format_id,
            'ext': ext,
            'filesize': filesize,
            'filesize_mb': round(filesize / 1024 / 1024, 2) if filesize else None,
        }
        
        # Check if video or audio only
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        height = fmt.get('height') or 0  # Ensure height is int, not None
        
        if vcodec != 'none' and vcodec:
            format_info['type'] = 'video'
            format_info['resolution'] = f"{fmt.get('width', '?')}x{height}" if height else 'unknown'
            format_info['height'] = height
            format_info['fps'] = fmt.get('fps', 0)
            format_info['vcodec'] = vcodec
            format_info['has_audio'] = acodec != 'none' and acodec
            video_formats.append(format_info)
        elif acodec != 'none' and acodec:
            format_info['type'] = 'audio'
            format_info['abr'] = fmt.get('abr', 0)  # Audio bitrate
            format_info['acodec'] = acodec
            audio_formats.append(format_info)
    
    # Sort by quality
    video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
    audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
    
    # Create simple options for UI
    simple_options = []
    
    # MP3 option (audio only)
    best_audio = audio_formats[0] if audio_formats else None
    audio_size = best_audio.get('filesize_mb') if best_audio else None
    # Estimate MP3 size from duration (64kbps = ~0.5MB per minute)
    if not audio_size and duration:
        audio_size = round(duration * 64 * 1000 / 8 / 1024 / 1024, 2)
    
    simple_options.append({
        'id': 'mp3',
        'label': 'MP3 (Audio)',
        'type': 'audio',
        'ext': 'mp3',
        'size_mb': audio_size,
    })
    
    # Video options - group by height
    heights_added = set()
    for vf in video_formats:
        height = vf.get('height', 0)
        if height and height not in heights_added and height >= 360:
            heights_added.add(height)
            
            # Find best format with audio for this height
            label = f"MP4 {height}p"
            if height >= 1080:
                label += " (HD)"
            elif height >= 720:
                label += " (HD)"
            
            simple_options.append({
                'id': f'video_{height}',
                'label': label,
                'type': 'video',
                'ext': 'mp4',
                'height': height,
                'size_mb': vf.get('filesize_mb'),
            })
    
    return {
        'platform': platform,
        'title': info.get('title', 'Unknown'),
        'duration': duration,
        'duration_str': f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else None,
        'thumbnail': info.get('thumbnail'),
        'options': simple_options,
        'video_formats': video_formats[:10],  # Limit to top 10
        'audio_formats': audio_formats[:5],
    }


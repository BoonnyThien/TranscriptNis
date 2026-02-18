"""
Transcription Service
Calls Cloudflare Workers AI (Whisper) to transcribe audio files.
Returns text with word-level timestamps and VTT format.
Handles large files by splitting them into chunks using FFmpeg.
"""

import httpx
import os
import subprocess
from pathlib import Path
from typing import Optional, List

from app.config import (
    CLOUDFLARE_ACCOUNT_ID, 
    CLOUDFLARE_API_TOKEN,
    WHISPER_MODEL,
)
from app.services.audio_downloader import _get_ffmpeg_location


class TranscriptionError(Exception):
    """Custom exception for transcription errors."""
    pass


def format_vtt_time(seconds: float) -> str:
    """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def generate_vtt(words: List[dict]) -> str:
    """
    Generate VTT subtitle format from word timestamps.
    Groups words into subtitle segments (~5 seconds each).
    """
    if not words:
        return ""
    
    vtt_lines = ["WEBVTT", ""]
    
    # Group words into segments
    segment_words = []
    segment_start = 0
    
    for word in words:
        if not segment_words:
            segment_start = word.get('start', 0)
        
        segment_words.append(word.get('word', ''))
        segment_end = word.get('end', segment_start + 5)
        
        # Create new segment every ~5 seconds or at sentence end
        word_text = word.get('word', '')
        is_sentence_end = word_text.endswith(('.', '!', '?', '。', '？', '！'))
        
        if segment_end - segment_start >= 5 or is_sentence_end:
            text = ' '.join(segment_words).strip()
            if text:
                vtt_lines.append(f"{format_vtt_time(segment_start)} --> {format_vtt_time(segment_end)}")
                vtt_lines.append(text)
                vtt_lines.append("")
            segment_words = []
    
    # Handle remaining words
    if segment_words:
        text = ' '.join(segment_words).strip()
        if text:
            end_time = words[-1].get('end', segment_start + 5) if words else segment_start + 5
            vtt_lines.append(f"{format_vtt_time(segment_start)} --> {format_vtt_time(end_time)}")
            vtt_lines.append(text)
            vtt_lines.append("")
    
    return '\n'.join(vtt_lines)


def format_text_with_timestamps(words: List[dict], text: str) -> str:
    """
    Format text with line breaks for better readability.
    Adds paragraph breaks at sentence endings.
    """
    if not text:
        return ""
    
    # If we have word timestamps, use them to add line breaks
    if words:
        lines = []
        current_line = []
        last_end = 0
        
        for word in words:
            word_text = word.get('word', '')
            start = word.get('start', last_end)
            
            current_line.append(word_text)
            
            # Check for sentence end or long pause (>1.5 seconds)
            is_sentence_end = word_text.rstrip().endswith(('.', '!', '?', '。', '？', '！', '…'))
            pause = start - last_end if last_end > 0 else 0
            
            if is_sentence_end or pause > 1.5:
                lines.append(' '.join(current_line).strip())
                current_line = []
            
            last_end = word.get('end', start + 0.5)
        
        if current_line:
            lines.append(' '.join(current_line).strip())
        
        return '\n'.join(filter(None, lines))
    
    # Fallback: just return original text with basic formatting
    import re
    # Add line breaks after sentences
    formatted = re.sub(r'([.!?。？！]) +', r'\1\n', text)
    return formatted


def split_audio_into_chunks(audio_path: Path, chunk_size_mb: int = 9) -> List[Path]:
    """
    Split audio file into smaller chunks using FFmpeg if it exceeds the size limit.
    Target size slightly less than 10MB to be safe.
    """
    try:
        file_size = audio_path.stat().st_size
        
        # If file is small enough, return as single chunk
        if file_size <= chunk_size_mb * 1024 * 1024:
            return [audio_path]
        
        print(f"[DEBUG] File size {file_size/1024/1024:.2f}MB exceeds limit. Splitting...")
        
        # Calculate duration to estimate splitting
        ffmpeg_cmd = _get_ffmpeg_location() or 'ffmpeg'
        if ffmpeg_cmd != 'ffmpeg':
            ffmpeg_cmd = str(Path(ffmpeg_cmd) / 'ffmpeg.exe')

        # Split strategy
        segment_time = 300  # 5 minutes
        
        output_pattern = str(audio_path.parent / f"{audio_path.stem}_chunk_%03d{audio_path.suffix}")
        
        cmd = [
            ffmpeg_cmd, '-i', str(audio_path),
            '-f', 'segment',
            '-segment_time', str(segment_time),
            '-c', 'copy',
            output_pattern
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        # Find generated chunks
        chunks = []
        for chunk in sorted(audio_path.parent.glob(f"{audio_path.stem}_chunk_*{audio_path.suffix}")):
            chunks.append(chunk)
            
        if not chunks:
            # Maybe failed to generate pattern?
            return [audio_path]
            
        print(f"[DEBUG] Split into {len(chunks)} chunks.")
        return chunks
        
    except Exception as e:
        print(f"[ERROR] Error splitting audio: {e}")
        # Fallback to single file if split fails
        return [audio_path]


async def process_single_chunk(
    chunk_path: Path, 
    language: Optional[str]
) -> dict:
    """Helper to process a single audio chunk."""
    try:
        with open(chunk_path, 'rb') as f:
            audio_data = f.read()
    except Exception as e:
        raise TranscriptionError(f"Failed to read audio chunk: {str(e)}")
    
    audio_array = list(audio_data)
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{WHISPER_MODEL}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json={"audio": audio_array},
            )
            
            result = response.json()
            
            if response.status_code != 200:
                print(f"[ERROR] API Error for chunk {chunk_path.name}: {response.status_code}")
                # Don't raise error, just return empty so other chunks can proceed
                return {'text': '', 'words': []}
                
            if not result.get('success'):
                print(f"[ERROR] API Success=False for chunk {chunk_path.name}")
                return {'text': '', 'words': []}
                
            return result.get('result', {})
            
    except Exception as e:
        print(f"[ERROR] Exception processing chunk {chunk_path.name}: {e}")
        return {'text': '', 'words': []}


async def transcribe_audio(
    audio_path: Path,
    language: Optional[str] = None,
    include_timestamps: bool = True
) -> dict:
    """
    Transcribe an audio file using Cloudflare Workers AI (Whisper).
    Handles large files by splitting them into chunks.
    
    Args:
        audio_path: Path to the audio file
        language: Optional language hint
        include_timestamps: Whether to include timestamps
    
    Returns:
        Dictionary with transcription results
    """
    if not audio_path.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")
    
    # Split audio if needed
    chunks = split_audio_into_chunks(audio_path)
    
    all_words = []
    full_text_parts = []
    time_offset = 0.0
    detected_language = language or 'unknown'
    
    # Process chunks sequence
    for i, chunk in enumerate(chunks):
        print(f"Transferring chunk {i+1}/{len(chunks)}...")
        
        # Process chunk
        result = await process_single_chunk(chunk, language)
        
        chunk_text = result.get('text', '')
        chunk_words = result.get('words', [])
        
        if chunk_text:
            full_text_parts.append(chunk_text)
        
        # Adjust timestamps
        if chunk_words:
            last_word_end = time_offset
            for word in chunk_words:
                start = word.get('start')
                end = word.get('end')
                
                # Check if start/end are valid numbers
                if start is not None and isinstance(start, (int, float)):
                    word['start'] = start + time_offset
                else:
                    word['start'] = last_word_end
                
                if end is not None and isinstance(end, (int, float)):
                    word['end'] = end + time_offset
                    last_word_end = word['end']
                else:
                    word['end'] = word['start'] + 0.1 # Fallback
                    last_word_end = word['end']
                
                all_words.append(word)
            
            # Update offset for next chunk
            time_offset = last_word_end
        else:
            # If no words detected in this chunk, add approximate duration
            # Default segment time is 300s (5m)
            time_offset += 300.0
        
        # Detect language from first chunk if not set
        if i == 0 and not language:
            detected_language = result.get('language', 'unknown')

        # Clean up chunk if it's not the original file
        if chunk != audio_path:
            try:
                os.remove(chunk)
            except:
                pass

    full_text_raw = " ".join(full_text_parts)
    formatted_text = format_text_with_timestamps(all_words, full_text_raw)
    vtt = generate_vtt(all_words)
    
    return {
        'text': formatted_text,
        'text_raw': full_text_raw,
        'word_count': len(full_text_raw.split()),
        'language': detected_language,
        'words': all_words,
        'vtt': vtt,
    }

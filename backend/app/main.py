"""
Universal Transcription API v3.0
- Multi-platform support (YouTube, Facebook, Instagram, TikTok, etc.)
- File upload support
- Video/Audio download
- Real-time progress (coming soon with WebSocket)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import time
import uuid
import os
import asyncio
from pathlib import Path

from app.config import validate_config, CLOUDFLARE_ACCOUNT_ID, TEMP_DIR
from app.services.audio_downloader import (
    download_audio,
    download_video,
    cleanup_audio_file,
    AudioDownloadError,
    get_supported_platforms,
    get_available_formats,
)
from app.services.transcription import (
    transcribe_audio,
    TranscriptionError,
)

# Store active jobs for progress tracking and cancellation
active_jobs = {}

# Initialize FastAPI app
app = FastAPI(
    title="Transcript AI API",
    description="""
## 🎙️ Universal Transcription API v3.0

**Tính năng mới:**
- 📤 Upload file từ máy tính
- 📥 Tải video MP4 / audio MP3
- 🌍 Hỗ trợ 1000+ nguồn video/audio
- 🔄 Theo dõi tiến trình real-time

### Nguồn hỗ trợ
YouTube, Facebook, Instagram, TikTok, Twitter/X, Vimeo, SoundCloud, và 1000+ nguồn khác.
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class TranscribeRequest(BaseModel):
    url: str
    language: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=ZXsQAXx_ao0",
                "language": "en"
            }
        }


class TranscribeResponse(BaseModel):
    success: bool
    text: str
    text_raw: Optional[str] = None  # Original text without formatting
    word_count: int
    language: str
    processing_time: float
    platform: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    message: Optional[str] = None
    job_id: Optional[str] = None
    vtt: Optional[str] = None  # VTT subtitle format
    words: Optional[List[dict]] = None  # Word-level timestamps


class DownloadRequest(BaseModel):
    url: str
    format: str = "mp3"  # mp3, mp4
    quality: str = "medium"  # low, medium, high, best
    format_id: Optional[str] = None  # Specific video format ID


class FormatsRequest(BaseModel):
    url: str


class FormatsResponse(BaseModel):
    platform: str
    title: str
    duration: float
    duration_str: Optional[str]
    thumbnail: Optional[str]
    options: List[dict]



class HealthResponse(BaseModel):
    status: str
    cloudflare_configured: bool
    version: str
    supported_platforms: List[str]


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, downloading, transcribing, completed, failed, cancelled
    progress: int  # 0-100
    message: str
    result: Optional[dict] = None


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check với danh sách platforms."""
    return HealthResponse(
        status="healthy",
        cloudflare_configured=bool(CLOUDFLARE_ACCOUNT_ID),
        version="3.0.0",
        supported_platforms=get_supported_platforms()
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    return await health_check()


@app.get("/platforms")
async def list_platforms():
    """Danh sách các nền tảng được hỗ trợ."""
    return {
        "platforms": get_supported_platforms(),
        "note": "yt-dlp hỗ trợ 1000+ nguồn. Một số Facebook Reels có thể không hoạt động do format mới."
    }


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: TranscribeRequest,
    background_tasks: BackgroundTasks
):
    """
    Transcribe audio từ URL.
    
    **Lưu ý về ngôn ngữ:**
    - Tham số `language` là GỢI Ý cho Whisper, không phải dịch tự động
    - Nếu không chọn, Whisper sẽ tự đoán ngôn ngữ
    - Chọn đúng ngôn ngữ giúp transcription chính xác hơn
    
    **Lưu ý về nhạc:**
    - Whisper chỉ nhận dạng LỜI NÓI, không phải lyrics bài hát
    - Video có nhạc sẽ hiển thị [Music] hoặc bỏ qua
    """
    start_time = time.time()
    job_id = str(uuid.uuid4())[:8]
    audio_path = None
    metadata = {}
    
    try:
        validate_config()
        
        # Download audio
        try:
            audio_path, metadata = await download_audio(request.url)
        except AudioDownloadError as e:
            error_msg = str(e)
            # Provide helpful error for Facebook Reels
            if 'facebook' in request.url.lower() and 'Cannot parse' in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Facebook Reels format không được hỗ trợ. Thử dùng link video thường (facebook.com/watch/...)"
                )
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Transcribe
        try:
            result = await transcribe_audio(audio_path, language=request.language)
        except TranscriptionError as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        processing_time = time.time() - start_time
        
        if audio_path:
            background_tasks.add_task(cleanup_audio_file, audio_path)
        
        return TranscribeResponse(
            success=True,
            text=result['text'],
            text_raw=result.get('text_raw'),
            word_count=result['word_count'],
            language=result['language'],
            processing_time=round(processing_time, 2),
            platform=metadata.get('platform', 'unknown'),
            title=metadata.get('title'),
            duration=metadata.get('duration'),
            message=f"Transcription hoàn thành từ {metadata.get('platform', 'unknown').title()}",
            job_id=job_id,
            vtt=result.get('vtt'),
            words=result.get('words'),
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cấu hình: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi không mong đợi: {str(e)}")
    finally:
        if audio_path and audio_path.exists():
            background_tasks.add_task(cleanup_audio_file, audio_path)


@app.post("/transcribe/upload", response_model=TranscribeResponse)
async def transcribe_upload(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    Transcribe từ file upload (MP3, MP4, WAV, M4A, WebM).
    
    Hỗ trợ:
    - Kéo thả file
    - Chọn file từ máy
    - Tối đa 25MB
    """
    start_time = time.time()
    job_id = str(uuid.uuid4())[:8]
    
    # Validate file type
    allowed_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 
                     'audio/webm', 'video/mp4', 'video/webm', 'audio/mp4']
    allowed_extensions = ['.mp3', '.mp4', '.wav', '.m4a', '.webm', '.ogg']
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type không hỗ trợ. Chấp nhận: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    temp_path = TEMP_DIR / f"{job_id}_{file.filename}"
    try:
        content = await file.read()
        
        # Check file size (25MB limit)
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File quá lớn. Tối đa 25MB.")
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Transcribe
        validate_config()
        result = await transcribe_audio(temp_path, language=language)
        
        processing_time = time.time() - start_time
        
        return TranscribeResponse(
            success=True,
            text=result['text'],
            text_raw=result.get('text_raw'),
            word_count=result['word_count'],
            language=result['language'],
            processing_time=round(processing_time, 2),
            platform="upload",
            title=file.filename,
            message="Transcription hoàn thành từ file upload",
            job_id=job_id,
            vtt=result.get('vtt'),
            words=result.get('words'),
        )
        
    except HTTPException:
        raise
    except TranscriptionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")
    finally:
        if temp_path.exists():
            os.remove(temp_path)


@app.post("/formats", response_model=FormatsResponse)
async def get_formats(request: FormatsRequest):
    """Lấy danh sách định dạng video có thể tải."""
    try:
        return await get_available_formats(request.url)
    except AudioDownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def download_media(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Tải video/audio từ URL.
    """
    try:
        if request.format == "mp3":
            file_path, metadata = await download_audio(request.url)
        else:
            file_path, metadata = await download_video(
                request.url, 
                quality=request.quality,
                format_id=request.format_id
            )
        
        filename = f"{metadata.get('title', 'video')[:50]}.{request.format}"
        # Clean filename
        filename = "".join(c for c in filename if c.isalnum() or c in ' .-_').strip()
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='audio/mpeg' if request.format == 'mp3' else 'video/mp4',
            background=background_tasks
        )
        
    except AudioDownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
async def get_info():
    """Thông tin về API và giới hạn."""
    return {
        "version": "3.0.0",
        "limits": {
            "max_file_size_mb": 25,
            "max_video_duration_minutes": 30,
            "supported_audio_formats": ["mp3", "wav", "m4a", "webm", "ogg"],
            "supported_video_formats": ["mp4", "webm"],
        },
        "notes": {
            "language": "Tham số language là GỢI Ý cho Whisper, không phải dịch tự động",
            "music": "Whisper chỉ nhận dạng lời nói, không nhận dạng lyrics bài hát",
            "facebook_reels": "Một số Facebook Reels có format mới chưa được hỗ trợ"
        }
    }


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

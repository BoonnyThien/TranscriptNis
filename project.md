# 🎙️ Transcript AI v3.1 - Universal Video/Audio Transcription

## Mô tả
Ứng dụng web chuyển đổi video/audio từ **BẤT KỲ NGUỒN NÀO** thành văn bản sử dụng Cloudflare Workers AI (Whisper).

## ✨ Tính năng mới v3.1 (LATEST)
- ✅ **Auto-Chunking (Cắt/Gộp tự động)** - Xử lý video dài/lớn không lo giới hạn Cloudflare (Tự động cắt nhỏ 5p và gộp kết quả)
- ✅ **Timestamps (Mốc thời gian)** - Trả về mốc thời gian chi tiết từng từ, hỗ trợ xuất file .vtt
- ✅ **Download Video Nâng Cao** - Xem danh sách định dạng có sẵn và kích thước ước tính trước khi tải
- ✅ **Fix Crash FB/TikTok** - Ổn định hóa logic sắp xếp định dạng và xử lý link chia sẻ mới nhất
- ✅ **Upload file từ máy tính** - Kéo thả hoặc chọn file (max 25MB)
- ✅ **Timer hiển thị** - Xem thời gian xử lý real-time
- ✅ **Hỗ trợ 12+ ngôn ngữ** - Giúp Whisper nhận dạng chính xác hơn

## 🌐 Nguồn được hỗ trợ
- ✅ **YouTube** (youtube.com, youtu.be)
- ✅ **Facebook** (video thường - /watch/, /share/v/)
- ✅ **Instagram** (Reels, Stories, Posts)
- ✅ **TikTok** (tiktok.com)
- ✅ **Twitter/X** (twitter.com, x.com)
- ✅ **Vimeo, SoundCloud, Dailymotion**
- ✅ **Direct links** (MP3, MP4, WAV, etc.)
- ✅ **1000+ nguồn khác** (powered by yt-dlp)

⚠️ **Lưu ý**: Một số Facebook Reels (`/share/r/...`) có format mới chưa được hỗ trợ

## Tech Stack
- **Backend**: FastAPI + yt-dlp + Cloudflare AI (Whisper)
- **Frontend**: Vue 3 + Vite + Tailwind CSS

---

## 📌 GHI NHỚ QUAN TRỌNG

### 🗣️ Về ngôn ngữ (Language)
- Tham số `language` là **GỢI Ý** cho Whisper
- **KHÔNG phải dịch tự động** sang ngôn ngữ khác
- Chọn đúng ngôn ngữ → nhận dạng chính xác hơn
- Không chọn → Whisper tự đoán (có thể sai)

### 🎵 Về nhạc (Music)
- Whisper chỉ nhận dạng **LỜI NÓI**
- **KHÔNG nhận lyrics bài hát**
- Video có nhạc → output `[Music]` hoặc bỏ qua
- Cần lyrics → dùng service khác (Shazam API)

---

## 🚀 Cách chạy

```powershell
# 1. Backend
cd "d:\Clone Voice\Transcript\backend"
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8888

# 2. Frontend (terminal mới)
cd "d:\Clone Voice\Transcript\frontend"
npm run dev
```

**Mở**: http://localhost:5173

---

## 📝 API Endpoints (v3.0)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Health check + platforms |
| GET | `/info` | Thông tin API và giới hạn |
| POST | `/formats` | Quét định dạng video/audio có sẵn |
| POST | `/transcribe` | Transcribe + Timestamps từ URL |
| POST | `/transcribe/upload` | Transcribe từ file upload |
| POST | `/download` | Tải video/audio (MP4/MP3) |

---

## 🔧 Checklist hoàn thành

### ✅ Giai đoạn 1: Backend Core
- [x] Setup Python env + FFmpeg
- [x] Hàm `download_audio` (yt-dlp)
- [x] Hàm `transcribe_audio` (Cloudflare Whisper)
- [x] API endpoint `/transcribe`

### ✅ Giai đoạn 2: Frontend  
- [x] Vue 3 + Vite + Tailwind
- [x] UI với URL input, language select
- [x] Loading state + Error handling
- [x] Copy to clipboard

### ✅ Giai đoạn 3: Tinh chỉnh
- [x] Đa ngôn ngữ (12+)
- [x] Dockerfile
- [x] README.md

### ✅ Giai đoạn 4: Đa nền tảng (v2.0)
- [x] Multi-platform support
- [x] Auto-detect platform
- [x] Platform icons

### ✅ Giai đoạn 5: Nâng cao (v3.0)
- [x] Upload file từ máy
- [x] Kéo thả (drag & drop)
- [x] Download video MP4
- [x] Download audio MP3
- [x] Timer hiển thị

### ✅ Giai đoạn 6: Hoàn thiện (v3.1)
- [x] Mốc thời gian (Timestamps)
- [x] Auto-Chunking (Cắt/Gộp file lớn)
- [x] Scan format trước khi tải
- [x] Fix lỗi sort NoneType (Facebook)

### 🔲 Tiếp theo (Optional)
- [ ] WebSocket cho real-time progress
- [ ] Cancel/pause transcription
- [ ] Batch processing (nhiều URLs)
- [ ] Export PDF/DOCX/SRT
- [ ] Authentication (JWT)

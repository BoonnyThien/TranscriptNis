# 🎙️ Transcript AI

<div align="center">

![Transcript AI](https://img.shields.io/badge/Transcript-AI-6366f1?style=for-the-badge&logo=openai&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare_AI-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)

**Chuyển đổi video YouTube thành văn bản với sức mạnh AI**

[Demo](#demo) • [Tính năng](#-tính-năng) • [Cài đặt](#-cài-đặt) • [Sử dụng](#-sử-dụng) • [API](#-api-documentation)

</div>

---

## ✨ Tính năng

- 🎬 **YouTube Transcription** - Paste link YouTube, nhận text
- 🌍 **Đa ngôn ngữ** - Hỗ trợ English, Tiếng Việt, 日本語, 한국어, và nhiều ngôn ngữ khác
- ⚡ **Nhanh chóng** - Powered by Cloudflare Workers AI (Whisper)
- 📋 **Copy to Clipboard** - Một click để copy kết quả
- 🎨 **UI đẹp** - Glassmorphism, dark theme, responsive
- 🐳 **Docker Ready** - Dễ dàng deploy với Docker

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **yt-dlp** - Download audio từ YouTube  
- **Cloudflare Workers AI** - Whisper model để transcribe
- **httpx** - Async HTTP client

### Frontend
- **Vue 3** - Composition API
- **Vite** - Lightning fast dev server
- **Tailwind CSS** - Utility-first CSS

---

## 📦 Cài đặt

### Prerequisites
- Python 3.11+
- Node.js 18+
- FFmpeg (cho yt-dlp)
- Cloudflare account

### 1. Clone repo

```bash
git clone https://github.com/your-username/transcript-ai.git
cd transcript-ai
```

### 2. Setup Backend

```bash
cd backend

# Tạo virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Cài dependencies
pip install -r requirements.txt

# Cấu hình Cloudflare
copy .env.example .env
```

#### Lấy Cloudflare credentials:

1. Đăng nhập [Cloudflare Dashboard](https://dash.cloudflare.com)
2. **Account ID**: Home → Workers & Pages → Overview (bên phải)
3. **API Token**: 
   - My Profile → API Tokens → Create Token
   - Chọn template "Workers AI (Read)"
   - Create Token và copy

4. Edit `.env`:
```env
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
```

### 3. Setup Frontend

```bash
cd frontend
npm install
```

---

## 🚀 Chạy ứng dụng

### Development

**Terminal 1 - Backend:**
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8888
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Truy cập: http://localhost:5173

### Docker (Production)

```bash
# Build và chạy
docker-compose up -d

# Xem logs
docker-compose logs -f
```

### Deploy to Cloudflare Pages (Recommended)

#### Frontend Deployment (Cloudflare Pages)

1. **Prepare your repository**
   ```bash
   git push origin main
   ```

2. **Connect to Cloudflare Pages**
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Pages → Create a project → Connect to Git
   - Select your repository
   - Build settings:
     - **Framework**: Vue (Vite)
     - **Build command**: `npm run build`
     - **Build output directory**: `frontend/dist`
     - **Root directory**: `/`

3. **Set environment variables** (if needed)
   - Add `VITE_API_URL` = your backend URL

4. **Deploy**
   - Choose production branch: `main`
   - Cloudflare will auto-deploy on push

#### Backend Deployment (Option 1: Separate Hosting)

For FastAPI backend, you can deploy to:
- **Railway.app** - Free tier available
- **Render.com** - Easy Python deployment
- **PythonAnywhere** - Python-specific hosting
- **Your own VPS** with Docker

Update your frontend to point to the backend API:
```env
VITE_API_URL=https://your-backend-domain.com
```

#### Backend Deployment (Option 2: Cloudflare Workers)

If you want to convert FastAPI to Cloudflare Workers:
```bash
npm install -g wrangler
wrangler deploy
```

(This requires converting Python to JavaScript/TypeScript first)

---

## 🎮 Sử dụng

1. Paste URL YouTube vào ô input
2. (Tùy chọn) Chọn ngôn ngữ
3. Click "Transcribe"
4. Đợi xử lý (có thể mất 1-3 phút tùy độ dài video)
5. Copy kết quả

### Ví dụ URLs được hỗ trợ:
- `https://www.youtube.com/watch?v=xxxxx`
- `https://youtu.be/xxxxx`
- Các nguồn khác do yt-dlp hỗ trợ

---

## 📖 API Documentation

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "cloudflare_configured": true,
  "version": "1.0.0"
}
```

### Transcribe
```http
POST /transcribe
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=...",
  "language": "vi"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "text": "Transcribed text here...",
  "word_count": 150,
  "language": "vi",
  "processing_time": 12.5,
  "message": "Transcription completed successfully"
}
```

Swagger UI: http://localhost:8888/docs

---

## 📁 Cấu trúc dự án

```
transcript-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   └── services/
│   │       ├── audio_downloader.py
│   │       └── transcription.py
│   ├── temp/
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## 🔧 Troubleshooting

### Lỗi "Failed to download audio"
- Kiểm tra URL có hợp lệ không
- Video có thể bị restricted hoặc private
- Thử update yt-dlp: `pip install -U yt-dlp`

### Lỗi "Configuration error"
- Kiểm tra `.env` đã có đủ credentials
- Verify API token có quyền Workers AI

### Lỗi "Request timed out"
- Video quá dài (>30 phút có thể mất nhiều thời gian)
- Thử với video ngắn hơn

---

## 📄 License

MIT License - feel free to use and modify!

---

<div align="center">

Made with ❤️ using Cloudflare Workers AI

</div>

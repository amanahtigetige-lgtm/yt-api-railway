import os, random, time
from flask import Flask, request, jsonify, send_from_directory
from pytubefix import YouTube
import yt_dlp

app = Flask(__name__)

# folder simpan hasil unduhan
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def is_tiktok_url(url: str) -> bool:
    return "tiktok.com" in url

def download_tiktok_video(url: str):
    rand_num = random.randint(10000, 99999)
    filename_base = f'daritiktok_{rand_num}'
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{filename_base}.%(ext)s'),
        'format': 'best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'nocheckcertificate': True,
        'force_overwrite': True,
        'headers': {'User-Agent': 'Mozilla/5.0'}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'TikTok Video')
        ext = info.get('ext', 'mp4')
        path = os.path.join(DOWNLOAD_DIR, f'{filename_base}.{ext}')
        os.utime(path, (time.time(), time.time()))
        return title, path

def download_youtube_video(url: str, audio_only: bool = False):
    yt = YouTube(url)
    title = yt.title
    if audio_only:
        # catatan: ini TIDAK transcode ke mp3, hanya rename sesuai kode awal Anda
        stream = yt.streams.filter(only_audio=True).first()
        out_file = stream.download(output_path=DOWNLOAD_DIR)
        base, _ = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
        return title, new_file
    else:
        stream = yt.streams.get_highest_resolution()
        path = stream.download(output_path=DOWNLOAD_DIR)
        return title, path

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    audio_only = bool(data.get("audio_only", False))

    if not url:
        return jsonify({"error": "url is required"}), 400

    try:
        if is_tiktok_url(url):
            title, path = download_tiktok_video(url)
        else:
            title, path = download_youtube_video(url, audio_only)

        file_name = os.path.basename(path)
        file_url = f"{request.host_url.rstrip('/')}/files/{file_name}"
        return jsonify({"title": title, "filename": file_name, "file_url": file_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    # kirim file sebagai attachment agar bisa diunduh dari WP
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

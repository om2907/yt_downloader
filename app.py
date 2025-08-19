import streamlit as st
import yt_dlp
from pathlib import Path
import os

st.set_page_config(page_title="YouTube Downloader", layout="centered")
st.title("🎥 YouTube Video & Audio Downloader")

# --- Input ---
url = st.text_input("Enter YouTube URL:")

mode = st.radio("Select Download Mode:", ["Video", "Audio Only"])

if mode == "Video":
    quality = st.selectbox("Select Video Quality:", ["360p", "480p", "720p", "1080p", "1440p", "2160p"])
    save_path = st.text_input("Save Folder:", "downloads/video")
else:
    codec = st.selectbox("Audio Codec:", ["mp3", "m4a"])
    bitrate = st.selectbox("Bitrate (kbps):", ["128", "192", "320"])
    save_path = st.text_input("Save Folder:", "downloads/audio")

# --- Progress Hooks ---
def make_progress_hook(progress_bar, status_placeholder):
    def hook(d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total and total > 0:
                progress = min(1.0, downloaded / total)
                try:
                    progress_bar.progress(progress)
                except Exception:
                    pass
                percent = int(progress * 100)
                speed = d.get("speed")
                eta = d.get("eta")
                status_placeholder.markdown(
                    f"**Downloading**: {d.get('filename','')[:80]}  \n"
                    f"Progress: **{percent}%** — ETA: **{eta}s** — Speed: **{speed or 'N/A'} B/s**"
                )
        elif status == "finished":
            try:
                progress_bar.progress(1.0)
            except Exception:
                pass
            status_placeholder.markdown("**Download finished — post-processing if needed...**")
        elif status == "error":
            status_placeholder.error("Error during download")
    return hook

# --- Download Functions ---
def download_video_streamlit(url, quality_label, save_path, hook):
    Path(save_path).mkdir(parents=True, exist_ok=True)

    # Map to yt-dlp format
    resolution_map = {
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
        "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    }
    ydl_opts = {
        "format": resolution_map.get(quality_label, "best"),
        "outtmpl": str(Path(save_path) / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "progress_hooks": [hook],
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        },
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_audio_streamlit(url, codec, bitrate_kbps, save_path, hook):
    Path(save_path).mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(Path(save_path) / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [hook],
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
            "preferredquality": str(bitrate_kbps),
        }],
        "quiet": True,
        "no_warnings": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# --- Start Download Button ---
start = st.button("Start Download")

if start:
    if not url:
        st.error("Please enter a valid YouTube URL")
    else:
        progress_bar = st.progress(0.0)
        status = st.empty()
        hook = make_progress_hook(progress_bar, status)

        try:
            if mode == "Video":
                download_video_streamlit(url, quality, save_path, hook)
            else:
                download_audio_streamlit(url, codec, int(bitrate), save_path, hook)
            status.success("✅ Download and post-processing completed!")
        except Exception as e:
            st.exception(e)

# --- Show Downloaded Files ---
if save_path:
    p = Path(save_path)
    if p.exists() and any(p.iterdir()):
        st.subheader("Files in save folder:")
        for f in sorted(p.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file():
                size_mb = f.stat().st_size / (1024*1024)
                c1, c2 = st.columns([6,1])
                c1.write(f"{f.name} — {size_mb:.2f} MB")
                if size_mb <= 200:
                    with open(f, "rb") as fh:
                        data = fh.read()
                    c2.download_button("Download", data=data, file_name=f.name)
                else:
                    c2.write("Large file")
    else:
        st.info(f"No files found yet in: {save_path}")

st.markdown("---")
st.markdown("**Notes:** ffmpeg must be installed locally for audio extraction or merging video+audio. Streamlit Cloud provides ffmpeg via packages.txt.")

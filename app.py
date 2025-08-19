"""
Streamlit YouTube downloader using yt-dlp

Requirements:
    pip install streamlit yt-dlp
    Install ffmpeg and add to PATH (Windows: https://www.gyan.dev/ffmpeg/builds/)

Run:
    streamlit run streamlit_yt_downloader.py

This app lets you:
 - Enter a YouTube URL
 - Choose Video (quality selection) or Audio-only (mp3/m4a + bitrate)
 - See live progress and post-processing status
 - After completion, view files in the save folder and (for smaller files) download them from the UI

"""

import streamlit as st
import yt_dlp
from pathlib import Path
import os
from typing import Optional


def build_video_format(height: Optional[int]) -> str:
    if height is None:  # "Best" quality
        return (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
            "best[ext=mp4]/"
            "bestvideo+bestaudio/"
            "best"
        )
    return (
        f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/"
        f"best[ext=mp4][height<={height}]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}]"
    )


def make_progress_hook(progress_bar, status_placeholder):
    """Return a yt-dlp progress hook that updates the given Streamlit widgets."""

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
                    # progress bar can sometimes error if the UI is closed
                    pass
                percent = int(progress * 100)
                speed = d.get("speed")
                eta = d.get("eta")
                status_placeholder.markdown(
                    f"**Downloading**: {d.get('filename','')[:80]}  "
                    f"Progress: **{percent}%** — ETA: **{eta}s** — Speed: **{speed or 'N/A'} B/s**"
                )
            else:
                status_placeholder.markdown(
                    f"**Downloading**: {d.get('filename','')} — {downloaded} bytes"
                )
        elif status == "finished":
            # finished downloading, now post-processing
            try:
                progress_bar.progress(1.0)
            except Exception:
                pass
            status_placeholder.markdown("**Download finished — now post-processing (merging/converting)...)**")
        elif status == "error":
            status_placeholder.error("yt-dlp reported an error")

    return hook


def download_video_streamlit(url: str, quality_label: str, save_path: str, hook):
    Path(save_path).mkdir(parents=True, exist_ok=True)

    heights = {
        "best": None,
        "2160p": 2160,
        "1440p": 1440,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
    }
    height = heights.get(quality_label.lower(), None)

    ydl_opts = {
        "outtmpl": str(Path(save_path) / "%(title).200B [%(id)s].%(ext)s"),
        "format": build_video_format(height),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "progress_hooks": [hook],
        # quiet reduces console noise (the UI uses the hook)
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_audio_streamlit(url: str, codec: str, bitrate_kbps: int, save_path: str, hook):
    Path(save_path).mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "outtmpl": str(Path(save_path) / "%(title).200B [%(id)s].%(ext)s"),
        "format": "bestaudio/best",
        "noplaylist": True,
        "progress_hooks": [hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": str(bitrate_kbps),
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# --- Streamlit UI ---
st.set_page_config(page_title="YouTube Downloader ", layout="centered")
st.title("YouTube Downloader ")
st.write("Enter a YouTube URL, choose Video (choose quality) or Audio-only (mp3/m4a + bitrate), then click Download.")

url = st.text_input("YouTube URL")

mode = st.radio("Mode", ("Video", "Audio only"))

if mode == "Video":
    col1, col2 = st.columns(2)
    quality = col1.selectbox("Quality", ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"], index=0)
    save_path = col2.text_input("Save folder", "downloads")
else:
    col1, col2 = st.columns(2)
    codec = col1.selectbox("Audio codec", ["mp3", "m4a"], index=0)
    bitrate = col2.selectbox("Bitrate (kbps)", ["128", "192", "320"], index=1)
    save_path = st.text_input("Save folder", "downloads")

start = st.button("Start Download")

if start:
    if not url:
        st.error("Please provide a YouTube URL.")
    else:
        progress_bar = st.progress(0.0)
        status = st.empty()

        try:
            hook = make_progress_hook(progress_bar, status)
            with st.spinner("Starting download..."):
                if mode == "Video":
                    download_video_streamlit(url, quality, save_path, hook)
                else:
                    download_audio_streamlit(url, codec, int(bitrate), save_path, hook)

            status.success("Download and post-processing completed!")

        except Exception as e:
            st.exception(e)



st.markdown("---")
st.markdown("Created By Om Chaudhari With❤️")



# End of file

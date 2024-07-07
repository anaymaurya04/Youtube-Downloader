from flask import Flask, request, jsonify, send_from_directory
from pytube import Playlist, YouTube
import os
import re
import logging

app = Flask(__name__, static_url_path='', static_folder='static')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOAD_FOLDER = "downloads"

def sanitize_filename(filename):
    sanitized = "".join(c for c in filename if c not in r'\/:*?"<>|').strip()
    return sanitized[:100] if len(sanitized) > 100 else sanitized

def ensure_download_folder():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

def download_video(url, folder_path=None):
    ensure_download_folder()
    try:
        yt = YouTube(url)
        video_stream = yt.streams.get_highest_resolution()
        safe_title = sanitize_filename(yt.title)
        output_path = folder_path if folder_path else DOWNLOAD_FOLDER
        video_stream.download(output_path=output_path, filename=f"{safe_title}.mp4")
        logger.info(f"Downloaded video: {yt.title}")
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise

def download_audio(url, folder_path=None):
    ensure_download_folder()
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        safe_title = sanitize_filename(yt.title)
        output_path = folder_path if folder_path else DOWNLOAD_FOLDER
        audio_stream.download(output_path=output_path, filename=f"{safe_title}.mp3")
        logger.info(f"Downloaded audio: {yt.title}")
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise

def download_playlist(url):
    ensure_download_folder()
    try:
        playlist = Playlist(url)
        safe_playlist_title = sanitize_filename(playlist.title)
        playlist_path = os.path.join(DOWNLOAD_FOLDER, safe_playlist_title)
        os.makedirs(playlist_path, exist_ok=True)
        for video_url in playlist.video_urls:
            download_video(video_url, folder_path=playlist_path)
        logger.info(f"Downloaded playlist: {playlist.title}")
    except Exception as e:
        logger.error(f"Error downloading playlist: {str(e)}")
        raise

def download_audio_playlist(url):
    ensure_download_folder()
    try:
        playlist = Playlist(url)
        safe_playlist_title = sanitize_filename(playlist.title)
        playlist_path = os.path.join(DOWNLOAD_FOLDER, safe_playlist_title)
        os.makedirs(playlist_path, exist_ok=True)
        for video_url in playlist.video_urls:
            download_audio(video_url, folder_path=playlist_path)
        logger.info(f"Downloaded audio playlist: {playlist.title}")
    except Exception as e:
        logger.error(f"Error downloading audio playlist: {str(e)}")
        raise

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    download_type = data.get('type')

    if not url or not download_type:
        return jsonify({"error": "Missing required parameters"}), 400

    if not re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$', url):
        return jsonify({"error": "Invalid URL"}), 400

    try:
        if download_type == 'video':
            download_video(url)
        elif download_type == 'audio':
            download_audio(url)
        elif download_type == 'playlist':
            download_playlist(url)
        elif download_type == 'audio_playlist':
            download_audio_playlist(url)
        else:
            return jsonify({"error": "Invalid download type"}), 400
        return jsonify({"message": "Download successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)

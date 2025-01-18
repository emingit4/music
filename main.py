from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from googleapiclient.discovery import build
import yt_dlp
import logging
import os

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot parameters
api_id = "28603118"
api_hash = "35a400855835510c0a926f1e965aa12d"
bot_token = "5357718486:AAG3bxaqLvPUBxPvvv46DQYfBCj7aQuwDTE"

app = Client("music_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
vc = PyTgCalls(app)

# YouTube API key
API_KEY = 'AIzaSyA8rNaOWHqOfPW2_EVnzKBhCkc2dIJ5tX8'

# Create YouTube Data API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

def search_youtube(query):
    request = youtube.search().list(
        part="snippet",
        maxResults=1,
        q=query
    )
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        video_id = response['items'][0]['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_url
    return None

def download_video(url):
    # Ensure the downloads directory exists
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # yt-dlp parameters
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best audio quality
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # File name and location
        'noplaylist': True,  # Do not download playlists
        'quiet': True,  # Only show necessary information in the console
        'nocheckcertificate': True,  # Skip certificate check
        'no_warnings': True,  # Suppress warnings
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
            'preferredcodec': 'mp3',  # Audio file format
            'preferredquality': '192',  # Audio quality
        }],
    }

    # Download video with yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.on_message(filters.command("play"))
async def play(_, message):
    if len(message.command) < 2:
        await message.reply("Zəhmət olmasa, mahnının adını yazın.")
        return

    query = " ".join(message.command[1:])
    video_url = search_youtube(query)
    if not video_url:
        await message.reply("Mahnı tapılmadı.")
        return

    download_video(video_url)  # Download the music

    # Find the path of the audio file
    audio_file = f"downloads/{query}.mp3"  # Ensure this path is correct

    if not vc.is_connected(message.chat.id):
        try:
            await vc.join_group_call(
                message.chat.id,
                MediaStream(audio_file)  # Add MediaStream with the audio file
            )
            await message.reply("Mahnı oynanır.")
        except Exception as e:
            logger.error(f"Səsli söhbətə qoşulma zamanı səhv baş verdi: {e}")
            await message.reply("Səsli söhbətə qoşulma zamanı səhv baş verdi.")
            return
    else:
        await message.reply("Zatən səsli söhbətə qoşulmusunuz.")

@app.on_message(filters.command("stop"))
async def stop(_, message):
    await vc.leave_group_call(message.chat.id)
    await message.reply("Mahnı dayandırıldı.")
    logger.info("Bot səsli söhbəti tərk etdi.")

async def start_bot():
    try:
        await app.start()  # Connect to Pyrogram
        await vc.start()   # Start PyTgCalls
        logger.info("Bot başladı.")
        await app.idle()  # Keep the bot running
    except Exception as e:
        logger.error(f"Botun başlaması zamanı səhv baş verdi: {e}")

# Start the bot
if __name__ == "__main__":
    app.run()

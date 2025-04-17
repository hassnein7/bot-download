import yt_dlp

def download_video(url, output_path="."):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s-%(id)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_audio(url, output_path="."):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s-%(id)s.%(ext)s',
        'extract_audio': True,
        'format': 'bestaudio/best',
        'audioformat': 'mp3',
        'audioquality': '0',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def get_video_options(url):
    ydl_opts = {
        'listformats': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        return formats

if __name__ == '__main__':
    video_url = input("Enter the video URL: ")
    print("Choose an option:")
    print("1. Download video")
    print("2. Download audio (MP3)")
    print("3. Show available qualities")

    choice = input("Enter your choice (1-3): ")

    if choice == '1':
        download_video(video_url)
        print("Video downloaded successfully!")
    elif choice == '2':
        download_audio(video_url)
        print("Audio downloaded successfully!")
    elif choice == '3':
        options = get_video_options(video_url)
        for f in options:
            print(f"{f['format_id']} {f.get('format_note', '')} {f['ext']} {f.get('width', '')}x{f.get('height', '')}")
    else:
        print("Invalid choice.")
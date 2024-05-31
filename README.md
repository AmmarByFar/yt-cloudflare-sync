# YouTube Channel to Cloudflare Stream Sync

This Python script allows you to sync videos from a specified YouTube channel to Cloudflare Stream, upload their thumbnails to Cloudflare Images, and update a Supabase table with the corresponding links.

## Features

- Downloads videos from a YouTube channel using the YouTube Data API and yt-dlp.
- Uploads videos to Cloudflare Stream.
- Uploads video thumbnails to Cloudflare Images.
- Updates a Supabase table with the video details, including the YouTube video ID, Cloudflare video ID, video format, thumbnail URL, and video tags.
- Supports environment variables for sensitive credentials.

## Prerequisites

Before running the script, make sure you have the following:

- Python 3.x installed on your machine.
- A YouTube API key with access to the YouTube Data API.
- Cloudflare API token and account ID for Cloudflare Stream and Cloudflare Images.
- Supabase project URL and API key.
- yt-dlp executable downloaded and its path specified in the script.

## Setup

1. Clone the repository or download the script file.

2. Install the required Python dependencies by running the following command:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the same directory as the script and add your credentials:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   CHANNEL_ID=your_channel_id
   CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
   CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
   CLOUDFLARE_IMAGE_API_TOKEN=your_cloudflare_image_api_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
   Replace the placeholders with your actual credentials.

4. Specify the path to your yt-dlp executable in the script:
   ```python
   yt_dlp_path = r"C:\path\to\yt-dlp.exe"
   ```

## Usage

To run the script, execute the following command:
```
python sync.py
```

The script will perform the following steps:

1. Retrieve the list of video IDs from the specified YouTube channel using the YouTube Data API.
2. Process each video:
   - Download the video using yt-dlp.
   - Retrieve video details using the YouTube Data API.
   - Extract video tags from the video details.
   - Use ffmpeg to determine the video dimensions and format (portrait or landscape).
   - Upload the video to Cloudflare Stream.
   - Download the video thumbnail from YouTube.
   - Upload the thumbnail to Cloudflare Images.
   - Update the Supabase table with the video details, including the YouTube video ID, Cloudflare video ID, video format, thumbnail URL, and video tags.
   - Delete the local video and thumbnail files.

3. Print the progress and status of each video processing step.

## Note

- The script skips the first video in the channel for debugging purposes. You can remove or modify this condition if needed.
- Make sure to handle the downloaded videos and thumbnails responsibly and in compliance with the respective platforms' terms of service.

## License

This script is provided as-is without any warranty. You are free to use, modify, and distribute it as per your requirements.
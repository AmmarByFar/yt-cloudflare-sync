# Sync Youtube videos from entire channel to cloudflare stream
# Author: Ammar
# Date: 2024
# License: MIT
# Usage: python3 sync.py

from dotenv import load_dotenv
import os
import requests
import subprocess
from tusclient import client
from supabase import create_client, Client
import json

load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_API_KEY")
channel_id = os.getenv("CHANNEL_ID")
cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
cloudflare_image_api_token = os.getenv("CLOUDFLARE_IMAGE_API_TOKEN")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Set the path to your yt-dlp executable
yt_dlp_path = r"C:\tools\yt-dlp.exe"

# Initialize the Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Retrieve the list of video IDs from your channel
url = f"https://www.googleapis.com/youtube/v3/search?key={youtube_api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=72"
response = requests.get(url)
data = response.json()

# Initialize a counter variable
video_count = 0

# Process each video
for search_result in data["items"]:
    video_id = search_result["id"]["videoId"]
    video_title = search_result["snippet"]["title"]
    video_description = search_result["snippet"]["description"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # Increment the video count
    video_count += 1
    
    # Skip the first video
    if video_count == 1:
        print(f"Skipping the first video: {video_title}")
        continue
    
    # Retrieve video details using the YouTube Data API
    video_details_url = f"https://www.googleapis.com/youtube/v3/videos?key={youtube_api_key}&id={video_id}&part=snippet,contentDetails"
    video_details_response = requests.get(video_details_url)
    video_details_data = video_details_response.json()
    print(f"Processing video: {video_title}")
    
    if video_details_data["items"]:
        video_item = video_details_data["items"][0]

        # Extract the tags from the video details
        video_tags = video_item["snippet"].get("tags", [])
        
        # Download the video using yt-dlp
        local_video_path = f"./downloads/{video_id}.webm"
        subprocess.call([yt_dlp_path, "-o", local_video_path, video_url])
        
        print(f"Downloaded video: {local_video_path}")

        # Use ffmpeg to get the video dimensions
        ffprobe_command = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            local_video_path
        ]
        ffprobe_output = subprocess.check_output(ffprobe_command).decode("utf-8")
        ffprobe_data = json.loads(ffprobe_output)

        video_width = int(ffprobe_data["streams"][0]["width"])
        video_height = int(ffprobe_data["streams"][0]["height"])

        is_short = video_height > video_width  # YouTube Shorts have a higher height than width
        video_format = "portrait" if is_short else "landscape"
        
        # Upload the video to Cloudflare Stream
        tus_url = f"https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/stream"
        headers = {"Authorization": f"Bearer {cloudflare_api_token}"}

        # Set the video title as metadata during the upload
        metadata = {
            "name": video_title
        }

        print(f"Uploading video to Cloudflare Stream...")
        
        try:
            my_client = client.TusClient(tus_url, headers=headers)
            with open(local_video_path, "rb") as file:
                uploader = my_client.uploader(file_stream=file, chunk_size=52428800, metadata=metadata)
                uploader.upload()
            
            print(f"Uploaded video to Cloudflare Stream: {uploader.url}")
            
            # Extract the Cloudflare video ID from the upload response
            cloudflare_video_id = uploader.url.split("?")[0].split("/")[-1]
            
            # Download the thumbnail from YouTube
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            thumbnail_response = requests.get(thumbnail_url)
            
            if thumbnail_response.status_code == 200:
                # Save the thumbnail locally
                local_thumbnail_path = f"./downloads/{video_id}_thumbnail.jpg"
                with open(local_thumbnail_path, "wb") as file:
                    file.write(thumbnail_response.content)
                
                print(f"Downloaded thumbnail: {local_thumbnail_path}")
                
                # Upload the thumbnail to Cloudflare Images
                cloudflare_image_headers = {"Authorization": f"Bearer {cloudflare_image_api_token}"}
                cloudflare_images_url = f"https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/images/v1"

                with open(local_thumbnail_path, "rb") as file:
                    files = {"file": file}
                    data = {"requireSignedURLs": "false"}
                    response = requests.post(cloudflare_images_url, headers=cloudflare_image_headers, files=files, data=data)
                
                if response.status_code == 200:
                    # print(f"Uploaded thumbnail to Cloudflare Images: {response.json()}")
                    thumbnail_data = response.json()
                    thumbnail_url = thumbnail_data["result"]["variants"][1]  # Get the thumbnail variant URL
                    
                    print(f"Uploaded thumbnail to Cloudflare Images: {thumbnail_url}")
                    
                   # Update the Supabase table with the video details
                    video_data = {
                        "youtube_videoId": video_id,
                        "cloudflare_videoId": cloudflare_video_id,
                        "title": video_title,
                        "orientation": video_format,
                        "thumbnail_url": thumbnail_url,
                        "description": video_description,
                    }
                    video_response = supabase.table("video_content").upsert(video_data).execute()
                    
                    # Retrieve the generated video ID from Supabase
                    video_content_id = video_response.data[0]["id"]
                    
                    # Retrieve the existing tags from the Supabase tags table
                    tags_response = supabase.table("tags").select("id", "name").execute()
                    existing_tags = {tag["name"].lower(): tag["id"] for tag in tags_response.data}
                    
                    # Insert the video tags into the video_tags table
                    for tag_name in video_tags:
                        tag_name = tag_name.lower()
                        if tag_name in existing_tags:
                            tag_id = existing_tags[tag_name]
                            video_tag_data = {
                                "video_id": video_content_id,
                                "tag_id": tag_id
                            }
                            supabase.table("video_tags").upsert(video_tag_data).execute()
                    
                    print(f"Updated Supabase tables with video details and tags for video ID: {video_id}")
                    print(f"Updated Supabase table with YouTube video ID: {video_id}, Cloudflare video ID: {cloudflare_video_id}, Video Format: {video_format}, and Thumbnail URL: {thumbnail_url}")
                else:
                    print(f"Error uploading thumbnail to Cloudflare Images: {response.text}")
                
                # Delete the local thumbnail file
                os.remove(local_thumbnail_path)
                print(f"Deleted local thumbnail file: {local_thumbnail_path}")
            else:
                print(f"Error downloading thumbnail: {thumbnail_response.status_code}")
            
            # Delete the local video file after successful upload and database update
            os.remove(local_video_path)
            print(f"Deleted local video file: {local_video_path}")
        except Exception as e:
            print(f"Error uploading video or updating Supabase: {str(e)}")
            break

print("Video processing and database update completed.")
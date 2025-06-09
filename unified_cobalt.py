@nightyScript(
    name="Unified Cobalt Tools",
    author="thedorekaczynski",
    description="All-in-one tool for downloading media and converting to GIFs",
    usage="""<p>c <url> [-720p] [-wav] [-audio] (Cobalt downloader)
<p>cg <url> [-fps=<fps>] [-scale=<width>:-1] [-time=<start>-<end>] [-optimize] [-720p] (Cobalt GIF converter)
<p>v2g <url or attachment> [-fps=<fps>] [-scale=<width>:-1] [-time=<start>-<end>] [-optimize] [-720p] [-speed=<factor>] (Direct FFmpeg GIF converter)
<p>c|cg|v2g url <your_local_cobalt_url>
<p>c|cg|v2g path <download_path>
<p>c|cg|v2g debug
<p>c|cg|v2g persistent
<p>c|cg|v2g lb <1|12|24|72> (Set litterbox expiry time in hours)
<p>c|cg|v2g limit <size_mb> (Set file size limit before using Litterbox)
<p>c|cg|v2g status"""
)
def unified_cobalt_script():
    """
    UNIFIED COBALT TOOLS
    -------------------
    
    This script provides a comprehensive suite of tools for downloading media and converting videos to GIFs:
    
    1. Cobalt Downloader: Downloads media from various platforms using the Cobalt API
    2. Cobalt GIF Converter: Downloads and converts videos to optimized GIFs
    3. Direct FFmpeg GIF Converter: Converts videos to GIFs with advanced FFmpeg parameters
    
    Features:
    - Download media from supported platforms
    - Convert videos to GIFs with customizable parameters
    - Optimize GIFs for size and quality
    - Automatic fallback to litterbox.catbox.moe for large files
    - Persistent storage option
    - Debug mode for troubleshooting
    - Configurable download paths and Cobalt instance URLs
    
    DOCKER SETUP GUIDE:
    1. Install Docker and Docker Compose:
       - Windows/Mac: Download Docker Desktop from docker.com
       - Linux: Install docker and docker-compose packages
    
    2. Create a directory for Cobalt:
       $ mkdir cobalt && cd cobalt
    
    3. Create docker-compose.yml:
```yaml
    services:
      cobalt-api:
        image: ghcr.io/imputnet/cobalt:10
        init: true
        read_only: true
        restart: unless-stopped
        container_name: cobalt-api
        ports:
          - 9000:9000/tcp
        environment:
          API_URL: "http://localhost:9000"
        labels:
          - com.centurylinklabs.watchtower.scope=cobalt

      watchtower:
        image: ghcr.io/containrrr/watchtower
        restart: unless-stopped
        command: --cleanup --scope cobalt --interval 900 --include-restarting
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock
```
    
    4. Start Cobalt:
       $ docker-compose up -d
    
    5. Pull required images:
       $ docker pull jrottenberg/ffmpeg:latest
       $ docker pull dylanninin/giflossy:latest
    
    COMMANDS:
    1. Cobalt Downloader (<p>c or <p>cobalt):
       - Download media: <p>c <url> [-720p] [-wav] [-audio]
       - Configure: <p>c url|path|debug|persistent|status
    
    2. Cobalt GIF (<p>cg or <p>cobaltgif):
       - Convert to GIF: <p>cg <url> [-fps=15] [-scale=480:-1] [-time=0-30] [-optimize] [-720p]
       - Configure: <p>cg url|path|debug|persistent|status
    
    3. Direct FFmpeg GIF (<p>v2g):
       - Convert to GIF: <p>v2g <url or attachment> [-fps=15] [-scale=480:-1] [-time=0-30] [-optimize] [-720p] [-speed=<factor>]
       - Configure: <p>v2g url|path|debug|persistent|status
    
    PARAMETERS:
    Cobalt Downloader:
    - Quality: -144p to -4320p, -max
    - Audio: -wav, -ogg, -opus, -best
    - Mode: -audio, -mute
    
    Cobalt GIF:
    - Quality: -144p to -4320p, -max
    - FPS: -fps=<number> (default: 15)
    - Scale: -scale=<width>:-1 (default: 480:-1)
    - Time: -time=<start>-<end> (in seconds)
    - Optimize: -optimize (reduces file size)
    
    Direct FFmpeg GIF:
    - Quality: -144p to -4320p, -max
    - FPS: -fps=<number> (default: 15)
    - Scale: -scale=<width>:-1 (default: 480:-1)
    - Time: -time=<start>-<end> (in seconds)
    - Optimize: -optimize (reduces file size)
    - Loop: -loop=<number> (default: 0, -1 for infinite)
    - Dither: -dither=<method> (default: bayer:bayer_scale=5)
    - Colors: -colors=<number> (default: 256)
    - Speed: -speed=<factor> (default: 1.0, e.g. 0.5 for half speed, 2.0 for double speed)
    
    EXAMPLES:
    1. Download a video in 720p quality:
       <p>c https://www.youtube.com/watch?v=dQw4w9WgXcQ -720p
    
    2. Download audio only in WAV format:
       <p>c https://www.youtube.com/watch?v=dQw4w9WgXcQ -wav -audio
    
    3. Convert a video to a GIF with 10 FPS and optimize for size:
       <p>cg https://www.youtube.com/watch?v=dQw4w9WgXcQ -fps=10 -optimize
    
    4. Convert a specific part of a video to a GIF (first 15 seconds):
       <p>cg https://www.youtube.com/watch?v=dQw4w9WgXcQ -time=0-15 -scale=640:-1
    
    5. Configure Cobalt to use a custom URL:
       <p>c url http://my-cobalt-server:9000
    
    6. Enable persistent storage to keep downloaded files:
       <p>c persistent
    
    7. Check the status of your Cobalt setup:
       <p>c status
    
    NOTES:
    - The -optimize flag is only available for GIF operations
    - All commands share the same configuration system
    - Files are processed locally in Docker containers
    - Discord has an 8MB file size limit (customizable with `c limit`)
    - URLs must start with http:// or https://
    - If you get an "invalid link" error, check that the URL is correct and supported by Cobalt
    - Large files (>limit) are automatically uploaded to litterbox.catbox.moe
    - Debug mode provides detailed logging for troubleshooting
    - Persistent storage keeps files in the configured download path
    """
    import json
    import aiohttp
    import asyncio
    import os
    import re
    import tempfile
    from pathlib import Path
    import shutil
    from datetime import datetime
    
    # Config keys
    COBALT_URL_KEY = "unified_cobalt_url"
    DOWNLOAD_PATH_KEY = "unified_cobalt_path"
    DEBUG_ENABLED_KEY = "unified_cobalt_debug"
    PERSISTENT_STORAGE_KEY = "unified_cobalt_persistent"
    LITTERBOX_EXPIRY_KEY = "unified_cobalt_litterbox_expiry"
    LITTERBOX_SIZE_THRESHOLD_MB_KEY = "unified_cobalt_limit_mb"
    
    # Initialize configuration
    if getConfigData().get(COBALT_URL_KEY) is None:
        updateConfigData(COBALT_URL_KEY, "http://localhost:9000")
    
    if getConfigData().get(DOWNLOAD_PATH_KEY) is None:
        default_path = os.path.join(tempfile.gettempdir(), "unified_cobalt")
        updateConfigData(DOWNLOAD_PATH_KEY, default_path)
    
    if getConfigData().get(DEBUG_ENABLED_KEY) is None:
        updateConfigData(DEBUG_ENABLED_KEY, False)
    
    if getConfigData().get(PERSISTENT_STORAGE_KEY) is None:
        updateConfigData(PERSISTENT_STORAGE_KEY, False)

    if getConfigData().get(LITTERBOX_EXPIRY_KEY) is None:
        updateConfigData(LITTERBOX_EXPIRY_KEY, "24h")  # Default to 24 hours

    if getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY) is None:
        updateConfigData(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8)
    
    # Helper function for debug logging
    def debug_log(message, type_="INFO"):
        """Log debug messages if debug mode is enabled"""
        if getConfigData().get(DEBUG_ENABLED_KEY, False):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [UNIFIED] [{type_}] {message}", type_=type_)
    
    # Helper function to ensure download directory exists
    def ensure_download_dir(persistent=False, workdir=False):
        """Create and return the appropriate download directory"""
        download_path = getConfigData().get(DOWNLOAD_PATH_KEY)
        if workdir:
            download_path = os.path.join(download_path, "workdir")
        os.makedirs(download_path, exist_ok=True)
        return download_path

    # Helper function to sanitize filenames
    def sanitize_filename(filename: str) -> str:
        """Return a filesystem-safe filename"""
        # Drop directory components and query strings/fragments
        base = os.path.basename(filename)
        base = base.split('?')[0].split('#')[0]
        # Replace characters that are invalid on Windows and other platforms
        base = re.sub(r'[<>:"/\\|?*]', '_', base)
        # Replace remaining whitespace with underscores
        base = re.sub(r'\s+', '_', base)
        return base
    
    # Helper function to parse Cobalt arguments
    def parse_cobalt_args(args_str):
        """Parse Cobalt-specific arguments from command string"""
        # Normalize spaces to handle both -flag=value and -flag value formats
        args_str = re.sub(r'-(\w+)=(\w+)', r'-\1 \2', args_str)
        
        # Split into words
        words = args_str.split()
        
        # Extract URL (everything before first flag)
        url_parts = []
        i = 0
        while i < len(words) and not words[i].startswith('-'):
            url_parts.append(words[i])
            i += 1
        url = ' '.join(url_parts)
        
        # Default values
        quality = "1080"
        audio = "mp3"
        mode = "auto"
        
        # Track provided flags
        quality_provided = False
        audio_provided = False
        mode_provided = False
        
        while i < len(words):
            # Quality flags (-720p, etc.)
            quality_match = re.match(r'-(\d+)p$', words[i])
            if quality_match:
                quality = quality_match.group(1)
                quality_provided = True
                i += 1
            # Max quality
            elif words[i] == '-max':
                quality = "max"
                quality_provided = True
                i += 1
            # Audio format
            elif words[i] in ['-wav', '-ogg', '-opus', '-best']:
                audio = words[i][1:]
                audio_provided = True
                i += 1
            # Mode flags
            elif words[i] in ['-audio', '-mute']:
                mode = words[i][1:]
                mode_provided = True
                i += 1
            # Legacy format support
            elif words[i] == '-quality' and i + 1 < len(words):
                quality = words[i+1]
                quality_provided = True
                i += 2
            elif words[i] == '-audio' and i + 1 < len(words):
                audio = words[i+1]
                audio_provided = True
                i += 2
            elif words[i] == '-mode' and i + 1 < len(words):
                mode = words[i+1]
                mode_provided = True
                i += 2
            else:
                i += 1
        
        return {
            "url": url.strip(),
            "quality": quality,
            "audio": audio,
            "mode": mode,
            "quality_provided": quality_provided,
            "audio_provided": audio_provided,
            "mode_provided": mode_provided
        }
    
    # Helper function to parse GIF arguments
    def parse_gif_args(args_str):
        """Parse GIF-specific arguments from command string"""
        # First get Cobalt args
        cobalt_args = parse_cobalt_args(args_str)
        
        # Then parse GIF-specific args
        fps_match = re.search(r'-fps=(\d+)', args_str)
        scale_match = re.search(r'-scale=(\d+:-1)', args_str)
        time_match = re.search(r'-time=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)', args_str)
        optimize_match = re.search(r'-optimize', args_str)
        speed_match = re.search(r'-speed=(\d*\.?\d+)', args_str)  # Add speed parameter
        
        # Get URL and remove GIF flags
        url = cobalt_args["url"]
        for match in [fps_match, scale_match, time_match, optimize_match, speed_match]:
            if match and match.group(0) in url:
                url = url.replace(match.group(0), "").strip()
        
        return {
            "url": url.strip(),
            "quality": cobalt_args["quality"],
            "audio": cobalt_args["audio"],
            "mode": cobalt_args["mode"],
            "quality_provided": cobalt_args["quality_provided"],
            "audio_provided": cobalt_args["audio_provided"],
            "mode_provided": cobalt_args["mode_provided"],
            "fps": int(fps_match.group(1)) if fps_match else 15,
            "scale": scale_match.group(1) if scale_match else "480:-1",
            "time": time_match.group(1) + "-" + time_match.group(2) if time_match else None,
            "optimize": bool(optimize_match),
            "speed": float(speed_match.group(1)) if speed_match else 1.0  # Add speed to return dict
        }
    
    # Helper function to parse v2g arguments
    def parse_v2g_args(args_str):
        """Parse v2g-specific arguments from command string"""
        # First get Cobalt args
        cobalt_args = parse_cobalt_args(args_str)
        
        # Then parse v2g-specific args
        fps_match = re.search(r'-fps=(\d+)', args_str)
        scale_match = re.search(r'-scale=(\d+:-1)', args_str)
        time_match = re.search(r'-time=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)', args_str)
        optimize_match = re.search(r'-optimize', args_str)
        quality_match = re.search(r'-(\d+)p', args_str)
        loop_match = re.search(r'-loop=(\d+)', args_str)
        dither_match = re.search(r'-dither=(\w+)', args_str)
        colors_match = re.search(r'-colors=(\d+)', args_str)
        speed_match = re.search(r'-speed=(\d*\.?\d+)', args_str)  # Add speed parameter
        
        # Get URL and remove v2g flags
        url = cobalt_args["url"]
        for match in [fps_match, scale_match, time_match, optimize_match, quality_match, loop_match, dither_match, colors_match, speed_match]:
            if match and match.group(0) in url:
                url = url.replace(match.group(0), "").strip()
        
        return {
            "url": url.strip(),
            "fps": int(fps_match.group(1)) if fps_match else 15,
            "scale": scale_match.group(1) if scale_match else "480:-1",
            "time": time_match.group(1) + "-" + time_match.group(2) if time_match else None,
            "optimize": bool(optimize_match),
            "quality": quality_match.group(1) if quality_match else "1080",
            "loop": int(loop_match.group(1)) if loop_match else 0,
            "dither": dither_match.group(1) if dither_match else "bayer:bayer_scale=5",
            "colors": int(colors_match.group(1)) if colors_match else 256,
            "speed": float(speed_match.group(1)) if speed_match else 1.0  # Add speed to return dict
        }
    
    # Helper function to run docker commands
    async def run_docker_cmd(cmd):
        """Execute a Docker command and return its output"""
        debug_log(f"Running docker command: {cmd}", type_="INFO")
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f"Docker command failed: {stderr.decode()}")
        return stdout.decode()
    
    # Helper function to download files
    async def download_file(url, filename, referer=None):
        """Download a file from URL to the download directory"""
        filename = sanitize_filename(filename)
        download_path = ensure_download_dir()
        file_path = os.path.join(download_path, filename)
        debug_log(f"Downloading to: {file_path}", type_="INFO")

        base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Range": "bytes=0-"
        }
        if referer:
            base_headers["Referer"] = referer
        
        async with aiohttp.ClientSession() as session:
            try:
                debug_log(f"Attempting download from URL: {url}", type_="INFO")
                headers = base_headers.copy()

                for attempt in range(2):
                    debug_log(f"Using headers: {headers}", type_="INFO")
                    async with session.get(url, headers=headers, timeout=60) as response:
                        debug_log(f"Response status: {response.status}", type_="INFO")
                        debug_log(f"Response headers: {dict(response.headers)}", type_="INFO")

                        if response.status in [200, 206]:
                            debug_log(f"Download connection established (HTTP {response.status})", type_="SUCCESS")
                            total_size = 0
                            with open(file_path, 'wb') as f:
                                while True:
                                    chunk = await response.content.read(8192)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                                    total_size += len(chunk)
                                    if total_size % (1024 * 1024) == 0:
                                        debug_log(f"Downloaded: {total_size / 1024 / 1024:.2f} MB", type_="INFO")

                            if total_size == 0:
                                raise Exception("Downloaded file is 0 bytes")

                            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                                raise Exception("File was not properly saved")

                            debug_log(f"Download completed. Size: {total_size / 1024 / 1024:.2f} MB", type_="SUCCESS")
                            return file_path
                        elif response.status == 403 and attempt == 0 and "Range" in headers:
                            debug_log("HTTP 403 received, retrying without Range header", type_="WARNING")
                            headers.pop("Range", None)
                            continue
                        else:
                            error_msg = f"Failed to download file: HTTP {response.status}"
                            debug_log(error_msg, type_="ERROR")
                            debug_log(f"Response headers: {dict(response.headers)}", type_="ERROR")
                            debug_log(f"Response content: {await response.text()}", type_="ERROR")
                            raise Exception(error_msg)
            except aiohttp.ClientError as e:
                error_msg = f"Network error: {str(e)}"
                debug_log(error_msg, type_="ERROR")
                debug_log(f"URL: {url}", type_="ERROR")
                debug_log(f"Headers: {headers}", type_="ERROR")
                if hasattr(e, 'status'):
                    debug_log(f"Error status: {e.status}", type_="ERROR")
                if hasattr(e, 'headers'):
                    debug_log(f"Error headers: {dict(e.headers)}", type_="ERROR")
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error during download: {str(e)}"
                debug_log(error_msg, type_="ERROR")
                debug_log(f"URL: {url}", type_="ERROR")
                debug_log(f"Headers: {headers}", type_="ERROR")
                raise
    
    # Helper function to validate URLs
    def is_valid_url(url):
        """Check if the URL is valid and has a supported scheme"""
        if not url:
            return False
        
        # Check if URL has a valid scheme
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Basic URL format validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    # Helper function to download from Cobalt
    async def download_from_cobalt(url, quality, audio, mode):
        """Download media from Cobalt API"""
        debug_log(f"Downloading from Cobalt: {url}", type_="INFO")
        debug_log(f"Quality: {quality}, Audio: {audio}, Mode: {mode}", type_="INFO")
        
        # Validate URL before sending to Cobalt API
        if not is_valid_url(url):
            debug_log(f"Invalid URL format: {url}", type_="ERROR")
            raise Exception("The URL you provided is invalid. Please check the URL format and try again.")
        
        cobalt_base_url = getConfigData().get(COBALT_URL_KEY, "http://localhost:9000")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        payload = {
            "url": url,
            "videoQuality": quality,
            "audioFormat": audio,
            "downloadMode": mode,
            "filenameStyle": "pretty"
        }
        
        debug_log(f"Sending request to Cobalt API: {cobalt_base_url}", type_="INFO")
        debug_log(f"Request payload: {payload}", type_="INFO")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    cobalt_base_url, 
                    headers=headers, 
                    json=payload,
                    timeout=30
                ) as response:
                    debug_log(f"Cobalt API response status: {response.status}", type_="INFO")
                    
                    try:
                        response_text = await response.text()
                        debug_log(f"Raw response: {response_text}", type_="INFO")
                        data = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError as e:
                        debug_log(f"Failed to parse JSON response: {str(e)}", type_="ERROR")
                        debug_log(f"Raw response text: {response_text}", type_="ERROR")
                        raise Exception(f"Invalid response from Cobalt API: {str(e)}")
                    
                    if response.status == 200:
                        if data.get("status") == "error":
                            error_code = data.get("error", {}).get("code", "unknown")
                            error_message = data.get("error", {}).get("message", "No error message provided")
                            debug_log(f"Cobalt API error - Code: {error_code}, Message: {error_message}", type_="ERROR")
                            
                            # Provide more user-friendly error messages for specific error codes
                            if error_code == "error.api.link.invalid":
                                raise Exception("The URL you provided is invalid or not supported by Cobalt. Please check the URL and try again.")
                            elif error_code == "error.api.link.unsupported":
                                raise Exception("This website is not supported by Cobalt. Please try a different URL.")
                            elif error_code == "error.api.link.private":
                                raise Exception("This content is private or requires authentication. Cobalt cannot access it.")
                            else:
                                raise Exception(f"Cobalt API error: {error_code} - {error_message}")
                        
                        elif data.get("status") in ["tunnel", "redirect"]:
                            download_url = data.get("url")
                            filename = data.get("filename", "download")
                            
                            if not download_url:
                                debug_log("No download URL in response", type_="ERROR")
                                debug_log(f"Full response data: {data}", type_="INFO")
                                raise Exception("No download URL received from Cobalt API")
                            
                            debug_log(f"Got download URL: {download_url}", type_="SUCCESS")
                            debug_log(f"Filename: {filename}", type_="INFO")
                            
                            try:
                                file_path = await download_file(download_url, filename, referer=url)
                                return file_path
                            except Exception as e:
                                error_str = str(e)
                                if "HTTP 403" in error_str:
                                    if "instagram.com" in url.lower():
                                        raise Exception("Instagram is blocking the download. Try:\n• Making sure the content is public\n• Waiting a few minutes\n• Using a different Cobalt instance")
                                    else:
                                        raise Exception(f"Access denied (403) when downloading. The server is blocking the request. Try again later or use a different Cobalt instance.")
                                elif "HTTP 429" in error_str:
                                    raise Exception("Too many requests. Please wait a few minutes before trying again.")
                                else:
                                    raise
                        
                        elif data.get("status") == "picker":
                            picker_items = data.get("picker", [])

                            if not picker_items:
                                debug_log("Empty picker items list", type_="ERROR")
                                debug_log(f"Full response data: {data}", type_="INFO")
                                raise Exception("No media items found in picker response")

                            debug_log(
                                f"Found {len(picker_items)} media items. Downloading all.",
                                type_="SUCCESS",
                            )

                            downloaded_paths = []
                            for idx, item in enumerate(picker_items, start=1):
                                item_url = item.get("url", "")
                                item_type = item.get("type", "unknown")

                                if not item_url:
                                    debug_log(
                                        f"No URL in picker item {idx}", type_="ERROR"
                                    )
                                    continue

                                filename = (
                                    f"cobalt_{idx}_{item_type}_{os.path.basename(item_url)}"
                                )
                                if not os.path.splitext(filename)[1]:
                                    if item_type == "photo":
                                        filename += ".jpg"
                                    elif item_type == "video":
                                        filename += ".mp4"
                                    elif item_type == "gif":
                                        filename += ".gif"

                                debug_log(
                                    f"Downloading picker item {idx} - URL: {item_url}, Type: {item_type}",
                                    type_="INFO",
                                )
                                try:
                                    path = await download_file(item_url, filename, referer=url)

                                    downloaded_paths.append(path)
                                except Exception as e:
                                    error_str = str(e)
                                    if "HTTP 403" in error_str:
                                        if "instagram.com" in url.lower():
                                            raise Exception(
                                                "Instagram is blocking the download. Try:\n• Making sure the content is public\n• Waiting a few minutes\n• Using a different Cobalt instance"
                                            )
                                        else:
                                            raise Exception(
                                                "Access denied (403) when downloading. The server is blocking the request. Try again later or use a different Cobalt instance."
                                            )
                                    elif "HTTP 429" in error_str:
                                        raise Exception(
                                            "Too many requests. Please wait a few minutes before trying again."
                                        )
                                    else:
                                        raise

                            audio_url = data.get("audio")
                            if audio_url:
                                audio_filename = data.get(
                                    "audioFilename",
                                    f"audio_{os.path.basename(audio_url)}" or "audio",
                                )
                                debug_log(
                                    f"Downloading slideshow audio - URL: {audio_url}",
                                    type_="INFO",
                                )
                                try:
                                    audio_path = await download_file(
                                        audio_url, audio_filename, referer=url

                                    )
                                    downloaded_paths.append(audio_path)
                                except Exception as e:
                                    debug_log(
                                        f"Failed to download slideshow audio: {str(e)}",
                                        type_="ERROR",
                                    )

                            if not downloaded_paths:
                                raise Exception(
                                    "Failed to download any items from picker response"
                                )

                            return downloaded_paths
                        else:
                            debug_log(f"Unknown status in response: {data.get('status')}", type_="ERROR")
                            debug_log(f"Full response data: {data}", type_="INFO")
                            raise Exception(f"Unknown response status: {data.get('status')}")
                    elif response.status == 400:
                        error_message = "Bad Request"
                        try:
                            if data.get("error"):
                                error_message = f"{data['error'].get('code', 'unknown')} - {data['error'].get('message', 'No message, Ensure the URL is supported by Cobalt, an unsupported URL was provided')}"
                        except:
                            pass
                        debug_log(f"Cobalt API returned 400 - {error_message}", type_="ERROR")
                        debug_log(f"Request payload: {payload}", type_="INFO")
                        debug_log(f"Response data: {data}", type_="INFO")
                        raise Exception(f"Cobalt API error (400): {error_message}")
                    else:
                        debug_log(f"Unexpected HTTP status: {response.status}", type_="ERROR")
                        debug_log(f"Response data: {data}", type_="INFO")
                        raise Exception(f"Cobalt API error: HTTP {response.status}")
                        
        except aiohttp.ClientError as e:
            debug_log(f"Network error: {str(e)}", type_="ERROR")
            debug_log(f"Request URL: {cobalt_base_url}", type_="INFO")
            debug_log(f"Request headers: {headers}", type_="INFO")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            if not str(e).startswith(("Cobalt API error", "Connection error")):
                debug_log(f"Unexpected error: {str(e)}", type_="ERROR")
            raise
    
    # Helper function to convert video to GIF
    async def convert_to_gif(video_path, fps, scale, time_range, optimize, speed=1.0):
        """Convert video to GIF using FFmpeg and optionally optimize with Giflossy"""
        debug_log(f"Converting video to GIF: {video_path}", type_="INFO")
        
        # Setup directories
        work_dir = ensure_download_dir(persistent=True, workdir=True)
        output_dir = ensure_download_dir(persistent=True)
        debug_log(f"Work directory: {work_dir}", type_="INFO")
        debug_log(f"Output directory: {output_dir}", type_="INFO")
        
        # Clean up existing files
        for file in ["input.mp4", "palette.png", "output.gif", "optimized.gif"]:
            try:
                os.remove(os.path.join(work_dir, file))
                debug_log(f"Cleaned up existing file: {file}", type_="INFO")
            except:
                pass
        
        # Copy video to work directory
        input_path = os.path.join(work_dir, "input.mp4")
        shutil.copy2(video_path, input_path)
        
        # Generate filename
        original_filename = os.path.splitext(os.path.basename(video_path))[0]
        original_filename = re.sub(r'[^\w\-_]', '_', original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gif_filename = f"{original_filename}_{timestamp}.gif"
        
        # Setup paths
        palette_path = os.path.join(work_dir, "palette.png")
        
        # Prepare time parameters
        time_params = ""
        if time_range:
            start_time, end_time = time_range.split("-")
            start_float = float(start_time)
            end_float = float(end_time)
            duration = str(end_float - start_float)
            time_params = f"-ss {start_time} -t {duration}"
        
        # Generate palette
        palette_cmd = (
            f'docker run --rm -v "{work_dir}:/tmp/work" jrottenberg/ffmpeg '
            f'-y {time_params} -i /tmp/work/input.mp4 '
            f'-vf "fps={fps},scale={scale}:flags=lanczos,palettegen" '
            f'/tmp/work/palette.png'
        )
        await run_docker_cmd(palette_cmd)
        
        if not os.path.exists(palette_path):
            raise Exception(f"Failed to generate palette image")
        
        # Convert to GIF with speed modification if specified
        vf_parts = []
        
        # Add basic filters
        vf_parts.append(f"scale={scale}:flags=lanczos")
        
        # Handle speed changes
        if speed != 1.0:
            # First apply speed change
            vf_parts.append(f"setpts={1/speed}*PTS")
            # Then force consistent frame rate
            vf_parts.append(f"fps={fps}")
        
        # Add palette use with dithering for better quality
        vf_parts.append("split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5")
        
        # Join filters with commas
        vf_string = ",".join(vf_parts)
        debug_log(f"Using video filter: {vf_string}", type_="INFO")
        
        gif_cmd = (
            f'docker run --rm -v "{work_dir}:/tmp/work" -v "{output_dir}:/tmp/output" jrottenberg/ffmpeg '
            f'-y {time_params} -i /tmp/work/input.mp4 -i /tmp/work/palette.png '
            f'-lavfi "{vf_string}" '
            f'/tmp/output/{gif_filename}'
        )
        try:
            await run_docker_cmd(gif_cmd)
        except Exception as e:
            error_str = str(e)
            # Truncate long error messages
            if len(error_str) > 1000:
                error_str = error_str[:997] + "..."
            raise Exception(f"FFmpeg error: {error_str}")
        
        gif_path = os.path.join(output_dir, gif_filename)
        if not os.path.exists(gif_path):
            raise Exception(f"GIF file not found")
        
        # Check initial size
        initial_size = os.path.getsize(gif_path) / (1024 * 1024)
        size_threshold = float(getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8))
        if initial_size > size_threshold and not optimize:
            debug_log(f"Initial GIF size ({initial_size:.2f}MB) exceeds Discord limit of {size_threshold}MB, skipping optimization", type_="INFO")
            return gif_path, initial_size, None, True  # Return True to indicate it should be uploaded to litterbox
        
        # Optimize if requested
        original_size = None
        if optimize:
            original_size = initial_size
            debug_log(f"Original GIF size: {original_size:.2f}MB", type_="INFO")
            
            optimized_gif = os.path.join(work_dir, "optimized.gif")
            giflossy_cmd = (
                f'docker run --rm -v "{output_dir}:/src" -v "{work_dir}:/dest" dylanninin/giflossy '
                f'gifsicle --lossy=30 /src/{gif_filename} -o /dest/optimized.gif'
            )
            try:
                await run_docker_cmd(giflossy_cmd)
            except Exception as e:
                error_str = str(e)
                # Truncate long error messages
                if len(error_str) > 1000:
                    error_str = error_str[:997] + "..."
                raise Exception(f"Giflossy error: {error_str}")
            
            if os.path.exists(optimized_gif):
                optimized_size = os.path.getsize(optimized_gif) / (1024 * 1024)
                size_reduction = ((original_size - optimized_size) / original_size) * 100
                
                if optimized_size > size_threshold:
                    debug_log("GIF still too large, trying higher compression", type_="INFO")
                    # Instead of optimizing the already optimized file, optimize the original with higher lossy value
                    giflossy_cmd = (
                        f'docker run --rm -v "{output_dir}:/src" -v "{work_dir}:/dest" dylanninin/giflossy '
                        f'gifsicle --lossy=60 /src/{gif_filename} -o /dest/optimized.gif'
                    )
                    try:
                        await run_docker_cmd(giflossy_cmd)
                    except Exception as e:
                        error_str = str(e)
                        # Truncate long error messages
                        if len(error_str) > 1000:
                            error_str = error_str[:997] + "..."
                        raise Exception(f"Giflossy error: {error_str}")
                    
                    if os.path.exists(optimized_gif):
                        optimized_size = os.path.getsize(optimized_gif) / (1024 * 1024)
                        size_reduction = ((original_size - optimized_size) / original_size) * 100
                        
                        if optimized_size > size_threshold:
                            debug_log("GIF still too large after second optimization", type_="INFO")
                            return gif_path, optimized_size, original_size, True  # Return True to indicate it should be uploaded to litterbox
                        else:
                            os.remove(gif_path)
                            shutil.move(optimized_gif, gif_path)
                    else:
                        raise Exception("Second optimization failed")
                else:
                    os.remove(gif_path)
                    shutil.move(optimized_gif, gif_path)
            else:
                raise Exception("GIF optimization failed")
        
        # Check final size
        final_size = os.path.getsize(gif_path) / (1024 * 1024)
        if final_size > size_threshold:
            debug_log(f"Final GIF size ({final_size:.2f}MB) exceeds Discord limit of {size_threshold}MB", type_="INFO")
            return gif_path, final_size, original_size, True  # Return True to indicate it should be uploaded to litterbox
        
        # Clean up
        try:
            for file in ["input.mp4", "palette.png"]:
                try:
                    os.remove(os.path.join(work_dir, file))
                except:
                    pass
        except Exception as e:
            debug_log(f"Cleanup error: {str(e)}", type_="ERROR")
        
        return gif_path, final_size, original_size, False  # Return False to indicate it should be sent to Discord

    # Helper function to upload files to litterbox.catbox.moe
    async def upload_to_litterbox(file_path):
        """Upload a file to litterbox.catbox.moe and return the URL.
        
        The uploaded file will be available for the configured duration before expiration.
        This is used as a fallback when files are too large for Discord's configured size limit.
        """
        debug_log(f"Uploading file to litterbox.catbox.moe: {file_path}", type_="INFO")
        
        try:
            # Read the file content first
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            async with aiohttp.ClientSession() as session:
                # Prepare the file for upload
                data = aiohttp.FormData()
                data.add_field('fileToUpload', file_content, filename=os.path.basename(file_path))
                data.add_field('reqtype', 'fileupload')
                data.add_field('time', getConfigData().get(LITTERBOX_EXPIRY_KEY, "24h"))  # Use configured expiry time
                
                # Upload the file
                async with session.post('https://litterbox.catbox.moe/resources/internals/api.php', data=data) as response:
                    if response.status == 200:
                        url = await response.text()
                        if url.startswith('https://'):
                            debug_log(f"File uploaded successfully: {url}", type_="SUCCESS")
                            return url
                        else:
                            raise Exception(f"Invalid response from litterbox: {url}")
                    else:
                        raise Exception(f"Failed to upload file: HTTP {response.status}")
        except Exception as e:
            debug_log(f"Error uploading to litterbox: {str(e)}", type_="ERROR")
            raise

    # Shared configuration command handler
    async def handle_config_command(ctx, args, command_name):
        """Handle configuration commands for both Cobalt and CobaltGIF"""
        args_parts = args.strip().split(' ', 1)
        action = args_parts[0].lower()
        
        if action == "url" and len(args_parts) > 1:
            url = args_parts[1].strip()
            if url.startswith("http://") or url.startswith("https://"):
                updateConfigData(COBALT_URL_KEY, url)
                debug_log(f"Cobalt URL updated to: {url}", type_="SUCCESS")
                await ctx.send(f"✅ Cobalt instance URL set to: {url}")
            else:
                debug_log(f"Invalid URL format attempted: {url}", type_="ERROR")
                await ctx.send("❌ Invalid URL format. Should start with http:// or https://")
        
        elif action == "path" and len(args_parts) > 1:
            path = args_parts[1].strip()
            try:
                os.makedirs(path, exist_ok=True)
                updateConfigData(DOWNLOAD_PATH_KEY, path)
                debug_log(f"Download path updated to: {path}", type_="SUCCESS")
                await ctx.send(f"✅ Download path set to: {path}")
            except Exception as e:
                debug_log(f"Error setting path: {str(e)}", type_="ERROR")
                await ctx.send(f"❌ Error setting path: {str(e)}")
        
        elif action == "debug":
            debug_enabled = not getConfigData().get(DEBUG_ENABLED_KEY, False)
            updateConfigData(DEBUG_ENABLED_KEY, debug_enabled)
            debug_log(f"Debug mode {'enabled' if debug_enabled else 'disabled'}", type_="SUCCESS")
            await ctx.send(f"✅ Debug mode {'enabled' if debug_enabled else 'disabled'}")
        
        elif action == "persistent":
            persistent_enabled = not getConfigData().get(PERSISTENT_STORAGE_KEY, False)
            updateConfigData(PERSISTENT_STORAGE_KEY, persistent_enabled)
            debug_log(f"Persistent storage {'enabled' if persistent_enabled else 'disabled'}", type_="SUCCESS")
            await ctx.send(f"✅ Persistent storage {'enabled' if persistent_enabled else 'disabled'}")
        
        elif action == "lb" and len(args_parts) > 1:
            time = args_parts[1].strip().lower()
            valid_times = {"1": "1h", "12": "12h", "24": "24h", "72": "72h"}
            if time in valid_times:
                updateConfigData(LITTERBOX_EXPIRY_KEY, valid_times[time])
                debug_log(f"Litterbox expiry time updated to: {valid_times[time]}", type_="SUCCESS")
                await ctx.send(f"✅ Litterbox file expiry set to {valid_times[time]}")
            else:
                debug_log(f"Invalid litterbox time attempted: {time}", type_="ERROR")
                await ctx.send("❌ Invalid time. Use 1, 12, 24, or 72 hours")

        elif action == "limit" and len(args_parts) > 1:
            try:
                threshold_mb = float(args_parts[1].strip())
                if threshold_mb <= 0:
                    await ctx.send("❌ Limit must be a positive number of megabytes.")
                    return
                updateConfigData(LITTERBOX_SIZE_THRESHOLD_MB_KEY, threshold_mb)
                debug_log(f"Litterbox upload limit set to {threshold_mb}MB", type_="SUCCESS")
                await ctx.send(f"✅ Litterbox upload limit set to: {threshold_mb} MB")
            except ValueError:
                await ctx.send(f"❌ Invalid limit. Provide a number in megabytes (e.g., `<p>{command_name} limit 20>`).")
        
        elif action == "status":
            msg = await ctx.send("🔍 Checking configuration...")
            try:
                cobalt_url = getConfigData().get(COBALT_URL_KEY, "http://localhost:9000")
                download_path = getConfigData().get(DOWNLOAD_PATH_KEY)
                debug_enabled = getConfigData().get(DEBUG_ENABLED_KEY, False)
                persistent_enabled = getConfigData().get(PERSISTENT_STORAGE_KEY, False)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(cobalt_url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            version = data.get("cobalt", {}).get("version", "Unknown")
                            services = data.get("cobalt", {}).get("services", [])
                            duration_limit = data.get("cobalt", {}).get("durationLimit", "Unknown")
                            
                            ffmpeg_version = await run_docker_cmd("docker run --rm jrottenberg/ffmpeg:latest -version")
                            ffmpeg_version = ffmpeg_version.split('\n')[0]
                            ffmpeg_version = re.sub(r'ffmpeg version (\d+\.\d+).*', r'ffmpeg version \1', ffmpeg_version)
                            
                            giflossy_version = await run_docker_cmd("docker run --rm dylanninin/giflossy gifsicle --version")
                            giflossy_version = giflossy_version.split('\n')[0]
                            
                            path_exists = os.path.exists(download_path)
                            path_writable = os.access(download_path, os.W_OK) if path_exists else False
                            
                            await msg.delete()
                            
                            status_content = (
                                f"**Cobalt Instance Status**\n"
                                f"URL: `{cobalt_url}`\n"
                                f"Version: `{version}`\n"
                                f"Duration Limit: `{duration_limit} seconds`\n"
                                f"Supported Services: `{', '.join(services)}`\n\n"
                                f"**🔄 Docker FFmpeg**: ✅ Working\n"
                                f"```{ffmpeg_version}```\n"
                                f"**🎨 Docker Giflossy**: ✅ Working\n"
                                f"```{giflossy_version}```\n"
                                f"**📁 Download Path**:\n"
                                f"```{download_path}```\n"
                                f"**🔍 Path Status**: {'✅' if path_exists else '❌'} Exists, {'✅' if path_writable else '❌'} Writable\n\n"
                                f"**⚙️ Features**:\n"
                                f"{'✅' if debug_enabled else '❌'} 🐛 Debug Mode\n"
                                f"{'✅' if persistent_enabled else '❌'} Persistent Storage\n"
                                f"**📤 Litterbox**: {getConfigData().get(LITTERBOX_EXPIRY_KEY, '24h')} expiry, {getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8)}MB limit\n\n"
                                f"**📊 Default Settings**:\n"
                                f"• 🎬 FPS: 15\n"
                                f"• 📏 Scale: 480:-1 (480px width, auto height)\n"
                                f"• ⏱️ Time Range: Entire video (if not specified)\n"
                                f"• 🔧 Optimization: Disabled by default\n"
                                f"• 💾 Storage: media subfolder when persistent"
                            )
                            
                            current_private = getConfigData().get("private")
                            updateConfigData("private", False)
                            
                            await forwardEmbedMethod(
                                channel_id=ctx.channel.id,
                                content=status_content,
                                title=f"{command_name} Status"
                            )
                            
                            updateConfigData("private", current_private)
                        else:
                            error_msg = f"❌ Cobalt instance at {cobalt_url} returned status {response.status}"
                            debug_log(error_msg, type_="ERROR")
                            await msg.edit(content=error_msg)
            except Exception as e:
                error_msg = f"❌ Could not connect to Cobalt instance at {cobalt_url}. Error: {str(e)}"
                debug_log(error_msg, type_="ERROR")
                await msg.edit(content=error_msg)
        
        else:
            await ctx.send(f"❌ Invalid command. Use `<p>{command_name} url <your_url>`, `<p>{command_name} path <download_path>`, `<p>{command_name} debug`, `<p>{command_name} persistent`, `<p>{command_name} lb <1|12|24|72>`, or `<p>{command_name} limit <size_mb>`")
    
    @bot.command(name="cobalt", aliases=["c"], description="Download media using Cobalt")
    async def cobalt_command(ctx, *, args: str = ""):
        """Handle Cobalt download commands"""
        await ctx.message.delete()
        
        # Handle configuration commands
        if args.lower().startswith(("url ", "path ", "debug", "persistent", "lb", "limit")):
            await handle_config_command(ctx, args, "cobalt")
            return
        
        # Handle download request
        if not args:
            await ctx.send("❌ Please provide a URL to download.")
            return
        
        # Validate that the first word is a URL before parsing
        first_word = args.split()[0].lower()
        if first_word in ["url", "path", "debug", "persistent", "lb", "limit", "status"]:
            await handle_config_command(ctx, args, "cobalt")
            return
        
        parsed_args = parse_cobalt_args(args)
        url_to_download = parsed_args["url"]
        
        if not url_to_download:
            await ctx.send("❌ Could not parse URL from arguments.")
            return
        
        msg = await ctx.send(f"⏳ Processing {url_to_download}...")
        
        try:
            # Download from Cobalt
            file_result = await download_from_cobalt(
                url_to_download,
                parsed_args["quality"],
                parsed_args["audio"],
                parsed_args["mode"]
            )

            file_paths = file_result if isinstance(file_result, list) else [file_result]
            size_threshold = float(getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8))

            for path in file_paths:
                file_size = os.path.getsize(path) / (1024 * 1024)
                if file_size > size_threshold:
                    await msg.edit(content="⏳ File exceeds Discord limit, uploading to litterbox.catbox.moe...")
                    try:
                        litterbox_url = await upload_to_litterbox(path)
                        await ctx.send(
                            f"📁 File uploaded to: {litterbox_url}\n⚠️ Note: This link will expire in {getConfigData().get(LITTERBOX_EXPIRY_KEY, '24h')}"
                        )
                        await msg.delete()
                    except Exception as upload_error:
                        await msg.edit(content=f"❌ Failed to upload to litterbox: {str(upload_error)}")
                else:
                    await msg.edit(content=f"⏳ Sending file ({file_size:.2f} MB)")
                    try:
                        await ctx.send(file=discord.File(path))
                        await msg.delete()
                    except Exception as e:
                        if "413 Payload Too Large" in str(e):
                            await msg.edit(content="⏳ File too large for Discord, uploading to litterbox.catbox.moe...")
                            try:
                                litterbox_url = await upload_to_litterbox(path)
                                await ctx.send(
                                    f"📁 File uploaded to: {litterbox_url}\n⚠️ Note: This link will expire in {getConfigData().get(LITTERBOX_EXPIRY_KEY, '24h')}"
                                )
                                await msg.delete()
                            except Exception as upload_error:
                                await msg.edit(content=f"❌ Failed to upload to litterbox: {str(upload_error)}")
                        else:
                            raise

                if not getConfigData().get(PERSISTENT_STORAGE_KEY, False):
                    try:
                        os.remove(path)
                        debug_log(f"Temporary file deleted: {path}", type_="SUCCESS")
                    except Exception as e:
                        debug_log(f"Error deleting temporary file: {str(e)}", type_="ERROR")
        
        except Exception as e:
            error_str = str(e)
            if "413 Payload Too Large" in error_str:
                limit_mb = getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8)
                user_msg = f"❌ File exceeds Discord's {limit_mb}MB limit. Try downloading with lower quality."
            elif "invalid or not supported by Cobalt" in error_str:
                user_msg = "❌ The URL you provided is invalid or not supported by Cobalt. Please check the URL and try again."
            elif "website is not supported by Cobalt" in error_str:
                user_msg = "❌ This website is not supported by Cobalt. Please try a different URL."
            elif "content is private or requires authentication" in error_str:
                user_msg = "❌ This content is private or requires authentication. Cobalt cannot access it."
            else:
                user_msg = f"❌ Error: {error_str}"
                if "0 bytes" in error_str:
                    user_msg += "\nThis might be due to anti-bot measures. Try again in a few minutes."
            debug_log(f"Error: {error_str}", type_="ERROR")
            await msg.edit(content=user_msg)
    
    @bot.command(name="cobaltgif", aliases=["cg"], description="Download and convert media to GIF using Cobalt")
    async def cobalt_gif_command(ctx, *, args: str = ""):
        """Handle Cobalt GIF conversion commands"""
        await ctx.message.delete()
        
        # Handle configuration commands
        if args.lower().startswith(("url ", "path ", "debug", "persistent", "lb", "limit")):
            await handle_config_command(ctx, args, "cobaltgif")
            return
        
        # Handle conversion request
        if not args:
            await ctx.send("❌ Please provide a URL to download and convert.")
            return
        
        # Validate that the first word is a URL before parsing
        first_word = args.split()[0].lower()
        if first_word in ["url", "path", "debug", "persistent", "lb", "limit", "status"]:
            await handle_config_command(ctx, args, "cobaltgif")
            return
        
        parsed_args = parse_gif_args(args)
        url_to_download = parsed_args["url"]
        
        if not url_to_download:
            await ctx.send("❌ Could not parse URL from arguments.")
            return
        
        msg = await ctx.send(f"⏳ Processing {url_to_download}...")
        
        try:
            # Step 1: Download video
            await msg.edit(content="⏳ Downloading video...")
            video_path = await download_from_cobalt(
                url_to_download,
                parsed_args["quality"],
                parsed_args["audio"],
                parsed_args["mode"]
            )
            
            # Step 2: Convert to GIF
            await msg.edit(content="⏳ Converting to GIF...")
            gif_path, final_size, original_size, should_upload = await convert_to_gif(
                video_path,
                parsed_args["fps"],
                parsed_args["scale"],
                parsed_args["time"],
                parsed_args["optimize"],
                parsed_args["speed"]  # Add speed parameter
            )
            
            # Step 3: Send the GIF
            await msg.edit(content="⏳ Sending GIF...")

            try:
                if should_upload:
                    await msg.edit(content="⏳ GIF exceeds Discord limit, uploading to litterbox.catbox.moe...")
                    try:
                        litterbox_url = await upload_to_litterbox(gif_path)
                        size_info = f"GIF Size: {final_size:.2f}MB"
                        if original_size is not None:
                            size_reduction = ((original_size - final_size) / original_size) * 100
                            size_info += f" (Reduced by {size_reduction:.1f}%)"
                        await ctx.send(f"{size_info}\n📁 Uploaded to: {litterbox_url}\n⚠️ Note: This link will expire in {getConfigData().get(LITTERBOX_EXPIRY_KEY, '24h')}")
                        await msg.delete()
                    except Exception as upload_error:
                        await msg.edit(content=f"❌ Failed to upload to litterbox: {str(upload_error)}")
                else:
                    if original_size is not None:
                        size_reduction = ((original_size - final_size) / original_size) * 100
                        await ctx.send(f"GIF Size: {final_size:.2f}MB (Reduced by {size_reduction:.1f}%)", file=discord.File(gif_path))
                    else:
                        await ctx.send(f"GIF Size: {final_size:.2f}MB", file=discord.File(gif_path))
                    await msg.delete()
            except Exception as e:
                if "413 Payload Too Large" in str(e):
                    await msg.edit(content="⏳ GIF exceeds Discord limit, uploading to litterbox.catbox.moe...")
                    try:
                        litterbox_url = await upload_to_litterbox(gif_path)
                        size_info = f"GIF Size: {final_size:.2f}MB"
                        if original_size is not None:
                            size_reduction = ((original_size - final_size) / original_size) * 100
                            size_info += f" (Reduced by {size_reduction:.1f}%)"
                        await ctx.send(f"{size_info}\n📁 Uploaded to: {litterbox_url}\n⚠️ Note: This link will expire in {getConfigData().get(LITTERBOX_EXPIRY_KEY, '24h')}")
                        await msg.delete()
                    except Exception as upload_error:
                        await msg.edit(content=f"❌ Failed to upload to litterbox: {str(upload_error)}")
                else:
                    raise
            
            # Clean up if not persistent
            if not getConfigData().get(PERSISTENT_STORAGE_KEY, False):
                try:
                    os.remove(video_path)
                    os.remove(gif_path)
                    debug_log("Temporary files deleted", type_="SUCCESS")
                except Exception as e:
                    debug_log(f"Error deleting temporary files: {str(e)}", type_="ERROR")
        
        except Exception as e:
            error_str = str(e)
            if "413 Payload Too Large" in error_str:
                limit_mb = getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8)
                user_msg = f"❌ GIF exceeds Discord's {limit_mb}MB limit. Try using -optimize, reducing quality, or shortening duration."
            elif "invalid or not supported by Cobalt" in error_str:
                user_msg = "❌ The URL you provided is invalid or not supported by Cobalt. Please check the URL and try again."
            elif "website is not supported by Cobalt" in error_str:
                user_msg = "❌ This website is not supported by Cobalt. Please try a different URL."
            elif "content is private or requires authentication" in error_str:
                user_msg = "❌ This content is private or requires authentication. Cobalt cannot access it."
            else:
                user_msg = f"❌ Error: {error_str}"
                if "0 bytes" in error_str:
                    user_msg += "\nThis might be due to anti-bot measures. Try again in a few minutes."
            debug_log(f"Error: {error_str}", type_="ERROR")
            await msg.edit(content=user_msg)

    @bot.command(name="v2g", description="Convert video to GIF using FFmpeg with custom parameters")
    async def v2g_command(ctx, *, args: str = ""):
        """Handle direct FFmpeg video to GIF conversion"""
        await ctx.message.delete()
        
        # Handle configuration commands
        if args.lower().startswith(("url ", "path ", "debug", "persistent", "lb", "limit")):
            await handle_config_command(ctx, args, "v2g")
            return

        video_path = None
        parsed_args = None

        # If no args, attempt to use the previous message
        if not args:
            history = [m async for m in ctx.channel.history(limit=2)]
            if len(history) < 2:
                return
            prev_msg = history[1]
            if prev_msg.attachments:
                attachment = prev_msg.attachments[0]
                if not any(attachment.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']):
                    return
                msg = await ctx.send("downloading attachment from previous message...")

                try:
                    video_path = await download_file(attachment.url, attachment.filename)
                    parsed_args = parse_v2g_args("")
                except Exception as e:
                    await msg.edit(content=f"error downloading attachment: {str(e)}")

                    return
            else:
                match = re.search(r'https?://\S+', prev_msg.content)
                if match and any(match.group(0).split('?')[0].lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']):
                    args = match.group(0)
                else:
                    return

        # Validate that the first word is a URL before parsing
        first_word = args.split()[0].lower() if args else ""
        if first_word in ["url", "path", "debug", "persistent", "lb", "limit", "status"]:
            await handle_config_command(ctx, args, "v2g")
            return

        if parsed_args is None:
            parsed_args = parse_v2g_args(args)

        # Check for attachment
        if video_path is None and ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if not any(attachment.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']):
                await ctx.send("please attach a video file (mp4, mov, avi, mkv, webm)")
                return
            
            msg = await ctx.send("downloading attachment...")
            try:
                video_path = await download_file(attachment.url, attachment.filename)
            except Exception as e:
                await msg.edit(content=f"error downloading attachment: {str(e)}")
                return
        elif video_path is None:
            # Handle URL
            parsed_args = parse_v2g_args(args)
            url_to_download = parsed_args["url"]
            
            if not url_to_download:
                await ctx.send("could not parse url from arguments.")
                return
            
            # Check if URL is from Twitter/X
            if any(domain in url_to_download.lower() for domain in ['twitter.com', 'x.com']):
                debug_log(f"Twitter/X URL detected: {url_to_download}", type_="INFO")
                await ctx.send("twitter/x urls are not supported in direct v2g mode. please use the cobalt gif converter instead:\n`<p>cg <url> [options]`")
                return
            
            msg = await ctx.send(f"downloading video...")
            try:
                # Download directly without using Cobalt
                video_path = await download_file(url_to_download, "input_video.mp4")
            except Exception as e:
                error_str = str(e)
                debug_log(f"Download error for URL {url_to_download}: {error_str}", type_="ERROR")
                
                # Provide more specific error messages
                if "Header value is too long" in error_str:
                    await msg.edit(content="this website's headers are too large for direct download. please use the cobalt gif converter instead:\n`<p>cg <url> [options]`")
                elif "403" in error_str:
                    await msg.edit(content="access denied. the website is blocking direct downloads. please use the cobalt gif converter instead:\n`<p>cg <url> [options]`")
                elif "429" in error_str:
                    await msg.edit(content="too many requests. please wait a few minutes before trying again.")
                else:
                    await msg.edit(content=f"error downloading video: {error_str}")
                return
        
        # Setup directories
        work_dir = ensure_download_dir(persistent=True, workdir=True)
        output_dir = ensure_download_dir(persistent=True)
        
        # Generate filename
        original_filename = os.path.splitext(os.path.basename(video_path))[0]
        original_filename = re.sub(r'[^\w\-_]', '_', original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gif_filename = f"{original_filename}_{timestamp}.gif"
        gif_path = os.path.join(output_dir, gif_filename)
        
        # Prepare FFmpeg parameters based on flags
        ffmpeg_params = []
        
        # Time parameters
        if parsed_args["time"]:
            start_time, end_time = parsed_args["time"].split("-")
            start_float = float(start_time)
            end_float = float(end_time)
            duration = str(end_float - start_float)
            ffmpeg_params.extend([f"-ss {start_time}", f"-t {duration}"])
        
        # Video filter parameters
        vf_parts = []
        
        # Basic filters
        vf_parts.append(f"fps={parsed_args['fps']}")
        vf_parts.append(f"scale={parsed_args['scale']}:flags=lanczos")
        
        # Add speed modification if specified
        if parsed_args["speed"] != 1.0:
            vf_parts.append(f"setpts={1/parsed_args['speed']}*PTS")
        
        # Palette generation
        if parsed_args["optimize"]:
            palette_params = f"palettegen=max_colors={parsed_args['colors']}:reserve_transparent=1"
            vf_parts.append(f"split[s0][s1];[s0]{palette_params}[p];[s1][p]paletteuse={parsed_args['dither']}")
        else:
            vf_parts.append(f"split[s0][s1];[s0]palettegen=max_colors={parsed_args['colors']}[p];[s1][p]paletteuse")
        
        ffmpeg_params.append(f'-vf "{",".join(vf_parts)}"')
        
        # Loop parameter
        if parsed_args["loop"] >= 0:
            ffmpeg_params.append(f"-loop {parsed_args['loop']}")
        
        # Convert to GIF using FFmpeg
        try:
            await msg.edit(content="converting to gif...")
            ffmpeg_cmd = (
                f'docker run --rm -v "{os.path.dirname(video_path)}:/input" -v "{output_dir}:/output" jrottenberg/ffmpeg '
                f'-y -i /input/{os.path.basename(video_path)} '
                f'{" ".join(ffmpeg_params)} '
                f'/output/{gif_filename}'
            )
            debug_log(f"Running FFmpeg command: {ffmpeg_cmd}", type_="INFO")
            await run_docker_cmd(ffmpeg_cmd)
            
            if not os.path.exists(gif_path):
                raise Exception("GIF file not found")
            
            # Check size
            final_size = os.path.getsize(gif_path) / (1024 * 1024)
            size_threshold = float(getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8))
            if final_size > size_threshold:
                await msg.edit(content="gif exceeds discord limit, uploading to litterbox.catbox.moe...")
                try:
                    litterbox_url = await upload_to_litterbox(gif_path)
                    await ctx.send(f"gif uploaded to: {litterbox_url}\nnote: this link will expire in {getConfigData().get(LITTERBOX_EXPIRY_KEY, '24h')}")
                    await msg.delete()
                except Exception as upload_error:
                    await msg.edit(content=f"failed to upload to litterbox: {str(upload_error)}")
                return
            
            # Send the GIF
            await msg.edit(content=f"sending gif ({final_size:.2f}mb)...")
            await ctx.send(file=discord.File(gif_path))
            await msg.delete()
            
            # Clean up
            if not getConfigData().get(PERSISTENT_STORAGE_KEY, False):
                try:
                    os.remove(video_path)
                    os.remove(gif_path)
                    debug_log("Temporary files deleted", type_="SUCCESS")
                except Exception as e:
                    debug_log(f"Error deleting temporary files: {str(e)}", type_="ERROR")
        
        except Exception as e:
            error_str = str(e)
            if "413 Payload Too Large" in error_str:
                limit_mb = getConfigData().get(LITTERBOX_SIZE_THRESHOLD_MB_KEY, 8)
                user_msg = f"gif exceeds discord's {limit_mb}MB limit. try using -optimize, reducing quality, or shortening duration."
            elif "Option vf (set video filters) cannot be applied to input url" in error_str:
                debug_log(f"FFmpeg command error: {error_str}", type_="ERROR")
                user_msg = "error processing video. please try again with different parameters."
            elif "Error parsing options for input file" in error_str:
                debug_log(f"FFmpeg input error: {error_str}", type_="ERROR")
                user_msg = "error reading video file. please check if the file is valid."
            elif "Error opening input files" in error_str:
                debug_log(f"FFmpeg file access error: {error_str}", type_="ERROR")
                user_msg = "error accessing video file. please try again."
            else:
                user_msg = f"error: {error_str}"
            debug_log(f"Error: {error_str}", type_="ERROR")
            await msg.edit(content=user_msg)

# Initialize the script
unified_cobalt_script()

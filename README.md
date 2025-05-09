# Unified Cobalt Tools

A comprehensive suite of tools for downloading media and converting videos to GIFs, designed for use with Nighty.

## Features

- **Cobalt Downloader**: Download media from various platforms using the Cobalt API
- **Cobalt GIF Converter**: Download and convert videos to optimized GIFs
- **Direct FFmpeg GIF Converter**: Convert videos to GIFs with advanced FFmpeg parameters

### Key Features
- Download media from supported platforms
- Convert videos to GIFs with customizable parameters
- Optimize GIFs for size and quality
- Automatic fallback to litterbox.catbox.moe for large files
- Persistent storage option
- Debug mode for troubleshooting
- Configurable download paths and Cobalt instance URLs

## Docker Setup

1. Install Docker and Docker Compose:
   - Windows/Mac: Download Docker Desktop from docker.com
   - Linux: Install docker and docker-compose packages

2. Create a directory for Cobalt:
   ```bash
   mkdir cobalt && cd cobalt
   ```

3. Create `docker-compose.yml`:
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
   ```bash
   docker-compose up -d
   ```

5. Pull required images:
   ```bash
   docker pull jrottenberg/ffmpeg:latest
   docker pull dylanninin/giflossy:latest
   ```

## Usage

### 1. Cobalt Downloader (`<p>c` or `<p>cobalt`)
- Download media: `<p>c <url> [--720p] [--wav] [--audio]`
- Configure: `<p>c url|path|debug|persistent|status`

### 2. Cobalt GIF (`<p>cg` or `<p>cobaltgif`)
- Convert to GIF: `<p>cg <url> [--fps=15] [--scale=480:-1] [--time=0-30] [--optimize] [--720p]`
- Configure: `<p>cg url|path|debug|persistent|status`

### 3. Direct FFmpeg GIF (`<p>v2g`)
- Convert to GIF: `<p>v2g <url or attachment> [--fps=15] [--scale=480:-1] [--time=0-30] [--optimize] [--720p] [--speed=<factor>]`
- Configure: `<p>v2g url|path|debug|persistent|status`

## Parameters

### Cobalt Downloader
- Quality: `--144p` to `--4320p`, `--max`
- Audio: `--wav`, `--ogg`, `--opus`, `--best`
- Mode: `--audio`, `--mute`

### Cobalt GIF
- Quality: `--144p` to `--4320p`, `--max`
- FPS: `--fps=<number>` (default: 15)
- Scale: `--scale=<width>:-1` (default: 480:-1)
- Time: `--time=<start>-<end>` (in seconds)
- Optimize: `--optimize` (reduces file size)

### Direct FFmpeg GIF
- Quality: `--144p` to `--4320p`, `--max`
- FPS: `--fps=<number>` (default: 15)
- Scale: `--scale=<width>:-1` (default: 480:-1)
- Time: `--time=<start>-<end>` (in seconds)
- Optimize: `--optimize` (reduces file size)
- Loop: `--loop=<number>` (default: 0, -1 for infinite)
- Dither: `--dither=<method>` (default: bayer:bayer_scale=5)
- Colors: `--colors=<number>` (default: 256)
- Speed: `--speed=<factor>` (default: 1.0, e.g. 0.5 for half speed, 2.0 for double speed)

## Examples

1. Download a video in 720p quality:
   ```
   <p>c https://www.youtube.com/watch?v=dQw4w9WgXcQ --720p
   ```

2. Download audio only in WAV format:
   ```
   <p>c https://www.youtube.com/watch?v=dQw4w9WgXcQ --wav --audio
   ```

3. Convert a video to a GIF with 10 FPS and optimize for size:
   ```
   <p>cg https://www.youtube.com/watch?v=dQw4w9WgXcQ --fps=10 --optimize
   ```

4. Convert a specific part of a video to a GIF (first 15 seconds):
   ```
   <p>cg https://www.youtube.com/watch?v=dQw4w9WgXcQ --time=0-15 --scale=640:-1
   ```

5. Configure Cobalt to use a custom URL:
   ```
   <p>c url http://my-cobalt-server:9000
   ```

6. Enable persistent storage to keep downloaded files:
   ```
   <p>c persistent
   ```

7. Check the status of your Cobalt setup:
   ```
   <p>c status
   ```

## Notes

- The `--optimize` flag is only available for GIF operations
- All commands share the same configuration system
- Files are processed locally in Docker containers
- Discord has an 8MB file size limit
- URLs must start with http:// or https://
- If you get an "invalid link" error, check that the URL is correct and supported by Cobalt
- Large files (>8MB) are automatically uploaded to litterbox.catbox.moe
- Debug mode provides detailed logging for troubleshooting
- Persistent storage keeps files in the configured download path

## License

MIT License - See LICENSE file for details 

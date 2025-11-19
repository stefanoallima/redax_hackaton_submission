# Hero Demo Video Assets

This directory contains the video assets for the landing page hero section.

## Required Files

### 1. hero_demo.mp4
- **Format**: MP4 (H.264 codec)
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 60 FPS
- **Duration**: 30-45 seconds
- **File Size**: Target <5MB (use compression)
- **Content**: Complete redaction workflow demonstration

#### Scenes (from VIDEO_DEMO_GUIDE.md):
1. **Upload** (5s) - Drag PDF file into desktop app
2. **Processing** (8s) - AI analyzing document with progress indicators
3. **Review** (10s) - User reviewing and accepting/rejecting detected PII
4. **Export** (8s) - Download redacted PDF with success animation
5. **Stats** (5s) - Show time savings (2 hours → 45 seconds)

### 2. hero_demo.webm (Optional)
- **Format**: WebM (VP9 codec)
- **Purpose**: Fallback for browsers that don't support MP4
- **Same specs as MP4**

### 3. hero_demo_poster.jpg
- **Format**: JPEG
- **Resolution**: 1920x1080
- **File Size**: <200KB
- **Content**: Screenshot of the upload screen (first frame of video)

## Creating the Video

Follow the complete guide in `VIDEO_DEMO_GUIDE.md` at the root of the project.

### Quick Steps:

1. **Record** using OBS Studio:
   ```bash
   # Settings:
   - Canvas: 1920x1080
   - FPS: 60
   - Encoder: H.264
   - Bitrate: 8000 Kbps
   ```

2. **Edit** using DaVinci Resolve or Premiere Pro:
   - Add text overlays for each scene
   - Add smooth transitions (0.3s fade)
   - Add subtle background music (optional)
   - Export at 1920x1080@60fps

3. **Compress** to <5MB:
   ```bash
   # Using FFmpeg
   ffmpeg -i hero_demo_raw.mp4 \
     -vcodec libx264 \
     -crf 28 \
     -preset slow \
     -vf scale=1920:1080 \
     -r 60 \
     -an \
     hero_demo.mp4
   ```

4. **Create WebM** (optional):
   ```bash
   ffmpeg -i hero_demo.mp4 \
     -c:v libvpx-vp9 \
     -crf 35 \
     -b:v 0 \
     hero_demo.webm
   ```

5. **Extract poster frame**:
   ```bash
   ffmpeg -i hero_demo.mp4 \
     -ss 00:00:00 \
     -vframes 1 \
     -q:v 2 \
     hero_demo_poster.jpg
   ```

## Placeholder Until Video is Ready

The HeroSection component is designed to gracefully handle missing video files:
- Shows loading spinner while video loads
- Falls back to poster image if video fails to load
- Provides accessible alt text

You can temporarily use a static image or animated GIF until the full video is produced.

## Testing

Once you add the video files:

1. Place `hero_demo.mp4` in this directory
2. Place `hero_demo_poster.jpg` in this directory
3. Restart the Next.js dev server
4. Navigate to http://localhost:3000
5. Check that:
   - Video auto-plays (muted)
   - Play/pause button works
   - Poster image shows while loading
   - Video loops seamlessly

## File References

The HeroSection component (`frontend/app/components/HeroSection.tsx`) references these files:

```tsx
<video poster="/videos/hero_demo_poster.jpg">
  <source src="/videos/hero_demo.mp4" type="video/mp4" />
  <source src="/videos/hero_demo.webm" type="video/webm" />
</video>
```

All paths are relative to the `public/` directory.

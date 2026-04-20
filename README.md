# Medialib v2

A Booru-like media library designed for storing, categorizing, and managing content.

The system is primarily oriented toward local image collections, but it also supports video and looped animations (including GIFs). Tag-based indexing and a custom **Domain Specific Language (DSL)** implementation allow for content searching as fast as Booru-style imageboards, far exceeding traditional tree-like folder hierarchies.

## Key Features

- **Network Access**: Access your collection from any device within your local network.
- **Access Control**: Manage content access using filtering mechanisms and user groups (e.g., the `nsfw` group).
- **Automated Import**: Upload content manually or automatically using the Derpibooru-Dl loader, which imports tags directly from the source.
- **Compatibility Adaptability**: Automatic processing of uploaded content to create a set of representations based on device compatibility levels.
- **Smart Rendering**: Displays content optimized for the compatibility level of the current device.
- **AI-Powered Tagging**: Simplifies routine tagging tasks with an AI tagger and tag implication mechanisms (automatically pulling abstract tags based on specific ones).
- **Hybrid Deduplication**: A combination of SHA256 and LAB-based perceptual hashing (phash) prevents duplicate uploads and identifies visually similar images.
- **Modern Compression**: Utilization of **WEBP** and **AVIF** formats reduces total collection size by approximately 50%. The `pyvips` library enables high-quality 10-bit AVIF representations with low RAM usage even for massive source files.

## Technology Stack

- **Backend**: Django 6.x, PostgreSQL.
- **Task Queue**: Celery + Redis (for heavy media processing).
- **Media Tools**: FFmpeg (video), pyvips (images), ImageHash (analytics), and Pillow.
- **Frontend**: Vanilla JS, Web Components, and CSS Variables (for easy theme switching).

## Project Architecture

- `media_receiving`: File ingestion, validation, and task management.
- `image_processing`: Core engine for representation processing, analysis, hash generation, and comparison.
- `medialib`: UI logic, collections, albums, and tags.
- `base`: Shared enums, functions, and base classes.

## Compatibility Levels (CL) Concept

The Compatibility Level concept is adapted from the earlier ACLMMP project. In Medialib v2, the level numbering order is determined by the formula $4 - X$ from initial ACLMMP definition. Detailed specifications can be found in `image_processing.core.specification`.

### Level Overview:

1. **CL1**: The minimum level supported by Medialib v2. Supports **WEBP** images, H.264 looped animations (60fps), or VP9 720p 30fps video in **WebM**.
2. **CL2**: Modern low-power devices. Capable of decoding **AVIF** (up to 2048x2048 at 10-bit), VP9 1080p (8-bit), or AV1 720p.
3. **CL3**: Mid-range PC level. Supports AVIF 4096x4096, native **SVG** rendering, AV1 1080p 60fps, or VP9 up to 4K.
4. **CL4**: High-performance devices capable of decoding **AV1 in 4K** at 60fps.

---

_Note: CL0 is reserved for legacy devices (PNG/JPEG up to 1024x1024) and is not currently targeted by this project._

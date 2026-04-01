# Vibereader Menu Bar

Native macOS menu bar app that shows tech news headlines from a remote vibereader API.

![macOS 13+](https://img.shields.io/badge/macOS-13%2B-blue) ![Swift 5.9](https://img.shields.io/badge/Swift-5.9-orange)

## Features

- **Menu bar icon** — "V" in your menu bar, no Dock icon
- **Live headlines** — top 15 articles with score, source, and category tags
- **Click to read** — opens articles in your default browser
- **Auto-refresh** — fetches new articles every 60 seconds
- **Refresh Feed** — manual refresh triggers a server-side fetch
- **Configurable API** — point to any vibereader backend via environment variable

## Requirements

- macOS 13 (Ventura) or later
- Swift 5.9+ (included with Xcode 15+)
- A running [vibereader web dashboard](https://github.com/user/vibereader) backend

## Build & Run

```bash
git clone <this-repo>
cd vibereader-menubar
swift build
.build/debug/VibereaderMenuBar
```

## Configuration

Set the `VIBEREADER_API` environment variable to point to your backend:

```bash
# Default: http://43.134.177.69:8888
export VIBEREADER_API=http://your-vps-ip:8888
.build/debug/VibereaderMenuBar
```

## API Contract

The app expects these endpoints on the backend:

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/api/articles` | `{"articles": [...], "fetched_at": "ISO8601"}` |
| POST | `/refresh` | `{"status": "ok"}` |

Each article object:
```json
{
  "id": "string",
  "title": "string",
  "url": "string",
  "source": "string",
  "score": 2.5,
  "categories": ["ai-ml", "web-dev"]
}
```

## Launch at Login

Copy the built binary to `/usr/local/bin/` and add a login item:

```bash
swift build -c release
cp .build/release/VibereaderMenuBar /usr/local/bin/
```

Then add `/usr/local/bin/VibereaderMenuBar` to System Settings > General > Login Items.

## Project Structure

```
Package.swift                              — SPM manifest
Sources/VibereaderMenuBar/
  main.swift                               — AppKit menu bar app (~190 lines)
  Info.plist                               — LSUIElement=true (no Dock icon)
```

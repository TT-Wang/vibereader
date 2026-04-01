# Vibereader Menu Bar

Native macOS menu bar app that shows tech news headlines from a remote vibereader API.

![macOS 13+](https://img.shields.io/badge/macOS-13%2B-blue) ![Swift 5.9](https://img.shields.io/badge/Swift-5.9-orange)

## Features

- **Menu bar popover** — "V" in your menu bar, click for a SwiftUI popover panel (no Dock icon)
- **Live headlines** — top 15 articles with colored score badges, category pills, and source labels
- **Search/filter** — live search bar to filter articles by text
- **Click to read** — opens articles in your default browser, popover stays open
- **Auto-refresh** — fetches new articles every 60 seconds with smooth animations
- **Refresh Feed** — manual refresh with spinning indicator
- **Configurable API** — point to any vibereader backend via environment variable

## Requirements

- macOS 13 (Ventura) or later
- Swift 5.9+ (included with Xcode 15+)
- A running [vibereader web dashboard](https://github.com/user/vibereader) backend

## Build & Run

```bash
git clone https://github.com/TT-Wang/vibereader-menubar.git
cd vibereader-menubar
rm -rf .build
swift build
.build/debug/VibereaderMenuBar 2>&1
```

> **Note:** Always use `rm -rf .build` before building after a `git pull` to ensure a clean build.

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
  main.swift                               — AppKit + SwiftUI popover app (~290 lines)
  Info.plist                               — LSUIElement=true (no Dock icon)
```

# Vibereader

Curated tech news dashboard. One command to install, one command to run.

## Install

```bash
curl -sL https://raw.githubusercontent.com/TT-Wang/vibereader-menubar/main/install.sh | bash && source ~/.zshrc
```

## Run

```bash
vibereader             # Web dashboard at http://localhost:8888
vibereader-bg          # Silent backend (for menubar app)
VibereaderMenuBar      # macOS menu bar app (if Swift is installed)
```

## What You Get

- Live headlines from **15 sources** (HN, TechCrunch, Wired, Ars Technica, CoinDesk, Quanta, and more)
- Articles scored by popularity + recency
- Category tags (AI/ML, web dev, crypto, science, security, etc.)
- One-click to read any article
- Works with only `feedparser` installed — `aiohttp` is optional (makes fetching faster)

## Troubleshooting

| Problem | Fix |
|---|---|
| `vibereader: command not found` | `source ~/.zshrc` or restart terminal |
| No articles showing | Wait a few seconds, click Refresh |
| `pip install failed` | `python3 -m pip install --user feedparser aiohttp` |

## Also: Claude Code Plugin

Get articles pushed in your terminal while Claude works:

```bash
claude plugin add github:TT-Wang/vibereader
```

## License

MIT

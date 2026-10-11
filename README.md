# 📺 YouTube Live Manager

A desktop application for creating YouTube live broadcasts (Full HD and Shorts) bound to fixed RTMP stream keys, with multiple saved profiles.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-Latest-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

- 🎬 **YouTube API Integration** — Creates broadcasts on your channel via YouTube Data API v3
- 🔑 **Fixed RTMP keys** — Each live type binds to a stream key you created once in YouTube Studio, so OBS settings never change
  - Separate keys for Full HD and Shorts
  - Keys are stored locally in `client-secret/` (git-ignored)
- 📺 **Full HD + Shorts** — Create either or both in one click; Shorts gets its own thumbnail and a ` | SHORTS` title suffix
- 🗂️ **Multiple profiles** — One tab per stream setup (title, tags, description, thumbnails), saved automatically
- 🧪 **Test Mode** — Private, ultra-low-latency broadcasts plus a button to delete them afterwards
- ⛔ **Cancel & rollback** — Cancelling or failing mid-way deletes the broadcasts already created (never the RTMP keys)

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:WeineOlliver/youtube-live-manager.git
   cd youtube-live-manager
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure YouTube API**
   - Set up a Google API project at [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the YouTube Data API v3
   - Create OAuth 2.0 credentials (Desktop app) and save the JSON in `client-secret/`

5. **Create the RTMP keys in YouTube Studio**
   - In YouTube Studio → Go live → Stream, create one reusable stream key for Full HD and another for Shorts
   - Paste each one in the matching "Chave RTMP" field at the top of the app

---

## 🚀 Quick Start

Run the application:
```bash
python main.py
```

This launches the YouTube Live Manager desktop application with the full dashboard interface.

---

## 📁 Project Structure

```
youtube-live-manager/
├── main.py                 # Application entry point
├── requirements.txt        # Project dependencies
├── config.json             # Saved profiles and settings
├── enhancements.md         # Feature roadmap & planned enhancements
├── client-secret/          # OAuth credentials, token and RTMP keys (git-ignored)
├── core/
│   ├── youtube_api.py      # YouTube API wrapper (broadcasts, RTMP key lookup, cleanup)
│   └── state.py            # Profiles, config and RTMP key persistence
├── ui/
│   ├── main_window.py      # Main window: token status, test mode, RTMP keys, tabs
│   ├── config_tab.py       # Per-profile tab (content, thumbnails, actions, log)
│   └── workers.py          # Background threads that create/delete broadcasts
└── tests/
    ├── test_state.py
    ├── test_workers.py
    └── test_youtube_api.py
```

---

## 🔧 Configuration

The `config.json` file stores your profiles and global settings:

```json
{
  "profiles": [
    {
      "name": "My Stream",
      "title": "Your Stream Title",
      "tags": "tag1, tag2, tag3",
      "description": "Stream description",
      "thumbnail_normal": "path/to/thumbnail.png",
      "thumbnail_shorts": "path/to/shorts-thumbnail.png",
      "enable_fhd": true,
      "enable_shorts": true
    }
  ],
  "active_profile_index": 0,
  "test_mode": false
}
```

The RTMP keys are not stored here: they live in `client-secret/stream_key.txt` (Full HD) and `client-secret/stream_key_shorts.txt` (Shorts).

---

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=core --cov=ui
```

---

## 🎯 Upcoming Features

Check [enhancements.md](enhancements.md) for planned features and improvements, including:
- Abort functionality with log-based decision making

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Create a new branch for your feature
2. Make your changes and commit with clear messages
3. Push to your fork and submit a pull request

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

---

## 📧 Contact

For questions or support, reach out to:
- **Email**: contato@olliverw9.com.br
- **Discord**: [Join Community](https://discord.gg/2QCvjBqNcM)
- **Instagram**: [@olliverw9](https://instagram.com/olliverw9)
- **Twitter**: [@olliverw9](https://twitter.com/olliverw9)

---

**Made with ❤️ by [OlliverW9](https://github.com/WeineOlliver)**

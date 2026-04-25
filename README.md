# 📺 YouTube Live Manager

A powerful desktop application for managing YouTube live streams with an intuitive dashboard, automated polls, and YouTube API integration.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-Latest-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

- 🎬 **YouTube API Integration** — Seamlessly connect to your YouTube channel
- 📋 **Dashboard Management** — Configure livestream metadata with a user-friendly form
  - Video title, tags, and description
  - Thumbnail management (Full HD & Shorts formats)
  - Custom poll questions and options
- 🤖 **Poll Automation** — Automatically manage polls during livestreams
- 💾 **State Persistence** — Save and load your configuration settings
- 🧪 **Test Mode** — Safe testing with built-in test mode controls
- ⚡ **Performance Optimized** — Responsive UI with background workers

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
   - Create OAuth 2.0 credentials
   - Place your credentials in the appropriate location

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
├── config.json            # Default configuration template
├── enhancements.md        # Feature roadmap & planned enhancements
├── core/
│   ├── __init__.py
│   ├── youtube_api.py     # YouTube API wrapper & integration
│   ├── poll_automation.py # Poll automation logic
│   └── state.py           # State management & persistence
├── ui/
│   ├── __init__.py
│   ├── main_window.py     # Main application window
│   └── workers.py         # Background worker threads
└── tests/
    ├── conftest.py        # Pytest configuration
    ├── test_state.py      # State management tests
    └── test_youtube_api.py # API integration tests
```

---

## 🔧 Configuration

The `config.json` file stores your livestream settings:

```json
{
  "title": "Your Stream Title",
  "tags": "tag1, tag2, tag3",
  "description": "Stream description",
  "thumbnail_normal": "path/to/thumbnail.png",
  "thumbnail_shorts": "path/to/shorts-thumbnail.png",
  "poll_fullhd_question": "Your poll question",
  "poll_fullhd_options": "Option 1\nOption 2\nOption 3",
  "test_mode": true
}
```

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
- Livestream deletion options in test mode
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

# 🎵 Radio Scrobbler

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/charliermarsh/ruff)

A Python application that scrobbles songs played on internet radio stations to Last.fm and Spotify.

## 🚀 Features

- [x] Scrobbles songs played on internet radio stations to Last.fm and Spotify
- [x] Supports configuration via YAML file
- [x] **Plugin-based architecture** for supporting multiple radio stream formats
- [x] **Strategy pattern** implementation for extensible stream parsing
- [x] Support for ICY metadata streams (SHOUTcast/Icecast)
- [x] Support for JSON API-based track information
- [x] Support for RSS/XML feed-based track information
- [x] Auto-detection of stream formats
- [x] Multiple radio station support with different parsers
- [ ] [Coming Soon] GUI version

## 📦 Installation

```bash
pip install .
```

## 📖 Usage

### Run CLI

```bash
radio-scrobble config.yaml
```

## ⚙️ Configuration

The project requires a configuration file in YAML format (`config.yaml`). The structure of the configuration file should be as follows:

```yaml
lastfm:
  api_key: key
  shared_secret: secret
  user_name: user
  md5_password: hash

spotify:
  client_id: YOUR_SPOTIFY_CLIENT_ID
  client_secret: YOUR_SPOTIFY_CLIENT_SECRET
  redirect_url: YOUR_SPOTIFY_REDIRECT_URL
  spotify_playlist_id: YOUR_SPOTIFY_PLAYLIST_ID

radios:
  # Traditional ICY metadata stream (auto-detected)
  - name: Radio 1
    stream_url: "http://us2.internet-radio.com:8443"
    
  # Radio station with JSON API for track info
  - name: "Modern Radio"
    stream_url: "http://modern-radio.example.com:8080/stream"
    parser_type: "JSON API Parser"
    parser_config:
      api_endpoint: "http://modern-radio.example.com/api/nowplaying"
      artist_field: "current_track.artist" 
      title_field: "current_track.title"
      
  # Radio station with RSS feed for track info  
  - name: "Classical FM"
    stream_url: "http://classical-fm.example.com:8000"
    parser_type: "RSS Parser"
    parser_config:
      rss_url: "http://classical-fm.example.com/nowplaying.xml"
      artist_tag: "artist"
      title_tag: "title"
```

### Last.fm Configuration

- 🔑 `api_key`: The API key obtained from Last.fm.
- 🔒 `shared_secret`: The shared secret obtained from Last.fm.
- 👤 `user_name`: The Last.fm username.
- 🔐 `md5_password`: The MD5 hash of the Last.fm password.

> You need an API account. It can be created [here](https://www.last.fm/api/account/create).

### Spotify Configuration

The spotify section is optional and allows you to configure scrobbling to Spotify. It should have the following properties:

- 🔑 `client_id`: Your Spotify client ID. Obtain this from the Spotify Developer Dashboard.
- 🔑 `client_secret`: Your Spotify client secret. Obtain this from the Spotify Developer Dashboard.
- 🔑 `redirect_url`: The redirect URL for your application. This can be set to <http://localhost:8888/callback> for console-based apps.
- 🎶 `spotify_playlist_id`: The ID of the playlist where scrobbled songs will be added.

> Auth data should be copied form spotify app. It could be simply created from [Dev dashboard](https://developer.spotify.com/dashboard)

> You can copy Share Link to playlist and copy id which follows `playlist/`. (Example: `https://open.spotify.com/playlist/<playlist id>?...`)

### Radio Configuration

The `radios` section allows you to specify multiple radio stations with different stream formats. Each radio station supports the following properties:

- 📻 `name`: The name of the radio station.
- 🔊 `stream_url`: The URL of the radio station's audio stream.
- 🔧 `parser_type` (optional): Explicit parser to use (e.g., "JSON API Parser", "RSS Parser"). If not specified, the system will auto-detect the format.
- ⚙️ `parser_config` (optional): Parser-specific configuration options.

#### Supported Stream Formats

- **ICY Metadata** (SHOUTcast/Icecast): Traditional internet radio streams with embedded metadata
- **JSON APIs**: Radio stations that provide track info via REST endpoints  
- **RSS/XML Feeds**: Stations that publish current track info in RSS or XML format
- **Custom Formats**: Easy to add new formats using the plugin architecture

See `example_config.yaml` and `docs/adding_new_stream_formats.md` for detailed configuration examples.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/ostfor/lastfm_radio_scrobbler/blob/master/LICENSE.md) file for details.

🎶 Enjoy scrobbling your favorite tunes to Last.fm and Spotify! 🎧

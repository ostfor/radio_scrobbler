import argparse
import logging
from pathlib import Path
import time
import datetime
from typing import Optional, List
import yaml

import pylast
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .config_schema import Config
from .stream_parsers import Track, StreamParserFactory

class RadioScrobbler:
    def __init__(self, config: Config):
        self.__logger = logging.getLogger(__name__)
        self.config = config
        self.track_old = None
        
        # Initialize stream parser factory
        self.parser_factory = StreamParserFactory()
        
        # Initialize stream parsers for each radio
        self.stream_parsers = []
        for radio in config.radios:
            parser = self.parser_factory.create_parser(
                stream_url=str(radio.stream_url),
                parser_type=radio.parser_type,
                config=radio.parser_config or {}
            )
            if parser:
                self.stream_parsers.append((radio.name, parser))
                self.__logger.info(f"Initialized parser for {radio.name}: {parser.get_parser_name()}")
            else:
                self.__logger.error(f"Failed to create parser for radio: {radio.name}")

        if not self.stream_parsers:
            raise ValueError("No valid stream parsers could be created")

        # Initialize Last.fm network
        self.network = pylast.LastFMNetwork(
            api_key=config.lastfm.api_key,
            api_secret=config.lastfm.shared_secret,
            username=config.lastfm.user_name,
            password_hash=config.lastfm.md5_password
        )

        # Initialize Spotify API client
        self.sp = None
        if self.config.spotify:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    scope='user-read-recently-played playlist-modify-private playlist-modify-public',
                    client_id=self.config.spotify.client_id,
                    client_secret=self.config.spotify.client_secret,
                    redirect_uri=self.config.spotify.redirect_url  # Optional, provide if necessary
                )
            )



    def search_spotify_track(self, track: Track) -> Optional[str]:
        # Search for the track
        if not self.sp:
            self.__logger.warning(f'Cannot search track beecause not authorised in spotify')
            return None
        search_query = f'artist:{track.artist} track:{track.title}'
        results = self.sp.search(search_query, type='track', limit=1)
        # Extract the track URI from the search results
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            return track_uri
        else:
            self.__logger.warning(f'Track {track} not found in spotify')
            return None

    def get_current_tracks(self) -> List[Track]:
        """Get current tracks from all configured radio streams.

        Returns:
            List of currently playing tracks from all available streams
        """
        tracks = []
        for radio_name, parser in self.stream_parsers:
            try:
                track = parser.get_current_track()
                if track:
                    tracks.append(track)
                    self.__logger.debug(f"Got track from {radio_name}: {track}")
                else:
                    self.__logger.debug(f"No track found for {radio_name}")
            except Exception as e:
                self.__logger.error(f"Error getting track from {radio_name}: {e}")
        
        return tracks
    
    def get_artist_track(self) -> Optional[Track]:
        """Get track from radio stream (backwards compatibility method).

        Returns:
            Track instance if track metadata found, None otherwise
        """
        tracks = self.get_current_tracks()
        return tracks[0] if tracks else None


    def scrobble(self, track: Track):
        """Scrobble one track

        Parameters
        ----------
        Ttrack : Track
            Track instance whic should be added
        """
        timestamp = datetime.datetime.now()
        self.network.scrobble(track.artist, track.title, timestamp)

        if self.sp and self.config.spotify:
            track_uri = self.search_spotify_track(track)
            # TODO: Add multiple items by one request
            if track_uri:
                self.sp.playlist_add_items(
                    self.config.spotify.spotify_playlist_id,
                    [track_uri]
                )

    def start_scrobbling(self):
        """Scrobbling tracks continiously"""
        while True:
            track = self.get_artist_track()
            if track and track != self.track_old:
                self.__logger.info(track)
                self.scrobble(track)
                self.track_old = track
            time.sleep(1)


def main():
    logger = logging.getLogger(__name__)
    # Parse args
    parser = argparse.ArgumentParser(
        description='Scrobble radio playlists to Last.fm and Spotify'
    )
    parser.add_argument(
        '--config', '-c',
        help='path to YAML configuration file',
        default=Path('~/.confiig/radio-scrobble/config.yaml')
    )
    args = parser.parse_args()

    if args.config:
        if Path(args.config).exists():
            with open(args.config, 'r') as config_file:
                config_data = yaml.safe_load(config_file)
            config = Config(**config_data)
        else:
            logger.error(f'Config {args.config} not found!')
            exit(1)

    # Start scrobbling
    scrobbler = RadioScrobbler(config)
    scrobbler.start_scrobbling()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    main()
"""JSON API stream parser for radio stations that provide track info via REST API."""

import json
from typing import Optional, Dict, Any
import requests

from .base import StreamParser, Track


class JsonApiStreamParser(StreamParser):
    """Parser for radio stations that provide current track info via JSON API.
    
    This parser handles radio stations that expose their current playing track
    information through REST APIs that return JSON data.
    
    Configuration options:
    - api_endpoint: The JSON API endpoint URL
    - artist_field: JSON field path for artist (e.g., "now_playing.artist")
    - title_field: JSON field path for title (e.g., "now_playing.title")
    - headers: Optional headers to send with API request
    """
    
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track from a JSON API.
        
        Returns:
            Track object if track metadata is found, None otherwise
        """
        api_endpoint = self.config.get('api_endpoint')
        if not api_endpoint:
            self.logger.error("JSON API parser requires 'api_endpoint' in configuration")
            return None
        
        try:
            headers = self.config.get('headers', {})
            response = requests.get(
                api_endpoint,
                headers=headers,
                timeout=self.config.get('timeout', 10)
            )
            response.raise_for_status()
            
            data = response.json()
            track = self._extract_track_from_json(data)
            
            if track:
                return self.clean_track_info(track)
                
        except requests.RequestException as e:
            self.logger.error(f"Error fetching JSON API {api_endpoint}: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in JSON API parser: {e}")
        
        return None
    
    def _extract_track_from_json(self, data: Dict[str, Any]) -> Optional[Track]:
        """Extract track information from JSON data.
        
        Args:
            data: The JSON data to parse
            
        Returns:
            Track object if parsing successful, None otherwise
        """
        artist_field = self.config.get('artist_field', 'artist')
        title_field = self.config.get('title_field', 'title')
        
        artist = self._get_nested_field(data, artist_field)
        title = self._get_nested_field(data, title_field)
        
        if not artist or not title:
            self.logger.warning(f"Could not extract artist/title from JSON data")
            return None
        
        # Clean up the values
        artist = str(artist).strip()
        title = str(title).strip()
        
        if not artist or not title or artist.lower() in ['unknown', 'n/a'] or title.lower() in ['unknown', 'n/a']:
            return None
        
        return Track(artist=artist, title=title)
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Optional[str]:
        """Get a nested field from JSON data using dot notation.
        
        Args:
            data: The JSON data
            field_path: Dot-separated path to the field (e.g., "now_playing.artist")
            
        Returns:
            Field value if found, None otherwise
        """
        try:
            current = data
            for key in field_path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            # Ensure we return a string or None
            return str(current) if current is not None else None
        except (KeyError, TypeError):
            return None
    
    @classmethod
    def can_handle(cls, stream_url: str) -> bool:
        """Check if this parser can handle the given stream URL.
        
        JSON API parser requires explicit configuration, so it doesn't
        auto-detect streams. It should only be used when explicitly
        configured for a specific radio station.
        
        Args:
            stream_url: The URL to check
            
        Returns:
            False - requires explicit configuration
        """
        # JSON API parser requires explicit configuration
        # It doesn't auto-detect streams
        return False
    
    @classmethod
    def get_parser_name(cls) -> str:
        """Get the name of this parser."""
        return "JSON API Parser"
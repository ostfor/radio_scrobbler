"""ICY metadata stream parser for SHOUTcast/Icecast streams."""

import re
from typing import Optional
import requests

from .base import StreamParser, Track


class IcyStreamParser(StreamParser):
    """Parser for ICY metadata streams (SHOUTcast/Icecast format).
    
    This parser handles streams that provide metadata through ICY protocol,
    which includes most traditional internet radio streams.
    """
    
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track from an ICY metadata stream.
        
        Returns:
            Track object if track metadata is found, None otherwise
        """
        try:
            response = requests.get(
                self.stream_url,
                headers={'Icy-MetaData': '1'},
                stream=True,
                timeout=self.config.get('timeout', 10)
            )
            response.raise_for_status()
            
            # Retrieve the Icy-MetaInt header
            icy_metaint_header = response.headers.get('icy-metaint')
            
            if not icy_metaint_header:
                self.logger.warning(f"No ICY metadata found for stream: {self.stream_url}")
                return None
            
            metaint = int(icy_metaint_header)
            
            for chunk in response.iter_content(chunk_size=metaint + 255):
                if len(chunk) <= metaint:
                    continue
                    
                # Extract metadata from the chunk
                metadata = self._decode_metadata(chunk[metaint:])
                track = self._parse_track_from_metadata(metadata)
                
                if track:
                    return self.clean_track_info(track)
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching ICY stream {self.stream_url}: {e}")
        except ValueError as e:
            self.logger.error(f"Error parsing ICY metadata: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in ICY parser: {e}")
        
        return None
    
    def _decode_metadata(self, metadata: bytes) -> str:
        """Decode the given metadata byte sequence into a string.
        
        Args:
            metadata: The byte sequence representing the metadata
            
        Returns:
            The decoded metadata as a string
        """
        # Try multiple encoding methods
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                return metadata.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, use latin-1 with error handling
        self.logger.warning("Failed to decode metadata with common encodings, using fallback")
        return metadata.decode('latin-1', errors='ignore')
    
    def _parse_track_from_metadata(self, metadata: str) -> Optional[Track]:
        """Parse track information from ICY metadata string.
        
        Args:
            metadata: The metadata string to parse
            
        Returns:
            Track object if parsing successful, None otherwise
        """
        # Look for StreamTitle in the metadata
        track_match = re.search(r'StreamTitle=(?P<track>[^;]+)', metadata)
        
        if not track_match:
            return None
        
        track_info = track_match.group('track').strip().strip("'\"")
        
        if not track_info or track_info.lower() in ['', 'unknown', 'n/a']:
            return None
        
        # Try to split artist and title
        # Common separators: " - ", " – ", " — ", " | "
        separators = [' - ', ' – ', ' — ', ' | ', ' / ']
        
        for separator in separators:
            if separator in track_info:
                parts = track_info.split(separator, 1)
                if len(parts) == 2:
                    artist, title = parts
                    return Track(artist=artist.strip(), title=title.strip())
        
        # If no separator found, treat the whole string as the title with unknown artist
        self.logger.warning(f"Could not parse artist/title from: {track_info}")
        return Track(artist="Unknown Artist", title=track_info)
    
    @classmethod
    def can_handle(cls, stream_url: str) -> bool:
        """Check if this parser can handle the given stream URL.
        
        ICY parser can handle most HTTP/HTTPS streams, but we'll check for
        explicit ICY support or common stream patterns.
        
        Args:
            stream_url: The URL to check
            
        Returns:
            True if this parser can likely handle the stream
        """
        if not stream_url.startswith(('http://', 'https://')):
            return False
        
        # Check if we can get ICY metadata
        try:
            response = requests.head(
                stream_url,
                headers={'Icy-MetaData': '1'},
                timeout=5
            )
            # If the response includes icy-metaint, we can handle it
            return 'icy-metaint' in response.headers
        except requests.RequestException:
            # If we can't check, assume we can handle it as a fallback
            # since ICY is the most common format
            return True
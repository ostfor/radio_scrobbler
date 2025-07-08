"""RSS/XML stream parser for radio stations that provide track info via RSS feeds."""

import xml.etree.ElementTree as ET
from typing import Optional
import requests

from .base import StreamParser, Track


class RssStreamParser(StreamParser):
    """Parser for radio stations that provide current track info via RSS/XML feeds.
    
    This parser handles radio stations that expose their current playing track
    information through RSS feeds or XML endpoints.
    
    Configuration options:
    - rss_url: The RSS/XML feed URL
    - item_selector: XPath-like selector for track items (default: first item)
    - artist_tag: XML tag name for artist (e.g., "artist", "dc:creator")
    - title_tag: XML tag name for title (e.g., "title")
    - description_separator: Separator in description field (e.g., " - ")
    """
    
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track from an RSS/XML feed.
        
        Returns:
            Track object if track metadata is found, None otherwise
        """
        rss_url = self.config.get('rss_url')
        if not rss_url:
            self.logger.error("RSS parser requires 'rss_url' in configuration")
            return None
        
        try:
            response = requests.get(
                rss_url,
                timeout=self.config.get('timeout', 10)
            )
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            track = self._extract_track_from_xml(root)
            
            if track:
                return self.clean_track_info(track)
                
        except requests.RequestException as e:
            self.logger.error(f"Error fetching RSS feed {rss_url}: {e}")
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in RSS parser: {e}")
        
        return None
    
    def _extract_track_from_xml(self, root: ET.Element) -> Optional[Track]:
        """Extract track information from XML/RSS data.
        
        Args:
            root: The XML root element
            
        Returns:
            Track object if parsing successful, None otherwise
        """
        # Find the first item (most recent track)
        item = root.find('.//item')
        if item is None:
            # Try alternative structures
            item = root.find('.//entry')  # Atom feed
            if item is None:
                self.logger.warning("No items found in RSS feed")
                return None
        
        artist = None
        title = None
        
        # Try to get artist and title from specific tags
        artist_tag = self.config.get('artist_tag', 'artist')
        title_tag = self.config.get('title_tag', 'title')
        
        artist_elem = item.find(artist_tag)
        title_elem = item.find(title_tag)
        
        if artist_elem is not None:
            artist = artist_elem.text
        if title_elem is not None:
            title = title_elem.text
        
        # If we have both, we're done
        if artist and title:
            return Track(artist=artist.strip(), title=title.strip())
        
        # Try to parse from description or title field
        description_elem = item.find('description')
        if description_elem is not None and description_elem.text:
            track = self._parse_from_description(description_elem.text)
            if track:
                return track
        
        # Try to parse from title field if no separate artist tag
        if title_elem is not None and not artist and title_elem.text:
            track = self._parse_from_title(title_elem.text)
            if track:
                return track
        
        self.logger.warning("Could not extract track information from RSS item")
        return None
    
    def _parse_from_description(self, description: str) -> Optional[Track]:
        """Try to parse artist and title from description text.
        
        Args:
            description: The description text
            
        Returns:
            Track object if parsing successful, None otherwise
        """
        if not description:
            return None
        
        description = description.strip()
        separator = self.config.get('description_separator', ' - ')
        
        if separator in description:
            parts = description.split(separator, 1)
            if len(parts) == 2:
                artist, title = parts
                return Track(artist=artist.strip(), title=title.strip())
        
        return None
    
    def _parse_from_title(self, title_text: str) -> Optional[Track]:
        """Try to parse artist and title from title text.
        
        Args:
            title_text: The title text
            
        Returns:
            Track object if parsing successful, None otherwise
        """
        if not title_text:
            return None
        
        title_text = title_text.strip()
        
        # Try common separators
        separators = [' - ', ' – ', ' — ', ' | ', ' / ', ': ']
        
        for separator in separators:
            if separator in title_text:
                parts = title_text.split(separator, 1)
                if len(parts) == 2:
                    artist, title = parts
                    return Track(artist=artist.strip(), title=title.strip())
        
        # If no separator found, treat as title with unknown artist
        return Track(artist="Unknown Artist", title=title_text)
    
    @classmethod
    def can_handle(cls, stream_url: str) -> bool:
        """Check if this parser can handle the given stream URL.
        
        RSS parser requires explicit configuration like JSON API parser,
        so it doesn't auto-detect streams.
        
        Args:
            stream_url: The URL to check
            
        Returns:
            False - requires explicit configuration
        """
        # RSS parser requires explicit configuration
        return False
    
    @classmethod
    def get_parser_name(cls) -> str:
        """Get the name of this parser."""
        return "RSS Parser"
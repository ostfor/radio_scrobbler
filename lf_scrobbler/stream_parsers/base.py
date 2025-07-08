"""Base stream parser interface using Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Optional, NamedTuple, Dict, Any
import logging


class Track(NamedTuple):
    """Track description"""
    artist: str
    title: str

    def __str__(self) -> str:
        return f"Artist: {self.artist}, Title: {self.title}"


class StreamParser(ABC):
    """Abstract base class for radio stream parsers.
    
    This implements the Strategy pattern, allowing different parsing strategies
    for different radio stream formats (ICY, SHOUTcast, JSON APIs, etc.).
    """
    
    def __init__(self, stream_url: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the stream parser.
        
        Args:
            stream_url: The URL of the radio stream
            config: Optional configuration parameters specific to this parser
        """
        self.stream_url = stream_url
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track from the radio stream.
        
        Returns:
            Track object if track metadata is found, None otherwise
        """
        pass
    
    @classmethod
    @abstractmethod
    def can_handle(cls, stream_url: str) -> bool:
        """Check if this parser can handle the given stream URL.
        
        Args:
            stream_url: The URL to check
            
        Returns:
            True if this parser can handle the stream, False otherwise
        """
        pass
    
    @classmethod
    def get_parser_name(cls) -> str:
        """Get the name of this parser.
        
        Returns:
            Human-readable name of the parser
        """
        return cls.__name__
    
    def clean_track_info(self, track: Track) -> Track:
        """Clean and normalize track information.
        
        Args:
            track: The track to clean
            
        Returns:
            Cleaned track with normalized metadata
        """
        import re
        return Track(
            artist=track.artist.strip(),
            title=re.sub(r'\[.*?\]', '', track.title).strip()
        )
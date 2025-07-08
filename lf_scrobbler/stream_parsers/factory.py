"""Factory for creating stream parsers based on stream format and configuration."""

from typing import List, Type, Optional, Dict, Any
import logging

from .base import StreamParser
from .icy_parser import IcyStreamParser
from .json_api_parser import JsonApiStreamParser
from .rss_parser import RssStreamParser


class StreamParserFactory:
    """Factory class for creating appropriate stream parsers.
    
    This implements the Factory pattern to automatically select and instantiate
    the correct parser based on stream URL and configuration.
    """
    
    # Registry of available parsers
    _parsers: List[Type[StreamParser]] = [
        IcyStreamParser,
        JsonApiStreamParser,
        RssStreamParser,
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def register_parser(cls, parser_class: Type[StreamParser]) -> None:
        """Register a new stream parser.
        
        This allows for dynamic registration of new parsers, making the
        system extensible for new stream formats.
        
        Args:
            parser_class: The parser class to register
        """
        if not issubclass(parser_class, StreamParser):
            raise ValueError(f"Parser must be a subclass of StreamParser")
        
        if parser_class not in cls._parsers:
            cls._parsers.append(parser_class)
    
    @classmethod
    def unregister_parser(cls, parser_class: Type[StreamParser]) -> None:
        """Unregister a stream parser.
        
        Args:
            parser_class: The parser class to unregister
        """
        if parser_class in cls._parsers:
            cls._parsers.remove(parser_class)
    
    @classmethod
    def get_available_parsers(cls) -> List[str]:
        """Get list of available parser names.
        
        Returns:
            List of parser names
        """
        return [parser.get_parser_name() for parser in cls._parsers]
    
    def create_parser(
        self, 
        stream_url: str, 
        parser_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[StreamParser]:
        """Create an appropriate stream parser for the given stream.
        
        Args:
            stream_url: The URL of the radio stream
            parser_type: Optional explicit parser type to use
            config: Optional configuration for the parser
            
        Returns:
            Configured StreamParser instance or None if no suitable parser found
        """
        config = config or {}
        
        # If parser type is explicitly specified, try to use it
        if parser_type:
            parser = self._create_explicit_parser(stream_url, parser_type, config)
            if parser:
                return parser
            self.logger.warning(f"Could not create specified parser '{parser_type}', falling back to auto-detection")
        
        # Auto-detect the best parser
        return self._auto_detect_parser(stream_url, config)
    
    def _create_explicit_parser(
        self, 
        stream_url: str, 
        parser_type: str, 
        config: Dict[str, Any]
    ) -> Optional[StreamParser]:
        """Create a parser of the specified type.
        
        Args:
            stream_url: The stream URL
            parser_type: The parser type name
            config: Parser configuration
            
        Returns:
            Parser instance or None if not found
        """
        for parser_class in self._parsers:
            if parser_class.get_parser_name().lower() == parser_type.lower():
                try:
                    return parser_class(stream_url, config)
                except Exception as e:
                    self.logger.error(f"Error creating parser '{parser_type}': {e}")
                    return None
        
        self.logger.error(f"Unknown parser type: {parser_type}")
        return None
    
    def _auto_detect_parser(
        self, 
        stream_url: str, 
        config: Dict[str, Any]
    ) -> Optional[StreamParser]:
        """Auto-detect the best parser for the stream.
        
        Args:
            stream_url: The stream URL
            config: Parser configuration
            
        Returns:
            Best matching parser or None if none found
        """
        suitable_parsers = []
        
        # Check which parsers can handle this stream
        for parser_class in self._parsers:
            try:
                if parser_class.can_handle(stream_url):
                    suitable_parsers.append(parser_class)
            except Exception as e:
                self.logger.warning(f"Error checking parser {parser_class.get_parser_name()}: {e}")
        
        if not suitable_parsers:
            self.logger.error(f"No suitable parser found for stream: {stream_url}")
            return None
        
        # For now, use the first suitable parser
        # In the future, we could implement priority-based selection
        parser_class = suitable_parsers[0]
        
        try:
            parser = parser_class(stream_url, config)
            self.logger.info(f"Using parser: {parser_class.get_parser_name()} for stream: {stream_url}")
            return parser
        except Exception as e:
            self.logger.error(f"Error creating parser {parser_class.get_parser_name()}: {e}")
            return None
    
    def test_parser(self, stream_url: str, parser_type: Optional[str] = None) -> bool:
        """Test if a parser can successfully parse the given stream.
        
        Args:
            stream_url: The stream URL to test
            parser_type: Optional specific parser type to test
            
        Returns:
            True if parsing is successful, False otherwise
        """
        try:
            parser = self.create_parser(stream_url, parser_type)
            if not parser:
                return False
            
            track = parser.get_current_track()
            return track is not None
        except Exception as e:
            self.logger.error(f"Error testing parser: {e}")
            return False
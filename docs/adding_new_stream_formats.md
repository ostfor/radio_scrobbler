# Adding New Radio Stream Formats

The Radio Scrobbler now supports a plugin-based architecture for handling different radio stream formats. This guide explains how to add support for new stream formats using the Strategy pattern.

## Architecture Overview

The system uses several design patterns to provide a clean, extensible architecture:

- **Strategy Pattern**: Different stream parsers implement the same interface but use different algorithms for parsing track metadata
- **Factory Pattern**: Automatically selects and instantiates the appropriate parser based on stream configuration
- **Plugin Architecture**: New parsers can be easily added without modifying existing code

## Creating a New Stream Parser

### 1. Implement the StreamParser Interface

All stream parsers must inherit from the `StreamParser` abstract base class:

```python
from typing import Optional
from lf_scrobbler.stream_parsers.base import StreamParser, Track

class MyCustomParser(StreamParser):
    """Parser for my custom radio stream format."""
    
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track from the stream.
        
        Returns:
            Track object if track metadata is found, None otherwise
        """
        # Your implementation here
        pass
    
    @classmethod
    def can_handle(cls, stream_url: str) -> bool:
        """Check if this parser can handle the given stream URL.
        
        Args:
            stream_url: The URL to check
            
        Returns:
            True if this parser can handle the stream, False otherwise
        """
        # Your logic to determine if this parser can handle the stream
        pass
    
    @classmethod
    def get_parser_name(cls) -> str:
        """Get the name of this parser."""
        return "My Custom Parser"
```

### 2. Key Methods to Implement

#### `get_current_track()` 
This is the main method that extracts track information from your stream format. It should:
- Handle network requests and parsing errors gracefully
- Return a `Track` object with artist and title
- Use `self.clean_track_info()` to normalize the track data
- Log appropriate warnings/errors

#### `can_handle()`
This class method determines if your parser can handle a given stream URL. It should:
- Return `True` if the parser can handle the stream
- Return `False` if explicit configuration is required
- Perform lightweight checks (avoid heavy network operations)

### 3. Configuration Options

Your parser can accept configuration through the `self.config` dictionary. Common options include:
- `timeout`: Request timeout in seconds
- Custom endpoint URLs
- Authentication headers
- Field mappings for data extraction

## Example Implementations

### Simple HTTP API Parser

```python
import requests
from typing import Optional
from lf_scrobbler.stream_parsers.base import StreamParser, Track

class HttpApiParser(StreamParser):
    """Parser for simple HTTP API endpoints."""
    
    def get_current_track(self) -> Optional[Track]:
        api_url = self.config.get('api_url')
        if not api_url:
            self.logger.error("HTTP API parser requires 'api_url' in configuration")
            return None
        
        try:
            response = requests.get(api_url, timeout=self.config.get('timeout', 10))
            response.raise_for_status()
            
            data = response.text.strip()
            if ' - ' in data:
                artist, title = data.split(' - ', 1)
                track = Track(artist=artist.strip(), title=title.strip())
                return self.clean_track_info(track)
                
        except requests.RequestException as e:
            self.logger.error(f"Error fetching API data: {e}")
        
        return None
    
    @classmethod
    def can_handle(cls, stream_url: str) -> bool:
        # Requires explicit configuration
        return False
```

### WebSocket Parser

```python
import json
import websocket
from typing import Optional
from lf_scrobbler.stream_parsers.base import StreamParser, Track

class WebSocketParser(StreamParser):
    """Parser for WebSocket-based track updates."""
    
    def __init__(self, stream_url: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(stream_url, config)
        self._current_track = None
        self._ws = None
        
    def get_current_track(self) -> Optional[Track]:
        if not self._ws:
            self._connect()
        
        return self._current_track
    
    def _connect(self):
        ws_url = self.config.get('websocket_url')
        if ws_url:
            self._ws = websocket.WebSocket()
            try:
                self._ws.connect(ws_url)
                # Set up message handler
                # Implementation details...
            except Exception as e:
                self.logger.error(f"WebSocket connection failed: {e}")
    
    @classmethod
    def can_handle(cls, stream_url: str) -> bool:
        return False  # Requires explicit configuration
```

## Registering Your Parser

### Method 1: Add to Factory Registry

Add your parser to the factory's parser registry:

```python
# In lf_scrobbler/stream_parsers/factory.py
from .my_custom_parser import MyCustomParser

class StreamParserFactory:
    _parsers: List[Type[StreamParser]] = [
        IcyStreamParser,
        JsonApiStreamParser,
        RssStreamParser,
        MyCustomParser,  # Add your parser here
    ]
```

### Method 2: Dynamic Registration

Register your parser at runtime:

```python
from lf_scrobbler.stream_parsers import StreamParserFactory
from my_module import MyCustomParser

# Register the parser
StreamParserFactory.register_parser(MyCustomParser)
```

## Configuration Examples

### Basic Configuration

```yaml
radios:
  - name: "My Radio Station"
    stream_url: "http://myradio.example.com:8000"
    parser_type: "My Custom Parser"
    parser_config:
      api_url: "http://myradio.example.com/api/nowplaying"
      timeout: 15
```

### Advanced Configuration

```yaml
radios:
  - name: "Complex Radio"
    stream_url: "http://complex-radio.example.com:8000"
    parser_type: "My Custom Parser"
    parser_config:
      api_url: "http://complex-radio.example.com/api/v2/current"
      headers:
        Authorization: "Bearer your-api-token"
        User-Agent: "RadioScrobbler/1.0"
      artist_field: "track.metadata.artist"
      title_field: "track.metadata.title"
      timeout: 20
      retry_count: 3
```

## Best Practices

### Error Handling
- Always use try-catch blocks for network operations
- Log errors with appropriate detail levels
- Return `None` when track information cannot be extracted
- Don't let exceptions propagate up to the main scrobbling loop

### Performance
- Keep `can_handle()` method lightweight
- Use appropriate timeouts for network requests
- Consider caching when appropriate
- Avoid blocking operations in the main thread

### Configuration
- Validate required configuration parameters
- Provide sensible default values
- Document all configuration options
- Use type hints for configuration fields

### Testing
```python
def test_my_parser():
    parser = MyCustomParser("http://example.com", {"api_url": "http://api.example.com"})
    track = parser.get_current_track()
    assert track is not None
    assert track.artist != ""
    assert track.title != ""
```

## Debugging Your Parser

### Enable Debug Logging
```python
import logging
logging.getLogger('MyCustomParser').setLevel(logging.DEBUG)
```

### Test Parser Independently
```python
from lf_scrobbler.stream_parsers import StreamParserFactory

factory = StreamParserFactory()
success = factory.test_parser("http://myradio.example.com", "My Custom Parser")
print(f"Parser test: {'PASSED' if success else 'FAILED'}")
```

### Check Available Parsers
```python
from lf_scrobbler.stream_parsers import StreamParserFactory

parsers = StreamParserFactory.get_available_parsers()
print("Available parsers:", parsers)
```

## Common Stream Formats

Here are some common radio stream formats you might want to support:

- **ICY Metadata** (SHOUTcast/Icecast) - Already implemented
- **JSON REST APIs** - Already implemented  
- **RSS/XML feeds** - Already implemented
- **WebSocket streams** - Example above
- **M3U8 playlists** - Could extract from playlist metadata
- **RTMP streams** - Would need RTMP client library
- **GraphQL APIs** - Similar to REST but with GraphQL queries
- **Custom radio station APIs** - Station-specific implementations

## Contributing

When contributing a new parser:

1. Follow the established patterns and interfaces
2. Include comprehensive error handling
3. Add configuration documentation
4. Provide usage examples
5. Write unit tests
6. Update this documentation

## Future Enhancements

Potential improvements to the parser system:

- **Priority-based parser selection**: Allow multiple parsers to claim a stream and select the best one
- **Fallback chains**: Try multiple parsers in sequence if the first one fails
- **Parser health monitoring**: Track parser success rates and automatically disable failing parsers
- **Dynamic parser loading**: Load parsers from external modules or configuration
- **Parser marketplace**: Share parsers between users
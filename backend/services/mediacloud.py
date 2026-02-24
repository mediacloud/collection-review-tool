"""MediaCloud API client service wrapper."""
import os
import mediacloud.api
from config import get_config


class MediaCloudService:
    """Service for interacting with MediaCloud API."""
    
    def __init__(self, api_key=None):
        """Initialize MediaCloud client."""
        config = get_config()
        self.api_key = api_key or config.MEDIACLOUD_API_KEY
        
        if not self.api_key:
            raise ValueError("MEDIACLOUD_API_KEY is required")
        
        # Use DirectoryApi for fetching sources and collections
        self.directory = mediacloud.api.DirectoryApi(self.api_key)
        self.search = mediacloud.api.SearchApi(self.api_key)
    
    def fetch_collection_details(self, collection_id):
        """
        Fetch collection details from MediaCloud API.
        
        Args:
            collection_id: MediaCloud collection ID (integer)
            
        Returns:
            Dictionary with collection details including name
            
        Note: If the API method is not available, returns a default name.
        """
        try:
            # Try to fetch collection details using available API methods
            # Check if collection_list method exists
            if hasattr(self.directory, 'collection_list'):
                try:
                    response = self.directory.collection_list(collection_id=collection_id)
                    collections = response.get('results', [])
                    if collections and len(collections) > 0:
                        collection = collections[0]
                        return {
                            'id': collection_id,
                            'name': collection.get('name') or collection.get('label') or f'Collection {collection_id}',
                            'description': collection.get('description', ''),
                            'tags_id': collection.get('tags_id', collection_id)
                        }
                except (AttributeError, TypeError):
                    pass
            
            # Fallback: try tag_list if available (collections are tags in MediaCloud)
            if hasattr(self.directory, 'tag_list'):
                try:
                    response = self.directory.tag_list(tags_id=collection_id)
                    tags = response.get('results', [])
                    if tags and len(tags) > 0:
                        tag = tags[0]
                        return {
                            'id': collection_id,
                            'name': tag.get('label') or tag.get('name') or f'Collection {collection_id}',
                            'description': tag.get('description', ''),
                            'tags_id': collection_id
                        }
                except (AttributeError, TypeError):
                    pass
        except Exception:
            # If all methods fail, continue to fallback
            pass
        
        # Fallback: return default name
        return {
            'id': collection_id,
            'name': f'Collection {collection_id}',
            'description': '',
            'tags_id': collection_id
        }
    
    def fetch_collection_sources(self, collection_id):
        """
        Fetch all sources for a given collection.
        
        Uses MediaCloud API v4 client's DirectoryApi.source_list() method.
        See: https://github.com/mediacloud/api-client/blob/main/mediacloud/api.py
        
        Args:
            collection_id: MediaCloud collection ID (integer)
            
        Returns:
            List of source dictionaries, each with:
                - id: MediaCloud source ID
                - label: Source name/label
                - homepage: Source homepage URL
            
        Raises:
            ValueError: If MEDIACLOUD_API_KEY is not set
            Exception: If API call fails (invalid collection, auth, network)
        """
        try:
            source_list = []
            offset = 0
            limit = 100  # Fetch in batches
            
            # Use source_list() method from DirectoryApi with collection_id filter
            # The method supports pagination via limit and offset
            while True:
                response = self.directory.source_list(
                    collection_id=collection_id,
                    limit=limit,
                    offset=offset
                )
                
                # Response is a dict, typically with 'results' key
                sources = response.get('results', [])
                
                if not sources:
                    break
                
                # Extract source information - store all available fields
                for source in sources:
                    source_id = source.get('media_id') or source.get('id') or source.get('source_id')
                    # Only add if we have at least an ID
                    if source_id:
                        # Store the full source data for later use in exports
                        source_dict = dict(source)  # Copy all fields
                        source_dict['id'] = source_id
                        # Ensure we have label and homepage for backward compatibility
                        if 'label' not in source_dict:
                            source_dict['label'] = source.get('name') or source.get('label') or ''
                        if 'homepage' not in source_dict:
                            source_dict['homepage'] = source.get('url') or source.get('homepage') or source.get('media_url') or ''
                        source_list.append(source_dict)
                
                # Check if there are more results to fetch
                if len(sources) < limit:
                    break
                
                offset += limit
            
            if not source_list:
                raise ValueError(f"No sources found for collection {collection_id}. "
                               f"Please verify the collection ID and API key permissions.")
            
            return source_list
            
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            # Re-raise with more context
            error_msg = f"Failed to fetch sources for collection {collection_id}: {str(e)}"
            raise Exception(error_msg) from e
    
    def fetch_source_by_id(self, source_id):
        """
        Fetch a single source by ID from MediaCloud API.
        
        Args:
            source_id: MediaCloud source ID (integer)
            
        Returns:
            Source dictionary with all available fields
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Use source_list with source_id filter or get source directly
            # The API might support filtering by source_id
            response = self.directory.source_list(
                source_id=source_id,
                limit=1
            )
            
            sources = response.get('results', [])
            if sources and len(sources) > 0:
                source = sources[0]
                source_dict = dict(source)  # Copy all fields
                source_id_val = source.get('media_id') or source.get('id') or source.get('source_id')
                source_dict['id'] = source_id_val
                return source_dict
            else:
                raise ValueError(f"Source {source_id} not found")
                
        except Exception as e:
            error_msg = f"Failed to fetch source {source_id}: {str(e)}"
            raise Exception(error_msg) from e


# Singleton instance
_mediacloud_service = None


def get_mediacloud_service():
    """Get or create MediaCloud service instance."""
    global _mediacloud_service
    if _mediacloud_service is None:
        _mediacloud_service = MediaCloudService()
    return _mediacloud_service

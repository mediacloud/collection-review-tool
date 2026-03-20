"""Service for loading and rendering annotation guidelines."""
from pathlib import Path
import json


class GuidelinesService:
    """Service for loading and rendering annotation guidelines."""
    
    def __init__(self):
        """Initialize guidelines service."""
        # Get the backend directory
        backend_dir = Path(__file__).parent.parent
        self.templates_dir = backend_dir / 'templates' / 'guidelines'
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def get_available_templates(self):
        """Get list of available guideline templates."""
        templates = []
        if self.templates_dir.exists():
            for file in self.templates_dir.glob('*.md'):
                templates.append(file.stem)
        # Ensure default exists
        if 'default' not in templates:
            templates.append('default')
        return sorted(templates)
    
    def render_guidelines(self, template_name, review, context_overrides=None):
        """
        Render guidelines template with review context.
        
        Args:
            template_name: Name of the template (without .md extension)
            review: Review object for interpolation
            context_overrides: optional dict to override/intersect template variables
            
        Returns:
            Rendered guidelines text (markdown)
        """
        # Default to 'default' if template not found
        if not template_name:
            template_name = 'default'
        
        template_path = self.templates_dir / f'{template_name}.md'
        
        # If template doesn't exist, use default
        if not template_path.exists():
            template_path = self.templates_dir / 'default.md'
        
        # Create default template if it doesn't exist
        if not template_path.exists():
            self._create_default_template()
            template_path = self.templates_dir / 'default.md'
        
        # Read template
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except Exception:
            return "Guidelines template not available."
        
        context_overrides = context_overrides or {}

        # Interpolate variables.
        # The "review" argument might be a queue Review or (for project-level rendering)
        # a ReviewProject; support both by using getattr fallbacks.
        collection_name_default = (
            getattr(review, 'collection_name', None)
            or f'Collection {getattr(review, "collection_id", "")}'.strip()
        )

        # If this is a ReviewProject, collection_ids_json is a JSON string.
        collection_id_default = getattr(review, 'collection_id', None)
        if collection_id_default is None and hasattr(review, 'collection_ids_json'):
            try:
                ids = json.loads(review.collection_ids_json or '[]')
                collection_id_default = ids[0] if ids else None
            except Exception:
                collection_id_default = None

        context = {
            'collection_name': collection_name_default,
            'collection_id': collection_id_default,
            'review_id': getattr(review, 'id', None),
            'review_name': getattr(review, 'name', None) or collection_name_default,
        }

        # Apply overrides last so callers can force stable values across queues.
        context.update(context_overrides)
        
        # Simple string substitution (can be enhanced with Jinja2 later)
        try:
            rendered = template_content.format(**context)
        except KeyError:
            # If there's a formatting error, return template as-is
            rendered = template_content
        
        return rendered
    
    def _create_default_template(self):
        """Create default template if it doesn't exist."""
        default_content = """# Review Guidelines: {collection_name}

Please review each source and decide whether to **Keep** or **Remove** it from the collection.

- **Keep**: The source is appropriate for this collection
- **Remove**: The source should be removed (please provide a reason)

Use your best judgment based on the collection's purpose and the source's relevance.
"""
        default_path = self.templates_dir / 'default.md'
        with open(default_path, 'w', encoding='utf-8') as f:
            f.write(default_content)


# Singleton instance
_guidelines_service = None


def get_guidelines_service():
    """Get or create guidelines service instance."""
    global _guidelines_service
    if _guidelines_service is None:
        _guidelines_service = GuidelinesService()
    return _guidelines_service

"""SQLAlchemy models for the review application."""
from datetime import datetime
from database import db
import enum
import json


class ReviewStatus(enum.Enum):
    """Review status enumeration."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'


class Decision(enum.Enum):
    """Decision enumeration for review items."""
    UNDECIDED = 'undecided'
    KEEP = 'keep'
    REMOVE = 'remove'
    ADD = 'add'
    SKIP = 'skip'


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Review(db.Model, TimestampMixin):
    """Review model representing a review session for a MediaCloud collection."""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, nullable=False, index=True)
    collection_name = db.Column(db.String(500), nullable=True)  # Name of the MediaCloud collection
    status = db.Column(db.Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    guidelines_template = db.Column(db.String(100), nullable=True, default='default')  # Template name for annotation guidelines
    # When true, UI should allow editing of per-source language and geography metadata
    edit_metadata = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationship to review items
    items = db.relationship('ReviewItem', backref='review', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_stats=False):
        """Convert review to dictionary."""
        data = {
            'id': self.id,
            'collection_id': self.collection_id,
            'collection_name': self.collection_name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'name': self.name,
            'notes': self.notes,
            'guidelines_template': self.guidelines_template or 'default',
            'edit_metadata': bool(self.edit_metadata)
        }
        
        if include_stats:
            data['stats'] = self.calculate_stats()
        
        return data
    
    def calculate_stats(self):
        """Calculate statistics for this review."""
        total = len(self.items)
        keep = sum(1 for item in self.items if item.decision == Decision.KEEP)
        remove = sum(1 for item in self.items if item.decision == Decision.REMOVE)
        add = sum(1 for item in self.items if item.decision == Decision.ADD)
        undecided = sum(1 for item in self.items if item.decision == Decision.UNDECIDED)
        skip = sum(1 for item in self.items if item.decision == Decision.SKIP)
        
        return {
            'total': total,
            'keep': keep,
            'remove': remove,
            'add': add,
            'undecided': undecided,
            'skip': skip
        }


class ReviewItem(db.Model, TimestampMixin):
    """Review item model representing a source in a review."""
    __tablename__ = 'review_items'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False, index=True)
    source_id = db.Column(db.Integer, nullable=True)  # MediaCloud source ID (null for new sources)
    source_label = db.Column(db.String(500), nullable=True)
    source_homepage = db.Column(db.String(1000), nullable=True)
    is_new_source = db.Column(db.Boolean, default=False, nullable=False)
    decision = db.Column(db.Enum(Decision), default=Decision.UNDECIDED, nullable=False)
    decided_at = db.Column(db.DateTime, nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)  # Reason for removal (required when decision is REMOVE)
    # Optional JSON-encoded metadata about the source as returned by MediaCloud.
    # This can include fields like stories_per_week, last_story, media_type, etc.
    source_metadata = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert review item to dictionary."""
        metadata = None
        if self.source_metadata:
            try:
                metadata = json.loads(self.source_metadata)
            except Exception:
                metadata = None

        return {
            'id': self.id,
            'review_id': self.review_id,
            'source_id': self.source_id,
            'source_label': self.source_label,
            'source_homepage': self.source_homepage,
            'is_new_source': self.is_new_source,
            'decision': self.decision.value,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
            'removal_reason': self.removal_reason,
            'source_metadata': metadata
        }

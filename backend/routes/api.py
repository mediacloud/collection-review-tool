"""API routes for the review application."""
from flask import Blueprint, request, jsonify, Response
from database import db
from models import Review, ReviewItem, ReviewStatus, Decision
from services.mediacloud import get_mediacloud_service
from services.guidelines import get_guidelines_service
from datetime import datetime
from urllib.parse import urlparse
import csv
import io
import os
import json

api_bp = Blueprint('api', __name__)


@api_bp.route('/guidelines/templates', methods=['GET'])
def get_guideline_templates():
    """Get list of available guideline templates."""
    try:
        service = get_guidelines_service()
        templates = service.get_available_templates()
        return jsonify({'templates': templates}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch templates: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/guidelines', methods=['GET'])
def get_review_guidelines(review_id):
    """Get rendered guidelines for a review."""
    try:
        review = Review.query.get_or_404(review_id)
        service = get_guidelines_service()
        template_name = review.guidelines_template or 'default'
        guidelines = service.render_guidelines(template_name, review)
        return jsonify({'guidelines': guidelines}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch guidelines: {str(e)}'}), 500


@api_bp.route('/reviews/start', methods=['POST'])
def start_review():
    """
    Start or resume a review for a MediaCloud collection.
    
    POST /api/reviews/start
    Body: { "collection_id": 123 }
    
    Returns: Review JSON with stats
    """
    try:
        data = request.get_json()
        if not data or 'collection_id' not in data:
            return jsonify({'error': 'collection_id is required'}), 400
        
        collection_id = data['collection_id']
        guidelines_template = data.get('guidelines_template', 'default')
        
        # Check for existing active review (status != 'completed')
        existing_review = Review.query.filter_by(
            collection_id=collection_id
        ).filter(
            Review.status != ReviewStatus.COMPLETED
        ).first()
        
        if existing_review:
            # If collection_name or name is not set, try to fetch them from MediaCloud
            if not existing_review.collection_name or not existing_review.name:
                try:
                    mediacloud = get_mediacloud_service()
                    collection_details = mediacloud.fetch_collection_details(collection_id)
                    collection_name = collection_details.get('name', f'Collection {collection_id}')
                    if not existing_review.collection_name:
                        existing_review.collection_name = collection_name
                    if not existing_review.name:
                        existing_review.name = collection_name
                    db.session.commit()
                except Exception:
                    # If fetching fails, ensure we at least have sensible defaults
                    existing_review.collection_name = existing_review.collection_name or f'Collection {collection_id}'
                    existing_review.name = existing_review.name or existing_review.collection_name
            
            # Return existing review with stats
            return jsonify({
                'review': existing_review.to_dict(include_stats=True)
            }), 200
        
        # Fetch collection details and sources from MediaCloud
        mediacloud = get_mediacloud_service()
        
        # Fetch collection name
        try:
            collection_details = mediacloud.fetch_collection_details(collection_id)
            collection_name = collection_details.get('name', f'Collection {collection_id}')
        except Exception as e:
            # If fetching collection name fails, use default
            collection_name = f'Collection {collection_id}'
        
        # Create new review, using the collection name as the human-friendly review name
        new_review = Review(
            collection_id=collection_id,
            collection_name=collection_name,
            name=collection_name,
            status=ReviewStatus.IN_PROGRESS,
            guidelines_template=guidelines_template
        )
        db.session.add(new_review)
        db.session.flush()  # Get the review ID
        
        # Fetch sources from MediaCloud
        try:
            sources = mediacloud.fetch_collection_sources(collection_id)
        except Exception as e:
            # Rollback review creation
            db.session.rollback()
            return jsonify({
                'error': f'Failed to fetch sources from MediaCloud: {str(e)}'
            }), 502
        
        # Create ReviewItems from sources, capturing full source metadata for later use
        for source in sources:
            review_item = ReviewItem(
                review_id=new_review.id,
                source_id=source['id'],
                source_label=source.get('label', ''),
                source_homepage=source.get('homepage', ''),
                is_new_source=False,
                decision=Decision.UNDECIDED,
                source_metadata=json.dumps(source)
            )
            db.session.add(review_item)
        
        # Commit all changes
        db.session.commit()
        
        # Return new review with stats
        return jsonify({
            'review': new_review.to_dict(include_stats=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@api_bp.route('/reviews/in-progress', methods=['GET'])
def get_in_progress_reviews():
    """
    Get all reviews that are in progress (not completed).
    
    GET /api/reviews/in-progress
    
    Returns: Array of review objects with completeness percentage
    """
    try:
        # Get all reviews that are not completed
        reviews = Review.query.filter(
            Review.status != ReviewStatus.COMPLETED
        ).order_by(Review.created_at.desc()).all()
        
        result = []
        for review in reviews:
            stats = review.calculate_stats()
            total = stats['total']
            
            # Calculate completeness: (decided items / total items) * 100
            # Decided items = total - undecided
            decided = total - stats['undecided']
            completeness = (decided / total * 100) if total > 0 else 0
            
            review_data = review.to_dict(include_stats=False)
            review_data['completeness'] = round(completeness, 1)
            review_data['stats'] = stats
            result.append(review_data)
        
        return jsonify({
            'reviews': result
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch in-progress reviews: {str(e)}'}), 500


@api_bp.route('/reviews/completed', methods=['GET'])
def get_completed_reviews():
    """
    Get all completed reviews.
    
    GET /api/reviews/completed
    
    Returns: Array of review objects with completeness percentage
    """
    try:
        # Get all completed reviews
        reviews = Review.query.filter(
            Review.status == ReviewStatus.COMPLETED
        ).order_by(Review.updated_at.desc()).all()
        
        result = []
        for review in reviews:
            stats = review.calculate_stats()
            total = stats['total']
            
            # Calculate completeness: (decided items / total items) * 100
            # Decided items = total - undecided
            decided = total - stats['undecided']
            completeness = (decided / total * 100) if total > 0 else 0
            
            review_data = review.to_dict(include_stats=False)
            review_data['completeness'] = round(completeness, 1)
            review_data['stats'] = stats
            result.append(review_data)
        
        return jsonify({
            'reviews': result
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch completed reviews: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """
    Get a review by ID with statistics.
    
    GET /api/reviews/<review_id>
    
    Returns: Review JSON with stats
    """
    try:
        review = Review.query.get_or_404(review_id)
        
        # If collection_name is not set, try to fetch it
        if not review.collection_name:
            try:
                mediacloud = get_mediacloud_service()
                collection_details = mediacloud.fetch_collection_details(review.collection_id)
                review.collection_name = collection_details.get('name', f'Collection {review.collection_id}')
                db.session.commit()
            except Exception:
                # If fetching fails, use default
                review.collection_name = review.collection_name or f'Collection {review.collection_id}'
        
        return jsonify({
            'review': review.to_dict(include_stats=True)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to fetch review: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/items', methods=['GET'])
def get_review_items(review_id):
    """
    Get review items with optional filtering and pagination.
    
    GET /api/reviews/<review_id>/items?page=1&page_size=20&decision=undecided
    
    Returns: Items array and total count
    """
    try:
        # Verify review exists
        review = Review.query.get_or_404(review_id)
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 100, type=int)
        decision_filter = request.args.get('decision', None)
        
        # Build query
        query = ReviewItem.query.filter_by(review_id=review_id)
        
        # Apply decision filter if provided
        if decision_filter:
            try:
                decision_enum = Decision(decision_filter)
                query = query.filter_by(decision=decision_enum)
            except ValueError:
                return jsonify({'error': f'Invalid decision value: {decision_filter}'}), 400
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        items = query.order_by(ReviewItem.id).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'items': [item.to_dict() for item in items],
            'total': total
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch items: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/items/<int:item_id>/decide', methods=['POST'])
def decide_item(review_id, item_id):
    """
    Make a decision on a review item.
    
    POST /api/reviews/<review_id>/items/<item_id>/decide
    Body: { "decision": "keep" }
    
    Returns: Updated item JSON
    """
    try:
        # Verify review exists
        review = Review.query.get_or_404(review_id)
        
        # Get item and verify it belongs to the review
        item = ReviewItem.query.filter_by(id=item_id, review_id=review_id).first_or_404()
        
        # Get decision from request
        data = request.get_json()
        if not data or 'decision' not in data:
            return jsonify({'error': 'decision is required'}), 400
        
        decision_str = data['decision']
        
        # Validate decision value
        try:
            decision_enum = Decision(decision_str)
        except ValueError:
            return jsonify({'error': f'Invalid decision: {decision_str}. Must be one of: keep, remove, add, undecided'}), 400
        
        # Validate decision based on item type
        if not item.is_new_source:
            # Existing sources can only be kept or removed
            if decision_enum not in [Decision.KEEP, Decision.REMOVE]:
                return jsonify({
                    'error': f'Existing sources can only be marked as "keep" or "remove", not "{decision_str}"'
                }), 400
        else:
            # New sources can be added (or removed/keep if desired)
            # The spec says new sources default to "add", but allows other decisions
            pass
        
        # Require removal_reason when decision is REMOVE
        if decision_enum == Decision.REMOVE:
            removal_reason = data.get('removal_reason', '').strip()
            if not removal_reason:
                return jsonify({
                    'error': 'removal_reason is required when decision is "remove"'
                }), 400
            item.removal_reason = removal_reason
        else:
            # Clear removal_reason if decision is not REMOVE
            item.removal_reason = None
        
        # Update item
        item.decision = decision_enum
        item.decided_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(item.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update item: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/items', methods=['POST'])
def create_review_item(review_id):
    """
    Propose a new source for a review.
    
    POST /api/reviews/<review_id>/items
    Body: {
        "source_label": "New Outlet",
        "source_homepage": "https://new-outlet.example"
    }
    
    Returns: Created item JSON
    """
    try:
        # Verify review exists
        review = Review.query.get_or_404(review_id)
        
        # Get data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        source_label = data.get('source_label')
        source_homepage = data.get('source_homepage')
        
        # Validate required fields
        if not source_label:
            return jsonify({'error': 'source_label is required'}), 400
        if not source_homepage:
            return jsonify({'error': 'source_homepage is required'}), 400
        
        # Create new review item
        new_item = ReviewItem(
            review_id=review_id,
            source_id=None,  # New sources don't have a MediaCloud source_id
            source_label=source_label,
            source_homepage=source_homepage,
            is_new_source=True,
            decision=Decision.ADD  # New sources default to "add"
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify(new_item.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create item: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/complete', methods=['POST'])
def complete_review(review_id):
    """
    Mark a review as completed.
    
    POST /api/reviews/<review_id>/complete
    
    Returns: Updated review JSON
    """
    try:
        review = Review.query.get_or_404(review_id)
        
        # Check for undecided items (warn but don't block)
        undecided_count = sum(1 for item in review.items if item.decision == Decision.UNDECIDED)
        
        if undecided_count > 0:
            # Return warning but still allow completion
            # In a production app, you might want to make this configurable
            pass
        
        # Update review status
        review.status = ReviewStatus.COMPLETED
        review.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'review': review.to_dict(include_stats=True),
            'warning': f'{undecided_count} undecided items remain' if undecided_count > 0 else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to complete review: {str(e)}'}), 500


def _generate_mediacloud_csv(items, collection_id, include_removal_reason=False):
    """
    Helper function to generate MediaCloud format CSV from review items.
    
    Args:
        items: List of ReviewItem objects to export
        collection_id: MediaCloud collection ID
        include_removal_reason: Whether to include removal_reason as an extra column
    
    Returns:
        CSV string content
    """
    # Read MediaCloud CSV columns from file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    columns_file = os.path.join(base_dir, '..', 'mc_csv_columns.txt')
    
    mc_columns = []
    try:
        with open(columns_file, 'r') as f:
            mc_columns = [line.strip().split('\t')[0].strip() for line in f if line.strip()]
    except FileNotFoundError:
        # Fallback to default columns if file not found
        mc_columns = [
            'id', 'homepage', 'domain', 'url_search_string', 'label', 'notes',
            'platform', 'pub_country', 'pub_state', 'media_type',
            'stories_per_week', 'last_story', 'primary_language'
        ]
    
    # Add removal_reason column if requested
    if include_removal_reason:
        mc_columns = mc_columns + ['removal_reason']
    
    # Get MediaCloud service for fetching full source data
    mediacloud = get_mediacloud_service()
    
    # Fetch all sources for the collection to get full data
    # This is more efficient than fetching one by one
    try:
        all_sources = mediacloud.fetch_collection_sources(collection_id)
        # Create a lookup dict by source ID
        sources_by_id = {str(s.get('id')): s for s in all_sources}
    except Exception as e:
        # If fetching fails, we'll handle it per item
        sources_by_id = {}
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header with MediaCloud columns
    writer.writerow(mc_columns)
    
    # Write data rows
    for item in items:
        if item.is_new_source:
            # New sources: only homepage and domain
            row = {}
            for col in mc_columns:
                if col == 'homepage':
                    row[col] = item.source_homepage or ''
                elif col == 'domain':
                    # Extract domain from homepage
                    domain = ''
                    if item.source_homepage:
                        try:
                            parsed = urlparse(item.source_homepage)
                            domain = parsed.netloc or ''
                        except:
                            domain = ''
                    row[col] = domain
                elif col == 'removal_reason':
                    row[col] = item.removal_reason or ''
                else:
                    row[col] = ''
            writer.writerow([row.get(col, '') for col in mc_columns])
        else:
            # Existing sources: fetch full data from MediaCloud
            source_data = sources_by_id.get(str(item.source_id), {})
            
            # Map MediaCloud API fields to CSV columns
            row = {}
            homepage = source_data.get('url') or source_data.get('homepage') or source_data.get('media_url') or item.source_homepage or ''
            
            for col in mc_columns:
                # Map common field names
                if col == 'id':
                    row[col] = item.source_id or ''
                elif col == 'homepage':
                    row[col] = homepage
                elif col == 'domain':
                    # Extract from homepage or use domain field
                    domain = source_data.get('domain', '')
                    if not domain and homepage:
                        try:
                            parsed = urlparse(homepage)
                            domain = parsed.netloc or ''
                        except:
                            pass
                    row[col] = domain
                elif col == 'label':
                    row[col] = source_data.get('name') or source_data.get('label') or item.source_label or ''
                elif col == 'removal_reason':
                    row[col] = item.removal_reason or ''
                else:
                    # Use the field name directly from source_data, or empty string
                    row[col] = source_data.get(col, '')
            
            writer.writerow([row.get(col, '') for col in mc_columns])
    
    output.seek(0)
    return output.getvalue()


@api_bp.route('/reviews/<int:review_id>/export', methods=['GET'])
def export_review(review_id):
    """
    Export review decisions as CSV in MediaCloud collection input format.
    Exports sources marked as 'keep' or 'add'.
    
    GET /api/reviews/<review_id>/export
    
    Returns: CSV file with review data in MediaCloud format
    """
    try:
        review = Review.query.get_or_404(review_id)
        
        # Get all items for this review - only export keep and add decisions
        items = ReviewItem.query.filter_by(review_id=review_id).filter(
            ReviewItem.decision.in_([Decision.KEEP, Decision.ADD])
        ).all()
        
        csv_content = _generate_mediacloud_csv(items, review.collection_id, include_removal_reason=False)
        
        # Create Flask response with CSV
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=review_{review_id}_export.csv'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export review: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/export/removed', methods=['GET'])
def export_removed_sources(review_id):
    """
    Export removed sources as CSV with all available metadata.
    
    GET /api/reviews/<review_id>/export/removed
    
    Returns: CSV file with removed sources in MediaCloud format, including removal_reason
    """
    try:
        review = Review.query.get_or_404(review_id)
        
        # Get all items marked as removed
        items = ReviewItem.query.filter_by(review_id=review_id).filter(
            ReviewItem.decision == Decision.REMOVE
        ).all()
        
        # Return empty CSV with headers if no items
        csv_content = _generate_mediacloud_csv(items, review.collection_id, include_removal_reason=True)
        
        # Create Flask response with CSV
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=review_{review_id}_removed_sources.csv'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export removed sources: {str(e)}'}), 500


@api_bp.route('/reviews/<int:review_id>/export/added', methods=['GET'])
def export_added_sources(review_id):
    """
    Export added sources (new sources) as CSV with all available metadata.
    
    GET /api/reviews/<review_id>/export/added
    
    Returns: CSV file with added sources in MediaCloud format
    """
    try:
        review = Review.query.get_or_404(review_id)
        
        # Get all items marked as add (these are new sources)
        items = ReviewItem.query.filter_by(review_id=review_id).filter(
            ReviewItem.decision == Decision.ADD
        ).all()
        
        # Return empty CSV with headers if no items
        csv_content = _generate_mediacloud_csv(items, review.collection_id, include_removal_reason=False)
        
        # Create Flask response with CSV
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=review_{review_id}_added_sources.csv'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Failed to export added sources: {str(e)}'}), 500

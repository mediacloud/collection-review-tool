/** API client for backend communication */
import axios from 'axios';

// Default to same-origin /api, so the built app served by Flask does not need CORS.
// VITE_API_BASE_URL can override this in special cases, but should normally be unset.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Start or resume a review for a collection
 * @param {number} collectionId - MediaCloud collection ID
 * @param {string} guidelinesTemplate - Guidelines template name (default: 'default')
 * @returns {Promise} Review object
 */
export async function startReview(collectionId, guidelinesTemplate = 'default', editMetadata = false) {
  const response = await api.post('/reviews/start', {
    collection_id: collectionId,
    guidelines_template: guidelinesTemplate,
    edit_metadata: !!editMetadata,
  });
  return response.data.review;
}

/**
 * Start a ReviewProject seeded from multiple MediaCloud collections.
 * @param {number[]} collectionIds
 * @param {string} guidelinesTemplate
 * @param {boolean} editMetadata
 * @param {string|null} name
 * @returns {Promise<Object>}
 */
export async function startReviewProject(
  collectionIds,
  guidelinesTemplate = 'default',
  editMetadata = false,
  name = null
) {
  const response = await api.post('/review-projects/start', {
    collection_ids: collectionIds,
    guidelines_template: guidelinesTemplate,
    edit_metadata: !!editMetadata,
    name,
  });
  return response.data;
}

/**
 * Step 2: generate reviewer queues for a ReviewProject.
 * @param {string} projectGuid
 * @param {number} queueCount
 */
export async function generateReviewProjectQueues(projectGuid, queueCount) {
  const response = await api.post(`/review-projects/${projectGuid}/queues`, {
    queue_count: queueCount,
  });
  return response.data;
}

/**
 * Get a ReviewProject (manager view).
 * @param {string} projectGuid
 */
export async function getReviewProject(projectGuid) {
  const response = await api.get(`/review-projects/${projectGuid}`);
  return response.data;
}

export function getReviewProjectExportUrl(projectGuid) {
  return `${API_BASE_URL}/review-projects/${projectGuid}/export`;
}

/**
 * Get all ReviewProjects with derived status and aggregated stats.
 * @returns {Promise<{projects: Array}>}
 */
export async function getReviewProjects() {
  const response = await api.get('/review-projects');
  return response.data.projects;
}

/**
 * Get a reviewer queue review by queue GUID.
 * @param {string} queueGuid
 */
export async function getReviewByQueueGuid(queueGuid) {
  const response = await api.get(`/review-queues/${queueGuid}`);
  return response.data.review;
}

export async function getReviewItemsByQueueGuid(queueGuid, options = {}) {
  const params = new URLSearchParams();
  if (options.page) params.append('page', options.page);
  if (options.page_size) params.append('page_size', options.page_size);
  if (options.decision) params.append('decision', options.decision);

  const response = await api.get(`/review-queues/${queueGuid}/items?${params.toString()}`);
  return response.data;
}

export async function decideQueueItem(queueGuid, itemId, decision, removalReason = null) {
  const body = { decision };
  if (decision === 'remove' && removalReason) {
    body.removal_reason = removalReason;
  }

  const response = await api.post(`/review-queues/${queueGuid}/items/${itemId}/decide`, body);
  return response.data;
}

export async function proposeNewSourceByQueueGuid(queueGuid, sourceLabel, sourceHomepage) {
  const response = await api.post(`/review-queues/${queueGuid}/items`, {
    source_label: sourceLabel,
    source_homepage: sourceHomepage,
  });
  return response.data;
}

export async function getReviewQueueGuidelines(queueGuid) {
  const response = await api.get(`/review-queues/${queueGuid}/guidelines`);
  return response.data.guidelines;
}

/**
 * Get all in-progress reviews
 * @returns {Promise} Array of review objects with completeness percentage
 */
export async function getInProgressReviews() {
  const response = await api.get('/reviews/in-progress');
  return response.data.reviews;
}

/**
 * Get all completed reviews
 * @returns {Promise} Array of review objects with completeness percentage
 */
export async function getCompletedReviews() {
  const response = await api.get('/reviews/completed');
  return response.data.reviews;
}

/**
 * Get a review by ID
 * @param {number} reviewId - Review ID
 * @returns {Promise} Review object with stats
 */
export async function getReview(reviewId) {
  const response = await api.get(`/reviews/${reviewId}`);
  return response.data.review;
}

/**
 * Get review items with optional filters
 * @param {number} reviewId - Review ID
 * @param {Object} options - Query options (page, page_size, decision)
 * @returns {Promise} Object with items array and total count
 */
export async function getReviewItems(reviewId, options = {}) {
  const params = new URLSearchParams();
  if (options.page) params.append('page', options.page);
  if (options.page_size) params.append('page_size', options.page_size);
  if (options.decision) params.append('decision', options.decision);
  
  const response = await api.get(`/reviews/${reviewId}/items?${params.toString()}`);
  return response.data;
}

/**
 * Make a decision on a review item
 * @param {number} reviewId - Review ID
 * @param {number} itemId - Item ID
 * @param {string} decision - Decision (keep, remove, add, undecided)
 * @param {string} removalReason - Reason for removal (required when decision is 'remove')
 * @returns {Promise} Updated item object
 */
export async function decideItem(reviewId, itemId, decision, removalReason = null) {
  const body = { decision };
  if (decision === 'remove' && removalReason) {
    body.removal_reason = removalReason;
  }
  const response = await api.post(`/reviews/${reviewId}/items/${itemId}/decide`, body);
  return response.data;
}

/**
 * Propose a new source for a review
 * @param {number} reviewId - Review ID
 * @param {string} sourceLabel - Source label/name
 * @param {string} sourceHomepage - Source homepage URL
 * @returns {Promise} Created item object
 */
export async function proposeNewSource(reviewId, sourceLabel, sourceHomepage) {
  const response = await api.post(`/reviews/${reviewId}/items`, {
    source_label: sourceLabel,
    source_homepage: sourceHomepage
  });
  return response.data;
}

/**
 * Complete a review
 * @param {number} reviewId - Review ID
 * @returns {Promise} Updated review object
 */
export async function completeReview(reviewId) {
  const response = await api.post(`/reviews/${reviewId}/complete`);
  return response.data.review;
}

/**
 * Get CSV export URL for a review (keep and add sources)
 * @param {number} reviewId - Review ID
 * @returns {string} Export URL
 */
export function getExportUrl(reviewId) {
  return `${API_BASE_URL}/reviews/${reviewId}/export`;
}

/**
 * Get CSV export URL for removed sources
 * @param {number} reviewId - Review ID
 * @returns {string} Export URL
 */
export function getRemovedSourcesExportUrl(reviewId) {
  return `${API_BASE_URL}/reviews/${reviewId}/export/removed`;
}

/**
 * Get CSV export URL for added sources
 * @param {number} reviewId - Review ID
 * @returns {string} Export URL
 */
export function getAddedSourcesExportUrl(reviewId) {
  return `${API_BASE_URL}/reviews/${reviewId}/export/added`;
}

/**
 * Get available guideline templates
 * @returns {Promise} Array of template names
 */
export async function getGuidelineTemplates() {
  const response = await api.get('/guidelines/templates');
  return response.data.templates;
}

/**
 * Get rendered guidelines for a review
 * @param {number} reviewId - Review ID
 * @returns {Promise} Guidelines text (markdown)
 */
export async function getReviewGuidelines(reviewId) {
  const response = await api.get(`/reviews/${reviewId}/guidelines`);
  return response.data.guidelines;
}

/**
 * Update mutable fields on a review
 * @param {number} reviewId - Review ID
 * @param {Object} payload - Fields to update (e.g., { edit_metadata: true })
 * @returns {Promise} Updated review object with stats
 */
export async function updateReview(reviewId, payload) {
  const response = await api.patch(`/reviews/${reviewId}`, payload);
  return response.data.review;
}

/**
 * Get live source details from MediaCloud via backend
 * @param {number} sourceId - MediaCloud source ID
 * @returns {Promise} Source object with latest metadata
 */
export async function getSourceDetails(sourceId) {
  const response = await api.get(`/sources/${sourceId}`);
  return response.data.source;
}

<script>
  import { onMount } from 'svelte';
  import { startReview, getInProgressReviews, getCompletedReviews, getGuidelineTemplates } from '../lib/api.js';

  let collectionId = '';
  let loading = false;
  let error = null;
  let inProgressReviews = [];
  let loadingReviews = false;
  let completedReviews = [];
  let loadingCompleted = false;
  let showCompleted = false;
  let guidelineTemplates = [];
  let selectedTemplate = 'default';
  let loadingTemplates = false;
  let editMetadata = false;

  onMount(async () => {
    await loadInProgressReviews();
    await loadGuidelineTemplates();
  });

  async function loadGuidelineTemplates() {
    loadingTemplates = true;
    try {
      guidelineTemplates = await getGuidelineTemplates();
      if (guidelineTemplates.length > 0 && !guidelineTemplates.includes(selectedTemplate)) {
        selectedTemplate = guidelineTemplates[0];
      }
    } catch (err) {
      console.error('Error loading templates:', err);
    } finally {
      loadingTemplates = false;
    }
  }

  async function loadInProgressReviews() {
    loadingReviews = true;
    try {
      inProgressReviews = await getInProgressReviews();
    } catch (err) {
      console.error('Error loading in-progress reviews:', err);
    } finally {
      loadingReviews = false;
    }
  }

  async function loadCompletedReviews() {
    if (completedReviews.length > 0) {
      // Already loaded, just toggle visibility
      showCompleted = !showCompleted;
      return;
    }
    
    loadingCompleted = true;
    try {
      completedReviews = await getCompletedReviews();
      showCompleted = true;
    } catch (err) {
      console.error('Error loading completed reviews:', err);
    } finally {
      loadingCompleted = false;
    }
  }

  function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function navigateToReview(reviewId) {
    window.navigate(`/reviews/${reviewId}`);
  }

  function handleKeydown(event, reviewId) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      navigateToReview(reviewId);
    }
  }

  async function handleSubmit() {
    // Convert to string and trim if it's a number
    const idStr = String(collectionId || '').trim();
    if (!idStr) {
      error = 'Please enter a collection ID';
      return;
    }

    const id = parseInt(idStr);
    if (isNaN(id) || id <= 0) {
      error = 'Collection ID must be a positive number';
      return;
    }

    loading = true;
    error = null;

    try {
      const review = await startReview(id, selectedTemplate, editMetadata);
      await loadInProgressReviews(); // Refresh the list
      window.navigate(`/reviews/${review.id}`);
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to start review';
      console.error('Error starting review:', err);
    } finally {
      loading = false;
    }
  }
</script>

<div class="container">
  <div class="main-content">
    <div class="card">
      <h1>MediaCloud Collections Review</h1>
      <p class="subtitle">Review and manage sources in MediaCloud collections</p>

      <form on:submit|preventDefault={handleSubmit}>
        <div class="form-group">
          <label for="collection-id">MediaCloud Collection ID</label>
          <input
            id="collection-id"
            type="number"
            bind:value={collectionId}
            placeholder="Enter collection ID"
            disabled={loading}
          />
        </div>

        {#if guidelineTemplates.length > 0}
          <div class="form-group">
            <label for="guideline-template">Annotation Guidelines Template</label>
            <select
              id="guideline-template"
              bind:value={selectedTemplate}
              disabled={loading || loadingTemplates}
            >
              {#each guidelineTemplates as template}
                <option value={template}>{template}</option>
              {/each}
            </select>
          </div>
        {/if}

        <div class="form-group">
          <button
            type="button"
            class="context-toggle-button"
            on:click={() => (editMetadata = !editMetadata)}
            disabled={loading}
          >
            <span class="toggle-label">
              <span class="toggle-indicator {editMetadata ? 'on' : 'off'}"></span>
              Enable metadata editing in this review
            </span>
          </button>
        </div>

        {#if error}
          <div class="error">{error}</div>
        {/if}

        <button type="submit" disabled={loading}>
          {loading ? 'Starting...' : 'Start / Resume Review'}
        </button>
      </form>
    </div>

    {#if inProgressReviews.length > 0}
      <div class="card reviews-list">
        <h2>Reviews in Progress</h2>
        {#if loadingReviews}
          <p class="loading-text">Loading reviews...</p>
        {:else}
          <div class="reviews-container">
            {#each inProgressReviews as review}
              <div 
                class="review-item" 
                on:click={() => navigateToReview(review.id)} 
                on:keydown={(e) => handleKeydown(e, review.id)}
                role="button" 
                tabindex="0"
              >
                <div class="review-header">
                  <span class="review-id">
                    {review.name || review.collection_name || `Collection #${review.collection_id}`}
                  </span>
                  <span class="completeness">{review.completeness}%</span>
                </div>
                <div class="review-meta">
                  <span class="review-date">Started: {formatDate(review.created_at)}</span>
                  {#if review.stats}
                    <span class="review-stats">
                      {review.stats.total} items • {review.stats.undecided} undecided
                    </span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <div class="card reviews-list">
      <div class="reviews-list-header">
        <h2>Completed Reviews</h2>
        <button 
          class="toggle-button" 
          on:click={loadCompletedReviews}
          disabled={loadingCompleted}
        >
          {loadingCompleted ? 'Loading...' : (showCompleted ? 'Hide' : 'Show')}
        </button>
      </div>
      {#if showCompleted}
        {#if loadingCompleted}
          <p class="loading-text">Loading reviews...</p>
        {:else if completedReviews.length === 0}
          <p class="empty-text">No completed reviews yet.</p>
        {:else}
          <div class="reviews-container">
            {#each completedReviews as review}
              <div 
                class="review-item completed" 
                on:click={() => navigateToReview(review.id)} 
                on:keydown={(e) => handleKeydown(e, review.id)}
                role="button" 
                tabindex="0"
              >
                <div class="review-header">
                  <span class="review-id">
                    {review.name || review.collection_name || `Collection #${review.collection_id}`}
                  </span>
                  <span class="completeness completed-badge">{review.completeness}%</span>
                </div>
                <div class="review-meta">
                  <span class="review-date">Completed: {formatDate(review.updated_at)}</span>
                  {#if review.stats}
                    <span class="review-stats">
                      {review.stats.total} items • {review.stats.undecided} undecided
                    </span>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      {/if}
    </div>
  </div>
</div>

<style>
  .container {
    min-height: 100vh;
    padding: 20px;
  }

  .main-content {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 40px;
    width: 100%;
  }

  h1 {
    font-size: 28px;
    margin-bottom: 10px;
    color: #2c3e50;
  }

  .subtitle {
    color: #7f8c8d;
    margin-bottom: 30px;
    font-size: 16px;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .context-toggle-button {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid #e0e4e8;
    background-color: #f8f9fa;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .context-toggle-button:hover:enabled {
    background-color: #eef2f7;
    border-color: #d0d7de;
  }

  .context-toggle-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .toggle-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #34495e;
  }

  .toggle-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid #bdc3c7;
    background-color: white;
  }

  .toggle-indicator.on {
    border-color: #27ae60;
    background-color: #27ae60;
  }

  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #34495e;
  }

  input, select {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    transition: border-color 0.3s;
  }

  input:focus, select:focus {
    outline: none;
    border-color: #3498db;
  }

  input:disabled, select:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }

  button {
    width: 100%;
    padding: 12px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  button:hover:not(:disabled) {
    background-color: #2980b9;
  }

  button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }

  .error {
    background-color: #fee;
    color: #c33;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 20px;
    border: 1px solid #fcc;
  }

  .reviews-list h2 {
    font-size: 24px;
    margin-bottom: 20px;
    color: #2c3e50;
  }

  .reviews-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .reviews-list-header h2 {
    margin-bottom: 0;
  }

  .toggle-button {
    padding: 8px 16px;
    background-color: #95a5a6;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
    white-space: nowrap;
  }

  .toggle-button:hover:not(:disabled) {
    background-color: #7f8c8d;
  }

  .toggle-button:disabled {
    background-color: #bdc3c7;
    cursor: not-allowed;
  }

  .empty-text {
    color: #7f8c8d;
    text-align: center;
    padding: 20px;
    font-style: italic;
  }

  .loading-text {
    color: #7f8c8d;
    text-align: center;
    padding: 20px;
  }

  .reviews-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .review-item {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;
    background-color: #fafafa;
  }

  .review-item:hover {
    background-color: #f0f0f0;
    border-color: #3498db;
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
  }

  .review-item.completed {
    background-color: #f8f9fa;
    border-color: #d5d5d5;
  }

  .review-item.completed:hover {
    background-color: #e9ecef;
    border-color: #95a5a6;
  }

  .review-item:focus {
    outline: 2px solid #3498db;
    outline-offset: 2px;
  }

  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .review-id {
    font-weight: 600;
    color: #2c3e50;
    font-size: 16px;
  }

  .completeness {
    font-weight: 600;
    color: #27ae60;
    font-size: 18px;
  }

  .completed-badge {
    color: #7f8c8d;
  }

  .review-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #7f8c8d;
  }

  .review-date {
    flex: 1;
  }

  .review-stats {
    margin-left: 16px;
  }
</style>

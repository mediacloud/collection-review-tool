<script>
  import { onMount } from 'svelte';
  import { 
    getReview, 
    getReviewItems, 
    decideItem, 
    proposeNewSource, 
    completeReview,
    getExportUrl,
    getRemovedSourcesExportUrl,
    getAddedSourcesExportUrl
  } from '../lib/api.js';
  import ReviewHeader from '../components/ReviewHeader.svelte';
  import SourceViewer from '../components/SourceViewer.svelte';
  import NewSourceForm from '../components/NewSourceForm.svelte';
  import RemovalReasonModal from '../components/RemovalReasonModal.svelte';

  let review = null;
  let currentItem = null;
  let allItems = [];
  let loading = false;
  let error = null;
  let reviewId = null;
  let showAllItems = false;
  let currentPath = window.location.pathname;
  let showRemovalModal = false;

  // Get review ID from URL
  function getReviewIdFromUrl() {
    const match = currentPath.match(/^\/reviews\/(\d+)$/);
    return match ? parseInt(match[1]) : null;
  }

  onMount(() => {
    // Listen for URL changes
    const updatePath = () => {
      currentPath = window.location.pathname;
      reviewId = getReviewIdFromUrl();
      if (reviewId) {
        loadReview();
      }
    };

    window.addEventListener('popstate', updatePath);
    reviewId = getReviewIdFromUrl();
    if (reviewId) {
      loadReview();
    }

    return () => {
      window.removeEventListener('popstate', updatePath);
    };
  });

  async function loadReview() {
    if (!reviewId) return;

    loading = true;
    error = null;

    try {
      review = await getReview(reviewId);
      if (review.status === 'completed') {
        await loadAllItems();
      } else {
        await loadNextUndecidedItem();
      }
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load review';
      console.error('Error loading review:', err);
    } finally {
      loading = false;
    }
  }

  async function loadAllItems() {
    if (!reviewId) return;

    try {
      const response = await getReviewItems(reviewId, {
        page: 1,
        page_size: 1000  // Get all items
      });
      allItems = response.items || [];
    } catch (err) {
      console.error('Error loading all items:', err);
    }
  }

  async function loadNextUndecidedItem() {
    if (!reviewId) return;

    try {
      const response = await getReviewItems(reviewId, {
        decision: 'undecided',
        page: 1,
        page_size: 1
      });

      if (response.items && response.items.length > 0) {
        currentItem = response.items[0];
      } else {
        currentItem = null;
      }
    } catch (err) {
      console.error('Error loading next item:', err);
    }
  }

  async function handleKeep() {
    if (!currentItem || loading) return;

    loading = true;
    error = null;

    try {
      await decideItem(reviewId, currentItem.id, 'keep');
      // Reload review to get updated stats
      review = await getReview(reviewId);
      // Load next undecided item
      await loadNextUndecidedItem();
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to update decision';
      console.error('Error making decision:', err);
    } finally {
      loading = false;
    }
  }

  function handleRemove() {
    if (!currentItem || loading) return;
    // Show modal to get removal reason
    showRemovalModal = true;
  }

  async function handleRemoveConfirm(removalReason) {
    if (!currentItem || loading) return;

    showRemovalModal = false;
    loading = true;
    error = null;

    try {
      await decideItem(reviewId, currentItem.id, 'remove', removalReason);
      // Reload review to get updated stats
      review = await getReview(reviewId);
      // Load next undecided item
      await loadNextUndecidedItem();
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to update decision';
      console.error('Error making decision:', err);
    } finally {
      loading = false;
    }
  }

  function handleRemoveCancel() {
    showRemovalModal = false;
  }

  async function handleNewSource(sourceLabel, sourceHomepage) {
    if (!reviewId || loading) return;

    loading = true;
    error = null;

    try {
      await proposeNewSource(reviewId, sourceLabel, sourceHomepage);
      // Reload review to get updated stats
      review = await getReview(reviewId);
      // Optionally reload items to show the new one
      await loadNextUndecidedItem();
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to add source';
      console.error('Error adding source:', err);
    } finally {
      loading = false;
    }
  }

  async function handleComplete() {
    if (!reviewId || loading) return;

    if (!confirm('Are you sure you want to complete this review? You can still download the CSV after completion.')) {
      return;
    }

    loading = true;
    error = null;

    try {
      review = await completeReview(reviewId);
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to complete review';
      console.error('Error completing review:', err);
    } finally {
      loading = false;
    }
  }
</script>

<div class="container">
  <div class="nav-link">
    <a href="/">← Back to Home</a>
  </div>

  {#if loading && !review}
    <div class="loading">Loading review...</div>
  {:else if error && !review}
    <div class="error-message">{error}</div>
  {:else if review}
    <ReviewHeader {review} />
    
    {#if error}
      <div class="error-banner">{error}</div>
    {/if}

    {#if review.status === 'completed'}
      <div class="completed-message">
        <p>✓ Review completed! Download the CSV export below.</p>
      </div>

      <div class="export-section">
        <h3>Export Files</h3>
        <div class="export-links">
          <a 
            href={getExportUrl(reviewId)} 
            download 
            class="btn-download"
          >
            Download Main Export (Keep & Add Sources)
          </a>
          {#if review.stats && review.stats.remove > 0}
            <a 
              href={getRemovedSourcesExportUrl(reviewId)} 
              download 
              class="btn-download btn-download-secondary"
            >
              Download Removed Sources ({review.stats.remove})
            </a>
          {/if}
          {#if review.stats && review.stats.add > 0}
            <a 
              href={getAddedSourcesExportUrl(reviewId)} 
              download 
              class="btn-download btn-download-secondary"
            >
              Download Added Sources ({review.stats.add})
            </a>
          {/if}
        </div>
      </div>

      <div class="items-section">
        <button 
          class="btn-toggle" 
          on:click={() => showAllItems = !showAllItems}
        >
          {showAllItems ? 'Hide' : 'Show'} All Decisions ({allItems.length})
        </button>

        {#if showAllItems && allItems.length > 0}
          <div class="items-table">
            <table>
              <thead>
                <tr>
                  <th>Source Label</th>
                  <th>Homepage</th>
                  <th>MediaCloud</th>
                  <th>Decision</th>
                  <th>Type</th>
                  <th>Removal Reason</th>
                </tr>
              </thead>
              <tbody>
                {#each allItems as item}
                  <tr>
                    <td>{item.source_label || 'N/A'}</td>
                    <td>
                      {#if item.source_homepage}
                        <a href={item.source_homepage} target="_blank" rel="noopener noreferrer">
                          {item.source_homepage}
                        </a>
                      {:else}
                        N/A
                      {/if}
                    </td>
                    <td>
                      {#if !item.is_new_source && item.source_id}
                        <a 
                          href={`https://search.mediacloud.org/sources/${item.source_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="mediacloud-table-link"
                        >
                          View ↗
                        </a>
                      {:else}
                        <span class="no-link">—</span>
                      {/if}
                    </td>
                    <td>
                      <span class="decision-badge decision-{item.decision}">
                        {item.decision}
                      </span>
                    </td>
                    <td>
                      {item.is_new_source ? 'New Source' : 'Existing'}
                    </td>
                    <td>
                      {#if item.decision === 'remove' && item.removal_reason}
                        <span class="removal-reason" title={item.removal_reason}>
                          {item.removal_reason}
                        </span>
                      {:else}
                        <span class="no-reason">—</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
      {:else}
        <SourceViewer 
          item={currentItem}
          onKeep={handleKeep}
          onRemove={handleRemove}
          {loading}
        />

      <NewSourceForm 
        onSubmit={handleNewSource}
        {loading}
      />

      <RemovalReasonModal
        show={showRemovalModal}
        sourceLabel={currentItem?.source_label}
        on:confirm={(e) => handleRemoveConfirm(e.detail)}
        on:close={handleRemoveCancel}
      />

      <div class="actions">
        <button 
          class="btn-complete" 
          on:click={handleComplete}
          disabled={loading}
        >
          Complete Review
        </button>
      </div>
    {/if}
  {/if}
</div>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }

  .nav-link {
    margin-bottom: 20px;
  }

  .nav-link a {
    color: #3498db;
    text-decoration: none;
    font-size: 14px;
    transition: color 0.3s;
  }

  .nav-link a:hover {
    color: #2980b9;
    text-decoration: underline;
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
    font-size: 18px;
  }

  .error-message {
    background: #fee;
    color: #c33;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #fcc;
    text-align: center;
  }

  .error-banner {
    background: #fee;
    color: #c33;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 20px;
    border: 1px solid #fcc;
  }

  .completed-message {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    text-align: center;
    margin-bottom: 20px;
  }

  .completed-message p {
    font-size: 18px;
    color: #27ae60;
    margin: 0;
  }

  .actions {
    margin-top: 20px;
  }

  .btn-complete {
    width: 100%;
    padding: 14px 24px;
    background-color: #27ae60;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  .btn-complete:hover:not(:disabled) {
    background-color: #229954;
  }

  .btn-complete:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }

  .export-section {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
  }

  .export-section h3 {
    margin-bottom: 20px;
    color: #2c3e50;
    font-size: 20px;
    text-align: center;
  }

  .export-links {
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .btn-download {
    display: block;
    padding: 14px 28px;
    background-color: #3498db;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    transition: background-color 0.3s;
    text-align: center;
  }

  .btn-download:hover {
    background-color: #2980b9;
  }

  .btn-download-secondary {
    background-color: #95a5a6;
  }

  .btn-download-secondary:hover {
    background-color: #7f8c8d;
  }

  .items-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  .btn-toggle {
    width: 100%;
    padding: 12px;
    background-color: #ecf0f1;
    color: #2c3e50;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
    margin-bottom: 20px;
  }

  .btn-toggle:hover {
    background-color: #bdc3c7;
  }

  .items-table {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  thead {
    background-color: #f8f9fa;
  }

  th {
    padding: 12px;
    text-align: left;
    font-weight: 600;
    color: #2c3e50;
    border-bottom: 2px solid #dee2e6;
  }

  td {
    padding: 12px;
    border-bottom: 1px solid #dee2e6;
  }

  tbody tr:hover {
    background-color: #f8f9fa;
  }

  .decision-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    text-transform: capitalize;
  }

  .decision-keep {
    background-color: #d4edda;
    color: #155724;
  }

  .decision-remove {
    background-color: #f8d7da;
    color: #721c24;
  }

  .decision-add {
    background-color: #d1ecf1;
    color: #0c5460;
  }

  .decision-undecided {
    background-color: #fff3cd;
    color: #856404;
  }

  table a {
    color: #3498db;
    text-decoration: none;
    word-break: break-all;
  }

  table a:hover {
    text-decoration: underline;
  }

  .removal-reason {
    max-width: 300px;
    display: inline-block;
    word-break: break-word;
    color: #721c24;
    font-size: 13px;
    line-height: 1.4;
  }

  .no-reason {
    color: #95a5a6;
    font-style: italic;
  }

  .mediacloud-table-link {
    color: #3498db;
    text-decoration: none;
    font-size: 13px;
  }

  .mediacloud-table-link:hover {
    text-decoration: underline;
  }

  .no-link {
    color: #95a5a6;
    font-style: italic;
  }
</style>

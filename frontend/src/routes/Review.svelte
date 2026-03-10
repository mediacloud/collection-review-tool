<script>
  import { onMount } from 'svelte';
  import { 
    getReview, 
    getReviewItems, 
    decideItem, 
    proposeNewSource, 
    getExportUrl,
    getRemovedSourcesExportUrl,
    getAddedSourcesExportUrl,
    getReviewGuidelines,
    getSourceDetails,
    updateReview
  } from '../lib/api.js';
  import iso3166 from 'iso-3166-2';
  import ReviewHeader from '../components/ReviewHeader.svelte';
  import SourceViewer from '../components/SourceViewer.svelte';
  import RemovalReasonModal from '../components/RemovalReasonModal.svelte';
  import NewSourceModal from '../components/NewSourceModal.svelte';
  import AllDecisionsModal from '../components/AllDecisionsModal.svelte';
  import EditMetadataModal from '../components/EditMetadataModal.svelte';

  let review = null;
  let currentItem = null;
  let allItems = [];
  let loading = false;
  let error = null;
  let reviewId = null;
  let showAllItems = false;
  let currentPath = window.location.pathname;
  let showRemovalModal = false;
  let showNewSourceModal = false;
  let guidelines = null;
  let showContextPanel = false;
  let showAllItemsModal = false;
  let showEditMetadataError = null;
  let showEditMetadataModal = false;
  let editFieldKey = null;
  let editFieldLabel = '';
  let editFieldCurrentValue = '';
  let editFieldOptions = [];

  const LANGUAGE_OPTIONS = [
    { value: 'en', label: 'en – English' },
    { value: 'es', label: 'es – Spanish' },
    { value: 'fr', label: 'fr – French' },
    { value: 'de', label: 'de – German' },
    { value: 'pt', label: 'pt – Portuguese' },
    { value: 'ru', label: 'ru – Russian' },
    { value: 'ar', label: 'ar – Arabic' },
    { value: 'zh', label: 'zh – Chinese' },
    { value: 'hi', label: 'hi – Hindi' },
    { value: 'bn', label: 'bn – Bengali' },
    { value: 'id', label: 'id – Indonesian' },
    { value: 'tr', label: 'tr – Turkish' },
    { value: 'vi', label: 'vi – Vietnamese' },
    { value: 'sw', label: 'sw – Swahili' },
    { value: 'fa', label: 'fa – Persian' }
  ];

  const COUNTRY_OPTIONS = [
    { value: 'US', label: 'US – United States' },
    { value: 'GB', label: 'GB – United Kingdom' },
    { value: 'CA', label: 'CA – Canada' },
    { value: 'AU', label: 'AU – Australia' },
    { value: 'NZ', label: 'NZ – New Zealand' },
    { value: 'FR', label: 'FR – France' },
    { value: 'DE', label: 'DE – Germany' },
    { value: 'ES', label: 'ES – Spain' },
    { value: 'IT', label: 'IT – Italy' },
    { value: 'BR', label: 'BR – Brazil' },
    { value: 'MX', label: 'MX – Mexico' },
    { value: 'AR', label: 'AR – Argentina' },
    { value: 'CN', label: 'CN – China' },
    { value: 'JP', label: 'JP – Japan' },
    { value: 'IN', label: 'IN – India' },
    { value: 'ZA', label: 'ZA – South Africa' },
    { value: 'NG', label: 'NG – Nigeria' },
    { value: 'EG', label: 'EG – Egypt' },
    { value: 'RU', label: 'RU – Russia' },
    { value: 'TR', label: 'TR – Türkiye' }
  ];

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
      // Always load all items so they're available for the "Show All Decisions" panel
      await loadAllItems();
      // Load guidelines
      await loadGuidelines();
      // Also load next undecided item if review is not completed
      if (review.status !== 'completed') {
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

  async function loadGuidelines() {
    if (!reviewId) return;

    try {
      guidelines = await getReviewGuidelines(reviewId);
    } catch (err) {
      console.error('Error loading guidelines:', err);
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
        await refreshCurrentItemMetadata();
      } else {
        currentItem = null;
      }
    } catch (err) {
      console.error('Error loading next item:', err);
    }
  }

  async function refreshCurrentItemMetadata() {
    if (!currentItem || currentItem.is_new_source || !currentItem.source_id) return;

    try {
      const liveSource = await getSourceDetails(currentItem.source_id);
      const mergedMetadata = {
        ...(currentItem.source_metadata || {}),
        ...liveSource
      };
      currentItem = {
        ...currentItem,
        source_metadata: mergedMetadata
      };
    } catch (err) {
      console.error('Error refreshing source metadata:', err);
    }
  }

  $: completionPercent = (review && review.stats)
    ? (() => {
        const total = review.stats.total || 0;
        if (!total) return 0;
        const undecided = review.stats.undecided || 0;
        const skipped = review.stats.skip || 0;
        const decided = total - undecided - skipped;
        return Math.round((decided / total) * 1000) / 10; // one decimal place
      })()
    : null;

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

  async function handleSkip() {
    if (!currentItem || loading) return;

    loading = true;
    error = null;

    try {
      await decideItem(reviewId, currentItem.id, 'skip');
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

  function handleOpenNewSourceModal() {
    if (loading) return;
    showNewSourceModal = true;
  }

  async function handleNewSourceModalConfirm(event) {
    const { label, homepage } = event.detail || {};
    showNewSourceModal = false;
    await handleNewSource(label, homepage);
  }

  function openAllDecisionsModal() {
    if (!allItems || allItems.length === 0) return;
    showAllItemsModal = true;
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

  function formatGuidelines(text) {
    if (!text) return '';
    // Simple markdown to HTML conversion
    const lines = text.split('\n');
    let html = '';
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Headers
      if (line.match(/^### /)) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += '<h3>' + line.substring(4) + '</h3>';
      } else if (line.match(/^## /)) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += '<h2>' + line.substring(3) + '</h2>';
      } else if (line.match(/^# /)) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += '<h1>' + line.substring(2) + '</h1>';
      } else if (line.match(/^- /)) {
        // List item
        if (!inList) {
          html += '<ul>';
          inList = true;
        }
        html += '<li>' + line.substring(2) + '</li>';
      } else {
        // Regular line
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        if (line.trim()) {
          // Apply bold formatting
          const bolded = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
          html += bolded + '<br>';
        } else {
          html += '<br>';
        }
      }
    }
    
    if (inList) {
      html += '</ul>';
    }
    
    return html;
  }

  async function toggleEditMetadata() {
    if (!review || !reviewId) return;
    const nextValue = !review.edit_metadata;
    showEditMetadataError = null;
    try {
      const updated = await updateReview(reviewId, { edit_metadata: nextValue });
      review = updated;
    } catch (err) {
      console.error('Error updating edit_metadata:', err);
      showEditMetadataError = err.response?.data?.error || err.message || 'Failed to update metadata editing setting';
    }
  }

  function openEditMetadata(fieldKey, label, currentValue, options = []) {
    editFieldKey = fieldKey;
    editFieldLabel = label;
    editFieldCurrentValue = currentValue || '';
    editFieldOptions = options;
    showEditMetadataModal = true;
  }

  function closeEditMetadata() {
    showEditMetadataModal = false;
    editFieldKey = null;
    editFieldLabel = '';
    editFieldCurrentValue = '';
    editFieldOptions = [];
  }

  function handleEditMetadataSave(event) {
    const newValue = event.detail;
    if (currentItem && currentItem.source_metadata && editFieldKey) {
      // If editing pub_state and we have a country code, validate ISO 3166-2
      if (editFieldKey === 'pub_state' && currentItem.source_metadata.pub_country && newValue) {
        const countryCode = currentItem.source_metadata.pub_country;
        const fullCode = `${countryCode}-${newValue}`;
        const subdivision = iso3166.subdivision(fullCode);
        if (!subdivision) {
          showEditMetadataError = `Invalid subdivision code "${newValue}" for country ${countryCode} (expected ISO 3166-2).`;
          return;
        }
        // Clear any previous error on success
        showEditMetadataError = null;
      }

      currentItem = {
        ...currentItem,
        source_metadata: {
          ...currentItem.source_metadata,
          [editFieldKey]: newValue
        }
      };
    }
    closeEditMetadata();
  }

</script>

<div class="container">
  {#if loading && !review}
    <div class="loading">Loading review...</div>
  {:else if error && !review}
    <div class="error-message">{error}</div>
  {:else if review}
    <div class="review-header-bar">
      <div class="review-footer-inner">
        <div class="footer-section footer-left">
          <button
            type="button"
            class="back-home"
            on:click={() => window.navigate('/')}
            title="Return to home"
            aria-label="Return to home"
          >
            ↩
          </button>
          <button
            type="button"
            class="sidebar-toggle"
            on:click={() => (showContextPanel = !showContextPanel)}
          >
            {showContextPanel ? 'Hide details' : 'Show details'}
          </button>
          <div class="footer-title">
            Review: {review.collection_name || `Collection #${review.collection_id}`}
            {#if completionPercent !== null}
              &nbsp;({completionPercent}% complete)
            {/if}
          </div>
        </div>
        <div class="footer-section footer-right">
          <button
            type="button"
            class="propose-button"
            on:click={handleOpenNewSourceModal}
            disabled={loading}
          >
            + Propose new source
          </button>
        </div>
      </div>
    </div>
    
    {#if showContextPanel}
      <div class="context-panel" on:click={() => (showContextPanel = false)}>
        <div class="context-inner" on:click|stopPropagation>
          <div class="context-section">
            <ReviewHeader {review} onShowAllDecisions={openAllDecisionsModal} />
          </div>

          <div class="context-section">
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
          </div>

          <div class="context-section">
            <button
              type="button"
              class="context-toggle-button"
              on:click={toggleEditMetadata}
            >
              <span class="toggle-label">
                <span class="toggle-indicator {review.edit_metadata ? 'on' : 'off'}"></span>
                Enable metadata editing for this review
              </span>
            </button>
            {#if showEditMetadataError}
              <div class="error-banner">
                {showEditMetadataError}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    <div class="review-layout">
      <div class="right-column">
        {#if error}
          <div class="error-banner">{error}</div>
        {/if}

        {#if guidelines}
          <div class="guidelines-section">
            <div class="guidelines-content">
              {@html formatGuidelines(guidelines)}
            </div>
          </div>
        {/if}

        {#if review.status === 'completed'}
          <div class="completed-message">
            <p>✓ Review completed! Download the CSV export below.</p>
          </div>
        {/if}

        {#if review.status !== 'completed'}
          <SourceViewer 
            item={currentItem}
            onKeep={handleKeep}
            onRemove={handleRemove}
            onSkip={handleSkip}
            editMetadata={review?.edit_metadata}
            onEditLanguage={() =>
              openEditMetadata(
                'primary_language',
                'Language (ISO 639-1)',
                currentItem?.source_metadata?.primary_language || currentItem?.source_metadata?.language,
                LANGUAGE_OPTIONS
              )
            }
            onEditPubCountry={() =>
              openEditMetadata(
                'pub_country',
                'Pub country (ISO 3166-1)',
                currentItem?.source_metadata?.pub_country,
                COUNTRY_OPTIONS
              )
            }
            onEditPubState={() =>
              openEditMetadata(
                'pub_state',
                'Pub state (ISO 3166-2)',
                currentItem?.source_metadata?.pub_state
              )
            }
            {loading}
          />
          
          <RemovalReasonModal
            show={showRemovalModal}
            sourceLabel={currentItem?.source_label}
            on:confirm={(e) => handleRemoveConfirm(e.detail)}
            on:close={handleRemoveCancel}
          />

          <NewSourceModal
            show={showNewSourceModal}
            {loading}
            on:confirm={handleNewSourceModalConfirm}
            on:close={() => (showNewSourceModal = false)}
          />
        {/if}
      </div>
    </div>

    <EditMetadataModal
      show={showEditMetadataModal}
      fieldLabel={editFieldLabel}
      currentValue={editFieldCurrentValue}
      options={editFieldOptions}
      on:save={handleEditMetadataSave}
      on:close={closeEditMetadata}
    />

    <AllDecisionsModal
      show={showAllItemsModal}
      items={allItems}
      on:close={() => (showAllItemsModal = false)}
    />
  {/if}
</div>

<style>
  .container {
    margin: 0 auto;
    padding: 20px;
    padding-top: 72px; /* space for fixed header */
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

  .review-layout {
    display: flex;
    gap: 20px;
    align-items: flex-start;
  }

  .right-column {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .review-header-bar {
    position: fixed;
    inset-inline: 0;
    top: 0;
    background: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    z-index: 900;
  }

  .review-footer-inner {
    max-width: 1320px;
    margin: 0 auto;
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
  }

  .footer-section {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .footer-left {
    min-width: 0;
  }

  .footer-title {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .footer-right {
    justify-content: flex-end;
  }

  .completion-pill {
    padding: 6px 12px;
    border-radius: 999px;
    background-color: #f0f3f6;
    color: #2c3e50;
    font-size: 13px;
    font-weight: 500;
  }

  .sidebar-toggle {
    padding: 6px 12px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background-color: white;
    font-size: 13px;
    font-weight: 500;
    color: #34495e;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .sidebar-toggle:hover {
    background-color: #f6f8fa;
    border-color: #c0c7d0;
  }

  .propose-button {
    padding: 8px 16px;
    border-radius: 999px;
    border: 1px solid #27ae60;
    background-color: #27ae60;
    color: white;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s, opacity 0.2s;
  }

  .propose-button:hover:enabled {
    background-color: #229954;
    border-color: #229954;
  }

  .propose-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .back-home {
    padding: 4px 8px;
    border: none;
    background: transparent;
    color: #2c3e50;
    font-size: 16px;
    font-weight: 400;
    text-decoration: none;
    cursor: pointer;
  }

  .back-home:hover {
    text-decoration: underline;
  }

  .context-panel {
    position: fixed;
    inset-inline: 0;
    top: 56px; /* just below header bar */
    bottom: 0;
    z-index: 850;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }

  .context-inner {
    max-width: 1320px;
    margin: 8px auto 0;
    background: white;
    border-radius: 10px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.16);
    border: 1px solid #d0d7de;
    padding: 12px 20px 12px;
    pointer-events: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .context-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }

  .context-title {
    font-size: 14px;
    font-weight: 600;
    color: #2c3e50;
  }

  .context-close {
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background-color: white;
    font-size: 12px;
    font-weight: 500;
    color: #34495e;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .context-close:hover {
    background-color: #f6f8fa;
    border-color: #c0c7d0;
  }

  .context-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
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

  .context-toggle-button:hover {
    background-color: #eef2f7;
    border-color: #d0d7de;
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

  .context-action {
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background-color: #f6f8fa;
    font-size: 12px;
    font-weight: 500;
    color: #34495e;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .context-action:hover:enabled {
    background-color: #e1e4e8;
    border-color: #c0c7d0;
  }

  .context-action:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-banner {
    background: #fee;
    color: #c33;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #fcc;
  }

  .guidelines-section {
    background: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 15px 20px;
    border-radius: 4px;
    margin-bottom: 20px;
  }

  .guidelines-content {
    color: #2c3e50;
    line-height: 1.4;
    font-size: 14px;
  }

  .guidelines-content :global(h1),
  .guidelines-content :global(h2),
  .guidelines-content :global(h3) {
    margin-top: 0;
    margin-bottom: 8px;
    color: #2c3e50;
  }

  .guidelines-content :global(h1) {
    font-size: 20px;
  }

  .guidelines-content :global(h2) {
    font-size: 18px;
  }

  .guidelines-content :global(h3) {
    font-size: 16px;
  }

  .guidelines-content :global(ul),
  .guidelines-content :global(ol) {
    margin: 8px 0;
    padding-left: 24px;
  }

  .guidelines-content :global(li) {
    margin: 4px 0;
  }

  .guidelines-content :global(strong) {
    font-weight: 600;
  }

  .completed-message {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    text-align: center;
  }

  .completed-message p {
    font-size: 18px;
    color: #27ae60;
    margin: 0;
  }

  .export-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  .left-actions {
    background: white;
    padding: 12px 16px 16px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  }

  .left-actions .btn-primary {
    width: 100%;
    padding: 10px 14px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s, transform 0.05s;
  }

  .left-actions .btn-primary:hover:not(:disabled) {
    background-color: #2980b9;
  }

  .left-actions .btn-primary:active:not(:disabled) {
    transform: translateY(1px);
  }

  .left-actions .btn-primary:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }

  .export-section h3 {
    margin-bottom: 15px;
    color: #2c3e50;
    font-size: 18px;
    text-align: center;
  }

  .export-links {
    display: flex;
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }

  .btn-download {
    display: block;
    padding: 12px 20px;
    background-color: #3498db;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-size: 14px;
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
    max-height: 400px;
    overflow-y: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  thead {
    background-color: #f8f9fa;
  }

  th {
    padding: 8px 6px;
    text-align: left;
    font-weight: 600;
    color: #2c3e50;
    border-bottom: 2px solid #dee2e6;
    font-size: 12px;
    white-space: nowrap;
  }

  td {
    padding: 8px 6px;
    border-bottom: 1px solid #dee2e6;
    font-size: 12px;
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

<script>
  import { onMount } from 'svelte';
  import SourceViewer from '../components/SourceViewer.svelte';
  import RemovalReasonModal from '../components/RemovalReasonModal.svelte';
  import { getReviewProject, getSkippedItemsByProjectGuid, decideQueueItem } from '../lib/api.js';

  let projectGuid = null;
  let project = null;
  let loading = false;
  let error = null;

  let items = [];
  let total = 0;
  let currentItem = null;

  let showRemovalModal = false;
  let removalTargetItem = null;

  function parseProjectGuidFromUrl() {
    const match = window.location.pathname.match(/^\/review-projects\/([0-9a-fA-F-]+)\/skipped$/);
    return match ? match[1] : null;
  }

  async function loadSkipped() {
    if (!projectGuid) return;
    loading = true;
    error = null;
    try {
      const [projectResp, data] = await Promise.all([
        getReviewProject(projectGuid),
        getSkippedItemsByProjectGuid(projectGuid, {
          page: 1,
          page_size: 1000,
          dedupe_source_id: true
        })
      ]);

      project = projectResp.project;

      items = data.items || [];
      total = data.total || 0;
      currentItem = items.length > 0 ? items[0] : null;
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load skipped sources';
      console.error('Error loading skipped sources:', err);
      items = [];
      total = 0;
      currentItem = null;
    } finally {
      loading = false;
    }
  }

  async function handleKeep() {
    if (!currentItem || loading) return;
    loading = true;
    error = null;
    try {
      await decideQueueItem(currentItem.queue_guid, currentItem.id, 'keep');
      await loadSkipped();
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to update decision';
      console.error('Error keeping skipped item:', err);
      loading = false;
    }
  }

  function handleRemove() {
    if (!currentItem || loading) return;
    showRemovalModal = true;
    removalTargetItem = currentItem;
  }

  async function handleRemoveConfirm(removalReason) {
    showRemovalModal = false;
    const target = removalTargetItem;
    removalTargetItem = null;
    if (!target || loading) return;

    loading = true;
    error = null;
    try {
      await decideQueueItem(target.queue_guid, target.id, 'remove', removalReason);
      await loadSkipped();
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to update decision';
      console.error('Error removing skipped item:', err);
      loading = false;
    }
  }

  onMount(async () => {
    projectGuid = parseProjectGuidFromUrl();
    await loadSkipped();
  });

  function goBack() {
    if (!projectGuid) return;
    window.navigate(`/review-projects/${projectGuid}`);
  }

  function handleSkipForNow() {
    if (loading || !currentItem) return;

    // "Skip for now" in the virtual skipped queue just rotates the current item
    // to the end of the local in-memory list (decision remains `skip`).
    if (items.length <= 1) return;

    const idx = items.findIndex((i) => i.id === currentItem.id);
    if (idx < 0 || idx === items.length - 1) return;

    const rotated = [...items];
    const [moved] = rotated.splice(idx, 1);
    rotated.push(moved);
    items = rotated;
    currentItem = rotated[0];
  }
</script>

<div class="container">
  <div class="header-bar">
    <div class="header-left">
      <button type="button" class="back-home" on:click={goBack}>↩</button>
      <div class="title">ReviewProject: {project?.name || projectGuid}</div>
    </div>
  </div>

  <div class="subheader">Skipped Sources</div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if loading && !currentItem}
    <div class="loading">Loading skipped sources...</div>
  {:else if !currentItem}
    <div class="empty-card">
      <div class="empty-title">Queue exhausted</div>
      <div class="empty-subtitle">
        There are no skipped sources left in this project.
      </div>
    </div>
  {:else}
    <SourceViewer
      item={currentItem}
      onKeep={handleKeep}
      onRemove={handleRemove}
      onSkip={handleSkipForNow}
      showSkip={true}
      editMetadata={false}
    />
  {/if}

  <RemovalReasonModal
    show={showRemovalModal}
    sourceLabel={removalTargetItem?.source_label}
    on:confirm={(e) => handleRemoveConfirm(e.detail)}
    on:close={() => (showRemovalModal = false)}
  />
</div>

<style>
  .container {
    margin: 0 auto;
    padding: 20px;
    padding-top: 72px;
    max-width: 80%;
  }

  .header-bar {
    position: fixed;
    top: 0;
    inset-inline: 0;
    background: #414a55;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
    z-index: 900;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 10px 20px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    color: white;
    min-width: 0;
  }

  .top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 14px;
  }

  .back-home {
    padding: 4px 8px;
    border: none;
    background: transparent;
    color: #f6f8fa;
    cursor: pointer;
    font-size: 16px;
    font-weight: 400;
  }

  .back-home:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
  }

  .title {
    font-weight: 700;
    color: #f6f8fa;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .subheader {
    margin: 0 0 20px;
    font-size: 20px;
    font-weight: 900;
    color: #2c3e50;
  }

  .count {
    font-size: 13px;
    color: #7f8c8d;
    font-weight: 800;
  }

  .loading {
    text-align: center;
    padding: 40px 0;
    color: #7f8c8d;
    font-size: 18px;
  }

  .error-banner {
    background: #fee;
    color: #c33;
    padding: 12px 14px;
    border-radius: 8px;
    border: 1px solid #fcc;
    margin-bottom: 16px;
    text-align: center;
  }

  .empty-card {
    background: white;
    border: 1px solid #d0d7de;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    padding: 18px 18px;
  }

  .empty-title {
    font-size: 16px;
    font-weight: 900;
    color: #2c3e50;
    margin-bottom: 6px;
  }

  .empty-subtitle {
    color: #7f8c8d;
    font-size: 13px;
    line-height: 1.35;
  }
</style>


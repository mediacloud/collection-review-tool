<script>
  import { onMount } from 'svelte';
  import {
    getReviewProject,
    getRemovedItemsByProjectGuid,
    decideQueueItem,
  } from '../lib/api.js';

  let projectGuid = null;
  let project = null;

  let loading = false;
  let error = null;
  let actionError = null;

  let items = [];
  let total = 0;
  let requeueLoadingId = null;

  function parseProjectGuidFromUrl() {
    const match = window.location.pathname.match(
      /^\/review-projects\/([0-9a-fA-F-]+)\/removed$/
    );
    return match ? match[1] : null;
  }

  function goBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    if (!projectGuid) return;
    window.navigate(`/review-projects/${projectGuid}`);
  }

  async function loadRemoved() {
    if (!projectGuid) return;
    loading = true;
    error = null;
    actionError = null;
    try {
      const [projectResp, removedResp] = await Promise.all([
        getReviewProject(projectGuid),
        getRemovedItemsByProjectGuid(projectGuid, {
          page: 1,
          page_size: 1000,
          dedupe_source_id: true,
        }),
      ]);

      project = projectResp.project;

      items = removedResp.items || [];
      total = removedResp.total || 0;
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load removed sources';
      console.error('Error loading removed sources:', err);
      items = [];
      total = 0;
    } finally {
      loading = false;
    }
  }

  async function handleRequeue(item) {
    if (!item || loading) return;
    requeueLoadingId = item.id;
    actionError = null;
    try {
      await decideQueueItem(item.queue_guid, item.id, 'skip');
      await loadRemoved();
    } catch (err) {
      actionError = err.response?.data?.error || err.message || 'Failed to requeue source';
      console.error('Error requeuing source:', err);
    } finally {
      requeueLoadingId = null;
    }
  }

  onMount(() => {
    projectGuid = parseProjectGuidFromUrl();
    loadRemoved();
  });
</script>

<div class="container">
  <div class="header-bar">
    <div class="header-left">
      <button type="button" class="back-home" on:click={goBack}>↩</button>
      <div class="title">ReviewProject: {project?.name || projectGuid}</div>
    </div>
  </div>

  <div class="subheader">Removed Sources</div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if actionError}
    <div class="error-banner meta-error">{actionError}</div>
  {/if}

  {#if loading && items.length === 0}
    <div class="loading">Loading removed sources...</div>
  {:else if items.length === 0}
    <div class="empty-card">
      <div class="empty-title">No removed sources</div>
      <div class="empty-subtitle">
        There are no sources marked as <strong>remove</strong> in this project.
      </div>
    </div>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Source Label</th>
            <th>Homepage</th>
            <th>Language</th>
            <th>Pub country</th>
            <th>Pub state</th>
            <th>Removal reason</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {#each items as item (item.id)}
            <tr>
              <td class="td-label">{item.source_label || 'N/A'}</td>
              <td>
                {#if item.source_homepage}
                  <a href={item.source_homepage} target="_blank" rel="noopener noreferrer">
                    {item.source_homepage}
                  </a>
                {:else}
                  —
                {/if}
              </td>
              <td>{item.source_metadata?.primary_language || item.source_metadata?.language || '—'}</td>
              <td>{item.source_metadata?.pub_country || '—'}</td>
              <td>{item.source_metadata?.pub_state || '—'}</td>
              <td class="td-reason">{item.removal_reason || '—'}</td>
              <td class="td-actions">
                <button
                  type="button"
                  class="btn-inline"
                  on:click={() => handleRequeue(item)}
                  disabled={loading || requeueLoadingId === item.id}
                  title={requeueLoadingId === item.id ? 'Requeueing...' : undefined}
                >
                  requeue
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
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

  .meta-error {
    margin-top: -6px;
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

  .table-wrapper {
    margin-top: 12px;
    overflow: auto;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    background: white;
    max-height: 700px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  thead {
    background-color: #f8f9fa;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  th {
    padding: 10px 10px;
    text-align: left;
    font-weight: 700;
    color: #2c3e50;
    border-bottom: 2px solid #dee2e6;
    white-space: nowrap;
  }

  td {
    padding: 10px 10px;
    border-bottom: 1px solid #dee2e6;
    vertical-align: top;
  }

  td a {
    color: #3498db;
    text-decoration: none;
  }

  td a:hover {
    text-decoration: underline;
  }

  .td-label {
    max-width: 260px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .td-reason {
    max-width: 320px;
  }

  .td-actions {
    white-space: nowrap;
  }

  .metadata-actions-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
  }

  .btn-inline {
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background: #fff;
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    color: #34495e;
  }

  .btn-inline:hover:not(:disabled) {
    background-color: #f6f8fa;
  }

  .btn-inline:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>


<script>
  import { createEventDispatcher } from 'svelte';

  export let show = false;
  export let items = [];
  /** @type {string} */
  export let modalTitle = 'All Decisions';
  /** @type {string} */
  export let modalDescription =
    'Showing all sources and their review decisions for this collection.';
  export let showQueueColumn = false;
  /** When true, show whether each row appears in the Project CSV download (keep/add only). */
  export let showProjectCsvColumn = false;
  /** Shown under the description when the item list is truncated (e.g. large projects). */
  export let truncationNote = '';
  export let loading = false;

  const dispatch = createEventDispatcher();

  function handleClose() {
    dispatch('close');
  }
</script>

{#if show}
  <div class="modal-overlay" on:click={handleClose}>
    <div
      class="modal-content"
      on:click|stopPropagation
      role="dialog"
      aria-modal="true"
      aria-labelledby="all-decisions-title"
    >
      <div class="modal-header">
        <h2 id="all-decisions-title">{modalTitle}</h2>
        <button class="close-button" type="button" on:click={handleClose} aria-label="Close">
          ×
        </button>
      </div>
      <p class="modal-description">
        {modalDescription}
      </p>
      {#if truncationNote}
        <p class="modal-truncation">{truncationNote}</p>
      {/if}

      <div class="table-wrapper">
        {#if loading}
          <p class="empty-text">Loading…</p>
        {:else if items && items.length > 0}
          <table>
            <thead>
              <tr>
                {#if showQueueColumn}
                  <th>Queue</th>
                {/if}
                <th>Source Label</th>
                <th>Homepage</th>
                <th>MediaCloud</th>
                <th>Decision</th>
                <th title="Optional note when the reviewer skipped this source.">Skip note</th>
                {#if showProjectCsvColumn}
                  <th
                    class="th-project-csv"
                    title="Yes if this row is included in the Project CSV file (keep or add only)."
                  >
                    Project CSV
                  </th>
                {/if}
                <th>Type</th>
                <th>Removal Reason</th>
              </tr>
            </thead>
            <tbody>
              {#each items as item}
                <tr>
                  {#if showQueueColumn}
                    <td>
                      {#if item.queue_index != null && item.queue_index !== undefined}
                        Queue #{(item.queue_index ?? 0) + 1}
                      {:else}
                        —
                      {/if}
                    </td>
                  {/if}
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
                    {#if item.decision === 'skip' && item.skip_note}
                      <span class="skip-note-cell" title={item.skip_note}>{item.skip_note}</span>
                    {:else}
                      <span class="no-reason">—</span>
                    {/if}
                  </td>
                  {#if showProjectCsvColumn}
                    <td>
                      {#if item.in_mc_export}
                        <span class="export-yes">Yes</span>
                      {:else}
                        <span class="export-no">No</span>
                      {/if}
                    </td>
                  {/if}
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
        {:else}
          <p class="empty-text">No items to display yet.</p>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 24px;
    z-index: 1000;
  }

  .modal-content {
    background: white;
    border-radius: 10px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
    max-width: 960px;
    width: 100%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    padding: 20px 22px 18px;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 4px;
  }

  h2 {
    margin: 0;
    font-size: 20px;
    color: #2c3e50;
  }

  .close-button {
    border: none;
    background: transparent;
    font-size: 22px;
    line-height: 1;
    cursor: pointer;
    color: #7f8c8d;
    padding: 4px 6px;
    border-radius: 999px;
    transition: background-color 0.2s, color 0.2s;
  }

  .close-button:hover {
    background-color: #ecf0f1;
    color: #2c3e50;
  }

  .modal-description {
    margin: 0 0 10px;
    font-size: 13px;
    color: #7f8c8d;
  }

  .modal-truncation {
    margin: -4px 0 10px;
    font-size: 12px;
    line-height: 1.4;
    color: #856404;
    background: #fff8e6;
    border: 1px solid #f5e0a8;
    border-radius: 6px;
    padding: 8px 10px;
  }

  .export-yes {
    font-weight: 700;
    color: #1f7a3d;
  }

  .export-no {
    color: #7f8c8d;
  }

  .table-wrapper {
    margin-top: 4px;
    overflow: auto;
    border-radius: 6px;
    border: 1px solid #dee2e6;
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

  .decision-skip {
    background-color: #e2e3e5;
    color: #495057;
  }

  a {
    color: #3498db;
    text-decoration: none;
    word-break: break-all;
  }

  a:hover {
    text-decoration: underline;
  }

  .mediacloud-table-link {
    color: #3498db;
    text-decoration: none;
    font-size: 13px;
  }

  .mediacloud-table-link:hover {
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

  .skip-note-cell {
    max-width: 280px;
    display: inline-block;
    word-break: break-word;
    color: #856404;
    font-size: 13px;
    line-height: 1.4;
  }

  .no-reason {
    color: #95a5a6;
    font-style: italic;
  }

  .no-link {
    color: #95a5a6;
    font-style: italic;
  }

  .empty-text {
    padding: 16px;
    text-align: center;
    color: #7f8c8d;
    font-size: 14px;
  }
</style>


<script>
  export let item;
  export let onKeep;
  export let onRemove;
  export let onSkip;
  export let editMetadata = false;
  export let onEditLanguage;
  export let onEditPubCountry;
  export let onEditPubState;
  export let loading = false;

  let faviconUrl = null;
  let metadata = {};
  let correctLanguage = false;
  let correctPubCountry = false;
  let correctPubState = false;
  let lastItemId = null;

  function formatNumber(value) {
    if (value === null || value === undefined || isNaN(Number(value))) {
      return null;
    }
    return Number(value).toLocaleString("en-US");
  }

  function formatDateTime(value) {
    if (!value) return null;
    const date = new Date(value);
    if (isNaN(date.getTime())) return null;
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  $: metadata = item && item.source_metadata ? item.source_metadata : {};

  $: if (item && item.source_homepage) {
    try {
      faviconUrl = `https://www.google.com/s2/favicons?domain_url=${encodeURIComponent(
        item.source_homepage
      )}&sz=64`;
    } catch (e) {
      faviconUrl = null;
    }
  } else {
    faviconUrl = null;
  }

  // Reset "correct" flags when the review item changes
  $: if (item && item.id !== lastItemId) {
    lastItemId = item.id;
    correctLanguage = false;
    correctPubCountry = false;
    correctPubState = false;
  }

  function handleEditLanguage() {
    correctLanguage = true;
    if (onEditLanguage) onEditLanguage();
  }

  function handleEditPubCountry() {
    correctPubCountry = true;
    if (onEditPubCountry) onEditPubCountry();
  }

  function handleEditPubState() {
    correctPubState = true;
    if (onEditPubState) onEditPubState();
  }

  $: canKeep = !loading && (!editMetadata || (correctLanguage && correctPubCountry && correctPubState));
</script>

{#if item}
  <div class="source-viewer">
    <div class="source-info">
      <div class="source-header">
        <div class="source-title-row">
          {#if faviconUrl}
            <img src={faviconUrl} alt="" class="favicon" />
          {/if}
          <div class="title-and-url">
            <h3>{item.source_label || 'Unnamed Source'}</h3>
            {#if item.source_homepage}
              <a
                href={item.source_homepage}
                target="_blank"
                rel="noopener noreferrer"
                class="homepage-inline"
              >
                {item.source_homepage}
              </a>
            {/if}
          </div>
          {#if metadata.stories_per_week && formatNumber(metadata.stories_per_week)}
            <span class="stories-pill">
              {formatNumber(metadata.stories_per_week)} stories per week
            </span>
          {/if}
        </div>
        <div class="header-right">
          {#if !item.is_new_source && item.source_id}
            <a 
              href={`https://search.mediacloud.org/sources/${item.source_id}`}
              target="_blank"
              rel="noopener noreferrer"
              class="mediacloud-link"
              title="Review source in MediaCloud"
            >
              Review in MediaCloud ↗
            </a>
          {/if}
        </div>
      </div>
      {#if item.is_new_source}
        <span class="badge new-source">New Source</span>
      {:else if item.source_id}
        <div class="source-metadata">
          <div class="metadata-grid">
            <div class="meta-card">
              <div class="meta-label">Language</div>
              <div class="meta-row">
                <div class="meta-value">
                  {metadata.primary_language || metadata.language || '—'}
                </div>
                {#if editMetadata}
                  <div class="meta-controls">
                    <button type="button" class="meta-correct-button">
                      <label class="meta-checkbox-label">
                        <input type="checkbox" bind:checked={correctLanguage} />
                        <span>Correct</span>
                      </label>
                    </button>
                    <button type="button" class="meta-edit-button" on:click={handleEditLanguage}>
                      Edit
                    </button>
                  </div>
                {/if}
              </div>
            </div>
            <div class="meta-card">
              <div class="meta-label">Pub country</div>
              <div class="meta-row">
                <div class="meta-value">
                  {metadata.pub_country || '—'}
                </div>
                {#if editMetadata}
                  <div class="meta-controls">
                    <button type="button" class="meta-correct-button">
                      <label class="meta-checkbox-label">
                        <input type="checkbox" bind:checked={correctPubCountry} />
                        <span>Correct</span>
                      </label>
                    </button>
                    <button type="button" class="meta-edit-button" on:click={handleEditPubCountry}>
                      Edit
                    </button>
                  </div>
                {/if}
              </div>
            </div>
            <div class="meta-card">
              <div class="meta-label">Pub state</div>
              <div class="meta-row">
                <div class="meta-value">
                  {metadata.pub_state || '—'}
                </div>
                {#if editMetadata}
                  <div class="meta-controls">
                    <button type="button" class="meta-correct-button">
                      <label class="meta-checkbox-label">
                        <input type="checkbox" bind:checked={correctPubState} />
                        <span>Correct</span>
                      </label>
                    </button>
                    <button type="button" class="meta-edit-button" on:click={handleEditPubState}>
                      Edit
                    </button>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
    
    <div class="actions">
      <div class="actions-left">
        <button 
          class="btn btn-remove" 
          on:click={onRemove} 
          disabled={loading}
        >
          Remove
        </button>
      </div>
      <div class="actions-right">
        <button 
          class="btn btn-skip" 
          on:click={onSkip} 
          disabled={loading}
        >
          Skip for now
        </button>
        <button 
          class="btn btn-keep" 
          on:click={onKeep} 
          disabled={!canKeep}
        >
          Keep
        </button>
      </div>
    </div>
  </div>
{:else}
  <div class="no-items">
    <p>No more items to review!</p>
  </div>
{/if}

<style>
  .source-viewer {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    margin: 0 auto 20px;
    width: 80%;
  }

  .source-info {
    margin-bottom: 25px;
  }

  .source-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 15px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }

  .header-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }

  .source-title-row {
    display: flex;
    align-items: stretch;
    gap: 12px;
  }

  .title-and-url {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    flex: 1;
  }

  h3 {
    font-size: 22px;
    margin: 0;
    color: #2c3e50;
    flex: 0 0 auto;
  }

  .favicon {
    width: 40px;
    height: 40px;
    border-radius: 4px;
    box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.06);
    flex-shrink: 0;
  }

  .mediacloud-link {
    color: #3498db;
    text-decoration: none;
    font-size: 14px;
    white-space: nowrap;
    transition: color 0.3s;
  }

  .stories-pill {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 12px 14px;
    border-radius: 10px;
    border: 1px solid #e0e4e8;
    background-color: #f8f9fa;
    color: #2c3e50;
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
  }

  .mediacloud-link:hover {
    color: #2980b9;
    text-decoration: underline;
  }

  .source-metadata {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #ecf0f1;
  }

  .metadata-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }

  .meta-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 12px 14px;
    border: 1px solid #e0e4e8;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .meta-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .meta-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #7f8c8d;
    font-weight: 600;
  }

  .meta-value {
    font-size: 15px;
    color: #2c3e50;
    word-break: break-word;
  }

  .meta-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .meta-checkbox-label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #34495e;
  }

  .meta-checkbox-label input {
    width: 14px;
    height: 14px;
  }

  .meta-correct-button {
    padding: 4px 8px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background-color: #f8f9fa;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .meta-correct-button:hover {
    background-color: #e1e4e8;
    border-color: #c0c7d0;
  }

  .meta-edit-button {
    padding: 4px 8px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background-color: white;
    font-size: 12px;
    font-weight: 500;
    color: #34495e;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .meta-edit-button:hover {
    background-color: #f6f8fa;
    border-color: #c0c7d0;
  }

  .monospace {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  }

  .homepage-inline {
    color: #3498db;
    text-decoration: none;
    font-size: 14px;
    word-break: break-all;
  }

  .homepage-inline:hover {
    text-decoration: underline;
  }

  .badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 10px;
  }

  .new-source {
    background-color: #3498db;
    color: white;
  }

  .actions {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }

  .actions-left,
  .actions-right {
    display: flex;
    gap: 12px;
    flex: 1;
  }

  .actions-left {
    justify-content: flex-start;
  }

  .actions-right {
    justify-content: flex-end;
  }

  .btn {
    padding: 14px 24px;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-keep {
    min-width: 50%;
    background-color: #27ae60;
    color: white;
  }

  .btn-keep:hover:not(:disabled) {
    background-color: #229954;
  }

  .btn-remove {
    min-width: 50%;
    background-color: transparent;
    color: #e74c3c;
    border: 1px solid #e74c3c;
  }

  .btn-remove:hover:not(:disabled) {
    background-color: rgba(231, 76, 60, 0.08);
  }

  .btn-skip {
    flex: 0 0 20%;
    background-color: #fff3cd;
    color: #856404;
  }

  .btn-skip:hover:not(:disabled) {
    background-color: #ffe08a;
  }

  .no-items {
    background: white;
    padding: 40px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  .no-items p {
    font-size: 18px;
    color: #7f8c8d;
  }
</style>

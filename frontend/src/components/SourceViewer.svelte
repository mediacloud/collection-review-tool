<script>
  export let item;
  export let onKeep;
  export let onRemove;
  export let onSkip;
  export let loading = false;

  let faviconUrl = null;
  let metadata = {};

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
        </div>
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
      {#if item.is_new_source}
        <span class="badge new-source">New Source</span>
      {:else if item.source_id}
        <div class="source-metadata">
          <div class="metadata-grid">
            <div class="meta-card">
              <div class="meta-label">Language</div>
              <div class="meta-value">
                {metadata.primary_language || metadata.language || '—'}
              </div>
            </div>
            <div class="meta-card">
              <div class="meta-label">Pub country</div>
              <div class="meta-value">
                {metadata.pub_country || '—'}
              </div>
            </div>
            <div class="meta-card">
              <div class="meta-label">Pub state</div>
              <div class="meta-value">
                {metadata.pub_state || '—'}
              </div>
            </div>
            <div class="meta-card">
              <div class="meta-label">Stories / week</div>
              <div class="meta-value">
                {#if metadata.stories_per_week && formatNumber(metadata.stories_per_week)}
                  {formatNumber(metadata.stories_per_week)}
                {:else}
                  —
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
    
    <div class="actions">
      <button 
        class="btn btn-keep" 
        on:click={onKeep} 
        disabled={loading}
      >
        Keep
      </button>
      <button 
        class="btn btn-remove" 
        on:click={onRemove} 
        disabled={loading}
      >
        Remove
      </button>
      <button 
        class="btn btn-skip" 
        on:click={onSkip} 
        disabled={loading}
      >
        Skip for now
      </button>
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
    margin-bottom: 20px;
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

  .source-title-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }

  .title-and-url {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
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
    grid-template-columns: repeat(4, minmax(0, 1fr));
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
    gap: 12px;
  }

  .btn {
    flex: 1;
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
    background-color: #27ae60;
    color: white;
  }

  .btn-keep:hover:not(:disabled) {
    background-color: #229954;
  }

  .btn-remove {
    background-color: #e74c3c;
    color: white;
  }

  .btn-remove:hover:not(:disabled) {
    background-color: #c0392b;
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

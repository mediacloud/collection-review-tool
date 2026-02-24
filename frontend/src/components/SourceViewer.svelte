<script>
  export let item;
  export let onKeep;
  export let onRemove;
  export let loading = false;
</script>

{#if item}
  <div class="source-viewer">
    <div class="source-info">
      <div class="source-header">
        <h3>{item.source_label || 'Unnamed Source'}</h3>
        {#if !item.is_new_source && item.source_id}
          <a 
            href={`https://search.mediacloud.org/sources/${item.source_id}`}
            target="_blank"
            rel="noopener noreferrer"
            class="mediacloud-link"
            title="View source in MediaCloud"
          >
            View in MediaCloud ↗
          </a>
        {/if}
      </div>
      {#if item.source_homepage}
        <a href={item.source_homepage} target="_blank" rel="noopener noreferrer" class="homepage-link">
          {item.source_homepage}
        </a>
      {/if}
      {#if item.is_new_source}
        <span class="badge new-source">New Source</span>
      {:else if item.source_id}
        <div class="source-metadata">
          <span class="metadata-item">Source ID: {item.source_id}</span>
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

  h3 {
    font-size: 22px;
    margin: 0;
    color: #2c3e50;
    flex: 1;
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
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #ecf0f1;
  }

  .metadata-item {
    font-size: 13px;
    color: #7f8c8d;
    display: inline-block;
    margin-right: 15px;
  }

  .homepage-link {
    color: #3498db;
    text-decoration: none;
    font-size: 14px;
    word-break: break-all;
    display: block;
    margin-top: 8px;
  }

  .homepage-link:hover {
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
    gap: 15px;
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

<script>
  export let review;
  export let onShowAllDecisions;
</script>

<div class="header">
  <div class="info">
    <div class="collection-info">
      <h2>{review.collection_name || `Collection #${review.collection_id}`}</h2>
      <span class="status status-{review.status}">{review.status}</span>
    </div>
    <a 
      href={`https://search.mediacloud.org/collections/${review.collection_id}`}
      target="_blank"
      rel="noopener noreferrer"
      class="mediacloud-icon-link"
      aria-label="Open collection in MediaCloud"
      title="Open this collection in MediaCloud"
    >
      ↗
    </a>
  </div>
  
  {#if review.stats}
    <div class="stats">
      <div class="stat">
        <span class="stat-label">Total</span>
        <span class="stat-value">{review.stats.total}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Keep</span>
        <span class="stat-value stat-keep">{review.stats.keep}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Remove</span>
        <span class="stat-value stat-remove">{review.stats.remove}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Add</span>
        <span class="stat-value stat-add">{review.stats.add}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Undecided</span>
        <span class="stat-value stat-undecided">{review.stats.undecided}</span>
      </div>
    </div>
    {#if onShowAllDecisions}
      <button
        type="button"
        class="all-decisions-button"
        on:click={onShowAllDecisions}
      >
        Show all decisions
      </button>
    {/if}
  {/if}
</div>

<style>
  .header {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .info {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 15px;
  }

  .collection-info {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  h2 {
    margin: 0;
    font-size: 20px;
    color: #2c3e50;
    line-height: 1.3;
  }

  .mediacloud-icon-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 999px;
    font-size: 13px;
    color: #3498db;
    border: 1px solid rgba(52, 152, 219, 0.2);
    background-color: #f5fbff;
    text-decoration: none;
    transition: background-color 0.2s, border-color 0.2s, color 0.2s;
  }

  .mediacloud-icon-link:hover {
    background-color: #e3f3ff;
    border-color: rgba(52, 152, 219, 0.5);
    color: #2980b9;
  }

  .status {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    width: fit-content;
  }

  .status-pending {
    background-color: #ecf0f1;
    color: #7f8c8d;
  }

  .status-in_progress {
    background-color: #fff3cd;
    color: #856404;
  }

  .status-completed {
    background-color: #27ae60;
    color: white;
  }

  .stats {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .all-decisions-button {
    margin-top: 8px;
    align-self: stretch;
    width: 100%;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid #3498db;
    background-color: #3498db;
    color: white;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .all-decisions-button:hover {
    background-color: #2980b9;
    border-color: #2980b9;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .stat-label {
    font-size: 12px;
    color: #7f8c8d;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .stat-value {
    font-size: 20px;
    font-weight: 600;
    color: #2c3e50;
  }

  .stat-keep {
    color: #27ae60;
  }

  .stat-remove {
    color: #e74c3c;
  }

  .stat-add {
    color: #3498db;
  }

  .stat-undecided {
    color: #f39c12;
  }
</style>

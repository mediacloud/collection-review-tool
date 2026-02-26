<script>
  export let review;
</script>

<div class="header">
  <div class="top-row">
    <a href="/" class="back-link">← Back to Home</a>
  </div>
  <div class="info">
    <div class="collection-info">
      <h2>{review.collection_name || `Collection #${review.collection_id}`}</h2>
      <a 
        href={`https://search.mediacloud.org/collections/${review.collection_id}`}
        target="_blank"
        rel="noopener noreferrer"
        class="mediacloud-link"
      >
        View in MediaCloud ↗
      </a>
    </div>
    <span class="status status-{review.status}">{review.status}</span>
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
  {/if}
</div>

<style>
  .header {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .top-row {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 8px;
  }

  .back-link {
    font-size: 13px;
    color: #3498db;
    text-decoration: none;
  }

  .back-link:hover {
    text-decoration: underline;
    color: #2980b9;
  }

  .info {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
    flex-wrap: wrap;
  }

  .collection-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  h2 {
    margin: 0;
    font-size: 20px;
    color: #2c3e50;
    line-height: 1.3;
  }

  .mediacloud-link {
    color: #3498db;
    text-decoration: none;
    font-size: 14px;
    transition: color 0.3s;
  }

  .mediacloud-link:hover {
    color: #2980b9;
    text-decoration: underline;
  }

  .status {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
  }

  .status-pending {
    background-color: #ecf0f1;
    color: #7f8c8d;
  }

  .status-in_progress {
    background-color: #3498db;
    color: white;
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

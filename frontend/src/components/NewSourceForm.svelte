<script>
  export let onSubmit;
  export let loading = false;

  let sourceLabel = '';
  let sourceHomepage = '';
  let error = null;

  function handleSubmit() {
    error = null;

    if (!sourceLabel.trim()) {
      error = 'Source label is required';
      return;
    }

    if (!sourceHomepage.trim()) {
      error = 'Source homepage is required';
      return;
    }

    // Basic URL validation
    try {
      new URL(sourceHomepage);
    } catch {
      error = 'Please enter a valid URL';
      return;
    }

    onSubmit(sourceLabel.trim(), sourceHomepage.trim());
    sourceLabel = '';
    sourceHomepage = '';
  }
</script>

<div class="new-source-form">
  <h3>Propose New Source</h3>
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="source-label">Source Label</label>
      <input
        id="source-label"
        type="text"
        bind:value={sourceLabel}
        placeholder="Enter source name"
        disabled={loading}
      />
    </div>

    <div class="form-group">
      <label for="source-homepage">Homepage URL</label>
      <input
        id="source-homepage"
        type="url"
        bind:value={sourceHomepage}
        placeholder="https://example.com"
        disabled={loading}
      />
    </div>

    {#if error}
      <div class="error">{error}</div>
    {/if}

    <button type="submit" disabled={loading}>
      {loading ? 'Adding...' : 'Add Source'}
    </button>
  </form>
</div>

<style>
  .new-source-form {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
  }

  h3 {
    margin-bottom: 20px;
    color: #2c3e50;
    font-size: 18px;
  }

  .form-group {
    margin-bottom: 15px;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #34495e;
    font-size: 14px;
  }

  input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.3s;
  }

  input:focus {
    outline: none;
    border-color: #3498db;
  }

  input:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }

  button {
    width: 100%;
    padding: 12px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  button:hover:not(:disabled) {
    background-color: #2980b9;
  }

  button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }

  .error {
    background-color: #fee;
    color: #c33;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 15px;
    font-size: 14px;
    border: 1px solid #fcc;
  }
</style>

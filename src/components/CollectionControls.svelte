<script lang="ts">
  import type { CollectionSummary } from "../api";

  export let collectionId: string;
  export let loading: boolean;
  export let collection: CollectionSummary | null;
  export let error: string | null;

  export let onLoadCollection: () => void;
</script>

<section class="controls">
  <div class="field-group">
    <label for="collection-id">Collection ID</label>
    <input
      id="collection-id"
      type="number"
      bind:value={collectionId}
      min="1"
      placeholder="Enter Media Cloud collection ID"
    />
    <button type="button" on:click={onLoadCollection} disabled={loading || !collectionId}>
      {#if loading}
        Loading…
      {:else}
        Load collection
      {/if}
    </button>
  </div>

  {#if collection}
    <div class="collection-meta">
      <h2>{collection.label}</h2>
      {#if collection.description}
        <p>{collection.description}</p>
      {/if}
      <p class="collection-id">Collection ID: {collection.tags_id}</p>
    </div>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}
</section>

<style>
  .controls {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e0e0e0;
    background: #fafafa;
  }

  .field-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
  }

  label {
    font-weight: 600;
    margin-right: 0.5rem;
  }

  input {
    padding: 0.4rem 0.6rem;
    border-radius: 4px;
    border: 1px solid #ccc;
    min-width: 10rem;
  }

  button {
    padding: 0.45rem 0.9rem;
    border-radius: 4px;
    border: none;
    background: #0077cc;
    color: #fff;
    cursor: pointer;
    font-weight: 600;
  }

  button[disabled] {
    opacity: 0.6;
    cursor: default;
  }

  .collection-meta h2 {
    margin: 0;
    font-size: 1.1rem;
  }

  .collection-meta p {
    margin: 0.25rem 0;
  }

  .collection-id {
    font-size: 0.85rem;
    color: #666;
  }

  .error {
    color: #b00020;
    font-size: 0.9rem;
  }
</style>


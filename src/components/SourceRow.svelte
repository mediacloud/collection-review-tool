<script lang="ts">
  import type { MediaSource } from "../api";

  export type ReviewAction = "unchanged" | "add" | "remove";

  export interface ReviewDecision {
    media_id: number;
    action: ReviewAction;
    reason: string;
  }

  export let source: MediaSource;
  export let decision: ReviewDecision;

  export let onChange: (updated: ReviewDecision) => void;

  const handleActionChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    onChange({ ...decision, action: target.value as ReviewAction });
  };

  const handleReasonChange = (event: Event) => {
    const target = event.target as HTMLTextAreaElement;
    onChange({ ...decision, reason: target.value });
  };
</script>

<tr class="row">
  <td class="name">
    <div class="primary">
      <span>{source.name}</span>
    </div>
    {#if source.url}
      <div class="secondary">
        <a href={source.url} target="_blank" rel="noreferrer">{source.url}</a>
      </div>
    {/if}
    <div class="meta">
      <span># {source.media_id}</span>
      {#if source.country}
        <span>· {source.country}</span>
      {/if}
      {#if source.language}
        <span>· {source.language}</span>
      {/if}
    </div>
  </td>
  <td class="actions">
    <div class="radio-group">
      <label>
        <input
          type="radio"
          name={`action-${source.media_id}`}
          value="unchanged"
          checked={decision.action === "unchanged"}
          on:change={handleActionChange}
        />
        No change
      </label>
      <label>
        <input
          type="radio"
          name={`action-${source.media_id}`}
          value="add"
          checked={decision.action === "add"}
          on:change={handleActionChange}
        />
        Add
      </label>
      <label>
        <input
          type="radio"
          name={`action-${source.media_id}`}
          value="remove"
          checked={decision.action === "remove"}
          on:change={handleActionChange}
        />
        Remove
      </label>
    </div>

    {#if decision.action === "remove"}
      <textarea
        placeholder="Explain why this source should be removed…"
        rows="2"
        value={decision.reason}
        on:input={handleReasonChange}
      />
    {/if}
  </td>
</tr>

<style>
  .row {
    border-bottom: 1px solid #eee;
  }

  .name {
    padding: 0.75rem 0.75rem 0.75rem 1rem;
    vertical-align: top;
  }

  .primary {
    font-weight: 600;
    margin-bottom: 0.25rem;
  }

  .secondary {
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
  }

  .secondary a {
    color: #0077cc;
    text-decoration: none;
  }

  .secondary a:hover {
    text-decoration: underline;
  }

  .meta {
    font-size: 0.8rem;
    color: #777;
    display: flex;
    gap: 0.4rem;
  }

  .actions {
    padding: 0.75rem;
    width: 260px;
    vertical-align: top;
  }

  .radio-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 0.4rem 0.5rem;
    border-radius: 4px;
    border: 1px solid #ccc;
    font-size: 0.85rem;
    resize: vertical;
  }
</style>


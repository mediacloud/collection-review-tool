<script>
  import { createEventDispatcher } from 'svelte';
  import BaseModal from './BaseModal.svelte';

  export let show = false;
  export let fieldLabel = '';
  export let currentValue = '';
  // Optional array of { value, label } for dropdowns
  export let options = [];
  // Optional read-only info message; when set, no input/select is shown
  export let readonlyMessage = '';

  const dispatch = createEventDispatcher();

  let value = '';

  $: if (show) {
    value = currentValue ?? '';
  }

  function handleSave() {
    dispatch('save', value.trim());
  }

  function handleClose() {
    dispatch('close');
  }
</script>

<BaseModal show={show} onClose={handleClose}>
  <div
    class="modal-content"
    role="dialog"
    aria-modal="true"
    aria-labelledby="edit-metadata-title"
  >
    <h2 id="edit-metadata-title">Edit {fieldLabel}</h2>
    <div class="form-group">
      <label for="edit-field">{fieldLabel}</label>
      {#if readonlyMessage}
        <p class="readonly-message">{readonlyMessage}</p>
      {:else if options && options.length > 0}
        <select id="edit-field" bind:value={value}>
          <option value="">-- Select {fieldLabel.toLowerCase()} --</option>
          {#each options as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      {:else}
        <input
          id="edit-field"
          type="text"
          bind:value={value}
        />
      {/if}
    </div>
    <div class="modal-actions">
      <button type="button" class="btn btn-secondary" on:click={handleClose}>
        Cancel
      </button>
      {#if !readonlyMessage}
        <button type="button" class="btn btn-primary" on:click={handleSave}>
          Save
        </button>
      {/if}
    </div>
  </div>
</BaseModal>

<style>
  .modal-content {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    max-width: 420px;
    width: 100%;
    padding: 24px 24px 20px;
  }

  h2 {
    margin: 0 0 12px;
    font-size: 20px;
    color: #2c3e50;
  }

  .form-group {
    margin-bottom: 16px;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #34495e;
    font-size: 14px;
  }

  input,
  select {
    width: 100%;
    box-sizing: border-box;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.2s;
  }

  input:focus {
    outline: none;
    border-color: #3498db;
  }

  .readonly-message {
    margin: 4px 0 0;
    font-size: 13px;
    color: #7f8c8d;
    line-height: 1.5;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  .btn {
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid transparent;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .btn-secondary {
    background-color: #ecf0f1;
    border-color: #d0d7de;
    color: #2c3e50;
  }

  .btn-secondary:hover {
    background-color: #d0d7de;
  }

  .btn-primary {
    background-color: #3498db;
    border-color: #3498db;
    color: white;
  }

  .btn-primary:hover {
    background-color: #2980b9;
    border-color: #2980b9;
  }
</style>


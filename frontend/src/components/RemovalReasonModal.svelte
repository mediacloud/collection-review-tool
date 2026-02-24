<script>
  import { createEventDispatcher } from 'svelte';
  
  export let show = false;
  export let sourceLabel = '';
  let removalReason = '';
  let error = '';

  const dispatch = createEventDispatcher();

  // Reset form when modal is closed
  $: if (!show) {
    removalReason = '';
    error = '';
  }

  function handleSubmit() {
    if (!removalReason.trim()) {
      error = 'Please provide a reason for removal';
      return;
    }
    error = '';
    handleConfirm();
  }

  function handleCancel() {
    removalReason = '';
    error = '';
    handleClose();
  }

  function handleKeydown(event) {
    if (event.key === 'Escape') {
      handleCancel();
    } else if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      handleSubmit();
    }
  }

  function handleConfirm() {
    dispatch('confirm', removalReason.trim());
    removalReason = '';
    error = '';
  }

  function handleClose() {
    dispatch('close');
  }
</script>

{#if show}
  <div class="modal-overlay" on:click={handleCancel} on:keydown={handleKeydown}>
    <div class="modal-content" on:click|stopPropagation role="dialog" aria-labelledby="modal-title" aria-modal="true">
      <h2 id="modal-title">Removal Reason Required</h2>
      <p class="modal-description">
        Please provide a reason for removing <strong>{sourceLabel || 'this source'}</strong>:
      </p>
      
      <div class="form-group">
        <label for="removal-reason">Removal Reason *</label>
        <textarea
          id="removal-reason"
          bind:value={removalReason}
          placeholder="Enter the reason for removing this source..."
          rows="4"
          class:error={error}
          autofocus
        ></textarea>
        {#if error}
          <div class="error-message">{error}</div>
        {/if}
      </div>

      <div class="modal-actions">
        <button class="btn btn-cancel" on:click={handleCancel} type="button">
          Cancel
        </button>
        <button class="btn btn-confirm" on:click={handleSubmit} type="button">
          Confirm Removal
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 20px;
  }

  .modal-content {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 100%;
    padding: 30px;
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      transform: translateY(-20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  h2 {
    font-size: 24px;
    margin-bottom: 10px;
    color: #2c3e50;
  }

  .modal-description {
    color: #7f8c8d;
    margin-bottom: 20px;
    line-height: 1.6;
  }

  .modal-description strong {
    color: #2c3e50;
  }

  .form-group {
    margin-bottom: 20px;
  }

  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #34495e;
  }

  textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    transition: border-color 0.3s;
  }

  textarea:focus {
    outline: none;
    border-color: #3498db;
  }

  textarea.error {
    border-color: #e74c3c;
  }

  .error-message {
    color: #e74c3c;
    font-size: 14px;
    margin-top: 5px;
  }

  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s;
  }

  .btn-cancel {
    background-color: #ecf0f1;
    color: #2c3e50;
  }

  .btn-cancel:hover {
    background-color: #bdc3c7;
  }

  .btn-confirm {
    background-color: #e74c3c;
    color: white;
  }

  .btn-confirm:hover {
    background-color: #c0392b;
  }
</style>

<script>
  import { createEventDispatcher } from 'svelte';
  import BaseModal from './BaseModal.svelte';

  export let show = false;
  export let sourceLabel = '';

  let skipNote = '';
  const dispatch = createEventDispatcher();

  $: if (!show) {
    skipNote = '';
  }

  function handleCancel() {
    skipNote = '';
    dispatch('close');
  }

  function handleConfirm() {
    dispatch('confirm', skipNote.trim());
    skipNote = '';
  }

  function handleKeydown(event) {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      handleConfirm();
    }
  }
</script>

<BaseModal show={show} onClose={handleCancel}>
  <div
    class="modal-content"
    role="dialog"
    aria-labelledby="skip-modal-title"
    aria-modal="true"
    on:keydown={handleKeydown}
  >
    <h2 id="skip-modal-title">Skip for now</h2>
    <p class="modal-description">
      Optionally add a note for coordinators about <strong>{sourceLabel || 'this source'}</strong>. Notes appear in the
      skipped queue and in the audit CSV.
    </p>

    <div class="form-group">
      <label for="skip-note">Note (optional)</label>
      <textarea
        id="skip-note"
        bind:value={skipNote}
        placeholder="e.g. needs verification, duplicate concern, wrong language…"
        rows="4"
      ></textarea>
    </div>

    <div class="modal-actions">
      <button class="btn btn-cancel" type="button" on:click={handleCancel}>Cancel</button>
      <button class="btn btn-confirm" type="button" on:click={handleConfirm}>Skip</button>
    </div>
  </div>
</BaseModal>

<style>
  .modal-content {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 100%;
    padding: 22px 24px 20px;
  }

  h2 {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #2c3e50;
  }

  .modal-description {
    margin: 0 0 16px 0;
    font-size: 14px;
    line-height: 1.45;
    color: #5a6c7d;
  }

  .form-group {
    margin-bottom: 18px;
  }

  .form-group label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #34495e;
    margin-bottom: 6px;
  }

  textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 10px 12px;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    min-height: 88px;
  }

  textarea:focus {
    outline: 2px solid #3498db;
    outline-offset: 1px;
    border-color: #3498db;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .btn {
    padding: 10px 16px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid transparent;
    font-family: inherit;
  }

  .btn-cancel {
    background: #f6f8fa;
    color: #34495e;
    border-color: #d0d7de;
  }

  .btn-cancel:hover {
    background: #eef1f4;
  }

  .btn-confirm {
    background: #95a5a6;
    color: white;
    border-color: #95a5a6;
  }

  .btn-confirm:hover {
    background: #7f8c8d;
    border-color: #7f8c8d;
  }
</style>

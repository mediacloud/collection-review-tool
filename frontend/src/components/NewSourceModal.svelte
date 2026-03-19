<script>
  import { createEventDispatcher } from 'svelte';
  import iso3166 from 'iso-3166-2';
  import * as rawIso3166 from 'iso-3166';

  export let show = false;
  export let loading = false;
  export let editMetadata = false;
  export let languageOptions = [];
  export let countryOptions = [];
  export let errorMessage = null;

  let sourceLabel = '';
  let sourceHomepage = '';
  let error = null;

  let primaryLanguage = '';
  let pubCountry = '';
  let pubState = '';
  let pubStateOptions = [];

  const dispatch = createEventDispatcher();

  // Reset form when modal is closed
  $: if (!show) {
    sourceLabel = '';
    sourceHomepage = '';
    error = null;
    primaryLanguage = '';
    pubCountry = '';
    pubState = '';
    pubStateOptions = [];
  }

  $: if (show && editMetadata) {
    // Update pub_state options whenever pub_country changes.
    const alpha2Country =
      pubCountry && pubCountry.length === 3
        ? rawIso3166.iso31661Alpha3ToAlpha2[pubCountry] || pubCountry
        : pubCountry;

    if (alpha2Country && iso3166.data[alpha2Country] && iso3166.data[alpha2Country].sub) {
      pubStateOptions = Object.keys(iso3166.data[alpha2Country].sub)
        .sort()
        .map((code) => {
          const sub = iso3166.data[alpha2Country].sub[code];
          return { value: code, label: `${code} – ${sub.name}` };
        });
    } else {
      pubStateOptions = [];
    }

    // If pub_state is no longer valid, clear it.
    if (pubState && !pubStateOptions.find((o) => o.value === pubState)) {
      pubState = '';
    }
  }

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

    try {
      new URL(sourceHomepage);
    } catch {
      error = 'Please enter a valid URL';
      return;
    }

    if (editMetadata) {
      if (!primaryLanguage) {
        error = 'Language is required when metadata editing is enabled';
        return;
      }
      if (!pubCountry) {
        error = 'Pub country is required when metadata editing is enabled';
        return;
      }
      if (!pubState) {
        error = 'Pub state is required when metadata editing is enabled';
        return;
      }
    }

    dispatch('confirm', {
      label: sourceLabel.trim(),
      homepage: sourceHomepage.trim(),
      primary_language: editMetadata ? primaryLanguage : null,
      pub_country: editMetadata ? pubCountry : null,
      pub_state: editMetadata ? pubState : null,
    });
  }

  function handleClose() {
    dispatch('close');
  }
</script>

{#if show}
  <div class="modal-overlay" on:click={handleClose}>
    <div
      class="modal-content"
      on:click|stopPropagation
      role="dialog"
      aria-labelledby="new-source-title"
      aria-modal="true"
    >
      <h2 id="new-source-title">Propose New Source</h2>
      <p class="modal-description">
        Add a new source to this review by providing a label and homepage URL.
      </p>

      <form on:submit|preventDefault={handleSubmit}>
        <div class="form-group">
          <label for="source-label">Source Label *</label>
          <input
            id="source-label"
            type="text"
            bind:value={sourceLabel}
            placeholder="Enter source name"
            disabled={loading}
            autofocus
          />
        </div>

        <div class="form-group">
          <label for="source-homepage">Homepage URL *</label>
          <input
            id="source-homepage"
            type="url"
            bind:value={sourceHomepage}
            placeholder="https://example.com"
            disabled={loading}
          />
        </div>

        {#if editMetadata}
          <div class="metadata-section">
            <h3>Source Metadata</h3>

            <div class="form-group">
              <label for="primary-language">Primary language *</label>
              <select
                id="primary-language"
                bind:value={primaryLanguage}
                disabled={loading}
              >
                <option value="">Select language...</option>
                {#each languageOptions as opt}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            </div>

            <div class="form-group">
              <label for="pub-country">Pub country (ISO 3166-1 alpha-3) *</label>
              <select
                id="pub-country"
                bind:value={pubCountry}
                disabled={loading}
              >
                <option value="">Select country...</option>
                {#each countryOptions as opt}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            </div>

            <div class="form-group">
              <label for="pub-state">Pub state (ISO 3166-2) *</label>
              <select
                id="pub-state"
                bind:value={pubState}
                disabled={loading || !pubStateOptions || pubStateOptions.length === 0}
              >
                <option value="">Select state...</option>
                {#each pubStateOptions as opt}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            </div>
          </div>
        {/if}

        {#if error}
          <div class="error-message">{error}</div>
        {/if}

        {#if errorMessage && !error}
          <div class="error-message">{errorMessage}</div>
        {/if}

        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-secondary"
            on:click={handleClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Adding...' : 'Add Source'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  .metadata-section {
    border: 1px solid #e0e4e8;
    border-radius: 8px;
    padding: 14px 14px;
    background: #f8f9fa;
    margin-bottom: 14px;
  }

  .metadata-section h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 900;
    color: #2c3e50;
  }

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
    max-width: 520px;
    width: 100%;
    padding: 28px 32px;
  }

  h2 {
    font-size: 22px;
    margin: 0 0 8px;
    color: #2c3e50;
  }

  .modal-description {
    color: #7f8c8d;
    margin-bottom: 18px;
    line-height: 1.5;
    font-size: 14px;
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

  input {
    width: 100%;
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

  input:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }

  select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.2s;
    background: white;
  }

  select:focus {
    outline: none;
    border-color: #3498db;
  }

  select:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }

  .error-message {
    background-color: #fee;
    color: #c33;
    padding: 10px 12px;
    border-radius: 4px;
    border: 1px solid #fcc;
    font-size: 13px;
    margin-top: 4px;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 4px;
  }

  .btn {
    padding: 10px 18px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s, opacity 0.2s;
  }

  .btn-primary {
    background-color: #3498db;
    color: white;
  }

  .btn-primary:hover:enabled {
    background-color: #2980b9;
  }

  .btn-secondary {
    background-color: #ecf0f1;
    color: #2c3e50;
  }

  .btn-secondary:hover:enabled {
    background-color: #bdc3c7;
  }

  .btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
</style>


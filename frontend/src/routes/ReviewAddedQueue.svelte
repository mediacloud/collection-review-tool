<script>
  import { onMount } from 'svelte';

  import iso3166 from 'iso-3166-2';
  import * as rawIso3166 from 'iso-3166';
  import EditMetadataModal from '../components/EditMetadataModal.svelte';
  import {
    getReviewProject,
    getAddedItemsByProjectGuid,
    updateQueueItemSourceMetadata,
  } from '../lib/api.js';

  let projectGuid = null;
  let project = null;

  let loading = false;
  let error = null;

  let items = [];
  let total = 0;
  let currentItem = null;

  let showEditMetadataModal = false;
  let showEditMetadataError = null;
  let editFieldKey = null;
  let editFieldLabel = '';
  let editFieldCurrentValue = '';
  let editFieldOptions = [];
  let editFieldReadonlyMessage = '';

  const LANGUAGE_OPTIONS = [
    { value: 'en', label: 'en – English' },
    { value: 'es', label: 'es – Spanish' },
    { value: 'fr', label: 'fr – French' },
    { value: 'de', label: 'de – German' },
    { value: 'pt', label: 'pt – Portuguese' },
    { value: 'ru', label: 'ru – Russian' },
    { value: 'ar', label: 'ar – Arabic' },
    { value: 'zh', label: 'zh – Chinese' },
    { value: 'hi', label: 'hi – Hindi' },
    { value: 'bn', label: 'bn – Bengali' },
    { value: 'id', label: 'id – Indonesian' },
    { value: 'tr', label: 'tr – Turkish' },
    { value: 'vi', label: 'vi – Vietnamese' },
    { value: 'sw', label: 'sw – Swahili' },
    { value: 'fa', label: 'fa – Persian' },
  ];

  const COUNTRY_OPTIONS = Object.keys(iso3166.data)
    .sort()
    .map((code2) => {
      const alpha3 = rawIso3166.iso31661Alpha2ToAlpha3[code2] || code2;
      return {
        value: alpha3,
        label: `${alpha3} – ${iso3166.data[code2].name}`,
      };
    });

  function parseProjectGuidFromUrl() {
    const match = window.location.pathname.match(
      /^\/review-projects\/([0-9a-fA-F-]+)\/added$/
    );
    return match ? match[1] : null;
  }

  function goBack() {
    if (!projectGuid) return;
    window.navigate(`/review-projects/${projectGuid}`);
  }

  async function loadAdded() {
    if (!projectGuid) return;
    loading = true;
    error = null;
    try {
      const [projectResp, addedResp] = await Promise.all([
        getReviewProject(projectGuid),
        getAddedItemsByProjectGuid(projectGuid, {
          page: 1,
          page_size: 1000,
          dedupe_source_id: true,
        }),
      ]);

      project = projectResp.project;

      items = addedResp.items || [];
      total = addedResp.total || 0;
      currentItem = items.length > 0 ? items[0] : null;
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load added sources';
      console.error('Error loading added sources:', err);
      items = [];
      total = 0;
      currentItem = null;
    } finally {
      loading = false;
    }
  }

  function openEditMetadata(
    fieldKey,
    label,
    currentValue,
    options = [],
    readonlyMsg = ''
  ) {
    // Ensure the modal edits the selected row.
    // (caller typically sets `currentItem` just before calling this)
    editFieldKey = fieldKey;
    editFieldLabel = label;
    editFieldCurrentValue = currentValue || '';
    editFieldOptions = options;
    editFieldReadonlyMessage = readonlyMsg;
    showEditMetadataModal = true;
    showEditMetadataError = null;
  }

  function closeEditMetadata() {
    showEditMetadataModal = false;
    editFieldKey = null;
    editFieldLabel = '';
    editFieldCurrentValue = '';
    editFieldOptions = [];
    editFieldReadonlyMessage = '';
    showEditMetadataError = null;
  }

  async function handleEditMetadataSave(event) {
    const newValue = event.detail;
    showEditMetadataError = null;

    if (!currentItem || !editFieldKey) return;

    // If editing pub_state and we have a country code, validate ISO 3166-2.
    if (editFieldKey === 'pub_state' && currentItem.source_metadata?.pub_country && newValue) {
      const storedCountry = currentItem.source_metadata.pub_country;
      const alpha2Country =
        storedCountry.length === 3
          ? rawIso3166.iso31661Alpha3ToAlpha2[storedCountry] || storedCountry
          : storedCountry;

      const subdivision = iso3166.subdivision(newValue);
      if (!subdivision) {
        showEditMetadataError = `Invalid subdivision code "${newValue}" for country ${storedCountry} (expected ISO 3166-2).`;
        return;
      }
      if (!newValue.startsWith(`${alpha2Country}-`)) {
        showEditMetadataError = `Subdivision code "${newValue}" does not match country ${storedCountry}.`;
        return;
      }
    }

    try {
      const payload = { [editFieldKey]: newValue };
      const resp = await updateQueueItemSourceMetadata(
        currentItem.queue_guid,
        currentItem.id,
        payload
      );

      const updated = resp.item;
      const merged = {
        ...updated,
        queue_guid: currentItem.queue_guid,
        queue_index: currentItem.queue_index,
      };

      items = items.map((i) => (i.id === merged.id && i.queue_guid === merged.queue_guid ? merged : i));
      currentItem = merged;

      closeEditMetadata();
    } catch (err) {
      showEditMetadataError =
        err.response?.data?.error || err.message || 'Failed to update source metadata';
      console.error('Error updating metadata:', err);
    }
  }

  onMount(() => {
    projectGuid = parseProjectGuidFromUrl();
    loadAdded();
  });
</script>

<div class="container">
  <div class="header-bar">
    <div class="header-left">
      <button type="button" class="back-home" on:click={goBack}>↩</button>
      <div class="title">ReviewProject: {project?.name || projectGuid}</div>
    </div>
  </div>

  <div class="subheader">Added Sources</div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if loading && items.length === 0}
    <div class="loading">Loading added sources...</div>
  {:else if items.length === 0}
    <div class="empty-card">
      <div class="empty-title">No added sources</div>
      <div class="empty-subtitle">There are no sources marked as <strong>add</strong> in this project.</div>
    </div>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Source Label</th>
            <th>Homepage</th>
            <th>Language</th>
            <th>Pub country</th>
            <th>Pub state</th>
            {#if project?.edit_metadata}
              <th>Metadata</th>
            {/if}
          </tr>
        </thead>
        <tbody>
          {#each items as item (item.id)}
            <tr>
              <td class="td-label">{item.source_label || 'N/A'}</td>
              <td>
                {#if item.source_homepage}
                  <a href={item.source_homepage} target="_blank" rel="noopener noreferrer">
                    {item.source_homepage}
                  </a>
                {:else}
                  —
                {/if}
              </td>
              <td>{item.source_metadata?.primary_language || item.source_metadata?.language || '—'}</td>
              <td>{item.source_metadata?.pub_country || '—'}</td>
              <td>{item.source_metadata?.pub_state || '—'}</td>
              {#if project?.edit_metadata}
                <td class="td-actions">
                  <div class="metadata-actions-row">
                    <button
                      type="button"
                      class="btn-inline"
                      on:click={() => {
                        currentItem = item;
                        openEditMetadata(
                          'primary_language',
                          'Language (ISO 639-1)',
                          item.source_metadata?.primary_language || item.source_metadata?.language,
                          LANGUAGE_OPTIONS
                        );
                      }}
                    >
                      Edit Language
                    </button>
                    <button
                      type="button"
                      class="btn-inline"
                      on:click={() => {
                        currentItem = item;
                        const options = [{ value: '', label: 'None / Not set' }, ...COUNTRY_OPTIONS];
                        openEditMetadata(
                          'pub_country',
                          'Pub country (ISO 3166-1 alpha-3)',
                          item.source_metadata?.pub_country,
                          options
                        );
                      }}
                    >
                      Edit Country
                    </button>
                    <button
                      type="button"
                      class="btn-inline"
                      on:click={() => {
                        currentItem = item;
                        const storedCountry = item.source_metadata?.pub_country;
                        if (!storedCountry) {
                          openEditMetadata(
                            'pub_state',
                            'Pub state (ISO 3166-2)',
                            item.source_metadata?.pub_state,
                            [],
                            'Pub state depends on a Pub country value. Please set Pub country first.'
                          );
                          return;
                        }

                        const alpha2Country =
                          storedCountry.length === 3
                            ? rawIso3166.iso31661Alpha3ToAlpha2[storedCountry] || storedCountry
                            : storedCountry;

                        let options = [];
                        if (iso3166.data[alpha2Country] && iso3166.data[alpha2Country].sub) {
                          options = Object.keys(iso3166.data[alpha2Country].sub)
                            .sort()
                            .map((code) => {
                              const sub = iso3166.data[alpha2Country].sub[code];
                              return { value: code, label: `${code} – ${sub.name}` };
                            });
                          options = [{ value: '', label: 'None / Not set' }, ...options];
                        }

                        openEditMetadata(
                          'pub_state',
                          `Pub state (ISO 3166-2 for ${storedCountry})`,
                          item.source_metadata?.pub_state,
                          options
                        );
                      }}
                    >
                      Edit State
                    </button>
                  </div>
                </td>
              {/if}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  {#if showEditMetadataError}
    <div class="error-banner meta-error">{showEditMetadataError}</div>
  {/if}

  <EditMetadataModal
    show={showEditMetadataModal}
    fieldLabel={editFieldLabel}
    currentValue={editFieldCurrentValue}
    options={editFieldOptions}
    readonlyMessage={editFieldReadonlyMessage}
    on:save={handleEditMetadataSave}
    on:close={closeEditMetadata}
  />
</div>

<style>
  .container {
    margin: 0 auto;
    padding: 20px;
    padding-top: 72px;
    max-width: 80%;
  }

  .header-bar {
    position: fixed;
    top: 0;
    inset-inline: 0;
    background: #414a55;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
    z-index: 900;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 10px 20px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    color: white;
    min-width: 0;
  }

  .top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 14px;
  }

  .back-home {
    padding: 4px 8px;
    border: none;
    background: transparent;
    color: #f6f8fa;
    cursor: pointer;
    font-size: 16px;
    font-weight: 400;
  }

  .back-home:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
  }

  .title {
    font-weight: 700;
    color: #f6f8fa;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .subheader {
    margin: 0 0 20px;
    font-size: 20px;
    font-weight: 900;
    color: #2c3e50;
  }

  .count {
    font-size: 13px;
    color: #7f8c8d;
    font-weight: 800;
  }

  .loading {
    text-align: center;
    padding: 40px 0;
    color: #7f8c8d;
    font-size: 18px;
  }

  .error-banner {
    background: #fee;
    color: #c33;
    padding: 12px 14px;
    border-radius: 8px;
    border: 1px solid #fcc;
    margin-bottom: 16px;
    text-align: center;
  }

  .meta-error {
    margin-top: -6px;
  }

  .empty-card {
    background: white;
    border: 1px solid #d0d7de;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    padding: 18px 18px;
  }

  .empty-title {
    font-size: 16px;
    font-weight: 900;
    color: #2c3e50;
    margin-bottom: 6px;
  }

  .empty-subtitle {
    color: #7f8c8d;
    font-size: 13px;
    line-height: 1.35;
  }

  .table-wrapper {
    margin-top: 12px;
    overflow: auto;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    background: white;
    max-height: 640px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  thead {
    background-color: #f8f9fa;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  th {
    padding: 10px 10px;
    text-align: left;
    font-weight: 700;
    color: #2c3e50;
    border-bottom: 2px solid #dee2e6;
    white-space: nowrap;
  }

  td {
    padding: 10px 10px;
    border-bottom: 1px solid #dee2e6;
    vertical-align: top;
  }

  td a {
    color: #3498db;
    text-decoration: none;
  }

  td a:hover {
    text-decoration: underline;
  }

  .td-label {
    max-width: 260px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .td-actions {
    white-space: nowrap;
  }

  .metadata-actions-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
  }

  .btn-inline {
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background: #fff;
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    color: #34495e;
  }

  .btn-inline:hover:not(:disabled) {
    background-color: #f6f8fa;
  }

  .btn-inline:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>


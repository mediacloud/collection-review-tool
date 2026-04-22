<script>
  import { onMount } from 'svelte';
  import iso3166 from 'iso-3166-2';
  import * as rawIso3166 from 'iso-3166';
  import SourceViewer from '../components/SourceViewer.svelte';
  import BaseModal from '../components/BaseModal.svelte';
  import RemovalReasonModal from '../components/RemovalReasonModal.svelte';
  import SkipNoteModal from '../components/SkipNoteModal.svelte';
  import EditMetadataModal from '../components/EditMetadataModal.svelte';
  import {
    getReviewProject,
    getKeptItemsByProjectGuid,
    decideQueueItem,
    updateQueueItemSourceMetadata,
  } from '../lib/api.js';

  let projectGuid = null;
  let project = null;

  let loading = false;
  let error = null;
  let actionError = null;
  let decidingItem = false;
  let showEditMetadataModal = false;
  let editFieldKey = null;
  let editFieldLabel = '';
  let editFieldCurrentValue = '';
  let editFieldOptions = [];
  let editFieldReadonlyMessage = '';

  let items = [];
  let total = 0;
  let selectedItem = null;
  let selectedItemCursor = -1;
  let showEditItemModal = false;
  let showRemovalModal = false;
  let showSkipNoteModal = false;

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
      /^\/review-projects\/([0-9a-fA-F-]+)\/kept$/
    );
    return match ? match[1] : null;
  }

  function goBack() {
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    if (!projectGuid) return;
    window.navigate(`/review-projects/${projectGuid}`);
  }

  async function loadKept() {
    if (!projectGuid) return;
    loading = true;
    error = null;
    actionError = null;
    try {
      const [projectResp, keptResp] = await Promise.all([
        getReviewProject(projectGuid),
        getKeptItemsByProjectGuid(projectGuid, {
          page: 1,
          page_size: 1000,
          dedupe_source_id: true,
        }),
      ]);

      project = projectResp.project;
      items = keptResp.items || [];
      total = keptResp.total || 0;
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load kept sources';
      console.error('Error loading kept sources:', err);
      items = [];
      total = 0;
    } finally {
      loading = false;
    }
  }

  function openItemEditor(item) {
    if (!item || decidingItem) return;
    selectedItemCursor = items.findIndex(
      (candidate) => candidate.id === item.id && candidate.queue_guid === item.queue_guid
    );
    selectedItem = item;
    showEditItemModal = true;
    showRemovalModal = false;
    showSkipNoteModal = false;
    actionError = null;
  }

  function closeItemEditor() {
    showEditItemModal = false;
    selectedItem = null;
    selectedItemCursor = -1;
    showRemovalModal = false;
    showSkipNoteModal = false;
    closeEditMetadata();
  }

  function goToNeighborItem(direction) {
    if (!showEditItemModal || decidingItem || items.length <= 1) return;
    const current = selectedItemCursor >= 0 ? selectedItemCursor : 0;
    const next = (current + direction + items.length) % items.length;
    selectedItemCursor = next;
    selectedItem = items[next];
    showRemovalModal = false;
    showSkipNoteModal = false;
    actionError = null;
  }

  async function decideSelectedItem(decision, removalReason = null, skipNote = null) {
    if (!selectedItem || decidingItem) return;
    const previousSelected = selectedItem;
    const previousCursor = selectedItemCursor >= 0 ? selectedItemCursor : 0;
    decidingItem = true;
    actionError = null;
    try {
      await decideQueueItem(
        selectedItem.queue_guid,
        selectedItem.id,
        decision,
        removalReason,
        skipNote
      );
      await loadKept();
      if (items.length === 0) {
        closeItemEditor();
        return;
      }

      const persistedIndex = items.findIndex(
        (candidate) =>
          candidate.id === previousSelected.id &&
          candidate.queue_guid === previousSelected.queue_guid
      );
      const nextCursor =
        persistedIndex >= 0
          ? (persistedIndex + 1) % items.length
          : Math.min(previousCursor, items.length - 1);
      selectedItemCursor = nextCursor;
      selectedItem = items[nextCursor];
      showRemovalModal = false;
      showSkipNoteModal = false;
    } catch (err) {
      actionError = err.response?.data?.error || err.message || 'Failed to update decision';
      console.error('Error updating kept-item decision:', err);
    } finally {
      decidingItem = false;
    }
  }

  function handleEditItemKeep() {
    decideSelectedItem('keep');
  }

  function handleEditItemRemove() {
    if (!selectedItem || decidingItem) return;
    showRemovalModal = true;
  }

  function handleEditItemSkip() {
    if (!selectedItem || decidingItem) return;
    showSkipNoteModal = true;
  }

  function openEditMetadata(fieldKey, label, currentValue, options = [], readonlyMsg = '') {
    editFieldKey = fieldKey;
    editFieldLabel = label;
    editFieldCurrentValue = currentValue || '';
    editFieldOptions = options;
    editFieldReadonlyMessage = readonlyMsg;
    showEditMetadataModal = true;
  }

  function closeEditMetadata() {
    showEditMetadataModal = false;
    editFieldKey = null;
    editFieldLabel = '';
    editFieldCurrentValue = '';
    editFieldOptions = [];
    editFieldReadonlyMessage = '';
  }

  async function handleEditMetadataSave(event) {
    const newValue = event.detail;
    if (!selectedItem || !editFieldKey) {
      closeEditMetadata();
      return;
    }

    if (editFieldKey === 'pub_state' && selectedItem.source_metadata?.pub_country && newValue) {
      const storedCountry = selectedItem.source_metadata.pub_country;
      const alpha2Country =
        storedCountry.length === 3
          ? rawIso3166.iso31661Alpha3ToAlpha2[storedCountry] || storedCountry
          : storedCountry;
      const subdivision = iso3166.subdivision(newValue);
      if (!subdivision) {
        actionError = `Invalid subdivision code "${newValue}" for country ${storedCountry} (expected ISO 3166-2).`;
        return;
      }
      if (!newValue.startsWith(`${alpha2Country}-`)) {
        actionError = `Subdivision code "${newValue}" does not match country ${storedCountry}.`;
        return;
      }
    }

    try {
      actionError = null;
      const response = await updateQueueItemSourceMetadata(selectedItem.queue_guid, selectedItem.id, {
        [editFieldKey]: newValue,
      });
      const updated = response?.item;
      if (updated) {
        const merged = {
          ...updated,
          queue_guid: selectedItem.queue_guid,
          queue_index: selectedItem.queue_index,
        };
        selectedItem = merged;
        items = items.map((item) =>
          item.id === merged.id && item.queue_guid === merged.queue_guid ? merged : item
        );
      }
      closeEditMetadata();
    } catch (err) {
      actionError = err.response?.data?.error || err.message || 'Failed to update source metadata';
    }
  }

  onMount(() => {
    projectGuid = parseProjectGuidFromUrl();
    loadKept();
  });
</script>

<div class="container">
  <div class="header-bar">
    <div class="header-left">
      <button type="button" class="back-home" on:click={goBack}>↩</button>
      <div class="title">ReviewProject: {project?.name || projectGuid}</div>
    </div>
  </div>

  <div class="subheader">Kept Sources ({total})</div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}
  {#if actionError}
    <div class="error-banner">{actionError}</div>
  {/if}

  {#if loading && items.length === 0}
    <div class="loading">Loading kept sources...</div>
  {:else if items.length === 0}
    <div class="empty-card">
      <div class="empty-title">No kept sources</div>
      <div class="empty-subtitle">
        There are no sources currently marked as <strong>keep</strong> in this project.
      </div>
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
            <th>MediaCloud</th>
            <th>Decision</th>
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
              <td>
                {#if !item.is_new_source && item.source_id}
                  <a
                    href={`https://search.mediacloud.org/sources/${item.source_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View ↗
                  </a>
                {:else}
                  —
                {/if}
              </td>
              <td>
                <button
                  type="button"
                  class="btn-inline"
                  on:click={() => openItemEditor(item)}
                  disabled={loading || decidingItem}
                >
                  Edit
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  <BaseModal show={showEditItemModal} onClose={closeItemEditor}>
    <div class="item-edit-modal-wrap">
      <div class="item-nav-row">
        <button
          type="button"
          class="item-nav-button"
          on:click={() => goToNeighborItem(-1)}
          disabled={decidingItem || items.length <= 1}
          aria-label="Previous source"
        >
          ←
        </button>
        <button
          type="button"
          class="item-nav-button"
          on:click={() => goToNeighborItem(1)}
          disabled={decidingItem || items.length <= 1}
          aria-label="Next source"
        >
          →
        </button>
      </div>
      {#if selectedItem}
        <SourceViewer
          item={selectedItem}
          onKeep={handleEditItemKeep}
          onRemove={handleEditItemRemove}
          onSkip={handleEditItemSkip}
          showSkip={true}
          editMetadata={!!project?.edit_metadata}
          onEditLanguage={() =>
            openEditMetadata(
              'primary_language',
              'Language (ISO 639-1)',
              selectedItem?.source_metadata?.primary_language || selectedItem?.source_metadata?.language,
              LANGUAGE_OPTIONS
            )
          }
          onEditPubCountry={() => {
            const options = [{ value: '', label: 'None / Not set' }, ...COUNTRY_OPTIONS];
            openEditMetadata(
              'pub_country',
              'Pub country (ISO 3166-1 alpha-3)',
              selectedItem?.source_metadata?.pub_country,
              options
            );
          }}
          onEditPubState={() => {
            const storedCountry = selectedItem?.source_metadata?.pub_country;
            if (!storedCountry) {
              openEditMetadata(
                'pub_state',
                'Pub state (ISO 3166-2)',
                selectedItem?.source_metadata?.pub_state,
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
              selectedItem?.source_metadata?.pub_state,
              options
            );
          }}
          loading={decidingItem}
        />
      {/if}
    </div>
  </BaseModal>

  <EditMetadataModal
    show={showEditMetadataModal}
    fieldLabel={editFieldLabel}
    currentValue={editFieldCurrentValue}
    options={editFieldOptions}
    readonlyMessage={editFieldReadonlyMessage}
    on:save={handleEditMetadataSave}
    on:close={closeEditMetadata}
  />

  <RemovalReasonModal
    show={showRemovalModal}
    sourceLabel={selectedItem?.source_label}
    on:confirm={(e) => {
      showRemovalModal = false;
      decideSelectedItem('remove', e.detail, null);
    }}
    on:close={() => (showRemovalModal = false)}
  />

  <SkipNoteModal
    show={showSkipNoteModal}
    sourceLabel={selectedItem?.source_label}
    on:confirm={(e) => {
      showSkipNoteModal = false;
      decideSelectedItem('skip', null, e.detail);
    }}
    on:close={() => (showSkipNoteModal = false)}
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
    max-height: 700px;
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

  .item-edit-modal-wrap {
    width: min(1120px, 96vw);
    max-height: calc(100vh - 120px);
    overflow: auto;
    padding: 8px;
  }

  .item-nav-row {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin: 0 0 8px 0;
  }

  .item-nav-button {
    width: 34px;
    height: 34px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background: #fff;
    color: #34495e;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
  }

  .item-nav-button:hover:not(:disabled) {
    background: #f6f8fa;
  }

  .item-nav-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>

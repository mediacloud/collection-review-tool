<script>
  import {
    getReviewProjectExportUrl,
    getReviewProjectAuditExportUrl,
  } from '../lib/api.js';

  /** @type {string} */
  export let projectGuid = '';
  export let canDownloadMainCsv = false;
  export let canDownloadAuditCsv = false;
  export let onDecisionsPreview = () => {};
  export let onPublish = async () => ({});
  export let onPreviewPublish = async () => ({});
  export let projectName = '';
  export let existingPublishCollection = null;
  export let mediacloudCollectionUrl = () => '#';
  export let mediacloudSourceUrl = () => '#';
  export let publishEnabled = true;
  export let publishMetadataUpdatesEnabled = true;
  export let publishTargetApiBaseUrl = 'https://search.mediacloud.org/api/';

  let exportPanelExpanded = false;
  let apiToken = '';
  let collectionName = '';
  let applyMetadataUpdates = false;
  let publishLoading = false;
  let publishError = null;
  let publishResult = null;
  let showPublishPreviewModal = false;
  let publishPreviewRows = [];
  let publishPreviewSummary = null;
  let preflight = null;
  let previewLoading = false;
  let previewError = null;
  $: publishDefaultName = `${(projectName || 'Review Project').trim() || 'Review Project'} | Collection-Review`;
  $: publishTargetLabel = existingPublishCollection ? `Collection ${existingPublishCollection}` : 'a new collection';
  $: previewHasRows = (publishPreviewRows || []).length > 0;
  $: previewTargetCollectionId = publishResult?.collection_id || existingPublishCollection;

  function invalidatePublishPreview() {
    showPublishPreviewModal = false;
    publishPreviewRows = [];
    publishPreviewSummary = null;
    preflight = null;
    previewError = null;
  }

  function handleMetadataCheckboxChange() {
    invalidatePublishPreview();
  }

  async function handleOpenPublishPreview() {
    publishError = null;
    previewError = null;
    publishPreviewRows = [];
    publishPreviewSummary = null;
    preflight = null;
    const trimmedToken = String(apiToken || '').trim();
    if (!trimmedToken) {
      publishError = 'API token is required';
      return;
    }

    previewLoading = true;
    try {
      const payload = {
        api_token: trimmedToken,
        apply_metadata_updates_to_existing_sources: !!(
          applyMetadataUpdates && publishMetadataUpdatesEnabled
        ),
      };
      const nameToUse = String(collectionName || '').trim();
      if (nameToUse) payload.collection_name = nameToUse;
      const previewData = await onPreviewPublish(payload);
      preflight = previewData?.preflight || null;
      publishPreviewRows = previewData?.preview?.rows || [];
      publishPreviewSummary = previewData?.preview?.summary || null;
      showPublishPreviewModal = true;
    } catch (err) {
      previewError = err?.response?.data?.error || err?.message || 'Failed to generate publish preview';
    } finally {
      previewLoading = false;
    }
  }

  async function handleConfirmPublish() {
    publishError = null;
    publishResult = null;
    const trimmedToken = String(apiToken || '').trim();
    if (!trimmedToken) {
      publishError = 'API token is required';
      return;
    }
    publishLoading = true;
    try {
      const payload = {
        api_token: trimmedToken,
        apply_metadata_updates_to_existing_sources: !!(
          applyMetadataUpdates && publishMetadataUpdatesEnabled
        ),
      };
      const nameToUse = String(collectionName || '').trim();
      if (nameToUse) payload.collection_name = nameToUse;
      const result = await onPublish(payload);
      publishResult = result || null;
      apiToken = '';
      showPublishPreviewModal = false;
    } catch (err) {
      publishError = err?.response?.data?.error || err?.message || 'Failed to publish project';
    } finally {
      publishLoading = false;
    }
  }

  const MAIN_CSV_DISABLED_TITLE =
    'Available after at least one source is marked keep or add in a reviewer queue. That file lists only those rows for Media Cloud.';
  const AUDIT_DISABLED_TITLE = 'Create reviewer queues and assign sources before exporting or previewing.';

  /** @param {string} operation */
  function operationPrimaryLabel(operation) {
    switch (operation) {
      case 'ensure_association':
        return 'Ensure in collection';
      case 'create_source_and_associate':
        return 'Create source';
      case 'remove_association':
        return 'Remove from collection';
      default:
        return operation || '—';
    }
  }

  /** @param {Record<string, unknown>} row */
  function rowWillPatchMetadata(row) {
    return !!(row.metadata_update && Object.keys(row.metadata_update).length > 0);
  }

  /** @param {Record<string, unknown>} row */
  function rowHasMetadataOnCreate(row) {
    return !!(row.metadata_on_create && Object.keys(row.metadata_on_create).length > 0);
  }

  /**
   * @param {Record<string, unknown>} row
   * @param {Record<string, string>} patch
   */
  function metaAfterMerged(row, patch) {
    const cur = { ...(row.metadata_current || {}) };
    return { ...cur, ...patch };
  }
</script>

<section class="project-export-wrap" class:is-collapsed={!exportPanelExpanded}>
  <div class="export-panel-toolbar">
    <h2 id="export-project-heading" class="export-panel-title">Export project</h2>
    <button
      type="button"
      class="export-collapse-toggle"
      on:click={() => (exportPanelExpanded = !exportPanelExpanded)}
      aria-expanded={exportPanelExpanded}
      aria-controls="export-project-panel"
      aria-label={exportPanelExpanded ? 'Collapse export project' : 'Expand export project'}
    >
      <span class="export-collapse-chevron" class:open={exportPanelExpanded} aria-hidden="true"></span>
      <span class="export-collapse-label">{exportPanelExpanded ? 'Hide' : 'Show'}</span>
    </button>
  </div>

  {#if exportPanelExpanded}
    <div
      id="export-project-panel"
      class="export-panel-body"
      role="region"
      aria-labelledby="export-project-heading"
    >
      <p class="export-intro">
        CSVs and the table preview are all based on the same underlying queue data. Use this section when you need files
        for Media Cloud or a full decision audit.
      </p>

      <ul class="export-options">
        <li class="export-option">
          <div class="export-option-main">
            <h3 class="export-option-title">Project CSV</h3>
            <p class="export-option-desc">
              Media Cloud-style spreadsheet: <strong>one row per source marked keep or add</strong> (combined across
              all queues). Skip, remove, and undecided sources are omitted. This is the file reviewers usually hand off
              for collection updates.
            </p>
          </div>
          <div class="export-option-actions">
            {#if canDownloadMainCsv}
              <a
                class="export-btn export-btn-primary"
                href={getReviewProjectExportUrl(projectGuid)}
                download
                title="Download Project CSV"
              >
                Download
              </a>
            {:else}
              <span
                class="export-btn export-btn-primary export-btn-disabled"
                title={MAIN_CSV_DISABLED_TITLE}
                aria-label={MAIN_CSV_DISABLED_TITLE}
              >
                Download
              </span>
            {/if}
          </div>
        </li>

        <li class="export-option">
          <div class="export-option-main">
            <h3 class="export-option-title">Audit CSV</h3>
            <p class="export-option-desc">
          <strong>Every</strong> queue row: same source columns as above, plus
          <strong>review_decision</strong>, <strong>removal_reason</strong>, <strong>skip_note</strong>, and
          <strong>reviewer_queue</strong> (queue number). Use for QA, reporting, or reconciling against the Project CSV.
            </p>
          </div>
          <div class="export-option-actions">
            {#if canDownloadAuditCsv}
              <a
                class="export-btn export-btn-secondary"
                href={getReviewProjectAuditExportUrl(projectGuid)}
                download
                title="Download audit CSV"
              >
                Download
              </a>
            {:else}
              <span
                class="export-btn export-btn-secondary export-btn-disabled"
                title={AUDIT_DISABLED_TITLE}
                aria-label={AUDIT_DISABLED_TITLE}
              >
                Download
              </span>
            {/if}
          </div>
        </li>

        <li class="export-option">
          <div class="export-option-main">
            <h3 class="export-option-title">Decisions preview</h3>
            <p class="export-option-desc">
              Opens a table of all sources in all queues. The <strong>Project CSV</strong> column is
              <strong>Yes</strong> only when that row would appear in the Project CSV file (decision is keep or add),
              and <strong>No</strong> otherwise.
            </p>
          </div>
          <div class="export-option-actions">
            <button
              type="button"
              class="export-btn export-btn-secondary"
              on:click={onDecisionsPreview}
              disabled={!canDownloadAuditCsv}
              title={canDownloadAuditCsv ? 'Open table preview' : AUDIT_DISABLED_TITLE}
            >
              Open preview
            </button>
          </div>
        </li>

        <li class="export-option">
          <div class="export-option-main">
            <h3 class="export-option-title">Publish to MediaCloud <span class="experimental-tag">[For authorized users]</span></h3>
            <p class="export-option-desc">
              {#if publishEnabled}
                Sync reviewer decisions directly to {publishTargetLabel}. First publish creates
                <strong> {publishDefaultName} </strong>; later publishes reuse the same target collection.
              {:else}
                Direct publish is currently disabled by server configuration.
              {/if}
            </p>
            {#if publishEnabled}
              <div class="publish-form">
              <label class="publish-label" for="publish-token-input">MediaCloud API token</label>
              <input
                id="publish-token-input"
                class="publish-input"
                type="password"
                bind:value={apiToken}
                placeholder="Paste your token (not stored)"
                disabled={publishLoading}
              />
              <label class="publish-label" for="publish-name-input">Collection name override (optional)</label>
              <input
                id="publish-name-input"
                class="publish-input"
                type="text"
                bind:value={collectionName}
                placeholder={publishDefaultName}
                disabled={publishLoading || !!existingPublishCollection}
              />
              {#if existingPublishCollection}
                <div class="publish-note">
                  Reusing existing target collection:
                  <a
                    href={mediacloudCollectionUrl(existingPublishCollection)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {existingPublishCollection}
                  </a>
                </div>
              {/if}
              {#if publishMetadataUpdatesEnabled}
                <label class="publish-metadata-toggle" title="PATCH primary_language, pub_country, pub_state on existing MediaCloud sources (KEEP/ADD only)">
                  <input
                    type="checkbox"
                    bind:checked={applyMetadataUpdates}
                    on:change={handleMetadataCheckboxChange}
                    disabled={publishLoading || previewLoading}
                  />
                  <span>Also push language / geography metadata to existing sources</span>
                </label>
              {/if}
              <div class="publish-note">
                KEEP/ADD are synced, REMOVE unlinks from the target collection, SKIP/UNDECIDED are no-op.
              </div>
              </div>
            {/if}
          </div>
          <div class="export-option-actions">
            <button
              type="button"
              class="export-btn export-btn-primary"
              on:click={handleOpenPublishPreview}
              disabled={publishLoading || previewLoading || !publishEnabled}
              title="Preview operations then export to MediaCloud"
            >
              {#if !publishEnabled}
                Disabled
              {:else}
                {previewLoading ? 'Preparing...' : 'Preview & Export'}
              {/if}
            </button>
          </div>
          {#if previewError}
            <div class="publish-error">{previewError}</div>
          {/if}
          {#if publishError}
            <div class="publish-error">{publishError}</div>
          {/if}
          {#if publishResult}
            <div
              class="publish-result"
              class:publish-result-partial={(publishResult.summary?.errors?.length || 0) > 0}
            >
              Published to collection
              <a
                href={mediacloudCollectionUrl(publishResult.collection_id)}
                target="_blank"
                rel="noopener noreferrer"
              >
                {publishResult.collection_id}
              </a>
              ({publishResult.summary?.ensured_associations || 0} ensured,
              {publishResult.summary?.removed_associations || 0} removed,
              {publishResult.summary?.created_sources || 0} new sources
              {#if (publishResult.summary?.metadata_updates_attempted || 0) > 0}
                , metadata {publishResult.summary?.metadata_updates_succeeded || 0} ok
                {#if (publishResult.summary?.metadata_updates_failed || 0) > 0}
                  / {publishResult.summary.metadata_updates_failed} failed
                {/if}
              {/if}
              ).
            </div>
            {#if (publishResult.summary?.warnings?.length || 0) > 0 || (publishResult.summary?.errors?.length || 0) > 0}
              <div class="publish-result-messages">
                {#if (publishResult.summary?.warnings?.length || 0) > 0}
                  <div class="publish-warnings-block">
                    <div class="publish-messages-title">Warnings</div>
                    <ul class="publish-messages-list">
                      {#each publishResult.summary.warnings as w}
                        <li>{w}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
                {#if (publishResult.summary?.errors?.length || 0) > 0}
                  <div class="publish-errors-block">
                    <div class="publish-messages-title">Errors</div>
                    <ul class="publish-messages-list">
                      {#each publishResult.summary.errors as e}
                        <li>{e}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </div>
            {/if}
          {/if}
        </li>
      </ul>
    </div>
  {/if}
</section>

{#if showPublishPreviewModal}
  <div class="publish-preview-overlay" on:click={() => (showPublishPreviewModal = false)}>
    <div
      class="publish-preview-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="publish-preview-title"
      on:click|stopPropagation
    >
      <div class="publish-preview-header">
        <h3 id="publish-preview-title">Publish Preview <span class="experimental-tag">[Experimental]</span></h3>
        <button type="button" class="publish-preview-close" on:click={() => (showPublishPreviewModal = false)}>×</button>
      </div>
      <p class="publish-preview-description">
        These are the rows that will result in MediaCloud operations if you continue.
      </p>
      <div class="publish-env-banner">
        Target API: <code>{preflight?.api_base_url || publishTargetApiBaseUrl}</code>
      </div>
      <div class="publish-preflight">
        {#if preflight?.ok}
          Token preflight passed{#if preflight?.profile?.email} as <strong>{preflight.profile.email}</strong>{/if}.
        {:else}
          Token preflight failed.
        {/if}
      </div>

      <div class="publish-preview-table-wrap">
        {#if previewHasRows}
          <table class="publish-preview-table">
            <thead>
              <tr>
                <th>Operation</th>
                <th>Decision</th>
                <th>Source</th>
                <th>Homepage</th>
                <th>Metadata</th>
                <th>MediaCloud</th>
              </tr>
            </thead>
            <tbody>
              {#each publishPreviewRows as row}
                <tr>
                  <td class="op-title-cell">
                    <div class="op-title-stack">
                      <span class="op-badge op-{row.operation}" title={row.operation}>
                        {operationPrimaryLabel(row.operation)}
                      </span>
                      {#if rowWillPatchMetadata(row)}
                        <span
                          class="op-badge op-metadata-will-update"
                          title="These fields will be PATCHed on the existing MediaCloud source before collection membership is ensured."
                        >
                          Metadata update
                        </span>
                      {:else if rowHasMetadataOnCreate(row)}
                        <span
                          class="op-badge op-metadata-will-update"
                          title="Language and geography from the review will be sent when the source is created."
                        >
                          Includes metadata
                        </span>
                      {/if}
                    </div>
                  </td>
                  <td>{row.decision}</td>
                  <td>{row.source_label || 'N/A'}</td>
                  <td>
                    {#if row.source_homepage}
                      <a href={row.source_homepage} target="_blank" rel="noopener noreferrer">{row.source_homepage}</a>
                    {:else}
                      —
                    {/if}
                  </td>
                  <td class="metadata-patch-cell">
                    {#if row.operation === 'create_source_and_associate' && rowHasMetadataOnCreate(row)}
                      <div class="metadata-diff">
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">Before</div>
                          <div class="metadata-diff-muted">— (source does not exist yet)</div>
                        </div>
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">After create</div>
                          <code class="metadata-patch-code">{JSON.stringify(row.metadata_on_create)}</code>
                        </div>
                      </div>
                    {:else if row.metadata_remote_status === 'unchanged'}
                      <div class="metadata-diff">
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">Before / after (MediaCloud)</div>
                          <span class="metadata-in-sync">Already in sync</span>
                          {#if row.metadata_current && Object.keys(row.metadata_current).length > 0}
                            <code class="metadata-patch-code metadata-patch-sub">{JSON.stringify(row.metadata_current)}</code>
                          {/if}
                        </div>
                      </div>
                    {:else if rowWillPatchMetadata(row)}
                      <div class="metadata-diff">
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">Before (MediaCloud)</div>
                          <code class="metadata-patch-code">{JSON.stringify(row.metadata_current || {})}</code>
                          <div class="metadata-patch-footnote">
                            PATCH updates only:
                            {Object.keys(row.metadata_update || {}).join(', ')}
                          </div>
                        </div>
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">After (publish)</div>
                          <code class="metadata-patch-code metadata-after-code">{JSON.stringify(
                              metaAfterMerged(row, row.metadata_update)
                            )}</code>
                          <div class="metadata-patch-footnote">
                            Full language / geography snapshot after applying the PATCH above (unchanged fields keep
                            their MediaCloud values).
                          </div>
                        </div>
                      </div>
                    {:else if row.metadata_remote_status === 'lookup_skipped_no_directory_api' || row.metadata_remote_status === 'lookup_failed_or_source_missing'}
                      <div class="metadata-diff">
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">Before (MediaCloud)</div>
                          <div class="metadata-diff-unknown">Unknown — could not load the current source.</div>
                        </div>
                        <div class="metadata-diff-block">
                          <div class="metadata-diff-heading">After (if you publish)</div>
                          {#if row.metadata_desired && Object.keys(row.metadata_desired).length > 0}
                            <code class="metadata-patch-code">{JSON.stringify(row.metadata_desired)}</code>
                          {:else}
                            <div class="metadata-diff-muted">—</div>
                          {/if}
                        </div>
                      </div>
                    {:else}
                      —
                    {/if}
                  </td>
                  <td>
                    {#if row.source_id}
                      <a href={mediacloudSourceUrl(row.source_id)} target="_blank" rel="noopener noreferrer">
                        View ↗
                      </a>
                    {:else}
                      —
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        {:else}
          <p class="publish-preview-empty">No actionable operations. Nothing will be exported.</p>
        {/if}
      </div>

      {#if publishPreviewSummary}
        <div class="publish-preview-summary">
          Planned: {publishPreviewSummary.ensure_association || 0} ensure, {publishPreviewSummary.create_source_and_associate || 0} create+associate, {publishPreviewSummary.remove_association || 0} remove
          {#if (publishPreviewSummary.metadata_updates_planned || 0) > 0}
            , {publishPreviewSummary.metadata_updates_planned} metadata change(s) vs MediaCloud
          {/if}
          {#if (publishPreviewSummary.metadata_updates_skipped_unchanged || 0) > 0}
            , {publishPreviewSummary.metadata_updates_skipped_unchanged} metadata already matched MediaCloud
          {/if}
          {#if (publishPreviewSummary.metadata_remote_lookup_skipped || 0) > 0}
            , {publishPreviewSummary.metadata_remote_lookup_skipped} source(s) could not be read for compare (publish may still PATCH from review if you continue)
          {/if}
          .
        </div>
      {/if}

      <div class="publish-preview-actions">
        <button type="button" class="export-btn export-btn-secondary" on:click={() => (showPublishPreviewModal = false)}>
          Cancel
        </button>
        <button
          type="button"
          class="export-btn export-btn-primary"
          on:click={handleConfirmPublish}
          disabled={!previewHasRows || publishLoading || !preflight?.ok}
        >
          {publishLoading ? 'Exporting...' : 'Export to MediaCloud'}
        </button>
      </div>
      {#if previewTargetCollectionId}
        <div class="publish-note">
          Target collection:
          <a href={mediacloudCollectionUrl(previewTargetCollectionId)} target="_blank" rel="noopener noreferrer">
            {previewTargetCollectionId}
          </a>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .project-export-wrap {
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    border: 1px solid #d0d7de;
    padding: 14px 18px 18px;
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .project-export-wrap.is-collapsed {
    padding-bottom: 14px;
  }

  .export-panel-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .export-panel-title {
    margin: 0;
    flex: 1;
    min-width: 0;
    font-size: 18px;
    font-weight: 700;
    color: #2c3e50;
  }

  .export-collapse-toggle {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid #d0d7de;
    background: #f6f8fa;
    color: #34495e;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    flex-shrink: 0;
    font-family: inherit;
  }

  .export-collapse-toggle:hover {
    background: #eef1f4;
    border-color: #c0c7d0;
  }

  .export-collapse-chevron {
    display: inline-block;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #5a6c7d;
    transform: rotate(-90deg);
    transition: transform 0.18s ease;
  }

  .export-collapse-chevron.open {
    transform: rotate(0deg);
  }

  .export-collapse-label {
    white-space: nowrap;
  }

  .export-panel-body {
    display: flex;
    flex-direction: column;
    gap: 0;
    margin-top: 14px;
    padding-top: 4px;
    border-top: 1px solid #e6e9ee;
  }

  .export-intro {
    margin: 0 0 18px 0;
    font-size: 14px;
    line-height: 1.5;
    color: #5a6c7d;
  }

  .export-options {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .export-option {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px 20px;
    padding: 16px 0;
    border-top: 1px solid #e6e9ee;
  }

  .publish-form {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 560px;
  }

  .publish-label {
    font-size: 12px;
    color: #5a6c7d;
    font-weight: 700;
  }

  .publish-input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    font-size: 13px;
  }

  .publish-note {
    font-size: 12px;
    color: #6a7a88;
    line-height: 1.35;
  }

  .publish-metadata-toggle {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-top: 6px;
    font-size: 12px;
    color: #34495e;
    line-height: 1.4;
    cursor: pointer;
  }

  .publish-metadata-toggle input {
    margin-top: 2px;
    flex-shrink: 0;
  }

  .op-title-cell {
    min-width: 148px;
  }

  .op-title-stack {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .op-metadata-will-update {
    background: #fff8e6;
    color: #8a5a00;
    border: 1px solid #f0d78c;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  .metadata-patch-cell {
    max-width: 280px;
    vertical-align: top;
    font-size: 11px;
  }

  .metadata-diff {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .metadata-diff-block {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .metadata-diff-heading {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #57606a;
  }

  .metadata-diff-muted {
    font-size: 11px;
    color: #7f8c8d;
    font-style: italic;
  }

  .metadata-diff-unknown {
    font-size: 11px;
    color: #9a6700;
    line-height: 1.35;
  }

  .metadata-patch-footnote {
    margin-top: 4px;
    font-size: 10px;
    line-height: 1.35;
    color: #57606a;
  }

  .metadata-patch-code {
    display: block;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
    padding: 4px 6px;
    background: #f6f8fa;
    border-radius: 4px;
    font-size: 10px;
    color: #24292f;
  }

  .metadata-after-code {
    background: #e8f5e9;
    border: 1px solid #c8e6c9;
  }

  .metadata-patch-sub {
    margin-top: 4px;
    opacity: 0.92;
  }

  .metadata-in-sync {
    font-size: 12px;
    color: #1f7a3d;
    font-weight: 600;
  }

  .publish-error {
    width: 100%;
    margin-top: 8px;
    color: #c0392b;
    font-size: 12px;
    font-weight: 600;
  }

  .publish-result {
    width: 100%;
    margin-top: 8px;
    color: #1f7a3d;
    font-size: 12px;
    font-weight: 600;
  }

  .publish-result.publish-result-partial {
    color: #8a5a00;
  }

  .publish-result-messages {
    margin-top: 10px;
    width: 100%;
    max-width: 560px;
    font-size: 12px;
    font-weight: 400;
    text-align: left;
  }

  .publish-messages-title {
    font-weight: 700;
    margin-bottom: 4px;
    color: #2c3e50;
  }

  .publish-messages-list {
    margin: 0 0 10px 16px;
    padding: 0;
    line-height: 1.45;
    color: #34495e;
  }

  .publish-warnings-block .publish-messages-list {
    color: #8a5a00;
  }

  .publish-errors-block .publish-messages-title {
    color: #a32011;
  }

  .publish-errors-block .publish-messages-list {
    color: #c0392b;
  }

  .experimental-tag {
    font-size: 12px;
    color: #a36a00;
    font-weight: 700;
  }

  .export-option:first-of-type {
    border-top: none;
    padding-top: 0;
  }

  .export-option-main {
    flex: 1 1 240px;
    min-width: 0;
  }

  .export-option-title {
    margin: 0 0 6px 0;
    font-size: 15px;
    font-weight: 700;
    color: #2c3e50;
  }

  .export-option-desc {
    margin: 0;
    font-size: 13px;
    line-height: 1.5;
    color: #5a6c7d;
  }

  .export-option-desc strong {
    color: #34495e;
    font-weight: 700;
  }

  .export-option-actions {
    flex: 0 0 auto;
    display: flex;
    align-items: flex-start;
    padding-top: 2px;
  }

  .export-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 118px;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    border: 1px solid transparent;
    cursor: pointer;
    box-sizing: border-box;
    font-family: inherit;
  }

  .export-btn-primary {
    background: #3498db;
    color: #fff;
    border-color: #3498db;
  }

  a.export-btn-primary:hover {
    background: #2980b9;
    border-color: #2980b9;
    color: #fff;
  }

  .export-btn-secondary {
    background: #fff;
    color: #34495e;
    border-color: #d0d7de;
  }

  button.export-btn-secondary:hover:not(:disabled) {
    background: #f6f8fa;
    border-color: #c0c7d0;
  }

  button.export-btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  a.export-btn-secondary:hover {
    background: #f6f8fa;
    border-color: #c0c7d0;
    color: #2c3e50;
  }

  .export-btn-disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .publish-preview-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1100;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .publish-preview-modal {
    width: min(1100px, 100%);
    max-height: 90vh;
    overflow: auto;
    background: #fff;
    border-radius: 10px;
    padding: 16px 18px 18px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .publish-preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .publish-preview-header h3 {
    margin: 0;
    font-size: 18px;
    color: #2c3e50;
  }

  .publish-preview-close {
    border: none;
    background: transparent;
    font-size: 22px;
    cursor: pointer;
    color: #7f8c8d;
  }

  .publish-preview-description {
    margin: 0;
    color: #5a6c7d;
    font-size: 13px;
  }

  .publish-env-banner {
    background: #eef6fc;
    border: 1px solid #cfe2ff;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 12px;
    color: #34495e;
  }

  .publish-preflight {
    font-size: 12px;
    color: #1f7a3d;
    font-weight: 600;
  }

  .publish-preview-table-wrap {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: auto;
  }

  .publish-preview-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .publish-preview-table th,
  .publish-preview-table td {
    padding: 8px 6px;
    border-bottom: 1px solid #dee2e6;
    text-align: left;
    vertical-align: top;
  }

  .publish-preview-table th {
    background: #f8f9fa;
    font-size: 12px;
    color: #2c3e50;
  }

  .publish-preview-empty {
    margin: 0;
    padding: 14px;
    color: #7f8c8d;
    font-size: 13px;
  }

  .op-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
  }

  .op-ensure_association {
    background: #d4edda;
    color: #155724;
  }

  .op-create_source_and_associate {
    background: #d1ecf1;
    color: #0c5460;
  }

  .op-remove_association {
    background: #f8d7da;
    color: #721c24;
  }

  .publish-preview-summary {
    font-size: 12px;
    color: #34495e;
    font-weight: 600;
  }

  .publish-preview-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
</style>

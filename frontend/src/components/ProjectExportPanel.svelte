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

  let exportPanelExpanded = false;

  const MAIN_CSV_DISABLED_TITLE =
    'Available after at least one source is marked keep or add in a reviewer queue. That file lists only those rows for Media Cloud.';
  const AUDIT_DISABLED_TITLE = 'Create reviewer queues and assign sources before exporting or previewing.';
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
      </ul>
    </div>
  {/if}
</section>

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
</style>

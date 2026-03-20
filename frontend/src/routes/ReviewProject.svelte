<script>
  import { onMount } from 'svelte';
  import {
    getReviewProject,
    getReviewProjectExportUrl,
    generateReviewProjectQueues,
    setReviewProjectEditMetadata,
    setReviewProjectName,
    getReviewProjectGuidelines,
    setReviewProjectGuidelines,
  } from '../lib/api.js';

  let projectGuid = null;
  let project = null;
  let queues = [];
  let derivedStatus = null;
  function queueProgressPercent(q) {
    if (!q || !q.stats || !q.stats.total) return 0;
    const total = q.stats.total;
    const undecided = q.stats.undecided || 0;
    const decidedOrDone = Math.max(0, total - undecided);
    return Math.round((decidedOrDone / total) * 100);
  }
  let stats = null;

  let loading = false;
  let error = null;

  let warning = null;
  let localEditMetadata = false;
  let initialEditMetadata = false;
  let editMetadataSaving = false;
  let editMetadataError = null;
  let queueCount = 2;
  let generatingQueues = false;
  let queueGenError = null;
  let localProjectName = '';
  let projectNameSaving = false;
  let projectNameError = null;
  let showProjectNameEditor = false;
  let copiedQueueGuid = null;
  let copiedIconTimer = null;
  let showEditMetadataEditor = false;

  let showGuidelinesEditor = false;
  let guidelinesLoadError = null;
  let guidelinesLoading = false;
  let guidelinesSaving = false;
  let guidelinesError = null;
  let initialGuidelinesMarkdown = '';
  let guidelinesMarkdown = '';

  let currentPath = window.location.pathname;

  function getProjectGuidFromUrl() {
    const match = currentPath.match(/^\/review-projects\/([0-9a-fA-F-]+)$/);
    return match ? match[1] : null;
  }

  function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  onMount(async () => {
    const params = new URLSearchParams(window.location.search);
    warning = params.get('warning');

    const updatePath = () => {
      currentPath = window.location.pathname;
      projectGuid = getProjectGuidFromUrl();
    };

    window.addEventListener('popstate', updatePath);
    projectGuid = getProjectGuidFromUrl();

    if (projectGuid) {
      await loadProject();
    }

    return () => {
      window.removeEventListener('popstate', updatePath);
    };
  });

  async function loadProject() {
    if (!projectGuid) return;

    loading = true;
    error = null;

    try {
      const data = await getReviewProject(projectGuid);
      project = data.project;
      localProjectName = project?.name || '';
      showProjectNameEditor = false;
      localEditMetadata = !!project.edit_metadata;
      initialEditMetadata = !!project.edit_metadata;
      showEditMetadataEditor = false;
      derivedStatus = data.derived_status;
      queues = data.queues || [];
      stats = data.stats || null;
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load review project';
      console.error('Error loading review project:', err);
    } finally {
      loading = false;
    }
  }

  async function handleGenerateQueues() {
    if (!projectGuid) return;
    generatingQueues = true;
    queueGenError = null;
    try {
      const result = await generateReviewProjectQueues(projectGuid, queueCount);
      warning = result?.warning || null;
      await loadProject();
    } catch (err) {
      queueGenError = err.response?.data?.error || err.message || 'Failed to generate queues';
      console.error('Error generating queues:', err);
    } finally {
      generatingQueues = false;
    }
  }

  async function handleSaveProjectEditMetadata() {
    if (!projectGuid || editMetadataSaving) return;

    editMetadataSaving = true;
    editMetadataError = null;

    const nextValue = !!localEditMetadata;
    try {
      await setReviewProjectEditMetadata(projectGuid, nextValue);
      await loadProject();
      showEditMetadataEditor = false;
    } catch (err) {
      editMetadataError =
        err.response?.data?.error || err.message || 'Failed to update metadata editing';
      // Revert UI if the server update failed.
      localEditMetadata = !nextValue;
    } finally {
      editMetadataSaving = false;
    }
  }

  async function handleSaveProjectName() {
    if (!projectGuid || !project || projectNameSaving) return;
    const nextName = String(localProjectName || '').trim();
    if (!nextName) {
      projectNameError = 'Project name cannot be empty';
      return;
    }

    projectNameSaving = true;
    projectNameError = null;
    try {
      const resp = await setReviewProjectName(projectGuid, nextName);
      if (resp?.project) {
        project = resp.project;
      } else {
        await loadProject();
      }
      showProjectNameEditor = false;
    } catch (err) {
      projectNameError = err.response?.data?.error || err.message || 'Failed to update project name';
    } finally {
      projectNameSaving = false;
    }
  }

  function handleStartProjectNameEdit() {
    localProjectName = project?.name || '';
    projectNameError = null;
    showProjectNameEditor = true;
  }

  function handleCancelProjectNameEdit() {
    localProjectName = project?.name || '';
    projectNameError = null;
    showProjectNameEditor = false;
  }

  function handleStartEditMetadataEdit() {
    localEditMetadata = initialEditMetadata;
    editMetadataError = null;
    showEditMetadataEditor = true;
  }

  function handleCancelEditMetadataEdit() {
    localEditMetadata = initialEditMetadata;
    editMetadataError = null;
    showEditMetadataEditor = false;
  }

  async function handleStartGuidelinesEdit() {
    if (!projectGuid || showGuidelinesEditor || guidelinesLoading) return;

    guidelinesLoadError = null;
    guidelinesLoading = true;

    try {
      const resp = await getReviewProjectGuidelines(projectGuid);
      const markdown = resp?.guidelines ?? '';
      initialGuidelinesMarkdown = markdown;
      guidelinesMarkdown = markdown;
      guidelinesError = null;
      showGuidelinesEditor = true;
    } catch (err) {
      guidelinesLoadError = err.response?.data?.error || err.message || 'Failed to load guidelines';
      guidelinesError = null;
    } finally {
      guidelinesLoading = false;
    }
  }

  function handleCancelGuidelinesEdit() {
    guidelinesError = null;
    guidelinesMarkdown = initialGuidelinesMarkdown;
    showGuidelinesEditor = false;
    guidelinesLoadError = null;
  }

  async function handleSaveGuidelinesEdit() {
    if (!projectGuid || guidelinesSaving) return;

    guidelinesError = null;
    guidelinesSaving = true;

    const nextMarkdown = String(guidelinesMarkdown ?? '');
    if (!nextMarkdown.trim()) {
      guidelinesError = 'Guidelines cannot be empty.';
      guidelinesSaving = false;
      return;
    }

    try {
      await setReviewProjectGuidelines(projectGuid, nextMarkdown);
      await loadProject();
      showGuidelinesEditor = false;
    } catch (err) {
      guidelinesError = err.response?.data?.error || err.message || 'Failed to save guidelines';
    } finally {
      guidelinesSaving = false;
    }
  }

  function queueReviewerLink(queueGuid) {
    return `${window.location.origin}/reviews/${queueGuid}`;
  }

  async function copyQueueLink(queueGuid) {
    const link = queueReviewerLink(queueGuid);
    try {
      await navigator.clipboard.writeText(link);
      copiedQueueGuid = queueGuid;
      if (copiedIconTimer) {
        clearTimeout(copiedIconTimer);
      }
      copiedIconTimer = setTimeout(() => {
        copiedQueueGuid = null;
        copiedIconTimer = null;
      }, 1200);
    } catch (e) {
      // Clipboard can fail due to browser permissions; fall back to selection-free UI.
      console.error('Copy failed:', e);
    }
  }
</script>

<div class="container">
  {#if loading && !project}
    <div class="loading">Loading project...</div>
  {:else if error && !project}
    <div class="error-message">{error}</div>
  {:else if project}
    <div class="header-bar">
      <div class="header-left">
        <button type="button" class="back-home" on:click={() => window.navigate('/')}>↩</button>
        <div class="title">
          ReviewProject: {project.name || projectGuid}
        </div>
      </div>

      <div class="header-right">
        <div class="status-pill status-pill-{derivedStatus}">
          {derivedStatus || project.status || 'pending'}
        </div>
        <a
          class="export-button"
          href={getReviewProjectExportUrl(projectGuid)}
          download
        >
          Download Project CSV
        </a>
      </div>
    </div>

    {#if warning}
      <div class="warning-banner">{warning}</div>
    {/if}

    <div class="content">
      <div class="project-meta">
        <div class="meta-row">
          <div class="meta-label">Project name</div>
          <div class="meta-value">
            {#if !showProjectNameEditor}
              <div class="project-name-display">
                <span class="project-name-text">{project.name || projectGuid}</span>
                <button
                  type="button"
                  class="edit-name-button"
                  on:click={handleStartProjectNameEdit}
                  title="Edit project name"
                  aria-label="Edit project name"
                >
                  ✎
                </button>
              </div>
            {:else}
              <div class="project-name-editor">
                <input
                  type="text"
                  bind:value={localProjectName}
                  class="project-name-input"
                  disabled={projectNameSaving}
                  placeholder="Enter project name"
                />
                <button
                  type="button"
                  class="cancel-name-button"
                  on:click={handleCancelProjectNameEdit}
                  disabled={projectNameSaving}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  class="save-name-button"
                  on:click={handleSaveProjectName}
                  disabled={projectNameSaving || !localProjectName || !localProjectName.trim()}
                >
                  {projectNameSaving ? 'Saving...' : 'Save'}
                </button>
              </div>
            {/if}
            {#if projectNameError}
              <div class="inline-error">{projectNameError}</div>
            {/if}
          </div>
        </div>

        <div class="meta-row">
          <div class="meta-label">Seed collections</div>
          <div class="meta-value">
            <div class="seed-collection-chips">
              {#each (project.collection_names && project.collection_names.length > 0 ? project.collection_names : project.collection_ids || []) as collection}
                <span class="seed-collection-chip">{collection}</span>
              {/each}
            </div>
          </div>
        </div>

        <div class="meta-row guidelines-meta-row">
          <div class="meta-label guidelines-meta-label">
            Guidelines (Markdown)
            {#if !showGuidelinesEditor}
              <button
                type="button"
                class="edit-name-button"
                on:click={handleStartGuidelinesEdit}
                title="Edit guidelines"
                aria-label="Edit guidelines"
                disabled={loading || guidelinesLoading}
              >
                ✎
              </button>
            {/if}
          </div>

          <div class="meta-value meta-value-guidelines">
            {#if showGuidelinesEditor}
              <div class="guidelines-editor">
                <textarea
                  class="guidelines-textarea"
                  bind:value={guidelinesMarkdown}
                  rows="10"
                  disabled={guidelinesLoading || guidelinesSaving}
                />

                <div class="guidelines-editor-actions">
                  <button
                    type="button"
                    class="cancel-name-button"
                    on:click={handleCancelGuidelinesEdit}
                    disabled={guidelinesSaving || guidelinesLoading}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    class="save-name-button"
                    on:click={handleSaveGuidelinesEdit}
                    disabled={guidelinesSaving || guidelinesLoading}
                  >
                    {guidelinesSaving ? 'Saving...' : 'Save'}
                  </button>
                </div>

                {#if guidelinesLoadError}
                  <div class="inline-error">{guidelinesLoadError}</div>
                {/if}
                {#if guidelinesError}
                  <div class="inline-error">{guidelinesError}</div>
                {/if}
              </div>
            {/if}
          </div>
        </div>

        {#if stats}
          <div class="meta-row">
            <div class="meta-label">Status</div>
            <div class="meta-value">
              <div class="status-count-row">
                <div class="status-count">
                  <span class="status-count-label">Total</span>
                  <span class="status-count-value">{stats.total || 0}</span>
                </div>
                <div class="status-count">
                  <span class="status-count-label">Undecided</span>
                  <span class="status-count-value">{stats.undecided || 0}</span>
                </div>
                <div class="status-count">
                  <span class="status-count-label">Keep</span>
                  <span class="status-count-value">{stats.keep || 0}</span>
                </div>
                <div class="status-count">
                  <span class="status-count-label">Skip</span>
                  <span class="status-count-value">{stats.skip || 0}</span>
                </div>
                <div class="status-count">
                  <span class="status-count-label">Remove</span>
                  <span class="status-count-value">{stats.remove || 0}</span>
                </div>
                <div class="status-count status-count-added">
                  <span class="status-count-label">Added</span>
                  <span class="status-count-value">{stats.add || 0}</span>
                </div>
              </div>
            </div>
          </div>
        {/if}

        {#if stats && stats.total > 0}
          <div class="project-progress-row">
            <div class="project-progress-bar">
              <div
                class="seg seg-undecided"
                style={`width: ${((stats.undecided || 0) / stats.total) * 100}%`}
                title={`Undecided: ${stats.undecided || 0}`}
              />
              <div
                class="seg seg-keep"
                style={`width: ${((stats.keep || 0) / stats.total) * 100}%`}
                title={`Keep: ${stats.keep || 0}`}
              />
              <div
                class="seg seg-remove"
                style={`width: ${((stats.remove || 0) / stats.total) * 100}%`}
                title={`Remove: ${stats.remove || 0}`}
              />
              <div
                class="seg seg-skip"
                style={`width: ${((stats.skip || 0) / stats.total) * 100}%`}
                title={`Skipped: ${stats.skip || 0}`}
              />
            </div>
          </div>
        {/if}
        {#if queues.length > 0}
          <div class="virtual-queue-bottom-actions">
            <div class="virtual-queue-metadata">
              <div class="project-name-display">
                <span class="project-name-text metadata-setting-text">
                  Review Source Metadata
                </span>
                {#if !showEditMetadataEditor}
                  <span class="project-name-text metadata-setting-text">
                    : {initialEditMetadata ? '✓' : '✕'}
                  </span>
                  <button
                    type="button"
                    class="edit-name-button"
                    on:click={handleStartEditMetadataEdit}
                    title="Edit metadata setting"
                    aria-label="Edit metadata setting"
                  >
                    ✎
                  </button>
                {:else}
                  <div class="setting-editor">
                    <label class="metadata-edit-toggle" title="Propagates to all reviewer queues in this project">
                      <input
                        type="checkbox"
                        bind:checked={localEditMetadata}
                        disabled={editMetadataSaving || generatingQueues}
                      />
                      <span class="toggle-slider"></span>
                    </label>
                    <button
                      type="button"
                      class="cancel-name-button"
                      on:click={handleCancelEditMetadataEdit}
                      disabled={editMetadataSaving || generatingQueues}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      class="save-name-button"
                      on:click={handleSaveProjectEditMetadata}
                      disabled={editMetadataSaving || generatingQueues}
                    >
                      {editMetadataSaving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                {/if}
              </div>
              {#if editMetadataError}
                <div class="inline-error">{editMetadataError}</div>
              {/if}
            </div>
            <div class="virtual-queue-bottom-buttons">
              <button
                type="button"
                class="queue-open"
                on:click={() => window.navigate(`/review-projects/${projectGuid}/skipped`)}
              >
                Review skipped sources
                {#if stats && stats.skip !== undefined && stats.skip > 0}
                  <span class="queue-count">({stats.skip})</span>
                {/if}
              </button>

              <button
                type="button"
                class="queue-copy"
                on:click={() => window.navigate(`/review-projects/${projectGuid}/added`)}
              >
                Review added sources
                {#if stats && stats.add !== undefined && stats.add > 0}
                  <span class="queue-count">({stats.add})</span>
                {/if}
              </button>

            <button
              type="button"
              class="queue-copy"
              on:click={() => window.navigate(`/review-projects/${projectGuid}/removed`)}
            >
              Review removed sources
              {#if stats && stats.remove !== undefined && stats.remove > 0}
                <span class="queue-count">({stats.remove})</span>
              {/if}
            </button>
            </div>
          </div>
        {/if}
      </div>

      <div class="queues">
        <h2>Reviewer Queues</h2>

        {#if queues.length === 0}
          <div class="queue-gen-card">
            <div class="queue-gen-title">Generate reviewer queues</div>
            <p class="queue-gen-subtitle">
              Queues are created after sources are seeded. Enter how many reviewers/queues you want to split into.
            </p>

            <form class="queue-gen-form" on:submit|preventDefault={handleGenerateQueues}>
              <div class="form-group">
                <label for="queue-count-input">queue_count</label>
                <input
                  id="queue-count-input"
                  type="number"
                  min="1"
                  step="1"
                  bind:value={queueCount}
                  disabled={generatingQueues}
                />
              </div>

              {#if queueGenError}
                <div class="error-banner">{queueGenError}</div>
              {/if}

              <button type="submit" disabled={generatingQueues}>
                {generatingQueues ? 'Generating...' : 'Generate queues'}
              </button>
            </form>
          </div>
        {:else}
          <div class="queues-grid">
            {#each queues as q}
              <div class="queue-card">
                <div class="queue-top">
                  <div class="queue-title">
                    Queue #{(q.queue_index ?? 0) + 1}
                  </div>
                  <div class="queue-status status-pill status-pill-{q.status}">
                    {q.status}
                  </div>
                </div>

                {#if q.stats}
                  <div class="queue-stats">
                    <div class="stat-line"><strong>{q.stats.total}</strong> total</div>
                    <div class="stat-line"><strong>{q.stats.undecided}</strong> undecided</div>
                    <div class="stat-line"><strong>{q.stats.keep}</strong> keep</div>
                    <div class="stat-line"><strong>{q.stats.remove}</strong> remove</div>
                    <div class="stat-line"><strong>{q.stats.add}</strong> add</div>
                    <div class="stat-line"><strong>{q.stats.skip}</strong> skip</div>
                  </div>

                  <div class="queue-progress">
                    <div class="queue-progress-outer">
                      <div
                        class="queue-progress-inner"
                        style={`width: ${queueProgressPercent(q)}%`}
                      />
                    </div>
                    <div class="queue-progress-label">{queueProgressPercent(q)}% complete</div>
                  </div>
                {/if}

                <div class="queue-link-row">
                  <div class="queue-link-label">Reviewer URL</div>
                  <div class="queue-link-value">
                    <code class="queue-code">{queueReviewerLink(q.queue_guid)}</code>
                    <button
                      type="button"
                      class="queue-copy-icon {copiedQueueGuid === q.queue_guid ? 'is-copied' : ''}"
                      on:click={() => copyQueueLink(q.queue_guid)}
                      title="Copy full reviewer URL"
                      aria-label="Copy full reviewer URL"
                    >
                      {#if copiedQueueGuid === q.queue_guid}
                        ✓
                      {:else}
                        📋
                      {/if}
                    </button>
                  </div>
                </div>

                <div class="queue-actions">
                  <button
                    type="button"
                    class="queue-open"
                    on:click={() => window.navigate(`/reviews/${q.queue_guid}`)}
                  >
                    Open Queue
                  </button>

                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

    </div>
  {/if}
</div>

<style>
  .container {
    margin: 0 auto;
    padding: 20px;
    padding-top: 72px;
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
    font-size: 18px;
  }

  .error-message {
    background: #fee;
    color: #c33;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #fcc;
    text-align: center;
  }

  .warning-banner {
    margin: 18px 0 0;
    background: #fff3cd;
    color: #856404;
    padding: 14px 16px;
    border-radius: 8px;
    border: 1px solid #ffeeba;
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
    font-size: 16px;
    font-weight: 400;
    cursor: pointer;
  }

  .title {
    font-weight: 700;
    color: #f6f8fa;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .status-pill {
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 13px;
    text-transform: lowercase;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #f6f8fa;
  }

  .status-pill-pending {
    background-color: #ecf0f1;
    color: #7f8c8d;
  }

  .status-pill-in_progress {
    background-color: #fff3cd;
    color: #856404;
  }

  .status-pill-completed {
    background-color: #27ae60;
    color: white;
  }

  .export-button {
    padding: 10px 14px;
    border-radius: 999px;
    background-color: #3498db;
    color: white;
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #3498db;
  }

  .content {
    max-width: 1320px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
    padding-top: 8px;
  }

  .project-meta {
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    border: 1px solid #d0d7de;
    padding: 16px 18px;
  }

  .meta-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 8px;
  }

  .meta-label {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 700;
    text-transform: uppercase;
  }

  .meta-value {
    font-size: 14px;
    color: #2c3e50;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .guidelines-meta-row {
    align-items: flex-start;
  }

  .guidelines-meta-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .meta-value-guidelines {
    overflow: visible;
    text-overflow: clip;
    flex: 1;
    min-width: 0;
  }

  .seed-collection-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }

  .seed-collection-chip {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background: #f6f8fa;
    color: #34495e;
    font-size: 12px;
    font-weight: 600;
    max-width: 360px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .project-name-editor {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .project-name-display {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .project-name-text {
    font-weight: 700;
    color: #2c3e50;
  }

  .metadata-setting-text {
    color: #7f8c8d;
  }

  .edit-name-button {
    width: 28px;
    height: 28px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background: #fff;
    color: #34495e;
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
  }

  .edit-name-button:hover {
    background-color: #f6f8fa;
  }

  .project-name-input {
    min-width: 260px;
    max-width: 520px;
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    font-size: 14px;
    color: #2c3e50;
  }

  .save-name-button {
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid #3498db;
    background-color: #3498db;
    color: white;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
  }

  .save-name-button:disabled {
    opacity: 0.65;
    cursor: not-allowed;
  }

  .cancel-name-button {
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid #d0d7de;
    background: #fff;
    color: #34495e;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
  }

  .cancel-name-button:disabled {
    opacity: 0.65;
    cursor: not-allowed;
  }

  .setting-display {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .setting-editor {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .setting-badge {
    min-width: 30px;
    height: 30px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 18px;
    border: 1px solid transparent;
  }

  .setting-on {
    background: #eaf8ef;
    color: #1f7a3d;
    border-color: #b7e2c4;
  }

  .setting-off {
    background: #f3f4f6;
    color: #7f8c8d;
    border-color: #d0d7de;
  }

  .inline-error {
    margin-top: 6px;
    color: #c0392b;
    font-size: 12px;
    font-weight: 600;
  }

  .guidelines-editor {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .guidelines-textarea {
    width: 100%;
    min-height: 240px;
    padding: 10px 12px;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    font-size: 13px;
    color: #2c3e50;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    background: white;
    resize: vertical;
  }

  .guidelines-editor-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    align-items: center;
  }

  .metadata-edit-toggle {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    position: relative;
    cursor: pointer;
  }

  .metadata-edit-toggle input {
    /* Hide the default checkbox; the slider is the visible control. */
    opacity: 0;
    position: absolute;
    width: 1px;
    height: 1px;
  }

  .toggle-slider {
    width: 44px;
    height: 24px;
    border-radius: 999px;
    background: #ecf0f1;
    border: 1px solid #d0d7de;
    position: relative;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  .toggle-slider::before {
    content: '';
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: white;
    position: absolute;
    top: 50%;
    left: 3px;
    transform: translateY(-50%);
    transition: transform 0.15s ease;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
  }

  .metadata-edit-toggle input:checked + .toggle-slider {
    background: #27ae60;
    border-color: #27ae60;
  }

  .metadata-edit-toggle input:checked + .toggle-slider::before {
    transform: translateY(-50%) translateX(20px);
  }

  .queues h2 {
    margin: 0 0 12px;
    color: #2c3e50;
  }

  .empty-text {
    color: #7f8c8d;
    font-style: italic;
  }

  .queue-gen-card {
    background: white;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    padding: 18px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .queue-gen-title {
    font-weight: 800;
    color: #2c3e50;
    font-size: 16px;
  }

  .queue-gen-subtitle {
    color: #7f8c8d;
    font-size: 13px;
    margin-top: -4px;
    margin-bottom: 4px;
  }

  .queue-gen-form .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
  }

  input[type="number"] {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
  }

  .error-banner {
    background: #fee;
    color: #c33;
    padding: 12px 14px;
    border-radius: 8px;
    border: 1px solid #fcc;
    margin-bottom: 12px;
  }

  button[type="submit"] {
    width: 100%;
    padding: 12px 14px;
    background-color: #3498db;
    border: none;
    border-radius: 8px;
    color: white;
    font-weight: 700;
    cursor: pointer;
  }

  button[type="submit"]:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .queues-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }

  .queue-card {
    background: white;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    padding: 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .queue-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
  }

  .queue-title {
    font-weight: 700;
    color: #2c3e50;
  }

  .queue-stats {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 4px 14px;
  }

  .queue-progress {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .queue-progress-outer {
    width: 100%;
    height: 10px;
    border-radius: 999px;
    background: #ecf0f1;
    border: 1px solid #d0d7de;
    overflow: hidden;
  }

  .queue-progress-inner {
    height: 100%;
    background: #27ae60;
    border-radius: 999px;
    transition: width 0.2s ease;
  }

  .queue-progress-label {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 700;
    text-transform: lowercase;
  }

  .stat-line {
    font-size: 13px;
    color: #34495e;
  }

  .queue-link-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .queue-link-value {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .queue-link-label {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 700;
    text-transform: uppercase;
  }

  .queue-code {
    flex: 1;
    font-size: 12px;
    color: #3498db;
    background: #f5fbff;
    border: 1px solid rgba(52, 152, 219, 0.2);
    padding: 6px 8px;
    border-radius: 8px;
    word-break: break-all;
  }

  .queue-copy-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    border: 1px solid #d0d7de;
    background-color: #f6f8fa;
    color: #34495e;
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    transition: color 180ms ease, border-color 180ms ease, background-color 180ms ease, opacity 220ms ease;
  }

  .queue-copy-icon:hover {
    background-color: #eef2f7;
  }

  .queue-copy-icon.is-copied {
    color: #1f7a3d;
    border-color: #b7e2c4;
    background-color: #eaf8ef;
    opacity: 1;
  }

  .queue-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }

  .queue-open {
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid #3498db;
    background-color: #3498db;
    color: white;
    font-weight: 700;
    cursor: pointer;
  }

  .queue-copy {
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid #d0d7de;
    background-color: #f6f8fa;
    color: #34495e;
    font-weight: 700;
    cursor: pointer;
  }

  .skipped-sources {
    background: white;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    padding: 16px 16px;
    margin-top: 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .skipped-sources h2 {
    margin: 0;
    color: #2c3e50;
    font-size: 20px;
  }

  .skipped-subtitle {
    color: #7f8c8d;
    font-size: 13px;
    line-height: 1.35;
  }

  .skipped-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    align-items: center;
  }

  .virtual-queue-bottom-actions {
    margin-top: 14px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
    flex-wrap: wrap;
  }

  .virtual-queue-metadata {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .virtual-queue-bottom-buttons {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .queue-count {
    margin-left: 8px;
    font-weight: 800;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.95);
  }

  /* Override count color for secondary (light) button */
  .queue-copy .queue-count {
    color: #7f8c8d;
  }

  .project-progress-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 14px;
  }

  .project-progress-bar {
    flex: 1;
    height: 12px;
    border-radius: 999px;
    background: #ecf0f1;
    border: 1px solid #d0d7de;
    overflow: hidden;
    display: flex;
  }

  .project-progress-bar .seg {
    height: 100%;
    transition: width 0.2s ease;
  }

  .seg-undecided {
    background: #95a5a6;
  }

  .seg-keep {
    background: #27ae60;
  }

  .seg-remove {
    background: #e74c3c;
  }

  .seg-skip {
    background: #f1c40f;
  }

  .status-count-row {
    display: flex;
    align-items: baseline;
    gap: 18px;
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .status-count {
    display: inline-flex;
    gap: 8px;
    align-items: baseline;
    white-space: nowrap;
  }

  .status-count-label {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 800;
    text-transform: lowercase;
  }

  .status-count-value {
    font-size: 14px;
    font-weight: 900;
    color: #2c3e50;
  }

  /* Make the Added count visually separated from the rest. */
  .status-count-added {
    margin-left: 8px;
    padding-left: 10px;
    border-left: 2px solid #d0d7de;
  }
</style>


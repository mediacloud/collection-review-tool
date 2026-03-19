<script>
  import { onMount } from 'svelte';
  import { getReviewProject, getReviewProjectExportUrl, generateReviewProjectQueues } from '../lib/api.js';

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
  let queueCount = 2;
  let generatingQueues = false;
  let queueGenError = null;

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

  function queueReviewerLink(queueGuid) {
    return `${window.location.origin}/reviews/${queueGuid}`;
  }

  async function copyQueueLink(queueGuid) {
    const link = queueReviewerLink(queueGuid);
    try {
      await navigator.clipboard.writeText(link);
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
          <div class="meta-label">Seed collections</div>
          <div class="meta-value">
            {(project.collection_names && project.collection_names.length > 0 ? project.collection_names : project.collection_ids || []).join(', ')}
          </div>
        </div>
        {#if stats}
          <div class="meta-row">
            <div class="meta-label">Sources total</div>
            <div class="meta-value">{stats.total}</div>
          </div>
          <div class="meta-row">
            <div class="meta-label">Undecided</div>
            <div class="meta-value">{stats.undecided}</div>
          </div>
          <div class="meta-row">
            <div class="meta-label">Keep / Add</div>
            <div class="meta-value">{stats.keep} keep, {stats.add} add</div>
          </div>
        {/if}
        <div class="meta-row">
          <div class="meta-label">Created</div>
          <div class="meta-value">{formatDate(project.created_at)}</div>
        </div>
        <div class="meta-row">
          <div class="meta-label">Last updated</div>
          <div class="meta-value">{formatDate(project.updated_at)}</div>
        </div>
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
                  <code class="queue-code">{`/reviews/${q.queue_guid}`}</code>
                </div>

                <div class="queue-actions">
                  <button
                    type="button"
                    class="queue-open"
                    on:click={() => window.navigate(`/reviews/${q.queue_guid}`)}
                  >
                    Open Queue
                  </button>

                  <button
                    type="button"
                    class="queue-copy"
                    on:click={() => copyQueueLink(q.queue_guid)}
                  >
                    Copy Link
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

  .queue-link-label {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 700;
    text-transform: uppercase;
  }

  .queue-code {
    font-size: 12px;
    color: #3498db;
    background: #f5fbff;
    border: 1px solid rgba(52, 152, 219, 0.2);
    padding: 6px 8px;
    border-radius: 8px;
    word-break: break-all;
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
</style>


<script>
  import { onMount } from 'svelte';
  import AllDecisionsModal from '../components/AllDecisionsModal.svelte';
  import { getReviewProject, getReviewItemsByQueueGuid } from '../lib/api.js';

  let projectGuid = null;
  let queueGuid = null;
  let project = null;
  let queue = null;
  let stats = null;
  let loading = false;
  let error = null;
  let showAllDecisionsModal = false;
  let allDecisionsItems = [];
  let allDecisionsLoading = false;
  let allDecisionsTruncation = '';

  function parseFromUrl() {
    const match = window.location.pathname.match(
      /^\/review-projects\/([0-9a-fA-F-]+)\/queues\/([0-9a-fA-F-]+)$/
    );
    return match ? { projectGuid: match[1], queueGuid: match[2] } : { projectGuid: null, queueGuid: null };
  }

  async function loadQueueLanding() {
    if (!projectGuid || !queueGuid) return;
    loading = true;
    error = null;
    try {
      const data = await getReviewProject(projectGuid);
      project = data.project;
      stats = data.stats || null;

      const queues = data.queues || [];
      queue = queues.find((q) => q.queue_guid === queueGuid) || null;
      if (!queue) {
        error = 'Queue not found for this project.';
      }
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to load reviewer landing page';
      console.error('Error loading reviewer landing page:', err);
    } finally {
      loading = false;
    }
  }

  async function openAllDecisionsModal() {
    if (!queueGuid) return;
    showAllDecisionsModal = true;
    allDecisionsLoading = true;
    allDecisionsItems = [];
    allDecisionsTruncation = '';
    try {
      const data = await getReviewItemsByQueueGuid(queueGuid, { page: 1, page_size: 1000 });
      allDecisionsItems = data.items || [];
      const totalRows = data.total ?? allDecisionsItems.length;
      if (totalRows > allDecisionsItems.length) {
        allDecisionsTruncation = `Showing ${allDecisionsItems.length} of ${totalRows} rows.`;
      }
    } catch (err) {
      allDecisionsTruncation =
        err.response?.data?.error || err.message || 'Failed to load queue decisions.';
    } finally {
      allDecisionsLoading = false;
    }
  }

  function handleReevaluateFromDecisions(event) {
    const item = event?.detail?.item;
    if (!item || !queueGuid) return;
    showAllDecisionsModal = false;
    window.navigate(`/reviews/${queueGuid}?mode=reevaluate&item_id=${item.id}`);
  }

  onMount(() => {
    const parsed = parseFromUrl();
    projectGuid = parsed.projectGuid;
    queueGuid = parsed.queueGuid;
    loadQueueLanding();
  });
</script>

<div class="container">
  <div class="header-bar">
    <div class="header-left">
      <div class="title">ReviewProject: {project?.name || projectGuid}</div>
    </div>
  </div>

  {#if loading && !project}
    <div class="loading">Loading reviewer landing page...</div>
  {:else if error}
    <div class="error-banner">{error}</div>
  {:else if project && queue}
    <div class="content">
      <div class="card">
        <h1>Your Media Cloud Source Review Queue</h1>
        <div class="landing-explainer">
          <p>
            <a
              href="https://search.mediacloud.org/"
              target="_blank"
              rel="noopener noreferrer"
            >Media Cloud</a>
            is an open research platform for studying online media. In Media Cloud, <strong>collections</strong> group
            sources so researchers and partners can analyze or curate them together.
          </p>
          <p>
            This application is for <strong>collections review</strong> workflows: you have been assigned a queue of sources, and your task is to decide whether to keep, skip, or remove on individual sources. Find your queue below to get started, and use the 'review decisions' button to validate your work.
          </p>
          <p>
            When you've exhausted your queue, inform your review project coordinator for next steps.   
          </div>
      </div>

      <div class="card">
        <h2>Your queue</h2>
        <div class="queue-status-toast">Queue status: {queue.status}</div>
        {#if queue.status === 'completed'}
          <div class="queue-complete-banner" role="status" aria-live="polite">
            <strong>Queue complete.</strong>
            You can review or edit prior decisions, then notify your project coordinator.
          </div>
        {/if}
        <div class="queue-summary">
          <div><strong>Total:</strong> {queue?.stats?.total ?? 0}</div>
          <div><strong>Undecided:</strong> {queue?.stats?.undecided ?? 0}</div>
        </div>
        {#if (queue?.stats?.total || 0) > 0}
          <div class="progress-block">
            <div class="progress-label">Your queue progress</div>
            <div class="project-progress-bar queue-progress-bar">
              <div
                class="seg seg-undecided"
                style={`width: ${((queue?.stats?.undecided || 0) / queue.stats.total) * 100}%`}
                title={`Undecided: ${queue?.stats?.undecided || 0}`}
              />
              <div
                class="seg seg-keep"
                style={`width: ${((queue?.stats?.keep || 0) / queue.stats.total) * 100}%`}
                title={`Keep: ${queue?.stats?.keep || 0}`}
              />
              <div
                class="seg seg-remove"
                style={`width: ${((queue?.stats?.remove || 0) / queue.stats.total) * 100}%`}
                title={`Remove: ${queue?.stats?.remove || 0}`}
              />
              <div
                class="seg seg-skip"
                style={`width: ${((queue?.stats?.skip || 0) / queue.stats.total) * 100}%`}
                title={`Skip: ${queue?.stats?.skip || 0}`}
              />
            </div>
          </div>
        {/if}
        <button
          type="button"
          class="primary-button open-queue-button"
          on:click={() => window.navigate(`/reviews/${queueGuid}`)}
        >
          Open my queue
        </button>
        <button
          type="button"
          class="primary-button queue-decisions-button"
          on:click={openAllDecisionsModal}
        >
          Review all decisions
        </button>
      </div>

      {#if stats}
        <div class="card">
          <h2>Project-wide status</h2>
          <div class="status-count-row">
            <div class="status-count"><span class="label">Total</span><span class="value">{stats.total || 0}</span></div>
            <div class="status-count"><span class="label">Undecided</span><span class="value">{stats.undecided || 0}</span></div>
            <div class="status-count"><span class="label">Keep</span><span class="value">{stats.keep || 0}</span></div>
            <div class="status-count"><span class="label">Skip</span><span class="value">{stats.skip || 0}</span></div>
            <div class="status-count"><span class="label">Remove</span><span class="value">{stats.remove || 0}</span></div>
            <div class="status-count"><span class="label">Added</span><span class="value">{stats.add || 0}</span></div>
          </div>

          {#if (stats.total || 0) > 0}
            <div class="progress-block">
              <div class="progress-label">Project progress</div>
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
                  title={`Skip: ${stats.skip || 0}`}
                />
              </div>
            </div>
          {/if}

          {#if project?.show_virtual_queue_links_on_reviewer_landing !== false}
            <div class="progress-block">
              <div class="progress-label">Project virtual queues</div>
              <div class="virtual-queue-nav-actions">
                <button type="button" class="secondary-button" on:click={() => window.navigate(`/review-projects/${projectGuid}/skipped`)}>
                  Review skipped sources
                </button>
                <button type="button" class="secondary-button" on:click={() => window.navigate(`/review-projects/${projectGuid}/added`)}>
                  Review added sources
                </button>
                <button type="button" class="secondary-button" on:click={() => window.navigate(`/review-projects/${projectGuid}/removed`)}>
                  Review removed sources
                </button>
                <button type="button" class="secondary-button" on:click={() => window.navigate(`/review-projects/${projectGuid}/kept`)}>
                  Review kept sources
                </button>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}

  <AllDecisionsModal
    show={showAllDecisionsModal}
    items={allDecisionsItems}
    loading={allDecisionsLoading}
    modalTitle="Queue decisions"
    modalDescription="All review decisions recorded for this reviewer queue."
    truncationNote={allDecisionsTruncation}
    on:close={() => (showAllDecisionsModal = false)}
    on:reevaluate={handleReevaluateFromDecisions}
  />
</div>

<style>
  .container {
    margin: 0 auto;
    padding: 20px;
    padding-top: 72px;
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

  .title {
    font-weight: 700;
    color: #f6f8fa;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .content {
    max-width: 980px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .card {
    background: white;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    padding: 16px 18px;
  }

  h1 {
    margin: 0 0 8px 0;
    font-size: 24px;
    color: #2c3e50;
  }

  h2 {
    margin: 0 0 10px 0;
    font-size: 18px;
    color: #2c3e50;
  }

  .subtitle {
    margin: 0;
    color: #5a6c7d;
  }

  .status-count-row {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
  }

  .status-count .label {
    color: #7f8c8d;
    font-size: 12px;
    font-weight: 700;
    margin-right: 6px;
  }

  .status-count .value {
    color: #2c3e50;
    font-size: 14px;
    font-weight: 900;
  }

.landing-explainer {
    margin: 0 0 14px 0;
    font-size: 14px;
    line-height: 1.55;
    color: #5a6c7d;
  }


  .queue-summary {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, max-content));
    gap: 8px 12px;
    margin-bottom: 12px;
    color: #34495e;
    font-size: 14px;
  }

  .queue-status-toast {
    display: inline-flex;
    align-items: center;
    margin-bottom: 10px;
    padding: 6px 10px;
    border-radius: 999px;
    background: #eef2f7;
    border: 1px solid #d0d7de;
    color: #34495e;
    font-size: 12px;
    font-weight: 700;
    text-transform: lowercase;
  }

  .queue-complete-banner {
    margin: 0 0 12px;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid #b7e2c4;
    background: #eaf8ef;
    color: #1f7a3d;
    font-size: 13px;
    line-height: 1.4;
  }

  .progress-block {
    margin-top: 12px;
  }

  .progress-label {
    margin-bottom: 6px;
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .project-progress-bar {
    width: 100%;
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

  .queue-progress-bar {
    height: 12px;
  }

  .primary-button,
  .secondary-button {
    padding: 10px 12px;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
  }

  .primary-button {
    border: 1px solid #3498db;
    background-color: #3498db;
    color: white;
  }

  .open-queue-button {
    width: 100%;
    margin-top: 8px;
    padding: 14px 16px;
    font-size: 17px;
    font-weight: 800;
  }

  .secondary-button {
    border: 1px solid #d0d7de;
    background-color: #f6f8fa;
    color: #34495e;
  }

  .queue-decisions-button {
    margin-top: 10px;
    width: 100%;
    padding: 8px 12px;
    background-color: #eef1f4;
    border-color: #d0d7de;
    color: #34495e;
  }

  .virtual-queue-nav-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
    font-size: 18px;
  }

  .error-banner {
    max-width: 980px;
    margin: 0 auto;
    background: #fee;
    color: #c33;
    padding: 12px 14px;
    border-radius: 8px;
    border: 1px solid #fcc;
    text-align: center;
  }
</style>

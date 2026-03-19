<script>
  import { onMount } from 'svelte';
  import { startReview, startReviewProject, getInProgressReviews, getCompletedReviews, getGuidelineTemplates, getReviewProjects } from '../lib/api.js';

  let collectionId = '';
  let projectCollectionIdsInput = '';
  let loading = false;
  let projectLoading = false;
  let error = null;
  let projectError = null;
  let inProgressReviews = [];
  let loadingReviews = false;
  let completedReviews = [];
  let loadingCompleted = false;
  let showCompleted = false;
  let reviewProjects = [];
  let loadingProjects = false;
  let showProjects = true;
  let guidelineTemplates = [];
  let selectedTemplate = 'default';
  let loadingTemplates = false;
  let editMetadata = false;

  onMount(async () => {
    await loadReviewProjects();
    await loadGuidelineTemplates();
  });

  async function loadGuidelineTemplates() {
    loadingTemplates = true;
    try {
      guidelineTemplates = await getGuidelineTemplates();
      if (guidelineTemplates.length > 0 && !guidelineTemplates.includes(selectedTemplate)) {
        selectedTemplate = guidelineTemplates[0];
      }
    } catch (err) {
      console.error('Error loading templates:', err);
    } finally {
      loadingTemplates = false;
    }
  }

  async function loadInProgressReviews() {
    loadingReviews = true;
    try {
      inProgressReviews = await getInProgressReviews();
    } catch (err) {
      console.error('Error loading in-progress reviews:', err);
    } finally {
      loadingReviews = false;
    }
  }

  async function loadCompletedReviews() {
    if (completedReviews.length > 0) {
      // Already loaded, just toggle visibility
      showCompleted = !showCompleted;
      return;
    }
    
    loadingCompleted = true;
    try {
      completedReviews = await getCompletedReviews();
      showCompleted = true;
    } catch (err) {
      console.error('Error loading completed reviews:', err);
    } finally {
      loadingCompleted = false;
    }
  }

  async function loadReviewProjects() {
    loadingProjects = true;
    try {
      reviewProjects = await getReviewProjects();
    } catch (err) {
      console.error('Error loading review projects:', err);
      reviewProjects = [];
    } finally {
      loadingProjects = false;
    }
  }

  function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function navigateToReview(reviewId) {
    window.navigate(`/reviews/${reviewId}`);
  }

  function handleKeydown(event, reviewId) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      navigateToReview(reviewId);
    }
  }

  async function handleSubmit() {
    // Convert to string and trim if it's a number
    const idStr = String(collectionId || '').trim();
    if (!idStr) {
      error = 'Please enter a collection ID';
      return;
    }

    const id = parseInt(idStr);
    if (isNaN(id) || id <= 0) {
      error = 'Collection ID must be a positive number';
      return;
    }

    loading = true;
    error = null;

    try {
      const review = await startReview(id, selectedTemplate, editMetadata);
      await loadInProgressReviews(); // Refresh the list
      window.navigate(`/reviews/${review.id}`);
    } catch (err) {
      error = err.response?.data?.error || err.message || 'Failed to start review';
      console.error('Error starting review:', err);
    } finally {
      loading = false;
    }
  }

  async function handleProjectSubmit() {
    projectError = null;

    const raw = String(projectCollectionIdsInput || '');
    const parts = raw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    if (parts.length === 0) {
      projectError = 'Please enter at least one collection ID (comma-separated).';
      return;
    }

    let collectionIds = [];
    try {
      collectionIds = parts.map((p) => parseInt(p, 10));
    } catch {
      projectError = 'All collection IDs must be valid integers.';
      return;
    }

    if (collectionIds.some((id) => !id || id <= 0)) {
      projectError = 'All collection IDs must be positive integers.';
      return;
    }

    projectLoading = true;
    try {
      const result = await startReviewProject(collectionIds, selectedTemplate, editMetadata);
      const guid = result?.project?.guid;
      if (!guid) {
        projectError = 'Project start succeeded but no project GUID was returned.';
        return;
      }
      // Any warnings are returned on the project page.
      window.navigate(`/review-projects/${guid}`);
    } catch (err) {
      projectError = err.response?.data?.error || err.message || 'Failed to start review project';
      console.error('Error starting review project:', err);
    } finally {
      projectLoading = false;
    }
  }
</script>

<div class="container">
  <div class="main-content">
    <div class="card">
      <h1>MediaCloud Collections Review</h1>
      <p class="subtitle">Review and manage sources in MediaCloud collections</p>

      <div class="project-divider" />

      <div class="project-section">
        <h2>Start ReviewProject</h2>
        <p class="subtitle">Seed a multi-collection project into reviewer queues.</p>

        <form on:submit|preventDefault={handleProjectSubmit}>
          {#if guidelineTemplates.length > 0}
            <div class="form-group">
              <label for="guideline-template">Annotation Guidelines Template</label>
              <select
                id="guideline-template"
                bind:value={selectedTemplate}
                disabled={projectLoading || loadingTemplates}
              >
                {#each guidelineTemplates as template}
                  <option value={template}>{template}</option>
                {/each}
              </select>
            </div>
          {/if}

          <div class="form-group">
            <button
              type="button"
              class="context-toggle-button"
              on:click={() => (editMetadata = !editMetadata)}
              disabled={projectLoading}
            >
              <span class="toggle-label">
                <span class="toggle-indicator {editMetadata ? 'on' : 'off'}"></span>
                Enable metadata editing in this project
              </span>
            </button>
          </div>

          <div class="form-group">
            <label for="project-collection-ids">MediaCloud Collection IDs</label>
            <input
              id="project-collection-ids"
              type="text"
              bind:value={projectCollectionIdsInput}
              placeholder="e.g. 123, 456, 789"
              disabled={projectLoading}
            />
          </div>

          {#if projectError}
            <div class="error">{projectError}</div>
          {/if}

          <button type="submit" disabled={projectLoading}>
            {projectLoading ? 'Starting...' : 'Start ReviewProject'}
          </button>
        </form>
      </div>
    </div>

    <div class="card">
      <div class="reviews-list-header">
        <h2>Review Projects</h2>
        <button
          class="toggle-button"
          on:click={() => (showProjects = !showProjects)}
          disabled={loadingProjects}
        >
          {loadingProjects ? 'Loading...' : (showProjects ? 'Hide' : 'Show')}
        </button>
      </div>

      {#if showProjects}
        {#if loadingProjects}
          <p class="loading-text">Loading projects...</p>
        {:else if reviewProjects.length === 0}
          <p class="empty-text">No review projects found.</p>
        {:else}
          <div class="projects-table-wrap">
            <table class="projects-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Queues</th>
                  <th>Total</th>
                  <th>Keep</th>
                  <th>Remove</th>
                  <th>Add</th>
                  <th>Undecided</th>
                  <th>Skip</th>
                  <th>Open</th>
                </tr>
              </thead>
              <tbody>
                {#each reviewProjects as p}
                  <tr>
                    <td class="projects-name">
                      {p.name || p.guid}
                    </td>
                    <td class="projects-status">
                      {p.derived_status}
                    </td>
                    <td>{p.queues_count}</td>
                    <td>{p.stats.total}</td>
                    <td>{p.stats.keep}</td>
                    <td>{p.stats.remove}</td>
                    <td>{p.stats.add}</td>
                    <td>{p.stats.undecided}</td>
                    <td>{p.stats.skip}</td>
                    <td>
                      <button
                        type="button"
                        class="projects-open"
                        on:click={() => window.navigate(`/review-projects/${p.guid}`)}
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}
    </div>

  </div>
</div>

<style>
  .container {
    min-height: 100vh;
    padding: 20px;
  }

  .main-content {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 40px;
    width: 100%;
  }

  h1 {
    font-size: 28px;
    margin-bottom: 10px;
    color: #2c3e50;
  }

  .subtitle {
    color: #7f8c8d;
    margin-bottom: 30px;
    font-size: 16px;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .context-toggle-button {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid #e0e4e8;
    background-color: #f8f9fa;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.2s, border-color 0.2s;
  }

  .context-toggle-button:hover:enabled {
    background-color: #eef2f7;
    border-color: #d0d7de;
  }

  .context-toggle-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .toggle-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #34495e;
  }

  .toggle-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid #bdc3c7;
    background-color: white;
  }

  .toggle-indicator.on {
    border-color: #27ae60;
    background-color: #27ae60;
  }

  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #34495e;
  }

  input, select {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    transition: border-color 0.3s;
  }

  input:focus, select:focus {
    outline: none;
    border-color: #3498db;
  }

  input:disabled, select:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }

  button {
    width: 100%;
    padding: 12px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  button:hover:not(:disabled) {
    background-color: #2980b9;
  }

  button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }

  .error {
    background-color: #fee;
    color: #c33;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 20px;
    border: 1px solid #fcc;
  }

  .project-divider {
    margin: 28px 0;
    border: 0;
    border-top: 1px solid #e0e4e8;
  }

  .projects-table-wrap {
    overflow-x: auto;
    margin-top: 12px;
  }

  .projects-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  .projects-table th,
  .projects-table td {
    border-bottom: 1px solid #e0e4e8;
    padding: 10px 8px;
    text-align: left;
    white-space: nowrap;
  }

  .projects-table th {
    color: #2c3e50;
    font-weight: 700;
    background: #f8f9fa;
  }

  .projects-name {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .projects-status {
    font-weight: 700;
    text-transform: lowercase;
    color: #34495e;
  }

  .projects-open {
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid #3498db;
    background-color: #3498db;
    color: white;
    font-weight: 700;
    cursor: pointer;
  }

  .projects-open:hover {
    background-color: #2980b9;
  }

  .project-section h2 {
    margin-bottom: 8px;
    color: #2c3e50;
    font-size: 20px;
  }

  .project-section .subtitle {
    margin: 0 0 18px 0;
    color: #7f8c8d;
    font-size: 14px;
  }

  .reviews-list h2 {
    font-size: 24px;
    margin-bottom: 20px;
    color: #2c3e50;
  }

  .reviews-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .reviews-list-header h2 {
    margin-bottom: 0;
  }

  .toggle-button {
    padding: 8px 16px;
    background-color: #95a5a6;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
    white-space: nowrap;
  }

  .toggle-button:hover:not(:disabled) {
    background-color: #7f8c8d;
  }

  .toggle-button:disabled {
    background-color: #bdc3c7;
    cursor: not-allowed;
  }

  .empty-text {
    color: #7f8c8d;
    text-align: center;
    padding: 20px;
    font-style: italic;
  }

  .loading-text {
    color: #7f8c8d;
    text-align: center;
    padding: 20px;
  }

  .reviews-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .review-item {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;
    background-color: #fafafa;
  }

  .review-item:hover {
    background-color: #f0f0f0;
    border-color: #3498db;
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
  }

  .review-item.completed {
    background-color: #f8f9fa;
    border-color: #d5d5d5;
  }

  .review-item.completed:hover {
    background-color: #e9ecef;
    border-color: #95a5a6;
  }

  .review-item:focus {
    outline: 2px solid #3498db;
    outline-offset: 2px;
  }

  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .review-id {
    font-weight: 600;
    color: #2c3e50;
    font-size: 16px;
  }

  .completeness {
    font-weight: 600;
    color: #27ae60;
    font-size: 18px;
  }

  .completed-badge {
    color: #7f8c8d;
  }

  .review-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #7f8c8d;
  }

  .review-date {
    flex: 1;
  }

  .review-stats {
    margin-left: 16px;
  }
</style>

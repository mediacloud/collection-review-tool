<script>
  let scrollY = 0;

  function backToTop() {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reducedMotion ? 'instant' : 'smooth' });
  }
</script>

<svelte:window bind:scrollY />

{#if scrollY > 320}
  <button
    type="button"
    class="btn back-to-top"
    aria-label="Back to top"
    title="Back to top"
    on:click={backToTop}
  >
    <span aria-hidden="true">&#8593;</span>
  </button>
{/if}

<style>
  .back-to-top {
    position: fixed;
    right: calc(20px + env(safe-area-inset-right, 0px));
    bottom: calc(20px + env(safe-area-inset-bottom, 0px));
    z-index: 40;
    width: 48px;
    height: 48px;
    padding: 0;
    justify-content: center;
    font-size: 24px;
    line-height: 1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  }

  .back-to-top:hover {
    border-color: var(--v2-ink);
  }

  .back-to-top:focus-visible {
    outline: 2px solid var(--v2-ink);
    outline-offset: 3px;
  }
</style>

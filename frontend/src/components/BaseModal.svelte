<script>
  import { onMount, onDestroy } from 'svelte';

  export let show = false;
  export let onClose = () => {};
  // Layout variant: "center" (default) or "below-header"
  export let variant = 'center';

  function handleOverlayClick() {
    onClose();
  }

  function handleKeydown(event) {
    if (event.key === 'Escape') {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
</script>

{#if show}
  <div class="base-modal-overlay {variant}" on:click={handleOverlayClick}>
    <div
      class="base-modal-content"
      on:click|stopPropagation
      role="dialog"
      aria-modal="true"
    >
      <slot />
    </div>
  </div>
{/if}

<style>
  .base-modal-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    z-index: 1100;
    box-sizing: border-box;
  }

  .base-modal-overlay.center {
    justify-content: center;
    align-items: center;
    padding: 20px;
  }

  .base-modal-overlay.below-header {
    justify-content: center;
    align-items: flex-start;
    padding: 56px 20px 20px;
  }

  .base-modal-content {
    max-width: 1320px;
  }
</style>



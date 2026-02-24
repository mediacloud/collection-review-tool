<script>
  import { onMount } from 'svelte';
  import Home from './routes/Home.svelte';
  import Review from './routes/Review.svelte';

  let currentPath = window.location.pathname;

  // Simple router using browser history API
  function navigate(path) {
    window.history.pushState({}, '', path);
    currentPath = path;
  }

  onMount(() => {
    // Listen for browser back/forward buttons
    window.addEventListener('popstate', () => {
      currentPath = window.location.pathname;
    });

    // Export navigate function for use in components
    window.navigate = navigate;
  });
</script>

<main>
  {#if currentPath === '/'}
    <Home />
  {:else if currentPath.startsWith('/reviews/')}
    <Review />
  {:else}
    <Home />
  {/if}
</main>

<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
  }

  main {
    min-height: 100vh;
  }
</style>

<script>
  // Layout wrapper: provides CSS tokens and fonts for all demo screens.
  // Screen routing is handled by App.svelte; use <slot> to render children.
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
  <link
    href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<div class="demo-root">
  <slot />
</div>

<style>
  /* ── Design tokens as CSS custom properties ─────────────────── */
  .demo-root {
    /* Backgrounds */
    --v2-bg: linear-gradient(180deg, #f7f7f6 0%, #ececea 100%);
    --v2-surface: #f9f9f8;
    --v2-card: #ffffff;

    /* Text */
    --v2-ink: #15171a;
    --v2-body: #44464a;
    --v2-mute: #7f8189;

    /* Borders */
    --v2-line: #e5e5e2;
    --v2-line-soft: #efefec;

    /* Nav */
    --v2-nav-ink: #15171a;
    --v2-nav-mute: rgba(33, 35, 40, 0.62);

    /* Accent (Media Cloud orange) */
    --v2-accent: #e25c40;
    --v2-accent-soft: #fce5dd;
    --v2-accent-ink: #b8431f;

    /* Decision palette */
    --v2-kept: #e25c40;
    --v2-kept-soft: #fce5dd;
    --v2-removed: #1a1c1f;
    --v2-removed-soft: #e1e1de;
    --v2-added: #f5a48a;
    --v2-added-soft: #fdede5;
    --v2-skipped: #9ca0a8;
    --v2-skipped-soft: #e8e8e5;
    --v2-undecided: #ebeae5;

    /* Status */
    --v2-red: #c8362f;
    --v2-red-soft: #f8dedb;
    --v2-warn: #b57a12;
    --v2-warn-soft: #f6e7c9;
    --v2-neutral: #e9e9e5;

    /* Typography */
    --v2-sans: 'DM Sans', system-ui, sans-serif;
    --v2-mono: 'DM Mono', ui-monospace, monospace;

    /* Shell */
    min-height: 100vh;
    background: var(--v2-bg);
    font-family: var(--v2-sans);
    position: relative;
  }
</style>

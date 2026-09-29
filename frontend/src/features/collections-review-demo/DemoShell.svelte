<script>
  import BackToTop from './BackToTop.svelte';

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
  <BackToTop />
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
    --v2-kept: #40b36a;
    --v2-kept-soft: #e8f3ec;
    --v2-removed: #c8362f;
    --v2-removed-soft: #f8e8e8;
    --v2-added: #2257e6;
    --v2-added-soft: #e8edfb;
    --v2-skipped: #6b7280;
    --v2-skipped-soft: #f0f1f3;
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
    --v2-text-caption: 0.875rem;
    --v2-text-secondary: 1.25rem;
    --v2-text-control: 1.0625rem;
    --v2-text-body: 1.25rem;
    --v2-text-heading: 1.375rem;

    /* Shell */
    min-height: 100vh;
    background: var(--v2-bg);
    font-family: var(--v2-sans);
    font-size: var(--v2-text-body);
    position: relative;
  }
</style>

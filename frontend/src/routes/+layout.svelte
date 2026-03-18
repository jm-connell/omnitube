<script lang="ts">
	import '../app.css';
	import { settingsStore } from '$lib/settings.svelte';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getStatus } from '$lib/api';

	let { children } = $props();
	let loaded = $state(false);
	let mobileMenuOpen = $state(false);

	onMount(async () => {
		settingsStore.applyTheme();

		// Check setup status — redirect to /setup if not complete
		try {
			const status = await getStatus();
			if (!status.setup_complete && !$page.url.pathname.startsWith('/setup')) {
				goto('/setup');
			}
		} catch {
			// Backend not available; still show the app
		}

		loaded = true;
	});

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}
</script>

{#if loaded}
	<div class="min-h-screen flex flex-col">
		<!-- Header -->
		<header class="sticky top-0 z-50 border-b border-omni-border bg-omni-surface/80 backdrop-blur-md">
			<div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
				<!-- Logo -->
				<a href="/" class="flex items-center gap-2 font-display text-lg font-semibold text-omni-accent hover:text-omni-accent-hover transition-colors">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<polygon points="5 3 19 12 5 21 5 3"/>
					</svg>
					OmniTube
				</a>

				<!-- Desktop Nav -->
				<nav class="hidden md:flex items-center gap-1">
					<a
						href="/"
						class="px-3 py-1.5 rounded-md text-sm font-mono transition-colors
							{$page.url.pathname === '/' ? 'bg-omni-accent/10 text-omni-accent' : 'text-omni-text-muted hover:text-omni-text hover:bg-omni-surface-hover'}"
					>
						feed
					</a>
					<a
						href="/channels"
						class="px-3 py-1.5 rounded-md text-sm font-mono transition-colors
							{$page.url.pathname === '/channels' ? 'bg-omni-accent/10 text-omni-accent' : 'text-omni-text-muted hover:text-omni-text hover:bg-omni-surface-hover'}"
					>
						channels
					</a>
					<a
						href="/settings"
						class="px-3 py-1.5 rounded-md text-sm font-mono transition-colors
							{$page.url.pathname === '/settings' ? 'bg-omni-accent/10 text-omni-accent' : 'text-omni-text-muted hover:text-omni-text hover:bg-omni-surface-hover'}"
					>
						settings
					</a>
				</nav>

				<!-- Mobile menu button -->
				<button
					class="md:hidden p-2 rounded-md text-omni-text-muted hover:text-omni-text hover:bg-omni-surface-hover transition-colors"
					onclick={toggleMobileMenu}
					aria-label="Toggle menu"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						{#if mobileMenuOpen}
							<line x1="18" y1="6" x2="6" y2="18"/>
							<line x1="6" y1="6" x2="18" y2="18"/>
						{:else}
							<line x1="4" y1="12" x2="20" y2="12"/>
							<line x1="4" y1="6" x2="20" y2="6"/>
							<line x1="4" y1="18" x2="20" y2="18"/>
						{/if}
					</svg>
				</button>
			</div>

			<!-- Mobile Nav -->
			{#if mobileMenuOpen}
				<nav class="md:hidden border-t border-omni-border bg-omni-surface px-4 py-2 animate-fade-in">
					<a
						href="/"
						class="block px-3 py-2 rounded-md text-sm font-mono transition-colors
							{$page.url.pathname === '/' ? 'bg-omni-accent/10 text-omni-accent' : 'text-omni-text-muted hover:text-omni-text'}"
						onclick={() => mobileMenuOpen = false}
					>
						feed
					</a>
					<a
						href="/channels"
						class="block px-3 py-2 rounded-md text-sm font-mono transition-colors
							{$page.url.pathname === '/channels' ? 'bg-omni-accent/10 text-omni-accent' : 'text-omni-text-muted hover:text-omni-text'}"
						onclick={() => mobileMenuOpen = false}
					>
						channels
					</a>
					<a
						href="/settings"
						class="block px-3 py-2 rounded-md text-sm font-mono transition-colors
							{$page.url.pathname === '/settings' ? 'bg-omni-accent/10 text-omni-accent' : 'text-omni-text-muted hover:text-omni-text'}"
						onclick={() => mobileMenuOpen = false}
					>
						settings
					</a>
				</nav>
			{/if}
		</header>

		<!-- Main content -->
		<main class="flex-1">
			{@render children()}
		</main>

		<!-- Footer -->
		<footer class="border-t border-omni-border py-4 text-center">
			<p class="text-xs font-mono text-omni-text-muted">omnitube v0.1.0</p>
		</footer>
	</div>
{:else}
	<!-- Loading state -->
	<div class="min-h-screen flex items-center justify-center bg-omni-bg">
		<div class="text-center">
			<div class="animate-pulse font-display text-2xl text-omni-accent">OmniTube</div>
			<p class="mt-2 text-sm text-omni-text-muted font-mono">loading...</p>
		</div>
	</div>
{/if}

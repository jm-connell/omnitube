<script lang="ts">
	import { settingsStore } from '$lib/settings.svelte';

	const settings = $derived(settingsStore.current);

	const accentColors = [
		{ id: 'sky', label: 'Sky', swatch: '#7dd3fc' },
		{ id: 'violet', label: 'Violet', swatch: '#c4b5fd' },
		{ id: 'emerald', label: 'Emerald', swatch: '#6ee7b7' },
		{ id: 'rose', label: 'Rose', swatch: '#fda4af' },
		{ id: 'amber', label: 'Amber', swatch: '#fcd34d' },
		{ id: 'cyan', label: 'Cyan', swatch: '#67e8f9' },
	] as const;

	function toggleTheme() {
		settingsStore.update({ theme: settings.theme === 'dark' ? 'light' : 'dark' });
	}

	function setAccent(color: typeof settings.accentColor) {
		settingsStore.update({ accentColor: color });
	}

	function toggle(key: keyof typeof settings) {
		settingsStore.update({ [key]: !settings[key] } as any);
	}
</script>

<svelte:head>
	<title>OmniTube — Settings</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-6">
	<h1 class="mb-8 font-display text-xl font-semibold text-omni-text">settings</h1>

	<!-- Theme Section -->
	<section class="mb-8">
		<h2 class="mb-4 text-xs font-mono font-semibold uppercase tracking-wider text-omni-text-muted">
			Appearance
		</h2>

		<div class="space-y-4 rounded-lg border border-omni-border bg-omni-surface p-4">
			<!-- Theme toggle -->
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-omni-text">Theme</p>
					<p class="text-xs text-omni-text-muted">Switch between dark and light mode</p>
				</div>
				<button
					class="rounded-full border border-omni-border bg-omni-bg px-4 py-1.5 text-xs font-mono text-omni-text
						hover:border-omni-accent transition-colors"
					onclick={toggleTheme}
				>
					{settings.theme === 'dark' ? '◑ dark' : '○ light'}
				</button>
			</div>

			<!-- Accent color -->
			<div>
				<p class="mb-2 text-sm font-medium text-omni-text">Accent Color</p>
				<div class="flex flex-wrap gap-2">
					{#each accentColors as color}
						<button
							class="flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all
								{settings.accentColor === color.id
									? 'border-omni-text scale-110'
									: 'border-transparent hover:border-omni-border'}"
							style="background-color: {color.swatch}"
							onclick={() => setAccent(color.id)}
							title={color.label}
						>
							{#if settings.accentColor === color.id}
								<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-omni-bg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
									<polyline points="20 6 9 17 4 12"/>
								</svg>
							{/if}
						</button>
					{/each}
				</div>
			</div>
		</div>
	</section>

	<!-- Feed Display Section -->
	<section class="mb-8">
		<h2 class="mb-4 text-xs font-mono font-semibold uppercase tracking-wider text-omni-text-muted">
			Feed Display
		</h2>

		<div class="space-y-1 rounded-lg border border-omni-border bg-omni-surface">
			<!-- Thumbnails -->
			<label class="flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-omni-surface-hover transition-colors">
				<div>
					<p class="text-sm font-medium text-omni-text">Thumbnails</p>
					<p class="text-xs text-omni-text-muted">Show video thumbnails in feed</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showThumbnails ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showThumbnails')}
					role="switch"
					aria-checked={settings.showThumbnails}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showThumbnails'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showThumbnails ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>

			<div class="border-t border-omni-border/50"></div>

			<!-- Descriptions -->
			<label class="flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-omni-surface-hover transition-colors">
				<div>
					<p class="text-sm font-medium text-omni-text">Descriptions</p>
					<p class="text-xs text-omni-text-muted">Show video descriptions in feed</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showDescriptions ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showDescriptions')}
					role="switch"
					aria-checked={settings.showDescriptions}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showDescriptions'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showDescriptions ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>

			<div class="border-t border-omni-border/50"></div>

			<!-- View count -->
			<label class="flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-omni-surface-hover transition-colors">
				<div>
					<p class="text-sm font-medium text-omni-text">View Count</p>
					<p class="text-xs text-omni-text-muted">Show view counts on video previews</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showViewCount ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showViewCount')}
					role="switch"
					aria-checked={settings.showViewCount}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showViewCount'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showViewCount ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>

			<div class="border-t border-omni-border/50"></div>

			<!-- Like count -->
			<label class="flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-omni-surface-hover transition-colors">
				<div>
					<p class="text-sm font-medium text-omni-text">Like Count</p>
					<p class="text-xs text-omni-text-muted">Show like counts on video previews</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showLikeCount ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showLikeCount')}
					role="switch"
					aria-checked={settings.showLikeCount}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showLikeCount'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showLikeCount ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>
		</div>
	</section>

	<!-- Data Management -->
	<section class="mb-8">
		<h2 class="mb-4 text-xs font-mono font-semibold uppercase tracking-wider text-omni-text-muted">
			Data
		</h2>

		<div class="space-y-3 rounded-lg border border-omni-border bg-omni-surface p-4">
			<a
				href="/setup"
				class="block rounded-md border border-omni-border px-4 py-2.5 text-center text-sm font-mono text-omni-text-muted
					hover:border-omni-accent hover:text-omni-accent transition-colors"
			>
				import more subscriptions
			</a>

			<button
				class="w-full rounded-md border border-omni-border px-4 py-2.5 text-sm font-mono text-omni-text-muted
					hover:border-omni-accent hover:text-omni-accent transition-colors"
				onclick={() => settingsStore.reset()}
			>
				reset settings to defaults
			</button>
		</div>
	</section>
</div>

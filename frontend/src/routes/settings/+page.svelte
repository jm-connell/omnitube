<script lang="ts">
	import { settingsStore, THEME_META, type ThemeName, type AccentColor } from '$lib/settings.svelte';

	const settings = $derived(settingsStore.current);

	const accentColors = [
		{ id: 'sky' as AccentColor, label: 'Sky', swatch: '#7dd3fc' },
		{ id: 'violet' as AccentColor, label: 'Violet', swatch: '#c4b5fd' },
		{ id: 'emerald' as AccentColor, label: 'Emerald', swatch: '#6ee7b7' },
		{ id: 'rose' as AccentColor, label: 'Rose', swatch: '#fda4af' },
		{ id: 'amber' as AccentColor, label: 'Amber', swatch: '#fcd34d' },
		{ id: 'cyan' as AccentColor, label: 'Cyan', swatch: '#67e8f9' },
	] as const;

	const themes = Object.entries(THEME_META) as [ThemeName, { label: string; description: string }][];

	const qualityOptions = [
		{ value: 0, label: 'Highest Available' },
		{ value: 2160, label: '4K (2160p)' },
		{ value: 1440, label: '1440p' },
		{ value: 1080, label: '1080p' },
		{ value: 720, label: '720p (recommended)' },
		{ value: 480, label: '480p' },
		{ value: 360, label: '360p' },
	];

	function setTheme(theme: ThemeName) {
		settingsStore.update({ theme });
	}

	function setAccent(color: AccentColor) {
		settingsStore.update({ accentColor: color });
	}

	function setCustomAccent(hex: string) {
		settingsStore.update({ accentColor: 'custom', customAccentColor: hex });
	}

	function addFavoriteColor() {
		const hex = settings.customAccentColor;
		if (hex && !settings.favoriteColors.includes(hex)) {
			settingsStore.update({ favoriteColors: [...settings.favoriteColors, hex] });
		}
	}

	function removeFavoriteColor(hex: string) {
		settingsStore.update({ favoriteColors: settings.favoriteColors.filter((c) => c !== hex) });
	}

	function toggle(key: keyof typeof settings) {
		settingsStore.update({ [key]: !settings[key] } as any);
	}

	let bgImageInput = $state('');

	function applyBackgroundImage() {
		if (bgImageInput.trim()) {
			settingsStore.update({ backgroundImage: bgImageInput.trim() });
		}
	}

	function clearBackgroundImage() {
		bgImageInput = '';
		settingsStore.update({ backgroundImage: '' });
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
			<!-- Theme grid -->
			<div>
				<p class="mb-3 text-sm font-medium text-omni-text">Theme</p>
				<div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
					{#each themes as [id, meta]}
						<button
							class="flex flex-col rounded-lg border px-3 py-2.5 text-left transition-all
								{settings.theme === id
									? 'border-omni-accent bg-omni-accent/10'
									: 'border-omni-border hover:border-omni-text-muted'}"
							onclick={() => setTheme(id)}
						>
							<span class="text-sm font-medium text-omni-text">{meta.label}</span>
							<span class="text-xs text-omni-text-muted">{meta.description}</span>
						</button>
					{/each}
				</div>
			</div>

			<!-- Background URL for translucent theme -->
			{#if settings.theme === 'translucent'}
				<div>
					<p class="mb-1 text-sm font-medium text-omni-text">Background Image URL</p>
					<p class="mb-2 text-xs text-omni-text-muted">Direct link to an image (png, jpg, webp)</p>
					<div class="flex gap-2">
						<input
							type="url"
							class="flex-1 rounded-md border border-omni-border bg-omni-bg px-3 py-1.5 text-sm text-omni-text placeholder:text-omni-text-muted/50 focus:border-omni-accent focus:outline-none"
							placeholder="https://example.com/wallpaper.jpg"
							bind:value={bgImageInput}
							onkeydown={(e) => { if (e.key === 'Enter') applyBackgroundImage(); }}
						/>
						<button
							class="rounded-md border border-omni-border px-3 py-1.5 text-xs font-mono text-omni-text hover:border-omni-accent transition-colors"
							onclick={applyBackgroundImage}
						>apply</button>
						{#if settings.backgroundImage}
							<button
								class="rounded-md border border-omni-border px-3 py-1.5 text-xs font-mono text-omni-text-muted hover:border-rose-400 hover:text-rose-400 transition-colors"
								onclick={clearBackgroundImage}
							>clear</button>
						{/if}
					</div>
				</div>

				<!-- Translucent glass controls -->
				<div class="space-y-3">
					<div>
						<div class="flex items-center justify-between mb-1">
							<p class="text-sm font-medium text-omni-text">Blur Amount</p>
							<span class="text-xs font-mono text-omni-text-muted">{settings.translucentBlur}px</span>
						</div>
						<input
							type="range"
							min="0" max="30" step="1"
							value={settings.translucentBlur}
							oninput={(e) => settingsStore.update({ translucentBlur: +e.currentTarget.value })}
							class="w-full accent-[var(--omni-accent)] h-1.5 rounded-full appearance-none bg-omni-border cursor-pointer"
						/>
					</div>

					<div>
						<div class="flex items-center justify-between mb-1">
							<p class="text-sm font-medium text-omni-text">Tint Opacity</p>
							<span class="text-xs font-mono text-omni-text-muted">{settings.translucentTint}%</span>
						</div>
						<input
							type="range"
							min="0" max="100" step="5"
							value={settings.translucentTint}
							oninput={(e) => settingsStore.update({ translucentTint: +e.currentTarget.value })}
							class="w-full accent-[var(--omni-accent)] h-1.5 rounded-full appearance-none bg-omni-border cursor-pointer"
						/>
					</div>

					<div>
						<p class="mb-2 text-sm font-medium text-omni-text">Tint Color</p>
						<div class="flex items-center gap-3">
							<div class="relative">
								<input
									type="color"
									class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
									value={settings.translucentTintColor}
									oninput={(e) => settingsStore.update({ translucentTintColor: e.currentTarget.value })}
								/>
								<div
									class="h-8 w-8 rounded-full border-2 border-omni-border pointer-events-none"
									style="background-color: {settings.translucentTintColor}"
								></div>
							</div>
							<span class="text-xs font-mono text-omni-text-muted">{settings.translucentTintColor}</span>
							<button
								class="rounded-md border border-omni-border px-2 py-1 text-[11px] font-mono text-omni-text-muted
									hover:border-omni-accent hover:text-omni-accent transition-colors"
								onclick={() => settingsStore.update({ translucentTintColor: '#0f172a' })}
							>reset</button>
						</div>
					</div>

					<div>
						<p class="mb-2 text-sm font-medium text-omni-text">Blur Mode</p>
						<div class="flex gap-2">
							<button
								class="rounded-md border px-3 py-1.5 text-xs font-mono transition-all
									{settings.translucentBlurMode === 'elements'
										? 'border-omni-accent bg-omni-accent/10 text-omni-accent'
										: 'border-omni-border text-omni-text-muted hover:border-omni-text-muted'}"
								onclick={() => settingsStore.update({ translucentBlurMode: 'elements' })}
							>
								Elements Only
							</button>
							<button
								class="rounded-md border px-3 py-1.5 text-xs font-mono transition-all
									{settings.translucentBlurMode === 'page'
										? 'border-omni-accent bg-omni-accent/10 text-omni-accent'
										: 'border-omni-border text-omni-text-muted hover:border-omni-text-muted'}"
								onclick={() => settingsStore.update({ translucentBlurMode: 'page' })}
							>
								Full Page
							</button>
						</div>
						<p class="mt-1 text-xs text-omni-text-muted">
							{settings.translucentBlurMode === 'elements'
								? 'Each card/panel gets its own glass blur effect'
								: 'Entire background is blurred behind all content'}
						</p>
					</div>
				</div>
			{/if}

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

					<!-- Favorite colors -->
					{#each settings.favoriteColors as fav}
						<div class="group relative">
							<button
								class="flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all
									{settings.accentColor === 'custom' && settings.customAccentColor === fav
										? 'border-omni-text scale-110'
										: 'border-transparent hover:border-omni-border'}"
								style="background-color: {fav}"
								onclick={() => setCustomAccent(fav)}
								title={fav}
							>
								{#if settings.accentColor === 'custom' && settings.customAccentColor === fav}
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-omni-bg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
										<polyline points="20 6 9 17 4 12"/>
									</svg>
								{/if}
							</button>
							<!-- Remove button on hover -->
							<button
								type="button"
								class="absolute -right-1 -top-1 hidden h-4 w-4 items-center justify-center rounded-full bg-omni-bg border border-omni-border text-[10px] text-omni-text-muted group-hover:flex cursor-pointer"
								onclick={() => removeFavoriteColor(fav)}
							>&times;</button>
						</div>
					{/each}

					<!-- Custom color picker -->
					<div class="relative flex h-8 w-8 items-center justify-center">
						<input
							type="color"
							class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
							value={settings.customAccentColor}
							oninput={(e) => setCustomAccent(e.currentTarget.value)}
							title="Pick custom color"
						/>
						<div
							class="flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all pointer-events-none
								{settings.accentColor === 'custom' && !settings.favoriteColors.includes(settings.customAccentColor)
									? 'border-omni-text scale-110'
									: 'border-dashed border-omni-border hover:border-omni-text-muted'}"
							style="background: conic-gradient(red, yellow, lime, aqua, blue, magenta, red)"
						>
						</div>
					</div>
				</div>

				<!-- Save to favorites -->
				{#if settings.accentColor === 'custom'}
					<button
						class="mt-2 rounded-md border border-omni-border px-2 py-1 text-[11px] font-mono text-omni-text-muted
							hover:border-omni-accent hover:text-omni-accent transition-colors
							disabled:opacity-30 disabled:cursor-not-allowed"
						onclick={addFavoriteColor}
						disabled={settings.favoriteColors.includes(settings.customAccentColor)}
					>
						{settings.favoriteColors.includes(settings.customAccentColor) ? 'saved' : '+ save color'}
					</button>
				{/if}
			</div>
		</div>
	</section>

	<!-- Video Playback Section -->
	<section class="mb-8">
		<h2 class="mb-4 text-xs font-mono font-semibold uppercase tracking-wider text-omni-text-muted">
			Video Playback
		</h2>

		<div class="space-y-4 rounded-lg border border-omni-border bg-omni-surface p-4">
			<!-- Default quality -->
			<div>
				<p class="mb-1 text-sm font-medium text-omni-text">Default Resolution</p>
				<p class="mb-2 text-xs text-omni-text-muted">
					Higher resolutions may buffer or fail due to YouTube throttling. 720p is the most reliable.
				</p>
				<div class="flex flex-wrap gap-2">
					{#each qualityOptions as opt}
						<button
							class="rounded-md border px-3 py-1.5 text-xs font-mono transition-all
								{settings.defaultQuality === opt.value
									? 'border-omni-accent bg-omni-accent/10 text-omni-accent'
									: 'border-omni-border text-omni-text-muted hover:border-omni-text-muted'}"
							onclick={() => settingsStore.update({ defaultQuality: opt.value })}
						>
							{opt.label}
						</button>
					{/each}
				</div>
			</div>

			<!-- Theater mode default -->
			<label class="flex cursor-pointer items-center justify-between hover:bg-omni-surface-hover transition-colors rounded-md px-1 py-2">
				<div>
					<p class="text-sm font-medium text-omni-text">Theater Mode Default</p>
					<p class="text-xs text-omni-text-muted">Open videos in theater mode by default</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.theaterMode ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('theaterMode')}
					role="switch"
					aria-checked={settings.theaterMode}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('theaterMode'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.theaterMode ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>

			<!-- Show description on watch page -->
			<label class="flex cursor-pointer items-center justify-between hover:bg-omni-surface-hover transition-colors rounded-md px-1 py-2">
				<div>
					<p class="text-sm font-medium text-omni-text">Video Description</p>
					<p class="text-xs text-omni-text-muted">Show description section on watch page</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showVideoDescription ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showVideoDescription')}
					role="switch"
					aria-checked={settings.showVideoDescription}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showVideoDescription'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showVideoDescription ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>

			<!-- Show comments on watch page -->
			<label class="flex cursor-pointer items-center justify-between hover:bg-omni-surface-hover transition-colors rounded-md px-1 py-2">
				<div>
					<p class="text-sm font-medium text-omni-text">Comments</p>
					<p class="text-xs text-omni-text-muted">Show comments section on watch page</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showVideoComments ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showVideoComments')}
					role="switch"
					aria-checked={settings.showVideoComments}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showVideoComments'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showVideoComments ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>
		</div>
	</section>

	<!-- Feed Display Section -->
	<section class="mb-8">
		<h2 class="mb-4 text-xs font-mono font-semibold uppercase tracking-wider text-omni-text-muted">
			Feed Display
		</h2>

		<div class="space-y-1 rounded-lg border border-omni-border bg-omni-surface">
			<!-- Livestreams -->
			<label class="flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-omni-surface-hover transition-colors">
				<div>
					<p class="text-sm font-medium text-omni-text">Livestreams</p>
					<p class="text-xs text-omni-text-muted">Show "Live Now" section on the feed page</p>
				</div>
				<div
					class="relative h-6 w-11 rounded-full transition-colors {settings.showLivestreams ? 'bg-omni-accent' : 'bg-omni-border'}"
					onclick={() => toggle('showLivestreams')}
					role="switch"
					aria-checked={settings.showLivestreams}
					tabindex="0"
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggle('showLivestreams'); }}
				>
					<div
						class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform
							{settings.showLivestreams ? 'translate-x-5' : 'translate-x-0.5'}"
					></div>
				</div>
			</label>

			<div class="border-t border-omni-border/50"></div>

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

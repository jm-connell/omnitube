<script lang="ts">
	import { goto } from '$app/navigation';
	import { importOPML, importChannels, addChannel, completeSetup, refreshFeed, type Channel } from '$lib/api';

	let step = $state<'welcome' | 'import' | 'manual' | 'done'>('welcome');
	let importMethod = $state<'opml' | 'manual' | null>(null);
	let opmlText = $state('');
	let manualInput = $state('');
	let importing = $state(false);
	let importError = $state('');
	let importedChannels = $state<Channel[]>([]);
	let refreshingFeed = $state(false);

	async function handleOPMLImport() {
		if (!opmlText.trim()) {
			importError = 'Paste your OPML/XML subscription export';
			return;
		}
		importing = true;
		importError = '';
		try {
			importedChannels = await importOPML(opmlText);
			step = 'done';
		} catch (e: any) {
			importError = e.message || 'Import failed';
		} finally {
			importing = false;
		}
	}

	async function handleManualImport() {
		if (!manualInput.trim()) {
			importError = 'Enter at least one channel ID or URL';
			return;
		}
		importing = true;
		importError = '';
		try {
			// Parse input: one channel per line, accept URLs or raw channel IDs
			const lines = manualInput
				.split('\n')
				.map((l) => l.trim())
				.filter(Boolean);

			const channels: Array<{ channel_id: string; name?: string }> = [];
			for (const line of lines) {
				channels.push({ channel_id: line });
			}

			importedChannels = await importChannels(channels);
			step = 'done';
		} catch (e: any) {
			importError = e.message || 'Import failed';
		} finally {
			importing = false;
		}
	}

	async function finishSetup() {
		refreshingFeed = true;
		try {
			await completeSetup();
			// Trigger initial feed refresh
			await refreshFeed();
		} catch {
			// Non-critical
		}
		goto('/');
	}

	function handleFileUpload(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		const reader = new FileReader();
		reader.onload = (e) => {
			opmlText = e.target?.result as string;
		};
		reader.readAsText(file);
	}

	function skipSetup() {
		completeSetup().then(() => goto('/'));
	}
</script>

<svelte:head>
	<title>OmniTube — Setup</title>
</svelte:head>

<div class="mx-auto max-w-lg px-4 py-12">
	<!-- Welcome -->
	{#if step === 'welcome'}
		<div class="text-center animate-fade-in">
			<div class="mb-8">
				<div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-2xl border border-omni-border bg-omni-surface">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-omni-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
						<polygon points="5 3 19 12 5 21 5 3"/>
					</svg>
				</div>
				<h1 class="font-display text-2xl font-bold text-omni-text">welcome to omnitube</h1>
				<p class="mt-2 text-sm text-omni-text-muted">
					A clean, distraction-free YouTube experience.<br />
					No algorithms. No ads. No shorts.
				</p>
			</div>

			<div class="space-y-3">
				<button
					class="w-full rounded-lg border border-omni-border bg-omni-surface px-4 py-4 text-left
						hover:border-omni-accent/40 hover:bg-omni-surface-hover transition-all"
					onclick={() => { importMethod = 'opml'; step = 'import'; }}
				>
					<div class="font-display text-sm font-semibold text-omni-text">import subscriptions</div>
					<p class="mt-1 text-xs text-omni-text-muted">
						Upload your YouTube subscription OPML export
					</p>
				</button>

				<button
					class="w-full rounded-lg border border-omni-border bg-omni-surface px-4 py-4 text-left
						hover:border-omni-accent/40 hover:bg-omni-surface-hover transition-all"
					onclick={() => { importMethod = 'manual'; step = 'manual'; }}
				>
					<div class="font-display text-sm font-semibold text-omni-text">add channels manually</div>
					<p class="mt-1 text-xs text-omni-text-muted">
						Paste channel IDs or YouTube channel URLs
					</p>
				</button>

				<button
					class="mt-4 text-xs font-mono text-omni-text-muted hover:text-omni-accent transition-colors"
					onclick={skipSetup}
				>
					skip for now →
				</button>
			</div>
		</div>

	<!-- OPML Import -->
	{:else if step === 'import'}
		<div class="animate-fade-in">
			<button
				class="mb-6 text-xs font-mono text-omni-text-muted hover:text-omni-accent transition-colors"
				onclick={() => step = 'welcome'}
			>
				← back
			</button>

			<h2 class="font-display text-xl font-bold text-omni-text">import subscriptions</h2>
			<p class="mt-2 text-sm text-omni-text-muted">
				Export your subscriptions from
				<a href="https://takeout.google.com/takeout/custom/youtube" target="_blank" rel="noopener"
					class="text-omni-accent hover:text-omni-accent-hover underline">
					Google Takeout
				</a>.
				Select only "subscriptions" → choose OPML format → download and upload here.
			</p>

			<div class="mt-6 space-y-4">
				<!-- File upload -->
				<label
					class="flex cursor-pointer flex-col items-center rounded-lg border-2 border-dashed border-omni-border
						bg-omni-surface px-4 py-8 hover:border-omni-accent/40 transition-colors"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="mb-2 h-8 w-8 text-omni-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
						<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
						<polyline points="17 8 12 3 7 8"/>
						<line x1="12" y1="3" x2="12" y2="15"/>
					</svg>
					<span class="text-sm font-mono text-omni-text-muted">
						{opmlText ? 'file loaded ✓' : 'click to upload .xml / .opml'}
					</span>
					<input type="file" accept=".xml,.opml" class="hidden" onchange={handleFileUpload} />
				</label>

				<div class="text-center text-xs font-mono text-omni-text-muted">or paste XML below</div>

				<textarea
					bind:value={opmlText}
					placeholder="Paste your OPML/XML content here..."
					rows="6"
					class="w-full rounded-lg border border-omni-border bg-omni-surface px-4 py-3 font-mono text-sm
						text-omni-text placeholder:text-omni-text-muted/40
						focus:border-omni-accent focus:outline-none transition-colors resize-none"
				></textarea>

				{#if importError}
					<p class="text-sm font-mono text-rose-400">{importError}</p>
				{/if}

				<button
					class="w-full rounded-lg bg-omni-accent px-4 py-3 font-display text-sm font-semibold text-omni-bg
						hover:bg-omni-accent-hover transition-colors disabled:opacity-50"
					onclick={handleOPMLImport}
					disabled={importing}
				>
					{importing ? 'importing...' : 'import subscriptions'}
				</button>
			</div>
		</div>

	<!-- Manual Import -->
	{:else if step === 'manual'}
		<div class="animate-fade-in">
			<button
				class="mb-6 text-xs font-mono text-omni-text-muted hover:text-omni-accent transition-colors"
				onclick={() => step = 'welcome'}
			>
				← back
			</button>

			<h2 class="font-display text-xl font-bold text-omni-text">add channels</h2>
			<p class="mt-2 text-sm text-omni-text-muted">
				Enter YouTube channel IDs or URLs, one per line.
			</p>

			<div class="mt-6 space-y-4">
				<textarea
					bind:value={manualInput}
					placeholder={"UCxxxxxxxxxxxxxxxxxxxxxx\nhttps://youtube.com/channel/UCxxxxxx\n..."}
					rows="8"
					class="w-full rounded-lg border border-omni-border bg-omni-surface px-4 py-3 font-mono text-sm
						text-omni-text placeholder:text-omni-text-muted/40
						focus:border-omni-accent focus:outline-none transition-colors resize-none"
				></textarea>

				{#if importError}
					<p class="text-sm font-mono text-rose-400">{importError}</p>
				{/if}

				<button
					class="w-full rounded-lg bg-omni-accent px-4 py-3 font-display text-sm font-semibold text-omni-bg
						hover:bg-omni-accent-hover transition-colors disabled:opacity-50"
					onclick={handleManualImport}
					disabled={importing}
				>
					{importing ? 'adding...' : 'add channels'}
				</button>
			</div>
		</div>

	<!-- Done -->
	{:else if step === 'done'}
		<div class="text-center animate-fade-in">
			<div class="mb-6">
				<div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/10">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<polyline points="20 6 9 17 4 12"/>
					</svg>
				</div>
				<h2 class="font-display text-xl font-bold text-omni-text">you're all set</h2>
				<p class="mt-2 text-sm text-omni-text-muted">
					{importedChannels.length} channel{importedChannels.length !== 1 ? 's' : ''} imported.
					Your feed is being built now.
				</p>
			</div>

			{#if importedChannels.length > 0}
				<div class="mb-6 max-h-48 overflow-y-auto rounded-lg border border-omni-border bg-omni-surface p-3 text-left">
					{#each importedChannels as ch}
						<div class="py-1 text-xs font-mono text-omni-text-muted">
							{ch.name}
						</div>
					{/each}
				</div>
			{/if}

			<button
				class="w-full rounded-lg bg-omni-accent px-4 py-3 font-display text-sm font-semibold text-omni-bg
					hover:bg-omni-accent-hover transition-colors disabled:opacity-50"
				onclick={finishSetup}
				disabled={refreshingFeed}
			>
				{refreshingFeed ? 'building feed...' : 'start watching →'}
			</button>
		</div>
	{/if}
</div>

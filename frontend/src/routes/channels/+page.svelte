<script lang="ts">
	import { onMount } from 'svelte';
	import { getChannels, addChannel, removeChannel, type Channel } from '$lib/api';

	let channels = $state<Channel[]>([]);
	let loading = $state(true);
	let error = $state('');

	let showAddForm = $state(false);
	let newChannelId = $state('');
	let newChannelName = $state('');
	let adding = $state(false);
	let addError = $state('');

	let confirmDelete = $state<string | null>(null);

	async function loadChannels() {
		loading = true;
		try {
			channels = await getChannels();
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	async function handleAdd() {
		if (!newChannelId.trim()) return;
		adding = true;
		addError = '';
		try {
			let channelId = newChannelId.trim();
			const ch = await addChannel(channelId, newChannelName.trim() || undefined);
			channels = [...channels, ch].sort((a, b) => a.name.localeCompare(b.name));
			newChannelId = '';
			newChannelName = '';
			showAddForm = false;
		} catch (e: any) {
			addError = e.message || 'Failed to add channel';
		} finally {
			adding = false;
		}
	}

	async function handleRemove(channelId: string) {
		try {
			await removeChannel(channelId);
			channels = channels.filter((c) => c.channel_id !== channelId);
			confirmDelete = null;
		} catch (e: any) {
			error = e.message;
		}
	}

	onMount(loadChannels);
</script>

<svelte:head>
	<title>OmniTube — Channels</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-6">
	<div class="mb-6 flex items-center justify-between">
		<h1 class="font-display text-xl font-semibold text-omni-text">channels</h1>
		<div class="flex items-center gap-3">
			<span class="text-xs font-mono text-omni-text-muted">{channels.length} subscribed</span>
			<button
				class="rounded-md border border-omni-border bg-omni-surface px-3 py-1.5 text-xs font-mono
					text-omni-accent hover:border-omni-accent hover:bg-omni-surface-hover transition-colors"
				onclick={() => showAddForm = !showAddForm}
			>
				{showAddForm ? 'cancel' : '+ add'}
			</button>
		</div>
	</div>

	<!-- Add channel form -->
	{#if showAddForm}
		<div class="mb-6 rounded-lg border border-omni-accent/20 bg-omni-surface p-4 animate-slide-up">
			<div class="space-y-3">
				<div>
					<label for="channel-id" class="mb-1 block text-xs font-mono text-omni-text-muted">channel ID or URL</label>
					<input
						id="channel-id"
						bind:value={newChannelId}
						placeholder="UCxxxxxx or https://youtube.com/channel/..."
						class="w-full rounded-md border border-omni-border bg-omni-bg px-3 py-2 font-mono text-sm text-omni-text
							placeholder:text-omni-text-muted/40 focus:border-omni-accent focus:outline-none transition-colors"
					/>
				</div>
				<div>
					<label for="channel-name" class="mb-1 block text-xs font-mono text-omni-text-muted">name (optional)</label>
					<input
						id="channel-name"
						bind:value={newChannelName}
						placeholder="Channel display name"
						class="w-full rounded-md border border-omni-border bg-omni-bg px-3 py-2 font-mono text-sm text-omni-text
							placeholder:text-omni-text-muted/40 focus:border-omni-accent focus:outline-none transition-colors"
					/>
				</div>

				{#if addError}
					<p class="text-xs font-mono text-rose-400">{addError}</p>
				{/if}

				<button
					class="rounded-md bg-omni-accent px-4 py-2 text-xs font-display font-semibold text-omni-bg
						hover:bg-omni-accent-hover transition-colors disabled:opacity-50"
					onclick={handleAdd}
					disabled={adding}
				>
					{adding ? 'adding...' : 'add channel'}
				</button>
			</div>
		</div>
	{/if}

	{#if error}
		<div class="mb-4 rounded-md border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-400 font-mono">
			{error}
		</div>
	{/if}

	{#if loading}
		<div class="space-y-2">
			{#each Array(8) as _}
				<div class="animate-pulse rounded-lg border border-omni-border bg-omni-surface p-3">
					<div class="h-4 w-1/3 rounded bg-omni-surface-hover"></div>
				</div>
			{/each}
		</div>
	{:else if channels.length === 0}
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<p class="font-display text-lg text-omni-text-muted">no channels yet</p>
			<p class="mt-1 text-sm text-omni-text-muted/60">
				Add channels or <a href="/setup" class="text-omni-accent hover:underline">import your subscriptions</a>.
			</p>
		</div>
	{:else}
		<div class="space-y-1">
			{#each channels as ch (ch.channel_id)}
				<div
					class="group flex items-center justify-between rounded-lg border border-omni-border bg-omni-surface px-4 py-3
						hover:border-omni-accent/20 hover:bg-omni-surface-hover transition-all"
				>
					<div class="min-w-0 flex-1">
						<a
							href="/?channel={ch.channel_id}"
							class="text-sm font-medium text-omni-text hover:text-omni-accent transition-colors"
						>
							{ch.name}
						</a>
						<p class="mt-0.5 truncate text-[11px] font-mono text-omni-text-muted/50">
							{ch.channel_id}
						</p>
					</div>

					<div class="ml-4 shrink-0">
						{#if confirmDelete === ch.channel_id}
							<div class="flex items-center gap-2">
								<button
									class="rounded px-2 py-1 text-xs font-mono text-rose-400 hover:bg-rose-500/10 transition-colors"
									onclick={() => handleRemove(ch.channel_id)}
								>
									confirm
								</button>
								<button
									class="rounded px-2 py-1 text-xs font-mono text-omni-text-muted hover:bg-omni-surface-hover transition-colors"
									onclick={() => confirmDelete = null}
								>
									cancel
								</button>
							</div>
						{:else}
							<button
								class="rounded px-2 py-1 text-xs font-mono text-omni-text-muted/40
									opacity-0 group-hover:opacity-100 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
								onclick={() => confirmDelete = ch.channel_id}
							>
								remove
							</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

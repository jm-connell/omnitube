<script lang="ts">
	import { onMount } from 'svelte';
	import { getFeed, refreshFeed, type Video } from '$lib/api';
	import { settingsStore } from '$lib/settings.svelte';
	import { timeAgo, formatCount } from '$lib/utils';

	let videos = $state<Video[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let refreshing = $state(false);
	let page = $state(1);
	let total = $state(0);
	let error = $state('');

	const perPage = 30;
	let hasMore = $derived(videos.length < total);

	async function loadFeed(pageNum = 1, append = false) {
		try {
			if (append) {
				loadingMore = true;
			} else {
				loading = true;
			}
			error = '';

			const res = await getFeed(pageNum, perPage);
			if (append) {
				videos = [...videos, ...res.videos];
			} else {
				videos = res.videos;
			}
			total = res.total;
			page = pageNum;
		} catch (e: any) {
			error = e.message || 'Failed to load feed';
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	async function handleRefresh() {
		refreshing = true;
		try {
			await refreshFeed();
			// Reset to page 1 to show newest content
			page = 1;
			await loadFeed(1);
		} catch (e: any) {
			error = e.message || 'Refresh failed';
		} finally {
			refreshing = false;
		}
	}

	function loadMore() {
		if (!loadingMore && hasMore) {
			loadFeed(page + 1, true);
		}
	}

	// Intersection observer for infinite scroll — uses $effect to
	// react to the sentinel element appearing/disappearing in the DOM
	let sentinel: HTMLDivElement;
	let observer: IntersectionObserver | null = null;

	$effect(() => {
		// Clean up previous observer
		observer?.disconnect();

		if (sentinel) {
			observer = new IntersectionObserver(
				(entries) => {
					if (entries[0].isIntersecting && !loadingMore) {
						loadMore();
					}
				},
				{ rootMargin: '400px' }
			);
			observer.observe(sentinel);
		}

		return () => observer?.disconnect();
	});

	onMount(() => {
		loadFeed();
	});

	const settings = $derived(settingsStore.current);
</script>

<svelte:head>
	<title>OmniTube — Feed</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-6">
	<!-- Header -->
	<div class="mb-6 flex items-center justify-between">
		<h1 class="font-display text-xl font-semibold text-omni-text">
			feed
		</h1>
		<div class="flex items-center gap-3">
			<span class="text-xs font-mono text-omni-text-muted">
				{total} videos
			</span>
			<button
				class="rounded-md border border-omni-border bg-omni-surface px-3 py-1.5 text-xs font-mono text-omni-text-muted
					hover:border-omni-accent hover:text-omni-accent transition-colors disabled:opacity-50"
				onclick={handleRefresh}
				disabled={refreshing}
			>
				{refreshing ? 'refreshing...' : 'refresh'}
			</button>
		</div>
	</div>

	<!-- Error -->
	{#if error}
		<div class="mb-4 rounded-md border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-400 font-mono">
			{error}
		</div>
	{/if}

	<!-- Loading state -->
	{#if loading}
		<div class="space-y-4">
			{#each Array(5) as _}
				<div class="animate-pulse rounded-lg border border-omni-border bg-omni-surface p-4">
					<div class="flex gap-4">
						{#if settings.showThumbnails}
							<div class="h-24 w-40 shrink-0 rounded-md bg-omni-surface-hover"></div>
						{/if}
						<div class="flex-1 space-y-2">
							<div class="h-4 w-3/4 rounded bg-omni-surface-hover"></div>
							<div class="h-3 w-1/2 rounded bg-omni-surface-hover"></div>
							<div class="h-3 w-1/4 rounded bg-omni-surface-hover"></div>
						</div>
					</div>
				</div>
			{/each}
		</div>

	<!-- Empty state -->
	{:else if videos.length === 0}
		<div class="flex flex-col items-center justify-center py-20 text-center">
			<svg xmlns="http://www.w3.org/2000/svg" class="mb-4 h-16 w-16 text-omni-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
				<rect x="2" y="2" width="20" height="20" rx="2"/>
				<path d="m10 8 6 4-6 4z"/>
			</svg>
			<h2 class="font-display text-lg text-omni-text-muted">no videos yet</h2>
			<p class="mt-1 text-sm text-omni-text-muted/60">
				Add some channels to start seeing videos in your feed.
			</p>
			<a
				href="/setup"
				class="mt-4 rounded-md bg-omni-accent px-4 py-2 text-sm font-mono font-medium text-omni-bg
					hover:bg-omni-accent-hover transition-colors"
			>
				import subscriptions
			</a>
		</div>

	<!-- Video list -->
	{:else}
		<div class="space-y-3">
			{#each videos as video (video.video_id)}
				<a
					href="/watch/{video.video_id}"
					class="group flex gap-4 rounded-lg border border-omni-border bg-omni-surface p-3
						hover:border-omni-accent/30 hover:bg-omni-surface-hover transition-all animate-fade-in"
				>
					<!-- Thumbnail -->
					{#if settings.showThumbnails && video.thumbnail_url}
						<div class="relative h-24 w-40 shrink-0 overflow-hidden rounded-md bg-omni-bg">
							<img
								src={video.thumbnail_url}
								alt=""
								class="h-full w-full object-cover transition-transform group-hover:scale-105"
								loading="lazy"
							/>
							{#if video.duration_seconds}
								<span class="absolute bottom-1 right-1 rounded bg-black/80 px-1.5 py-0.5 text-[10px] font-mono text-white">
									{formatCount(video.duration_seconds)}
								</span>
							{/if}
						</div>
					{/if}

					<!-- Info -->
					<div class="flex min-w-0 flex-1 flex-col justify-between py-0.5">
						<div>
							<h3 class="line-clamp-2 text-sm font-medium leading-snug text-omni-text group-hover:text-omni-accent transition-colors">
								{video.title}
							</h3>
							<p class="mt-1 text-xs font-mono text-omni-text-muted">
								{video.channel_name || video.channel_id}
							</p>
						</div>

						<div class="flex items-center gap-3 text-[11px] font-mono text-omni-text-muted/70">
							<span>{timeAgo(video.published_at)}</span>
							{#if settings.showViewCount && video.view_count}
								<span>{formatCount(video.view_count)} views</span>
							{/if}
							{#if settings.showLikeCount && video.like_count}
								<span>{formatCount(video.like_count)} likes</span>
							{/if}
						</div>

						{#if settings.showDescriptions && video.description}
							<p class="mt-1 line-clamp-2 text-xs text-omni-text-muted/60">
								{video.description}
							</p>
						{/if}
					</div>
				</a>
			{/each}
		</div>

		<!-- Loading more indicator -->
		{#if loadingMore}
			<div class="flex justify-center py-6">
				<span class="text-sm font-mono text-omni-text-muted animate-pulse">loading more...</span>
			</div>
		{/if}

		<!-- Infinite scroll sentinel -->
		<div bind:this={sentinel} class="h-1"></div>
	{/if}
</div>

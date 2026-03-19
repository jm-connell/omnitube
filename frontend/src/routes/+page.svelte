<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getFeed, refreshFeed, getLivestreams, type Video, type LivestreamInfo } from '$lib/api';
	import { settingsStore } from '$lib/settings.svelte';
	import { timeAgo, formatCount, formatDuration } from '$lib/utils';

	let videos = $state<Video[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let refreshing = $state(false);
	let currentPage = $state(1);
	let total = $state(0);
	let error = $state('');

	// Livestreams
	let livestreams = $state<LivestreamInfo[]>([]);
	let livestreamsOpen = $state(true);
	let livestreamsLoading = $state(false);
	let livestreamsChecked = $state(false);

	const perPage = 30;
	let hasMore = $derived(videos.length < total);
	let channelFilter = $derived($page.url.searchParams.get('channel'));

	async function loadFeed(pageNum = 1, append = false) {
		try {
			if (append) {
				loadingMore = true;
			} else {
				loading = true;
			}
			error = '';

			const res = await getFeed(pageNum, perPage, channelFilter || undefined);
			if (append) {
				videos = [...videos, ...res.videos];
			} else {
				videos = res.videos;
			}
			total = res.total;
			currentPage = pageNum;
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
			currentPage = 1;
			await loadFeed(1);
			if (settings.showLivestreams) loadLivestreams();
		} catch (e: any) {
			error = e.message || 'Refresh failed';
		} finally {
			refreshing = false;
		}
	}

	async function loadLivestreams() {
		livestreamsLoading = true;
		try {
			livestreams = await getLivestreams();
		} catch {
			// Silently fail — livestreams are optional
		} finally {
			livestreamsLoading = false;
			livestreamsChecked = true;
		}
	}

	function loadMore() {
		if (!loadingMore && hasMore) {
			loadFeed(currentPage + 1, true);
		}
	}

	// Intersection observer for infinite scroll — uses $effect to
	// react to the sentinel element appearing/disappearing in the DOM
	let sentinel = $state<HTMLDivElement | null>(null);
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
		if (settingsStore.current.showLivestreams) loadLivestreams();
	});

	// Reload when channel filter changes via URL navigation
	let prevChannelFilter: string | null | undefined;
	$effect(() => {
		const ch = channelFilter;
		if (prevChannelFilter !== undefined && ch !== prevChannelFilter) {
			currentPage = 1;
			loadFeed(1);
		}
		prevChannelFilter = ch;
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
			{#if channelFilter}
				<a
					href="/"
					class="rounded-md border border-omni-accent/30 bg-omni-accent/10 px-2 py-1 text-xs font-mono text-omni-accent
						hover:bg-omni-accent/20 transition-colors"
				>
					filtered &times; clear
				</a>
			{/if}
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

	<!-- Live Now Section -->
	{#if settings.showLivestreams && (livestreams.length > 0 || (livestreamsLoading && !livestreamsChecked))}
		<div class="mb-6">
			<button
				class="mb-3 flex w-full items-center gap-2 text-left"
				onclick={() => livestreamsOpen = !livestreamsOpen}
			>
				<span class="relative flex h-2.5 w-2.5">
					<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75"></span>
					<span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500"></span>
				</span>
				<span class="text-sm font-mono font-semibold text-omni-text">
					live now
				</span>
				<span class="text-xs font-mono text-omni-text-muted">({livestreams.length})</span>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="ml-auto h-4 w-4 text-omni-text-muted transition-transform {livestreamsOpen ? 'rotate-180' : ''}"
					viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
					stroke-linecap="round" stroke-linejoin="round"
				>
					<polyline points="6 9 12 15 18 9"/>
				</svg>
			</button>

			{#if livestreamsOpen}
				{#if livestreamsLoading && livestreams.length === 0}
					<div class="flex gap-3 overflow-x-auto pb-2">
						{#each Array(3) as _}
							<div class="w-56 shrink-0 animate-pulse rounded-lg border border-omni-border bg-omni-surface p-3">
								<div class="aspect-video w-full rounded-md bg-omni-surface-hover mb-2"></div>
								<div class="h-3 w-3/4 rounded bg-omni-surface-hover"></div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="flex gap-3 overflow-x-auto pb-2">
						{#each livestreams as stream (stream.video_id)}
							<a
								href="/watch/{stream.video_id}"
								class="group w-56 shrink-0 rounded-lg border border-omni-border bg-omni-surface p-3
									hover:border-red-500/30 hover:bg-omni-surface-hover transition-all"
							>
								{#if stream.thumbnail_url}
									<div class="relative mb-2 aspect-video w-full overflow-hidden rounded-md bg-omni-bg">
										<img
											src={stream.thumbnail_url}
											alt=""
											class="h-full w-full object-cover transition-transform group-hover:scale-105"
											loading="lazy"
										/>
										<span class="absolute bottom-1 left-1 flex items-center gap-1 rounded bg-red-600/90 px-1.5 py-0.5 text-[10px] font-mono font-bold text-white uppercase">
											<span class="h-1.5 w-1.5 rounded-full bg-white animate-pulse"></span>
											live
										</span>
									</div>
								{/if}
								<h3 class="line-clamp-2 text-xs font-mono font-medium text-omni-text group-hover:text-red-400 transition-colors leading-snug">
									{stream.title}
								</h3>
								<p class="mt-1 text-[11px] font-mono text-omni-text-muted truncate">
									{stream.channel_name}
								</p>
							</a>
						{/each}
					</div>
				{/if}
			{/if}
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
						<div class="relative w-40 shrink-0 overflow-hidden rounded-md bg-omni-bg aspect-video">
							<img
								src={video.thumbnail_url.replace('/hqdefault.jpg', '/mqdefault.jpg')}
								alt=""
								class="h-full w-full object-cover transition-transform group-hover:scale-105"
								loading="lazy"
							/>
							{#if video.duration_seconds}
								<span class="absolute bottom-1 right-1 rounded bg-black/80 px-1.5 py-0.5 text-[10px] font-mono text-white">
									{formatDuration(video.duration_seconds)}
								</span>
							{/if}
						</div>
					{/if}

					<!-- Info -->
					<div class="flex min-w-0 flex-1 flex-col justify-between py-0.5">
						<div>
							<h3 class="line-clamp-2 text-sm font-mono font-medium leading-snug text-omni-text group-hover:text-omni-accent transition-colors">
								{video.title}
							</h3>
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<span
								class="mt-1 inline-block text-xs font-mono text-omni-accent hover:underline transition-colors cursor-pointer"
								onclick={(e) => {
									e.preventDefault();
									e.stopPropagation();
									goto(`/?channel=${video.channel_id}`);
								}}
								onkeydown={(e) => {
									if (e.key === 'Enter') {
										e.preventDefault();
										e.stopPropagation();
										goto(`/?channel=${video.channel_id}`);
									}
								}}
							>
								{video.channel_name || video.channel_id}
							</span>
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

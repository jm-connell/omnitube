<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { getStreamInfo, type StreamInfo } from '$lib/api';
	import { settingsStore } from '$lib/settings.svelte';
	import { formatCount, formatDuration } from '$lib/utils';

	let streamInfo = $state<StreamInfo | null>(null);
	let loading = $state(true);
	let error = $state('');
	let videoEl: HTMLVideoElement;
	let audioEl: HTMLAudioElement;
	let showDescription = $state(false);

	$effect(() => {
		const videoId = $page.params.id;
		if (videoId) {
			loadVideo(videoId);
		}
	});

	async function loadVideo(videoId: string) {
		loading = true;
		error = '';
		try {
			streamInfo = await getStreamInfo(videoId);
		} catch (e: any) {
			error = e.message || 'Failed to load video';
		} finally {
			loading = false;
		}
	}

	/**
	 * Synchronize audio with video for separate streams (DASH).
	 */
	function syncAudio() {
		if (!audioEl || !videoEl) return;

		videoEl.addEventListener('play', () => {
			audioEl.currentTime = videoEl.currentTime;
			audioEl.play();
		});
		videoEl.addEventListener('pause', () => audioEl.pause());
		videoEl.addEventListener('seeked', () => {
			audioEl.currentTime = videoEl.currentTime;
		});
		videoEl.addEventListener('ratechange', () => {
			audioEl.playbackRate = videoEl.playbackRate;
		});
	}

	onMount(() => {
		return () => {
			// Cleanup
			if (audioEl) {
				audioEl.pause();
				audioEl.src = '';
			}
		};
	});

	const settings = $derived(settingsStore.current);
</script>

<svelte:head>
	<title>{streamInfo?.title || 'Loading...'} — OmniTube</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-6">
	<!-- Back link -->
	<a
		href="/"
		class="mb-4 inline-flex items-center gap-1.5 text-xs font-mono text-omni-text-muted hover:text-omni-accent transition-colors"
	>
		<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<polyline points="15 18 9 12 15 6"/>
		</svg>
		back to feed
	</a>

	{#if loading}
		<!-- Loading skeleton -->
		<div class="animate-pulse space-y-4">
			<div class="aspect-video w-full rounded-lg bg-omni-surface"></div>
			<div class="h-6 w-3/4 rounded bg-omni-surface"></div>
			<div class="h-4 w-1/3 rounded bg-omni-surface"></div>
		</div>
	{:else if error}
		<div class="flex flex-col items-center justify-center py-20 text-center">
			<div class="rounded-md border border-rose-500/30 bg-rose-500/10 px-6 py-4">
				<p class="text-sm font-mono text-rose-400">{error}</p>
			</div>
			<a href="/" class="mt-4 text-sm font-mono text-omni-accent hover:text-omni-accent-hover transition-colors">
				← back to feed
			</a>
		</div>
	{:else if streamInfo}
		<!-- Video Player -->
		<div class="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
			<video
				bind:this={videoEl}
				class="h-full w-full"
				controls
				autoplay
				playsinline
				src={streamInfo.video_url}
				onloadeddata={() => {
					if (streamInfo?.audio_url) {
						syncAudio();
					}
				}}
			>
				<track kind="captions" />
			</video>

			<!-- Hidden audio element for separate audio stream -->
			{#if streamInfo.audio_url}
				<audio
					bind:this={audioEl}
					src={streamInfo.audio_url}
					preload="auto"
				></audio>
			{/if}
		</div>

		<!-- Video Info -->
		<div class="mt-4 space-y-3">
			<h1 class="text-lg font-semibold leading-snug text-omni-text">
				{streamInfo.title}
			</h1>

			<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-omni-text-muted">
				{#if streamInfo.channel}
					<span class="text-omni-accent">{streamInfo.channel}</span>
				{/if}
				{#if streamInfo.duration}
					<span>{formatDuration(streamInfo.duration)}</span>
				{/if}
				{#if settings.showViewCount && streamInfo.view_count}
					<span>{formatCount(streamInfo.view_count)} views</span>
				{/if}
				{#if settings.showLikeCount && streamInfo.like_count}
					<span>{formatCount(streamInfo.like_count)} likes</span>
				{/if}
			</div>

			<!-- Chapters -->
			{#if streamInfo.chapters && streamInfo.chapters.length > 0}
				<div class="rounded-lg border border-omni-border bg-omni-surface p-3">
					<h3 class="mb-2 text-xs font-mono font-semibold text-omni-text-muted uppercase tracking-wider">
						Chapters
					</h3>
					<div class="space-y-1">
						{#each streamInfo.chapters as chapter}
							<button
								class="flex w-full items-center gap-3 rounded px-2 py-1 text-left text-sm text-omni-text-muted
									hover:bg-omni-surface-hover hover:text-omni-text transition-colors"
								onclick={() => {
									if (videoEl) {
										videoEl.currentTime = chapter.start_time;
										if (audioEl) audioEl.currentTime = chapter.start_time;
									}
								}}
							>
								<span class="shrink-0 font-mono text-xs text-omni-accent">
									{formatDuration(chapter.start_time)}
								</span>
								<span class="truncate">{chapter.title}</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Description -->
			{#if streamInfo.description}
				<div class="rounded-lg border border-omni-border bg-omni-surface">
					<button
						class="flex w-full items-center justify-between px-4 py-3 text-left text-xs font-mono text-omni-text-muted
							hover:text-omni-text transition-colors"
						onclick={() => showDescription = !showDescription}
					>
						<span>description</span>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-4 w-4 transition-transform {showDescription ? 'rotate-180' : ''}"
							viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
						>
							<polyline points="6 9 12 15 18 9"/>
						</svg>
					</button>
					{#if showDescription}
						<div class="border-t border-omni-border px-4 py-3 animate-fade-in">
							<pre class="whitespace-pre-wrap text-sm font-mono text-omni-text-muted leading-relaxed">
								{streamInfo.description}
							</pre>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</div>

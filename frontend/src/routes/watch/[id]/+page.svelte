<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores';
	import { getStreamInfo, type StreamInfo } from '$lib/api';
	import { settingsStore } from '$lib/settings.svelte';
	import { formatCount, formatDuration } from '$lib/utils';

	let streamInfo = $state<StreamInfo | null>(null);
	let loading = $state(true);
	let error = $state('');
	let videoEl = $state<HTMLVideoElement>();
	let audioEl = $state<HTMLAudioElement>();
	let showDescription = $state(false);
	let theaterMode = $state(false);
	let selectedQuality = $state(1440);
	let changingQuality = $state(false);

	$effect(() => {
		const videoId = $page.params.id;
		if (videoId) {
			loadVideo(videoId);
		}
	});

	async function loadVideo(videoId: string, quality?: number) {
		if (!quality) {
			loading = true;
		}
		error = '';
		try {
			streamInfo = await getStreamInfo(videoId, quality || selectedQuality);
			if (streamInfo.available_qualities?.length && !quality) {
				if (!streamInfo.available_qualities.includes(selectedQuality)) {
					selectedQuality = streamInfo.available_qualities[0];
				}
			}
		} catch (e: any) {
			error = e.message || 'Failed to load video';
		} finally {
			loading = false;
			changingQuality = false;
		}
	}

	async function changeQuality(quality: number) {
		if (quality === selectedQuality || !streamInfo) return;
		const currentTime = videoEl?.currentTime || 0;
		const wasPlaying = videoEl && !videoEl.paused;
		selectedQuality = quality;
		changingQuality = true;
		const videoId = $page.params.id;
		if (videoId) {
			await loadVideo(videoId, quality);
			await tick();
			if (videoEl) {
				videoEl.currentTime = currentTime;
				if (wasPlaying) videoEl.play();
			}
			if (audioEl) {
				audioEl.currentTime = currentTime;
				if (wasPlaying) audioEl.play();
			}
		}
	}

	function syncAudio() {
		if (!audioEl || !videoEl) return;
		const audio = audioEl;
		const video = videoEl;
		if (!video.paused) {
			audio.currentTime = video.currentTime;
			audio.play();
		}
		video.addEventListener('play', () => {
			audio.currentTime = video.currentTime;
			audio.play();
		});
		video.addEventListener('pause', () => audio.pause());
		video.addEventListener('seeked', () => {
			audio.currentTime = video.currentTime;
		});
		video.addEventListener('ratechange', () => {
			audio.playbackRate = video.playbackRate;
		});
	}

	function linkifyDescription(text: string): string {
		const escaped = text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;');
		return escaped.replace(
			/(https?:\/\/[^\s<]+)/g,
			'<a href="$1" target="_blank" rel="noopener noreferrer" class="text-omni-accent hover:underline break-all">$1</a>'
		);
	}

	onMount(() => {
		return () => {
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

<div class="mx-auto px-4 py-6 transition-all duration-300 {theaterMode ? 'max-w-screen-2xl' : 'max-w-5xl'}">
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
		<div
			class="relative w-full overflow-hidden rounded-lg bg-black"
			style="aspect-ratio: {streamInfo.width && streamInfo.height ? `${streamInfo.width}/${streamInfo.height}` : '16/9'}"
		>
		<!-- svelte-ignore a11y_media_has_caption -->
			<video
				bind:this={videoEl}
				class="h-full w-full"
				controls
				autoplay
				playsinline
				preload="auto"
				src={streamInfo.video_url}
				onloadeddata={() => {
					if (streamInfo?.audio_url) {
						syncAudio();
					}
				}}
			>
				{#if streamInfo.subtitles && streamInfo.subtitles.length > 0}
					{#each streamInfo.subtitles as sub}
						<track
							kind="captions"
							src="/api/stream/{$page.params.id}/subtitles/{sub.lang}"
							srclang={sub.lang}
							label={sub.label}
						/>
					{/each}
				{:else}
					<track kind="captions" />
				{/if}
			</video>

			{#if streamInfo.audio_url}
				<audio
					bind:this={audioEl}
					src={streamInfo.audio_url}
					preload="auto"
				></audio>
			{/if}
		</div>

		<!-- Player Controls -->
		<div class="mt-2 flex items-center justify-end gap-2">
			{#if streamInfo.available_qualities?.length}
				<select
					class="appearance-none rounded border border-omni-border bg-omni-surface px-2 py-1 pr-7 text-xs font-mono text-omni-text-muted
						hover:border-omni-accent focus:border-omni-accent focus:outline-none transition-colors
						{changingQuality ? 'opacity-50' : ''}"
					value={selectedQuality}
					onchange={(e) => changeQuality(Number(e.currentTarget.value))}
					disabled={changingQuality}
				>
					{#each streamInfo.available_qualities as q}
						<option value={q}>{q}p</option>
					{/each}
				</select>
			{/if}

			<button
				class="rounded border border-omni-border bg-omni-surface px-2 py-1 text-xs font-mono text-omni-text-muted
					hover:border-omni-accent hover:text-omni-accent transition-colors"
				onclick={() => theaterMode = !theaterMode}
				title={theaterMode ? 'Exit theater mode' : 'Theater mode'}
			>
				{theaterMode ? 'exit theater' : 'theater'}
			</button>
		</div>

		<!-- Video Info -->
		<div class="mt-4 space-y-3">
			<h1 class="text-lg font-mono font-semibold leading-snug text-omni-text">
				{streamInfo.title}
			</h1>

			<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-omni-text-muted">
				{#if streamInfo.channel}
					<a href="/?channel={streamInfo.channel_id}" class="text-omni-accent hover:underline transition-colors">{streamInfo.channel}</a>
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
							<pre class="whitespace-pre-wrap text-sm font-mono text-omni-text-muted leading-relaxed text-left">{@html linkifyDescription(streamInfo.description)}</pre>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</div>

<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores';
	import { getStreamInfo, getComments, type StreamInfo, type CommentData } from '$lib/api';
	import { settingsStore } from '$lib/settings.svelte';
	import { formatCount, formatDuration } from '$lib/utils';

	let streamInfo = $state<StreamInfo | null>(null);
	let loading = $state(true);
	let error = $state('');
	let videoEl = $state<HTMLVideoElement>();
	let audioEl = $state<HTMLAudioElement>();
	let showDescription = $state(false);
	let theaterMode = $state(settingsStore.current.theaterMode);
	let selectedQuality = $state(settingsStore.current.defaultQuality || 720);
	let changingQuality = $state(false);

	// Comments
	let showComments = $state(false);
	let comments = $state<CommentData[]>([]);
	let commentsLoading = $state(false);
	let commentsLoaded = $state(false);
	let commentsError = $state('');

	// Hold-click for 2x speed
	let holdTimer: ReturnType<typeof setTimeout> | null = null;
	let isHolding = $state(false);
	let savedPlaybackRate = 1;

	// Custom controls
	let captionSize = $state<'small' | 'medium' | 'large'>('medium');
	let volume = $state(1);
	let previousVolume = 1;
	let showMenu = $state(false);
	let captionsEnabled = $state(false);

	$effect(() => {
		const videoId = $page.params.id;
		if (videoId) {
			loadVideo(videoId);
			// Reset comments when video changes
			showComments = false;
			comments = [];
			commentsLoaded = false;
			commentsError = '';
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

	async function loadComments() {
		if (commentsLoaded || commentsLoading) return;
		commentsLoading = true;
		commentsError = '';
		try {
			const videoId = $page.params.id;
			if (!videoId) return;
			const res = await getComments(videoId, 30);
			comments = res.comments;
			commentsLoaded = true;
		} catch (e: any) {
			commentsError = e.message || 'Failed to load comments';
		} finally {
			commentsLoading = false;
		}
	}

	function toggleComments() {
		showComments = !showComments;
		if (showComments && !commentsLoaded) {
			loadComments();
		}
	}

	function syncAudio() {
		cleanupFn?.();
		if (!audioEl || !videoEl) return;
		const audio = audioEl;
		const video = videoEl;

		// Mute video element (audio handled by separate <audio>)
		video.muted = true;
		audio.volume = volume;

		let seekDebounce: ReturnType<typeof setTimeout> | null = null;
		let isSeeking = false;

		const onPlay = () => {
			audio.currentTime = video.currentTime;
			audio.play().catch(() => {});
		};
		const onPause = () => audio.pause();
		const onSeeking = () => {
			isSeeking = true;
			audio.pause();
		};
		const onSeeked = () => {
			if (seekDebounce) clearTimeout(seekDebounce);
			seekDebounce = setTimeout(() => {
				isSeeking = false;
				audio.currentTime = video.currentTime;
				if (!video.paused) {
					audio.play().catch(() => {});
				}
				seekDebounce = null;
			}, 150);
		};
		const onRateChange = () => {
			audio.playbackRate = video.playbackRate;
		};

		video.addEventListener('play', onPlay);
		video.addEventListener('pause', onPause);
		video.addEventListener('seeking', onSeeking);
		video.addEventListener('seeked', onSeeked);
		video.addEventListener('ratechange', onRateChange);

		// Initial sync
		if (!video.paused) {
			audio.currentTime = video.currentTime;
			audio.play().catch(() => {});
		}

		// Drift correction — check every second, correct if >150ms off
		const syncInterval = setInterval(() => {
			if (!video.paused && !audio.paused && !isSeeking) {
				const drift = Math.abs(video.currentTime - audio.currentTime);
				if (drift > 0.15) {
					audio.currentTime = video.currentTime;
				}
			}
		}, 1000);

		cleanupFn = () => {
			clearInterval(syncInterval);
			if (seekDebounce) clearTimeout(seekDebounce);
			video.removeEventListener('play', onPlay);
			video.removeEventListener('pause', onPause);
			video.removeEventListener('seeking', onSeeking);
			video.removeEventListener('seeked', onSeeked);
			video.removeEventListener('ratechange', onRateChange);
		};
	}

	let cleanupFn: (() => void) | null = null;

	function setVolume(v: number) {
		volume = Math.max(0, Math.min(1, v));
		if (streamInfo?.audio_url && audioEl) {
			audioEl.volume = volume;
		} else if (videoEl) {
			videoEl.volume = volume;
		}
	}

	function toggleCaptions() {
		if (!videoEl) return;
		const tracks = videoEl.textTracks;
		if (captionsEnabled) {
			for (let i = 0; i < tracks.length; i++) {
				tracks[i].mode = 'disabled';
			}
			captionsEnabled = false;
		} else {
			if (tracks.length > 0) {
				tracks[0].mode = 'showing';
				captionsEnabled = true;
			}
		}
	}

	function toggleFullscreen() {
		const container = videoEl?.closest('.relative');
		if (!document.fullscreenElement) {
			container?.requestFullscreen();
		} else {
			document.exitFullscreen();
		}
	}

	async function handleDownload() {
		const videoId = $page.params.id;
		if (!videoId) return;
		try {
			const res = await fetch(`/api/stream/${videoId}/download?quality=${selectedQuality}`);
			const data = await res.json();
			if (data.url) {
				window.open(data.url, '_blank');
			}
		} catch (e) {
			console.error('Download failed:', e);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!videoEl) return;
		// Ignore when typing in inputs
		const tag = (e.target as HTMLElement)?.tagName;
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

		switch (e.key) {
			case 'ArrowLeft':
				e.preventDefault();
				e.stopPropagation();
				videoEl.currentTime = Math.max(0, videoEl.currentTime - 5);
				if (audioEl) audioEl.currentTime = videoEl.currentTime;
				break;
			case 'ArrowRight':
				e.preventDefault();
				e.stopPropagation();
				videoEl.currentTime = Math.min(videoEl.duration || Infinity, videoEl.currentTime + 5);
				if (audioEl) audioEl.currentTime = videoEl.currentTime;
				break;
			case 'ArrowUp':
				e.preventDefault();
				e.stopPropagation();
				setVolume(volume + 0.05);
				break;
			case 'ArrowDown':
				e.preventDefault();
				e.stopPropagation();
				setVolume(volume - 0.05);
				break;
			case ' ':
			case 'k':
				e.preventDefault();
				e.stopPropagation();
				if (videoEl.paused) videoEl.play();
				else videoEl.pause();
				break;
			case 'f':
				e.preventDefault();
				toggleFullscreen();
				break;
			case 'c':
				e.preventDefault();
				toggleCaptions();
				break;
			case 'm':
				e.preventDefault();
				e.stopPropagation();
				if (volume > 0) {
					previousVolume = volume;
					setVolume(0);
				} else {
					setVolume(previousVolume);
				}
				break;
		}
	}

	function handleVideoPointerDown(e: PointerEvent) {
		if (!videoEl) return;
		// Only on the video itself, not controls
		if (e.button !== 0) return;
		savedPlaybackRate = videoEl.playbackRate;
		holdTimer = setTimeout(() => {
			isHolding = true;
			if (videoEl) {
				videoEl.playbackRate = 2;
				if (audioEl) audioEl.playbackRate = 2;
			}
		}, 300);
	}

	function handleVideoPointerUp() {
		if (holdTimer) {
			clearTimeout(holdTimer);
			holdTimer = null;
		}
		if (isHolding && videoEl) {
			videoEl.playbackRate = savedPlaybackRate;
			if (audioEl) audioEl.playbackRate = savedPlaybackRate;
			isHolding = false;
		}
	}

	function linkifyDescription(text: string): string {
		const escaped = text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;');
		// Linkify URLs
		let result = escaped.replace(
			/(https?:\/\/[^\s<]+)/g,
			'<a href="$1" target="_blank" rel="noopener noreferrer" class="text-omni-accent hover:underline break-all">$1</a>'
		);
		// Make timestamps clickable (0:00, 1:23, 1:23:45)
		result = result.replace(
			/(?<![:\w])(\d{1,2}(?::\d{2}){1,2})(?![:\w])/g,
			(match) => {
				const parts = match.split(':').map(Number);
				let seconds = 0;
				if (parts.length === 3) seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
				else if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
				return `<button class="text-omni-accent hover:underline font-mono" data-seek="${seconds}">${match}</button>`;
			}
		);
		return result;
	}

	function linkifyComment(text: string): string {
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
		window.addEventListener('keydown', handleKeydown);
		window.addEventListener('pointerup', handleVideoPointerUp);

		// Handle clicks on timestamp seek buttons in description
		function handleSeekClick(e: MouseEvent) {
			const btn = (e.target as HTMLElement).closest('[data-seek]');
			if (btn && videoEl) {
				const time = Number(btn.getAttribute('data-seek'));
				if (!isNaN(time)) {
					videoEl.currentTime = time;
					if (audioEl) audioEl.currentTime = time;
				}
			}
		}
		document.addEventListener('click', handleSeekClick);

		return () => {
			window.removeEventListener('keydown', handleKeydown);
			window.removeEventListener('pointerup', handleVideoPointerUp);
			document.removeEventListener('click', handleSeekClick);
			if (holdTimer) clearTimeout(holdTimer);
			cleanupFn?.();
			if (audioEl) {
				audioEl.pause();
				audioEl.src = '';
			}
			document.getElementById('omni-caption-style')?.remove();
		};
	});

	// Prevent native video controls from stealing keyboard focus
	// so arrow keys always go through our handler (5s skip, not native 10s)
	$effect(() => {
		if (videoEl) {
			const blurOnFocus = () => requestAnimationFrame(() => videoEl?.blur());
			videoEl.addEventListener('focus', blurOnFocus);
			return () => videoEl?.removeEventListener('focus', blurOnFocus);
		}
	});

	// Dynamic caption size CSS
	$effect(() => {
		const sizes: Record<string, string> = { small: '0.85rem', medium: '1.3rem', large: '2rem' };
		let style = document.getElementById('omni-caption-style');
		if (!style) {
			style = document.createElement('style');
			style.id = 'omni-caption-style';
			document.head.appendChild(style);
		}
		style.textContent = `video::cue { font-size: ${sizes[captionSize]} !important; background: rgba(0,0,0,0.7); color: white; line-height: 1.4; }`;
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
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="relative w-full overflow-hidden rounded-lg bg-black"
			style="aspect-ratio: {streamInfo.width && streamInfo.height ? `${streamInfo.width}/${streamInfo.height}` : '16/9'}"
			onpointerdown={handleVideoPointerDown}
		>
			{#if isHolding}
				<div class="absolute top-3 left-1/2 -translate-x-1/2 z-10 rounded-full bg-black/70 px-3 py-1 text-xs font-mono text-white pointer-events-none">
					2x speed
				</div>
			{/if}
		<!-- svelte-ignore a11y_media_has_caption -->
			<video
				bind:this={videoEl}
				class="h-full w-full"
				controls
				autoplay
				playsinline
				preload="auto"
				src="/api/stream/{$page.params.id}/proxy/video?quality={selectedQuality}"
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
					src="/api/stream/{$page.params.id}/proxy/audio?quality={selectedQuality}"
					preload="auto"
				></audio>
			{/if}
		</div>

		<!-- Title + Controls Row -->
		<div class="mt-3 flex flex-wrap items-start justify-between gap-3">
			<h1 class="flex-1 min-w-0 text-lg font-mono font-semibold leading-snug text-omni-text">
				{streamInfo.title}
			</h1>

			<div class="flex shrink-0 items-center gap-2">
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
					onclick={() => { theaterMode = !theaterMode; settingsStore.update({ theaterMode }); }}
					title={theaterMode ? 'Exit theater mode' : 'Theater mode'}
				>
					{theaterMode ? 'exit theater' : 'theater'}
				</button>

				<!-- More Options Menu -->
				<div class="relative">
					<button
						class="rounded border border-omni-border bg-omni-surface px-2 py-1 text-xs font-mono text-omni-text-muted
							hover:border-omni-accent hover:text-omni-accent transition-colors"
						onclick={() => showMenu = !showMenu}
						title="More options"
					>
						⋯
					</button>
					{#if showMenu}
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<div class="fixed inset-0 z-20" onclick={() => showMenu = false}></div>
						<div class="absolute right-0 top-full mt-1.5 z-30 rounded-lg border border-omni-border bg-omni-surface p-3 space-y-3 min-w-56 shadow-xl animate-fade-in">
							<!-- Volume -->
							<div class="flex items-center gap-2">
								<span class="text-xs font-mono text-omni-text-muted w-16 shrink-0">volume</span>
								<input
									type="range" min="0" max="1" step="0.01"
									value={volume}
									oninput={(e) => setVolume(Number(e.currentTarget.value))}
									class="flex-1 h-1 cursor-pointer accent-[var(--omni-accent)]"
								/>
								<span class="text-xs font-mono text-omni-text-muted w-8 text-right">{Math.round(volume * 100)}%</span>
							</div>

							<!-- Caption Size -->
							<div class="flex items-center gap-2">
								<span class="text-xs font-mono text-omni-text-muted w-16 shrink-0">captions</span>
								<select
									class="flex-1 appearance-none rounded border border-omni-border bg-omni-bg px-2 py-1 text-xs font-mono text-omni-text-muted
										focus:border-omni-accent focus:outline-none transition-colors"
									value={captionSize}
									onchange={(e) => captionSize = e.currentTarget.value as 'small' | 'medium' | 'large'}
								>
									<option value="small">small</option>
									<option value="medium">medium</option>
									<option value="large">large</option>
								</select>
								<button
									class="rounded border px-2 py-1 text-xs font-mono transition-colors
										{captionsEnabled
											? 'border-omni-accent bg-omni-accent/10 text-omni-accent'
											: 'border-omni-border text-omni-text-muted hover:border-omni-accent hover:text-omni-accent'}"
									onclick={toggleCaptions}
								>
									{captionsEnabled ? 'on' : 'off'}
								</button>
							</div>

							<!-- Fullscreen -->
							<button
								class="w-full rounded border border-omni-border px-2 py-1.5 text-xs font-mono text-omni-text-muted text-left
									hover:border-omni-accent hover:text-omni-accent transition-colors"
								onclick={() => { toggleFullscreen(); showMenu = false; }}
							>
								fullscreen (f)
							</button>

							<!-- Download -->
							<button
								class="w-full rounded border border-omni-border px-2 py-1.5 text-xs font-mono text-omni-text-muted text-left
									hover:border-omni-accent hover:text-omni-accent transition-colors"
								onclick={() => { handleDownload(); showMenu = false; }}
							>
								download
							</button>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Video Meta -->
		<div class="mt-2 space-y-3">
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

			<!-- Description (includes chapters) -->
			{#if settings.showVideoDescription && (streamInfo.description || (streamInfo.chapters && streamInfo.chapters.length > 0))}
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
						<div class="border-t border-omni-border px-4 py-3 animate-fade-in space-y-3">
							{#if streamInfo.chapters && streamInfo.chapters.length > 0}
								<div>
									<h4 class="mb-1.5 text-[11px] font-mono font-semibold text-omni-text-muted/70 uppercase tracking-wider">Chapters</h4>
									<div class="space-y-0.5">
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
							{#if streamInfo.description}
								{#if streamInfo.chapters && streamInfo.chapters.length > 0}
									<div class="border-t border-omni-border/50"></div>
								{/if}
								<pre class="whitespace-pre-wrap text-sm font-mono text-omni-text-muted leading-relaxed text-left">{@html linkifyDescription(streamInfo.description)}</pre>
							{/if}
						</div>
					{/if}
				</div>
			{/if}

			<!-- Comments -->
			{#if settings.showVideoComments}
			<div class="rounded-lg border border-omni-border bg-omni-surface">
				<button
					class="flex w-full items-center justify-between px-4 py-3 text-left text-xs font-mono text-omni-text-muted
						hover:text-omni-text transition-colors"
					onclick={toggleComments}
				>
					<span>comments</span>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-4 w-4 transition-transform {showComments ? 'rotate-180' : ''}"
						viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
					>
						<polyline points="6 9 12 15 18 9"/>
					</svg>
				</button>
				{#if showComments}
					<div class="border-t border-omni-border px-4 py-3 animate-fade-in">
						{#if commentsLoading}
							<div class="space-y-3">
								{#each Array(3) as _}
									<div class="animate-pulse space-y-1">
										<div class="h-3 w-24 rounded bg-omni-surface-hover"></div>
										<div class="h-3 w-full rounded bg-omni-surface-hover"></div>
									</div>
								{/each}
							</div>
						{:else if commentsError}
							<p class="text-xs font-mono text-rose-400">{commentsError}</p>
						{:else if comments.length === 0}
							<p class="text-xs font-mono text-omni-text-muted">no comments found</p>
						{:else}
							<div class="space-y-4 max-h-96 overflow-y-auto">
								{#each comments as comment}
									<div class="space-y-1">
										<div class="flex items-center gap-2 text-xs font-mono">
											<span class="font-semibold text-omni-text">{comment.author}</span>
											{#if comment.time_text}
												<span class="text-omni-text-muted/50">{comment.time_text}</span>
											{/if}
											{#if comment.is_pinned}
												<span class="text-omni-accent text-[10px]">pinned</span>
											{/if}
										</div>
										<p class="text-sm font-mono text-omni-text-muted leading-relaxed whitespace-pre-wrap">{@html linkifyComment(comment.text)}</p>
										{#if comment.likes > 0}
											<span class="text-[11px] font-mono text-omni-text-muted/50">{formatCount(comment.likes)} likes</span>
										{/if}
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{/if}
			</div>
			{/if}
		</div>
	{/if}
</div>

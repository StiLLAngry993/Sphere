/**
 * Sphere · Stories  (static/js/stories.js)
 *
 * Drop this file in static/js/ and load it at the bottom of home.html:
 *   <script src="{% static 'js/stories.js' %}" defer></script>
 *
 * Requires:
 *   - Django CSRF cookie (js-cookie or meta tag)
 *   - The _story_bar.html partial to be included in home.html
 */

'use strict';

// ─── CSRF helper ───────────────────────────────────────────────────────────
function getCsrf() {
  // Try meta tag first, then cookie
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.content;
  return document.cookie.split(';')
    .find(c => c.trim().startsWith('csrftoken='))
    ?.split('=')[1] ?? '';
}

// ─── Format seconds → m:ss ─────────────────────────────────────────────────
function fmtTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

// ═══════════════════════════════════════════════════════════════════════════
// STORY BAR  ─ fetch feed, render bubbles, open viewer on click
// ═══════════════════════════════════════════════════════════════════════════

let storyGroups = [];   // [{user_id, username, display_name, profile_picture, stories[], all_viewed, is_own}]
let viewerGroupIdx = 0; // which group the viewer is showing
let viewerStoryIdx = 0; // which story within that group

async function loadStoryFeed() {
  try {
    const res = await fetch('/stories/feed/', { credentials: 'same-origin' });
    if (!res.ok) return;
    const data = await res.json();
    storyGroups = data.groups;
    renderBubbles();
  } catch (e) {
    console.warn('Stories feed failed', e);
  }
}

function renderBubbles() {
  const container = document.getElementById('storyBubbles');
  if (!container) return;
  container.innerHTML = '';

  storyGroups.forEach((group, gi) => {
    if (group.is_own) return; // own story handled by addStoryBtn area separately

    const btn = document.createElement('button');
    btn.className = 'story-bubble';
    btn.setAttribute('aria-label', `${group.display_name}'s story`);

    const ringCls = group.all_viewed
      ? 'story-bubble__ring story-bubble__ring--viewed'
      : 'story-bubble__ring';

    const avatarHTML = group.profile_picture
      ? `<img src="${group.profile_picture}" alt="${group.display_name}" class="story-bubble__avatar">`
      : `<div class="story-bubble__avatar story-bubble__avatar--placeholder">${group.display_name[0].toUpperCase()}</div>`;

    btn.innerHTML = `
      <div class="${ringCls}">
        <div class="story-bubble__avatar-wrap">${avatarHTML}</div>
      </div>
      <span class="story-bubble__name">${group.display_name}</span>
    `;

    btn.addEventListener('click', () => openViewer(gi, 0));
    container.appendChild(btn);
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// VIEWER
// ═══════════════════════════════════════════════════════════════════════════

let viewerTimer = null;
let viewerProgressStart = null;
let viewerProgressDuration = 5000; // ms

const viewer       = document.getElementById('storyViewer');
const viewerImg    = document.getElementById('viewerImg');
const viewerVid    = document.getElementById('viewerVid');
const viewerAudio  = document.getElementById('viewerAudio');
const viewerAvatar = document.getElementById('viewerAvatar');
const viewerName   = document.getElementById('viewerName');
const viewerTime   = document.getElementById('viewerTime');
const viewerViews  = document.getElementById('viewerViews');
const viewerDel    = document.getElementById('viewerDelete');
const viewerClose  = document.getElementById('viewerClose');
const viewerPrev   = document.getElementById('viewerPrev');
const viewerNext   = document.getElementById('viewerNext');
const progressBar  = document.getElementById('viewerProgress');

function openViewer(groupIdx, storyIdx) {
  viewerGroupIdx = groupIdx;
  viewerStoryIdx = storyIdx;
  viewer.removeAttribute('hidden');
  document.body.style.overflow = 'hidden';
  showCurrentStory();
}

function closeViewer() {
  clearViewerTimer();
  viewer.setAttribute('hidden', '');
  document.body.style.overflow = '';
  viewerVid.pause();
  viewerVid.src = '';
  viewerAudio.src = '';
}

function showCurrentStory() {
  clearViewerTimer();

  const group = storyGroups[viewerGroupIdx];
  if (!group) { closeViewer(); return; }

  const story = group.stories[viewerStoryIdx];
  if (!story) { closeViewer(); return; }

  // Mark viewed
  fetch(`/stories/${story.id}/view/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrf() },
    credentials: 'same-origin',
  }).catch(() => {});

  // Header
  viewerAvatar.src   = group.profile_picture || '';
  viewerAvatar.alt   = group.display_name;
  viewerName.textContent = group.display_name;
  viewerTime.textContent = timeAgo(story.created_at);

  // Delete button visibility (own stories)
  viewerDel.hidden = !group.is_own;

  // Nav arrows
  viewerPrev.hidden = (viewerGroupIdx === 0 && viewerStoryIdx === 0);
  const isLast = viewerGroupIdx === storyGroups.length - 1 &&
                 viewerStoryIdx === group.stories.length - 1;
  viewerNext.hidden = isLast;

  // Build progress bars
  buildProgressBars(group.stories.length, viewerStoryIdx);

  // Media
  const duration = (story.duration || 5) * 1000;
  viewerProgressDuration = duration;

  if (story.media_type === 'image') {
    viewerImg.src = story.media_url;
    viewerImg.removeAttribute('hidden');
    viewerVid.setAttribute('hidden', '');
    viewerVid.pause();
    viewerVid.src = '';
    viewerAudio.pause();
    viewerAudio.src = '';
    startProgressTimer(duration);
  } else {
    viewerImg.setAttribute('hidden', '');
    viewerVid.removeAttribute('hidden');
    viewerVid.src = story.media_url;
    // If there's an uploaded audio, mute the video and play audio only
    viewerVid.muted = !!story.audio_url;
    viewerVid.play();
    viewerVid.onloadedmetadata = () => {
      const dur = (viewerVid.duration || 5) * 1000;
      startProgressTimer(dur);
    };
  }

  // Audio overlay (plays alongside video, or solo if no video)
  if (story.audio_url) {
    viewerAudio.src = story.audio_url;
    viewerAudio.play().catch(err => {
      console.warn('Could not autoplay audio:', err);
    });
  } else {
    viewerAudio.src = '';
    viewerAudio.pause();
  }

  viewerViews.textContent = '';
}

function buildProgressBars(count, activeIdx) {
  progressBar.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const bar = document.createElement('div');
    bar.className = 'viewer-progress__bar';
    const fill = document.createElement('div');
    fill.className = 'viewer-progress__bar-fill';
    if (i < activeIdx) fill.style.width = '100%';   // already viewed
    if (i === activeIdx) fill.id = 'activeFill';     // being animated
    bar.appendChild(fill);
    progressBar.appendChild(bar);
  }
}

function startProgressTimer(durationMs) {
  const fill = document.getElementById('activeFill');
  if (!fill) return;

  viewerProgressStart = performance.now();
  function tick(now) {
    const elapsed = now - viewerProgressStart;
    const pct = Math.min((elapsed / durationMs) * 100, 100);
    fill.style.width = pct + '%';
    if (pct < 100) {
      viewerTimer = requestAnimationFrame(tick);
    } else {
      advanceStory();
    }
  }
  viewerTimer = requestAnimationFrame(tick);
}

function clearViewerTimer() {
  if (viewerTimer) { cancelAnimationFrame(viewerTimer); viewerTimer = null; }
}

function advanceStory() {
  const group = storyGroups[viewerGroupIdx];
  if (viewerStoryIdx < group.stories.length - 1) {
    viewerStoryIdx++;
    showCurrentStory();
  } else if (viewerGroupIdx < storyGroups.length - 1) {
    viewerGroupIdx++;
    viewerStoryIdx = 0;
    showCurrentStory();
  } else {
    closeViewer();
  }
}

function retreatStory() {
  if (viewerStoryIdx > 0) {
    viewerStoryIdx--;
    showCurrentStory();
  } else if (viewerGroupIdx > 0) {
    viewerGroupIdx--;
    viewerStoryIdx = storyGroups[viewerGroupIdx].stories.length - 1;
    showCurrentStory();
  }
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.floor(diff / 3600000);
  const m = Math.floor(diff / 60000);
  if (h >= 1) return `${h}h ago`;
  if (m >= 1) return `${m}m ago`;
  return 'just now';
}

// Viewer events
if (viewerClose) viewerClose.addEventListener('click', closeViewer);
if (viewerNext)  viewerNext.addEventListener('click', advanceStory);
if (viewerPrev)  viewerPrev.addEventListener('click', retreatStory);
document.addEventListener('keydown', e => {
  if (viewer.hidden) return;
  if (e.key === 'ArrowRight') advanceStory();
  if (e.key === 'ArrowLeft')  retreatStory();
  if (e.key === 'Escape')     closeViewer();
});

// Pause on hold / tap left-right zones
viewer?.addEventListener('pointerdown', e => {
  const rect = viewer.getBoundingClientRect();
  const x = e.clientX - rect.left;
  if (x < rect.width * 0.3) retreatStory();
  else if (x > rect.width * 0.7) advanceStory();
});

// Delete own story
viewerDel?.addEventListener('click', async () => {
  const group = storyGroups[viewerGroupIdx];
  const story = group.stories[viewerStoryIdx];
  if (!confirm('Delete this story?')) return;

  const res = await fetch(`/stories/${story.id}/delete/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrf() },
    credentials: 'same-origin',
  });
  if (res.ok) {
    group.stories.splice(viewerStoryIdx, 1);
    if (group.stories.length === 0) {
      storyGroups.splice(viewerGroupIdx, 1);
      renderBubbles();
      closeViewer();
    } else {
      viewerStoryIdx = Math.min(viewerStoryIdx, group.stories.length - 1);
      showCurrentStory();
    }
  }
});


// ═══════════════════════════════════════════════════════════════════════════
// UPLOAD FLOW
// ═══════════════════════════════════════════════════════════════════════════

const uploadModal  = document.getElementById('uploadModal');
const stepPick     = document.getElementById('stepPick');
const stepEdit     = document.getElementById('stepEdit');
const mediaInput   = document.getElementById('mediaInput');
const audioInput   = document.getElementById('audioInput');
const dropZone     = document.getElementById('dropZone');
const imgPreview   = document.getElementById('imgPreview');
const vidPreview   = document.getElementById('vidPreview');
const trimSection  = document.getElementById('trimSection');
const trimDuration = document.getElementById('trimDuration');
const audioLabel   = document.getElementById('audioLabel');
const audioPreview = document.getElementById('audioPreview');
const removeAudio  = document.getElementById('removeAudio');
const audioPick    = document.getElementById('audioPick');
const confirmBtn   = document.getElementById('confirmUpload');
const confirmLabel = document.getElementById('confirmLabel');
const confirmSpinner = document.getElementById('confirmSpinner');
const addStoryBtn  = document.getElementById('addStoryBtn');

let selectedFile   = null;
let selectedAudio  = null;
let mediaType      = 'image';
let trimStartSec   = 0;
let trimEndSec     = 0;
let videoDuration  = 0;
let isUploading    = false; // Prevent double upload

// Open / close
addStoryBtn?.addEventListener('click', openUploadModal);
document.getElementById('closeUpload')?.addEventListener('click', closeUploadModal);
document.getElementById('closeEdit')?.addEventListener('click', closeUploadModal);
document.getElementById('backToPick')?.addEventListener('click', () => goToStep(1));
document.getElementById('uploadBackdrop')?.addEventListener('click', closeUploadModal);

function openUploadModal() {
  uploadModal.removeAttribute('hidden');
  document.body.style.overflow = 'hidden';
  goToStep(1);
}
function closeUploadModal() {
  uploadModal.setAttribute('hidden', '');
  document.body.style.overflow = '';
  resetUploadState();
}
function goToStep(n) {
  stepPick.hidden = (n !== 1);
  stepEdit.hidden = (n !== 2);
}

function resetUploadState() {
  selectedFile = null;
  selectedAudio = null;
  mediaType = 'image';
  trimStartSec = 0;
  trimEndSec = 0;
  videoDuration = 0;
  if (mediaInput) mediaInput.value = '';
  if (audioInput) audioInput.value = '';
  if (imgPreview) { imgPreview.hidden = true; imgPreview.src = ''; }
  if (vidPreview) { vidPreview.hidden = true; vidPreview.src = ''; }
  if (trimSection) trimSection.hidden = true;
  audioLabel.textContent = 'Choose from device';
  audioPreview.hidden = true;
  audioPreview.src = '';
  removeAudio.hidden = true;
  confirmBtn.disabled = false;
  confirmLabel.hidden = false;
  confirmSpinner.hidden = true;
}

// File input
mediaInput?.addEventListener('change', e => {
  const file = e.target.files?.[0];
  if (file) handleMediaFile(file);
});

// Drop zone
dropZone?.addEventListener('click', () => mediaInput?.click());
dropZone?.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') mediaInput?.click(); });
dropZone?.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone?.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files?.[0];
  if (file) handleMediaFile(file);
});

function handleMediaFile(file) {
  if (file.size > 50 * 1024 * 1024) {
    alert('File too large. Max 50 MB.');
    return;
  }

  selectedFile = file;
  mediaType = file.type.startsWith('video') ? 'video' : 'image';
  const url = URL.createObjectURL(file);

  if (mediaType === 'image') {
    imgPreview.src = url;
    imgPreview.hidden = false;
    vidPreview.hidden = true;
    trimSection.hidden = true;
  } else {
    vidPreview.src = url;
    vidPreview.hidden = false;
    imgPreview.hidden = true;
    vidPreview.onloadedmetadata = () => {
      videoDuration = vidPreview.duration;
      trimStartSec = 0;
      trimEndSec = videoDuration;
      trimSection.hidden = false;
      initTrimSlider();
    };
    vidPreview.play();
  }

  goToStep(2);
}

// ── Trim slider ─────────────────────────────────────────────────────────────

const trimTrack    = document.getElementById('trimTrack');
const trimSelected = document.getElementById('trimSelected');
const trimStartH   = document.getElementById('trimStart');
const trimEndH     = document.getElementById('trimEnd');
const trimStartLbl = document.getElementById('trimStartLabel');
const trimEndLbl   = document.getElementById('trimEndLabel');

function initTrimSlider() {
  updateTrimUI();
}

function updateTrimUI() {
  if (!trimTrack) return;
  const trackW = trimTrack.offsetWidth;
  const startPct = (trimStartSec / videoDuration) * 100;
  const endPct   = (trimEndSec   / videoDuration) * 100;
  if (trimSelected) {
    trimSelected.style.left  = startPct + '%';
    trimSelected.style.width = (endPct - startPct) + '%';
  }
  if (trimStartH) trimStartH.style.left = startPct + '%';
  if (trimEndH)   trimEndH.style.left   = endPct   + '%';
  if (trimStartLbl) trimStartLbl.textContent = fmtTime(trimStartSec);
  if (trimEndLbl)   trimEndLbl.textContent   = fmtTime(trimEndSec);
  if (trimDuration) trimDuration.textContent = fmtTime(trimEndSec - trimStartSec);
}

function makeDraggable(handle, onMove) {
  if (!handle) return;
  let dragging = false;
  handle.addEventListener('pointerdown', e => {
    dragging = true;
    handle.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  handle.addEventListener('pointermove', e => {
    if (!dragging || !trimTrack) return;
    const rect = trimTrack.getBoundingClientRect();
    const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onMove(pct * videoDuration);
    updateTrimUI();
    if (vidPreview) {
      vidPreview.currentTime = trimStartSec;
    }
  });
  handle.addEventListener('pointerup', () => { dragging = false; });
}

makeDraggable(trimStartH, sec => {
  trimStartSec = Math.min(sec, trimEndSec - 0.5);
  trimStartSec = Math.max(0, trimStartSec);
});
makeDraggable(trimEndH, sec => {
  trimEndSec = Math.max(sec, trimStartSec + 0.5);
  trimEndSec = Math.min(videoDuration, trimEndSec);
});

// ── Audio picker ────────────────────────────────────────────────────────────

audioPick?.addEventListener('click', () => audioInput?.click());
audioPick?.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') audioInput?.click(); });

audioInput?.addEventListener('change', e => {
  const file = e.target.files?.[0];
  if (!file) return;
  
  // Validate audio file size (10MB max for audio)
  if (file.size > 10 * 1024 * 1024) {
    alert('Audio file too large. Max 10 MB.');
    audioInput.value = '';
    return;
  }
  
  selectedAudio = file;
  audioLabel.textContent = file.name.slice(0, 28) + (file.name.length > 28 ? '…' : '');
  audioPreview.src = URL.createObjectURL(file);
  audioPreview.hidden = false;
  removeAudio.hidden = false;
});

removeAudio?.addEventListener('click', () => {
  selectedAudio = null;
  if (audioInput) audioInput.value = '';
  audioLabel.textContent = 'Choose from device';
  audioPreview.hidden = true;
  audioPreview.src = '';
  removeAudio.hidden = true;
});

// ── Upload submit ────────────────────────────────────────────────────────────

confirmBtn?.addEventListener('click', async () => {
  if (!selectedFile || isUploading) return;

  isUploading = true;
  confirmBtn.disabled = true;
  confirmLabel.hidden = true;
  confirmSpinner.hidden = false;

  const formData = new FormData();
  formData.append('media_file', selectedFile);
  formData.append('media_type', mediaType);

  const duration = mediaType === 'video'
    ? Math.round(trimEndSec - trimStartSec)
    : 5;
  formData.append('duration', duration);

  if (selectedAudio) {
    formData.append('audio_file', selectedAudio);
  }

  try {
    console.log('Starting upload...', {mediaType, duration, hasAudio: !!selectedAudio});
    const csrfToken = getCsrf();
    console.log('CSRF Token:', csrfToken ? 'Present' : 'MISSING');
    
    const res = await fetch('/stories/upload/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      credentials: 'same-origin',
      body: formData,
    });
    
    console.log('Upload response status:', res.status, res.statusText);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    console.log('Upload response data:', data);

    if (data.success) {
      console.log('Upload successful, closing modal...');
      closeUploadModal();
      // Refresh feed so own story appears
      await loadStoryFeed();
      // Flash the add button to show success
      addStoryBtn?.classList.add('story-bubble--success');
      setTimeout(() => addStoryBtn?.classList.remove('story-bubble--success'), 2000);
    } else {
      console.error('Upload failed:', data.error);
      alert(data.error || 'Upload failed. Please try again.');
      confirmBtn.disabled = false;
      confirmLabel.hidden = false;
      confirmSpinner.hidden = true;
    }
  } catch (err) {
    console.error('Upload error', err);
    alert('Upload failed. Check your connection or file size.');
    confirmBtn.disabled = false;
    confirmLabel.hidden = false;
    confirmSpinner.hidden = true;
  } finally {
    isUploading = false;
  }
});

// ── Own story viewer (add-story bubble when stories exist) ──────────────────
// If the logged-in user already has stories, clicking the add bubble should
// open the viewer first then provide an option to add more.
// (Simple approach: always open upload modal since the header story ring
//  already shows the count; feel free to extend this logic.)

// ── Init ────────────────────────────────────────────────────────────────────
loadStoryFeed();

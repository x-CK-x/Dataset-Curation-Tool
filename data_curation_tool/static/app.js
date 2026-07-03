if (typeof window !== 'undefined') window.__DCT_APP_JS_MODULE_EVALUATED = true;

// Backward-compatible label reference: Generate Tool Plan From This Context
const state = {
  tab: 'Dashboard',
  summary: {},
  datasets: [],
  media: { items: [], total: 0, page: 1, page_size: 80 },
  selected: new Set(),
  selectedMediaCache: {},
  activeMedia: null,
  jobs: [],
  jobSelections: new Set(),
  jobDetails: {},
  lastApiError: null,
  jobsAutoRefresh: true,
  modelsAutoRefresh: true,
  lastJobsFingerprint: '',
  lastModelStatusFingerprint: '',
  models: [],
  lastModelListRefreshAt: 0,
  modelStatuses: { stages: ['download', 'load', 'inference', 'training'], models: {}, aggregate: {} },
  modelResource: { devices: [], loaded_models: [], loading_reservations: [], warnings: [] },
  modelLoadPrefs: {},
  modelPlacementPlans: {},
  modelKindFilter: '',
  modelDownloadQueueMode: 'serial',
  customModelForm: { name: '', label: '', category: '', provider: 'huggingface', repo_id: '', local_path: '', description: '', capabilities: '', size_gb: '', vram_gb: '', precision: 'checkpoint-defined', modality: 'image/text', recommended_backend: 'auto' },
  modelRunSelection: '',
  quickModelSelection: '',
  curationModelSelection: '',
  tagSelectionModelSelection: '',
  predictionModelSelection: '',
  assistantModelSelection: '',
  assistantAgentToolsChatEnabled: false,
  assistantConfig: null,
  orchestratorPlan: null,
  orchestratorPlanModels: '',
  orchestratorPlanSelections: {},
  orchestrationModelSelection: '',
  presets: [],
  settings: {},
  tagProfiles: [],
  tagProfile: 'e621',
  orderingStrategy: 'booru',
  retainImportedOrder: false,
  downloadSources: [],
  downloadValidation: null,
  orchestrationTemplates: [],
  importFolders: [],
  tagDrafts: {},
  tagDraftSource: {},
  tagMeta: {},
  tagMetaPending: new Set(),
  tagScores: {},
  tagScorePending: new Set(),
  tagScoreRequestKeys: {},
  uiScrollMemory: {},
  renderScheduled: false,
  renderDeferredForEditing: false,
  controlInteractionHoldUntil: 0,
  dropdownInteractionActive: false,
  lastCompletedModelJobIds: new Set(),
  tagScoreAnalytics: null,
  featureMatrix: null,
  compareSelected: { left: new Set(), right: new Set() },
  compareFocus: { left: 0, right: 1 },
  lastTagSelection: null,
  lastTagSelectionError: null,
  lastTagSelectionChat: null,
  lastTagSelectionChatError: null,
  tagSelectionChatConversationId: null,
  tagSelectionChatMessages: [],
  tagSelectionChatState: {},
  tagSelectionChatDraft: '',
  tagSelectionChatSending: false,
  tagSelectionChatQueue: [],
  tagSelectionChatCurrent: null,
  assistantThinkingMode: '',
  assistantReasoningEffort: '',
  assistantShowVisiblePlan: true,
  assistantShowLiveActionNotes: true,
  assistantPlanningPasses: '',
  assistantPlanMaxTokens: '',
  assistantMinChatTokens: '',
  tagSelectionEditMessageId: null,
  tagSelectionEditDraft: '',
  codeProjectRoot: '',
  codeProjectScan: null,
  codeSelectedFiles: new Set(),
  codeModelSelection: '',
  codePrompt: '',
  codeChatDraft: '',
  codeChatSending: false,
  codeChatQueue: [],
  codeChatCurrent: null,
  codeThinkingMode: '',
  codeReasoningEffort: '',
  codeShowVisiblePlan: true,
  codeShowLiveActionNotes: true,
  codePlanningPasses: '',
  codePlanMaxTokens: '',
  codeMinChatTokens: '',
  codeConversationId: null,
  codeMessages: [],
  codeConversationState: {},
  codeLastResponse: null,
  codeLastError: null,
  codeEditMessageId: null,
  codeEditDraft: '',
  agentStatus: null,
  agentGoal: '',
  agentContext: '',
  agentModelSelection: '',
  agentPlan: null,
  agentConversationId: null,
  agentCommand: '',
  agentPythonScript: '',
  agentCwd: '',
  agentShell: 'auto',
  agentTimeout: 120,
  agentUserApproved: false,
  agentCoaExecutionEnabled: false,
  tagSelectionAgentToolsChatEnabled: false,
  codeAgentToolsChatEnabled: false,
  agentAllowHighRisk: false,
  agentHighRiskConfirmation: '',
  agentPath: '',
  agentUrl: 'about:blank',
  agentUseExistingProfile: false,
  agentBrowserProfilePath: '',
  agentLastResult: null,
  agentDebugLogs: null,
  agentDebugLogContent: null,
  agentSurfacePlans: {},
  agentCoaOptionsByMessage: {},
  agentCoaRunJobs: {},
  agentCoaJobWatchers: {},
  agentSurfaceDrafts: {},
  galleryScoresEnabled: false,
  editorAssistantSelection: null,
  editorManualTagSelections: {},
  editorSelectionCategory: '',
  editorFocus: 0,
  chatMessages: [],
  chatConversations: [],
  chatConversationId: null,
  chatConversationState: {},
  chatDraft: '',
  chatSending: false,
  chatQueue: [],
  chatCurrent: null,
  chatIncludeMetadata: true,
  chatMetadataPaths: '',
  dictionaryStatus: null,
  metadataOutput: null,
  metadataSchema: null,
  metadataSelectedPaths: new Set(),
  metadataFieldOutput: null,
  mediaToolOutput: null,
  recorder: null,
  recordChunks: [],
  voiceStatus: null,
  browserAudioDevices: { inputs: [], outputs: [] },
  voiceRecorder: null,
  voiceRecordTarget: null,
  voiceRecordStartedAt: 0,
  voiceBusy: false,
  ttsBusy: false,
  lastVoiceOutput: null,
  lastVoiceError: null,
  voiceSurfaceSttEnabled: null,
  voiceSurfaceTtsEnabled: null,
  ttsSpokenMessageIds: new Set(),
  groups: [],
  referenceStatus: null,
  referenceRuns: [],
  referenceResults: [],
  referenceOutput: null,
  annotationState: null,
  annotationMode: 'bbox',
  annotationDraftBbox: null,
  annotationPolygon: [],
  annotationPose2D: [],
  annotationPose3D: [],
  annotationEdges: [],
  poseTemplates: [],
  poseModel: '',
  poseModelStatus: null,
  poseModelOutput: null,
  poseProposals: [],
  poseProposalIndex: 0,
  poseTool: 'move',
  poseNewJointName: '',
  poseAutoConnect: true,
  poseSelectedJoint: null,
  poseConnectStart: null,
  poseTemplate: 'coco17',
  poseLoadedAnnotationId: null,
  poseViewerYaw: 0.45,
  poseViewerPitch: -0.2,
  poseViewerZoom: 115,
  customSkeletonKey: '',
  customSkeletonLabel: '',
  customSkeletonDimension: 'mixed',
  customSkeletonNames: '',
  customSkeletonEdges: '',
  poseShowSaved: true,
  poseLocalModelPath: '',
  poseCustomModelType: 'auto',
  threeDProviders: { generation: [], rigging: [] },
  threeDAssets: [],
  threeDProvider: 'triposr_local',
  threeDRigProvider: 'unirig_local',
  threeDRepoPath: '',
  threeDRigRepoPath: '',
  threeDEndpoint: '',
  threeDApiKey: '',
  threeDInputPath: '',
  threeDPrompt: '',
  threeDNegativePrompt: '',
  threeDMultiImagePaths: '',
  threeDVideoPath: '',
  threeDTokenProfile: '',
  threeDApiModelId: '',
  threeDContextShrinkerModel: '',
  threeDProviderRouteJson: '',
  threeDTargetFormats: 'glb',
  threeDOutputFormat: 'glb',
  threeDSelectedAsset: '',
  threeDBlenderExecutable: '',
  threeDLastJob: null,
  threeDViewportPath: '',
  threeDViewportMode: 'shaded',
  threeDViewportPayload: null,
  threeDViewportResult: null,
  threeDViewportYaw: 0.65,
  threeDViewportPitch: -0.25,
  threeDViewportZoom: 220,
  comfyStatus: null,
  comfyWorkflows: null,
  comfyMediaPackage: null,
  flexAvatarStatus: null,
  flexAvatarAssets: { inputs: [], avatar_codes: [], renderings: [], manifests: [], training_bundles: [], driver_sequences: [] },
  flexAvatarOutput: null,
  flexAvatarSourceManifest: '',
  flexAvatarDriverManifest: '',
  flexAvatarMode: 'single',
  flexAvatarAvatarName: 'avatar',
  flexAvatarLastJob: null,
  annotationModel: '',
  annotationModelStatus: null,
  annotationOutput: null,
  detectionModels: [],
  segmentationModels: [],
  detectionModel: '',
  segmentationModel: '',
  detectionModelStatus: null,
  segmentationModelStatus: null,
  detectionClassInfo: null,
  segmentationClassInfo: null,
  detectionClassQuery: '',
  segmentationClassQuery: '',
  detectionClassSearch: '',
  segmentationClassSearch: '',
  detectionOutput: null,
  segmentationOutput: null,
  detectionDraftBbox: null,
  segmentationPolygon: [],
  segmentationPromptBbox: null,
  segmentationPromptPoints: [],
  segmentationPointTool: 'positive',
  segmentationOutputMode: 'instance',
  segmentationDrawMode: 'polygon',
  segmentationGuideEnabled: false,
  segmentationGuideModel: '',
  detectionLayerSelection: new Set(),
  segmentationLayerSelection: new Set(),
  detectionPreviewSelection: new Set(),
  segmentationPreviewSelection: new Set(),
  detectionEditingLayerId: null,
  segmentationEditingLayerId: null,
  detectionMergeOperation: 'union',
  segmentationMergeOperation: 'union',
  segmentationEditTool: 'brush',
  segmentationBrushSize: 32,
  segmentationBrushOpacity: 1,
  segmentationBrushHardness: 0.9,
  segmentationLayerColor: '#22c55e',
  segmentationLayerOpacity: 0.55,
  segmentationMagicMethod: 'flood_fill',
  segmentationMagicTolerance: 24,
  segmentationMagicMode: 'add',
  segmentationMagicFeather: 0,
  segmentationMagicGrow: 0,
  segmentationMagicInvert: false,
  segmentationMergeThreshold: 1,
  segmentationMergeFeather: 0,
  segmentationMergeGrow: 0,
  segmentationEditorMergeMode: 'add',
  segmentationMergeBaseId: null,
  externalApps: null,
  externalAppOutput: null,
  quickExternalTool: 'topaz_photo_ai',
  browserStatus: null,
  browserOutput: null,
  mcpToolStatus: null,
  jobDetailId: null,
  lastModelRunJob: null,
  migrationSourceText: '',
  migrationOutput: null,
  migrationLastJob: null,
  formMemory: {},
  lastUserInteractionAt: 0,
  filters: { q: '', tag: '', dataset_id: '', media_type: '', duplicate: '' },
};

const tabs = [
  'Dashboard', 'Import', 'Gallery', 'Tag Editor', 'Detection & Boxes', 'Segmentation & Masks', 'Pose & 3D', '3D Studio', '3D Viewport', 'ComfyUI Bridge', 'FlexAvatar', 'Compare', 'Batch Tags',
  'Prediction Analytics', 'Media Tools', 'Reference Finder', 'Source Browser', 'Assistant', 'Orchestrate', 'Models', 'Augment', 'Downloads', 'Presets',
  'Tag Dictionaries', 'Database', 'Install Migration', 'Code Assistant', 'Agent Tools', 'MCP Tools', 'Future Modalities', 'Settings', 'Help & Workflows', 'Jobs'
];

const EXTERNAL_APP_OPTIONS = [
  ['topaz_photo_ai', 'Topaz Photo AI'],
  ['topaz_gigapixel', 'Topaz Gigapixel'],
  ['topaz_denoise', 'Topaz DeNoise'],
  ['topaz_sharpen', 'Topaz Sharpen'],
  ['topaz_mask', 'Topaz Mask'],
  ['krita', 'Krita'],
  ['comfyui', 'ComfyUI']
];

async function api(path, options = {}) {
  const opts = { ...options };
  const originalBody = opts.body;
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(path, opts);
  if (!res.ok) {
    const raw = await res.text();
    let detail = raw;
    let parsed = null;
    try {
      parsed = JSON.parse(raw);
      detail = parsed.detail || parsed.error || parsed.message || raw;
      if (typeof detail !== 'string') detail = JSON.stringify(detail, null, 2);
    } catch (_) {}
    const message = detail || `${res.status} ${res.statusText}`;
    state.lastApiError = {
      time: new Date().toISOString(),
      method: opts.method || 'GET',
      path,
      status: res.status,
      statusText: res.statusText,
      message,
      detail,
      raw,
      parsed,
      requestBody: originalBody instanceof FormData ? '[FormData]' : originalBody
    };
    const err = new Error(message);
    err.status = res.status;
    err.statusText = res.statusText;
    err.path = path;
    err.method = opts.method || 'GET';
    err.detail = detail;
    err.raw = raw;
    err.parsed = parsed;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (key === 'class') node.className = value;
    else if (key === 'html') node.innerHTML = value;
    else if (key === 'style') node.setAttribute('style', value);
    else if (key.startsWith('on') && typeof value === 'function') node.addEventListener(key.slice(2), value);
    else if (key === 'checked') node.checked = Boolean(value);
    else if (key === 'disabled') node.disabled = Boolean(value);
    else if (key === 'value') node.value = value ?? '';
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  const list = Array.isArray(children) ? children : [children];
  for (const child of list) {
    if (child === undefined || child === null) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function toast(message, ok = true) {
  const full = String(message ?? '');
  const visible = full.length > 700 ? `${full.slice(0, 700)}…` : full;
  const box = el('div', { class: `badge toast ${ok ? 'ok' : 'bad'}`, title: full }, visible);
  document.body.append(box);
  setTimeout(() => box.remove(), 5200);
}

async function copyText(text, label = 'Copied') {
  const value = String(text ?? '');
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value);
    else throw new Error('Clipboard API unavailable');
    toast(label);
  } catch (_) {
    const area = el('textarea', { style: 'position:fixed;left:-9999px;top:0' }, value);
    document.body.append(area);
    area.focus();
    area.select();
    try { document.execCommand('copy'); toast(label); } catch (err) { toast('Copy failed; use the visible log text.', false); }
    area.remove();
  }
}

function downloadTextFile(filename, text) {
  const blob = new Blob([String(text ?? '')], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = el('a', { href: url, download: filename || 'data-curation-tool-log.txt' });
  document.body.append(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 500);
}

function formKey(tab, node, index) {
  const explicit = node.getAttribute('data-form-key') || '';
  const label = explicit || node.getAttribute('aria-label') || node.getAttribute('placeholder') || node.getAttribute('title') || node.name || node.id || `${node.tagName}:${index}`;
  return `${tab}::${node.tagName.toLowerCase()}::${label}::${explicit ? 'stable' : index}`;
}
function formControls(root = document.getElementById('app')) {
  return root ? [...root.querySelectorAll('input, select, textarea')] : [];
}
function isTextEditingElement(node = document.activeElement) {
  if (!node) return false;
  const tag = String(node.tagName || '').toUpperCase();
  if (tag === 'TEXTAREA') return true;
  if (tag === 'INPUT') {
    const type = String(node.type || 'text').toLowerCase();
    return !['button','checkbox','color','file','hidden','image','radio','range','reset','submit'].includes(type);
  }
  return Boolean(node.isContentEditable);
}
function isSelectEditingElement(node = document.activeElement) {
  return Boolean(node && String(node.tagName || '').toUpperCase() === 'SELECT');
}
function isRenderSensitiveControl(node = document.activeElement) {
  if (!node) return false;
  const root = document.getElementById('app');
  if (root && !root.contains(node)) return false;
  return isTextEditingElement(node) || isSelectEditingElement(node);
}
function markControlInteraction(node = document.activeElement, holdMs = 4500) {
  const root = document.getElementById('app');
  if (!root || (node && root.contains(node))) state.lastUserInteractionAt = Date.now();
  if (node && root && root.contains(node)) {
    const tag = String(node.tagName || '').toUpperCase();
    const inputType = String(node.type || '').toLowerCase();
    if (tag === 'INPUT' && ['checkbox','radio','range'].includes(inputType)) {
      state.controlInteractionHoldUntil = Date.now() + 2500;
      return;
    }
  }
  if (!isRenderSensitiveControl(node)) return;
  const isSelect = isSelectEditingElement(node);
  // Native SELECT menus live outside the DOM. While a dropdown is open, normal
  // polling renders can close it even when the app later restores focus. Some
  // browsers fire focusout while the native menu is still open, so keep the hold
  // long and release it mainly on change or an explicit outside click.
  const hold = isSelect ? Math.max(Number(holdMs || 0), 90000) : holdMs;
  if (isSelect) state.dropdownInteractionActive = true;
  state.controlInteractionHoldUntil = Date.now() + Math.max(500, hold);
}

function releaseDropdownInteractionSoon(delay = 900) {
  const until = Date.now() + Math.max(250, delay);
  state.controlInteractionHoldUntil = Math.min(Number(state.controlInteractionHoldUntil || 0) || until, until);
  setTimeout(() => { state.dropdownInteractionActive = false; flushDeferredRenderWhenSafe(); }, Math.max(120, delay + 40));
}
function recentUserInteraction(ms = 6000) {
  return Date.now() - Number(state.lastUserInteractionAt || 0) < ms;
}
function shouldDeferControlRender() {
  const hardHold = isRenderSensitiveControl() || state.dropdownInteractionActive || Date.now() < Number(state.controlInteractionHoldUntil || 0);
  if (hardHold) return true;
  // Jobs, Models, Gallery, and the Tag Editor contain dense controls/lists.
  // Polling renders on these tabs are expensive and can interrupt selection,
  // scrolling, and model-menu inspection, so defer only briefly after user input
  // while live DOM progress updaters keep bars/statuses current.
  const passiveSensitiveTabs = new Set(['Jobs', 'Models', 'Gallery', 'Tag Editor']);
  return passiveSensitiveTabs.has(state.tab) && recentUserInteraction(state.tab === 'Gallery' ? 1800 : 6500);
}
['focusin','pointerdown','mousedown','mouseup','click','touchstart','touchmove','keydown','keyup','input','wheel'].forEach(eventName => {
  document.addEventListener(eventName, event => markControlInteraction(event.target), true);
});
document.addEventListener('change', event => {
  if (String(event.target?.tagName || '').toUpperCase() === 'SELECT') releaseDropdownInteractionSoon(1800);
}, true);
document.addEventListener('focusout', event => {
  if (String(event.target?.tagName || '').toUpperCase() === 'SELECT') releaseDropdownInteractionSoon(12000);
}, true);
document.addEventListener('pointerdown', event => {
  if (!state.dropdownInteractionActive) return;
  if (String(event.target?.tagName || '').toUpperCase() !== 'SELECT') releaseDropdownInteractionSoon(900);
}, true);
function activeControlSnapshot(tab = state.tab) {
  const root = document.getElementById('app');
  const node = document.activeElement;
  if (!root || !node || !root.contains(node) || !['INPUT','SELECT','TEXTAREA'].includes(String(node.tagName || '').toUpperCase())) return null;
  if (node.type === 'file') return null;
  const controls = formControls(root);
  const index = controls.indexOf(node);
  if (index < 0) return null;
  const snap = { key: formKey(tab, node, index), tag: node.tagName, value: node.value, scrollTop: node.scrollTop || 0, scrollLeft: node.scrollLeft || 0 };
  if (typeof node.selectionStart === 'number') {
    snap.selectionStart = node.selectionStart;
    snap.selectionEnd = node.selectionEnd;
    snap.selectionDirection = node.selectionDirection || 'none';
  }
  return snap;
}
function restoreActiveControl(snapshot, tab = state.tab) {
  if (!snapshot) return;
  const root = document.getElementById('app');
  if (!root) return;
  const controls = formControls(root);
  const target = controls.find((node, index) => formKey(tab, node, index) === snapshot.key);
  if (!target) return;
  try { target.focus({ preventScroll: true }); } catch (_) { try { target.focus(); } catch (__) {} }
  if (target.value !== undefined && snapshot.value !== undefined && target.value !== snapshot.value && target.dataset.noPersist !== '1') target.value = snapshot.value;
  if (typeof target.setSelectionRange === 'function' && typeof snapshot.selectionStart === 'number') {
    try { target.setSelectionRange(snapshot.selectionStart, snapshot.selectionEnd, snapshot.selectionDirection || 'none'); } catch (_) {}
  }
  target.scrollTop = snapshot.scrollTop || 0;
  target.scrollLeft = snapshot.scrollLeft || 0;
}
function renderOrDeferForEditing() {
  if (shouldDeferControlRender()) {
    state.renderDeferredForEditing = true;
    updateLiveStatusDom();
    setTimeout(flushDeferredRenderWhenSafe, 700);
    return false;
  }
  state.renderDeferredForEditing = false;
  render(true, true);
  return true;
}
function flushDeferredRenderWhenSafe() {
  if (!state.renderDeferredForEditing) return;
  if (shouldDeferControlRender()) {
    const wait = Math.max(120, Math.min(1200, Number(state.controlInteractionHoldUntil || 0) - Date.now() + 60));
    setTimeout(flushDeferredRenderWhenSafe, wait);
    return;
  }
  state.renderDeferredForEditing = false;
  render(true, true);
}
document.addEventListener('focusout', () => {
  if (!state.renderDeferredForEditing) return;
  setTimeout(flushDeferredRenderWhenSafe, 120);
});
function snapshotFormState(tab = state.tab) {
  const root = document.getElementById('app');
  if (!root) return;
  const values = {};
  [...root.querySelectorAll('input, select, textarea')].forEach((node, index) => {
    if (node.type === 'file' || node.dataset.noPersist === '1') return;
    const key = formKey(tab, node, index);
    if (node.tagName === 'SELECT' && node.multiple) values[key] = [...node.selectedOptions].map(o => o.value);
    else if (node.type === 'checkbox') values[key] = node.checked;
    else values[key] = node.value;
  });
  state.formMemory[tab] = values;
  try { sessionStorage.setItem('dctFormMemory', JSON.stringify(state.formMemory)); } catch (_) {}
}
function restoreFormState(tab = state.tab) {
  if (!Object.keys(state.formMemory || {}).length) {
    try { state.formMemory = JSON.parse(sessionStorage.getItem('dctFormMemory') || '{}') || {}; } catch (_) { state.formMemory = {}; }
  }
  const values = state.formMemory?.[tab];
  if (!values) return;
  const root = document.getElementById('app');
  if (!root) return;
  [...root.querySelectorAll('input, select, textarea')].forEach((node, index) => {
    if (node.type === 'file' || node.dataset.noPersist === '1') return;
    const key = formKey(tab, node, index);
    if (!(key in values)) return;
    const value = values[key];
    if (node.tagName === 'SELECT' && node.multiple && Array.isArray(value)) {
      [...node.options].forEach(o => { o.selected = value.includes(o.value); });
    } else if (node.type === 'checkbox') node.checked = Boolean(value);
    else node.value = value ?? '';
  });
}

function scrollNodeKey(node, index) {
  if (!node) return `node:${index}`;
  if (node.id) return `id:${node.id}`;
  const dataKey = node.getAttribute('data-scroll-key') || node.getAttribute('data-role') || node.getAttribute('aria-label') || node.getAttribute('name') || node.getAttribute('title') || '';
  const classKey = String(node.className || '').trim().replace(/\s+/g, '.');
  return `${node.tagName.toLowerCase()}::${dataKey || classKey || 'scroll'}::${index}`;
}
function isScrollableNode(node) {
  if (!node || node === document.body || node === document.documentElement) return false;
  return (node.scrollHeight > node.clientHeight + 2) || (node.scrollWidth > node.clientWidth + 2);
}
function snapshotScrollState(tab = state.tab) {
  const root = document.getElementById('app');
  const elements = [];
  if (root) {
    [...root.querySelectorAll('*')].forEach((node, index) => {
      if (!isScrollableNode(node)) return;
      elements.push({ key: scrollNodeKey(node, index), top: node.scrollTop || 0, left: node.scrollLeft || 0 });
    });
  }
  state.uiScrollMemory[tab] = { windowX: window.scrollX || 0, windowY: window.scrollY || 0, elements };
  try { sessionStorage.setItem('dctScrollMemory', JSON.stringify(state.uiScrollMemory)); } catch (_) {}
}
function restoreScrollState(tab = state.tab) {
  if (!Object.keys(state.uiScrollMemory || {}).length) {
    try { state.uiScrollMemory = JSON.parse(sessionStorage.getItem('dctScrollMemory') || '{}') || {}; } catch (_) { state.uiScrollMemory = {}; }
  }
  const memory = state.uiScrollMemory?.[tab];
  if (!memory) return;
  const apply = () => {
    try { window.scrollTo(memory.windowX || 0, memory.windowY || 0); } catch (_) {}
    const root = document.getElementById('app');
    if (!root) return;
    const byKey = new Map();
    [...root.querySelectorAll('*')].forEach((node, index) => {
      if (isScrollableNode(node)) byKey.set(scrollNodeKey(node, index), node);
    });
    for (const row of memory.elements || []) {
      const node = byKey.get(row.key);
      if (!node) continue;
      node.scrollTop = row.top || 0;
      node.scrollLeft = row.left || 0;
    }
  };
  apply();
  requestAnimationFrame(apply);
  setTimeout(apply, 0);
}
function scheduleRender(delay = 80) {
  if (state.renderScheduled) return;
  state.renderScheduled = true;
  setTimeout(() => { state.renderScheduled = false; renderOrDeferForEditing(); }, delay);
}

function setTab(tab) { snapshotFormState(); snapshotScrollState(); state.tab = tab; render(false); }
const CATEGORY_ALIASES = {
  '0': 'general', '1': 'artist', '2': 'rating', '3': 'copyright', '4': 'character', '5': 'species', '6': 'invalid', '7': 'meta', '8': 'lore',
  tag: 'general', tags: 'general', copy: 'copyright', series: 'copyright', deprecated: 'invalid', artstyle: 'style', art_style: 'style',
  rating_safe: 'rating', rating_questionable: 'rating', rating_explicit: 'rating'
};
function normalizeCategoryKey(category) {
  const raw = String(category || 'unknown').trim().toLowerCase().replace(/\s+/g, '_');
  return CATEGORY_ALIASES[raw] || raw || 'unknown';
}
function activeProfile() { return state.tagProfiles.find(p => p.key === state.tagProfile) || state.tagProfiles[0] || { key: 'e621', label: 'e621', categories: [], precedence: [] }; }
function categories(profileKey = state.tagProfile) { return (state.tagProfiles.find(p => p.key === profileKey) || activeProfile()).categories || []; }
function categoryByKey(key) { const normalized = normalizeCategoryKey(key); return categories().find(c => c.key === normalized) || { key: normalized, label: normalized, css_class: `cat-${normalized || 'unknown'}` }; }
function categoryCss(category) { const normalized = normalizeCategoryKey(category); const c = categoryByKey(normalized); return c.css_class || `cat-${normalized || 'unknown'}`; }
function categoryColor(category) {
  const colors = state.settings?.category_colors || {};
  const key = normalizeCategoryKey(category);
  return colors[key] || colors[category] || '';
}
function categoryStyle(category) {
  const color = categoryColor(category);
  return color ? `--chip-color:${color}; border-color:${color}; background: color-mix(in srgb, ${color} 22%, transparent);` : '';
}
function card(title, children) { return el('section', { class: 'card' }, [el('h2', {}, title), ...children]); }
function modelDownloadWorkerCount() {
  if (state.modelDownloadQueueMode === 'parallel') return Math.max(1, Number(state.settings.model_download_parallel_workers || 4));
  if (state.modelDownloadQueueMode === 'serial') return 1;
  return state.settings.model_download_serial_queue === false ? Math.max(1, Number(state.settings.model_download_parallel_workers || 4)) : 1;
}
function modelDownloadModeLabel() { return modelDownloadWorkerCount() <= 1 ? 'serial queue / one transfer at a time' : `${modelDownloadWorkerCount()} parallel file transfers`; }
function modelDownloadModeControl() {
  const sel = el('select', { title: 'Choose serial queue to protect large model downloads, or parallel transfers when you want more bandwidth use.', onchange: e => { state.modelDownloadQueueMode = e.target.value; render(true, true); } }, [
    el('option', { value: 'serial' }, 'Serial queue: one model file transfer at a time'),
    el('option', { value: 'parallel' }, 'Parallel transfers: split bandwidth across files'),
    el('option', { value: 'settings' }, 'Use Settings default')
  ]);
  sel.value = state.modelDownloadQueueMode || (state.settings.model_download_serial_queue === false ? 'parallel' : 'serial');
  return sel;
}
function errorLogCard(title = 'Last Error / Debug Details', err = state.lastApiError) {
  if (!err) return null;
  const payload = typeof err === 'string' ? { message: err } : err;
  const text = JSON.stringify(payload, null, 2);
  return card(title, [
    el('p', { class: 'muted' }, 'Full browser-visible error/debug payload. Use this when a toast or progress circle truncates the useful part of a model/job failure.'),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => copyText(text, 'Copied error details') }, 'Copy Full Error'),
      el('button', { class: 'secondary', onclick: () => downloadTextFile(`dct_error_${Date.now()}.json`, text) }, 'Download Error JSON'),
      el('button', { class: 'secondary', onclick: () => { state.lastApiError = null; state.lastTagSelectionError = null; render(true, true); } }, 'Clear Error')
    ]),
    el('pre', { class: 'log full-log debug-log' }, text)
  ]);
}
function isUserCustomModel(m) { return Boolean(m?.user_custom || m?.custom || String(m?.name || '').startsWith('custom-user-')); }
function modelIsApi(m) { return Boolean(m?.cloud || ['openai','openrouter','anthropic','cloud'].includes(String(m?.provider || '').toLowerCase())); }
function modelKindSet(m) { return new Set([...(m?.capabilities || []), String(m?.kind || '')].map(x => String(x || '').toLowerCase())); }
function modelCategoryDisplay(m) {
  const caps = modelKindSet(m);
  const kind = String(m?.kind || '').toLowerCase();
  let key = kind || 'model';
  let label = kind || 'Model';
  let color = '#94a3b8';
  let rank = 3;
  if (caps.has('mcp') || caps.has('mcp_tool') || kind === 'mcp_tool') { key = 'mcp_tool'; label = 'MCP tool bridge'; color = '#f472b6'; rank = 0.7; }
  else if (caps.has('text_to_3d') || caps.has('image_to_3d') || caps.has('multi_image_to_3d') || caps.has('video_to_3d') || caps.has('3d_generation') || kind === '3d_generation') { key = '3d_generation'; label = '3D generation'; color = '#fb923c'; rank = 2.55; }
  else if (caps.has('rigging') || caps.has('avatar_3d') || caps.has('3d_tool') || kind === 'avatar_3d' || kind === '3d_tool' || kind === 'rigging') { key = '3d_tool'; label = '3D rig/avatar/tool'; color = '#facc15'; rank = 2.6; }
  else if (modelIsApi(m)) { key = 'api'; label = `API / Cloud ${kind || 'model'}`; color = '#cbd5e1'; rank = 9; }
  else if (caps.has('vlm') || caps.has('image_text_to_text') || kind === 'vlm') { key = 'vlm'; label = 'VLM / image+text assistant'; color = '#22d3ee'; rank = 0; }
  else if (caps.has('llm') || caps.has('assistant') || kind === 'llm' || kind === 'assistant') { key = 'llm'; label = 'LLM / assistant'; color = '#c084fc'; rank = 1; }
  else if (caps.has('tag') || caps.has('auto_tag') || kind === 'tagger') { key = 'tagger'; label = 'Tagger'; color = '#34d399'; rank = 2; }
  else if (caps.has('caption') || kind === 'captioner') { key = 'captioner'; label = 'Captioner'; color = '#fbbf24'; rank = 2.1; }
  else if (caps.has('speech_to_text') || caps.has('stt') || kind === 'stt') { key = 'stt'; label = 'Speech-to-text'; color = '#38bdf8'; rank = 2.12; }
  else if (caps.has('text_to_speech') || caps.has('tts') || kind === 'tts') { key = 'tts'; label = 'Text-to-speech'; color = '#a3e635'; rank = 2.14; }
  else if (caps.has('speaker_diarization') || caps.has('diarization') || kind === 'audio_diarization') { key = 'audio_diarization'; label = 'Audio diarization'; color = '#67e8f9'; rank = 2.16; }
  else if (caps.has('rating') || kind === 'rating') { key = 'rating'; label = 'Rating model'; color = '#fb7185'; rank = 2.2; }
  else if (caps.has('classify') || caps.has('image_classification') || kind === 'classifier') { key = 'classifier'; label = 'Classifier'; color = '#60a5fa'; rank = 2.3; }
  else if (caps.has('detect') || kind === 'detection') { key = 'detection'; label = 'Detector'; color = '#f97316'; rank = 3; }
  else if (caps.has('segment') || kind === 'segmentation') { key = 'segmentation'; label = 'Segmentation'; color = '#2dd4bf'; rank = 3.1; }
  if (isUserCustomModel(m)) { label = `Custom ${label}`; rank -= 0.25; }
  return { key, label, color, rank };
}
function sortedModels(rows = state.models) { return [...(rows || [])].sort((a, b) => { const ac = isUserCustomModel(a) ? 0 : 1; const bc = isUserCustomModel(b) ? 0 : 1; if (ac !== bc) return ac - bc; const ar = modelCategoryDisplay(a).rank; const br = modelCategoryDisplay(b).rank; if (ar !== br) return ar - br; const ak = String(a.kind || ''); const bk = String(b.kind || ''); if (ak !== bk) return ak.localeCompare(bk); return String(a.label || a.name || '').localeCompare(String(b.label || b.name || '')); }); }
function modelLoadedInstanceCount(mOrName) {
  const name = typeof mOrName === 'string' ? mOrName : (mOrName?.name || mOrName?.model_name || '');
  const catalog = typeof mOrName === 'object' ? mOrName : (state.models || []).find(m => m.name === name);
  const lifecycle = modelLifecycle(mOrName);
  const fromCatalog = Number(catalog?.loaded_instance_count || 0);
  const fromLifecycle = Number(lifecycle?.loaded_instance_count || 0);
  return Math.max(0, fromCatalog, fromLifecycle, modelLoaded(mOrName) ? 1 : 0);
}
function modelDownloadIssues(m) { const issues = m?.download_integrity?.issues || m?.local_integrity_issues || []; return Array.isArray(issues) ? issues.filter(Boolean) : []; }
function modelSupportWarnings(m) { const warnings = m?.download_integrity?.warnings || m?.local_support_warnings || []; return Array.isArray(warnings) ? warnings.filter(Boolean) : []; }
function modelHFAccessLabel(m) {
  const access = String(m?.hf_access || '').toLowerCase();
  if (m?.requires_hf_token || access === 'gated' || access === 'restricted') return 'HF TOKEN / TERMS REQUIRED';
  if (access === 'hf_token_recommended' || access === 'token_recommended' || access === 'token-recommended') return 'HF TOKEN RECOMMENDED';
  return '';
}
function modelHFAccessTitle(m) {
  const label = modelHFAccessLabel(m);
  if (!label) return '';
  const note = m?.hf_access_note || m?.memory_note || '';
  return `${label}${note ? ': ' + note : ''}`;
}
function modelStatusBits(m) {
  const bits = [];
  const dl = stageStatus(m, 'download');
  const load = stageStatus(m, 'load');
  const inf = stageStatus(m, 'inference');
  const issues = modelDownloadIssues(m);
  const downloaded = Boolean(m?.downloaded);
  const loadedCount = modelLoadedInstanceCount(m);
  const offloaded = Boolean(m?.offloaded_to_cpu || (m?.loaded_instances || []).some(x => x && x.offloaded_to_cpu));
  if (stageActive(m, 'download')) bits.push(`DL ${String(dl.state || 'running')} ${statusPercent(dl)}%`);
  else if (downloaded) bits.push('DOWNLOADED');
  else if (m?.download_supported) bits.push('NOT DOWNLOADED');
  if (issues.length) bits.push('INCOMPLETE');
  if (stageActive(m, 'load')) bits.push(`${String(load.state || 'load').toUpperCase()} ${statusPercent(load)}%`);
  else if (loadedCount) bits.push(offloaded ? `CPU OFFLOADED x${loadedCount}` : `LOADED x${loadedCount}`);
  if (stageActive(m, 'inference')) bits.push(`INFER ${statusPercent(inf)}%`);
  if (m?.cloud) bits.push('API');
  return bits;
}
function modelStatusClass(m) {
  if (m?.offloaded_to_cpu || (m?.loaded_instances || []).some(x => x && x.offloaded_to_cpu)) return 'model-option-offloaded';
  if (modelLoadedInstanceCount(m)) return 'model-option-loaded';
  if (stageActive(m, 'download') || stageActive(m, 'load') || stageActive(m, 'inference')) return 'model-option-active';
  if (m?.downloaded) return 'model-option-downloaded';
  if (modelDownloadIssues(m).length) return 'model-option-repair';
  if (m?.download_supported) return 'model-option-missing';
  return 'model-option-ready';
}
function primeModelLifecycleForSelection(mOrName) { const m = typeof mOrName === 'object' ? mOrName : (state.models || []).find(row => row.name === mOrName); const name = m?.name || String(mOrName || ''); if (!name) return; if (m?.downloaded) setOptimisticModelStage(name, 'download', 'completed', 1, 'Model files are present'); if (modelLoaded(name) || m?.loaded) setOptimisticModelStage(name, 'load', 'completed', 1, 'Model is loaded in memory'); else if (!stageActive(name, 'load')) setOptimisticModelStage(name, 'load', 'idle', 0, 'Model not loaded yet'); if (!stageActive(name, 'inference')) setOptimisticModelStage(name, 'inference', 'idle', 0, 'Selected for inference'); }
function sortedTagSelectionModels(rows = state.models) { return [...(rows || [])].sort((a, b) => { const ar = modelCategoryDisplay(a).rank; const br = modelCategoryDisplay(b).rank; if (ar !== br) return ar - br; const as = modelLoadedInstanceCount(a) ? 0 : a.downloaded ? 1 : 2; const bs = modelLoadedInstanceCount(b) ? 0 : b.downloaded ? 1 : 2; if (as !== bs) return as - bs; return String(a.label || a.name || '').localeCompare(String(b.label || b.name || '')); }); }
function modelCatalogActive(m) { return Boolean(modelLoaded(m) || stageActive(m, 'load') || stageActive(m, 'inference') || stageActive(m, 'training')); }
function modelActiveForCatalog(m) { return modelCatalogActive(m); }
function sortedModelsForModelsTab(rows = state.models) { return [...(rows || [])].sort((a, b) => { const aa = modelCatalogActive(a) ? 0 : 1; const ba = modelCatalogActive(b) ? 0 : 1; if (aa !== ba) return aa - ba; const ac = isUserCustomModel(a) ? 0 : 1; const bc = isUserCustomModel(b) ? 0 : 1; if (ac !== bc) return ac - bc; const ar = modelCategoryDisplay(a).rank; const br = modelCategoryDisplay(b).rank; if (ar !== br) return ar - br; return String(a.label || a.name || '').localeCompare(String(b.label || b.name || '')); }); }
function sortedModelCatalogRows(rows = state.models) { return sortedModelsForModelsTab(rows); }
function modelActiveHighlightStyle(m) { if (!modelCatalogActive(m) || isUserCustomModel(m)) return ''; const cat = modelCategoryDisplay(m); return `--model-kind-color:${cat.color}; --model-category-color:${cat.color}; border-color:${cat.color}; background: color-mix(in srgb, ${cat.color} 18%, rgba(15,23,42,.70)); box-shadow: 0 0 0 1px color-mix(in srgb, ${cat.color} 55%, transparent), 0 10px 34px color-mix(in srgb, ${cat.color} 16%, transparent);`; }
function modelMemorySummary(m) {
  const profiles = m?.runtime_vram_profiles || {};
  const parts = [];
  const order = ['bf16', 'fp16', '8bit', 'sfp8', '4bit', 'q4_0'];
  for (const key of order) {
    const val = profiles[key];
    if (val !== undefined && val !== null && Number(val) > 0) parts.push(`${key} ~${Number(val).toFixed(1)}GB`);
  }
  if (!parts.length && Number(m?.vram_gb || 0) > 0) parts.push(`VRAM ~${Number(m.vram_gb).toFixed(1)}GB`);
  if (!parts.length && Number(m?.size_gb || 0) > 0) parts.push(`weights ~${Number(m.size_gb).toFixed(1)}GB`);
  return parts.join(' / ');
}
function modelMemoryTitle(m) {
  const mem = modelMemorySummary(m);
  const note = m?.memory_note ? ` ${m.memory_note}` : '';
  return `${mem ? 'Memory estimate: ' + mem + '.' : 'No VRAM estimate in registry.'}${note}`;
}
function modelLabel(m) { const bits = []; const cat = modelCategoryDisplay(m); const mem = modelMemorySummary(m); const hf = modelHFAccessLabel(m); if (isUserCustomModel(m)) bits.push(`CUSTOM:${m.custom_model_category || m.custom_category || m.kind || 'model'}`); if (mem) bits.push(mem); if (hf) bits.push(hf); bits.push(...modelStatusBits(m)); if (m.installed || !m.optional) bits.push('adapter'); return `${isUserCustomModel(m) ? '★ ' : ''}${m.label || m.name} · ${cat.label}${bits.length ? ' · ' + bits.join(' / ') : ''}`; }
function modelOptionNode(m) { const cat = modelCategoryDisplay(m); const status = modelStatusBits(m).join(' / ') || m.status_summary || 'no status'; const issues = modelDownloadIssues(m); const warnings = modelSupportWarnings(m); return el('option', { value: m.name, class: `${isUserCustomModel(m) ? 'custom-model-option ' : ''}model-option-${cat.key} ${modelStatusClass(m)}`, title: `${cat.label}; kind=${m.kind || 'unknown'}; provider=${m.provider || 'unknown'}; status=${status}; loaded instances=${modelLoadedInstanceCount(m)}; ${m.local ? 'local/builtin' : modelIsApi(m) ? 'API/cloud' : 'downloadable/localizable'}; ${modelMemoryTitle(m)}${modelHFAccessTitle(m) ? '; ' + modelHFAccessTitle(m) : ''}${issues.length ? '; hard integrity issues=' + issues.join(' | ') : ''}${warnings.length ? '; support warnings=' + warnings.join(' | ') : ''}`, style: `color:${cat.color};` }, modelLabel(m)); }
function modelOptions(filter = () => true) { return sortedModels(state.models).filter(filter).map(modelOptionNode); }
function selectHasValue(select, value) {
  return Boolean(select && value !== undefined && value !== null && [...select.options].some(o => o.value === String(value)));
}
function setSelectValue(select, value) {
  if (!selectHasValue(select, value)) return false;
  select.value = String(value);
  return true;
}
function rememberSelect(stateKey, select, fallback = '', renderOnChange = false) {
  if (!select) return '';
  select.dataset.noPersist = '1';
  const remembered = state[stateKey];
  if (!setSelectValue(select, remembered)) setSelectValue(select, fallback);
  if (!select.value && select.options.length) select.value = select.options[0].value;
  state[stateKey] = select.value || '';
  select.addEventListener('change', () => { state[stateKey] = select.value || ''; if (renderOnChange) render(); });
  return state[stateKey];
}

const MODEL_LIFECYCLE_STAGES = ['download', 'load', 'inference', 'training'];
const MODEL_STAGE_LABELS = { download: 'Download', load: 'Load', inference: 'Inference', training: 'Training' };
const MODEL_ACTIVE_STATES = new Set(['queued', 'running', 'unloading']);
function defaultStageStatus(modelName = '', stage = '') {
  return { model_name: modelName || '', stage, state: 'idle', active: false, progress: 0, percent: 0, message: 'Idle', job_id: null, error: null };
}
function lifecycleModels() { return state.modelStatuses?.models || {}; }
function modelLifecycle(mOrName) {
  const name = typeof mOrName === 'string' ? mOrName : (mOrName?.name || '');
  return lifecycleModels()[name] || (typeof mOrName === 'object' ? (mOrName.lifecycle || {}) : {}) || {};
}
function stageStatus(mOrName, stage) {
  const name = typeof mOrName === 'string' ? mOrName : (mOrName?.name || '');
  return modelLifecycle(mOrName)[stage] || defaultStageStatus(name, stage);
}
function aggregateStageStatus(stage) { return state.modelStatuses?.aggregate?.[stage] || defaultStageStatus('', stage); }
function isStageActive(status) { return Boolean(status?.active) || MODEL_ACTIVE_STATES.has(String(status?.state || '').toLowerCase()); }
function stageActive(mOrName, stage) { return isStageActive(stageStatus(mOrName, stage)); }
function modelLoaded(mOrName) {
  const name = typeof mOrName === 'string' ? mOrName : (mOrName?.name || mOrName?.model_name || '');
  const catalog = typeof mOrName === 'object' ? mOrName : (state.models || []).find(m => m.name === name);
  const lifecycle = modelLifecycle(mOrName);
  return Boolean(catalog?.loaded || lifecycle?.loaded);
}
function modelBusy(mOrName, stages = ['download', 'load']) { return stages.some(stage => stageActive(mOrName, stage)); }
function statusPercent(status) {
  if (Number.isFinite(Number(status?.percent))) return Math.max(0, Math.min(100, Math.round(Number(status.percent))));
  return Math.max(0, Math.min(100, Math.round(Number(status?.progress || 0) * 100)));
}
function stageCircle(status, label) {
  const pct = statusPercent(status);
  const stageName = status?.stage || Object.entries(MODEL_STAGE_LABELS).find(([, v]) => v === label)?.[0] || String(label || '').toLowerCase();
  const stateName = String(status?.state || 'idle').toLowerCase();
  const modelPart = status?.model_name ? ` · ${status.model_name}` : '';
  const jobPart = status?.job_id ? ` · job #${status.job_id}` : '';
  const msg = status?.message || (stateName === 'idle' ? 'Idle' : stateName);
  const title = `${label}: ${pct}% · ${msg}${modelPart}${jobPart}`;
  return el('div', { class: `stage-pill ${stateName} ${isStageActive(status) ? 'active' : ''}`, title, 'data-lifecycle-model': status?.model_name || '__aggregate__', 'data-lifecycle-stage': stageName }, [
    el('div', { class: 'progress-ring', style: `--pct:${pct}%`, 'data-role': 'stage-ring' }, el('span', { 'data-role': 'stage-percent' }, `${pct}%`)),
    el('div', { class: 'stage-text' }, [
      el('strong', {}, label),
      el('span', { class: 'muted tiny', 'data-role': 'stage-state' }, `${stateName}${modelPart}${jobPart}`),
      msg ? el('span', { class: 'muted tiny', 'data-role': 'stage-message' }, msg) : null
    ])
  ]);
}
function modelLifecycleStrip(mOrName, compact = false) {
  return el('div', { class: `model-lifecycle ${compact ? 'compact' : ''}` }, MODEL_LIFECYCLE_STAGES.map(stage => stageCircle(stageStatus(mOrName, stage), MODEL_STAGE_LABELS[stage] || stage)));
}
function aggregateLifecycleStrip() {
  return el('div', { class: 'model-lifecycle aggregate' }, MODEL_LIFECYCLE_STAGES.map(stage => stageCircle(aggregateStageStatus(stage), MODEL_STAGE_LABELS[stage] || stage)));
}
function setOptimisticModelStage(modelName, stage, stateName = 'running', progress = 0, message = '') {
  const name = String(modelName || '').trim();
  if (!name || !stage) return null;
  state.modelStatuses ||= { stages: MODEL_LIFECYCLE_STAGES, models: {}, aggregate: {} };
  state.modelStatuses.models ||= {};
  state.modelStatuses.models[name] ||= {};
  const prior = state.modelStatuses.models[name][stage] || defaultStageStatus(name, stage);
  const pct = Math.max(0, Math.min(1, Number(progress || 0)));
  const row = { ...prior, model_name: name, stage, state: stateName, active: ['queued','running'].includes(String(stateName).toLowerCase()), progress: pct, percent: Math.round(pct * 100), message: message || prior.message || stateName, updated_at: new Date().toISOString() };
  state.modelStatuses.models[name][stage] = row;
  return row;
}
function mergeSingleModelStatus(modelName, status) {
  const name = String(modelName || '').trim();
  if (!name || !status) return;
  state.modelStatuses ||= { stages: MODEL_LIFECYCLE_STAGES, models: {}, aggregate: {} };
  state.modelStatuses.models ||= {};
  state.modelStatuses.models[name] = { ...(state.modelStatuses.models[name] || {}), ...(status.stages || status || {}) };
  if ('loaded' in status) state.modelStatuses.models[name].loaded = status.loaded;
  if (status.placement) state.modelStatuses.models[name].placement = status.placement;
}

function updateLiveStatusDom() {
  const root = document.getElementById('app');
  if (!root) return;
  try {
    root.querySelectorAll('[data-lifecycle-stage]').forEach(node => {
      const stage = node.dataset.lifecycleStage || '';
      const model = node.dataset.lifecycleModel || '';
      const status = model === '__aggregate__' ? aggregateStageStatus(stage) : stageStatus(model, stage);
      const pct = statusPercent(status);
      const stateName = String(status?.state || 'idle').toLowerCase();
      node.className = `stage-pill ${stateName} ${isStageActive(status) ? 'active' : ''}`;
      const ring = node.querySelector('[data-role="stage-ring"]');
      if (ring) ring.style.setProperty('--pct', `${pct}%`);
      const percent = node.querySelector('[data-role="stage-percent"]');
      if (percent) percent.textContent = `${pct}%`;
      const stateText = node.querySelector('[data-role="stage-state"]');
      if (stateText) stateText.textContent = `${stateName}${status?.model_name ? ' · ' + status.model_name : ''}${status?.job_id ? ' · job #' + status.job_id : ''}`;
      const msg = node.querySelector('[data-role="stage-message"]');
      if (msg) msg.textContent = status?.message || '';
    });
    const jobsById = new Map((state.jobs || []).map(j => [String(j.id), j]));
    root.querySelectorAll('[data-job-progress-id]').forEach(span => {
      const job = jobsById.get(String(span.dataset.jobProgressId));
      if (job) span.style.width = `${Math.round((Number(job.progress || 0)) * 100)}%`;
    });
    root.querySelectorAll('[data-job-status-id]').forEach(node => {
      const job = jobsById.get(String(node.dataset.jobStatusId));
      if (job) node.textContent = job.status || '';
    });
    root.querySelectorAll('[data-job-message-id]').forEach(node => {
      const job = jobsById.get(String(node.dataset.jobMessageId));
      if (job) {
        node.textContent = job.error ? String(job.error).slice(0, 260) : (job.message || '');
        node.className = job.error ? 'bad-text' : '';
      }
    });
  } catch (err) { console.warn('live status update failed', err); }
}
async function refreshModelStatuses(renderAfter = false) {
  state.modelStatuses = await api('/api/models/status').catch(() => state.modelStatuses || { stages: MODEL_LIFECYCLE_STAGES, models: {}, aggregate: {} });
  if (state.modelStatuses?.placement) state.modelResource = state.modelStatuses.placement;
  if (renderAfter) renderOrDeferForEditing();
  return state.modelStatuses;
}
function datasetOptions() { return [el('option', { value: '' }, 'Any dataset'), ...state.datasets.map(d => el('option', { value: d.id }, `${d.name} (${d.media_count})`))]; }
function profileOptions() { return (state.tagProfiles.length ? state.tagProfiles : [{ key: 'e621', label: 'e621' }]).map(p => el('option', { value: p.key }, p.label || p.key)); }
function tagProfileSelect(attrs = {}) {
  const select = el('select', { ...attrs, onchange: async e => { state.tagProfile = e.target.value; state.dictionaryStatus = null; await loadDictionaryStatus().catch(() => {}); render(); } }, profileOptions());
  select.value = state.tagProfile;
  return select;
}


function cacheMediaItem(item) {
  if (item && item.id !== undefined && item.id !== null) state.selectedMediaCache[String(item.id)] = item;
  return item;
}
function cacheMediaItems(items = []) { for (const item of items || []) cacheMediaItem(item); }
function selectedMediaItemsCached() {
  const byId = new Map((state.media.items || []).map(item => [Number(item.id), item]));
  if (state.activeMedia) byId.set(Number(state.activeMedia.id), state.activeMedia);
  const out = [];
  for (const id of state.selected) {
    const n = Number(id);
    const item = byId.get(n) || state.selectedMediaCache[String(n)];
    if (item) out.push(item);
  }
  return out;
}
function addSelectedMedia(item) {
  if (!item) return;
  state.selected.add(item.id);
  cacheMediaItem(item);
}
function clearSelectedMedia() { state.selected.clear(); }

async function refreshAll() {
  try {
    const [summary, datasets, jobs, models, modelStatuses, modelResource, assistantConfig, presets, settings, profiles, sources, templates, detectionModels, segmentationModels, poseTemplates, threeDProviders, threeDAssets, flexAvatarStatus, flexAvatarAssets, agentStatus, voiceStatus, mcpToolStatus] = await Promise.all([
      api('/api/system/summary'), api('/api/datasets'), api('/api/jobs'), api('/api/models'), api('/api/models/status').catch(() => ({ stages: MODEL_LIFECYCLE_STAGES, models: {}, aggregate: {} })), api('/api/models/resource-status').catch(() => ({ devices: [], loaded_models: [], loading_reservations: [], warnings: [] })), api('/api/models/assistant-config').catch(() => null),
      api('/api/presets'), api('/api/settings'), api('/api/tags/profiles').catch(() => []),
      api('/api/downloads/sources').catch(() => []), api('/api/orchestration/templates').catch(() => []),
      api('/api/spatial/detection/models').catch(() => []), api('/api/spatial/segmentation/models').catch(() => []),
      api('/api/reference/annotations/pose-templates').catch(() => []), api('/api/three-d/providers').catch(() => ({ generation: [], rigging: [] })),
      api('/api/three-d/assets').catch(() => []), api('/api/flexavatar/status').catch(() => null), api('/api/flexavatar/assets').catch(() => ({ inputs: [], avatar_codes: [], renderings: [], manifests: [], training_bundles: [], driver_sequences: [] })), api('/api/agent-tools/status').catch(() => null), api('/api/voice/status').catch(() => null), api('/api/mcp-tools/status').catch(() => null)
    ]);
    Object.assign(state, { summary, datasets, jobs, models, modelStatuses: modelStatuses || { stages: MODEL_LIFECYCLE_STAGES, models: {}, aggregate: {} }, modelResource: modelResource || { devices: [], loaded_models: [], loading_reservations: [], warnings: [] }, assistantConfig, presets, settings, tagProfiles: profiles || [], downloadSources: sources || [], orchestrationTemplates: templates || [], detectionModels: detectionModels || [], segmentationModels: segmentationModels || [], poseTemplates: poseTemplates || [], threeDProviders: threeDProviders || { generation: [], rigging: [] }, threeDAssets: threeDAssets || [], flexAvatarStatus, flexAvatarAssets: flexAvatarAssets || { inputs: [], avatar_codes: [], renderings: [], manifests: [], training_bundles: [], driver_sequences: [] }, agentStatus, voiceStatus, mcpToolStatus });
    if (settings?.default_tag_profile && state.tagProfiles.some(p => p.key === settings.default_tag_profile)) state.tagProfile = settings.default_tag_profile;
    if (!state.tagProfiles.some(p => p.key === state.tagProfile) && state.tagProfiles.length) state.tagProfile = state.tagProfiles[0].key;
    state.orderingStrategy = settings?.default_ordering_strategy || state.orderingStrategy;
    state.retainImportedOrder = Boolean(settings?.retain_imported_tag_order);
    if (settings?.preferred_external_image_tool) state.quickExternalTool = settings.preferred_external_image_tool;
  } catch (err) { console.error(err); toast(err.message, false); }
}

async function loadMedia() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(state.filters)) if (v !== '' && v !== null && v !== undefined) p.set(k, v);
  p.set('page', state.media.page || 1);
  p.set('page_size', state.media.page_size || state.settings.default_page_size || 80);
  state.media = await api(`/api/media?${p.toString()}`);
  cacheMediaItems(state.media.items || []);
  if (state.activeMedia) {
    const updated = state.media.items.find(x => x.id === state.activeMedia.id);
    if (updated) state.activeMedia = updated;
  }
  return state.media;
}
async function refreshMediaRows(mediaIds = []) {
  const ids = [...new Set((mediaIds || []).map(Number).filter(n => Number.isFinite(n) && n > 0))];
  for (const id of ids) {
    delete state.tagDrafts[id];
    delete state.tagDraftSource[id];
  }
  invalidateTagScoreCache(ids.length ? ids : null);
  await loadMedia();
  if (state.activeMedia) {
    const activeId = Number(state.activeMedia.id);
    if (!ids.length || ids.includes(activeId)) {
      const fresh = await api(`/api/media/${activeId}`).catch(() => null);
      if (fresh) {
        state.activeMedia = cacheMediaItem(fresh);
        const idx = (state.media.items || []).findIndex(x => x.id === fresh.id);
        if (idx >= 0) state.media.items[idx] = fresh;
      }
    }
  }
  return true;
}
function affectedMediaIdsFromJob(job) {
  const ids = new Set();
  const add = value => { const n = Number(value); if (Number.isFinite(n) && n > 0) ids.add(n); };
  const params = job?.params || {};
  const result = job?.result || {};
  for (const value of params.media_ids || []) add(value);
  for (const value of result.media_ids || []) add(value);
  for (const value of result.applied?.media_ids || []) add(value);
  for (const key of Object.keys(result.preview_tags_by_media || {})) add(key);
  for (const key of Object.keys(result.selected_tags_by_media || {})) add(key);
  return [...ids];
}
function isCompletedModelJob(job) {
  return Boolean(job && String(job.type || '').startsWith('model_') && ['completed', 'failed'].includes(String(job.status || '').toLowerCase()));
}
function modelJobMayMutateMedia(job) {
  const type = String(job?.type || '');
  if (type !== 'model_inference') return false;
  const params = job?.params || {};
  const result = job?.result || {};
  return Boolean(params.apply_tags || params.apply_caption || result.applied_tags || result.applied_captions || result.applied?.changed);
}
async function refreshMediaAfterCompletedModelJobs(jobs) {
  const mutating = (jobs || []).filter(modelJobMayMutateMedia);
  if (!mutating.length) return false;
  const affected = new Set();
  for (const job of mutating) for (const id of affectedMediaIdsFromJob(job)) affected.add(id);
  return refreshMediaRows([...affected]);
}
async function refreshCompletedModelJobById(jobId) {
  const id = Number(jobId);
  if (!Number.isFinite(id) || id <= 0) return false;
  const job = (state.jobs || []).find(j => Number(j.id) === id);
  if (!job || !isCompletedModelJob(job)) return false;
  const refreshed = await refreshMediaAfterCompletedModelJobs([job]);
  state.lastCompletedModelJobIds.add(job.id);
  return refreshed;
}

async function loadDictionaryStatus() {
  state.dictionaryStatus = await api(`/api/tags/dictionary/status?profile_key=${encodeURIComponent(state.tagProfile)}`);
  return state.dictionaryStatus;
}

async function loadChatConversations() {
  const r = await api('/api/models/chat/conversations').catch(() => ({ conversations: [] }));
  state.chatConversations = r.conversations || [];
  return state.chatConversations;
}
async function loadChatConversation(id) {
  if (!id) { state.chatConversationId = null; state.chatMessages = []; state.chatConversationState = {}; return null; }
  const r = await api(`/api/models/chat/conversations/${id}`);
  state.chatConversationId = r.conversation?.id || id;
  state.chatMessages = (r.messages || []).map(m => ({ id: m.id, role: m.role, content: m.content, created_at: m.created_at, model_name: m.model_name, response: m.response || {}, context: m.context || {} }));
  state.chatConversationState = r.state || r.conversation?.state || {};
  return r;
}

async function loadScopedChatConversation(id, scope = 'main') {
  if (!id) {
    if (scope === 'tagSelection') { state.tagSelectionChatConversationId = null; state.tagSelectionChatMessages = []; }
    else if (scope === 'code') { state.codeConversationId = null; state.codeMessages = []; }
    else { state.chatConversationId = null; state.chatMessages = []; }
    return null;
  }
  const r = await api(`/api/models/chat/conversations/${id}`);
  const messages = (r.messages || []).map(m => ({ id: m.id, role: m.role, content: m.content, created_at: m.created_at, model_name: m.model_name, response: m.response || {}, context: m.context || {} }));
  if (scope === 'tagSelection') { state.tagSelectionChatConversationId = r.conversation?.id || id; state.tagSelectionChatMessages = messages; state.tagSelectionChatState = r.state || r.conversation?.state || {}; }
  else if (scope === 'code') { state.codeConversationId = r.conversation?.id || id; state.codeMessages = messages; state.codeConversationState = r.state || r.conversation?.state || {}; }
  else { state.chatConversationId = r.conversation?.id || id; state.chatMessages = messages; state.chatConversationState = r.state || r.conversation?.state || {}; }
  return r;
}


function chatStateForScope(scope) {
  if (scope === 'tagSelection') return state.tagSelectionChatState || {};
  if (scope === 'code') return state.codeConversationState || {};
  return state.chatConversationState || {};
}
function zeroContextBudget(modelName = '', contextLimitTokens = 0) {
  return {
    estimated: true,
    model_name: modelName || '',
    context_limit_tokens: Number(contextLimitTokens || 0),
    input_tokens_estimate: 0,
    output_tokens_estimate: 0,
    tokens_used_estimate: 0,
    percent_used: 0,
    warning: false,
    critical: false,
    auto_condensed: false,
    context_cleared: true,
    note: 'Model memory/context was cleared for this conversation. Visible transcript remains only as a UI record until new messages are sent.'
  };
}
function setScopeContextCleared(scope, conversationId, messages = []) {
  const maxId = Math.max(0, ...(messages || []).map(m => Number(m.id || 0)).filter(Number.isFinite));
  const prevState = chatStateForScope(scope);
  const prevBudget = prevState?.last_context_budget || {};
  const budget = zeroContextBudget(prevBudget.model_name || '', prevBudget.context_limit_tokens || 0);
  if (scope === 'tagSelection') {
    state.tagSelectionChatState = { ...(state.tagSelectionChatState || {}), memory_summary: '', context_reset_message_id: maxId, context_cleared_at: new Date().toISOString(), last_context_budget: budget };
    if (state.lastTagSelectionChat) state.lastTagSelectionChat = { ...state.lastTagSelectionChat, memory_summary: '', context_budget: budget };
  } else if (scope === 'code') {
    state.codeConversationState = { ...(state.codeConversationState || {}), memory_summary: '', context_reset_message_id: maxId, context_cleared_at: new Date().toISOString(), last_context_budget: budget };
    if (state.codeLastResponse) state.codeLastResponse = { ...state.codeLastResponse, memory_summary: '', context_budget: budget };
  } else {
    state.chatConversationState = { ...(state.chatConversationState || {}), memory_summary: '', context_reset_message_id: maxId, context_cleared_at: new Date().toISOString(), last_context_budget: budget };
  }
}
function chatContextBudgetForScope(scope, messages = []) {
  const scopeState = chatStateForScope(scope);
  const resetId = Number(scopeState?.context_reset_message_id || 0);
  const stateBudget = scopeState?.last_context_budget || null;
  if (stateBudget?.context_cleared || (resetId && Number(stateBudget?.tokens_used_estimate || 0) === 0)) return stateBudget;
  const eligible = resetId ? (messages || []).filter(m => Number(m.id || 0) > resetId) : (messages || []);
  const lastWithBudget = [...eligible].reverse().find(m => m?.response?.context_budget);
  if (lastWithBudget?.response?.context_budget) return lastWithBudget.response.context_budget;
  if (scope === 'tagSelection') return state.lastTagSelectionChat?.context_budget || stateBudget || null;
  if (scope === 'code') return state.codeLastResponse?.context_budget || stateBudget || null;
  return stateBudget || null;
}
function contextBudgetPanel(scope, messages = []) {
  const b = chatContextBudgetForScope(scope, messages);
  if (!b) return null;
  const pct = Math.max(0, Math.min(100, Math.round(Number(b.percent_used || 0) * 100)));
  const cls = b.critical ? 'failed' : (b.warning ? 'queued' : 'completed');
  return el('div', { class: `stage-pill context-budget ${cls}`, title: b.note || 'Estimated context usage' }, [
    el('div', { class: 'progress-ring', style: `--pct:${pct}%` }, el('span', {}, `${pct}%`)),
    el('div', { class: 'stage-text' }, [
      el('strong', {}, 'Context'),
      el('span', {}, `${b.tokens_used_estimate || 0} / ${b.context_limit_tokens || '?'} tokens used`),
      b.auto_condensed ? el('span', { class: 'ok-text' }, 'auto-condensed') : (b.warning ? el('span', { class: 'warn-text' }, 'near limit') : null)
    ].filter(Boolean))
  ]);
}

function chatMemorySummaryForScope(scope) {
  const scopeState = chatStateForScope(scope);
  if (scopeState?.context_reset_message_id && !scopeState?.memory_summary) return '';
  if (scope === 'tagSelection') return state.tagSelectionChatState?.memory_summary || state.lastTagSelectionChat?.memory_summary || '';
  if (scope === 'code') return state.codeConversationState?.memory_summary || state.codeLastResponse?.memory_summary || '';
  return scopeState?.memory_summary || '';
}
function chatQueueStateForScope(scope) {
  if (scope === 'tagSelection') return { sending: state.tagSelectionChatSending, current: state.tagSelectionChatCurrent, queue: state.tagSelectionChatQueue || [] };
  if (scope === 'code') return { sending: state.codeChatSending, current: state.codeChatCurrent, queue: state.codeChatQueue || [] };
  return { sending: state.chatSending, current: state.chatCurrent, queue: state.chatQueue || [] };
}

function resetStaleChatQueueLock(scope, maxMs = 10 * 60 * 1000) {
  const now = Date.now();
  const currentKey = scope === 'tagSelection' ? 'tagSelectionChatCurrent' : scope === 'code' ? 'codeChatCurrent' : 'chatCurrent';
  const sendingKey = scope === 'tagSelection' ? 'tagSelectionChatSending' : scope === 'code' ? 'codeChatSending' : 'chatSending';
  const current = state[currentKey];
  if (!state[sendingKey]) return false;
  const started = Date.parse(current?.queued_at || current?.started_at || '') || 0;
  if (!current || (started && now - started > maxMs)) {
    state[sendingKey] = false;
    state[currentKey] = null;
    return true;
  }
  return false;
}
function clearChatQueueForScope(scope) {
  if (scope === 'tagSelection') { state.tagSelectionChatSending = false; state.tagSelectionChatCurrent = null; state.tagSelectionChatQueue = []; }
  else if (scope === 'code') { state.codeChatSending = false; state.codeChatCurrent = null; state.codeChatQueue = []; }
  else { state.chatSending = false; state.chatCurrent = null; state.chatQueue = []; }
}
async function saveConversationState(scope, conversationId, snapshot = {}) {
  if (!conversationId) throw new Error('Start or load a conversation before saving its state.');
  const r = await api(`/api/models/chat/conversations/${conversationId}/state`, { method: 'PUT', body: snapshot });
  if (scope === 'tagSelection') { state.tagSelectionChatState = r.state || r.conversation?.state || {}; state.tagSelectionChatMessages = r.messages || state.tagSelectionChatMessages || []; }
  else if (scope === 'code') { state.codeConversationState = r.state || r.conversation?.state || {}; state.codeMessages = r.messages || state.codeMessages || []; }
  toast('Conversation state saved');
  return r;
}
function agentToolDecisionPill(decision, compact = false) {
  if (!decision || state.settings?.agent_tools_show_tool_decision_badges === false) return null;
  const mode = String(decision.mode || decision.response_mode || 'unknown').toLowerCase();
  const labelMap = {
    direct_answer: 'No tool needed',
    answer_directly: 'No tool needed',
    disabled: 'Tools off',
    app_gui_action: 'In-app GUI action',
    gui_action: 'In-app GUI action',
    local_tools: 'Local tool COA',
    tool_coa: 'Local tool COA',
    model_delegation: 'Model subtask',
    mixed: 'Mixed COA',
    mixed_or_unknown_tool_plan: 'Tool plan detected',
    ask_clarifying_question: 'Clarification needed'
  };
  const clsMap = {
    direct_answer: 'no-tool', answer_directly: 'no-tool', disabled: 'disabled',
    app_gui_action: 'gui', gui_action: 'gui', local_tools: 'tools', tool_coa: 'tools',
    model_delegation: 'model', mixed: 'mixed', mixed_or_unknown_tool_plan: 'mixed', ask_clarifying_question: 'clarify'
  };
  const text = labelMap[mode] || mode.replaceAll('_', ' ');
  const reason = decision.reason || decision.note || 'The assistant classified whether the request needed tools.';
  const bits = [];
  if (Number.isFinite(Number(decision.tool_call_count))) bits.push(`${decision.tool_call_count} OS/model tool${Number(decision.tool_call_count) === 1 ? '' : 's'}`);
  if (Number.isFinite(Number(decision.app_gui_action_count))) bits.push(`${decision.app_gui_action_count} GUI action${Number(decision.app_gui_action_count) === 1 ? '' : 's'}`);
  return el('div', { class: `agent-tool-decision ${clsMap[mode] || 'unknown'} ${compact ? 'compact' : ''}`, title: reason }, [
    el('strong', {}, text),
    !compact ? el('span', {}, reason) : null,
    !compact && bits.length ? el('span', { class: 'tiny muted' }, bits.join(' · ')) : null
  ].filter(Boolean));
}

function liveActionNotesOverlay(scope, qState, options = {}) {
  const enabled = (scope === 'code' ? state.codeShowLiveActionNotes : state.assistantShowLiveActionNotes) !== false && state.settings?.assistant_show_live_action_notes !== false;
  if (!enabled || !(qState?.sending || qState?.current || (qState?.queue || []).length || options.activeJobId)) return null;
  const phases = [
    'Reading current UI context and selected media/data',
    'Building compact model context and checking token budget',
    'Preparing visible plan/action notes',
    'Waiting for model output or approved tool result',
    'Parsing COAs/tool calls and preserving debug logs',
    'Ready to relay tool results back into the conversation'
  ];
  const idx = Math.floor(Date.now() / 1800) % phases.length;
  return el('div', { class: 'live-action-notes-overlay', title: 'Temporary live status/action notes. This is not hidden chain-of-thought.' }, [
    el('div', { class: 'live-action-header' }, [el('span', { class: 'pulse-dot' }, ''), el('strong', {}, 'Live action notes')]),
    el('div', { class: 'tiny muted' }, 'Model-private hidden chain-of-thought is not exposed; this panel shows live, user-facing execution status.'),
    el('div', { class: 'live-action-line' }, phases[idx]),
    qState?.current ? el('div', { class: 'tiny' }, `Active: ${(qState.current.text || qState.current.prompt || '').slice(0, 160)}`) : null,
    (qState?.queue || []).length ? el('div', { class: 'tiny' }, `${qState.queue.length} queued message(s)`) : null
  ].filter(Boolean));
}

function conversationHistoryPanel(scope, conversationId, messages, options = {}) {
  const title = options.title || 'Conversation';
  const editIdKey = `${scope}EditMessageId`;
  const editDraftKey = `${scope}EditDraft`;
  const reload = options.reload || (async id => loadScopedChatConversation(id, scope));
  const setConv = options.setConversation || (id => {
    if (scope === 'tagSelection') state.tagSelectionChatConversationId = id;
    else if (scope === 'code') state.codeConversationId = id;
    else state.chatConversationId = id;
  });
  const rows = messages || [];
  const memory = chatMemorySummaryForScope(scope);
  const bubbles = rows.length ? rows.map(m => {
    const role = String(m.role || '').toLowerCase();
    const isUser = role === 'user';
    const isTool = role === 'tool' || role === 'agent_tool_result';
    const editing = Number(state[editIdKey] || 0) === Number(m.id);
    if (editing) {
      const draft = el('textarea', { rows: 8, style: 'width:100%', value: state[editDraftKey] || m.content || '', oninput: e => { state[editDraftKey] = e.target.value; } });
      return el('div', { class: `chat-row ${isUser ? 'mine' : 'theirs'}` }, [
        el('div', { class: `chat-bubble ${isUser ? 'user' : 'assistant'} editing` }, [
          el('div', { class: 'chat-meta' }, `${isUser ? 'You' : 'Assistant'} #${m.id} · edit point`),
          draft,
          el('div', { class: 'row tight chat-actions' }, [
            el('button', { class: 'primary small', title: 'Save this message and delete the later turns so you can continue normally from here.', onclick: async () => {
              try {
                const r = await api(`/api/models/chat/conversations/${conversationId}/messages/${m.id}`, { method: 'PUT', body: { content: draft.value, truncate_after: true } });
                state[editIdKey] = null; state[editDraftKey] = '';
                setConv(r.conversation?.id || conversationId);
                await reload(r.conversation?.id || conversationId);
                toast(`Edited message #${m.id}; later turns were removed so you can continue from here.`);
                render(true, true);
              } catch (err) { toast(err.message, false); }
            } }, 'Save edit and continue from here'),
            el('button', { class: 'secondary small', onclick: () => { state[editIdKey] = null; state[editDraftKey] = ''; render(true, true); } }, 'Cancel')
          ])
        ])
      ]);
    }
    return el('div', { class: `chat-row ${isUser ? 'mine' : 'theirs'}` }, [
      el('div', { class: `chat-bubble ${isUser ? 'user' : isTool ? 'tool' : 'assistant'}` }, [
        el('div', { class: 'chat-meta' }, `${isUser ? 'You' : isTool ? 'Tool result' : 'Assistant'}${m.model_name && !isUser ? ' · ' + m.model_name : ''}${m.id ? ' #' + m.id : ''}`),
        !isUser && !isTool && m.response?.visible_plan ? visiblePlanPanel(m.response, 'Visible plan for this response') : null,
        !isUser && !isTool && m.response?.agent_tool_decision ? agentToolDecisionPill(m.response.agent_tool_decision) : null,
        el('div', { class: 'chat-content' }, m.content || ''),
        (!isUser && !isTool && (options.enableCoaControls !== false)) ? assistantMessageCoaControls(scope, conversationId, m, { modelName: options.modelName, runtimeControls: options.runtimeControls, surface: options.surface || title, context: options.context, options: options.coaOptions || {}, reload: async () => reload(conversationId) }) : null,
        el('div', { class: 'row tight chat-actions' }, [
          isUser ? el('button', { class: 'secondary small icon-button', title: 'Edit this user message, remove later turns, and keep chatting from this point.', onclick: () => { state[editIdKey] = Number(m.id); state[editDraftKey] = m.content || ''; render(true, true); } }, '✎ Edit message') : null,
          el('button', { class: 'secondary small', title: 'Delete only this message and rebuild cached memory from the remaining history.', disabled: !conversationId || !m.id, onclick: async () => { try { if (!confirm(`Delete message #${m.id}?`)) return; await api(`/api/models/chat/conversations/${conversationId}/messages/${m.id}`, { method: 'DELETE' }); await reload(conversationId); toast(`Deleted message #${m.id}`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Delete'),
          el('button', { class: 'secondary small', title: 'Delete this message and all later turns so you can continue from the prior point.', disabled: !conversationId || !m.id, onclick: async () => { try { if (!confirm(`Delete message #${m.id} and all later turns?`)) return; await api(`/api/models/chat/conversations/${conversationId}/messages/${m.id}?delete_following=true`, { method: 'DELETE' }); await reload(conversationId); toast(`Deleted message #${m.id} and later turns`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Delete from here'),
          !isUser && !isTool ? el('button', { class: 'secondary small', title: 'Speak this assistant message with the configured TTS model.', onclick: async () => speakAssistantText(m.content || '', m.id) }, 'Speak') : null,
          !isUser ? el('button', { class: 'secondary small', title: 'Advanced: make a separate branch that keeps messages up through this assistant response.', onclick: async () => { try { const r = await api('/api/models/chat/conversations/fork', { method: 'POST', body: { message_id: m.id } }); setConv(r.conversation.id); await reload(r.conversation.id); await loadChatConversations(); toast('Conversation branch created from selected message'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Branch from here') : null
        ].filter(Boolean))
      ])
    ]);
  }) : [el('p', { class: 'muted' }, 'No persisted messages for this conversation yet. Send a message to start a scrollable chat thread.')];
  const qState = chatQueueStateForScope(scope);
  const queuedBubbles = [];
  if (qState.current) queuedBubbles.push(el('div', { class: 'chat-row mine pending' }, [el('div', { class: 'chat-bubble user pending' }, [el('div', { class: 'chat-meta' }, 'You · sending now'), el('div', { class: 'chat-content' }, qState.current.text || qState.current.prompt || '')])])) ;
  for (const [idx, item] of (qState.queue || []).entries()) {
    queuedBubbles.push(el('div', { class: 'chat-row mine pending' }, [el('div', { class: 'chat-bubble user pending' }, [el('div', { class: 'chat-meta' }, `You · queued #${idx + 1}`), el('div', { class: 'chat-content' }, item.text || item.prompt || '')])])) ;
  }
  const composerCfg = options.composer || null;
  const lastAssistant = [...rows].reverse().find(m => String(m.role || '').toLowerCase() === 'assistant' && String(m.content || '').trim());
  let composerNode = null;
  if (composerCfg) {
    const draftKey = composerCfg.draftKey || `${scope}ChatDraft`;
    const area = el('textarea', {
      class: 'chat-composer-input',
      rows: composerCfg.rows || 4,
      placeholder: composerCfg.placeholder || 'Type a message...',
      value: state[draftKey] || '',
      'data-form-key': `${scope}-bottom-chat-composer`,
      oninput: e => { state[draftKey] = e.target.value; },
      onkeydown: async e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && composerCfg.onSend) {
          e.preventDefault();
          const text = (state[draftKey] || '').trim();
          if (!text) return;
          state[draftKey] = '';
          render(true, true);
          try { await composerCfg.onSend(text, { continueLastOutput: false }); } catch (err) { toast(err.message, false); render(true, true); }
        }
      }
    });
    const sendLabel = composerCfg.sendLabel || 'Send message';
    const finishLabel = composerCfg.finishLabel || 'Finish previous output';
    const qStateNow = chatQueueStateForScope(scope);
    const queueText = qStateNow.sending || (qStateNow.queue || []).length ? ` · ${qStateNow.sending ? 'responding' : 'idle'}${(qStateNow.queue || []).length ? ` · ${(qStateNow.queue || []).length} queued` : ''}` : '';
    composerNode = el('div', { class: 'chat-composer' }, [
      area,
      el('div', { class: 'row tight spread chat-composer-actions' }, [
        el('span', { class: 'muted tiny' }, (composerCfg.hint || 'Ctrl+Enter sends. The model receives saved memory plus recent conversation turns.') + queueText),
        el('span', { class: 'row tight' }, [
          composerCfg.extraLeft || null,
          voiceSurfaceToggles(),
          voiceInputButton(area),
          el('button', { class: 'primary small', disabled: !composerCfg.onSend, title: qStateNow.sending ? 'A response is still running; this message will be queued and sent next.' : 'Send now.', onclick: async () => {
            const text = (state[draftKey] || '').trim();
            if (!text) { toast('Type a message first.', false); return; }
            state[draftKey] = '';
            render(true, true);
            try { await composerCfg.onSend(text, { continueLastOutput: false }); } catch (err) { toast(err.message, false); render(true, true); }
          } }, qStateNow.sending ? 'Queue Message' : sendLabel),
          el('button', { class: 'secondary small', disabled: Boolean(!composerCfg.onSend || !lastAssistant || !conversationId), title: qStateNow.sending ? 'The finish request will be queued behind the current response.' : 'Ask the model to continue from the previous assistant answer without repeating text already visible.', onclick: async () => {
            const text = (state[draftKey] || '').trim() || 'Finish the previous output.';
            state[draftKey] = '';
            render(true, true);
            try { await composerCfg.onSend(text, { continueLastOutput: true, lastAssistant }); } catch (err) { toast(err.message, false); render(true, true); }
          } }, qStateNow.sending ? 'Queue Finish' : finishLabel)
        ].filter(Boolean))
      ])
    ]);
  }
  if (voiceSurfaceTtsEnabled() && state.settings?.voice_tts_auto_speak && lastAssistant?.id && !state.ttsSpokenMessageIds.has(String(lastAssistant.id)) && !qState.sending) {
    state.ttsSpokenMessageIds.add(String(lastAssistant.id));
    setTimeout(() => speakAssistantText(lastAssistant.content || '', lastAssistant.id), 0);
  }
  return el('div', { class: 'conversation-panel' }, [
    el('div', { class: 'row spread' }, [
      el('h3', {}, `${title}${conversationId ? ' #' + conversationId : ' · new'}`),
      options.saveState ? el('button', { class: 'secondary small', disabled: !conversationId, title: 'Save the current image/project, tags/captions, selected files, and conversation memory as this chat state.', onclick: async () => { try { await saveConversationState(scope, conversationId, options.saveState()); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Save current state') : null,
      el('button', { class: 'secondary small', disabled: !conversationId, title: 'Clear the model-visible memory/context for this conversation. Visible messages stay on screen as a transcript, but they are no longer sent back to the model unless new turns are added after this reset.', onclick: async () => { try { const r = await api(`/api/models/chat/conversations/${conversationId}/clear`, { method: 'POST', body: { clear_messages: false, clear_memory: true, keep_state: true, reset_context: true } }); await reload(conversationId); const rowsAfter = scope === 'tagSelection' ? state.tagSelectionChatMessages : scope === 'code' ? state.codeMessages : state.chatMessages; setScopeContextCleared(scope, conversationId, rowsAfter || r.messages || []); toast('Cleared model memory/context for this conversation'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Clear memory'),
      el('button', { class: 'danger small', disabled: !conversationId, title: 'Clear chat messages and cached memory, while keeping saved image/project state.', onclick: async () => { try { if (!confirm('Clear all visible messages and cached memory for this conversation?')) return; await api(`/api/models/chat/conversations/${conversationId}/clear`, { method: 'POST', body: { clear_messages: true, clear_memory: true, keep_state: true } }); await reload(conversationId); toast('Cleared conversation messages and memory'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Clear chat'),
      (qState.sending || (qState.queue || []).length) ? el('button', { class: 'secondary small', title: 'Unlock the local UI queue only. This does not cancel a backend model/tool job; use Jobs to stop jobs.', onclick: () => { clearChatQueueForScope(scope); toast('Cleared local pending chat queue / send lock'); render(true, true); } }, 'Unlock / Clear Pending') : null
    ].filter(Boolean)),
    liveActionNotesOverlay(scope, qState, options),
    contextBudgetPanel(scope, rows),
    memory ? el('details', { class: 'memory-summary' }, [el('summary', {}, 'Cached memory / condensed context'), el('pre', { class: 'log compact' }, memory)]) : el('p', { class: 'muted tiny' }, 'Cached memory will appear here automatically once the conversation gets long enough, or after you save state.'),
    lastVoiceOutputPanel(),
    el('div', { class: 'chat-thread' }, [...bubbles, ...queuedBubbles]),
    composerNode
  ].filter(Boolean));
}


function selectedMetadataTargetIds(getMediaIds) {
  return [...new Set((getMediaIds ? getMediaIds() : [...state.selected]).map(Number).filter(Boolean))];
}
function metadataQuickCard(options = {}) {
  const getMediaIds = options.getMediaIds || (() => [...state.selected]);
  const title = options.title || 'Embedded Metadata Extraction / Compose';
  const description = options.description || 'Extract generation metadata, inspect full JSON-like schemas, compose selected fields, and apply tags/captions without leaving this workflow.';
  const includeRaw = el('input', { type: 'checkbox', checked: true });
  const applyTags = el('input', { type: 'checkbox' });
  const applyCaption = el('input', { type: 'checkbox' });
  const replaceTags = el('input', { type: 'checkbox' });
  const tagSource = el('select', {}, ['positive_prompt','all','all_prompts','character_prompts','lora_refs','training_tags','negative_prompt'].map(x => el('option',{value:x},x)));
  const captionSource = el('select', {}, ['positive_prompt','caption','summary','character_prompts','negative_prompt','all'].map(x => el('option',{value:x},x)));
  const selectedPaths = el('textarea', { rows: '4', placeholder: 'Optional schema paths, one per line. Example:\n$.derived.positive_prompt\n$.normalized_metadata.normalized.generation.workflow' }, state.metadataSelectedPaths ? [...state.metadataSelectedPaths].join('\\n') : '');
  const inputDelimiter = el('input', { value: 'auto', title: 'Original delimiter: auto, none, comma, etc.' });
  const outputDelimiter = el('input', { value: ', ', title: 'Output delimiter for concatenated fields' });
  const keepParens = el('input', { type: 'checkbox' });
  const keepCurly = el('input', { type: 'checkbox' });
  const stripWeights = el('input', { type: 'checkbox', checked: true });
  const targetSummary = () => `${selectedMetadataTargetIds(getMediaIds).length} media item(s)`;
  const out = () => el('pre', { class: 'log compact' }, state.metadataFieldOutput ? JSON.stringify(state.metadataFieldOutput, null, 2) : state.metadataOutput ? JSON.stringify(state.metadataOutput, null, 2) : 'No metadata result in this session yet.');
  return card(title, [
    el('p', { class: 'muted' }, description),
    el('div', { class: 'muted tiny' }, `Target: ${targetSummary()}`),
    el('div', { class: 'row' }, [el('label',{},[includeRaw,' raw/schema']), tagProfileSelect(), tagSource, captionSource, el('label',{},[applyTags,' apply tags']), el('label',{},[applyCaption,' apply caption']), el('label',{},[replaceTags,' replace tags'])]),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => { try { const ids=selectedMetadataTargetIds(getMediaIds); if(!ids.length) throw new Error('No metadata targets selected.'); state.metadataOutput = await api('/api/media-tools/metadata/extract-now', { method: 'POST', body: { media_ids: ids, include_raw: includeRaw.checked, apply_tags: applyTags.checked, apply_caption: applyCaption.checked, replace_tags: replaceTags.checked, tag_source: tagSource.value, caption_source: captionSource.value, tag_profile: state.tagProfile, order_strategy: state.orderingStrategy } }); if(applyTags.checked || applyCaption.checked) await loadMedia(); toast(`Metadata extracted for ${state.metadataOutput.count || 0} item(s)`); render(); } catch(err){ toast(err.message,false); } } }, 'Extract / Apply'),
      el('button', { class: 'secondary', onclick: async () => { try { const ids=selectedMetadataTargetIds(getMediaIds); if(!ids.length) throw new Error('No metadata targets selected.'); state.metadataSchema = await api('/api/media-tools/metadata/schema', { method:'POST', body: { media_ids: ids.slice(0, 1), include_raw: includeRaw.checked, max_items: 5000 } }); state.metadataFieldOutput = state.metadataSchema; toast(`Schema has ${state.metadataSchema.results?.[0]?.schema?.count || 0} path(s)`); render(); } catch(err){ toast(err.message,false); } } }, 'Inspect Schema'),
      el('button', { class: 'primary', onclick: async () => { try { const ids=selectedMetadataTargetIds(getMediaIds); const paths=selectedPaths.value.split(/\n+/).map(x=>x.trim()).filter(Boolean); if(!ids.length) throw new Error('No metadata targets selected.'); if(!paths.length) throw new Error('Paste or select one or more metadata schema paths first.'); state.metadataSelectedPaths = new Set(paths); state.metadataFieldOutput = await api('/api/media-tools/metadata/compose', { method:'POST', body: { media_ids: ids, selected_paths: paths, include_raw: includeRaw.checked, input_delimiter: inputDelimiter.value || 'auto', output_delimiter: outputDelimiter.value || ', ', split_to_tags: true, keep_parentheses: keepParens.checked, keep_curly_braces: keepCurly.checked, keep_square_brackets: keepCurly.checked, keep_weight_syntax: !stripWeights.checked, apply_tags: applyTags.checked, apply_caption: applyCaption.checked, replace_tags: replaceTags.checked, tag_profile: state.tagProfile, order_strategy: state.orderingStrategy } }); if(applyTags.checked || applyCaption.checked) await loadMedia(); toast(`Composed metadata for ${state.metadataFieldOutput.count || 0} item(s)`); render(); } catch(err){ toast(err.message,false); } } }, 'Compose Selected Paths')
    ]),
    el('div', { class: 'row' }, [el('label',{},['input delimiter', inputDelimiter]), el('label',{},['output delimiter', outputDelimiter]), el('label',{},[keepParens,' keep parentheses']), el('label',{},[keepCurly,' keep braces/brackets']), el('label',{},[stripWeights,' strip weights'])]),
    selectedPaths,
    state.metadataSchema ? metadataSchemaPicker() : null,
    out()
  ].filter(Boolean));
}

function shell(content) {
  return el('div', { class: 'app' }, [
    el('aside', { class: 'sidebar' }, [
      el('div', { class: 'logo' }, 'Data Curation Tool'),
      el('div', { class: 'subtitle' }, 'Local-first dataset curation HUD. Conda backend. FastAPI. No Gradio.'),
      el('div', { class: 'profile-box' }, [
        el('label', { class: 'label compact' }, ['Active tag dictionary', tagProfileSelect()]),
        el('div', { class: 'muted tiny' }, 'Autocomplete, colors, ordering, tag agents, and downloader tag fields use this profile.')
      ]),
      el('div', { class: 'nav' }, tabs.map(tab => el('button', { class: state.tab === tab ? 'active' : '', onclick: () => setTab(tab) }, tab)))
    ]),
    el('main', { class: 'main' }, [
      el('div', { class: 'topbar' }, [
        el('h1', {}, state.tab),
        el('span', { class: 'badge', 'data-role': 'selected-count' }, `${state.selected.size} selected`),
        state.lastModelRunJob ? el('button', { class: 'secondary small', onclick: () => { state.jobDetailId = state.lastModelRunJob; setTab('Jobs'); } }, `Open Last Job #${state.lastModelRunJob}`) : null
      ].filter(Boolean)),
      content
    ])
  ]);
}

function categoryLegend(profileKey = state.tagProfile) {
  const items = categories(profileKey);
  if (!items.length) return el('p', { class: 'muted' }, 'No categories loaded for this profile yet.');
  return el('div', { class: 'legend' }, items.map(c => el('span', { class: `legend-item ${c.css_class || `cat-${c.key}`}`, style: categoryStyle(c.key) }, c.label || c.key)));
}

function dashboard() {
  const status = state.dictionaryStatus;
  return el('div', { class: 'grid' }, [
    el('div', { class: 'grid cols-3' }, [
      card('Datasets', [el('div', { class: 'stat' }, state.summary.datasets || 0), el('div', { class: 'muted' }, 'loaded dataset roots')]),
      card('Media', [el('div', { class: 'stat' }, state.summary.media || 0), el('div', { class: 'muted' }, 'tracked files')]),
      card('Dictionary', [el('div', { class: 'stat' }, status?.total || 0), el('div', { class: 'muted' }, `${activeProfile().label || state.tagProfile} autocomplete tags`)])
    ]),
    card('Implemented Feature Surface', [el('div', { class: 'chips open' }, [
      'Conda-first install', 'NVIDIA/torch device detection', 'Native folder picker', 'Booru downloader presets',
      'Booru tag dictionary imports', 'Fast top-k autocomplete', 'Color-coded suggestions', 'Prompt-order tag strip',
      'Pointer drag/drop tag reorder', 'Per-chip × delete', 'Unknown tag persistence', 'Custom categories',
      'Batch add/remove/set/replace', 'Quick select', 'Compare tag transfer', 'Prediction-score hovercards', 'Model score analytics', 'Upscale/edit augmentations', 'External licensed tool bridge', 'LLM/VLM chat adapters', 'Agentic orchestration', 'Device/token settings'
    ].map(x => el('span', { class: 'chip' }, x)))]),
    card('Active Category Legend', [el('div', { class: 'row' }, [tagProfileSelect(), el('button', { class: 'secondary', onclick: async () => { await loadDictionaryStatus(); render(); } }, 'Refresh Dictionary Status')]), categoryLegend()]),
    card('Recent Jobs', [jobsTable(8)])
  ]);
}

async function pickFolder(targetInput, title = 'Select dataset folder') {
  try {
    const result = await api('/api/system/pick-folder', { method: 'POST', body: { title, initial_dir: targetInput?.value || null } });
    if (!result.available) throw new Error(result.error || 'Folder picker is not available.');
    if (result.path && targetInput) targetInput.value = result.path;
    return result.path;
  } catch (err) { toast(err.message, false); return null; }
}

function importView() {
  const path = el('input', { placeholder: 'C:\\datasets\\my_set or /data/my_set', style: 'width:100%' });
  const name = el('input', { placeholder: 'Optional dataset name', style: 'width:100%' });
  const recursive = el('input', { type: 'checkbox', checked: true });
  const sidecars = el('input', { type: 'checkbox', checked: true });
  const skipDupes = el('input', { type: 'checkbox', checked: true });
  const retainOrder = el('input', { type: 'checkbox', checked: state.retainImportedOrder });
  const autoSyncTags = el('input', { type: 'checkbox', checked: false });
  const embeddedMeta = el('input', { type: 'checkbox', checked: Boolean(state.settings.metadata_extract_on_import) });
  const computeSha = el('input', { type: 'checkbox', checked: true });
  const computePhash = el('input', { type: 'checkbox', checked: false });
  const probeDims = el('input', { type: 'checkbox', checked: true });
  const nearDupes = el('input', { type: 'checkbox', checked: false });
  const commitBatch = el('input', { type: 'number', min: '16', max: '4096', value: 512, title: 'How many inspected files are committed per SQLite transaction' });
  const importWorkers = el('input', { type: 'number', min: '0', max: '64', value: state.settings.import_worker_count || 0, title: '0 = auto' });
  const importProfile = tagProfileSelect();
  const addCurrent = () => {
    const p = path.value.trim();
    if (!p) return toast('Select or type a folder first.', false);
    if (!state.importFolders.some(x => x.root_path === p)) state.importFolders.push({ root_path: p, name: name.value || null });
    render();
  };
  return el('div', { class: 'grid' }, [
    card('Import Local Dataset Folder/s', [
      el('label', { class: 'label' }, ['Root folder', path]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { const p = await pickFolder(path); if (p) addCurrent(); } }, 'Browse Folder...'),
        el('button', { class: 'secondary', onclick: addCurrent }, 'Add Typed Folder'),
        el('button', { class: 'secondary', onclick: () => { state.importFolders = []; render(); } }, 'Clear Folder List')
      ]),
      el('label', { class: 'label' }, ['Name', name]),
      el('div', { class: 'row' }, [
        el('label', {}, [recursive, ' Recursive']), el('label', {}, [sidecars, ' Read sidecars']), el('label', {}, [skipDupes, ' Skip exact duplicates']),
        el('label', {}, [retainOrder, ' Custom dataset: retain imported tag order']),
        el('label', {}, [autoSyncTags, ' Auto-sync selected booru tag DB if empty/stale ≥2 weeks'])
      ]),
      el('div', { class: 'row' }, [
        el('label', {}, [computeSha, ' Compute SHA-256 exact hashes']),
        el('label', {}, [computePhash, ' Compute perceptual hashes']),
        el('label', {}, [probeDims, ' Probe dimensions']),
        el('label', {}, [nearDupes, ' Scan near-duplicates during import (slower)']),
        el('label', {}, [embeddedMeta, ' Read embedded generation metadata when available (slower)'])
      ]),
      el('div', { class: 'row' }, [
        el('label', { class: 'label compact' }, ['Tag profile for txt sidecars / category coloring', importProfile]),
        el('label', { class: 'label compact' }, ['Parallel import workers (0 = auto)', importWorkers]),
        el('label', { class: 'label compact' }, ['SQLite commit batch size', commitBatch])
      ]),
      importFolderList(),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const folders = state.importFolders.length ? state.importFolders : [{ root_path: path.value, name: name.value || null }];
          const clean = folders.filter(x => (x.root_path || '').trim()).map(x => ({
            root_path: x.root_path,
            name: x.name || null,
            recursive: recursive.checked,
            read_sidecars: sidecars.checked,
            skip_duplicates: skipDupes.checked,
            tag_profile: importProfile.value || state.tagProfile,
            order_strategy: retainOrder.checked ? 'retain' : state.orderingStrategy,
            auto_sync_tag_dictionary: autoSyncTags.checked,
            import_workers: Number(importWorkers.value || 0),
            read_embedded_metadata: embeddedMeta.checked,
            compute_sha256: computeSha.checked,
            compute_phash: computePhash.checked || nearDupes.checked,
            probe_dimensions: probeDims.checked,
            find_near_duplicates: nearDupes.checked,
            import_commit_batch_size: Number(commitBatch.value || 512)
          }));
          if (!clean.length) throw new Error('No folder selected.');
          if (retainOrder.checked !== state.retainImportedOrder) {
            state.retainImportedOrder = retainOrder.checked;
            await api('/api/settings', { method: 'PUT', body: { values: { retain_imported_tag_order: retainOrder.checked } } }).catch(() => {});
          }
          const result = clean.length === 1 ? await api('/api/datasets/import', { method: 'POST', body: clean[0] }) : await api('/api/datasets/import-many', { method: 'POST', body: { folders: clean } });
          toast(`Import queued as job ${result.job_id}`); await refreshAll(); setTab('Jobs');
        } catch (err) { toast(err.message, false); }
      } }, 'Import Selected Folder/s')
    ]),
    card('Datasets', [datasetsTable()])
  ]);
}

function importFolderList() {
  if (!state.importFolders.length) return el('p', { class: 'muted' }, 'No folders queued yet. Use Browse Folder to select dataset roots without typing paths.');
  return el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['Folder', 'Name', ''].map(h => el('th', {}, h)))),
    el('tbody', {}, state.importFolders.map((f, idx) => el('tr', {}, [el('td', {}, f.root_path), el('td', {}, f.name || ''), el('td', {}, el('button', { class: 'danger small', onclick: () => { state.importFolders.splice(idx, 1); render(); } }, 'Remove'))])))
  ]);
}

function datasetsTable() {
  return el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['ID', 'Name', 'Media', 'Root'].map(h => el('th', {}, h)))),
    el('tbody', {}, state.datasets.map(d => el('tr', {}, [el('td', {}, d.id), el('td', {}, d.name), el('td', {}, d.media_count), el('td', {}, d.root_path)])))
  ]);
}

function activeTagTextMode() { return (state.settings?.tag_text_mode_active || 'underscores') === 'spaces' ? 'spaces' : 'underscores'; }
function parseTagString(raw) { return String(raw || '').split(/[;,\n]+/).map(x => normalizeTag(x)).filter(Boolean); }
function normalizeTag(x) {
  const canonical = String(x || '').trim().replace(/\s+/g, '_').toLowerCase().replace(/^[_ ,]+|[_ ,]+$/g, '');
  return activeTagTextMode() === 'spaces' ? canonical.replace(/_/g, ' ') : canonical;
}
function firstTag(raw) { return parseTagString(raw)[0] || ''; }
function currentToken(input) { const text = input.value || ''; const pos = input.selectionStart ?? text.length; const left = text.slice(0, pos); const m = left.match(/([^,;\n]*)$/); return normalizeTag(m ? m[1] : text); }
function insertTokenAtCursor(input, tag) {
  const text = input.value || '';
  const pos = input.selectionStart ?? text.length;
  const before = text.slice(0, pos).replace(/[^,;\n]*$/, '');
  const after = text.slice(pos).replace(/^[^,;\n]*/, '');
  const sep = before && !/[;,\n]\s*$/.test(before) ? ', ' : '';
  input.value = `${before}${sep}${tag}${after ? after : ', '}`;
}

function currentLogicToken(input) {
  const text = input.value || '';
  const pos = input.selectionStart ?? text.length;
  const left = text.slice(0, pos);
  const m = left.match(/(?:^|[\s(),!|&-])([^\s(),!|&-]*)$/);
  const raw = (m ? m[1] : '').trim();
  if (!raw || ['AND', 'OR', 'NOT'].includes(raw.toUpperCase())) return '';
  return normalizeTag(raw.replace(/^['"]|['"]$/g, ''));
}
function insertLogicTokenAtCursor(input, tag) {
  const clean = String(tag || '').trim();
  if (!clean) return;
  const token = /\s/.test(clean) ? `"${clean.replace(/"/g, '\"')}"` : clean;
  const text = input.value || '';
  const pos = input.selectionStart ?? text.length;
  const before = text.slice(0, pos).replace(/[^\s(),!|&-]*$/, '');
  const after = text.slice(pos).replace(/^[^\s(),!|&-]*/, '');
  const sep = before && !/[\s(]$/.test(before) ? ' ' : '';
  input.value = `${before}${sep}${token} ${after}`;
  input.focus();
  const next = (`${before}${sep}${token} `).length;
  input.setSelectionRange(next, next);
}

function tagAutocompleteControl({ placeholder = 'tag', value = '', multiline = false, onPick = null, onCommit = null, onChange = null, profileGetter = () => state.tagProfile, tokenMode = 'tag' } = {}) {
  const input = el(multiline ? 'textarea' : 'input', { placeholder, value, class: 'tag-autocomplete-input' });
  const box = el('div', { class: 'suggestions' });
  const wrap = el('div', { class: 'suggest-wrap' }, [input, box]);
  let timer = null;
  let latest = 0;
  async function updateSuggestions() {
    const token = tokenMode === 'logic' ? currentLogicToken(input) : currentToken(input);
    if (!token) { box.classList.remove('open'); box.replaceChildren(); return; }
    const requestNo = ++latest;
    const limit = Number(state.settings.tag_suggestion_count || 40);
    const profileKey = profileGetter() || state.tagProfile;
    const items = await api(`/api/tags/suggest?profile_key=${encodeURIComponent(profileKey)}&q=${encodeURIComponent(token)}&limit=${limit}`).catch(() => []);
    if (requestNo !== latest) return;
    const createButton = el('button', { class: 'suggestion create-suggestion', onmousedown: async e => {
      e.preventDefault();
      if (onCommit) await onCommit(token, null, true); else (tokenMode === 'logic' ? insertLogicTokenAtCursor(input, token) : insertTokenAtCursor(input, token));
      box.classList.remove('open');
    } }, [el('span', { class: 'chip cat-unknown' }, `Create/remember: ${token}`), el('span', { class: 'muted tiny' }, 'unknown/custom')]);
    const buttons = items.map(s => el('button', { class: 'suggestion', onmousedown: async e => {
      e.preventDefault();
      state.tagMeta[profileKey] ||= {};
      state.tagMeta[profileKey][s.tag] = { tag: s.tag, category: s.category, post_count: s.post_count, known: true, custom: Boolean(s.custom) };
      if (onPick) await onPick(s.tag, s); else (tokenMode === 'logic' ? insertLogicTokenAtCursor(input, s.tag) : insertTokenAtCursor(input, s.tag));
      box.classList.remove('open');
      if (onChange) onChange(input.value);
    } }, [el('span', { class: `chip ${categoryCss(s.category)}`, style: categoryStyle(s.category) }, s.tag), el('span', { class: 'muted tiny' }, `${s.category}${s.post_count ? ` · ${s.post_count}` : ''}${s.custom ? ' · custom' : ''}`)]));
    box.replaceChildren(...buttons, createButton);
    box.classList.add('open');
  }
  input.addEventListener('input', () => { if (onChange) onChange(input.value); clearTimeout(timer); timer = setTimeout(updateSuggestions, 50); });
  input.addEventListener('focus', () => { clearTimeout(timer); timer = setTimeout(updateSuggestions, 50); });
  input.addEventListener('blur', () => setTimeout(() => box.classList.remove('open'), 180));
  input.addEventListener('keydown', async e => {
    if (e.key === 'Enter' && !multiline) {
      e.preventDefault();
      const first = box.classList.contains('open') ? box.querySelector('.suggestion') : null;
      if (first) return first.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
      if (onCommit) { await onCommit(input.value); input.value = ''; }
    }
    if (e.key === 'Tab' && box.classList.contains('open')) {
      const first = box.querySelector('.suggestion');
      if (first) { e.preventDefault(); first.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true })); }
    }
  });
  return { wrap, input, box };
}

async function refreshGallerySidecars() {
  try {
    const ids = state.selected.size ? [...state.selected] : (state.media.items || []).map(item => item.id);
    if (!ids.length) return toast('No visible or selected media to refresh.', false);
    const result = await api('/api/media/refresh-sidecars', { method: 'POST', body: { media_ids: ids, tag_profile: state.tagProfile } });
    state.tagMeta[state.tagProfile] = {};
    await loadMedia();
    toast(`Refreshed sidecars for ${result.refreshed || 0} media item(s).`);
    render();
  } catch (err) { toast(err.message, false); }
}

async function reapplyVisibleCategories(saveSidecars = false) {
  try {
    const ids = state.selected.size ? [...state.selected] : (state.media.items || []).map(item => item.id);
    if (!ids.length) return toast('No visible or selected media to recategorize.', false);
    const result = await api('/api/tags/categories/reapply', { method: 'POST', body: { media_ids: ids, profile_key: state.tagProfile, save_sidecars: saveSidecars } });
    state.tagMeta[state.tagProfile] = {};
    await loadMedia();
    toast(`Reapplied categories to ${result.changed || 0} media item(s).`);
    render();
  } catch (err) { toast(err.message, false); }
}

async function refreshGalleryPage(resetPage = false) {
  if (resetPage) state.media.page = 1;
  await loadMedia();
  render();
}

async function discoverExternalApps(deepScan = false) {
  state.externalApps = await api('/api/augment/external-tools/discover', {
    method: 'POST',
    body: { refresh: true, deep_scan: Boolean(deepScan), save_discovered_paths: true }
  });
  return state.externalApps;
}

function externalAppRow(toolKey) {
  return (state.externalApps?.tools || []).find(row => row.key === toolKey) || null;
}

async function launchExternalToolNow(toolKey, mediaIds = [...state.selected], extra = {}) {
  try {
    const ids = [...new Set((mediaIds || []).map(Number).filter(Boolean))];
    if (!ids.length) throw new Error('Select at least one image in the Gallery first.');
    const result = await api('/api/augment/external-tool/launch-now', {
      method: 'POST',
      body: {
        media_ids: ids,
        tool_name: toolKey || 'topaz_photo_ai',
        mode: 'open',
        copy_inputs: extra.copy_inputs !== false,
        auto_discover: true,
        save_discovered_path: true,
        executable_path: extra.executable_path || null,
        output_dir: extra.output_dir || null,
        options: { launch_application: true, deep_scan: Boolean(extra.deep_scan) }
      }
    });
    state.externalAppOutput = result;
    const detail = result.pid ? ` (PID ${result.pid})` : '';
    toast(`${result.message || `Launched ${result.label || toolKey}`}${detail}`);
    render();
    return result;
  } catch (err) {
    state.externalAppOutput = { ok: false, error: err.message, tool_name: toolKey };
    toast(err.message, false);
    setTab('Augment');
    return null;
  }
}

function mediaPreviewElement(item, cls = 'preview', opts = {}) {
  const src = `/api/media/${item.id}/file`;
  const thumb = `/api/media/${item.id}/thumbnail`;
  const ext = String(item.ext || '').toLowerCase();
  const type = item.media_type || '';
  const common = { class: cls, title: item.relative_path || item.path || '' };
  if (type === 'audio' || ['.mp3','.wav','.flac','.m4a','.ogg','.opus','.aac'].includes(ext)) {
    return el('audio', { ...common, src, controls: true, preload: 'metadata' });
  }
  if (type === 'video' || ['.webm','.mov','.mp4','.mkv','.avi','.m4v'].includes(ext)) {
    return el('video', { ...common, src, controls: true, muted: Boolean(opts.muted ?? true), loop: Boolean(opts.loop ?? false), preload: 'metadata', playsInline: true });
  }
  return el('img', { ...common, src: opts.thumbnail ? thumb : src, loading: opts.thumbnail ? 'lazy' : undefined });
}

function updateTileSelectionDom() {
  const root = document.getElementById('app');
  if (!root) return;
  root.querySelectorAll('.tile[data-media-id]').forEach(node => {
    const id = Number(node.getAttribute('data-media-id'));
    node.classList.toggle('selected', state.selected.has(id));
    node.classList.toggle('active-media', Boolean(state.activeMedia && Number(state.activeMedia.id) === id));
  });
  root.querySelectorAll('[data-role="selected-count"]').forEach(node => { node.textContent = `${state.selected.size} selected`; });
  root.querySelectorAll('[data-role="gallery-selected-count"]').forEach(node => { node.textContent = `Selected: ${state.selected.size} image(s)`; });
  document.querySelectorAll('[data-role="selected-count"]').forEach(node => { node.textContent = `${state.selected.size} selected`; });
  document.querySelectorAll('[data-role="gallery-selected-count"]').forEach(node => { node.textContent = `Selected: ${state.selected.size} image(s)`; });
}


function galleryView() {
  requestTagMetadata((state.media.items || []).flatMap(item => item.tags || []));
  const scoreItems = (state.media.items || []).filter(item => state.selected.has(item.id) || Number(state.activeMedia?.id || 0) === Number(item.id)).slice(0, 8);
  for (const item of scoreItems) requestTagScores(item.id, item.tags || []);
  const q = el('input', { placeholder: 'Search path', value: state.filters.q, oninput: e => state.filters.q = e.target.value });
  const tagCtl = tagAutocompleteControl({ placeholder: 'Tag filter', value: state.filters.tag, onCommit: v => { state.filters.tag = firstTag(v); }, onChange: v => { state.filters.tag = firstTag(v); } });
  const dataset = el('select', { onchange: e => state.filters.dataset_id = e.target.value }, datasetOptions()); dataset.value = state.filters.dataset_id;
  const type = el('select', { onchange: e => state.filters.media_type = e.target.value }, [el('option', { value: '' }, 'Any type'), el('option', { value: 'image' }, 'Images'), el('option', { value: 'animation' }, 'Animations'), el('option', { value: 'video' }, 'Videos'), el('option', { value: 'audio' }, 'Audio')]); type.value = state.filters.media_type;
  const categorySelect = el('select', {}, [el('option', { value: '' }, 'Category quick select'), ...categories().map(c => el('option', { value: c.key }, c.label || c.key))]);
  const externalQuick = el('select', { onchange: e => { state.quickExternalTool = e.target.value; } }, EXTERNAL_APP_OPTIONS.map(([value, label]) => el('option', { value }, label)));
  externalQuick.value = state.quickExternalTool || 'topaz_photo_ai';
  return el('div', { class: 'grid' }, [
    el('div', { class: 'gallery-toolbar' }, [
      q, dataset, type, tagCtl.wrap,
      el('button', { class: 'primary', onclick: () => refreshGalleryPage(true) }, 'Search / Refresh'),
      el('button', { class: 'secondary', onclick: () => refreshGalleryPage(false) }, 'Reload Page'),
      el('button', { class: 'secondary', onclick: refreshGallerySidecars }, 'Refresh JSON/Sidecars + Reload'),
      el('button', { class: 'secondary', onclick: () => reapplyVisibleCategories(false) }, 'Reapply Profile/Custom Categories'),
      el('button', { class: 'secondary', onclick: () => { state.galleryScoresEnabled = !state.galleryScoresEnabled; if (state.galleryScoresEnabled) for (const item of (state.media.items || [])) requestTagScores(item.id, item.tags || []); render(); } }, state.galleryScoresEnabled ? 'Hide Page Prediction Scores' : 'Load Page Prediction Scores')
    ]),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: () => { clearSelectedMedia(); updateTileSelectionDom(); } }, 'Clear Selection'),
      el('button', { class: 'secondary', onclick: () => { for (const item of state.media.items) addSelectedMedia(item); updateTileSelectionDom(); } }, 'Select Page'),
      el('button', { class: 'secondary', onclick: () => { for (const item of state.media.items) if (!item.tags.length) addSelectedMedia(item); updateTileSelectionDom(); } }, 'Select Untagged Page'),
      categorySelect,
      el('button', { class: 'secondary', onclick: () => { const cat = categorySelect.value; if (!cat) return; for (const item of state.media.items) if ((item.tags || []).some(t => categoryOf(t, item) === cat)) addSelectedMedia(item); updateTileSelectionDom(); } }, 'Select Page by Category'),
      el('button', { class: 'secondary', onclick: () => setTab('Batch Tags') }, 'Batch Options'),
      externalQuick,
      el('button', { class: 'primary', onclick: async () => launchExternalToolNow(externalQuick.value, [...state.selected]) }, 'Launch / Send Selected Now'),
      el('button', { class: 'secondary', onclick: () => { const first = state.media.items.find(x => state.selected.has(x.id)); if (first) { state.activeMedia = first; setTab('Detection & Boxes'); } } }, 'Detect / Draw Boxes'),
      el('button', { class: 'secondary', onclick: () => { const first = state.media.items.find(x => state.selected.has(x.id)); if (first) { state.activeMedia = first; setTab('Segmentation & Masks'); } } }, 'Segment / Edit Masks'),
      el('button', { class: 'secondary', onclick: () => { const first = state.media.items.find(x => state.selected.has(x.id)); if (first) { state.activeMedia = first; setTab('Tag Editor'); } } }, 'Edit First Selected'),
      el('span', { class: 'muted', 'data-role': 'gallery-selected-count' }, `Selected: ${state.selected.size} image(s)`), el('span', { class: 'muted' }, `${state.media.total || 0} files`)
    ]),
    el('div', { class: 'gallery' }, state.media.items.map(tile)),
    pager()
  ]);
}

function tile(item) {
  const scoreMediaId = (state.selected.has(item.id) || Number(state.activeMedia?.id || 0) === Number(item.id)) ? item.id : null;
  return el('div', { class: `tile ${state.selected.has(item.id) ? 'selected' : ''} ${state.activeMedia && state.activeMedia.id === item.id ? 'active-media' : ''}`, 'data-media-id': item.id, onclick: e => {
    if (e.detail > 1) return;
    if (e.ctrlKey || e.metaKey || e.shiftKey) { state.selected.has(item.id) ? state.selected.delete(item.id) : addSelectedMedia(item); }
    else { clearSelectedMedia(); addSelectedMedia(item); state.activeMedia = cacheMediaItem(item); }
    updateTileSelectionDom();
  }, ondblclick: () => { state.activeMedia = cacheMediaItem(item); addSelectedMedia(item); updateTileSelectionDom(); setTab('Tag Editor'); } }, [
    mediaPreviewElement(item, 'tile-media', { thumbnail: true, muted: true, loop: true }),
    el('div', { class: 'meta' }, [el('div', { class: 'name', title: item.path }, item.relative_path || item.path), el('div', { class: 'chips' }, (item.tags || []).slice(0, 12).map(t => predictionChip(t, categoryOf(t, item), scoreMediaId)))])
  ]);
}

function pager() {
  const totalPages = Math.max(1, Math.ceil((state.media.total || 0) / (state.media.page_size || 80)));
  return el('div', { class: 'row' }, [
    el('button', { class: 'secondary', disabled: state.media.page <= 1, onclick: async () => { state.media.page--; await loadMedia(); render(); } }, 'Prev'),
    el('span', { class: 'muted' }, `Page ${state.media.page || 1} / ${totalPages}`),
    el('button', { class: 'secondary', disabled: state.media.page >= totalPages, onclick: async () => { state.media.page++; await loadMedia(); render(); } }, 'Next')
  ]);
}

function chip(tag, category = 'unknown', attrs = {}) { return el('span', { ...attrs, class: `${attrs.class || 'chip'} ${categoryCss(category)}`, style: [attrs.style || '', categoryStyle(category)].filter(Boolean).join(';') }, tag); }
function ensureDraft(item) {
  if (!item) return [];
  if (state.tagDraftSource[item.id] !== item.tag_string) {
    state.tagDrafts[item.id] = [...(item.tags || [])];
    state.tagDraftSource[item.id] = item.tag_string;
  }
  return state.tagDrafts[item.id];
}
function categoryFromItem(tag, item = null) {
  if (!item || !item.categories) return null;
  const cleanTag = normalizeTag(tag);
  if (item.categories[cleanTag]) return normalizeCategoryKey(item.categories[cleanTag]);
  if (item.categories[tag]) return normalizeCategoryKey(item.categories[tag]);
  const foundKey = Object.keys(item.categories).find(k => normalizeTag(k) === cleanTag);
  return foundKey ? normalizeCategoryKey(item.categories[foundKey]) : null;
}
function categoryOf(tag, item = null) {
  const cleanTag = normalizeTag(tag);
  const profileMeta = state.tagMeta[state.tagProfile] || {};
  if (profileMeta[cleanTag]?.custom) return normalizeCategoryKey(profileMeta[cleanTag].category || 'unknown');
  const itemCategory = categoryFromItem(tag, item);
  if (itemCategory) return itemCategory;
  if (profileMeta[cleanTag]) return normalizeCategoryKey(profileMeta[cleanTag].category || 'unknown');
  return 'unknown';
}
async function requestTagMetadata(tags) {
  const clean = [...new Set((tags || []).map(normalizeTag).filter(Boolean))];
  const profileKey = state.tagProfile;
  const missing = clean.filter(t => !(state.tagMeta[profileKey] || {})[t]);
  if (!missing.length) return;
  const key = `${profileKey}:${missing.sort().join('|')}`;
  if (state.tagMetaPending.has(key)) return;
  state.tagMetaPending.add(key);
  try {
    const meta = await api('/api/tags/metadata', { method: 'POST', body: { tags: missing, profile_key: profileKey } });
    state.tagMeta[profileKey] ||= {};
    Object.assign(state.tagMeta[profileKey], meta || {});
    if (state.tab === 'Tag Editor' || state.tab === 'Compare' || state.tab === 'Batch Tags' || state.tab === 'Gallery') scheduleRender();
  } catch (err) { console.warn(err); }
  finally { state.tagMetaPending.delete(key); }
}

function scoreColorClass(modelName, idx = 0) { return `model-score-${Math.abs(hashString(modelName || String(idx))) % 10}`; }
function hashString(s) { let h = 0; for (let i = 0; i < String(s).length; i++) h = ((h << 5) - h + String(s).charCodeAt(i)) | 0; return h; }
function tagScoreRequestSignature(mediaId, tags = []) {
  const clean = [...new Set((tags || []).map(normalizeTag).filter(Boolean))].sort();
  return `${mediaId}:${clean.join('|')}`;
}
function invalidateTagScoreCache(mediaIds = null) {
  if (!mediaIds) { state.tagScoreRequestKeys = {}; return; }
  for (const mediaId of mediaIds) delete state.tagScoreRequestKeys[String(mediaId)];
}
async function requestTagScores(mediaId, tags = []) {
  if (!mediaId) return;
  const key = String(mediaId);
  const signature = tagScoreRequestSignature(mediaId, tags);
  if (state.tagScorePending.has(key)) return;
  if (state.tagScoreRequestKeys[key] === signature && state.tagScores[key]) return;
  state.tagScorePending.add(key);
  try {
    const queryTags = [...new Set((tags || []).map(normalizeTag).filter(Boolean))];
    const query = queryTags.length ? `?tags=${encodeURIComponent(queryTags.join(','))}` : '';
    const previous = JSON.stringify(state.tagScores[key] || {});
    const res = await api(`/api/models/tag-scores/${mediaId}${query}`);
    state.tagScores[key] = res.scores || {};
    state.tagScoreRequestKeys[key] = signature;
    const changed = previous !== JSON.stringify(state.tagScores[key] || {});
    if (changed && (state.tab === 'Tag Editor' || state.tab === 'Compare' || state.tab === 'Gallery' || state.tab === 'Prediction Analytics')) scheduleRender();
  } catch (err) { console.warn('tag score load failed', err); }
  finally { state.tagScorePending.delete(key); }
}
function scoreEntriesFor(mediaId, tag) { return (((state.tagScores || {})[String(mediaId)] || {})[normalizeTag(tag)] || []).slice().sort((a,b) => Number(b.score||0) - Number(a.score||0)); }
function bestTagScore(mediaId, tag) {
  const entries = scoreEntriesFor(mediaId, tag);
  if (!entries.length) return null;
  const best = Math.max(...entries.map(e => Number(e.score || 0)).filter(v => Number.isFinite(v)));
  return Number.isFinite(best) ? best : null;
}
function categorySortIndex(category) {
  const key = normalizeCategoryKey(category || 'unknown');
  const list = categories();
  const idx = list.findIndex(c => normalizeCategoryKey(c.key) === key || normalizeCategoryKey(c.label) === key);
  return idx >= 0 ? idx : 9999;
}
function sortDraftTagsWithScores(item, tags, mode = 'scored_category') {
  const decorated = tags.map((tag, idx) => ({
    tag,
    idx,
    clean: normalizeTag(tag),
    category: normalizeCategoryKey(categoryOf(tag, item) || 'unknown'),
    score: bestTagScore(item?.id, tag)
  }));
  const scored = decorated.filter(row => row.score !== null);
  const unscored = decorated.filter(row => row.score === null).sort((a, b) => a.idx - b.idx);
  const byCategoryThenScore = (a, b) => {
    const ca = categorySortIndex(a.category);
    const cb = categorySortIndex(b.category);
    if (ca !== cb) return ca - cb;
    if (a.category !== b.category) return a.category.localeCompare(b.category);
    if (Number(b.score || 0) !== Number(a.score || 0)) return Number(b.score || 0) - Number(a.score || 0);
    return a.idx - b.idx;
  };
  const byScoreThenCategory = (a, b) => {
    if (Number(b.score || 0) !== Number(a.score || 0)) return Number(b.score || 0) - Number(a.score || 0);
    return byCategoryThenScore(a, b);
  };
  const byCategoryAll = (a, b) => {
    const ca = categorySortIndex(a.category);
    const cb = categorySortIndex(b.category);
    if (ca !== cb) return ca - cb;
    if (a.category !== b.category) return a.category.localeCompare(b.category);
    return a.idx - b.idx;
  };
  if (mode === 'all_category') return decorated.slice().sort(byCategoryAll).map(row => row.tag);
  const sortedScored = scored.sort(mode === 'scored_accuracy' ? byScoreThenCategory : byCategoryThenScore);
  return [...sortedScored, ...unscored].map(row => row.tag);
}
function scoreTitle(mediaId, tag, category) {
  const entries = scoreEntriesFor(mediaId, tag);
  if (!entries.length) return `${category || 'unknown'} · no stored model scores yet`;
  return `${category || 'unknown'} · model scores:\n` + entries.map(e => `${e.model_name}: ${(Number(e.score||0)*100).toFixed(1)}%`).join('\n');
}
function tagScoreHoverPanel(mediaId, tag) {
  const entries = scoreEntriesFor(mediaId, tag);
  if (!entries.length) return el('span', { class: 'tag-score-popover muted' }, 'No stored model scores for this tag yet.');
  return el('span', { class: 'tag-score-popover' }, [
    el('strong', {}, 'Prediction scores'),
    ...entries.map((e, idx) => el('span', { class: `score-line ${scoreColorClass(e.model_name, idx)}` }, [
      el('span', { class: 'score-model' }, e.model_name),
      el('span', { class: 'score-bar', style: `--score:${Math.round(Number(e.score||0)*100)}%` }, ''),
      el('span', { class: 'score-value' }, `${(Number(e.score||0)*100).toFixed(1)}%`)
    ]))
  ]);
}
function predictionChip(tag, category = 'unknown', mediaId = null, attrs = {}) {
  const cleanAttrs = { ...attrs };
  cleanAttrs.class = `${attrs.class || 'chip'} ${categoryCss(category)} prediction-aware-chip`;
  cleanAttrs.style = [attrs.style || '', categoryStyle(category)].filter(Boolean).join(';');
  cleanAttrs.title = mediaId ? scoreTitle(mediaId, tag, category) : (attrs.title || String(category || 'unknown'));
  const children = [el('span', { class: 'chip-label' }, tag)];
  if (mediaId) children.push(tagScoreHoverPanel(mediaId, tag));
  return el('span', cleanAttrs, children);
}

function editorSelectionArray(mediaId) {
  const key = String(mediaId || '');
  return Array.isArray(state.editorManualTagSelections[key]) ? state.editorManualTagSelections[key] : [];
}
function editorSelectionSet(mediaId) {
  return new Set(editorSelectionArray(mediaId).map(normalizeTag).filter(Boolean));
}
function setEditorSelection(mediaId, tags) {
  const key = String(mediaId || '');
  const clean = [...new Set((tags || []).map(normalizeTag).filter(Boolean))];
  if (!clean.length) delete state.editorManualTagSelections[key];
  else state.editorManualTagSelections[key] = clean;
}
function assistantSelectionForMedia(item) {
  if (!item) return [];
  return (state.editorAssistantSelection?.selected_tags_by_media || {})[item.id] || (state.editorAssistantSelection?.selected_tags_by_media || {})[String(item.id)] || [];
}
function combinedEditorSelection(item) {
  const selected = editorSelectionSet(item?.id);
  for (const tag of assistantSelectionForMedia(item)) selected.add(normalizeTag(tag));
  return selected;
}
function mutateEditorSelection(item, mutator) {
  if (!item) return;
  const set = combinedEditorSelection(item);
  mutator(set);
  setEditorSelection(item.id, [...set]);
  state.editorAssistantSelection = null;
}
function editorTagSelectionControls(item, tags, draw, raw) {
  const categorySelect = el('select', {}, categories().map(c => el('option', { value: c.key }, c.label || c.key)));
  const selected = combinedEditorSelection(item);
  const applySelection = () => { draw(); raw.value = tags.join(', '); };
  const selectByCategory = (mode = 'select') => {
    const cat = categorySelect.value;
    mutateEditorSelection(item, set => {
      for (const tag of tags) {
        if (categoryOf(tag, item) === cat) {
          if (mode === 'deselect') set.delete(tag); else set.add(tag);
        }
      }
    });
    applySelection();
  };
  return el('div', { class: 'manual-tag-selection' }, [
    el('div', { class: 'muted tiny' }, `${selected.size} highlighted tag(s). Highlighted tags can be selected manually or by the LLM/VLM assistant preview below.`),
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', onclick: () => { setEditorSelection(item.id, tags); state.editorAssistantSelection = null; applySelection(); } }, 'Select All Tags'),
      el('button', { class: 'secondary small', onclick: () => { setEditorSelection(item.id, []); state.editorAssistantSelection = null; applySelection(); } }, 'Deselect All'),
      el('button', { class: 'secondary small', onclick: () => { mutateEditorSelection(item, set => { for (const tag of tags) set.has(tag) ? set.delete(tag) : set.add(tag); }); applySelection(); } }, 'Invert Selection'),
      categorySelect,
      el('button', { class: 'secondary small', onclick: () => selectByCategory('select') }, 'Select Category'),
      el('button', { class: 'secondary small', onclick: () => selectByCategory('deselect') }, 'Deselect Category')
    ]),
    el('div', { class: 'row tight' }, [
      el('button', { class: 'danger small', onclick: () => { const set = combinedEditorSelection(item); if (!set.size) return toast('No highlighted tags selected.', false); const kept = tags.filter(t => !set.has(t)); tags.splice(0, tags.length, ...kept); setEditorSelection(item.id, []); state.editorAssistantSelection = null; applySelection(); } }, 'Remove Highlighted from Draft'),
      el('button', { class: 'secondary small', onclick: () => { const set = combinedEditorSelection(item); if (!set.size) return toast('No highlighted tags selected.', false); const kept = tags.filter(t => set.has(t)); tags.splice(0, tags.length, ...kept); setEditorSelection(item.id, kept); state.editorAssistantSelection = null; applySelection(); } }, 'Keep Only Highlighted in Draft')
    ])
  ]);
}

function tagCategorySortIndex(tag, item = null) {
  const cat = normalizeCategoryKey(categoryOf(tag, item));
  const profile = activeProfile();
  const precedence = (profile.precedence || []).map(normalizeCategoryKey);
  let idx = precedence.indexOf(cat);
  if (idx >= 0) return idx;
  const cats = categories().map(c => normalizeCategoryKey(c.key));
  idx = cats.indexOf(cat);
  return idx >= 0 ? 1000 + idx : 9999;
}
function tagBestPredictionScore(mediaId, tag) {
  const entries = scoreEntriesFor(mediaId, tag);
  if (!entries.length) return null;
  const scores = entries.map(e => Number(e.score)).filter(n => Number.isFinite(n));
  return scores.length ? Math.max(...scores) : null;
}
function sortPredictedTagsForDraft(item, tags, mode = 'category') {
  const scored = [];
  const unscored = [];
  tags.forEach((tag, index) => {
    const score = tagBestPredictionScore(item?.id, tag);
    const row = { tag, index, score: score === null ? null : Number(score), catIndex: tagCategorySortIndex(tag, item), cat: normalizeCategoryKey(categoryOf(tag, item)) };
    if (score === null) unscored.push(row); else scored.push(row);
  });
  if (!scored.length) return null;
  scored.sort((a, b) => {
    if (mode === 'accuracy') {
      const scoreDiff = Number(b.score || 0) - Number(a.score || 0);
      if (Math.abs(scoreDiff) > 1e-9) return scoreDiff;
      if (a.catIndex !== b.catIndex) return a.catIndex - b.catIndex;
    } else {
      if (a.catIndex !== b.catIndex) return a.catIndex - b.catIndex;
      if (a.cat !== b.cat) return a.cat.localeCompare(b.cat);
      const scoreDiff = Number(b.score || 0) - Number(a.score || 0);
      if (Math.abs(scoreDiff) > 1e-9) return scoreDiff;
    }
    return a.index - b.index;
  });
  // Tags with no stored prediction score are treated as manually curated/unknown
  // confidence and kept at the end in their existing order.
  return [...scored, ...unscored].map(row => row.tag);
}

function categoryRankForTag(item, tag) {
  const cat = normalizeCategoryKey(categoryOf(tag, item) || 'unknown');
  const list = categories();
  const idx = list.findIndex(c => normalizeCategoryKey(c.key) === cat);
  if (idx >= 0) return idx;
  return cat === 'unknown' ? 9998 : 9990;
}
function topPredictionScore(mediaId, tag) {
  const entries = scoreEntriesFor(mediaId, tag);
  if (!entries.length) return null;
  let best = null;
  for (const entry of entries) {
    const score = Number(entry.score);
    if (Number.isFinite(score) && (best === null || score > best)) best = score;
  }
  return best;
}
function sortDraftTagsForEditor(item, tags, mode) {
  const annotated = tags.map((tag, idx) => ({ tag, idx, categoryRank: categoryRankForTag(item, tag), score: topPredictionScore(item?.id, tag) }));
  const byOriginal = (a, b) => a.idx - b.idx;
  const byCategory = (a, b) => (a.categoryRank - b.categoryRank) || byOriginal(a, b);
  const byScore = (a, b) => (Number(b.score ?? -1) - Number(a.score ?? -1)) || byOriginal(a, b);
  if (mode === 'all_category') return annotated.slice().sort(byCategory).map(x => x.tag);
  const predicted = annotated.filter(x => x.score !== null);
  const unpredicted = annotated.filter(x => x.score === null).sort(byOriginal);
  if (mode === 'predicted_score') predicted.sort(byScore);
  else if (mode === 'predicted_category') predicted.sort((a, b) => (a.categoryRank - b.categoryRank) || (Number(b.score ?? -1) - Number(a.score ?? -1)) || byOriginal(a, b));
  else predicted.sort(byOriginal);
  // Unscored tags are usually manually curated/imported. Keep their relative
  // order and place them after scored/model-predicted tags unless the user
  // explicitly chooses Sort All by Category.
  return [...predicted, ...unpredicted].map(x => x.tag);
}

function tagStrip(item, unknownCategorySelect) {
  const tags = ensureDraft(item);
  requestTagMetadata(tags);
  requestTagScores(item.id, tags);
  const raw = el('textarea', { class: 'tag-raw', 'data-form-key': `tag-raw-${item.id}` }, tags.join(', '));
  raw.dataset.noPersist = '1';
  const strip = el('div', { class: 'tag-strip pointer-sortable', 'data-role': 'ordered-tag-strip', 'data-editor-media-id': item.id });
  const marker = el('span', { class: 'drop-marker' });
  const selectionCategory = el('select', { title: 'Category used by Select/Deselect by Category', onchange: e => { state.editorSelectionCategory = e.target.value; } }, [
    el('option', { value: '' }, 'category…'),
    ...categories().map(c => el('option', { value: c.key }, c.label || c.key))
  ]);
  selectionCategory.value = state.editorSelectionCategory || '';
  const selectedCount = el('span', { class: 'badge', 'data-role': 'editor-selected-tag-count', 'data-editor-media-id': item.id }, '0 highlighted');
  const candidateBox = el('div', { class: 'assistant-candidate-tags' });
  let drag = null;
  let pendingPointer = null;

  function selectedCandidateTagsOutsideDraft() {
    const draftSet = new Set(tags.map(normalizeTag).filter(Boolean));
    return editorSelectedTags(item).map(normalizeTag).filter(tag => tag && !draftSet.has(tag));
  }
  async function addHighlightedCandidatesToDraft(candidateTags = null) {
    const candidates = candidateTags || selectedCandidateTagsOutsideDraft();
    if (!candidates.length) return;
    for (const tag of candidates) await addDraftTag(item, tag, unknownCategorySelect.value || 'custom');
    const selected = new Set(editorSelectedTags(item));
    for (const tag of candidates) selected.add(normalizeTag(tag));
    setEditorSelectedTags(item, [...selected]);
    raw.value = tags.join(', ');
    draw();
  }
  function refreshCandidateBox() {
    const candidates = selectedCandidateTagsOutsideDraft();
    if (!candidates.length) {
      candidateBox.replaceChildren();
      return;
    }
    requestTagMetadata(candidates);
    candidateBox.replaceChildren(
      el('div', { class: 'muted tiny' }, 'Highlighted candidate tags not yet in the draft. These can come from a VLM/LLM preview or manual selection context.'),
      el('div', { class: 'chips open selectable-tags' }, candidates.map(tag => predictionChip(tag, categoryOf(tag, item), item.id, { class: 'chip selected-tag', onclick: async e => { e.preventDefault(); await addHighlightedCandidatesToDraft([tag]); } }))),
      el('div', { class: 'row tight' }, [
        el('button', { class: 'secondary small', onclick: async () => { await addHighlightedCandidatesToDraft(candidates); } }, 'Add Highlighted Candidates to Draft'),
        el('button', { class: 'secondary small', onclick: () => { const draftSet = new Set(tags.map(normalizeTag)); setEditorSelectedTags(item, editorSelectedTags(item).filter(tag => draftSet.has(normalizeTag(tag)))); draw(); } }, 'Clear Candidate Highlights')
      ])
    );
  }
  function refreshSelectedCount() {
    selectedCount.textContent = `${editorSelectedTags(item).length} highlighted`;
  }
  function draw() {
    const selectedNow = new Set(editorSelectedTags(item));
    refreshSelectedCount();
    strip.replaceChildren(...tags.map((tag, idx) => {
      const category = categoryOf(tag, item);
      const cleanTag = normalizeTag(tag);
      const isSelected = selectedNow.has(cleanTag);
      const chipNode = el('span', { class: `tag-chip ${categoryCss(category)} ${isSelected ? 'selected-tag' : ''}`, style: categoryStyle(category), title: scoreTitle(item.id, tag, category), 'data-index': idx, 'data-editor-tag': cleanTag, 'data-editor-media-id': item.id }, [
        el('button', { class: `tag-select-toggle ${isSelected ? 'active' : ''}`, title: isSelected ? 'Deselect/highlight off' : 'Select/highlight this tag', onclick: e => { e.preventDefault(); e.stopPropagation(); toggleEditorSelectedTag(item, tag); draw(); } }, isSelected ? '✓' : '○'),
        el('span', { class: 'tag-chip-text' }, tag),
        tagScoreHoverPanel(item.id, tag),
        el('button', { class: 'tag-x', title: 'Remove tag', onclick: e => { e.preventDefault(); e.stopPropagation(); tags.splice(idx, 1); setEditorSelectedTags(item, editorSelectedTags(item).filter(t => normalizeTag(t) !== cleanTag)); draw(); raw.value = tags.join(', '); } }, '×')
      ]);
      chipNode.addEventListener('pointerdown', e => {
        if (e.target.closest('button')) return;
        e.preventDefault();
        pendingPointer = { from: idx, x: e.clientX, y: e.clientY, chipNode };
        document.addEventListener('pointermove', onMove);
        document.addEventListener('pointerup', onUp, { once: true });
      });
      return chipNode;
    }));
    refreshCandidateBox();
  }
  function beginChipDrag(e) {
    if (!pendingPointer || drag) return;
    drag = { from: pendingPointer.from, to: pendingPointer.from };
    pendingPointer.chipNode.classList.add('dragging');
    strip.classList.add('drag-active');
    const idx = dropIndexFromPointer(strip, e.clientX, e.clientY);
    drag.to = idx;
    positionDropMarker(strip, marker, idx);
  }
  function onMove(e) {
    if (!pendingPointer && !drag) return;
    if (!drag && pendingPointer) {
      const moved = Math.abs(e.clientX - pendingPointer.x) + Math.abs(e.clientY - pendingPointer.y);
      if (moved > 6) beginChipDrag(e);
    }
    if (!drag) return;
    const idx = dropIndexFromPointer(strip, e.clientX, e.clientY);
    drag.to = idx;
    positionDropMarker(strip, marker, idx);
  }
  function onUp() {
    document.removeEventListener('pointermove', onMove);
    if (!drag && pendingPointer) {
      const tag = tags[pendingPointer.from];
      toggleEditorSelectedTag(item, tag);
      pendingPointer = null;
      draw();
      return;
    }
    if (!drag) { pendingPointer = null; return; }
    let { from, to } = drag;
    marker.remove();
    strip.classList.remove('drag-active');
    if (to > from) to -= 1;
    if (to !== from && from >= 0) {
      const [moved] = tags.splice(from, 1);
      tags.splice(Math.max(0, Math.min(to, tags.length)), 0, moved);
    }
    drag = null;
    pendingPointer = null;
    draw();
    raw.value = tags.join(', ');
  }
  function mutateSelection(mode) {
    const current = new Set(editorSelectedTags(item));
    const cleanTags = tags.map(normalizeTag).filter(Boolean);
    const byCategory = () => {
      const wanted = normalizeCategoryKey(selectionCategory.value || state.editorSelectionCategory || '');
      if (!wanted) return [];
      return tags.filter(tag => normalizeCategoryKey(categoryOf(tag, item)) === wanted).map(normalizeTag).filter(Boolean);
    };
    if (mode === 'all') cleanTags.forEach(tag => current.add(tag));
    else if (mode === 'none') current.clear();
    else if (mode === 'invert') cleanTags.forEach(tag => { if (current.has(tag)) current.delete(tag); else current.add(tag); });
    else if (mode === 'category') byCategory().forEach(tag => current.add(tag));
    else if (mode === 'uncategory') byCategory().forEach(tag => current.delete(tag));
    const allowed = new Set(cleanTags);
    setEditorSelectedTags(item, [...current].filter(tag => allowed.has(tag)));
    draw();
  }
  function sortPredictedDraft(mode) {
    const sorted = mode === 'all_category' ? sortDraftTagsWithScores(item, tags, 'all_category') : sortPredictedTagsForDraft(item, tags, mode);
    if (!sorted) { toast('No stored prediction scores are available for these tags yet. Run/refresh a model prediction first, or use Sort All by Category.', false); return; }
    tags.splice(0, tags.length, ...sorted);
    raw.value = tags.join(', ');
    draw();
    if (mode === 'all_category') toast('All draft tags sorted by category.');
    else toast(mode === 'accuracy' ? 'Predicted tags sorted by score; unscored tags kept at the end in current/manual order.' : 'Predicted tags sorted by category; unscored tags kept at the end in current/manual order.');
  }
  function sortDraft(mode) {
    const sorted = sortDraftTagsForEditor(item, tags, mode);
    tags.splice(0, tags.length, ...sorted);
    raw.value = tags.join(', ');
    draw();
  }
  draw();
  const addCtl = tagAutocompleteControl({
    placeholder: 'new_tag or partial tag',
    onPick: async tag => { await addDraftTag(item, tag, unknownCategorySelect.value); draw(); raw.value = tags.join(', '); },
    onCommit: async value => { await addDraftTag(item, value, unknownCategorySelect.value); draw(); raw.value = tags.join(', '); }
  });
  return el('div', { class: 'grid' }, [
    categoryLegend(),
    el('div', { class: 'selection-toolbar' }, [
      selectedCount,
      el('button', { class: 'secondary small', onclick: () => mutateSelection('all') }, 'Select All'),
      el('button', { class: 'secondary small', onclick: () => mutateSelection('none') }, 'Deselect All'),
      el('button', { class: 'secondary small', onclick: () => mutateSelection('invert') }, 'Inverse All'),
      el('button', { class: 'secondary small', title: 'Sort only tags with prediction scores by category; keep tags with no score at the end in the current/manual order.', onclick: () => sortPredictedDraft('category') }, 'Sort Predicted by Category'),
      el('button', { class: 'secondary small', title: 'Sort only tags with prediction scores by confidence; keep tags with no score at the end in the current/manual order.', onclick: () => sortPredictedDraft('accuracy') }, 'Sort Predicted by Accuracy'),
      el('button', { class: 'secondary small', title: 'Sort every draft tag by the selected tag-profile category order.', onclick: () => sortPredictedDraft('all_category') }, 'Sort All by Category'),
      selectionCategory,
      el('button', { class: 'secondary small', onclick: () => mutateSelection('category') }, 'Select by Category'),
      el('button', { class: 'secondary small', onclick: () => mutateSelection('uncategory') }, 'Deselect by Category')
    ]),
    strip,
    candidateBox,
    el('div', { class: 'row' }, [
      addCtl.wrap,
      unknownCategorySelect,
      el('button', { class: 'secondary', onclick: async () => { await addDraftTag(item, addCtl.input.value, unknownCategorySelect.value); addCtl.input.value = ''; draw(); raw.value = tags.join(', '); } }, 'Add / Remember Unknown'),
      el('button', { class: 'secondary', onclick: () => { const next = parseTagString(raw.value); state.tagDrafts[item.id] = next; setEditorSelectedTags(item, editorSelectedTags(item).filter(t => next.includes(normalizeTag(t)))); render(); } }, 'Apply Raw Text to Strip'),
      el('button', { class: 'secondary', onclick: () => { delete state.tagDrafts[item.id]; delete state.tagDraftSource[item.id]; setEditorSelectedTags(item, []); render(); } }, 'Revert to Saved')
    ]),
    el('label', { class: 'label' }, ['Raw tag string', raw])
  ]);
}


function dropIndexFromPointer(strip, x, y) {
  const chips = [...strip.querySelectorAll('.tag-chip:not(.dragging)')];
  if (!chips.length) return 0;
  for (let i = 0; i < chips.length; i++) {
    const rect = chips[i].getBoundingClientRect();
    const inRow = y >= rect.top - 8 && y <= rect.bottom + 8;
    if (inRow && x < rect.left + rect.width / 2) return i;
    if (y < rect.top && x < rect.right) return i;
  }
  return chips.length;
}
function positionDropMarker(strip, marker, idx) {
  const chips = [...strip.querySelectorAll('.tag-chip:not(.dragging)')];
  if (idx >= chips.length) strip.append(marker); else strip.insertBefore(marker, chips[idx]);
}

async function addDraftTag(item, raw, category = 'custom') {
  const tag = firstTag(raw);
  if (!tag || !item) return;
  const tags = ensureDraft(item);
  if (!tags.includes(tag)) tags.push(tag);
  const meta = await api('/api/tags/metadata', { method: 'POST', body: { tags: [tag], profile_key: state.tagProfile } }).catch(() => ({}));
  const known = Boolean(meta[tag]?.known);
  if (!known) await rememberUnknownTags([tag], category);
}
async function rememberUnknownTags(tags, category = 'custom') {
  for (const tag of tags.map(normalizeTag).filter(Boolean)) {
    const r = await api('/api/tags/custom', { method: 'POST', body: { profile_key: state.tagProfile, tag, category } });
    state.tagMeta[state.tagProfile] ||= {};
    state.tagMeta[state.tagProfile][tag] = { tag, category: r.category || category, post_count: 0, known: true, custom: true };
  }
}

function orderingControls() {
  const ordering = el('select', { onchange: e => state.orderingStrategy = e.target.value }, [
    el('option', { value: 'retain' }, 'Retain current/custom order'),
    el('option', { value: 'booru' }, 'By selected booru/profile category precedence'),
    el('option', { value: 'lora_purpose' }, 'By LoRA/model purpose: style → character → concept'),
    el('option', { value: 'custom_profile' }, 'By custom profile precedence')
  ]);
  ordering.value = state.orderingStrategy;
  return ordering;
}

function selectedEditorItems() { return selectedMediaItemsCached(); }
function activeEditorItem() {
  const queue = selectedEditorItems();
  if (queue.length) {
    const current = state.activeMedia ? queue.find(x => x.id === state.activeMedia.id) : null;
    if (current) { state.editorFocus = queue.findIndex(x => x.id === current.id); return current; }
    state.editorFocus = Math.max(0, Math.min(state.editorFocus || 0, queue.length - 1));
    state.activeMedia = queue[state.editorFocus];
    return state.activeMedia;
  }
  return state.activeMedia || state.media.items.find(x => state.selected.has(x.id)) || state.media.items[0];
}
function editorQueueControls(item) {
  const queue = selectedEditorItems();
  if (queue.length <= 1) return el('p', { class: 'muted tiny' }, 'Select multiple gallery items to switch through them here.');
  const idx = Math.max(0, queue.findIndex(x => x.id === item.id));
  state.editorFocus = idx;
  const select = el('select', { onchange: e => { const chosen = queue.find(x => x.id === Number(e.target.value)); if (chosen) { state.activeMedia = chosen; state.editorFocus = queue.findIndex(x => x.id === chosen.id); render(); } } }, queue.map((x, i) => el('option', { value: x.id }, `${i + 1}: ${x.relative_path || x.path}`)));
  select.value = item.id;
  return el('div', { class: 'row' }, [
    el('span', { class: 'badge' }, `${queue.length} selected`),
    el('button', { class: 'secondary small', onclick: () => { state.editorFocus = (idx - 1 + queue.length) % queue.length; state.activeMedia = queue[state.editorFocus]; render(); } }, '◀ Previous'),
    select,
    el('button', { class: 'secondary small', onclick: () => { state.editorFocus = (idx + 1) % queue.length; state.activeMedia = queue[state.editorFocus]; render(); } }, 'Next ▶')
  ]);
}

function tagEditorView() {
  const item = activeEditorItem();
  if (!item) return card('Tag Editor', [el('p', { class: 'muted' }, 'Load the gallery and select an image.')]);
  const captionText = el('textarea', { 'data-form-key': `caption-${item.id}` }, item.caption || '');
  captionText.dataset.noPersist = '1';
  const unknownCategory = el('select', {}, categories().map(c => el('option', { value: c.key }, c.label || c.key))); unknownCategory.value = 'custom';
  const retainOrder = el('input', { type: 'checkbox', checked: state.retainImportedOrder, onchange: e => state.retainImportedOrder = e.target.checked });
  return el('div', { class: 'detail' }, [
    el('div', {}, [mediaPreviewElement(item, 'preview')]),
    el('div', { class: 'grid' }, [
      card('Selected Media', [editorQueueControls(item), el('div', { class: 'muted path' }, item.path)]),
      card('Tag Source, Ordering, and Unknown Tags', [
        el('p', { class: 'muted' }, 'Autocomplete, colors, and precedence come from the active profile. Unknown tags are persisted to the selected profile with your chosen category.'),
        el('div', { class: 'row' }, [tagProfileSelect(), orderingControls(), el('label', {}, [retainOrder, ' Custom dataset: retain existing imported order'])]),
        el('button', { class: 'secondary', onclick: async () => {
          try { const tags = ensureDraft(item); const strategy = retainOrder.checked ? 'retain' : state.orderingStrategy; const r = await api('/api/tags/reorder', { method: 'POST', body: { tags, profile_key: state.tagProfile, strategy } }); state.tagDrafts[item.id] = r.tags; state.tagMeta[state.tagProfile] ||= {}; Object.assign(state.tagMeta[state.tagProfile], r.metadata || {}); render(); } catch (err) { toast(err.message, false); }
        } }, 'Apply Ordering Strategy to Draft'),
        el('button', { class: 'secondary', onclick: async () => { await reapplyVisibleCategories(false); state.activeMedia = cacheMediaItem(await api(`/api/media/${item.id}`)); render(); } }, 'Reapply Categories to This/Selected')
      ]),
      card('Ordered Category-Colored Tag Editor', [
        el('p', { class: 'muted' }, 'Drag a chip with the mouse to reorder. The insertion marker shows where it will land. Click × to remove a tag.'),
        tagStrip(item, unknownCategory),
        el('button', { class: 'primary', onclick: async () => {
          try { const tags = ensureDraft(item); const strategy = retainOrder.checked ? 'retain' : state.orderingStrategy; await api(`/api/media/${item.id}/tags`, { method: 'PUT', body: { tag_string: tags.join(', '), tag_profile: state.tagProfile, order_strategy: strategy } }); toast('Ordered tags saved'); delete state.tagDrafts[item.id]; delete state.tagDraftSource[item.id]; await loadMedia(); state.activeMedia = cacheMediaItem(await api(`/api/media/${item.id}`)); render(); } catch (err) { toast(err.message, false); }
        } }, 'Save Ordered Tags')
      ]),
      modelTagSelectionCard({
        title: 'LLM/VLM/Assistant Tag Selection for This Image',
        description: 'Run the assistant against only the image open in the editor. Preview highlights matching chips; remove/keep/set/add applies directly to this image. You can manually highlight chips first and then apply or send those highlighted tags as candidate context.',
        getMediaIds: () => [item.id],
        getCandidateTags: () => editorManualCandidateTags(item),
        getCandidateTagsByMedia: () => ({ [String(item.id)]: editorManualCandidateTags(item) }),
        targetLabel: () => `Image #${item.id}`,
        categorySize: '5',
        defaultCriteria: 'look at the image and validate existing tags by selecting the ones that match and/or are present in the image.',
        allCategoriesDefault: true,
        validateExistingTagsDefault: true,
        afterRun: async (result, operation) => {
          if (operation === 'preview') markEditorAssistantSelection(result, item);
          else { delete state.tagDrafts[item.id]; delete state.tagDraftSource[item.id]; state.editorAssistantSelection = null; setEditorSelectedTags(item, []); state.activeMedia = cacheMediaItem(await api(`/api/media/${item.id}`)); }
        }
      }),
      imageTagRatingQuickRunCard({ title: 'Quick Tag / Rating Model for This Image', getMediaIds: () => [item.id] }),
      metadataQuickCard({ title: 'Metadata Extraction / Compose for This Image', getMediaIds: () => [item.id] }),
      card('Caption', [captionText, el('button', { class: 'primary', onclick: async () => { try { await api(`/api/media/${item.id}/caption`, { method: 'PUT', body: { caption: captionText.value } }); toast('Caption saved'); await loadMedia(); state.activeMedia = cacheMediaItem(await api(`/api/media/${item.id}`)); render(); } catch (err) { toast(err.message, false); } } }, 'Save Caption')])
    ])
  ]);
}


async function loadAnnotationState(mediaId) {
  if (!mediaId) return null;
  state.annotationState = await api(`/api/reference/annotations/editor-state/${mediaId}`);
  return state.annotationState;
}

function annotationModelFilter(m) {
  const caps = new Set(m.capabilities || []);
  // Keep this dropdown restricted to models that can actually return spatial
  // annotations. Generic chat/tag/caption assistants are intentionally excluded
  // because selecting one here can make SAM/YOLO dispatch try to use strings such
  // as "dataset-assistant" as checkpoint paths. VLM/API rows must advertise
  // the explicit "annotation" or "open_vocabulary" capability to appear here.
  const spatialCaps = ['detect','bbox','segment','mask','video_mask','pose','pose2d','pose3d','keypoints','annotation','open_vocabulary','custom_pt_compatible'];
  if (m.name === 'dataset-assistant' || caps.has('no-model-download') || caps.has('caption_suggestions') || caps.has('tag_suggestions')) return false;
  return spatialCaps.some(x => caps.has(x)) || ['detection','segmentation','pose2d','pose3d','custom'].includes(m.kind);
}
function selectedAnnotationModel() {
  const models = state.models.filter(annotationModelFilter);
  if (state.annotationModel && !models.some(m => m.name === state.annotationModel)) state.annotationModel = '';
  if (!state.annotationModel && models.length) {
    const preferred = models.find(m => (m.name || '').startsWith('sam-vit-b')) || models.find(m => (m.name || '').includes('yolo11n-seg')) || models[0];
    state.annotationModel = preferred.name;
  }
  return state.models.find(m => m.name === state.annotationModel) || models[0] || null;
}
async function refreshAnnotationModelStatus(modelKey, opts = {}) {
  const params = new URLSearchParams({ model_key: modelKey || '' });
  if (opts.local_model_path) params.set('local_model_path', opts.local_model_path);
  if (opts.custom_model_type) params.set('custom_model_type', opts.custom_model_type);
  state.annotationModelStatus = await api(`/api/reference/annotations/model-status?${params.toString()}`);
  return state.annotationModelStatus;
}
function annotationModelStatusPanel(m) {
  const status = state.annotationModelStatus && state.annotationModelStatus.model_key === (m && m.name) ? state.annotationModelStatus : null;
  const localPath = el('input', { placeholder: 'Optional custom/local model path (.pt/.pth/.onnx/.safetensors/etc.)', value: state.annotationLocalModelPath || '', style: 'min-width:420px', oninput: e => { state.annotationLocalModelPath = e.target.value; } });
  const customType = el('select', { onchange: e => { state.annotationCustomModelType = e.target.value; } }, ['auto','yolo','sam','sam_hq','sam2','grounding_dino','pose2d','pose3d','custom'].map(x => el('option', { value: x }, x)));
  customType.value = state.annotationCustomModelType || 'auto';
  const badges = [];
  const downloadActive = m ? stageActive(m, 'download') : false;
  const loadActive = m ? stageActive(m, 'load') : false;
  if (m) {
    badges.push(el('span', { class: 'chip' }, m.provider || 'provider'));
    badges.push(el('span', { class: 'chip' }, m.kind || 'kind'));
    if (m.download_supported) badges.push(el('span', { class: 'chip' }, m.downloaded ? 'weights downloaded' : 'weights not downloaded'));
    else badges.push(el('span', { class: 'chip' }, 'custom/API/no download'));
    if (status) badges.push(el('span', { class: `chip ${status.available ? 'cat-general' : 'cat-invalid'}` }, status.available ? 'runtime available' : 'runtime not ready'));
    if (m.vram_gb) badges.push(el('span', { class: 'chip' }, `~${m.vram_gb} GB VRAM`));
  }
  return card('Annotation Model Status / Download / Load', [
    el('p', { class: 'muted' }, 'Use this panel to install optional annotation runtimes, download official weights, validate/load a selected model, or point to a custom trained local checkpoint.'),
    el('div', { class: 'chips open' }, badges),
    m ? modelLifecycleStrip(m, true) : null,
    el('div', { class: 'row' }, [
      localPath, customType,
      el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/reference/annotations/install-deps', { method: 'POST', body: { include_sam2: false } }); state.annotationLastJob = r.job_id; toast(`Annotation dependency install queued as job ${r.job_id}`); } catch (err) { toast(err.message, false); } } }, 'Install SAM/SAM-HQ/YOLO Deps'),
      el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/reference/annotations/install-deps', { method: 'POST', body: { include_sam2: true } }); state.annotationLastJob = r.job_id; toast(`Annotation dependency install with SAM2 queued as job ${r.job_id}`); } catch (err) { toast(err.message, false); } } }, 'Install + SAM2 Deps'),
      el('button', { class: 'secondary', onclick: async () => { try { await refreshAnnotationModelStatus(m?.name || '', { local_model_path: state.annotationLocalModelPath || '', custom_model_type: state.annotationCustomModelType || 'auto' }); toast('Annotation model status refreshed'); render(); } catch (err) { toast(err.message, false); } } }, 'Check Status')
    ]),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', disabled: !(m && m.download_supported) || downloadActive || loadActive, onclick: async () => { try { const r = await api('/api/reference/annotations/download-model', { method: 'POST', body: { model_key: m.name, dry_run: true, parallel_downloads: modelDownloadWorkerCount() } }); state.annotationLastJob = r.job_id; await refreshModelStatuses(); toast(`Annotation model download dry-run queued as job ${r.job_id}`); render(); } catch (err) { toast(err.message, false); } } }, 'Dry-run Download'),
      el('button', { class: 'primary', disabled: !(m && m.download_supported) || downloadActive || loadActive, onclick: async () => { try { const r = await api('/api/reference/annotations/download-model', { method: 'POST', body: { model_key: m.name, dry_run: false, parallel_downloads: modelDownloadWorkerCount() } }); state.annotationLastJob = r.job_id; await refreshModelStatuses(); toast(`Annotation model download queued as job ${r.job_id}`); render(); } catch (err) { toast(err.message, false); } } }, m && m.downloaded ? 'Re-download / Update Weights' : 'Download Weights'),
      el('button', { class: 'primary', disabled: !(m && m.name) || downloadActive || loadActive, onclick: async () => { try { state.annotationModelStatus = await api('/api/reference/annotations/load-model', { method: 'POST', body: { model_key: m?.name || '', device: state.annotationDevice || 'auto', options: { local_model_path: state.annotationLocalModelPath || '', custom_model_type: state.annotationCustomModelType || 'auto' } } }); await refreshModelStatuses(); toast('Annotation model validated/loaded'); render(); } catch (err) { toast(err.message, false); } } }, 'Load / Validate'),
      el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/models/unload', { method: 'POST', body: { model_name: m?.name } }); await refreshAll(); toast(r.job_id ? `Unload queued as job ${r.job_id}` : (r.message || 'No loaded model to unload.')); render(); } catch (err) { toast(err.message, false); } } }, 'Unload'),
      state.annotationLastJob ? el('button', { class: 'secondary', onclick: () => setTab('Jobs') }, `Open Job #${state.annotationLastJob}`) : null
    ].filter(Boolean)),
    el('pre', { class: 'log' }, JSON.stringify(status || m || {}, null, 2))
  ]);
}


function pose3DViewerCard(poseText) {
  const canvas = el('canvas', { class: 'pose3d-canvas', width: 520, height: 360 });
  const name = el('input', { placeholder: 'joint name', value: `joint_${(state.annotationPose3D || []).length}` });
  const x = el('input', { type: 'number', step: '0.05', value: '0', title: 'x' });
  const y = el('input', { type: 'number', step: '0.05', value: '0', title: 'y/up' });
  const z = el('input', { type: 'number', step: '0.05', value: '0', title: 'z/depth' });
  const from = el('input', { placeholder: 'edge from index/name', style: 'width:130px' });
  const to = el('input', { placeholder: 'edge to index/name', style: 'width:130px' });
  function syncPoseText() {
    if (poseText) poseText.value = JSON.stringify({ keypoints_2d: state.annotationPose2D || [], keypoints_3d: state.annotationPose3D || [], edges: state.annotationEdges || [] }, null, 2);
  }
  function project(p) {
    const scale = 95;
    const px = canvas.width / 2 + Number(p.x || 0) * scale + Number(p.z || 0) * scale * 0.45;
    const py = canvas.height / 2 - Number(p.y || 0) * scale + Number(p.z || 0) * scale * 0.28;
    return { x: px, y: py };
  }
  function draw() {
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(148,163,184,0.35)'; ctx.lineWidth = 1;
    for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(canvas.width/2 + i*40, 20); ctx.lineTo(canvas.width/2 + i*40, canvas.height-20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(20, canvas.height/2 + i*40); ctx.lineTo(canvas.width-20, canvas.height/2 + i*40); ctx.stroke(); }
    const pts = state.annotationPose3D || [];
    ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 3;
    for (const e of state.annotationEdges || []) {
      const a = typeof e[0] === 'number' ? pts[e[0]] : pts.find(p => p.name === e[0]);
      const b = typeof e[1] === 'number' ? pts[e[1]] : pts.find(p => p.name === e[1]);
      if (!a || !b) continue;
      const pa = project(a), pb = project(b); ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke();
    }
    pts.forEach((p, i) => { const q = project(p); ctx.beginPath(); ctx.fillStyle = '#facc15'; ctx.arc(q.x, q.y, 6, 0, Math.PI*2); ctx.fill(); ctx.fillStyle = '#e2e8f0'; ctx.fillText(`${i}:${p.name || ''}`, q.x + 8, q.y - 8); });
  }
  setTimeout(draw, 0);
  return card('Mini 3D Pose / Bone Viewer', [
    el('p', { class: 'muted' }, 'Create a lightweight 3D skeleton annotation for a Blender character/rig mapping dataset. Use normalized coordinates for now; the Blender bridge can import/export these joints and edges.'),
    canvas,
    el('div', { class: 'row' }, [name, el('label', {}, ['x', x]), el('label', {}, ['y', y]), el('label', {}, ['z', z]),
      el('button', { class: 'primary', onclick: () => { const pts = state.annotationPose3D || []; const joint = { name: name.value || `joint_${pts.length}`, x: Number(x.value || 0), y: Number(y.value || 0), z: Number(z.value || 0) }; state.annotationPose3D = [...pts, joint]; if (pts.length) state.annotationEdges = [...(state.annotationEdges || []), [pts.length - 1, pts.length]]; syncPoseText(); render(); } }, 'Add Joint + Auto-edge')
    ]),
    el('div', { class: 'row' }, [from, to,
      el('button', { class: 'secondary', onclick: () => { const parse = v => /^\d+$/.test(v) ? Number(v) : v; if (from.value && to.value) state.annotationEdges = [...(state.annotationEdges || []), [parse(from.value), parse(to.value)]]; syncPoseText(); render(); } }, 'Add Edge'),
      el('button', { class: 'secondary', onclick: () => { state.annotationPose3D = []; state.annotationEdges = []; syncPoseText(); render(); } }, 'Clear 3D Pose'),
      el('button', { class: 'secondary', onclick: () => { syncPoseText(); toast('3D pose JSON synced to annotation metadata field.'); } }, 'Sync JSON')
    ]),
    el('details', {}, [el('summary', {}, 'Current 3D joints / edges'), el('pre', { class: 'log' }, JSON.stringify({ keypoints_3d: state.annotationPose3D || [], edges: state.annotationEdges || [] }, null, 2))])
  ]);
}

function annotationEditorView() {
  const item = activeEditorItem();
  if (!item) return card('Annotation Editor', [el('p', { class: 'muted' }, 'Load the gallery and select an image.')]);
  if (!state.annotationState || !state.annotationState.media || Number(state.annotationState.media.id) !== Number(item.id)) {
    setTimeout(async () => { try { await loadAnnotationState(item.id); render(); } catch (err) { toast(err.message, false); } }, 0);
    return card('Annotation Editor', [el('p', { class: 'muted' }, `Loading annotation state for image #${item.id}...`)]);
  }
  const annotations = state.annotationState.annotations || [];
  const label = el('input', { value: state.annotationLabel || 'object', placeholder: 'label / class name' });
  label.addEventListener('input', e => { state.annotationLabel = e.target.value; });
  const target = el('input', { value: state.annotationTarget || '', placeholder: 'optional target / character name' });
  target.addEventListener('input', e => { state.annotationTarget = e.target.value; });
  const mode = el('select', { onchange: e => { state.annotationMode = e.target.value; state.annotationDraftBbox = null; state.annotationPolygon = []; state.annotationPose2D = []; render(); } }, ['bbox', 'bbox_mask', 'polygon', 'mask', 'pose2d', 'pose3d', 'animation_pose'].map(x => el('option', { value: x }, x)));
  mode.value = state.annotationMode || 'bbox';
  const selectedModel = selectedAnnotationModel() || { name: '', label: 'No annotation model selected', downloaded: false, installed: false, capabilities: [] };
  const modelSelect = el('select', { onchange: async e => { state.annotationModel = e.target.value; try { await refreshAnnotationModelStatus(state.annotationModel, { local_model_path: state.annotationLocalModelPath || '', custom_model_type: state.annotationCustomModelType || 'auto' }); } catch (_) {} render(); } }, [el('option', { value: '' }, 'Select a real model — no fallback boxes/masks'), ...modelOptions(annotationModelFilter)]);
  modelSelect.value = state.annotationModel || (selectedModel && selectedModel.name) || '';
  const prompt = el('textarea', { rows: '2', placeholder: 'Prompt for model/assistant proposal, e.g. detect the blue-haired character, segment the foreground subject, estimate the 2D pose skeleton' }, state.annotationPrompt || 'find the target object');
  prompt.addEventListener('input', e => { state.annotationPrompt = e.target.value; });
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.05', value: state.annotationThreshold || state.settings.classifier_threshold || 0.35, oninput: e => { state.annotationThreshold = e.target.value; } });
  const device = el('input', { placeholder: 'device: auto, cpu, cuda:0', value: state.annotationDevice || 'auto', style: 'width:150px', oninput: e => { state.annotationDevice = e.target.value; } });
  const maxProps = el('input', { type: 'number', min: '1', max: '1000', value: state.annotationMaxProposals || 25, style: 'width:90px', oninput: e => { state.annotationMaxProposals = e.target.value; } });
  const imgsz = el('input', { type: 'number', min: '128', step: '32', value: state.annotationImageSize || 1024, style: 'width:90px', oninput: e => { state.annotationImageSize = e.target.value; } });
  const iou = el('input', { type: 'number', min: '0', max: '1', step: '0.05', value: state.annotationIou || 0.5, style: 'width:90px', oninput: e => { state.annotationIou = e.target.value; } });
  const bboxPrompt = el('textarea', { rows: '2', placeholder: 'Optional SAM bbox prompt JSON, e.g. {"x1":10,"y1":20,"x2":400,"y2":500}' }, state.annotationBboxPrompt || '');
  bboxPrompt.addEventListener('input', e => { state.annotationBboxPrompt = e.target.value; });
  const poseText = el('textarea', { rows: '4', style: 'width:100%', placeholder: 'Optional pose/keypoint JSON. 2D points can also be clicked on the image canvas.' }, JSON.stringify({ keypoints_2d: state.annotationPose2D || [], keypoints_3d: state.annotationPose3D || [], edges: state.annotationEdges || [] }, null, 2));
  const maskPath = el('input', { placeholder: 'Mask PNG path exported from Krita or another editor', style: 'min-width:360px' });
  function proposalOptions() {
    let bp = null;
    try { bp = bboxPrompt.value.trim() ? JSON.parse(bboxPrompt.value) : null; } catch (_) { bp = null; }
    let pose = {};
    try { pose = poseText.value.trim() ? JSON.parse(poseText.value) : {}; } catch (_) { pose = {}; }
    return {
      local_model_path: state.annotationLocalModelPath || '',
      custom_model_type: state.annotationCustomModelType || 'auto',
      max_proposals: Number(maxProps.value || 25),
      imgsz: Number(imgsz.value || 1024),
      iou: Number(iou.value || 0.5),
      bbox_prompt: bp,
      keypoints_2d: pose.keypoints_2d || state.annotationPose2D || [],
      keypoints_3d: pose.keypoints_3d || state.annotationPose3D || [],
      edges: pose.edges || state.annotationEdges || [],
      frames: pose.frames || [],
      allow_fallback: false
    };
  }
  return el('div', { class: 'grid' }, [
    card('Annotation Editor: bboxes + segmentation masks + pose labels', [
      editorQueueControls(item),
      el('p', { class: 'muted' }, 'Draw multiple bboxes, polygons, masks, 2D keypoint sets, or 3D/animation pose metadata per image. Model proposals now dispatch to selected YOLO/SAM/SAM-HQ/SAM2/VLM/API adapters when available.'),
      el('div', { class: 'chips open' }, [el('span', { class: 'chip' }, 'bbox: drag rectangle'), el('span', { class: 'chip' }, 'polygon/mask: click points'), el('span', { class: 'chip' }, 'pose2d: click joints; edges auto-connect'), el('span', { class: 'chip' }, 'pose3d: use Mini 3D Pose Viewer')]),
      el('div', { class: 'row' }, [label, target, mode, el('button', { class: 'secondary', onclick: async () => { await loadAnnotationState(item.id); render(); } }, 'Refresh Annotations')]),
      (['image','animation'].includes(item.media_type) ? annotationCanvas(item, annotations) : el('div', {}, [mediaPreviewElement(item, 'preview'), el('p', { class: 'muted' }, 'Video/audio annotation is done on extracted frames or imported masks. Use Media Tools to extract PNG frames or audio clips, then annotate those dataset items.')]))
    ]),
    annotationModelStatusPanel(selectedModel),
    card('Model-assisted generation controls', [
      el('p', { class: 'muted' }, 'Preview/Generate only displays model-produced proposals. If the model is missing, fails, or returns no detections, no fake box or mask is created.'),
      el('div', { class: 'row' }, [modelSelect, el('label', {}, ['threshold', threshold]), el('label', {}, ['device', device]), el('label', {}, ['max proposals', maxProps]), el('label', {}, ['imgsz', imgsz]), el('label', {}, ['IoU', iou])]),
      el('div', { class: 'row' }, [el('button', { class: 'secondary', onclick: async () => { try { await refreshAnnotationModelStatus(modelSelect.value, { local_model_path: state.annotationLocalModelPath || '', custom_model_type: state.annotationCustomModelType || 'auto' }); toast('Status refreshed'); render(); } catch (err) { toast(err.message, false); } } }, 'Refresh Selected Model Status')]),
      prompt,
      bboxPrompt,
      el('details', {}, [el('summary', {}, '2D / 3D pose JSON editor'), poseText]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => {
          try {
            state.annotationOutput = await api('/api/reference/annotations/propose', { method: 'POST', body: { media_id: item.id, label: label.value || 'object', target_name: target.value || '', prompt: prompt.value, model_key: modelSelect.value || '', threshold: Number(threshold.value || 0.35), annotation_type: mode.value, save: false, create_mask: mode.value.includes('mask'), device: device.value || 'auto', options: proposalOptions() } });
            state.annotationModelStatus = state.annotationOutput.model_status || state.annotationModelStatus;
            if (state.annotationOutput.ok === false) { toast(state.annotationOutput.error || 'No model-generated proposals were produced.', false); render(); return; }
            const p = (state.annotationOutput.proposals || [])[0]; if (p) { state.annotationDraftBbox = p.bbox || null; state.annotationPolygon = p.polygon || []; state.annotationPose2D = p.metadata?.keypoints_2d || state.annotationPose2D || []; state.annotationPose3D = p.metadata?.keypoints_3d || state.annotationPose3D || []; }
            toast(`Generated ${state.annotationOutput.count || 0} model proposal(s)`); render();
          } catch (err) { toast(err.message, false); }
        } }, 'Preview Proposal'),
        el('button', { class: 'primary', onclick: async () => {
          try {
            state.annotationOutput = await api('/api/reference/annotations/propose', { method: 'POST', body: { media_id: item.id, label: label.value || 'object', target_name: target.value || '', prompt: prompt.value, model_key: modelSelect.value || '', threshold: Number(threshold.value || 0.35), annotation_type: mode.value, save: true, create_mask: mode.value.includes('mask'), device: device.value || 'auto', options: proposalOptions() } });
            state.annotationModelStatus = state.annotationOutput.model_status || state.annotationModelStatus;
            if (state.annotationOutput.ok === false) { toast(state.annotationOutput.error || 'No model-generated annotations were saved.', false); render(); return; }
            await loadAnnotationState(item.id); toast(`Saved ${state.annotationOutput.saved?.length || 0} model annotation(s)`); render();
          } catch (err) { toast(err.message, false); }
        } }, 'Generate + Save')
      ])
    ]),
    (mode.value === 'pose3d' || mode.value === 'animation_pose') ? pose3DViewerCard(poseText) : null,
    card('Manual save / editor controls', [
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => {
          try {
            let meta = {};
            try { meta = poseText.value.trim() ? JSON.parse(poseText.value) : {}; } catch (_) { meta = {}; }
            const body = { media_id: item.id, label: label.value || 'object', target_name: target.value || '', annotation_type: mode.value, bbox: state.annotationDraftBbox || {}, polygon: state.annotationPolygon || [], metadata: { ...meta, keypoints_2d: (state.annotationPose2D || []).length ? state.annotationPose2D : (meta.keypoints_2d || []), keypoints_3d: (state.annotationPose3D || []).length ? state.annotationPose3D : (meta.keypoints_3d || []), edges: (state.annotationEdges || []).length ? state.annotationEdges : (meta.edges || []) } };
            if (mode.value.includes('bbox') && !body.bbox.x1 && !body.bbox.x) throw new Error('Draw a bbox first.');
            if ((mode.value === 'polygon' || mode.value === 'mask') && (!body.polygon || body.polygon.length < 3)) throw new Error('Click at least 3 polygon points first.');
            if (mode.value === 'pose2d' && !(body.metadata.keypoints_2d || []).length) throw new Error('Click keypoints on the image or paste keypoint JSON first.');
            if ((mode.value === 'pose3d' || mode.value === 'animation_pose') && !(body.metadata.keypoints_3d || []).length) throw new Error('Add 3D joints in the Mini 3D Pose Viewer or paste keypoint JSON first.');
            state.annotationOutput = await api('/api/reference/annotations', { method: 'POST', body });
            state.annotationDraftBbox = null; state.annotationPolygon = []; state.annotationPose2D = [];
            await loadAnnotationState(item.id); toast('Annotation saved'); render();
          } catch (err) { toast(err.message, false); }
        } }, 'Save Drawn / Edited Annotation'),
        el('button', { class: 'secondary', onclick: () => { state.annotationDraftBbox = null; state.annotationPolygon = []; state.annotationPose2D = []; state.annotationPose3D = []; state.annotationEdges = []; render(); } }, 'Clear Draft'),
        el('button', { class: 'secondary', onclick: () => { if ((state.annotationPolygon || []).length) state.annotationPolygon = state.annotationPolygon.slice(0, -1); else if ((state.annotationPose2D || []).length) state.annotationPose2D = state.annotationPose2D.slice(0, -1); render(); } }, 'Undo Last Point'),
        el('button', { class: 'secondary', onclick: () => { const bbox = state.annotationDraftBbox; if (bbox) bboxPrompt.value = JSON.stringify(bbox); state.annotationBboxPrompt = bboxPrompt.value; toast('Draft bbox copied to SAM prompt field'); } }, 'Use Draft BBox as SAM Prompt')
      ])
    ]),
    quickCurationModelRunCard({ title: 'Tag/Rating Classifier for Annotated Image', getMediaIds: () => [item.id], description: 'Run JTP-3 or visual rating models on the image you are annotating so labels, ratings, and annotation decisions can be cross-checked.' }),
    card('Krita annotation bridge', [
      el('p', { class: 'muted' }, 'Export the selected image plus annotation manifest/masks to a Krita handoff folder. Import a mask PNG back as an annotation after editing in Krita.'),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { state.annotationOutput = await api('/api/krita/annotation-package', { method: 'POST', body: { media_id: item.id, annotation_ids: annotations.map(a => a.id), include_masks: true } }); toast('Krita annotation package created'); render(); } catch (err) { toast(err.message, false); } } }, 'Create Krita Annotation Package'),
        maskPath,
        el('button', { class: 'primary', onclick: async () => { try { if (!maskPath.value.trim()) throw new Error('Enter the edited mask PNG path first.'); state.annotationOutput = await api('/api/krita/import-annotation-mask', { method: 'POST', body: { media_id: item.id, mask_path: maskPath.value.trim(), label: label.value || 'object', target_name: target.value || '' } }); await loadAnnotationState(item.id); toast('Krita mask imported as annotation'); render(); } catch (err) { toast(err.message, false); } } }, 'Import Mask Path')
      ]),
      el('a', { href: '/api/krita/plugin', target: '_blank' }, 'Download optional Krita bridge plugin')
    ]),
    card('Blender 3D pose bridge', [
      el('p', { class: 'muted' }, 'Install the Blender bridge plugin to send selected armature bones/joints back to this app as pose3d or animation_pose annotations. Use the current media id in the plugin panel.'),
      el('div', { class: 'row' }, [
        el('span', { class: 'badge' }, `Current media id: ${item.id}`),
        el('a', { href: '/api/blender/plugin', target: '_blank' }, 'Download Blender bridge plugin'),
        el('button', { class: 'secondary', onclick: () => { navigator.clipboard?.writeText(String(item.id)); toast('Media id copied for Blender plugin.'); } }, 'Copy Media ID')
      ]),
      el('pre', { class: 'log' }, JSON.stringify({ keypoints_3d: state.annotationPose3D || [], edges: state.annotationEdges || [] }, null, 2))
    ]),
    imageTagRatingQuickRunCard({ title: 'Quick Tag / Rating Model for Annotated Image', getMediaIds: () => [item.id], description: 'Use JTP/rating/classifier models while annotating so labels can be generated alongside bbox/mask/pose work.' }),
    card('Existing annotations', [annotationTable(annotations)]),
    card('Annotation output', [el('pre', { class: 'log' }, JSON.stringify(state.annotationOutput || {}, null, 2))])
  ]);
}

function annotationCanvas(item, annotations) {
  const wrap = el('div', { class: 'annotation-wrap' });
  const img = el('img', { class: 'annotation-image', src: `/api/media/${item.id}/file` });
  const canvas = el('canvas', { class: 'annotation-canvas' });
  wrap.append(img, canvas);
  let drawing = false;
  let start = null;
  let draft = state.annotationDraftBbox;
  let polygon = state.annotationPolygon || [];
  function resize() {
    const rect = img.getBoundingClientRect();
    const w = img.naturalWidth || item.width || rect.width || 1;
    const h = img.naturalHeight || item.height || rect.height || 1;
    canvas.width = w; canvas.height = h;
    canvas.style.width = `${rect.width || w}px`; canvas.style.height = `${rect.height || h}px`;
    redraw();
  }
  function pos(e) {
    const rect = canvas.getBoundingClientRect();
    return { x: Math.max(0, Math.min(canvas.width, (e.clientX - rect.left) * canvas.width / Math.max(rect.width, 1))), y: Math.max(0, Math.min(canvas.height, (e.clientY - rect.top) * canvas.height / Math.max(rect.height, 1))) };
  }
  function drawBox(ctx, bbox, color = '#38bdf8', label = '') {
    if (!bbox) return;
    const x1 = Number(bbox.x1 ?? bbox.x ?? 0), y1 = Number(bbox.y1 ?? bbox.y ?? 0), x2 = Number(bbox.x2 ?? (x1 + Number(bbox.w || 0))), y2 = Number(bbox.y2 ?? (y1 + Number(bbox.h || 0)));
    ctx.strokeStyle = color; ctx.lineWidth = Math.max(2, canvas.width / 500); ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    if (label) { ctx.fillStyle = 'rgba(0,0,0,0.65)'; ctx.fillRect(x1, Math.max(0, y1 - 20), Math.min(ctx.measureText(label).width + 10, canvas.width - x1), 20); ctx.fillStyle = 'white'; ctx.fillText(label, x1 + 5, Math.max(14, y1 - 6)); }
  }
  function drawPolygon(ctx, points, color = '#a78bfa', label = '') {
    if (!points || !points.length) return;
    ctx.strokeStyle = color; ctx.fillStyle = 'rgba(167,139,250,0.22)'; ctx.lineWidth = Math.max(2, canvas.width / 500); ctx.beginPath();
    points.forEach((p, i) => { if (i === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]); });
    if (points.length > 2) ctx.closePath(); ctx.fill(); ctx.stroke();
    for (const p of points) { ctx.beginPath(); ctx.arc(p[0], p[1], 4, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill(); }
    if (label && points[0]) { ctx.fillStyle = 'white'; ctx.fillText(label, points[0][0] + 5, points[0][1] - 5); }
  }
  function drawPose2D(ctx, points, edges = [], color = '#eab308', label = '') {
    const pts = (points || []).map((p, i) => ({ name: p.name || String(i), x: Number(p.x ?? p[0] ?? 0), y: Number(p.y ?? p[1] ?? 0) }));
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = Math.max(2, canvas.width / 700);
    for (const e of edges || []) {
      const a = typeof e[0] === 'number' ? pts[e[0]] : pts.find(p => p.name === e[0]);
      const b = typeof e[1] === 'number' ? pts[e[1]] : pts.find(p => p.name === e[1]);
      if (a && b) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
    }
    pts.forEach((p, i) => { ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = 'white'; ctx.fillText(p.name || String(i), p.x + 6, p.y - 6); ctx.fillStyle = color; });
    if (label && pts[0]) { ctx.fillStyle = 'white'; ctx.fillText(label, pts[0].x + 8, pts[0].y + 12); }
  }
  function redraw() {
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.font = `${Math.max(12, Math.round(canvas.width / 80))}px sans-serif`;
    for (const ann of annotations || []) {
      if (ann.bbox && Object.keys(ann.bbox).length) drawBox(ctx, ann.bbox, '#22c55e', ann.label || ann.target_name || ann.annotation_type || 'annotation');
      if (ann.polygon && ann.polygon.length) drawPolygon(ctx, ann.polygon, '#f97316', ann.label || ann.target_name || 'mask');
      if (ann.metadata && ann.metadata.keypoints_2d) drawPose2D(ctx, ann.metadata.keypoints_2d, ann.metadata.edges || [], '#06b6d4', ann.label || 'pose2d');
    }
    if (draft) drawBox(ctx, draft, '#ef4444', 'draft');
    if (polygon && polygon.length) drawPolygon(ctx, polygon, '#ef4444', 'draft mask');
    if ((state.annotationPose2D || []).length) drawPose2D(ctx, state.annotationPose2D, state.annotationEdges || [], '#ef4444', 'draft pose2d');
  }
  canvas.addEventListener('pointerdown', e => {
    const p = pos(e);
    if ((state.annotationMode || 'bbox').includes('bbox')) { drawing = true; start = p; draft = { x1: p.x, y1: p.y, x2: p.x, y2: p.y }; }
    else if ((state.annotationMode || '') === 'pose2d') { const idx = (state.annotationPose2D || []).length; state.annotationPose2D = [...(state.annotationPose2D || []), { name: `kp_${idx}`, x: p.x, y: p.y }]; if (idx > 0) state.annotationEdges = [...(state.annotationEdges || []), [idx - 1, idx]]; }
    else { polygon = [...polygon, [p.x, p.y]]; state.annotationPolygon = polygon; }
    redraw();
  });
  canvas.addEventListener('pointermove', e => { if (!drawing || !start) return; const p = pos(e); draft = { x1: Math.min(start.x, p.x), y1: Math.min(start.y, p.y), x2: Math.max(start.x, p.x), y2: Math.max(start.y, p.y) }; state.annotationDraftBbox = draft; redraw(); });
  window.addEventListener('pointerup', () => { if (drawing) { drawing = false; state.annotationDraftBbox = draft; } });
  canvas.addEventListener('dblclick', e => { e.preventDefault(); if (!(state.annotationMode || '').includes('bbox')) { state.annotationPolygon = polygon; toast(`${polygon.length} polygon point(s) / ${(state.annotationPose2D || []).length} keypoint(s) captured. Press Save Drawn Annotation.`); } });
  img.addEventListener('load', resize); setTimeout(resize, 0); window.addEventListener('resize', resize, { once: true });
  return wrap;
}

function annotationTable(rows) {
  if (!rows || !rows.length) return el('p', { class: 'muted' }, 'No annotations saved for this media item yet.');
  return el('div', { class: 'table-scroll' }, el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['ID','Label','Type','Source','Confidence','BBox','Polygon pts','Mask','Metadata','Actions'].map(h => el('th', {}, h)))),
    el('tbody', {}, rows.map(a => el('tr', {}, [
      el('td', {}, a.id), el('td', {}, a.label || ''), el('td', {}, a.annotation_type || ''), el('td', {}, a.source || ''), el('td', {}, a.confidence == null ? '' : Number(a.confidence).toFixed(3)),
      el('td', { class: 'tiny' }, a.bbox ? JSON.stringify(a.bbox) : ''), el('td', {}, (a.polygon || []).length), el('td', { class: 'path tiny' }, a.mask_path || ''), el('td', { class: 'tiny' }, a.metadata ? JSON.stringify(a.metadata) : ''),
      el('td', {}, el('div', { class: 'row' }, [
        el('button', { class: 'secondary small', onclick: () => { state.annotationDraftBbox = a.bbox || null; state.annotationPolygon = a.polygon || []; state.annotationPose2D = a.metadata?.keypoints_2d || []; state.annotationPose3D = a.metadata?.keypoints_3d || []; state.annotationEdges = a.metadata?.edges || []; toast('Annotation loaded into draft editor'); render(); } }, 'Load Draft'),
        el('button', { class: 'danger small', onclick: async () => { try { await api(`/api/reference/annotations/${a.id}`, { method: 'DELETE' }); await loadAnnotationState(a.media_id); toast('Annotation deleted'); render(); } catch (err) { toast(err.message, false); } } }, 'Delete')
      ]))
    ])))
  ]));
}


function spatialTaskModels(task) {
  return task === 'detection' ? (state.detectionModels || []) : (state.segmentationModels || []);
}

function selectedSpatialModel(task) {
  const models = spatialTaskModels(task);
  const keyName = task === 'detection' ? 'detectionModel' : 'segmentationModel';
  let key = state[keyName] || '';
  if (key && !models.some(row => row.name === key)) key = '';
  if (!key && models.length) {
    const preferred = task === 'detection'
      ? (models.find(row => row.name === 'yolo11n-detect') || models[0])
      : (models.find(row => row.name === 'yolo11n-seg') || models.find(row => row.name === 'sam-vit-b') || models[0]);
    key = preferred?.name || '';
    state[keyName] = key;
  }
  return models.find(row => row.name === key) || models[0] || null;
}

function spatialModelSelect(task) {
  const models = spatialTaskModels(task);
  const current = selectedSpatialModel(task);
  const select = el('select', { onchange: async e => {
    await releaseSpatialPreviewFiles(task);
    if (task === 'detection') { state.detectionModel = e.target.value; state.detectionClassInfo = null; state.detectionOutput = null; }
    else { state.segmentationModel = e.target.value; state.segmentationClassInfo = null; state.segmentationOutput = null; }
    try { await refreshSpatialModelStatus(task, e.target.value); } catch (_) {}
    try { await refreshSpatialModelClasses(task, e.target.value); } catch (_) {}
    render();
  } }, [el('option', { value: '' }, `Select ${task} model — no fallback output`), ...models.map(row => el('option', { value: row.name }, modelLabel(row)))]);
  select.value = current?.name || '';
  return select;
}

async function refreshSpatialModelStatus(task, modelKey) {
  const localKey = task === 'detection' ? 'detectionLocalModelPath' : 'segmentationLocalModelPath';
  const typeKey = task === 'detection' ? 'detectionCustomModelType' : 'segmentationCustomModelType';
  const params = new URLSearchParams({ model_key: modelKey || '' });
  if (state[localKey]) params.set('local_model_path', state[localKey]);
  if (state[typeKey]) params.set('custom_model_type', state[typeKey]);
  const status = await api(`/api/reference/annotations/model-status?${params.toString()}`);
  if (task === 'detection') state.detectionModelStatus = status;
  else state.segmentationModelStatus = status;
  return status;
}

async function refreshSpatialModelClasses(task, modelKey, query = '') {
  if (!modelKey) return null;
  const localKey = task === 'detection' ? 'detectionLocalModelPath' : 'segmentationLocalModelPath';
  const typeKey = task === 'detection' ? 'detectionCustomModelType' : 'segmentationCustomModelType';
  const params = new URLSearchParams({ model_key: modelKey, custom_model_type: state[typeKey] || (task === 'detection' ? 'yolo' : 'auto'), q: query || '', limit: '500' });
  if (state[localKey]) params.set('local_model_path', state[localKey]);
  const info = await api(`/api/spatial/${task}/model-classes?${params.toString()}`);
  if (task === 'detection') state.detectionClassInfo = info;
  else state.segmentationClassInfo = info;
  return info;
}

function spatialClassPanel(task, model) {
  const isDetection = task === 'detection';
  const infoKey = isDetection ? 'detectionClassInfo' : 'segmentationClassInfo';
  const queryKey = isDetection ? 'detectionClassQuery' : 'segmentationClassQuery';
  const searchKey = isDetection ? 'detectionClassSearch' : 'segmentationClassSearch';
  const info = state[infoKey];
  const queryInput = el('input', {
    value: state[queryKey] || '',
    placeholder: info?.mode === 'text_conditioned' ? 'Free-form class/object prompt' : 'Class/token to find (blank = all classes)',
    style: 'min-width:300px',
    oninput: e => { state[queryKey] = e.target.value; }
  });
  const searchInput = el('input', {
    value: state[searchKey] || '', placeholder: 'Search parsed model classes', style: 'min-width:260px',
    oninput: e => { state[searchKey] = e.target.value; }
  });
  const rows = info?.classes || [];
  const modeText = info?.mode === 'closed_set'
    ? 'Closed-set: the typed class is resolved to a real class ID and passed to inference as a strict filter.'
    : info?.mode === 'class_agnostic'
      ? 'Class-agnostic: text does not change mask geometry. Use a bbox prompt or detector-guided segmentation for semantic class-specific masks.'
      : info?.mode === 'text_conditioned'
        ? 'Text-conditioned: the prompt is sent to the model and should change geometry.'
        : (info?.message || 'Inspect the model to determine whether it has a fixed class list.');
  return card(`${isDetection ? 'Detection' : 'Segmentation'} Class / Token Support`, [
    el('div', { class: 'row' }, [
      queryInput,
      el('button', { class: 'secondary', disabled: !model, onclick: async () => { try { await refreshSpatialModelClasses(task, model.name, state[searchKey] || ''); toast('Model class metadata refreshed'); render(); } catch (err) { toast(err.message, false); } } }, 'Inspect / Search Classes'),
      info?.class_count != null ? el('span', { class: 'badge' }, `${info.class_count} class(es)`) : null,
      info?.source ? el('span', { class: 'chip' }, String(info.source)) : null
    ].filter(Boolean)),
    el('p', { class: info?.mode === 'class_agnostic' ? 'muted warning' : 'muted' }, modeText),
    info?.message ? el('p', { class: 'muted tiny' }, info.message) : null,
    info?.mode === 'closed_set' && !rows.length ? el('p', { class: 'bad tiny' }, 'No classes were parsed. Load/validate the custom model or place data.yaml, config.json, classes.txt, labels.txt, or names.txt beside it.') : null,
    rows.length ? el('div', { class: 'class-token-list' }, rows.map(row => el('button', {
      class: `class-token ${String(state[queryKey] || '').toLowerCase() === String(row.name || '').toLowerCase() ? 'active' : ''}`,
      title: `Class ID ${row.id}`,
      onclick: () => { state[queryKey] = row.name; render(); }
    }, `${row.id}: ${row.name}`))) : null,
    info && info.matched_count > info.returned_count ? el('p', { class: 'muted tiny' }, `Showing ${info.returned_count} of ${info.matched_count} matches. Narrow the class search to inspect more.`) : null
  ].filter(Boolean));
}

function spatialPreviewSelection(task) {
  return task === 'detection' ? state.detectionPreviewSelection : state.segmentationPreviewSelection;
}

function resetSpatialPreviewSelection(task, proposals = []) {
  const selection = spatialPreviewSelection(task); selection.clear();
  (proposals || []).forEach((_, index) => selection.add(index));
}

async function releaseSpatialPreviewFiles(task) {
  const outputKey = task === 'detection' ? 'detectionOutput' : 'segmentationOutput';
  const output = state[outputKey];
  const maskPaths = (output?.proposals || []).map(row => row.mask_path).filter(Boolean);
  try { await api(`/api/spatial/${task}/clear-preview`, { method: 'POST', body: { mask_paths: maskPaths } }); } catch (_) {}
}

async function clearSpatialPreview(task) {
  const outputKey = task === 'detection' ? 'detectionOutput' : 'segmentationOutput';
  await releaseSpatialPreviewFiles(task);
  state[outputKey] = null;
  spatialPreviewSelection(task).clear();
  render();
}

async function clearSavedGeneratedSpatial(task, item, modelKey = '') {
  if (!item) return;
  if (!window.confirm(`Delete saved model-generated ${task === 'detection' ? 'boxes' : 'masks'} for this image? Manual annotations are preserved.`)) return;
  const params = modelKey ? `?model_key=${encodeURIComponent(modelKey)}` : '';
  const result = await api(`/api/spatial/${task}/generated/${item.id}${params}`, { method: 'DELETE' });
  await loadAnnotationState(item.id);
  toast(`Deleted ${result.deleted_annotations || 0} saved model-generated annotation(s)`);
  render();
}

function spatialModelPanel(task, model) {
  const isDetection = task === 'detection';
  const isSamFamily = !isDetection && Boolean(model && (/^sam(?:-|2)/.test(String(model.name || ''))));
  const status = (isDetection ? state.detectionModelStatus : state.segmentationModelStatus) || model?.annotation_status || null;
  const localKey = isDetection ? 'detectionLocalModelPath' : 'segmentationLocalModelPath';
  const typeKey = isDetection ? 'detectionCustomModelType' : 'segmentationCustomModelType';
  const localPath = el('input', {
    placeholder: isDetection ? 'Optional custom YOLO/detector checkpoint path' : 'Optional custom SAM/SAM-HQ/SAM2/YOLO-seg checkpoint path',
    value: state[localKey] || '', style: 'min-width:450px', oninput: e => { state[localKey] = e.target.value; state[isDetection ? 'detectionClassInfo' : 'segmentationClassInfo'] = null; }
  });
  const types = isDetection ? ['yolo','grounding_dino','custom'] : ['auto','yolo','sam','sam_hq','sam2','custom'];
  const customType = el('select', { onchange: e => { state[typeKey] = e.target.value; state[isDetection ? 'detectionClassInfo' : 'segmentationClassInfo'] = null; } }, types.map(value => el('option', { value }, value)));
  customType.value = state[typeKey] || (isDetection ? 'yolo' : 'auto');
  const badges = model ? [
    el('span', { class: 'chip' }, model.provider || 'provider'),
    el('span', { class: 'chip' }, model.kind || task),
    el('span', { class: `chip ${model.downloaded ? 'cat-general' : 'cat-meta'}` }, model.download_supported ? (model.downloaded ? 'weights downloaded' : 'weights not downloaded') : 'local/API'),
    el('span', { class: `chip ${status?.available ? 'cat-general' : 'cat-invalid'}` }, status?.available ? 'runtime ready' : 'not loaded/ready'),
    model.vram_gb ? el('span', { class: 'chip' }, `~${model.vram_gb} GB VRAM`) : null
  ].filter(Boolean) : [];
  return card(`${isDetection ? 'Detection' : 'Segmentation'} Model: Download / Load / Status`, [
    el('p', { class: 'muted' }, isDetection
      ? 'Only bbox/detection models appear here. Segmentation and pose models are deliberately excluded.'
      : 'Only mask/segmentation models appear here. Detection-only and pose models are deliberately excluded.'),
    el('div', { class: 'chips open' }, badges),
    el('div', { class: 'row' }, [localPath, customType,
      el('button', { class: 'secondary', onclick: async () => { const chosen = await pickFilePath(localPath, `Select custom ${task} model`); if (chosen) state[localKey] = chosen; } }, 'Browse Custom Model...'),
      el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/reference/annotations/install-deps', { method: 'POST', body: { include_sam2: !isDetection && Boolean(state.segmentationInstallSam2) } }); toast(`Dependency install queued as job ${r.job_id}`); state.annotationLastJob = r.job_id; } catch (err) { toast(err.message, false); } } }, isDetection ? 'Install Detection Runtime' : 'Install Segmentation Runtime'),
      isSamFamily ? el('button', { class: 'primary', onclick: async () => { try {
        const r = await api('/api/reference/annotations/setup-model', { method: 'POST', body: { model_key: model.name, device: state.segmentationDevice || 'auto', force_download: false, parallel_downloads: modelDownloadWorkerCount(), options: { local_model_path: state.segmentationLocalModelPath || '', custom_model_type: customType.value } } });
        if (r.ok === false) throw new Error(r.error || 'SAM setup could not be queued.');
        state.annotationLastJob = r.job_id; toast(`SAM setup queued as job ${r.job_id}: runtime → weights → validation`); render();
      } catch (err) { toast(err.message, false); } } }, 'Set Up Runtime + Weights + Load') : null
    ]),
    isSamFamily ? el('p', { class: 'muted tiny' }, String(model.name || '').startsWith('sam2')
      ? 'SAM2.1 setup is most reliable in WSL/Linux on Windows because the official installation may compile an optional CUDA extension.'
      : 'The setup assistant installs only the selected SAM family, downloads its exact checkpoint, then validates the runtime/checkpoint pairing.') : null,
    !isDetection ? el('label', {}, [el('input', { type: 'checkbox', checked: Boolean(state.segmentationInstallSam2), onchange: e => { state.segmentationInstallSam2 = e.target.checked; } }), ' include SAM2 runtime']) : null,
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', disabled: !(model?.download_supported), onclick: async () => { try { const r = await api('/api/reference/annotations/download-model', { method: 'POST', body: { model_key: model.name, dry_run: true, parallel_downloads: modelDownloadWorkerCount() } }); state.annotationLastJob = r.job_id; toast(`Download check queued as job ${r.job_id}`); } catch (err) { toast(err.message, false); } } }, 'Dry-run Download'),
      el('button', { class: 'primary', disabled: !(model?.download_supported), onclick: async () => { try { const r = await api('/api/reference/annotations/download-model', { method: 'POST', body: { model_key: model.name, dry_run: false, parallel_downloads: modelDownloadWorkerCount() } }); state.annotationLastJob = r.job_id; toast(`Model download queued as job ${r.job_id}`); } catch (err) { toast(err.message, false); } } }, model?.downloaded ? 'Update / Re-download' : 'Download Weights'),
      el('button', { class: 'primary', disabled: !model, onclick: async () => { try {
        const options = { local_model_path: state[localKey] || '', custom_model_type: customType.value };
        const result = await api('/api/reference/annotations/load-model', { method: 'POST', body: { model_key: model.name, device: state[`${task}Device`] || 'auto', options } });
        if (isDetection) state.detectionModelStatus = result; else state.segmentationModelStatus = result;
        await refreshSpatialModelClasses(task, model.name).catch(() => null);
        toast(`${task} model loaded/validated`); render();
      } catch (err) { toast(err.message, false); } } }, 'Load / Validate'),
      el('button', { class: 'secondary', disabled: !model, onclick: async () => { try { const r = await api('/api/models/unload', { method: 'POST', body: { model_name: model.name } }); toast(r.job_id ? `Unload queued as job ${r.job_id}` : (r.message || 'No loaded model to unload.')); await refreshSpatialModelStatus(task, model.name); await refreshAll(); render(); } catch (err) { toast(err.message, false); } } }, 'Unload'),
      el('button', { class: 'secondary', disabled: !model, onclick: async () => { try { await refreshSpatialModelStatus(task, model.name); toast('Status refreshed'); render(); } catch (err) { toast(err.message, false); } } }, 'Refresh Status'),
      state.annotationLastJob ? el('button', { class: 'secondary', onclick: () => setTab('Jobs') }, `Open Job #${state.annotationLastJob}`) : null
    ].filter(Boolean)),
    el('pre', { class: 'log' }, JSON.stringify(status || model || {}, null, 2))
  ].filter(Boolean));
}

function _spatialBoxValues(bbox) {
  if (!bbox) return null;
  if (bbox.xyxy && bbox.xyxy.length >= 4) return bbox.xyxy.slice(0, 4).map(Number);
  if (bbox.x1 != null) return [Number(bbox.x1), Number(bbox.y1), Number(bbox.x2), Number(bbox.y2)];
  if (bbox.x != null) return [Number(bbox.x), Number(bbox.y), Number(bbox.x) + Number(bbox.w || 0), Number(bbox.y) + Number(bbox.h || 0)];
  return null;
}

function _drawSpatialBox(ctx, bbox, color, label = '', opacity = 1, selected = false) {
  const values = _spatialBoxValues(bbox); if (!values) return;
  const [x1,y1,x2,y2] = values;
  ctx.save(); ctx.globalAlpha = Math.max(0.05, Math.min(Number(opacity ?? 1), 1)); ctx.strokeStyle = color; ctx.lineWidth = Math.max(selected ? 4 : 2, ctx.canvas.width / (selected ? 400 : 600)); ctx.setLineDash(selected ? [10, 5] : []); ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
  if (label) { ctx.font = `${Math.max(13, Math.round(ctx.canvas.width / 90))}px sans-serif`; const width = ctx.measureText(label).width + 10; ctx.fillStyle = color; ctx.fillRect(x1, Math.max(0, y1 - 22), width, 22); ctx.fillStyle = '#fff'; ctx.fillText(label, x1 + 5, Math.max(15, y1 - 6)); }
  ctx.restore();
}

function _drawSpatialPolygon(ctx, points, color, label = '', opacity = 1, selected = false) {
  if (!points || !points.length) return;
  ctx.save(); ctx.globalAlpha = Math.max(0.05, Math.min(Number(opacity ?? 1), 1)); ctx.strokeStyle = color; ctx.fillStyle = `${color}55`; ctx.lineWidth = Math.max(selected ? 4 : 2, ctx.canvas.width / (selected ? 400 : 600)); ctx.setLineDash(selected ? [10, 5] : []); ctx.beginPath();
  points.forEach((point, index) => { const x = Number(point[0] ?? point.x ?? 0); const y = Number(point[1] ?? point.y ?? 0); if (!index) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
  if (points.length >= 3) ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = color; for (const point of points) { const x = Number(point[0] ?? point.x ?? 0); const y = Number(point[1] ?? point.y ?? 0); ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2); ctx.fill(); }
  if (label) { const p = points[0]; ctx.fillStyle = '#fff'; ctx.fillText(label, Number(p[0] ?? p.x ?? 0) + 6, Number(p[1] ?? p.y ?? 0) - 6); }
  ctx.restore();
}

function _drawSegmentationPromptPoints(ctx, points) {
  const radius = Math.max(8, ctx.canvas.width / 120);
  ctx.save();
  ctx.lineWidth = Math.max(2, ctx.canvas.width / 800);
  ctx.font = `bold ${Math.max(14, Math.round(radius * 1.35))}px sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  (points || []).forEach((point, index) => {
    const positive = Number(point.label ?? (point.positive === false ? 0 : 1)) > 0;
    const x = Number(point.x || 0), y = Number(point.y || 0);
    ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = positive ? 'rgba(34,197,94,.92)' : 'rgba(239,68,68,.92)';
    ctx.fill(); ctx.strokeStyle = '#ffffff'; ctx.stroke();
    ctx.fillStyle = '#ffffff'; ctx.fillText(positive ? '+' : '−', x, y + 1);
    ctx.fillStyle = '#ffffff'; ctx.strokeStyle = '#111827'; ctx.lineWidth = 3;
    const number = String(index + 1); ctx.strokeText(number, x + radius * 1.45, y - radius * 1.15); ctx.fillText(number, x + radius * 1.45, y - radius * 1.15);
  });
  ctx.restore();
}

function _hexToRgb(color) {
  const value = String(color || '#22c55e').replace('#','').trim();
  const normalized = value.length === 3 ? value.split('').map(x => x + x).join('') : value.padEnd(6, '0').slice(0,6);
  const number = Number.parseInt(normalized, 16);
  return Number.isFinite(number) ? [(number >> 16) & 255, (number >> 8) & 255, number & 255] : [34,197,94];
}

function _colorizedMaskCanvas(maskImage, width, height, color = '#22c55e', opacity = 0.55) {
  const off = document.createElement('canvas'); off.width = width; off.height = height;
  const octx = off.getContext('2d', { willReadFrequently: true }); if (!octx) return off;
  octx.drawImage(maskImage, 0, 0, width, height);
  try {
    const imageData = octx.getImageData(0, 0, width, height); const data = imageData.data; const [r,g,b] = _hexToRgb(color); const alpha = Math.round(Math.max(0, Math.min(Number(opacity ?? 0.55), 1)) * 255);
    for (let i = 0; i < data.length; i += 4) {
      const luminance = Math.max(data[i], data[i+1], data[i+2]);
      const sourceAlpha = data[i+3] / 255;
      data[i] = r; data[i+1] = g; data[i+2] = b; data[i+3] = Math.round((luminance / 255) * sourceAlpha * alpha);
    }
    octx.putImageData(imageData, 0, 0);
  } catch (_) { /* Same-origin mask route should permit pixels; fallback stays grayscale. */ }
  return off;
}

function spatialCanvas(item, task, annotations, proposals) {
  const wrap = el('div', { class: 'annotation-wrap' });
  const img = el('img', { class: 'annotation-image', src: `/api/media/${item.id}/file` });
  const canvas = el('canvas', { class: 'annotation-canvas' });
  wrap.append(img, canvas);
  let drawing = false; let start = null; let dragHandle = 'new'; let originalBox = null;
  const visibleAnnotations = (annotations || []).filter(row => row.visible !== false);
  const layerSelection = task === 'detection' ? state.detectionLayerSelection : state.segmentationLayerSelection;
  const maskRows = task === 'segmentation' ? [...visibleAnnotations, ...(proposals || [])].filter(row => row.mask_path) : [];
  const maskAssets = maskRows.map(row => { const image = new Image(); const asset = { row, image, tinted: null, width: 0, height: 0 }; image.onload = () => { asset.tinted = null; redraw(); }; const cacheKey = row.metadata?.run_id || row.id || row.mask_path; image.src = `/api/spatial/mask-preview?path=${encodeURIComponent(row.mask_path)}&v=${encodeURIComponent(cacheKey)}`; return asset; });
  function pos(event) { const rect = canvas.getBoundingClientRect(); return { x: (event.clientX - rect.left) * (canvas.width / Math.max(1, rect.width)), y: (event.clientY - rect.top) * (canvas.height / Math.max(1, rect.height)) }; }
  function redraw() {
    const ctx = canvas.getContext('2d'); if (!ctx) return; ctx.clearRect(0,0,canvas.width,canvas.height); ctx.font = `${Math.max(13, Math.round(canvas.width / 90))}px sans-serif`;
    if (task === 'segmentation') {
      for (const asset of maskAssets) {
        if (!asset.image.complete || !asset.image.naturalWidth) continue;
        const color = asset.row.color || (asset.row.id ? '#22c55e' : '#f97316'); const opacity = asset.row.opacity ?? (asset.row.id ? 0.55 : 0.45);
        if (!asset.tinted || asset.width !== canvas.width || asset.height !== canvas.height || asset.color !== color || asset.opacity !== opacity) { asset.tinted = _colorizedMaskCanvas(asset.image, canvas.width, canvas.height, color, opacity); asset.width = canvas.width; asset.height = canvas.height; asset.color = color; asset.opacity = opacity; }
        const blendMap = { normal:'source-over', add:'lighter', subtract:'destination-out' };
        ctx.save(); ctx.globalCompositeOperation = blendMap[asset.row.blend_mode] || asset.row.blend_mode || 'source-over'; ctx.drawImage(asset.tinted, 0, 0); ctx.restore();
      }
    }
    for (const row of visibleAnnotations) {
      const color = row.color || '#22c55e'; const opacity = row.opacity ?? 0.75; const selected = layerSelection?.has(Number(row.id));
      if (task === 'detection') _drawSpatialBox(ctx, row.bbox, color, `${row.layer_name || row.label || 'box'}${row.confidence != null ? ` ${(Number(row.confidence)*100).toFixed(0)}%` : ''}`, opacity, selected);
      else { if (row.polygon?.length) _drawSpatialPolygon(ctx, row.polygon, color, row.layer_name || row.label || 'mask', opacity, selected); if (row.bbox && Object.keys(row.bbox).length) _drawSpatialBox(ctx, row.bbox, color, row.layer_name || row.label || 'mask', opacity, selected); }
    }
    for (const row of proposals || []) {
      const text = `${row.label || 'proposal'}${row.confidence != null ? ` ${(Number(row.confidence)*100).toFixed(1)}%` : ''}`;
      if (row.polygon?.length) _drawSpatialPolygon(ctx, row.polygon, '#f97316', text);
      if (row.bbox && Object.keys(row.bbox).length) _drawSpatialBox(ctx, row.bbox, '#f97316', text);
    }
    if (task === 'detection' && state.detectionDraftBbox) {
      _drawSpatialBox(ctx, state.detectionDraftBbox, '#ef4444', state.detectionEditingLayerId ? `editing layer #${state.detectionEditingLayerId}` : 'manual draft', 1, true);
      const values = _spatialBoxValues(state.detectionDraftBbox); if (values) { ctx.save(); ctx.fillStyle='#fff'; ctx.strokeStyle='#ef4444'; ctx.lineWidth=2; for (const [hx,hy] of [[values[0],values[1]],[values[2],values[1]],[values[0],values[3]],[values[2],values[3]]]) { ctx.fillRect(hx-6,hy-6,12,12); ctx.strokeRect(hx-6,hy-6,12,12); } ctx.restore(); }
    }
    if (task === 'segmentation') {
      if ((state.segmentationPolygon || []).length) _drawSpatialPolygon(ctx, state.segmentationPolygon, '#ef4444', 'manual mask draft');
      if (state.segmentationPromptBbox) _drawSpatialBox(ctx, state.segmentationPromptBbox, '#38bdf8', 'model bbox prompt');
      _drawSegmentationPromptPoints(ctx, state.segmentationPromptPoints || []);
    }
  }
  function resize() { const rect = img.getBoundingClientRect(); canvas.width = img.naturalWidth || item.width || rect.width || 1; canvas.height = img.naturalHeight || item.height || rect.height || 1; redraw(); }
  canvas.addEventListener('pointerdown', event => {
    const point = pos(event);
    if (task === 'detection') {
      drawing = true; start = point; dragHandle = 'new'; originalBox = state.detectionDraftBbox ? { ...state.detectionDraftBbox } : null;
      const values = _spatialBoxValues(state.detectionDraftBbox); const hit = Math.max(10, canvas.width / 80);
      if (values && state.detectionEditingLayerId) {
        const handles = [['nw',values[0],values[1]],['ne',values[2],values[1]],['sw',values[0],values[3]],['se',values[2],values[3]]];
        const found = handles.find(([,x,y]) => Math.hypot(point.x-x,point.y-y) <= hit);
        if (found) dragHandle = found[0];
        else if (point.x >= values[0] && point.x <= values[2] && point.y >= values[1] && point.y <= values[3]) dragHandle = 'move';
      }
      if (dragHandle === 'new') state.detectionDraftBbox = { x1: point.x, y1: point.y, x2: point.x, y2: point.y };
    } else if (state.segmentationDrawMode === 'bbox_prompt') { drawing = true; start = point; dragHandle='new'; state.segmentationPromptBbox = { x1: point.x, y1: point.y, x2: point.x, y2: point.y }; }
    else if (state.segmentationDrawMode === 'positive_point' || state.segmentationDrawMode === 'negative_point') {
      state.segmentationPromptPoints = [...(state.segmentationPromptPoints || []), { x: point.x, y: point.y, label: state.segmentationDrawMode === 'positive_point' ? 1 : 0 }];
    } else if (state.segmentationDrawMode === 'remove_point') {
      const points = state.segmentationPromptPoints || []; const hit = Math.max(14, canvas.width / 80);
      let nearest = -1, distance = Infinity;
      points.forEach((candidate, index) => { const d = Math.hypot(Number(candidate.x)-point.x, Number(candidate.y)-point.y); if (d < distance) { nearest = index; distance = d; } });
      if (nearest >= 0 && distance <= hit) state.segmentationPromptPoints = points.filter((_, index) => index !== nearest);
    } else { state.segmentationPolygon = [...(state.segmentationPolygon || []), [point.x, point.y]]; }
    redraw();
  });
  canvas.addEventListener('pointermove', event => {
    if (!drawing || !start) return; const point = pos(event);
    if (task === 'detection' && originalBox && dragHandle !== 'new') {
      const values = _spatialBoxValues(originalBox); if (!values) return; let [x1,y1,x2,y2]=values;
      if (dragHandle === 'move') { const dx=point.x-start.x, dy=point.y-start.y; x1+=dx; x2+=dx; y1+=dy; y2+=dy; }
      else { if (dragHandle.includes('w')) x1=point.x; if (dragHandle.includes('e')) x2=point.x; if (dragHandle.includes('n')) y1=point.y; if (dragHandle.includes('s')) y2=point.y; }
      state.detectionDraftBbox={x1:Math.min(x1,x2),y1:Math.min(y1,y2),x2:Math.max(x1,x2),y2:Math.max(y1,y2)};
    } else {
      const box = { x1: Math.min(start.x, point.x), y1: Math.min(start.y, point.y), x2: Math.max(start.x, point.x), y2: Math.max(start.y, point.y) };
      if (task === 'detection') state.detectionDraftBbox = box; else state.segmentationPromptBbox = box;
    }
    redraw();
  });
  window.addEventListener('pointerup', () => { drawing = false; start = null; originalBox=null; dragHandle='new'; });
  canvas.addEventListener('dblclick', event => { if (task === 'segmentation' && state.segmentationDrawMode === 'polygon') { event.preventDefault(); toast(`${(state.segmentationPolygon || []).length} mask polygon point(s) captured.`); } });
  img.addEventListener('load', resize); setTimeout(resize, 0); window.addEventListener('resize', resize, { once: true });
  return wrap;
}

function spatialProposalSummary(task, output) {
  const rows = output?.proposals || [];
  if (!output) return el('p', { class: 'muted' }, `No ${task} preview has run for this image.`);
  if (output.ok === false) return el('pre', { class: 'log bad' }, JSON.stringify(output, null, 2));
  const selected = spatialPreviewSelection(task);
  for (const index of [...selected]) if (index < 0 || index >= rows.length) selected.delete(index);
  return el('div', { class: 'grid' }, [
    el('div', { class: 'row' }, [
      el('span', { class: 'badge ok' }, `${rows.length} real model proposal(s)`),
      el('span', { class: 'badge' }, `${selected.size} selected`),
      el('button', { class: 'secondary small', onclick: () => { rows.forEach((_, index) => selected.add(index)); render(); } }, 'Select All Preview Layers'),
      el('button', { class: 'secondary small', onclick: () => { selected.clear(); render(); } }, 'Clear Preview Selection'),
      el('span', { class: 'muted tiny' }, 'Orange overlays are unsaved previews; persisted layers join the editable stack.')
    ]),
    output.conditioning ? el('div', { class: 'model-card' }, [
      el('strong', {}, `Conditioning: ${output.conditioning.mode || 'unknown'}`),
      el('div', { class: 'muted tiny' }, `Class/token: ${output.conditioning.class_query || '<all / none>'} · affects geometry: ${output.conditioning.prompt_affects_geometry === true ? 'yes' : output.conditioning.prompt_affects_geometry === false ? 'no' : 'unknown'}`),
      output.conditioning.guide_model_key ? el('div', { class: 'muted tiny' }, `Guide detector: ${output.conditioning.guide_model_key} · ${output.conditioning.guide_box_count || 0} bbox prompt(s)`) : null
    ].filter(Boolean)) : null,
    ...(output.warnings || []).map(message => el('div', { class: 'badge bad' }, message)),
    output.diagnostics ? el('div', { class: 'muted tiny' }, `Confidence range: ${output.diagnostics.confidence_min == null ? 'n/a' : Number(output.diagnostics.confidence_min).toFixed(4)} – ${output.diagnostics.confidence_max == null ? 'n/a' : Number(output.diagnostics.confidence_max).toFixed(4)} · labels: ${(output.diagnostics.class_labels || []).join(', ') || 'none'}`) : null,
    ...rows.map((row, index) => el('div', { class: `model-card preview-layer-card ${selected.has(index) ? 'selected' : ''}` }, [
      el('label', { class: 'row' }, [
        el('input', { type: 'checkbox', checked: selected.has(index), onchange: e => { if (e.target.checked) selected.add(index); else selected.delete(index); render(); } }),
        el('strong', {}, `${index + 1}. ${row.label || task}`)
      ]),
      el('div', { class: 'muted tiny' }, `${row.model_key || ''} · ${row.annotation_type || task} · ${row.confidence == null ? 'no confidence' : `${(Number(row.confidence)*100).toFixed(2)}%`}`),
      row.mask_path ? el('div', { class: 'path tiny' }, row.mask_path) : null,
      row.mask_path ? el('img', { class: 'mask-mini-preview', src: `/api/spatial/mask-preview?path=${encodeURIComponent(row.mask_path)}&v=${encodeURIComponent(row.metadata?.run_id || row.mask_path)}` }) : null
    ].filter(Boolean)))
  ]);
}

function spatialAnnotationTable(rows, task) {
  if (!rows?.length) return el('p', { class: 'muted' }, `No saved ${task} annotations for this image.`);
  return el('div', { class: 'table-scroll' }, el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['ID','Label','Type','Source / Model','Confidence','Geometry / Mask','Actions'].map(h => el('th', {}, h)))),
    el('tbody', {}, rows.map(row => el('tr', {}, [
      el('td', {}, row.id), el('td', {}, row.label || ''), el('td', {}, row.annotation_type || ''),
      el('td', { class: 'tiny' }, `${row.source || ''}${row.model_key ? ` / ${row.model_key}` : ''}`),
      el('td', {}, row.confidence == null ? '' : Number(row.confidence).toFixed(3)),
      el('td', { class: 'tiny path' }, task === 'detection' ? JSON.stringify(row.bbox || {}) : (row.mask_path || `${(row.polygon || []).length} polygon points`)),
      el('td', {}, el('div', { class: 'row' }, [
        task === 'detection' ? el('button', { class: 'secondary small', onclick: () => { state.segmentationPromptBbox = row.bbox || null; state.activeMedia = state.activeMedia || (state.annotationState?.media || null); toast('BBox copied into the segmentation prompt.'); setTab('Segmentation & Masks'); } }, 'Use as Mask Prompt') : null,
        el('button', { class: 'secondary small', onclick: () => { if (task === 'detection') state.detectionDraftBbox = row.bbox || null; else { state.segmentationPolygon = row.polygon || []; state.segmentationPromptBbox = row.bbox || null; } toast('Loaded into the manual draft editor'); render(); } }, 'Load Draft'),
        el('button', { class: 'danger small', onclick: async () => { try { await api(`/api/reference/annotations/${row.id}`, { method: 'DELETE' }); await loadAnnotationState(row.media_id); toast('Annotation deleted'); render(); } catch (err) { toast(err.message, false); } } }, 'Delete')
      ].filter(Boolean)))
    ])))
  ]));
}

function spatialLayerSelection(task) {
  return task === 'detection' ? state.detectionLayerSelection : state.segmentationLayerSelection;
}

async function patchSpatialLayer(task, item, row, changes, message = 'Layer updated') {
  try {
    await api(`/api/spatial/layers/${row.id}`, { method: 'PATCH', body: changes });
    await loadAnnotationState(item.id); toast(message); render();
  } catch (err) { toast(err.message, false); }
}

async function deleteSpatialLayer(task, item, row) {
  if (!window.confirm(`Delete layer “${row.layer_name || row.label || row.id}”?`)) return;
  try {
    await api(`/api/reference/annotations/${row.id}`, { method: 'DELETE' });
    spatialLayerSelection(task).delete(Number(row.id));
    if (task === 'detection' && Number(state.detectionEditingLayerId) === Number(row.id)) state.detectionEditingLayerId = null;
    if (task === 'segmentation' && Number(state.segmentationEditingLayerId) === Number(row.id)) state.segmentationEditingLayerId = null;
    await loadAnnotationState(item.id); toast('Layer deleted'); render();
  } catch (err) { toast(err.message, false); }
}

async function reorderSpatialLayers(task, item, displayRows) {
  try {
    // The editor displays top-most first; the backend stores bottom-to-top draw order.
    const annotationIds = [...displayRows].reverse().map(row => Number(row.id));
    await api('/api/spatial/layers/reorder', { method: 'POST', body: { media_id: item.id, annotation_ids: annotationIds, task } });
    await loadAnnotationState(item.id); render();
  } catch (err) { toast(err.message, false); }
}

async function restoreLatestSpatialRevision(task, item, row) {
  try {
    const revisions = await api(`/api/spatial/layers/${row.id}/revisions?limit=1`);
    if (!revisions?.length) return toast('This layer has no saved revision to restore.', false);
    await api(`/api/spatial/layers/${row.id}/revisions/${revisions[0].id}/restore`, { method: 'POST' });
    await loadAnnotationState(item.id); toast(`Restored previous saved state for layer #${row.id}`); render();
  } catch (err) { toast(err.message, false); }
}

function spatialLayerStack(task, item, rows) {
  const selected = spatialLayerSelection(task);
  const ids = new Set((rows || []).map(row => Number(row.id)));
  for (const id of [...selected]) if (!ids.has(Number(id))) selected.delete(id);
  const displayRows = [...(rows || [])].sort((a,b) => Number(b.layer_order || b.id) - Number(a.layer_order || a.id));
  let draggedId = null;
  const stack = el('div', { class: 'layer-stack' }, displayRows.map((row, index) => {
    const selectedBox = el('input', { type: 'checkbox', checked: selected.has(Number(row.id)), onchange: e => { if (e.target.checked) selected.add(Number(row.id)); else selected.delete(Number(row.id)); render(); } });
    const nameInput = el('input', { class: 'layer-name-input', value: row.layer_name || row.label || `Layer ${row.id}`, onchange: e => patchSpatialLayer(task, item, row, { layer_name: e.target.value }, 'Layer renamed') });
    const opacity = el('input', { type: 'range', min: '0.05', max: '1', step: '0.05', value: row.opacity ?? 0.55, title: `Opacity ${Math.round(Number(row.opacity ?? 0.55)*100)}%`, onchange: e => patchSpatialLayer(task, item, row, { opacity: Number(e.target.value) }, 'Layer opacity saved') });
    const color = el('input', { type: 'color', value: row.color || (task === 'detection' ? '#22c55e' : '#22c55e'), title: 'Overlay color', onchange: e => patchSpatialLayer(task, item, row, { color: e.target.value }, 'Layer color saved') });
    const blend = el('select', { title: 'Overlay blend mode', onchange: e => patchSpatialLayer(task, item, row, { blend_mode: e.target.value }, 'Blend mode saved') }, ['normal','multiply','screen','overlay','difference'].map(value => el('option', { value }, value))); blend.value = row.blend_mode || 'normal';
    const layer = el('div', {
      class: `layer-row ${selected.has(Number(row.id)) ? 'selected' : ''} ${row.visible === false ? 'hidden-layer' : ''}`,
      draggable: 'true',
      ondragstart: e => { draggedId = Number(row.id); e.dataTransfer?.setData('text/plain', String(row.id)); e.dataTransfer.effectAllowed = 'move'; },
      ondragover: e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; },
      ondrop: e => {
        e.preventDefault(); const sourceId = draggedId || Number(e.dataTransfer?.getData('text/plain')); if (!sourceId || sourceId === Number(row.id)) return;
        const reordered = [...displayRows]; const sourceIndex = reordered.findIndex(value => Number(value.id) === sourceId); const targetIndex = reordered.findIndex(value => Number(value.id) === Number(row.id));
        if (sourceIndex < 0 || targetIndex < 0) return; const [moved] = reordered.splice(sourceIndex, 1); reordered.splice(targetIndex, 0, moved); reorderSpatialLayers(task, item, reordered);
      }
    }, [
      el('div', { class: 'layer-main' }, [
        el('span', { class: 'layer-drag', title: 'Drag to reorder' }, '☰'), selectedBox,
        el('button', { class: 'icon-button', title: row.visible === false ? 'Show layer' : 'Hide layer', onclick: () => patchSpatialLayer(task, item, row, { visible: row.visible === false }, row.visible === false ? 'Layer shown' : 'Layer hidden') }, row.visible === false ? '◌' : '◉'),
        el('button', { class: 'icon-button', title: row.locked ? 'Unlock layer' : 'Lock layer', onclick: () => patchSpatialLayer(task, item, row, { locked: !row.locked }, row.locked ? 'Layer unlocked' : 'Layer locked') }, row.locked ? '🔒' : '🔓'),
        color, nameInput,
        el('span', { class: 'badge tiny' }, `${row.source || 'user'}${row.model_key ? ` · ${row.model_key}` : ''}`),
        row.confidence == null ? null : el('span', { class: 'badge tiny' }, `${(Number(row.confidence)*100).toFixed(2)}%`)
      ].filter(Boolean)),
      el('div', { class: 'layer-controls' }, [
        el('label', { class: 'tiny' }, ['opacity ', opacity]), blend,
        el('button', { class: 'secondary small', disabled: index === 0, onclick: () => { const reordered = [...displayRows]; [reordered[index-1], reordered[index]] = [reordered[index], reordered[index-1]]; reorderSpatialLayers(task, item, reordered); } }, 'Move Up'),
        el('button', { class: 'secondary small', disabled: index === displayRows.length-1, onclick: () => { const reordered = [...displayRows]; [reordered[index+1], reordered[index]] = [reordered[index], reordered[index+1]]; reorderSpatialLayers(task, item, reordered); } }, 'Move Down'),
        el('button', { class: 'secondary small', onclick: () => {
          if (task === 'detection') { state.detectionEditingLayerId = Number(row.id); state.detectionDraftBbox = row.bbox || null; }
          else { state.segmentationEditingLayerId = Number(row.id); state.segmentationLayerColor = row.color || '#22c55e'; state.segmentationLayerOpacity = row.opacity ?? 0.55; }
          toast(`Editing layer #${row.id}`); render();
        } }, 'Edit'),
        el('button', { class: 'secondary small', onclick: async () => { try { await api(`/api/spatial/layers/${row.id}/duplicate`, { method: 'POST', body: { layer_name: `${row.layer_name || row.label || 'layer'} copy` } }); await loadAnnotationState(item.id); toast('Layer duplicated'); render(); } catch (err) { toast(err.message, false); } } }, 'Duplicate'),
        el('button', { class: 'secondary small', title: 'Restore the state before the latest saved edit', onclick: () => restoreLatestSpatialRevision(task, item, row) }, 'Undo Saved Edit'),
        el('button', { class: 'danger small', onclick: () => deleteSpatialLayer(task, item, row) }, 'Delete')
      ])
    ]);
    return layer;
  }));
  return el('div', { class: 'grid' }, [
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: () => { for (const row of rows || []) selected.add(Number(row.id)); render(); } }, 'Select All Layers'),
      el('button', { class: 'secondary', onclick: () => { selected.clear(); render(); } }, 'Clear Layer Selection'),
      el('span', { class: 'muted tiny' }, `${selected.size} selected · drag layers or use Move Up/Down; top rows render above lower rows`)
    ]),
    stack
  ]);
}

async function persistSpatialPreview(task, item, proposals, label = '') {
  if (!proposals?.length) return toast('There is no generated preview to persist.', false);
  const selection = spatialPreviewSelection(task);
  const chosen = proposals.filter((_, index) => selection.has(index));
  if (!chosen.length) return toast('Select one or more generated preview layers first.', false);
  try {
    const result = await api(`/api/spatial/${task}/persist-preview`, { method: 'POST', body: { media_id: item.id, proposals: chosen, label } });
    const layerSelection = spatialLayerSelection(task); layerSelection.clear();
    for (const row of result.saved || []) { const id = Number(row.id || row.annotation_id); if (id) layerSelection.add(id); }
    const previewMaskPaths = (proposals || []).map(row => row.mask_path).filter(Boolean);
    if (previewMaskPaths.length) await api(`/api/spatial/${task}/clear-preview`, { method:'POST', body:{ mask_paths:previewMaskPaths } }).catch(()=>null);
    if (task === 'detection') state.detectionOutput = null; else state.segmentationOutput = null;
    selection.clear();
    await loadAnnotationState(item.id); toast(`Persisted ${result.count || 0} selected preview layer(s)`); render();
  } catch (err) { toast(err.message, false); }
}

async function mergeSelectedSpatialLayers(task, item, operation, label, deleteSources = false, baseAnnotationId = null, proposals = []) {
  const layerSelection = spatialLayerSelection(task);
  const ids = [...layerSelection].map(Number);
  const previewSelection = spatialPreviewSelection(task);
  const chosenPreviews = (proposals || []).filter((_, index) => previewSelection.has(index));
  try {
    // Unsaved model proposals are promoted to ordinary persistent layers first,
    // so users can combine model/model, model/user, or model/composite results in
    // one operation without losing the individual source layers.
    if (chosenPreviews.length) {
      const persisted = await api(`/api/spatial/${task}/persist-preview`, { method:'POST', body:{ media_id:item.id, proposals:chosenPreviews, label:'' } });
      for (const row of persisted.saved || []) { const id=Number(row.id || row.annotation_id); if (id) { ids.push(id); layerSelection.add(id); } }
      const previewMaskPaths = (proposals || []).map(row => row.mask_path).filter(Boolean);
      if (previewMaskPaths.length) await api(`/api/spatial/${task}/clear-preview`, { method:'POST', body:{ mask_paths:previewMaskPaths } }).catch(()=>null);
      previewSelection.clear();
      if (task === 'detection') state.detectionOutput = null; else state.segmentationOutput = null;
    }
    if (ids.length < 2) throw new Error(`Select at least two saved or preview ${task === 'detection' ? 'box' : 'mask'} layers to combine.`);
    let effectiveBase = baseAnnotationId || null;
    if (task === 'segmentation' && operation === 'subtract' && effectiveBase && !ids.includes(Number(effectiveBase))) effectiveBase = ids[0] || null;
    const result = await api(`/api/spatial/${task}/layers/merge`, { method: 'POST', body: { media_id: item.id, annotation_ids: ids, operation, label, layer_name: `${label || 'combined'} (${operation})`, delete_sources: deleteSources, base_annotation_id: effectiveBase, threshold: Number(state.segmentationMergeThreshold ?? 1), feather: Number(state.segmentationMergeFeather ?? 0), grow: Number(state.segmentationMergeGrow ?? 0) } });
    layerSelection.clear(); const newId = Number(result.annotation?.id || result.annotation?.annotation_id); if (newId) layerSelection.add(newId);
    await loadAnnotationState(item.id); toast(`Created composite ${task} layer #${newId || ''}`); render();
  } catch (err) { toast(err.message, false); }
}

async function deleteSelectedSpatialLayers(task, item) {
  const selection = spatialLayerSelection(task); const ids = [...selection].map(Number);
  if (!ids.length) return toast('Select one or more saved layers first.', false);
  if (!window.confirm(`Delete ${ids.length} selected ${task} layer(s)?`)) return;
  try {
    const result = await api('/api/spatial/layers/delete', { method: 'POST', body: { annotation_ids: ids } });
    selection.clear();
    if (task === 'detection') state.detectionEditingLayerId = null; else state.segmentationEditingLayerId = null;
    await loadAnnotationState(item.id); toast(`Deleted ${result.deleted || 0} layer(s)`); render();
  } catch (err) { toast(err.message, false); }
}

function spatialLayerCompositor(task, item, rows, proposals) {
  const isDetection = task === 'detection';
  const operationValues = isDetection ? ['union','intersection','average','confidence_weighted'] : ['union','intersection','subtract','xor'];
  const key = isDetection ? 'detectionMergeOperation' : 'segmentationMergeOperation';
  const operation = el('select', { onchange: e => { state[key] = e.target.value; render(); } }, operationValues.map(value => el('option', { value }, value.replaceAll('_',' ')))); operation.value = state[key] || 'union';
  const label = el('input', { value: isDetection ? (state.detectionMergeLabel || 'combined_box') : (state.segmentationMergeLabel || 'combined_mask'), placeholder: 'new composite layer label', oninput: e => { if (isDetection) state.detectionMergeLabel = e.target.value; else state.segmentationMergeLabel = e.target.value; } });
  const deleteSources = el('input', { type: 'checkbox' });
  const selectedIds = [...spatialLayerSelection(task)].map(Number);
  const selectedRows = (rows || []).filter(row => selectedIds.includes(Number(row.id)));
  const baseSelect = isDetection ? null : el('select', { onchange:e=>{state.segmentationMergeBaseId=Number(e.target.value)||null;} }, [
    el('option', { value:'' }, 'Subtract base: first selected layer'),
    ...selectedRows.map(row=>el('option',{value:row.id},`Base #${row.id}: ${row.layer_name || row.label || 'mask'}`))
  ]);
  if (baseSelect) baseSelect.value = selectedIds.includes(Number(state.segmentationMergeBaseId)) ? String(state.segmentationMergeBaseId) : '';
  const maskControls = isDetection ? null : el('div', { class: 'row' }, [
    el('label', {}, ['mask threshold ', el('input', { type:'number', min:'0', max:'255', value: state.segmentationMergeThreshold ?? 1, style:'width:80px', oninput:e=>{state.segmentationMergeThreshold=Number(e.target.value);} })]),
    el('label', {}, ['feather px ', el('input', { type:'number', min:'0', max:'128', value: state.segmentationMergeFeather ?? 0, style:'width:80px', oninput:e=>{state.segmentationMergeFeather=Number(e.target.value);} })]),
    el('label', {}, ['grow/shrink px ', el('input', { type:'number', min:'-128', max:'128', value: state.segmentationMergeGrow ?? 0, style:'width:90px', oninput:e=>{state.segmentationMergeGrow=Number(e.target.value);} })]),
    operation.value === 'subtract' ? baseSelect : null
  ].filter(Boolean));
  return card(isDetection ? 'Box Layer Stack & Compositor' : 'Mask Layer Stack & Compositor', [
    el('p', { class: 'muted' }, isDetection
      ? 'Persist model/user/composite boxes as independent editable layers. Select saved layers and/or unsaved model preview layers, then create an enclosing union, common intersection, coordinate average, or confidence-weighted box. Selected previews are persisted automatically; source layers are kept by default.'
      : 'Persist model/user/Krita/composite masks as independent editable layers. Select saved layers and/or unsaved model preview layers. Union, intersection, subtract (chosen base minus the rest), and XOR create a new editable layer while preserving the source layers by default. Selected previews are persisted automatically.'),
    spatialLayerStack(task, item, rows), maskControls,
    el('div', { class: 'row' }, [operation, label, el('label', {}, [deleteSources, ' delete source layers after merge']),
      el('button', { class: 'primary', onclick: () => mergeSelectedSpatialLayers(task, item, operation.value, label.value, deleteSources.checked, baseSelect ? Number(baseSelect.value)||null : null, proposals) }, `Combine Selected ${isDetection ? 'Boxes' : 'Masks'}`),
      el('button', { class: 'secondary', disabled: !proposals?.length, onclick: () => persistSpatialPreview(task, item, proposals, label.value) }, 'Persist Selected Preview Layers'),
      el('button', { class: 'danger', onclick: () => deleteSelectedSpatialLayers(task, item) }, 'Delete Selected Saved Layers')
    ])
  ].filter(Boolean));
}

function maskPaintEditor(item, row = null) {
  const wrap = el('div', { class: 'mask-paint-wrap' });
  const canvas = el('canvas', { class: 'mask-paint-canvas' });
  const status = el('div', { class: 'muted tiny' }, row ? `Loading layer #${row.id}...` : 'Loading blank mask canvas...');
  wrap.append(canvas, status);
  const image = new Image();
  const maskCanvas = document.createElement('canvas');
  const maskCtx = maskCanvas.getContext('2d', { willReadFrequently: true });
  let readyResolve; const ready = new Promise(resolve => { readyResolve = resolve; });
  let drawing = false; let start = null; let last = null; let lasso = []; let previewEnd = null;
  const undoStack = []; const redoStack = []; const maxHistory = 24;
  function point(event) { const rect = canvas.getBoundingClientRect(); return { x: Math.max(0, Math.min(canvas.width, (event.clientX - rect.left) * canvas.width / Math.max(1, rect.width))), y: Math.max(0, Math.min(canvas.height, (event.clientY - rect.top) * canvas.height / Math.max(1, rect.height))) }; }
  function snapshot() { if (!maskCanvas.width || !maskCanvas.height) return; try { undoStack.push(maskCtx.getImageData(0,0,maskCanvas.width,maskCanvas.height)); if (undoStack.length > maxHistory) undoStack.shift(); redoStack.length = 0; } catch (_) {} }
  function restore(data) { if (!data) return; maskCtx.clearRect(0,0,maskCanvas.width,maskCanvas.height); maskCtx.putImageData(data,0,0); redraw(); }
  function stampBrush(p, erase = false) {
    const radius = Math.max(0.5, Number(state.segmentationBrushSize || 32) / 2);
    const opacity = Math.max(0.01, Math.min(1, Number(state.segmentationBrushOpacity ?? 1)));
    const hardness = Math.max(0, Math.min(1, Number(state.segmentationBrushHardness ?? 0.9)));
    maskCtx.save(); maskCtx.globalCompositeOperation = erase ? 'destination-out' : 'source-over';
    const gradient = maskCtx.createRadialGradient(p.x,p.y,Math.max(0,radius*hardness),p.x,p.y,radius);
    const solid = `rgba(255,255,255,${opacity})`; gradient.addColorStop(0,solid); gradient.addColorStop(Math.max(0.001,hardness),solid); gradient.addColorStop(1,'rgba(255,255,255,0)');
    maskCtx.fillStyle=gradient; maskCtx.beginPath(); maskCtx.arc(p.x,p.y,radius,0,Math.PI*2); maskCtx.fill(); maskCtx.restore();
  }
  function drawMaskStroke(a, b, erase = false) {
    const distance=Math.hypot(b.x-a.x,b.y-a.y); const spacing=Math.max(1,Number(state.segmentationBrushSize||32)*0.18); const steps=Math.max(1,Math.ceil(distance/spacing));
    for(let i=0;i<=steps;i++){const t=i/steps;stampBrush({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t},erase);}
  }
  function commitShape(tool, a, b, points = []) {
    if (state.segmentationShapeMode === 'replace') maskCtx.clearRect(0,0,maskCanvas.width,maskCanvas.height);
    maskCtx.save(); maskCtx.globalCompositeOperation = state.segmentationShapeMode === 'subtract' ? 'destination-out' : 'source-over'; maskCtx.fillStyle = `rgba(255,255,255,${Math.max(.01,Math.min(1,Number(state.segmentationBrushOpacity??1)))})`; maskCtx.strokeStyle = '#fff';
    if (tool === 'rectangle') maskCtx.fillRect(Math.min(a.x,b.x), Math.min(a.y,b.y), Math.abs(b.x-a.x), Math.abs(b.y-a.y));
    else if (tool === 'ellipse') { maskCtx.beginPath(); maskCtx.ellipse((a.x+b.x)/2,(a.y+b.y)/2,Math.abs(b.x-a.x)/2,Math.abs(b.y-a.y)/2,0,0,Math.PI*2); maskCtx.fill(); }
    else if (tool === 'lasso' && points.length >= 3) { maskCtx.beginPath(); maskCtx.moveTo(points[0].x,points[0].y); points.slice(1).forEach(p => maskCtx.lineTo(p.x,p.y)); maskCtx.closePath(); maskCtx.fill(); }
    maskCtx.restore();
  }
  function redraw() {
    const ctx = canvas.getContext('2d'); if (!ctx || !canvas.width) return;
    ctx.clearRect(0,0,canvas.width,canvas.height); ctx.drawImage(image,0,0,canvas.width,canvas.height);
    const tinted = _colorizedMaskCanvas(maskCanvas, canvas.width, canvas.height, state.segmentationLayerColor || row?.color || '#22c55e', state.segmentationLayerOpacity ?? row?.opacity ?? 0.55); ctx.drawImage(tinted,0,0);
    ctx.save(); ctx.strokeStyle = '#f97316'; ctx.lineWidth = Math.max(2,canvas.width/700); ctx.setLineDash([8,5]);
    const tool = state.segmentationEditTool || 'brush';
    if (drawing && start && previewEnd && ['rectangle','ellipse'].includes(tool)) { if (tool === 'rectangle') ctx.strokeRect(Math.min(start.x,previewEnd.x),Math.min(start.y,previewEnd.y),Math.abs(previewEnd.x-start.x),Math.abs(previewEnd.y-start.y)); else { ctx.beginPath(); ctx.ellipse((start.x+previewEnd.x)/2,(start.y+previewEnd.y)/2,Math.abs(previewEnd.x-start.x)/2,Math.abs(previewEnd.y-start.y)/2,0,0,Math.PI*2); ctx.stroke(); } }
    if (drawing && tool === 'lasso' && lasso.length) { ctx.beginPath(); ctx.moveTo(lasso[0].x,lasso[0].y); lasso.slice(1).forEach(p => ctx.lineTo(p.x,p.y)); ctx.stroke(); }
    ctx.restore();
  }
  function imageAsAlphaMask(maskImage) {
    const off=document.createElement('canvas'); off.width=maskCanvas.width; off.height=maskCanvas.height; const octx=off.getContext('2d',{willReadFrequently:true});
    octx.drawImage(maskImage,0,0,off.width,off.height); const data=octx.getImageData(0,0,off.width,off.height); const pixels=data.data;
    for(let i=0;i<pixels.length;i+=4){const existingAlpha=pixels[i+3];const luminance=Math.max(pixels[i],pixels[i+1],pixels[i+2]);const alpha=existingAlpha<255?existingAlpha:luminance;pixels[i]=pixels[i+1]=pixels[i+2]=255;pixels[i+3]=alpha;}
    octx.putImageData(data,0,0); return off;
  }
  async function loadMaskPath(path, mode = 'replace') {
    if (!path) return;
    const maskImage = new Image();
    await new Promise((resolve,reject) => { maskImage.onload=resolve; maskImage.onerror=()=>reject(new Error('Could not load mask layer image.')); maskImage.src=`/api/spatial/mask-preview?path=${encodeURIComponent(path)}&v=${Date.now()}`; });
    const incoming=imageAsAlphaMask(maskImage);
    if (mode === 'replace') { maskCtx.clearRect(0,0,maskCanvas.width,maskCanvas.height); maskCtx.drawImage(incoming,0,0); redraw(); return; }
    if (mode === 'intersection') { const current=document.createElement('canvas');current.width=maskCanvas.width;current.height=maskCanvas.height;current.getContext('2d').drawImage(maskCanvas,0,0);maskCtx.clearRect(0,0,maskCanvas.width,maskCanvas.height);maskCtx.drawImage(current,0,0);maskCtx.save();maskCtx.globalCompositeOperation='destination-in';maskCtx.drawImage(incoming,0,0);maskCtx.restore();redraw();return; }
    maskCtx.save(); maskCtx.globalCompositeOperation = mode === 'subtract' ? 'destination-out' : mode === 'xor' ? 'xor' : 'source-over'; maskCtx.drawImage(incoming,0,0); maskCtx.restore(); redraw();
  }
  async function magicSelect(p) {
    try {
      status.textContent = 'Running Magic Select...'; snapshot();
      const result = await api('/api/spatial/segmentation/magic-select', { method:'POST', body:{ media_id:item.id, x:p.x, y:p.y, method:state.segmentationMagicMethod || 'flood_fill', tolerance:Number(state.segmentationMagicTolerance ?? 24), connectivity:8, bbox:state.segmentationPromptBbox || {}, iterations:Number(state.segmentationMagicIterations ?? 5), radius_ratio:Number(state.segmentationMagicRadius ?? 0.22), feather:Number(state.segmentationMagicFeather ?? 0), grow:Number(state.segmentationMagicGrow ?? 0), invert:Boolean(state.segmentationMagicInvert) } });
      await loadMaskPath(result.mask_path, state.segmentationMagicMode || 'add'); status.textContent = `Magic Select: ${Number(result.pixel_count||0).toLocaleString()} pixels (${state.segmentationMagicMode || 'add'}).`;
      await api('/api/spatial/segmentation/clear-preview', { method:'POST', body:{ mask_paths:[result.mask_path] } }).catch(()=>null);
    } catch (err) { status.textContent = err.message; toast(err.message,false); }
  }
  canvas.addEventListener('pointerdown', async event => {
    if (!maskCanvas.width) return; const p=point(event); const tool=state.segmentationEditTool || 'brush';
    if (tool === 'magic') { await magicSelect(p); return; }
    drawing=true; start=p; last=p; previewEnd=p; lasso=[p]; snapshot(); canvas.setPointerCapture?.(event.pointerId);
    if (tool === 'brush') drawMaskStroke(p,p,false); else if (tool === 'eraser') drawMaskStroke(p,p,true); redraw();
  });
  canvas.addEventListener('pointermove', event => { if (!drawing) return; const p=point(event); const tool=state.segmentationEditTool || 'brush'; previewEnd=p; if (tool==='brush') drawMaskStroke(last,p,false); else if (tool==='eraser') drawMaskStroke(last,p,true); else if (tool==='lasso') lasso.push(p); last=p; redraw(); });
  function finish(event) { if (!drawing) return; const p=event ? point(event) : previewEnd || start; const tool=state.segmentationEditTool || 'brush'; if (['rectangle','ellipse'].includes(tool)) commitShape(tool,start,p); else if (tool==='lasso') commitShape('lasso',start,p,lasso); drawing=false; start=null; last=null; previewEnd=null; lasso=[]; redraw(); }
  canvas.addEventListener('pointerup', finish); canvas.addEventListener('pointercancel', finish); canvas.addEventListener('pointerleave', event => { if (drawing && ['brush','eraser','lasso'].includes(state.segmentationEditTool || '')) finish(event); });
  image.onload = async () => {
    canvas.width=image.naturalWidth || item.width || 1; canvas.height=image.naturalHeight || item.height || 1; maskCanvas.width=canvas.width; maskCanvas.height=canvas.height;
    try {
      if (row?.mask_path) await loadMaskPath(row.mask_path,'replace');
      else if (row?.polygon?.length) { maskCtx.fillStyle='#fff'; maskCtx.beginPath(); maskCtx.moveTo(row.polygon[0][0],row.polygon[0][1]); row.polygon.slice(1).forEach(p=>maskCtx.lineTo(p[0],p[1])); maskCtx.closePath(); maskCtx.fill(); }
      else if (row?.bbox && Object.keys(row.bbox).length) { const values=_spatialBoxValues(row.bbox); if (values) maskCtx.fillRect(values[0],values[1],values[2]-values[0],values[3]-values[1]); }
      redraw(); status.textContent=row ? `Editing persistent mask layer #${row.id}.` : 'Blank mask layer ready.'; readyResolve();
    } catch (err) { status.textContent=err.message; readyResolve(); }
  };
  image.onerror=()=>{status.textContent='Could not load the source image.';readyResolve();}; image.src=`/api/media/${item.id}/file`;
  return {
    node:wrap, ready, toDataURL:()=>maskCanvas.toDataURL('image/png'),
    clear:()=>{snapshot();maskCtx.clearRect(0,0,maskCanvas.width,maskCanvas.height);redraw();},
    invert:()=>{snapshot();const data=maskCtx.getImageData(0,0,maskCanvas.width,maskCanvas.height);for(let i=0;i<data.data.length;i+=4){const alpha=data.data[i+3]||Math.max(data.data[i],data.data[i+1],data.data[i+2]);data.data[i]=data.data[i+1]=data.data[i+2]=255;data.data[i+3]=255-alpha;}maskCtx.putImageData(data,0,0);redraw();},
    undo:()=>{if(!undoStack.length)return;redoStack.push(maskCtx.getImageData(0,0,maskCanvas.width,maskCanvas.height));restore(undoStack.pop());},
    redo:()=>{if(!redoStack.length)return;undoStack.push(maskCtx.getImageData(0,0,maskCanvas.width,maskCanvas.height));restore(redoStack.pop());},
    loadMaskPath:async(path,mode='replace')=>{snapshot();await loadMaskPath(path,mode);}, redraw
  };
}

function _ensureSpatialEditorItem(item, title) {
  if (!item) return card(title, [el('p', { class: 'muted' }, 'Load the Gallery and select an image first.')]);
  if (!state.annotationState || Number(state.annotationState.media?.id) !== Number(item.id)) {
    setTimeout(async () => { try { await releaseSpatialPreviewFiles('detection'); await releaseSpatialPreviewFiles('segmentation'); await loadAnnotationState(item.id); state.detectionOutput = null; state.segmentationOutput = null; state.detectionPreviewSelection.clear(); state.segmentationPreviewSelection.clear(); state.detectionLayerSelection.clear(); state.segmentationLayerSelection.clear(); state.detectionEditingLayerId=null; state.segmentationEditingLayerId=null; render(); } catch (err) { toast(err.message, false); } }, 0);
    return card(title, [el('p', { class: 'muted' }, `Loading spatial annotation state for image #${item.id}...`)]);
  }
  return null;
}

function detectionEditorView() {
  const item = activeEditorItem(); const loading = _ensureSpatialEditorItem(item, 'Detection & Bounding Boxes'); if (loading) return loading;
  const rows = (state.annotationState.annotations || []).filter(row => ['bbox','obb','rotated_bbox'].includes(String(row.annotation_type || '').toLowerCase()));
  const output = state.detectionOutput?.media_id === item.id ? state.detectionOutput : null;
  const proposals = output?.proposals || [];
  const model = selectedSpatialModel('detection'); const modelSelect = spatialModelSelect('detection');
  if (model && !state.detectionClassInfo) setTimeout(() => refreshSpatialModelClasses('detection', model.name).then(render).catch(() => null), 0);
  const label = el('input', { value: state.detectionLabel || '', placeholder: 'Optional saved annotation label (blank = true model class)', style: 'min-width:300px', oninput: e => { state.detectionLabel = e.target.value; } });
  const target = el('input', { value: state.detectionTarget || '', placeholder: 'optional character/object target', oninput: e => { state.detectionTarget = e.target.value; } });
  const prompt = el('textarea', { rows: '2', placeholder: 'Used only by text-conditioned/open-vocabulary models' }, state.detectionPrompt || ''); prompt.addEventListener('input', e => { state.detectionPrompt = e.target.value; });
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.001', value: state.detectionThreshold ?? state.settings.classifier_threshold ?? 0.25, style: 'width:90px', oninput: e => { state.detectionThreshold = e.target.value; } });
  const iou = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: state.detectionIou ?? 0.7, style: 'width:90px', oninput: e => { state.detectionIou = e.target.value; } });
  const imgsz = el('input', { type: 'number', min: '128', step: '32', value: state.detectionImageSize ?? 1024, style: 'width:100px', oninput: e => { state.detectionImageSize = e.target.value; } });
  const maxProps = el('input', { type: 'number', min: '1', max: '3000', value: state.detectionMaxProposals ?? 300, style: 'width:90px', oninput: e => { state.detectionMaxProposals = e.target.value; } });
  const device = el('input', { value: state.detectionDevice || 'auto', placeholder: 'auto / cuda:0 / cpu', style: 'width:150px', oninput: e => { state.detectionDevice = e.target.value; } });
  const agnosticNms = el('input', { type: 'checkbox', checked: Boolean(state.detectionAgnosticNms), onchange: e => { state.detectionAgnosticNms = e.target.checked; } });
  const augment = el('input', { type: 'checkbox', checked: Boolean(state.detectionAugment), onchange: e => { state.detectionAugment = e.target.checked; } });
  const body = save => ({
    media_id: item.id,
    label: label.value.trim() || state.detectionClassQuery || 'object',
    target_name: target.value || '',
    prompt: prompt.value || state.detectionClassQuery || '',
    model_key: modelSelect.value,
    threshold: Number(threshold.value),
    save,
    device: device.value || 'auto',
    options: {
      local_model_path: state.detectionLocalModelPath || '',
      custom_model_type: state.detectionCustomModelType || 'yolo',
      class_query: state.detectionClassQuery || '',
      annotation_label: label.value.trim(),
      strict_class_filter: true,
      max_proposals: Number(maxProps.value || 300),
      max_det: Number(maxProps.value || 300),
      imgsz: Number(imgsz.value || 1024),
      iou: Number(iou.value),
      agnostic_nms: Boolean(agnosticNms.checked),
      augment: Boolean(augment.checked),
    }
  });
  const runDetection = async save => {
    if (!modelSelect.value) throw new Error('Select a detection model first.');
    await releaseSpatialPreviewFiles('detection');
    state.detectionOutput = await api('/api/spatial/detection/propose', { method: 'POST', body: body(save) });
    resetSpatialPreviewSelection('detection', save ? [] : (state.detectionOutput.proposals || []));
    if (!state.detectionOutput.ok) throw new Error(state.detectionOutput.error || 'Detection failed');
    if (save) await loadAnnotationState(item.id);
    toast(save ? `Saved ${state.detectionOutput.saved?.length || 0} model bbox annotation(s)` : `Previewed ${state.detectionOutput.count} real model box(es)`);
    render();
  };
  return el('div', { class: 'grid' }, [
    card('Detection & Bounding Boxes', [
      editorQueueControls(item),
      el('p', { class: 'muted' }, 'This workspace creates detection boxes only. Closed-set models now strictly filter by the selected model class; they never relabel unrelated detections with the typed token. Orange boxes are unsaved model previews; green boxes are saved annotations.'),
      el('div', { class: 'row' }, [label, target,
        el('button', { class: 'secondary', onclick: async () => { await loadAnnotationState(item.id); render(); } }, 'Refresh Boxes'),
        el('button', { class: 'secondary', disabled: !output, onclick: () => clearSpatialPreview('detection') }, 'Clear Generated Preview'),
        el('button', { class: 'danger', onclick: () => clearSavedGeneratedSpatial('detection', item, modelSelect.value || '') }, 'Delete Saved Model Boxes')
      ]),
      spatialCanvas(item, 'detection', rows, proposals)
    ]),
    spatialModelPanel('detection', model),
    spatialClassPanel('detection', model),
    card('Run Detection Model', [
      el('div', { class: 'row' }, [modelSelect, el('label', {}, ['confidence', threshold]), el('label', {}, ['NMS IoU', iou]), el('label', {}, ['image size', imgsz]), el('label', {}, ['max boxes', maxProps]), device]),
      prompt,
      el('div', { class: 'row' }, [
        el('label', {}, [agnosticNms, ' class-agnostic NMS']),
        el('label', {}, [augment, ' test-time augmentation']),
        el('span', { class: 'muted tiny' }, 'For Ultralytics NMS, a higher IoU retains more overlapping boxes; a lower IoU suppresses more. max boxes is passed to the model as max_det.')
      ]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { await runDetection(false); } catch (err) { state.detectionOutput = { ok:false, media_id:item.id, proposals:[], error:err.message }; toast(err.message, false); render(); } } }, 'Preview Model Boxes'),
        el('button', { class: 'primary', onclick: async () => { try { await runDetection(true); } catch (err) { state.detectionOutput = { ok:false, media_id:item.id, proposals:[], error:err.message }; toast(err.message, false); render(); } } }, 'Generate + Save Boxes'),
        el('button', { class: 'secondary', disabled: !output, onclick: () => clearSpatialPreview('detection') }, 'Clear Preview Boxes')
      ]),
      spatialProposalSummary('detection', output)
    ]),
    card('Manual / Layer Bounding Box Editor', [
      el('p', { class: 'muted' }, state.detectionEditingLayerId ? `Editing persistent layer #${state.detectionEditingLayerId}. Drag a replacement box, then update the same layer.` : 'Drag a box on the image. Save it as a new independent layer, or choose Edit on an existing layer to replace that layer geometry.'),
      el('div', { class: 'row' }, [
        state.detectionEditingLayerId ? el('span', { class: 'badge' }, `Editing layer #${state.detectionEditingLayerId}`) : null,
        el('button', { class: 'primary', onclick: async () => { try { if (!state.detectionDraftBbox) throw new Error('Drag a bbox on the image first.'); const saved = await api('/api/reference/annotations', { method: 'POST', body: { media_id: item.id, label: label.value || state.detectionClassQuery || 'object', target_name: target.value || '', annotation_type: 'bbox', bbox: state.detectionDraftBbox, source: 'user', metadata: { spatial_task: 'detection' }, layer_name: label.value || state.detectionClassQuery || 'manual box', color: '#ef4444', opacity: 0.8 } }); state.detectionDraftBbox = null; state.detectionEditingLayerId = null; await loadAnnotationState(item.id); toast(`New bbox layer saved #${saved.id || saved.annotation_id || ''}`); render(); } catch (err) { toast(err.message, false); } } }, 'Save as New Box Layer'),
        el('button', { class: 'primary', disabled: !state.detectionEditingLayerId, onclick: async () => { try { if (!state.detectionDraftBbox || !state.detectionEditingLayerId) throw new Error('Load a layer and draw its replacement bbox first.'); await api(`/api/spatial/layers/${state.detectionEditingLayerId}`, { method: 'PATCH', body: { bbox: state.detectionDraftBbox, label: label.value || state.detectionClassQuery || 'object', target_name: target.value || '', metadata: { spatial_task: 'detection', edited_in_layer_editor: true } } }); const id=state.detectionEditingLayerId; state.detectionDraftBbox=null; state.detectionEditingLayerId=null; await loadAnnotationState(item.id); toast(`Box layer #${id} updated`); render(); } catch (err) { toast(err.message,false); } } }, 'Update Selected Box Layer'),
        el('button', { class: 'secondary', disabled: spatialPreviewSelection('detection').size !== 1, onclick: () => { const indexes=[...spatialPreviewSelection('detection')]; const proposal=proposals[indexes[0]]; if (!proposal?.bbox) return toast('Select exactly one generated preview box first.', false); state.detectionDraftBbox={...proposal.bbox}; state.detectionEditingLayerId=null; state.detectionLabel=proposal.label || state.detectionLabel || ''; toast('Generated preview box loaded into the editable draft. Save it as a new layer after adjusting it.'); render(); } }, 'Load Selected Preview Box into Editor'),
        el('button', { class: 'secondary', onclick: () => { state.detectionDraftBbox = null; state.detectionEditingLayerId = null; render(); } }, 'Clear / Exit Edit'),
        el('button', { class: 'secondary', onclick: () => { if (!state.detectionDraftBbox) return toast('Draw or load a bbox first.', false); state.segmentationPromptBbox = { ...state.detectionDraftBbox }; toast('Draft bbox copied into Segmentation & Masks.'); setTab('Segmentation & Masks'); } }, 'Use Draft as Segmentation Prompt')
      ].filter(Boolean))
    ]),
    spatialLayerCompositor('detection', item, rows, proposals),
    quickCurationModelRunCard({ title: 'Tag / Rating Cross-check for Detection Image', getMediaIds: () => [item.id], description: 'Run JTP-3 or visual rating models separately from spatial detection.' }),
    card('Detection Result JSON', [el('pre', { class: 'log' }, JSON.stringify(output || {}, null, 2))])
  ]);
}

function segmentationEditorView() {
  const item = activeEditorItem(); const loading = _ensureSpatialEditorItem(item, 'Segmentation & Masks'); if (loading) return loading;
  const rows = (state.annotationState.annotations || []).filter(row => ['mask','polygon','bbox_mask','segmentation'].includes(String(row.annotation_type || '').toLowerCase()));
  const output = state.segmentationOutput?.media_id === item.id ? state.segmentationOutput : null;
  const proposals = output?.proposals || [];
  const model = selectedSpatialModel('segmentation'); const modelSelect = spatialModelSelect('segmentation');
  if (model && !state.segmentationClassInfo) setTimeout(() => refreshSpatialModelClasses('segmentation', model.name).then(render).catch(() => null), 0);
  const classMode = state.segmentationClassInfo?.mode || 'unknown';
  const label = el('input', { value: state.segmentationLabel || '', placeholder: 'Optional saved mask label', style: 'min-width:260px', oninput: e => { state.segmentationLabel = e.target.value; } });
  const target = el('input', { value: state.segmentationTarget || '', placeholder: 'optional character/object target', oninput: e => { state.segmentationTarget = e.target.value; } });
  const drawMode = el('select', { onchange: e => { state.segmentationDrawMode = e.target.value; render(); } }, [
    el('option', { value: 'polygon' }, 'Draw editable mask polygon'),
    el('option', { value: 'bbox_prompt' }, 'Draw bbox prompt for model'),
    el('option', { value: 'positive_point' }, 'Positive Point (+ include)'),
    el('option', { value: 'negative_point' }, 'Negative Point (− exclude)'),
    el('option', { value: 'remove_point' }, 'Remove Point Tool')
  ]); drawMode.value = state.segmentationDrawMode || 'polygon';
  const outputMode = el('select', { onchange: e => { state.segmentationOutputMode = e.target.value; } }, [
    el('option', { value: 'instance' }, 'Instance masks — separate candidate layers'),
    el('option', { value: 'semantic_union' }, 'Semantic class mask — union best prompted instances')
  ]); outputMode.value = state.segmentationOutputMode || 'instance';
  const prompt = el('textarea', { rows: '2', placeholder: 'Only text-conditioned segmentation/VLM adapters use this prompt' }, state.segmentationPrompt || ''); prompt.addEventListener('input', e => { state.segmentationPrompt = e.target.value; });
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.001', value: state.segmentationThreshold ?? 0.25, style: 'width:90px', oninput: e => { state.segmentationThreshold = e.target.value; } });
  const iou = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: state.segmentationIou ?? 0.7, style: 'width:90px', oninput: e => { state.segmentationIou = e.target.value; } });
  const imgsz = el('input', { type: 'number', min: '128', step: '32', value: state.segmentationImageSize ?? 1024, style: 'width:100px', oninput: e => { state.segmentationImageSize = e.target.value; } });
  const maxProps = el('input', { type: 'number', min: '1', max: '3000', value: state.segmentationMaxProposals ?? 100, style: 'width:90px', oninput: e => { state.segmentationMaxProposals = e.target.value; } });
  const device = el('input', { value: state.segmentationDevice || 'auto', placeholder: 'auto / cuda:0 / cpu', style: 'width:150px', oninput: e => { state.segmentationDevice = e.target.value; } });
  const multimask = el('input', { type: 'checkbox', checked: state.segmentationMultimask !== false, onchange: e => { state.segmentationMultimask = e.target.checked; } });
  const retinaMasks = el('input', { type: 'checkbox', checked: state.segmentationRetinaMasks !== false, onchange: e => { state.segmentationRetinaMasks = e.target.checked; } });
  const agnosticNms = el('input', { type: 'checkbox', checked: Boolean(state.segmentationAgnosticNms), onchange: e => { state.segmentationAgnosticNms = e.target.checked; } });
  const augment = el('input', { type: 'checkbox', checked: Boolean(state.segmentationAugment), onchange: e => { state.segmentationAugment = e.target.checked; } });
  const pointsPerSide = el('input', { type: 'number', min: '4', max: '128', value: state.segmentationPointsPerSide ?? 32, style: 'width:80px', oninput: e => { state.segmentationPointsPerSide = e.target.value; } });
  const predIou = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: state.segmentationPredIou ?? 0.70, style: 'width:80px', oninput: e => { state.segmentationPredIou = e.target.value; } });
  const stability = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: state.segmentationStability ?? 0.85, style: 'width:80px', oninput: e => { state.segmentationStability = e.target.value; } });
  const boxNms = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: state.segmentationBoxNms ?? 0.7, style: 'width:80px', oninput: e => { state.segmentationBoxNms = e.target.value; } });
  const cropLayers = el('input', { type: 'number', min: '0', max: '4', value: state.segmentationCropLayers ?? 0, style: 'width:70px', oninput: e => { state.segmentationCropLayers = e.target.value; } });
  const minArea = el('input', { type: 'number', min: '0', step: '16', value: state.segmentationMinArea ?? 0, style: 'width:100px', oninput: e => { state.segmentationMinArea = e.target.value; } });
  const maskPath = el('input', { placeholder: 'Edited mask PNG path from Krita or another editor', style: 'min-width:420px' });

  const detectionModels = spatialTaskModels('detection');
  if (!state.segmentationGuideModel && detectionModels.length) state.segmentationGuideModel = detectionModels[0].name;
  const guideEnabled = el('input', { type: 'checkbox', checked: Boolean(state.segmentationGuideEnabled), onchange: e => { state.segmentationGuideEnabled = e.target.checked; render(); } });
  const guideModel = el('select', { onchange: e => { state.segmentationGuideModel = e.target.value; } }, [el('option', { value: '' }, 'Select guide detector'), ...detectionModels.map(row => el('option', { value: row.name }, modelLabel(row)))]); guideModel.value = state.segmentationGuideModel || '';
  const guideThreshold = el('input', { type: 'number', min: '0', max: '1', step: '0.001', value: state.segmentationGuideThreshold ?? 0.20, style: 'width:90px', oninput: e => { state.segmentationGuideThreshold = e.target.value; } });
  const guideMax = el('input', { type: 'number', min: '1', max: '1000', value: state.segmentationGuideMax ?? 50, style: 'width:80px', oninput: e => { state.segmentationGuideMax = e.target.value; } });

  const body = save => ({
    media_id: item.id,
    label: label.value.trim() || state.segmentationClassQuery || 'object',
    target_name: target.value || '',
    prompt: prompt.value || state.segmentationClassQuery || '',
    model_key: modelSelect.value,
    threshold: Number(threshold.value),
    save,
    device: device.value || 'auto',
    options: {
      local_model_path: state.segmentationLocalModelPath || '',
      custom_model_type: state.segmentationCustomModelType || 'auto',
      class_query: state.segmentationClassQuery || '',
      annotation_label: label.value.trim(),
      strict_class_filter: true,
      max_proposals: Number(maxProps.value || 100),
      max_det: Number(maxProps.value || 100),
      imgsz: Number(imgsz.value || 1024),
      iou: Number(iou.value),
      bbox_prompt: state.segmentationPromptBbox || null,
      point_prompts: (state.segmentationPromptPoints || []).map(point => ({ x: Number(point.x), y: Number(point.y), label: Number(point.label) > 0 ? 1 : 0 })),
      output_mode: outputMode.value || 'instance',
      multimask: Boolean(multimask.checked),
      retina_masks: Boolean(retinaMasks.checked),
      agnostic_nms: Boolean(agnosticNms.checked),
      augment: Boolean(augment.checked),
      points_per_side: Number(pointsPerSide.value || 32),
      pred_iou_thresh: Number(predIou.value),
      stability_score_thresh: Number(stability.value),
      box_nms_thresh: Number(boxNms.value),
      crop_n_layers: Number(cropLayers.value || 0),
      min_mask_region_area: Number(minArea.value || 0),
      guide_detection_model_key: state.segmentationGuideEnabled ? guideModel.value : '',
      guide_threshold: Number(guideThreshold.value),
      guide_max_proposals: Number(guideMax.value || 50),
      guide_detection_options: {
        local_model_path: state.detectionLocalModelPath || '',
        custom_model_type: state.detectionCustomModelType || 'yolo',
        imgsz: Number(state.detectionImageSize || imgsz.value || 1024),
        iou: Number(state.detectionIou ?? 0.7),
        max_proposals: Number(guideMax.value || 50),
        agnostic_nms: Boolean(state.detectionAgnosticNms),
      }
    }
  });
  const runSegmentation = async save => {
    if (!modelSelect.value) throw new Error('Select a segmentation model first.');
    if (state.segmentationGuideEnabled && !guideModel.value) throw new Error('Select a guide detector or disable detector-guided segmentation.');
    if (state.segmentationGuideEnabled && !String(state.segmentationClassQuery || '').trim()) throw new Error('Detector-guided segmentation requires a class/token to find.');
    await releaseSpatialPreviewFiles('segmentation');
    state.segmentationOutput = await api('/api/spatial/segmentation/propose', { method: 'POST', body: body(save) });
    resetSpatialPreviewSelection('segmentation', save ? [] : (state.segmentationOutput.proposals || []));
    if (!state.segmentationOutput.ok) throw new Error(state.segmentationOutput.error || 'Segmentation failed');
    if (save) await loadAnnotationState(item.id);
    toast(save ? `Saved ${state.segmentationOutput.saved?.length || 0} model mask annotation(s)` : `Previewed ${state.segmentationOutput.count} real model mask(s)`);
    render();
  };
  const editingMaskRow = rows.find(row => Number(row.id) === Number(state.segmentationEditingLayerId)) || null;
  const maskEditor = maskPaintEditor(item, editingMaskRow);
  const editTool = el('select', { onchange: e => { state.segmentationEditTool = e.target.value; maskEditor.redraw(); } }, [
    ['brush','Brush'], ['eraser','Eraser'], ['lasso','Freehand Lasso'], ['ellipse','Ellipse Select'], ['rectangle','Rectangle Select'], ['magic','Magic Select']
  ].map(([value,text]) => el('option', { value }, text))); editTool.value = state.segmentationEditTool || 'brush';
  const brushSize = el('input', { type: 'range', min: '1', max: '256', step: '1', value: state.segmentationBrushSize || 32, oninput: e => { state.segmentationBrushSize = Number(e.target.value); brushSizeLabel.textContent = `${e.target.value}px`; } });
  const brushSizeLabel = el('span', { class: 'badge tiny' }, `${state.segmentationBrushSize || 32}px`);
  const brushOpacity = el('input', { type:'range', min:'0.05', max:'1', step:'0.05', value:state.segmentationBrushOpacity ?? 1, oninput:e=>{state.segmentationBrushOpacity=Number(e.target.value);} });
  const brushHardness = el('input', { type:'range', min:'0.05', max:'1', step:'0.05', value:state.segmentationBrushHardness ?? 0.9, oninput:e=>{state.segmentationBrushHardness=Number(e.target.value);} });
  const shapeMode = el('select', { onchange: e => { state.segmentationShapeMode = e.target.value; } }, [el('option', { value: 'add' }, 'Shapes add to mask'), el('option', { value: 'subtract' }, 'Shapes subtract from mask'), el('option', { value: 'replace' }, 'Shapes replace mask')]); shapeMode.value = state.segmentationShapeMode || 'add';
  const layerColor = el('input', { type: 'color', value: state.segmentationLayerColor || editingMaskRow?.color || '#22c55e', onchange: e => { state.segmentationLayerColor = e.target.value; maskEditor.redraw(); } });
  const layerOpacity = el('input', { type: 'range', min: '0.05', max: '1', step: '0.05', value: state.segmentationLayerOpacity ?? editingMaskRow?.opacity ?? 0.55, oninput: e => { state.segmentationLayerOpacity = Number(e.target.value); maskEditor.redraw(); } });
  const magicMethod = el('select', { onchange: e => { state.segmentationMagicMethod = e.target.value; } }, [el('option', { value: 'flood_fill' }, 'Contiguous Color Flood Fill'), el('option', { value: 'color_range' }, 'Non-contiguous Similar Color'), el('option', { value: 'grabcut' }, 'Object GrabCut (uses bbox prompt or click area)')]); magicMethod.value = state.segmentationMagicMethod || 'flood_fill';
  const magicMode = el('select', { onchange: e => { state.segmentationMagicMode = e.target.value; } }, ['add','subtract','replace','intersection','xor'].map(value => el('option', { value }, `Magic result: ${value}`))); magicMode.value = state.segmentationMagicMode || 'add';
  const magicTolerance = el('input', { type: 'number', min: '0', max: '255', value: state.segmentationMagicTolerance ?? 24, style: 'width:80px', oninput: e => { state.segmentationMagicTolerance = Number(e.target.value); } });
  const magicFeather = el('input', { type:'number', min:'0', max:'128', value:state.segmentationMagicFeather ?? 0, style:'width:75px', oninput:e=>{state.segmentationMagicFeather=Number(e.target.value);} });
  const magicGrow = el('input', { type:'number', min:'-128', max:'128', value:state.segmentationMagicGrow ?? 0, style:'width:75px', oninput:e=>{state.segmentationMagicGrow=Number(e.target.value);} });
  const magicInvert = el('input', { type:'checkbox', checked:Boolean(state.segmentationMagicInvert), onchange:e=>{state.segmentationMagicInvert=e.target.checked;} });
  const editorMergeMode = el('select', {}, ['add','subtract','intersection','xor','replace'].map(value=>el('option',{value},`Load selected layers: ${value}`))); editorMergeMode.value=state.segmentationEditorMergeMode||'add'; editorMergeMode.addEventListener('change',e=>{state.segmentationEditorMergeMode=e.target.value;});
  return el('div', { class: 'grid' }, [
    card('Segmentation & Masks', [
      editorQueueControls(item),
      el('p', { class: 'muted' }, 'This workspace creates masks/polygons only. YOLO segmentation uses strict class-ID filtering. SAM/SAM-HQ/SAM2 are class-agnostic and accept positive points, negative points, bbox prompts, or detector-guided boxes. Green translucent pixels are actual mask files; orange geometry is an unsaved preview.'),
      el('div', { class: 'row' }, [label, target, drawMode,
        el('button', { class: 'secondary', onclick: async () => { await loadAnnotationState(item.id); render(); } }, 'Refresh Masks'),
        el('button', { class: 'secondary', disabled: !output, onclick: () => clearSpatialPreview('segmentation') }, 'Clear Generated Preview'),
        el('button', { class: 'danger', onclick: () => clearSavedGeneratedSpatial('segmentation', item, modelSelect.value || '') }, 'Delete Saved Model Masks')
      ]),
      el('div', { class: 'row' }, [
        el('button', { class: state.segmentationDrawMode === 'positive_point' ? 'primary' : 'secondary', onclick: () => { state.segmentationDrawMode = 'positive_point'; render(); } }, 'Positive Point (+ Include)'),
        el('button', { class: state.segmentationDrawMode === 'negative_point' ? 'primary' : 'secondary', onclick: () => { state.segmentationDrawMode = 'negative_point'; render(); } }, 'Negative Point (− Exclude)'),
        el('button', { class: state.segmentationDrawMode === 'remove_point' ? 'primary' : 'secondary', onclick: () => { state.segmentationDrawMode = 'remove_point'; render(); } }, 'Remove Point Tool'),
        el('button', { class: 'secondary', disabled: !(state.segmentationPromptPoints || []).length, onclick: () => { state.segmentationPromptPoints = (state.segmentationPromptPoints || []).slice(0, -1); render(); } }, 'Undo Last Point'),
        el('button', { class: 'secondary', onclick: () => { state.segmentationPromptPoints = (state.segmentationPromptPoints || []).filter(point => Number(point.label) <= 0); render(); } }, 'Clear Positive'),
        el('button', { class: 'secondary', onclick: () => { state.segmentationPromptPoints = (state.segmentationPromptPoints || []).filter(point => Number(point.label) > 0); render(); } }, 'Clear Negative'),
        el('button', { class: 'secondary', onclick: () => { state.segmentationPromptPoints = []; render(); } }, 'Clear All Points')
      ]),
      el('div', { class: 'muted tiny' }, (state.segmentationPromptPoints || []).length
        ? `Point order: ${(state.segmentationPromptPoints || []).map((point, index) => `${index + 1}:${Number(point.label) > 0 ? '+' : '−'}(${Number(point.x).toFixed(1)}, ${Number(point.y).toFixed(1)})`).join(' · ')}`
        : 'No point prompts. Add one or more green positive points inside the target and red negative points on confusing background/neighboring objects.'),
      spatialCanvas(item, 'segmentation', rows, proposals)
    ]),
    spatialModelPanel('segmentation', model),
    spatialClassPanel('segmentation', model),
    classMode === 'class_agnostic' ? card('Semantic Class → Detector → SAM Pipeline', [
      el('p', { class: 'muted' }, 'SAM cannot locate a named class by itself. Enable this pipeline to run a detection model for the selected class/token, then send every returned box to SAM as a prompt. Different valid classes can therefore produce different boxes, masks, and scores.'),
      el('div', { class: 'row' }, [el('label', {}, [guideEnabled, ' enable detector-guided segmentation']), guideModel, el('label', {}, ['guide confidence', guideThreshold]), el('label', {}, ['max guide boxes', guideMax])])
    ]) : null,
    card('Run Segmentation Model', [
      el('div', { class: 'row' }, [modelSelect, outputMode, el('label', {}, ['confidence / mask IoU', threshold]), el('label', {}, ['YOLO NMS IoU', iou]), el('label', {}, ['image size', imgsz]), el('label', {}, ['max masks', maxProps]), device]),
      prompt,
      el('div', { class: 'row' }, [
        el('span', { class: 'muted tiny' }, `BBox prompt: ${state.segmentationPromptBbox ? JSON.stringify(state.segmentationPromptBbox) : 'none (automatic or detector-guided mode)'}`),
        el('span', { class: 'muted tiny' }, `Point prompts: ${(state.segmentationPromptPoints || []).length}`),
        el('button', { class: 'secondary', onclick: () => { state.segmentationPromptBbox = null; render(); } }, 'Clear BBox Prompt')
      ]),
      el('details', { open: false }, [
        el('summary', {}, 'Multiple-output / NMS / automatic-mask controls'),
        el('div', { class: 'row' }, [
          el('label', {}, [multimask, ' return alternative masks per bbox prompt']),
          el('label', {}, [retinaMasks, ' high-resolution YOLO masks']),
          el('label', {}, [agnosticNms, ' class-agnostic YOLO NMS']),
          el('label', {}, [augment, ' YOLO test-time augmentation'])
        ]),
        el('div', { class: 'row' }, [
          el('label', {}, ['SAM points/side', pointsPerSide]),
          el('label', {}, ['SAM predicted-IoU minimum', predIou]),
          el('label', {}, ['SAM stability minimum', stability]),
          el('label', {}, ['SAM box NMS', boxNms]),
          el('label', {}, ['crop layers', cropLayers]),
          el('label', {}, ['minimum mask area', minArea])
        ]),
        el('p', { class: 'muted tiny' }, 'To obtain more automatic SAM masks, raise points/side or crop layers and lower predicted-IoU/stability thresholds. For YOLO, max masks is passed as max_det; a higher NMS IoU retains more overlapping instances.')
      ]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { await runSegmentation(false); } catch (err) { state.segmentationOutput = { ok:false, media_id:item.id, proposals:[], error:err.message }; toast(err.message, false); render(); } } }, 'Preview Actual Masks'),
        el('button', { class: 'primary', onclick: async () => { try { await runSegmentation(true); } catch (err) { state.segmentationOutput = { ok:false, media_id:item.id, proposals:[], error:err.message }; toast(err.message, false); render(); } } }, 'Generate + Save Masks'),
        el('button', { class: 'secondary', disabled: !output, onclick: () => clearSpatialPreview('segmentation') }, 'Clear Preview Masks')
      ]),
      spatialProposalSummary('segmentation', output)
    ]),
    card('Layer Mask Editor — Brush / Eraser / Lasso / Ellipse / Magic Select', [
      el('p', { class: 'muted' }, editingMaskRow
        ? `Editing persistent layer #${editingMaskRow.id} (${editingMaskRow.layer_name || editingMaskRow.label || 'mask'}). Every save updates this layer and records a revision; choose Exit / New Blank to create another object layer.`
        : 'Editing a new blank mask. Paint or select one object, then save it as its own persistent layer. Existing model, Krita, composite, and manual layers remain available in the stack.'),
      el('div', { class: 'mask-toolbar' }, [
        editTool, el('label', {}, ['brush size ', brushSize, brushSizeLabel]), el('label', {}, ['brush opacity ', brushOpacity]), el('label', {}, ['hardness ', brushHardness]), shapeMode,
        el('label', {}, ['overlay color ', layerColor]), el('label', {}, ['overlay opacity ', layerOpacity]),
        el('button', { class: 'secondary', onclick: () => maskEditor.undo() }, 'Undo'),
        el('button', { class: 'secondary', onclick: () => maskEditor.redo() }, 'Redo'),
        el('button', { class: 'secondary', onclick: () => maskEditor.invert() }, 'Invert'),
        el('button', { class: 'secondary', onclick: () => maskEditor.clear() }, 'Clear Canvas')
      ]),
      el('div', { class: 'row' }, [magicMethod, magicMode, el('label', {}, ['tolerance ', magicTolerance]), el('label', {}, ['feather ', magicFeather]), el('label', {}, ['grow/shrink ', magicGrow]), el('label', {}, [magicInvert, ' invert']),
        el('span', { class: 'muted tiny' }, 'Choose Magic Select, then click the object/region. Contiguous Flood Fill follows connected similar pixels; Non-contiguous Similar Color finds matching colors across the image; GrabCut estimates an object from the current bbox prompt or click area.')
      ]),
      maskEditor.node,
      el('div', { class: 'row' }, [
        editorMergeMode,
        el('button', { class:'secondary', onclick:async()=>{try{await maskEditor.ready;const selectedRows=rows.filter(row=>state.segmentationLayerSelection.has(Number(row.id))&&row.mask_path);if(!selectedRows.length)throw new Error('Select one or more saved mask layers with mask files first.');let mode=editorMergeMode.value;for(let index=0;index<selectedRows.length;index++){await maskEditor.loadMaskPath(selectedRows[index].mask_path,index===0&&mode==='replace'?'replace':mode);}toast(`Loaded ${selectedRows.length} selected mask layer(s) into the editor using ${mode}.`);}catch(err){toast(err.message,false);}} }, 'Load Selected Layers into Editor'),
        el('button', { class:'secondary', disabled:spatialPreviewSelection('segmentation').size===0, onclick:async()=>{try{await maskEditor.ready;const selectedPreviews=proposals.filter((_,index)=>spatialPreviewSelection('segmentation').has(index)&&proposals[index].mask_path);if(!selectedPreviews.length)throw new Error('Select one or more generated preview masks first.');let mode=editorMergeMode.value;for(let index=0;index<selectedPreviews.length;index++){await maskEditor.loadMaskPath(selectedPreviews[index].mask_path,index===0&&mode==='replace'?'replace':mode);}toast(`Loaded ${selectedPreviews.length} generated preview mask(s) into the editor using ${mode}. Save as a new persistent layer after refining.`);}catch(err){toast(err.message,false);}} }, 'Load Selected Preview Masks into Editor'),
        el('button', { class:'secondary', onclick:async()=>{try{const result=await api('/api/spatial/segmentation/layers/blank',{method:'POST',body:{media_id:item.id,label:label.value||'blank_mask',layer_name:label.value||'blank mask'}});state.segmentationEditingLayerId=Number(result.id||result.annotation_id);await loadAnnotationState(item.id);toast('Blank persistent mask layer created');render();}catch(err){toast(err.message,false);}} }, 'Add Blank Persistent Layer')
      ]),
      el('div', { class: 'row' }, [
        editingMaskRow ? el('span', { class: 'badge' }, `Editing layer #${editingMaskRow.id}`) : el('span', { class: 'badge' }, 'New mask layer'),
        el('button', { class: 'primary', onclick: async () => { try { await maskEditor.ready; const saved = await api('/api/spatial/segmentation/save-mask-layer', { method: 'POST', body: { media_id: item.id, mask_data_url: maskEditor.toDataURL(), annotation_id: null, label: label.value || state.segmentationClassQuery || 'object', target_name: target.value || '', source: 'user', metadata: { spatial_task: 'segmentation', editor_tool: state.segmentationEditTool || 'brush' }, layer_name: label.value || state.segmentationClassQuery || 'manual mask', opacity: Number(state.segmentationLayerOpacity ?? 0.55), color: state.segmentationLayerColor || '#22c55e' } }); state.segmentationEditingLayerId = Number(saved.id || saved.annotation_id); await loadAnnotationState(item.id); toast(`New mask layer saved #${state.segmentationEditingLayerId || ''}`); render(); } catch (err) { toast(err.message,false); } } }, 'Save as New Mask Layer'),
        el('button', { class: 'primary', disabled: !editingMaskRow, onclick: async () => { try { if (!editingMaskRow) throw new Error('Choose Edit on a saved mask layer first.'); await maskEditor.ready; await api('/api/spatial/segmentation/save-mask-layer', { method: 'POST', body: { media_id: item.id, mask_data_url: maskEditor.toDataURL(), annotation_id: editingMaskRow.id, label: label.value || editingMaskRow.label || state.segmentationClassQuery || 'object', target_name: target.value || editingMaskRow.target_name || '', source: editingMaskRow.source || 'user', model_key: editingMaskRow.model_key || '', metadata: { spatial_task: 'segmentation', edited_in_mask_editor: true, editor_tool: state.segmentationEditTool || 'brush' }, layer_name: editingMaskRow.layer_name || label.value || 'edited mask', opacity: Number(state.segmentationLayerOpacity ?? editingMaskRow.opacity ?? 0.55), color: state.segmentationLayerColor || editingMaskRow.color || '#22c55e' } }); await loadAnnotationState(item.id); toast(`Mask layer #${editingMaskRow.id} updated`); render(); } catch (err) { toast(err.message,false); } } }, 'Update Selected Mask Layer'),
        el('button', { class: 'secondary', onclick: () => { state.segmentationEditingLayerId = null; render(); } }, 'Exit Edit / New Blank Layer')
      ])
    ]),
    el('details', { class: 'card', open: false }, [
      el('summary', {}, 'Legacy click-point polygon tool'),
      el('p', { class: 'muted' }, 'The older point-by-point polygon workflow remains available for precise vertex control.'),
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => { try { if ((state.segmentationPolygon || []).length < 3) throw new Error('Draw at least three polygon points first.'); const result = await api('/api/reference/annotations', { method: 'POST', body: { media_id: item.id, label: label.value || state.segmentationClassQuery || 'object', target_name: target.value || '', annotation_type: 'mask', polygon: state.segmentationPolygon, bbox: {}, source: 'user', metadata: { spatial_task: 'segmentation', prompt_bbox: state.segmentationPromptBbox || null }, layer_name: label.value || 'polygon mask', color: state.segmentationLayerColor || '#22c55e', opacity: Number(state.segmentationLayerOpacity ?? 0.55) } }); state.segmentationPolygon = []; state.segmentationOutput = null; await loadAnnotationState(item.id); toast(`Manual polygon layer saved: ${result.mask_path || ''}`); render(); } catch (err) { toast(err.message, false); } } }, 'Save Polygon as New Layer'),
        el('button', { class: 'secondary', onclick: () => { state.segmentationPolygon = (state.segmentationPolygon || []).slice(0, -1); render(); } }, 'Undo Last Point'),
        el('button', { class: 'secondary', onclick: () => { state.segmentationPolygon = []; render(); } }, 'Clear Polygon')
      ])
    ]),
    card('Krita Mask Editing Bridge', [el('p', { class: 'muted' }, 'Create a Krita package containing the image and current masks, refine a mask in Krita, then import that edited PNG as another mask annotation.'), el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => { try { state.annotationOutput = await api('/api/krita/annotation-package', { method: 'POST', body: { media_id: item.id, annotation_ids: rows.map(row => row.id), include_masks: true } }); toast('Krita mask package created'); render(); } catch (err) { toast(err.message, false); } } }, 'Create Krita Mask Package'),
      maskPath, el('button', { class: 'secondary', onclick: async () => await pickFilePath(maskPath, 'Select edited mask PNG') }, 'Browse Mask...'),
      el('button', { class: 'primary', onclick: async () => { try { if (!maskPath.value.trim()) throw new Error('Select an edited mask PNG first.'); state.annotationOutput = await api('/api/krita/import-annotation-mask', { method: 'POST', body: { media_id: item.id, mask_path: maskPath.value.trim(), label: label.value || state.segmentationClassQuery || 'object', target_name: target.value || '' } }); await loadAnnotationState(item.id); toast('Krita mask imported'); render(); } catch (err) { toast(err.message, false); } } }, 'Import Edited Mask')
    ]), el('a', { href: '/api/krita/plugin', target: '_blank' }, 'Download optional Krita bridge plugin')]),
    quickCurationModelRunCard({ title: 'Tag / Rating Cross-check for Segmentation Image', getMediaIds: () => [item.id], description: 'Run JTP-3 or visual rating models independently from mask generation.' }),
    spatialLayerCompositor('segmentation', item, rows, proposals),
    card('Segmentation Result JSON', [el('pre', { class: 'log' }, JSON.stringify(output || {}, null, 2))])
  ].filter(Boolean));
}

function poseTemplateRecord(key) {
  return (state.poseTemplates || []).find(row => row.key === key) || { key: 'custom', label: 'Custom', names: [], edges: [], dimension: 'mixed' };
}

function posePoints(mode = state.annotationMode) {
  return mode === 'pose2d' ? (state.annotationPose2D || []) : (state.annotationPose3D || []);
}

function setPosePoints(mode, points) {
  if (mode === 'pose2d') state.annotationPose2D = points;
  else state.annotationPose3D = points;
}

function poseEdgeIndices(edge, points = posePoints()) {
  if (!Array.isArray(edge) || edge.length < 2) return null;
  const lookup = new Map(points.map((point, index) => [String(point.name || index), index]));
  const convert = value => Number.isInteger(value) ? value : (/^\d+$/.test(String(value)) ? Number(value) : lookup.get(String(value)));
  const a = convert(edge[0]), b = convert(edge[1]);
  return Number.isInteger(a) && Number.isInteger(b) && a >= 0 && b >= 0 && a < points.length && b < points.length && a !== b ? [a, b] : null;
}

function addPoseEdge(a, b) {
  if (!Number.isInteger(a) || !Number.isInteger(b) || a === b) return;
  const exists = (state.annotationEdges || []).some(edge => {
    const pair = poseEdgeIndices(edge, posePoints());
    return pair && ((pair[0] === a && pair[1] === b) || (pair[0] === b && pair[1] === a));
  });
  if (!exists) state.annotationEdges = [...(state.annotationEdges || []), [a, b]];
}

function deletePoseJoint(index, mode = state.annotationMode) {
  const points = posePoints(mode);
  if (index < 0 || index >= points.length) return;
  const kept = points.filter((_, i) => i !== index);
  const edges = [];
  for (const edge of state.annotationEdges || []) {
    const pair = poseEdgeIndices(edge, points);
    if (!pair || pair.includes(index)) continue;
    edges.push(pair.map(value => value > index ? value - 1 : value));
  }
  setPosePoints(mode, kept);
  state.annotationEdges = edges;
  state.poseSelectedJoint = null;
  state.poseConnectStart = null;
}

function defaultPoseLocation(name, index, count, width, height, mode) {
  const n = String(name || '').toLowerCase();
  const side = n.startsWith('left_') ? -1 : n.startsWith('right_') ? 1 : 0;
  const centerX = width * 0.5;
  let x = centerX, y = height * (0.15 + 0.7 * index / Math.max(1, count - 1));
  if (n.includes('eye') || n.includes('ear') || n.includes('mouth') || n === 'nose') { y = height * 0.16; x += side * width * (n.includes('ear') ? .07 : .025); }
  else if (n.includes('head')) { y = height * .12; }
  else if (n.includes('neck')) { y = height * .23; }
  else if (n.includes('shoulder')) { y = height * .28; x += side * width * .13; }
  else if (n.includes('elbow')) { y = height * .43; x += side * width * .21; }
  else if (n.includes('wrist') || n.includes('hand') || n.includes('pinky') || n.includes('thumb') || n.includes('index')) { y = height * .56; x += side * width * .27; }
  else if (n.includes('spine') || n.includes('thorax')) { y = height * .39; }
  else if (n.includes('pelvis') || n.includes('hip')) { y = height * .55; x += side * width * .075; }
  else if (n.includes('knee')) { y = height * .73; x += side * width * .085; }
  else if (n.includes('ankle') || n.includes('heel') || n.includes('foot')) { y = height * .91; x += side * width * .09; }
  if (mode === 'pose2d') return { name, x, y, score: 1 };
  return { name, x: (x / width - .5) * 2, y: (.5 - y / height) * 2, z: 0, image_x: x, image_y: y, score: 1 };
}

function applyPoseTemplate(item, createMissing = true) {
  const mode = state.annotationMode === 'pose2d' ? 'pose2d' : 'pose3d';
  const template = poseTemplateRecord(state.poseTemplate || 'custom');
  const names = template.names || [];
  let points = posePoints(mode).map(point => ({ ...point }));
  if (names.length && points.length === names.length) points = points.map((point, index) => ({ ...point, name: names[index] }));
  else if (names.length && createMissing) {
    const width = Number(item.width || state.annotationState?.media?.width || 768);
    const height = Number(item.height || state.annotationState?.media?.height || 1024);
    points = names.map((name, index) => defaultPoseLocation(name, index, names.length, width, height, mode));
  }
  setPosePoints(mode, points);
  state.annotationEdges = (template.edges || []).map(edge => [...edge]);
  state.poseSelectedJoint = null;
  state.poseConnectStart = null;
}

function pose3DWithImageProjection(points3d, points2d) {
  const byName = new Map((points2d || []).map((point, index) => [String(point.name || index), point]));
  return (points3d || []).map((point, index) => {
    const projected = byName.get(String(point.name || index)) || (points2d || [])[index] || {};
    return {
      ...point,
      image_x: Number.isFinite(Number(point.image_x)) ? Number(point.image_x) : Number(projected.x ?? projected.image_x ?? 0),
      image_y: Number.isFinite(Number(point.image_y)) ? Number(point.image_y) : Number(projected.y ?? projected.image_y ?? 0),
    };
  });
}

function applyPoseProposal(proposal, index = 0) {
  if (!proposal) return;
  const metadata = proposal.metadata || {};
  const has3d = (metadata.keypoints_3d || []).length > 0;
  const has2d = (metadata.keypoints_2d || []).length > 0;
  if (has2d) state.annotationPose2D = metadata.keypoints_2d.map(point => ({ ...point }));
  if (has3d) state.annotationPose3D = pose3DWithImageProjection(metadata.keypoints_3d, metadata.keypoints_2d || []);
  state.annotationEdges = (metadata.edges || []).map(edge => [...edge]);
  state.poseTemplate = metadata.skeleton_template || metadata.template || state.poseTemplate || 'custom';
  state.poseProposalIndex = index;
  state.poseSelectedJoint = null;
  state.poseConnectStart = null;
}

function poseOverlayEditor(item, mode) {
  const wrap = el('div', { class: 'annotation-wrap pose-editor-wrap' });
  const img = el('img', { class: 'annotation-image', src: `/api/media/${item.id}/file`, draggable: 'false' });
  const canvas = el('canvas', { class: `annotation-canvas pose-editor-canvas tool-${state.poseTool}` });
  const hud = el('div', { class: 'pose-hud' }, '');
  wrap.append(img, canvas, hud);
  let dragging = null;
  let lastPointer = null;

  function currentPoints() { return posePoints(mode); }
  function displayPoint(point) {
    if (mode === 'pose2d') return { x: Number(point.x || 0), y: Number(point.y || 0) };
    if (Number.isFinite(Number(point.image_x)) && Number.isFinite(Number(point.image_y))) return { x: Number(point.image_x), y: Number(point.image_y) };
    const x = Number(point.x || 0), y = Number(point.y || 0);
    if (Math.abs(x) <= 2.5 && Math.abs(y) <= 2.5) return { x: canvas.width * (.5 + x / 2), y: canvas.height * (.5 - y / 2) };
    return { x, y };
  }
  function updatePointFromDisplay(index, position) {
    const points = currentPoints().map(point => ({ ...point }));
    if (!points[index]) return;
    if (mode === 'pose2d') { points[index].x = position.x; points[index].y = position.y; }
    else {
      const previous = displayPoint(points[index]);
      const display = points.map(displayPoint);
      const worldX = points.map(point => Number(point.x)).filter(Number.isFinite);
      const worldY = points.map(point => Number(point.y)).filter(Number.isFinite);
      const pixelX = display.map(point => Number(point.x)).filter(Number.isFinite);
      const pixelY = display.map(point => Number(point.y)).filter(Number.isFinite);
      const span = values => values.length ? Math.max(...values) - Math.min(...values) : 0;
      const scaleX = span(pixelX) > 1e-6 && span(worldX) > 1e-6 ? span(worldX) / span(pixelX) : 2 / Math.max(1, canvas.width);
      const scaleY = span(pixelY) > 1e-6 && span(worldY) > 1e-6 ? span(worldY) / span(pixelY) : 2 / Math.max(1, canvas.height);
      points[index].x = Number(points[index].x || 0) + (position.x - previous.x) * scaleX;
      points[index].y = Number(points[index].y || 0) - (position.y - previous.y) * scaleY;
      points[index].z = Number(points[index].z || 0);
      points[index].image_x = position.x; points[index].image_y = position.y;
    }
    setPosePoints(mode, points);
  }
  function resize() {
    const rect = img.getBoundingClientRect();
    canvas.width = img.naturalWidth || item.width || Math.max(1, rect.width);
    canvas.height = img.naturalHeight || item.height || Math.max(1, rect.height);
    canvas.style.width = `${rect.width || canvas.width}px`; canvas.style.height = `${rect.height || canvas.height}px`;
    draw();
  }
  function position(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(canvas.width, (event.clientX - rect.left) * canvas.width / Math.max(rect.width, 1))),
      y: Math.max(0, Math.min(canvas.height, (event.clientY - rect.top) * canvas.height / Math.max(rect.height, 1))),
    };
  }
  function nearestJoint(p, radius = Math.max(12, canvas.width / 55)) {
    let best = null, distance = Infinity;
    currentPoints().forEach((point, index) => { const q = displayPoint(point); const d = Math.hypot(q.x - p.x, q.y - p.y); if (d < distance) { best = index; distance = d; } });
    return distance <= radius ? best : null;
  }
  function pointSegmentDistance(p, a, b) {
    const dx = b.x - a.x, dy = b.y - a.y; const length2 = dx * dx + dy * dy;
    if (!length2) return Math.hypot(p.x - a.x, p.y - a.y);
    const t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / length2));
    return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
  }
  function nearestEdge(p) {
    const points = currentPoints(); let best = null, distance = Infinity;
    (state.annotationEdges || []).forEach((edge, edgeIndex) => { const pair = poseEdgeIndices(edge, points); if (!pair) return; const d = pointSegmentDistance(p, displayPoint(points[pair[0]]), displayPoint(points[pair[1]])); if (d < distance) { best = edgeIndex; distance = d; } });
    return distance <= Math.max(10, canvas.width / 70) ? best : null;
  }
  function drawSaved(ctx) {
    if (!state.poseShowSaved) return;
    for (const ann of state.annotationState?.annotations || []) {
      if (!['pose2d','pose3d','animation_pose'].includes(String(ann.annotation_type || '').toLowerCase())) continue;
      if (state.poseLoadedAnnotationId && Number(ann.id) === Number(state.poseLoadedAnnotationId)) continue;
      const meta = ann.metadata || {};
      const points = mode === 'pose2d' ? (meta.keypoints_2d || []) : (meta.keypoints_3d || []);
      if (!points.length) continue;
      ctx.save(); ctx.globalAlpha = .28; ctx.strokeStyle = '#94a3b8'; ctx.fillStyle = '#94a3b8'; ctx.lineWidth = Math.max(1.5, canvas.width / 800);
      for (const edge of meta.edges || []) { const pair = poseEdgeIndices(edge, points); if (!pair) continue; const a = mode === 'pose2d' ? points[pair[0]] : { x: points[pair[0]].image_x ?? points[pair[0]].x, y: points[pair[0]].image_y ?? points[pair[0]].y }; const b = mode === 'pose2d' ? points[pair[1]] : { x: points[pair[1]].image_x ?? points[pair[1]].x, y: points[pair[1]].image_y ?? points[pair[1]].y }; ctx.beginPath(); ctx.moveTo(Number(a.x || 0), Number(a.y || 0)); ctx.lineTo(Number(b.x || 0), Number(b.y || 0)); ctx.stroke(); }
      ctx.restore();
    }
  }
  function draw() {
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    drawSaved(ctx);
    const points = currentPoints(); const pointRadius = Math.max(5, canvas.width / 180); const lineWidth = Math.max(3, canvas.width / 350);
    ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = lineWidth; ctx.shadowColor = 'rgba(0,0,0,.8)'; ctx.shadowBlur = Math.max(2, lineWidth);
    for (const edge of state.annotationEdges || []) {
      const pair = poseEdgeIndices(edge, points); if (!pair) continue;
      const a = displayPoint(points[pair[0]]), b = displayPoint(points[pair[1]]);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    ctx.shadowBlur = 0; ctx.font = `${Math.max(11, Math.round(canvas.width / 90))}px sans-serif`;
    points.forEach((point, index) => {
      const q = displayPoint(point); const selected = state.poseSelectedJoint === index; const connecting = state.poseConnectStart === index;
      ctx.beginPath(); ctx.fillStyle = selected ? '#f97316' : connecting ? '#e879f9' : '#facc15'; ctx.strokeStyle = '#020617'; ctx.lineWidth = Math.max(1.5, pointRadius / 3); ctx.arc(q.x, q.y, selected ? pointRadius * 1.35 : pointRadius, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      const label = `${index}:${point.name || `joint_${index}`}`; const tx = Math.min(canvas.width - 5, q.x + pointRadius + 3), ty = Math.max(12, q.y - pointRadius - 2);
      ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,.85)'; ctx.strokeText(label, tx, ty); ctx.fillStyle = '#f8fafc'; ctx.fillText(label, tx, ty);
    });
    const toolLabels = { move: 'Move joints', add: 'Add joint', connect: 'Connect bones', delete_joint: 'Delete joint', delete_edge: 'Delete bone' };
    hud.textContent = `${toolLabels[state.poseTool] || state.poseTool} · ${points.length} joints · ${(state.annotationEdges || []).length} bones${state.poseSelectedJoint != null ? ` · selected ${state.poseSelectedJoint}` : ''}`;
  }
  canvas.addEventListener('pointerdown', event => {
    event.preventDefault(); canvas.setPointerCapture?.(event.pointerId);
    const p = position(event); const hit = nearestJoint(p); lastPointer = p;
    if (state.poseTool === 'move') {
      if (hit != null) { state.poseSelectedJoint = hit; dragging = hit; }
      else state.poseSelectedJoint = null;
    } else if (state.poseTool === 'add') {
      const points = currentPoints(); const name = String(state.poseNewJointName || '').trim() || `joint_${points.length}`;
      const point = mode === 'pose2d' ? { name, x: p.x, y: p.y, score: 1 } : { name, x: (p.x / canvas.width - .5) * 2, y: (.5 - p.y / canvas.height) * 2, z: 0, image_x: p.x, image_y: p.y, score: 1 };
      setPosePoints(mode, [...points, point]);
      if (state.poseAutoConnect && state.poseSelectedJoint != null) addPoseEdge(state.poseSelectedJoint, points.length);
      state.poseSelectedJoint = points.length; state.poseNewJointName = ''; draw();
    } else if (state.poseTool === 'connect') {
      if (hit == null) return;
      if (state.poseConnectStart == null) { state.poseConnectStart = hit; state.poseSelectedJoint = hit; }
      else { addPoseEdge(state.poseConnectStart, hit); state.poseSelectedJoint = hit; state.poseConnectStart = null; }
    } else if (state.poseTool === 'delete_joint' && hit != null) deletePoseJoint(hit, mode);
    else if (state.poseTool === 'delete_edge') { const edge = nearestEdge(p); if (edge != null) state.annotationEdges = (state.annotationEdges || []).filter((_, index) => index !== edge); }
    draw();
  });
  canvas.addEventListener('pointermove', event => {
    if (dragging == null) return;
    const p = position(event); updatePointFromDisplay(dragging, p); lastPointer = p; draw();
  });
  const stop = event => { dragging = null; lastPointer = null; if (event?.pointerId != null) canvas.releasePointerCapture?.(event.pointerId); draw(); };
  canvas.addEventListener('pointerup', stop); canvas.addEventListener('pointercancel', stop);
  canvas.addEventListener('contextmenu', event => { event.preventDefault(); const hit = nearestJoint(position(event)); if (hit != null) { deletePoseJoint(hit, mode); draw(); } });
  img.addEventListener('load', resize); setTimeout(resize, 0); window.addEventListener('resize', resize, { once: true });
  return wrap;
}

function pose3DInteractiveViewer() {
  const canvas = el('canvas', { class: 'pose3d-canvas pose3d-interactive', width: 720, height: 480 });
  let dragging = null; let last = null; let rotating = false;
  const points = () => state.annotationPose3D || [];
  function rotated(point) {
    const yaw = Number(state.poseViewerYaw || 0), pitch = Number(state.poseViewerPitch || 0);
    const x = Number(point.x || 0), y = Number(point.y || 0), z = Number(point.z || 0);
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = cy * x + sy * z, z1 = -sy * x + cy * z;
    return { x: x1, y: cp * y - sp * z1, z: sp * y + cp * z1 };
  }
  function project(point) { const p = rotated(point), scale = Number(state.poseViewerZoom || 115); return { x: canvas.width / 2 + p.x * scale, y: canvas.height / 2 - p.y * scale, depth: p.z }; }
  function hitTest(position) { let best = null, distance = Infinity; points().forEach((point, index) => { const q = project(point), d = Math.hypot(q.x - position.x, q.y - position.y); if (d < distance) { distance = d; best = index; } }); return distance <= 15 ? best : null; }
  const depth=el('input',{type:'range',min:'-3',max:'3',step:'.01',value:0,disabled:true,oninput:e=>{if(state.poseSelectedJoint==null)return;const pts=points().map(point=>({...point}));pts[state.poseSelectedJoint].z=Number(e.target.value);state.annotationPose3D=pts;draw();}});
  const selectedBadge=el('span',{class:'muted'},'Select a joint to edit depth');
  function drawGrid(ctx) {
    ctx.strokeStyle = 'rgba(148,163,184,.18)'; ctx.lineWidth = 1;
    for (let i = -8; i <= 8; i++) { const offset = i * 32; ctx.beginPath(); ctx.moveTo(canvas.width/2 + offset, 0); ctx.lineTo(canvas.width/2 + offset, canvas.height); ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, canvas.height/2 + offset); ctx.lineTo(canvas.width, canvas.height/2 + offset); ctx.stroke(); }
    ctx.strokeStyle = 'rgba(248,250,252,.45)'; ctx.beginPath(); ctx.moveTo(canvas.width/2, 0); ctx.lineTo(canvas.width/2, canvas.height); ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, canvas.height/2); ctx.lineTo(canvas.width, canvas.height/2); ctx.stroke();
  }
  function draw() {
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0,0,canvas.width,canvas.height); ctx.fillStyle='#05070d'; ctx.fillRect(0,0,canvas.width,canvas.height); drawGrid(ctx);
    const pts = points(); ctx.lineWidth=4; ctx.lineCap='round'; ctx.shadowColor='rgba(0,0,0,.8)'; ctx.shadowBlur=4;
    for (const edge of state.annotationEdges || []) { const pair=poseEdgeIndices(edge,pts); if(!pair) continue; const a=project(pts[pair[0]]), b=project(pts[pair[1]]); const depth=(a.depth+b.depth)/2; ctx.strokeStyle=depth>0?'#22d3ee':'#60a5fa'; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke(); }
    ctx.shadowBlur=0; const order=pts.map((point,index)=>({point,index,q:project(point)})).sort((a,b)=>a.q.depth-b.q.depth);
    for (const row of order) { const selected=state.poseSelectedJoint===row.index; ctx.beginPath(); ctx.fillStyle=selected?'#f97316':'#facc15'; ctx.strokeStyle='#020617'; ctx.lineWidth=2; ctx.arc(row.q.x,row.q.y,selected?9:7,0,Math.PI*2); ctx.fill(); ctx.stroke(); ctx.fillStyle='#f8fafc'; ctx.font='12px sans-serif'; ctx.fillText(`${row.index}:${row.point.name || ''}`,row.q.x+10,row.q.y-8); }
    const selected=state.poseSelectedJoint != null ? pts[state.poseSelectedJoint] : null;
    depth.disabled=!selected;
    if(selected&&document.activeElement!==depth)depth.value=String(Number(selected.z||0));
    selectedBadge.className=selected?'badge':'muted';
    selectedBadge.textContent=selected?(selected.name||`joint ${state.poseSelectedJoint}`):'Select a joint to edit depth';
  }
  function pos(event){ const rect=canvas.getBoundingClientRect(); return {x:(event.clientX-rect.left)*canvas.width/Math.max(rect.width,1),y:(event.clientY-rect.top)*canvas.height/Math.max(rect.height,1)}; }
  canvas.addEventListener('pointerdown', event => { event.preventDefault(); const p=pos(event), hit=hitTest(p); last=p; canvas.setPointerCapture?.(event.pointerId); if(hit!=null){dragging=hit;state.poseSelectedJoint=hit;} else rotating=true; draw(); });
  canvas.addEventListener('pointermove', event => { if(dragging==null&&!rotating)return; const p=pos(event), dx=p.x-last.x, dy=p.y-last.y; last=p; if(rotating){state.poseViewerYaw=Number(state.poseViewerYaw||0)+dx*.008;state.poseViewerPitch=Math.max(-1.45,Math.min(1.45,Number(state.poseViewerPitch||0)+dy*.008));}
    else { const pts=points().map(point=>({...point})), scale=Number(state.poseViewerZoom||115), yaw=Number(state.poseViewerYaw||0), pitch=Number(state.poseViewerPitch||0), cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch); const right={x:cy,y:0,z:sy}, up={x:-sp*sy,y:cp,z:sp*cy}; const point=pts[dragging]; point.x=Number(point.x||0)+(dx/scale)*right.x+(-dy/scale)*up.x; point.y=Number(point.y||0)+(dx/scale)*right.y+(-dy/scale)*up.y; point.z=Number(point.z||0)+(dx/scale)*right.z+(-dy/scale)*up.z; state.annotationPose3D=pts; }
    draw(); });
  const stop=event=>{dragging=null;rotating=false;last=null;canvas.releasePointerCapture?.(event.pointerId);draw();}; canvas.addEventListener('pointerup',stop);canvas.addEventListener('pointercancel',stop);
  canvas.addEventListener('wheel',event=>{event.preventDefault();state.poseViewerZoom=Math.max(35,Math.min(400,Number(state.poseViewerZoom||115)*(event.deltaY>0?.9:1.1)));draw();},{passive:false});
  setTimeout(draw,0);
  return card('Interactive 3D Skeleton Viewer',[
    el('p',{class:'muted'},'Drag a joint to edit its 3D position. Drag empty space to orbit. Scroll to zoom. Bones are redrawn continuously as joints move.'),canvas,
    el('div',{class:'row'},[
      el('button',{class:'secondary small',onclick:()=>{state.poseViewerYaw=0;state.poseViewerPitch=0;draw();}},'Front'),
      el('button',{class:'secondary small',onclick:()=>{state.poseViewerYaw=Math.PI/2;state.poseViewerPitch=0;draw();}},'Side'),
      el('button',{class:'secondary small',onclick:()=>{state.poseViewerYaw=.45;state.poseViewerPitch=-.2;state.poseViewerZoom=115;draw();}},'Reset View'),
      el('label',{class:'label compact'},[`Selected depth (z)`,depth]),selectedBadge
    ])
  ]);
}

function poseToolButton(key,label){return el('button',{class:state.poseTool===key?'primary':'secondary',onclick:()=>{state.poseTool=key;state.poseConnectStart=null;render();}},label);}

function poseSavedTable(rows,item){
  if(!rows.length)return el('p',{class:'muted'},'No pose annotations saved for this image yet.');
  return el('div',{class:'table-scroll'},el('table',{class:'table'},[
    el('thead',{},el('tr',{},['ID','Label','Type','Template','Joints','Bones','Actions'].map(h=>el('th',{},h)))),
    el('tbody',{},rows.map(row=>{const meta=row.metadata||{},pts=row.annotation_type==='pose2d'?(meta.keypoints_2d||[]):(meta.keypoints_3d||[]);return el('tr',{},[
      el('td',{},row.id),el('td',{},row.label||''),el('td',{},row.annotation_type||''),el('td',{},meta.skeleton_template||meta.template||'custom'),el('td',{},pts.length),el('td',{},(meta.edges||[]).length),
      el('td',{},el('div',{class:'row'},[
        el('button',{class:'secondary small',onclick:()=>{state.annotationMode=row.annotation_type==='pose2d'?'pose2d':'pose3d';state.annotationPose2D=(meta.keypoints_2d||[]).map(p=>({...p}));state.annotationPose3D=pose3DWithImageProjection(meta.keypoints_3d||[],meta.keypoints_2d||[]);state.annotationEdges=(meta.edges||[]).map(e=>[...e]);state.poseTemplate=meta.skeleton_template||meta.template||'custom';state.poseLoadedAnnotationId=row.id;state.annotationLabel=row.label||'pose';state.annotationTarget=row.target_name||'';state.poseSelectedJoint=null;toast(`Loaded pose annotation ${row.id} for editing`);render();}},'Load / Edit'),
        el('button',{class:'secondary small',onclick:()=>{navigator.clipboard?.writeText(JSON.stringify(meta,null,2));toast('Pose metadata copied');}},'Copy JSON'),
        el('button',{class:'danger small',onclick:async()=>{try{await api(`/api/reference/annotations/${row.id}`,{method:'DELETE'});if(state.poseLoadedAnnotationId===row.id)state.poseLoadedAnnotationId=null;await loadAnnotationState(item.id);toast('Pose deleted');render();}catch(err){toast(err.message,false);}}},'Delete')
      ]))
    ]);}))
  ]));
}

function customSkeletonBuilderCard() {
  const key=el('input',{value:state.customSkeletonKey||'',placeholder:'template key e.g. quadruped_tail_rig',oninput:e=>state.customSkeletonKey=e.target.value});
  const label=el('input',{value:state.customSkeletonLabel||'',placeholder:'display label',oninput:e=>state.customSkeletonLabel=e.target.value});
  const dimension=el('select',{onchange:e=>state.customSkeletonDimension=e.target.value},['2d','3d','mixed'].map(v=>el('option',{value:v},v))); dimension.value=state.customSkeletonDimension||'mixed';
  const names=el('textarea',{rows:'4',placeholder:'One node/joint name per line. Works for non-humanoid characters, tails, wings, props, vehicles, etc.',oninput:e=>state.customSkeletonNames=e.target.value},state.customSkeletonNames||'');
  const edges=el('textarea',{rows:'5',placeholder:'Edges: from,to,label,group per line\nExample: root,tail_01,tail base,tail',oninput:e=>state.customSkeletonEdges=e.target.value},state.customSkeletonEdges||'');
  function parseNames(){return (names.value||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
  function parseEdges(){return (edges.value||'').split(/\r?\n/).map(line=>line.trim()).filter(Boolean).map((line,idx)=>{const p=line.split(',').map(x=>x.trim());return {from:p[0],to:p[1],label:p[2]||`edge_${idx}`,group:p[3]||'default'};}).filter(e=>e.from&&e.to);}
  return card('Custom Skeleton Templates — Non-humanoid / Arbitrary Rigs',[
    el('p',{class:'muted'},'Create reusable skeleton topologies for animals, creatures, props, vehicles, wings, tails, tentacles, and other non-humanoid shapes. Edges can be labeled individually and grouped for rigging/export.'),
    el('div',{class:'row'},[key,label,dimension]),
    el('div',{class:'grid cols-2'},[names,edges]),
    el('div',{class:'row'},[
      el('button',{class:'secondary',onclick:()=>{const pts=state.annotationPose3D?.length?state.annotationPose3D:state.annotationPose2D||[];names.value=pts.map((p,i)=>p.name||`joint_${i}`).join('\n');state.customSkeletonNames=names.value;edges.value=(state.annotationEdges||[]).map((e,i)=>`${e[0]},${e[1]},edge_${i},custom`).join('\n');state.customSkeletonEdges=edges.value;render();}},'Use Current Pose as Template'),
      el('button',{class:'primary',onclick:async()=>{try{const payload={key:key.value||'custom_skeleton',label:label.value||key.value||'Custom skeleton',dimension:dimension.value,names:parseNames(),edges:parseEdges(),groups:[...new Set(parseEdges().map(e=>e.group))].map(g=>({key:g,label:g}))};const result=await api('/api/reference/annotations/custom-skeletons',{method:'POST',body:payload});state.poseTemplates=await api('/api/reference/annotations/pose-templates');state.poseTemplate=result.template.key;toast(`Saved skeleton template ${result.template.key}`);render();}catch(err){toast(err.message,false);}}},'Save / Update Template')
    ]),
    el('pre',{class:'log'},JSON.stringify({names:parseNames(),edges:parseEdges()},null,2))
  ]);
}

function poseEditorView() {
  const item=activeEditorItem(); const loading=_ensureSpatialEditorItem(item,'Pose & 3D'); if(loading)return loading;
  const rows=(state.annotationState.annotations||[]).filter(row=>['pose2d','pose3d','animation_pose'].includes(String(row.annotation_type||'').toLowerCase()));
  const mode=el('select',{onchange:e=>{state.annotationMode=e.target.value;state.poseSelectedJoint=null;state.poseConnectStart=null;render();}},[
    el('option',{value:'pose2d'},'2D pose overlay'),el('option',{value:'pose3d'},'3D pose + image projection'),el('option',{value:'animation_pose'},'3D animation pose / frames')]);
  mode.value=['pose2d','pose3d','animation_pose'].includes(state.annotationMode)?state.annotationMode:'pose2d';state.annotationMode=mode.value;
  const workingMode=mode.value==='pose2d'?'pose2d':'pose3d';
  const label=el('input',{value:state.annotationLabel||'pose',placeholder:'pose / rig label',oninput:e=>state.annotationLabel=e.target.value});
  const target=el('input',{value:state.annotationTarget||'',placeholder:'character / rig name',oninput:e=>state.annotationTarget=e.target.value});
  const template=el('select',{onchange:e=>{state.poseTemplate=e.target.value;}},(state.poseTemplates||[]).map(row=>el('option',{value:row.key},row.label||row.key)));template.value=state.poseTemplate||'custom';
  const jointName=el('input',{value:state.poseNewJointName||'',placeholder:'next joint name',oninput:e=>state.poseNewJointName=e.target.value});
  const autoConnect=el('input',{type:'checkbox',checked:state.poseAutoConnect,onchange:e=>state.poseAutoConnect=e.target.checked});
  const poseModels=(state.models||[]).filter(row=>{const caps=new Set(row.capabilities||[]);return caps.has('pose')||caps.has('pose2d')||caps.has('pose3d')||caps.has('keypoints')||caps.has('keypoints3d');});
  if(state.poseModel&&!poseModels.some(row=>row.name===state.poseModel))state.poseModel='';
  if(!state.poseModel&&poseModels.length)state.poseModel=(workingMode==='pose3d'?poseModels.find(row=>(row.capabilities||[]).includes('pose3d')):poseModels.find(row=>(row.capabilities||[]).includes('pose2d')))?.name||poseModels[0].name;
  const poseModel=el('select',{onchange:e=>{state.poseModel=e.target.value;state.poseModelStatus=null;}},[el('option',{value:''},'Select pose inference model'),...poseModels.map(row=>el('option',{value:row.name},`${modelLabel(row)} · ${(row.capabilities||[]).join(', ')}`))]);poseModel.value=state.poseModel||'';
  const selectedModel=poseModels.find(row=>row.name===poseModel.value)||null;
  const localPath=el('input',{value:state.poseLocalModelPath||'',placeholder:'optional custom MMPose config/checkpoint or MediaPipe .task path',style:'min-width:420px',oninput:e=>state.poseLocalModelPath=e.target.value});
  const customType=el('select',{onchange:e=>state.poseCustomModelType=e.target.value},['auto','mediapipe','mmpose','pose2d','pose3d'].map(value=>el('option',{value},value)));customType.value=state.poseCustomModelType||'auto';
  const proposals=state.poseProposals||[];
  const proposalSelect=el('select',{onchange:e=>{state.poseProposalIndex=Number(e.target.value);applyPoseProposal(proposals[state.poseProposalIndex],state.poseProposalIndex);render();}},proposals.map((proposal,index)=>el('option',{value:index},`Pose ${index+1} · ${(Number(proposal.confidence||0)*100).toFixed(1)}% · ${proposal.annotation_type||''}`)));proposalSelect.value=String(Math.min(state.poseProposalIndex||0,Math.max(0,proposals.length-1)));
  const jsonText=JSON.stringify({keypoints_2d:state.annotationPose2D||[],keypoints_3d:state.annotationPose3D||[],edges:state.annotationEdges||[],skeleton_template:state.poseTemplate||'custom',image_width:item.width,image_height:item.height},null,2);

  async function savePose(asNew=false){
    const points=posePoints(workingMode); if(!points.length)throw new Error('Create or infer at least one joint first.');
    const metadata={keypoints_2d:state.annotationPose2D||[],keypoints_3d:state.annotationPose3D||[],edges:state.annotationEdges||[],skeleton_template:state.poseTemplate||'custom',coordinate_space:workingMode==='pose2d'?'image_pixels':'world_3d+image_projection',image_width:item.width||null,image_height:item.height||null};
    const body={media_id:item.id,label:label.value||'pose',target_name:target.value||'',annotation_type:mode.value,source:'user',model_key:state.poseModel||'',metadata};
    if(state.poseLoadedAnnotationId&&!asNew){await api(`/api/spatial/layers/${state.poseLoadedAnnotationId}`,{method:'PATCH',body:{label:body.label,target_name:body.target_name,annotation_type:body.annotation_type,metadata:body.metadata,model_key:body.model_key,source:'user',force:true}});toast(`Pose annotation ${state.poseLoadedAnnotationId} updated`);}
    else {const result=await api('/api/reference/annotations',{method:'POST',body});state.poseLoadedAnnotationId=result.id||result.annotation_id;toast('Pose annotation saved');}
    await loadAnnotationState(item.id);render();
  }

  return el('div',{class:'grid'},[
    card('Pose Editor — Visible Bones and Drag-editable Joints',[
      editorQueueControls(item),
      el('p',{class:'muted'},'Bones are rendered before joint nodes, so topology remains visible. Select Move and drag any node over the image; every connected edge is recomputed on each pointer movement.'),
      el('div',{class:'row'},[label,target,mode,template,el('button',{class:'secondary',onclick:()=>{applyPoseTemplate(item,true);toast(`Applied ${poseTemplateRecord(state.poseTemplate).label}`);render();}},'Create / Apply Skeleton Template'),el('label',{class:'row'},[autoConnect,'Auto-connect new joint'])]),
      el('div',{class:'pose-toolbar'},[poseToolButton('move','Move / Select'),poseToolButton('add','Add Joint'),poseToolButton('connect','Connect Bones'),poseToolButton('delete_joint','Delete Joint'),poseToolButton('delete_edge','Delete Bone'),jointName,
        el('button',{class:'secondary',onclick:()=>{if(state.poseSelectedJoint==null)return toast('Select a joint first.',false);const points=posePoints(workingMode).map(p=>({...p}));points[state.poseSelectedJoint].name=prompt('Joint name',points[state.poseSelectedJoint].name||`joint_${state.poseSelectedJoint}`)||points[state.poseSelectedJoint].name;setPosePoints(workingMode,points);render();}},'Rename Selected'),
        el('button',{class:'secondary',onclick:()=>{const points=posePoints(workingMode);if(state.poseSelectedJoint==null||!points.length)return;deletePoseJoint(state.poseSelectedJoint,workingMode);render();}},'Delete Selected'),
        el('button',{class:'secondary',onclick:()=>{state.annotationEdges=[];state.poseConnectStart=null;render();}},'Clear Bones'),
        el('button',{class:'danger',onclick:()=>{setPosePoints(workingMode,[]);state.annotationEdges=[];state.poseSelectedJoint=null;state.poseLoadedAnnotationId=null;render();}},'Clear Current Pose')
      ]),
      poseOverlayEditor(item,workingMode),
      el('p',{class:'muted'},'Right-click a node to delete it. In Connect Bones mode, click the first joint and then the second. In Delete Bone mode, click close to an edge.')
    ]),
    workingMode==='pose3d'?pose3DInteractiveViewer():null,
    card('Pose Inference Models — 2D and 3D',[
      el('p',{class:'muted'},'Available backends include YOLO pose, MediaPipe BlazePose (2D + world 3D), MMPose RTMPose/ViTPose/WholeBody/Animal, MotionBERT 3D human pose, InterNet 3D hand pose, and custom MMPose checkpoints.'),
      el('div',{class:'row'},[poseModel,localPath,customType]),
      el('div',{class:'row'},[
        el('button',{class:'secondary',disabled:!selectedModel,onclick:async()=>{try{const family=(selectedModel?.provider==='mmpose'||String(selectedModel?.name||'').startsWith('mmpose-'))?'mmpose':selectedModel?.provider==='mediapipe'||String(selectedModel?.name||'').startsWith('mediapipe-')?'mediapipe':'ultralytics';const result=await api('/api/reference/annotations/install-pose-deps',{method:'POST',body:{family,extra_args:[]}});state.threeDLastJob=result.job_id;state.lastModelRunJob=result.job_id;toast(`${family} runtime install queued as job ${result.job_id}. Staying here; open Jobs for full logs.`);await refreshAll();render();}catch(err){toast(err.message,false);}}},'Install Selected Pose Runtime'),
        el('button',{class:'secondary',onclick:async()=>{try{const result=await api('/api/reference/annotations/install-pose-deps',{method:'POST',body:{family:'basic',extra_args:[]}});state.lastModelRunJob=result.job_id;toast(`Basic pose runtimes queued as job ${result.job_id}. MMPose is optional/separate.`);await refreshAll();render();}catch(err){toast(err.message,false);}}},'Install Basic Pose Runtimes'),
        el('button',{class:'secondary',disabled:!selectedModel?.download_supported,onclick:async()=>{try{const result=await api('/api/reference/annotations/download-model',{method:'POST',body:{model_key:selectedModel.name,dry_run:false,force_download:false,parallel_downloads:modelDownloadWorkerCount()}});state.lastModelRunJob=result.job_id;toast(`Weights download queued as job ${result.job_id}. Staying here.`);await refreshAll();render();}catch(err){toast(err.message,false);}}},selectedModel?.downloaded?'Update Weights':'Download Weights'),
        el('button',{class:'secondary',disabled:!selectedModel,onclick:async()=>{try{const params=new URLSearchParams({model_key:selectedModel.name});if(localPath.value)params.set('local_model_path',localPath.value);if(customType.value)params.set('custom_model_type',customType.value);state.poseModelStatus=await api(`/api/reference/annotations/model-status?${params}`);toast(state.poseModelStatus.available?'Pose model is ready':'Pose model is not ready',Boolean(state.poseModelStatus.available));render();}catch(err){toast(err.message,false);}}},'Check Status'),
        el('button',{class:'secondary',disabled:!selectedModel,onclick:async()=>{try{state.poseModelStatus=await api('/api/reference/annotations/load-model',{method:'POST',body:{model_key:selectedModel.name,device:'auto',options:{local_model_path:localPath.value||'',custom_model_type:customType.value||'auto'}}});toast('Pose model validated and marked loaded');render();}catch(err){toast(err.message,false);}}},'Load / Validate'),
        el('button',{class:'primary',disabled:!selectedModel,onclick:async()=>{try{state.poseModelOutput=await api('/api/reference/annotations/propose',{method:'POST',body:{media_id:item.id,label:label.value||'pose',target_name:target.value||'',prompt:'estimate all visible subject poses',model_key:selectedModel.name,threshold:.2,annotation_type:mode.value,save:false,device:'auto',options:{local_model_path:localPath.value||'',custom_model_type:customType.value||'auto',max_proposals:32}}});if(!state.poseModelOutput.ok)throw new Error(state.poseModelOutput.error||'Pose inference failed');state.poseProposals=state.poseModelOutput.proposals||[];state.poseProposalIndex=0;if(state.poseProposals.length)applyPoseProposal(state.poseProposals[0],0);toast(`Loaded ${state.poseProposals.length} pose proposal(s)`);render();}catch(err){toast(err.message,false);}}},'Run Pose Inference')
      ]),
      proposals.length?el('div',{class:'row'},[proposalSelect,el('button',{class:'secondary',onclick:()=>{applyPoseProposal(proposals[Number(proposalSelect.value)||0],Number(proposalSelect.value)||0);render();}},'Apply Selected Proposal'),el('span',{class:'badge'},`${proposals.length} detected pose(s)`) ]):el('p',{class:'muted'},'Run inference to populate editable pose proposals.'),
      el('pre',{class:'log'},JSON.stringify(state.poseModelStatus||selectedModel||{},null,2))
    ]),
    card('Save / Update Pose Dataset Annotation',[
      el('div',{class:'row'},[
        el('button',{class:'primary',onclick:async()=>{try{await savePose(false);}catch(err){toast(err.message,false);}}},state.poseLoadedAnnotationId?`Update Annotation #${state.poseLoadedAnnotationId}`:'Save Pose Annotation'),
        el('button',{class:'secondary',onclick:async()=>{try{await savePose(true);}catch(err){toast(err.message,false);}}},'Save as New Annotation'),
        el('button',{class:'secondary',onclick:()=>{state.poseLoadedAnnotationId=null;toast('Next save will create a new annotation');render();}},'Detach from Loaded Annotation'),
        el('label',{class:'row'},[el('input',{type:'checkbox',checked:state.poseShowSaved,onchange:e=>{state.poseShowSaved=e.target.checked;render();}}),'Ghost saved poses'])
      ]),
      el('details',{},[el('summary',{},'Current pose JSON'),el('pre',{class:'log'},jsonText)])
    ]),
    customSkeletonBuilderCard(),
    card('Blender Pose and Rig Bridge',[
      el('p',{class:'muted'},'The Blender add-on can fetch this saved pose into an armature, send edited bones back, import the latest generated asset, and queue generation or automatic rigging jobs.'),
      el('div',{class:'row'},[el('span',{class:'badge'},`Media ID: ${item.id}`),state.poseLoadedAnnotationId?el('span',{class:'badge'},`Annotation ID: ${state.poseLoadedAnnotationId}`):null,el('a',{href:'/api/blender/plugin',target:'_blank'},'Download Blender Bridge v0.4'),el('button',{class:'secondary',onclick:()=>{navigator.clipboard?.writeText(String(item.id));toast('Media ID copied');}},'Copy Media ID'),el('button',{class:'secondary',onclick:()=>setTab('3D Studio')},'Open 3D Generation / Rigging Studio')].filter(Boolean))
    ]),
    card('Saved Pose Annotations',[poseSavedTable(rows,item)]),
    card('Pose Inference Result JSON',[el('pre',{class:'log'},JSON.stringify(state.poseModelOutput||{},null,2))])
  ].filter(Boolean));
}

function vecProject3D(p, mode, width, height, yaw, pitch, zoom) {
  const x = Number(p?.[0] ?? p?.x ?? 0), y = Number(p?.[1] ?? p?.y ?? 0), z = Number(p?.[2] ?? p?.z ?? 0);
  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  const rx = x * cy - z * sy;
  const rz = x * sy + z * cy;
  const ry = y * cp - rz * sp;
  const rz2 = y * sp + rz * cp;
  const scale = zoom / Math.max(0.25, 4 + rz2 * 0.15);
  return [width / 2 + rx * scale, height / 2 - ry * scale, rz2];
}

function viewportBounds(meshes) {
  let min=[Infinity,Infinity,Infinity], max=[-Infinity,-Infinity,-Infinity];
  for (const mesh of meshes || []) for (const v of mesh.vertices || []) for (let i=0;i<3;i++){ const n=Number(v[i]||0); min[i]=Math.min(min[i],n); max[i]=Math.max(max[i],n); }
  if (!isFinite(min[0])) return {center:[0,0,0], scale:1};
  const center=[(min[0]+max[0])/2,(min[1]+max[1])/2,(min[2]+max[2])/2];
  const span=Math.max(max[0]-min[0],max[1]-min[1],max[2]-min[2],1e-6);
  return {center, scale:2.5/span};
}

function normalizedVertices(meshes) {
  const b=viewportBounds(meshes);
  return (meshes||[]).map(mesh=>({ ...mesh, vertices:(mesh.vertices||[]).map(v=>[(Number(v[0]||0)-b.center[0])*b.scale,(Number(v[1]||0)-b.center[1])*b.scale,(Number(v[2]||0)-b.center[2])*b.scale]) }));
}

function drawDct3DViewport(canvas, payload, mode) {
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W=canvas.width, H=canvas.height;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle = '#070b12'; ctx.fillRect(0,0,W,H);
  ctx.strokeStyle = '#1f2937'; ctx.lineWidth = 1;
  for (let x=0;x<W;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for (let y=0;y<H;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  const yaw=Number(state.threeDViewportYaw||0.65), pitch=Number(state.threeDViewportPitch||-0.25), zoom=Number(state.threeDViewportZoom||220);
  const meshes=normalizedVertices(payload?.meshes || []);
  if (mode === 'uv' || mode === 'uv_topology') {
    ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 1;
    for (const mesh of payload?.meshes || []) for (const face of mesh.uvs || []) { if (face.length < 3) continue; ctx.beginPath(); face.forEach((uv,i)=>{ const x=Number(uv[0]||0)*W; const y=(1-Number(uv[1]||0))*H; if(i)ctx.lineTo(x,y); else ctx.moveTo(x,y); }); ctx.closePath(); ctx.stroke(); }
    ctx.fillStyle='#cbd5e1'; ctx.fillText('UV topology mode',12,20); return;
  }
  const drawFace = (verts, face, fill, stroke) => { const pts=face.map(i=>vecProject3D(verts[i],mode,W,H,yaw,pitch,zoom)); if(pts.length<3||pts.some(p=>!isFinite(p[0])))return; ctx.beginPath(); pts.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])); ctx.closePath(); if(fill){ctx.fillStyle=fill;ctx.fill();} if(stroke){ctx.strokeStyle=stroke;ctx.stroke();} };
  for (const mesh of meshes) {
    const verts=mesh.vertices||[];
    const faces=(mesh.faces||[]).slice(0,40000);
    if (mode === 'wireframe') { ctx.lineWidth=0.7; faces.forEach(f=>drawFace(verts,f,null,'#7dd3fc')); }
    else { ctx.lineWidth=0.35; faces.forEach((f,idx)=>{ const shade=90+(idx%80); drawFace(verts,f,`rgba(${shade},${shade+40},${shade+75},0.38)`, (mode==='rendered'||mode==='material')?'rgba(230,240,255,0.18)':null); }); }
    if (mode === 'normals') { ctx.strokeStyle='#f97316'; ctx.lineWidth=1; faces.slice(0,3000).forEach((f,idx)=>{ const pts=f.map(i=>verts[i]); if(pts.length<3)return; const c=[(pts[0][0]+pts[1][0]+pts[2][0])/3,(pts[0][1]+pts[1][1]+pts[2][1])/3,(pts[0][2]+pts[1][2]+pts[2][2])/3]; const n=(mesh.normals||[])[idx]||[0,0,1]; const a=vecProject3D(c,mode,W,H,yaw,pitch,zoom), b=vecProject3D([c[0]+n[0]*0.06,c[1]+n[1]*0.06,c[2]+n[2]*0.06],mode,W,H,yaw,pitch,zoom); ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke(); }); }
  }
  if (['bones','rendered','material','shaded','wireframe'].includes(mode)) {
    for (const arm of payload?.armatures || []) {
      ctx.strokeStyle='#facc15'; ctx.fillStyle='#fde68a'; ctx.lineWidth=2;
      for (const bone of arm.bones || []) { const h=vecProject3D(bone.head,mode,W,H,yaw,pitch,zoom), t=vecProject3D(bone.tail,mode,W,H,yaw,pitch,zoom); ctx.beginPath(); ctx.moveTo(h[0],h[1]); ctx.lineTo(t[0],t[1]); ctx.stroke(); ctx.beginPath(); ctx.arc(h[0],h[1],3,0,Math.PI*2); ctx.fill(); ctx.fillText(bone.name||'', h[0]+5, h[1]-5); }
    }
  }
  ctx.fillStyle='#cbd5e1'; ctx.font='12px sans-serif'; ctx.fillText(`${payload?.source_format||'asset'} · ${(payload?.meshes||[]).length} mesh(es) · ${(payload?.armatures||[]).length} armature(s) · mode: ${mode}`,12,20);
}

function threeDViewportView() {
  const assets=state.threeDAssets||[];
  if(!state.threeDSelectedAsset&&assets.length)state.threeDSelectedAsset=assets[0].path;
  const assetSelect=el('select',{onchange:e=>{state.threeDSelectedAsset=e.target.value;render();}},[el('option',{value:''},'Select 3D asset'),...assets.map(asset=>el('option',{value:asset.path},`${asset.name} · ${asset.format}`))]); assetSelect.value=state.threeDSelectedAsset||'';
  const pathInput=el('input',{value:state.threeDViewportPath||'',placeholder:'or paste .blend/.obj/.fbx/.glb/.ply/.stl/.usd path',style:'min-width:420px',oninput:e=>state.threeDViewportPath=e.target.value});
  const blenderExe=el('input',{value:state.threeDBlenderExecutable||'',placeholder:'Blender executable path for .blend/.fbx conversion',style:'min-width:360px',oninput:e=>state.threeDBlenderExecutable=e.target.value});
  const mode=el('select',{onchange:e=>{state.threeDViewportMode=e.target.value;render();}},['shaded','wireframe','uv_topology','normals','bones','material','rendered'].map(m=>el('option',{value:m},m))); mode.value=state.threeDViewportMode||'shaded';
  const canvas=el('canvas',{width:'960',height:'560',class:'viewport3d'});
  let dragging=false,last=null;
  canvas.addEventListener('pointerdown',e=>{dragging=true;last=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!dragging)return;const dx=e.clientX-last[0],dy=e.clientY-last[1];last=[e.clientX,e.clientY];state.threeDViewportYaw=Number(state.threeDViewportYaw||0.65)+dx*0.01;state.threeDViewportPitch=Number(state.threeDViewportPitch||-0.25)+dy*0.01;drawDct3DViewport(canvas,state.threeDViewportPayload,mode.value);});
  canvas.addEventListener('pointerup',e=>{dragging=false;});
  canvas.addEventListener('wheel',e=>{e.preventDefault();state.threeDViewportZoom=Math.max(40,Math.min(1200,Number(state.threeDViewportZoom||220)*(e.deltaY>0?0.9:1.1)));drawDct3DViewport(canvas,state.threeDViewportPayload,mode.value);},{passive:false});
  setTimeout(()=>drawDct3DViewport(canvas,state.threeDViewportPayload,mode.value),0);
  return el('div',{class:'grid'},[
    card('3D Viewport',[
      el('p',{class:'muted'},'Load .OBJ directly, or use Blender to convert .BLEND/.FBX/.GLB/.GLTF/.PLY/.STL/.USD assets into a lightweight viewport payload. Drag to orbit, mouse-wheel to zoom.'),
      el('div',{class:'row'},[assetSelect,pathInput,mode]),
      el('div',{class:'row'},[blenderExe,el('button',{class:'secondary',onclick:async()=>{try{state.threeDAssets=await api('/api/three-d/assets');toast('3D asset library refreshed');render();}catch(err){toast(err.message,false);}}},'Refresh Asset Library')]),
      el('div',{class:'row'},[
        el('button',{class:'primary',onclick:async()=>{try{const result=await api('/api/three-d/viewport/prepare',{method:'POST',body:{asset_path:assetSelect.value||pathInput.value,path:pathInput.value,blender_executable:blenderExe.value,include_payload:true}});state.threeDViewportPayload=result.payload;state.threeDViewportResult=result;toast(`Loaded viewport payload: ${result.mesh_count} mesh(es), ${result.armature_count} armature(s)`);render();}catch(err){toast(err.message,false);}}},'Load / Convert into Viewport'),
        el('button',{class:'secondary',onclick:()=>{state.threeDViewportYaw=0;state.threeDViewportPitch=0;state.threeDViewportZoom=220;render();}},'Front View'),
        el('button',{class:'secondary',onclick:()=>{state.threeDViewportYaw=Math.PI/2;state.threeDViewportPitch=0;state.threeDViewportZoom=220;render();}},'Side View'),
        el('button',{class:'secondary',onclick:()=>{state.threeDViewportYaw=0.65;state.threeDViewportPitch=-0.25;render();}},'Perspective')
      ]), canvas
    ]),
    card('Viewport Data / Rig Inspection',[el('p',{class:'muted'},'Armature bones, node labels, edge/group names, material names, UV topology, normals, and object inventory are retained in the viewer payload for rigging/debugging.'), el('pre',{class:'log'},JSON.stringify(state.threeDViewportResult||{},null,2))])
  ]);
}

function comfyBridgeView() {
  const selectedId=[...state.selected][0] || state.activeMedia?.id || '';
  const mediaId=el('input',{type:'number',value:selectedId,placeholder:'media id',style:'width:110px'});
  return el('div',{class:'grid'},[
    card('ComfyUI Bridge',[
      el('p',{class:'muted'},'Install the optional DCT custom nodes in ComfyUI to send generated media, masks, metadata JSON, tag strings, captions, and LoRA metadata to/from this tool. The old source node names are intentionally not exposed.'),
      el('div',{class:'row'},[
        el('a',{href:'/api/comfy/nodes/package',target:'_blank',class:'button-link'},'Download DCT ComfyUI Nodes'),
        el('button',{class:'secondary',onclick:async()=>{try{state.comfyStatus=await api('/api/comfy/status');toast('Comfy bridge status refreshed');render();}catch(err){toast(err.message,false);}}},'Check Bridge Status'),
        el('button',{class:'secondary',onclick:async()=>{try{state.comfyWorkflows=await api('/api/comfy/workflows');toast('Workflow templates written');render();}catch(err){toast(err.message,false);}}},'Write Workflow Templates')
      ]),
      el('pre',{class:'log'},JSON.stringify(state.comfyStatus||{},null,2))
    ]),
    card('Send Selected Media to ComfyUI Handoff',[
      el('p',{class:'muted'},'Creates a safe copy and manifest with tags/captions/metadata that a ComfyUI workflow can load through the DCT Receive Media Package node.'),
      el('div',{class:'row'},[mediaId,el('button',{class:'primary',onclick:async()=>{try{if(!mediaId.value)throw new Error('Choose a media id.');state.comfyMediaPackage=await api(`/api/comfy/media/package/${Number(mediaId.value)}`,{method:'POST'});toast('Comfy handoff package created');render();}catch(err){toast(err.message,false);}}},'Create Handoff Manifest')]),
      state.comfyMediaPackage?el('pre',{class:'log'},JSON.stringify(state.comfyMediaPackage,null,2)):el('p',{class:'muted'},'No handoff created yet.')
    ]),
    card('ComfyUI Webhook Endpoints',[el('pre',{class:'log'},`POST /api/comfy/receive\nPOST /api/comfy/receive-file\nPOST /api/comfy/metadata/extract\nPOST /api/comfy/media/package/{media_id}\nGET  /api/comfy/nodes/package\nGET  /api/comfy/workflows`)])
  ]);
}

function threeDStudioView() {
  const item=activeEditorItem()||state.media.items?.[0]||null;
  const generation=state.threeDProviders?.generation||[], rigging=state.threeDProviders?.rigging||[];
  if(state.threeDProvider&&!generation.some(row=>row.key===state.threeDProvider))state.threeDProvider=generation[0]?.key||'';
  if(state.threeDRigProvider&&!rigging.some(row=>row.key===state.threeDRigProvider))state.threeDRigProvider=rigging[0]?.key||'';
  const provider=el('select',{onchange:e=>{state.threeDProvider=e.target.value;const row=generation.find(p=>p.key===e.target.value);if(row?.default_endpoint)state.threeDEndpoint=row.default_endpoint;render();}},generation.map(row=>el('option',{value:row.key},`${row.label}${row.vram_gb?` · ~${row.vram_gb} GB VRAM`:''}`)));provider.value=state.threeDProvider||'';
  const selectedProvider=generation.find(row=>row.key===provider.value)||{};
  const sourcePath=el('input',{value:state.threeDInputPath||'',placeholder:'input image path (blank uses current media)',style:'min-width:360px',oninput:e=>state.threeDInputPath=e.target.value});
  const multiImagePaths=el('textarea',{rows:'3',placeholder:'multi-image / multiview reference paths, one per line. Used by Meshy/Tripo/Rodin/Hunyuan/generic multi-image providers.',style:'width:100%',oninput:e=>state.threeDMultiImagePaths=e.target.value},state.threeDMultiImagePaths||'');
  const videoPath=el('input',{value:state.threeDVideoPath||'',placeholder:'optional video/turntable path for video-to-3D providers',style:'min-width:360px',oninput:e=>state.threeDVideoPath=e.target.value});
  const promptInput=el('textarea',{rows:'3',placeholder:'text prompt; required for text-to-3D providers and optional guidance for image/multi-image/video providers',oninput:e=>state.threeDPrompt=e.target.value},state.threeDPrompt||'');
  const negativePrompt=el('textarea',{rows:'2',placeholder:'optional negative prompt / exclusions for cloud or generic providers',oninput:e=>state.threeDNegativePrompt=e.target.value},state.threeDNegativePrompt||'');
  const generationRepo=el('input',{value:state.threeDRepoPath||'',placeholder:'cloned generation-provider repository path',style:'min-width:420px',oninput:e=>state.threeDRepoPath=e.target.value});
  const rigRepo=el('input',{value:state.threeDRigRepoPath||state.threeDRepoPath||'',placeholder:'cloned UniRig repository path',style:'min-width:420px',oninput:e=>state.threeDRigRepoPath=e.target.value});
  const endpoint=el('input',{value:state.threeDEndpoint||selectedProvider.default_endpoint||'',placeholder:'API endpoint',style:'min-width:420px',oninput:e=>state.threeDEndpoint=e.target.value});
  const apiKey=el('input',{type:'password',value:state.threeDApiKey||'',placeholder:'API key (kept in this browser state only)',style:'min-width:320px',oninput:e=>state.threeDApiKey=e.target.value});
  const tokenProfile=el('input',{value:state.threeDTokenProfile||'',placeholder:'token/API-key profile name, e.g. openrouter:default or meshy:personal',style:'min-width:300px',oninput:e=>state.threeDTokenProfile=e.target.value});
  const apiModelId=el('input',{value:state.threeDApiModelId||'',placeholder:'cloud/provider model id, e.g. deepseek/deepseek-v4-pro or provider 3D model',style:'min-width:360px',oninput:e=>state.threeDApiModelId=e.target.value});
  const contextShrinker=el('input',{value:state.threeDContextShrinkerModel||'',placeholder:'context shrinking model for cloud prompts, e.g. openrouter:auto',style:'min-width:340px',oninput:e=>state.threeDContextShrinkerModel=e.target.value});
  const providerRoute=el('textarea',{rows:'2',placeholder:'optional provider route JSON, e.g. {"allow_fallbacks":true,"order":["DeepInfra"]}',style:'width:100%',oninput:e=>state.threeDProviderRouteJson=e.target.value},state.threeDProviderRouteJson||'');
  const targetFormats=el('input',{value:state.threeDTargetFormats||state.threeDOutputFormat||'glb',placeholder:'target formats: glb,fbx,obj,usdz,stl',style:'min-width:260px',oninput:e=>state.threeDTargetFormats=e.target.value});
  const outputFormat=el('select',{onchange:e=>{state.threeDOutputFormat=e.target.value;if(!targetFormats.value.trim())targetFormats.value=e.target.value;}},['glb','fbx','obj','usdz','stl','ply'].map(value=>el('option',{value},value.toUpperCase())));outputFormat.value=state.threeDOutputFormat||'glb';
  const assets=state.threeDAssets||[];
  if(!state.threeDSelectedAsset&&assets.length)state.threeDSelectedAsset=assets[0].path;
  const assetSelect=el('select',{onchange:e=>state.threeDSelectedAsset=e.target.value},[el('option',{value:''},'Select generated/imported 3D asset'),...assets.map(asset=>el('option',{value:asset.path},`${asset.name} · ${(asset.size_bytes/1048576).toFixed(1)} MB · ${asset.metadata?.provider||'asset'}`))]);assetSelect.value=state.threeDSelectedAsset||'';
  const rigProvider=el('select',{onchange:e=>state.threeDRigProvider=e.target.value},rigging.map(row=>el('option',{value:row.key},row.label)));rigProvider.value=state.threeDRigProvider||'';
  const blenderExe=el('input',{value:state.threeDBlenderExecutable||'',placeholder:'Blender executable path (blank = blender on PATH)',style:'min-width:360px',oninput:e=>state.threeDBlenderExecutable=e.target.value});
  const importPath=el('input',{placeholder:'existing .glb/.fbx/.obj/.ply/.stl/.usd/.vrm path',style:'min-width:420px'});
  const poseRows=(state.annotationState?.annotations||[]).filter(row=>['pose3d','animation_pose'].includes(String(row.annotation_type||'').toLowerCase()));
  const poseAnnotation=el('select',{},[el('option',{value:''},'Latest 3D pose for current media / basic fallback rig'),...poseRows.map(row=>el('option',{value:row.id},`Annotation ${row.id} · ${row.label||row.annotation_type}`))]);

  async function queueGeneration(dryRun){
    let route = {};
    if (providerRoute.value.trim()) {
      try { route = JSON.parse(providerRoute.value); } catch (err) { throw new Error('Provider route JSON is invalid: ' + err.message); }
    }
    const body={
      provider:provider.value,
      media_id:(!sourcePath.value.trim()&&!videoPath.value.trim()&&item)?item.id:null,
      input_path:sourcePath.value.trim(),
      multi_image_paths:multiImagePaths.value,
      video_path:videoPath.value.trim(),
      prompt:promptInput.value.trim(),
      negative_prompt:negativePrompt.value.trim(),
      repo_path:generationRepo.value.trim(),
      endpoint:endpoint.value.trim(),
      api_key:apiKey.value,
      token_profile:tokenProfile.value.trim(),
      api_model_id:apiModelId.value.trim(),
      ai_model:apiModelId.value.trim(),
      model_context_shrinker:contextShrinker.value.trim(),
      context_shrinker_model:contextShrinker.value.trim(),
      provider_route:route,
      output_format:outputFormat.value,
      target_formats:parseTagString(targetFormats.value).length?parseTagString(targetFormats.value):[outputFormat.value],
      dry_run:dryRun,texture:true,remove_background:true,seed:1234,options:{enable_pbr:true}
    };
    const result=await api('/api/three-d/generate',{method:'POST',body});state.threeDLastJob=result.job_id;toast(`${dryRun?'3D dry-run':'3D generation'} queued as job ${result.job_id}`);setTab('Jobs');
  }
  async function queueRig(dryRun){
    if(!assetSelect.value)throw new Error('Select a 3D asset first.');
    const body={provider:rigProvider.value,asset_path:assetSelect.value,repo_path:rigRepo.value.trim(),blender_executable:blenderExe.value.trim(),output_format:'glb',media_id:item?.id||null,annotation_id:poseAnnotation.value?Number(poseAnnotation.value):null,automatic_weights:true,skeleton_only:false,dry_run:dryRun,options:{}};
    const result=await api('/api/three-d/rig',{method:'POST',body});state.threeDLastJob=result.job_id;toast(`${dryRun?'Rigging dry-run':'Automatic rigging'} queued as job ${result.job_id}`);setTab('Jobs');
  }
  const assetTable=assets.length?el('div',{class:'table-scroll'},el('table',{class:'table'},[
    el('thead',{},el('tr',{},['Asset','Provider','Format','Size','Modified','Actions'].map(h=>el('th',{},h)))),
    el('tbody',{},assets.map(asset=>el('tr',{},[
      el('td',{class:'path'},asset.name),el('td',{},asset.metadata?.provider||''),el('td',{},String(asset.format||'').toUpperCase()),el('td',{},`${(Number(asset.size_bytes||0)/1048576).toFixed(1)} MB`),el('td',{class:'tiny'},asset.modified_at||''),
      el('td',{},el('div',{class:'row'},[
        asset.download_url?el('a',{href:asset.download_url,target:'_blank'},'Download'):null,
        el('button',{class:'secondary small',onclick:()=>{state.threeDSelectedAsset=asset.path;toast('Selected as rigging input');render();}},'Rig This'),
        el('button',{class:'secondary small',onclick:async()=>{try{await api('/api/three-d/open-in-blender',{method:'POST',body:{asset_path:asset.path,blender_executable:blenderExe.value.trim()}});toast('Blender launch requested');}catch(err){toast(err.message,false);}}},'Open in Blender'),
        el('button',{class:'secondary small',onclick:()=>{navigator.clipboard?.writeText(asset.path);toast('Asset path copied');}},'Copy Path'),
        el('button',{class:'secondary small',onclick:()=>{state.threeDSelectedAsset=asset.path;state.threeDViewportPath=asset.path;setTab('3D Viewport');}},'View 3D')
      ].filter(Boolean)))
    ])))
  ])):el('p',{class:'muted'},'No managed 3D assets yet. Generate or import one below.');

  return el('div',{class:'grid'},[
    card('3D Generation Studio',[
      el('p',{class:'muted'},'Generate real 3D assets from the current image, a local image path, or a text prompt. Local repository adapters execute the official provider entry points; API adapters submit and poll provider tasks.'),
      item?el('div',{class:'row'},[el('img',{src:`/api/media/${item.id}/thumbnail`,class:'thumb small'}),el('span',{class:'badge'},`Current source media ${item.id}: ${item.relative_path||item.path}`)]):null,
      el('div',{class:'row'},[provider,outputFormat,targetFormats,sourcePath,videoPath]),promptInput,negativePrompt,
      el('details',{},[el('summary',{},'Multi-image / video / cloud-provider options'), multiImagePaths, el('div',{class:'row'},[generationRepo,endpoint,apiKey]), el('div',{class:'row'},[tokenProfile,apiModelId,contextShrinker]), providerRoute]),
      el('div',{class:'row'},[
        el('button',{class:'secondary',onclick:async()=>{try{await queueGeneration(true);}catch(err){toast(err.message,false);}}},'Validate / Dry-run'),
        el('button',{class:'primary',onclick:async()=>{try{await queueGeneration(false);}catch(err){toast(err.message,false);}}},'Generate 3D Asset'),
        el('span',{class:'badge'},selectedProvider.mode||''),selectedProvider.repo_url?el('a',{href:selectedProvider.repo_url,target:'_blank'},'Official Repository'):null
      ].filter(Boolean)),
      el('p',{class:'muted'},selectedProvider.description||'Select a provider.'),
      el('details',{},[el('summary',{},'Provider capability record'),el('pre',{class:'log'},JSON.stringify(selectedProvider,null,2))])
    ]),
    card('Automatic 3D Rigging',[
      el('p',{class:'muted'},'UniRig predicts skeleton topology and skinning weights. Blender pose-driven rigging converts your edited 3D pose into an armature and applies automatic weights before exporting GLB/FBX.'),
      el('div',{class:'row'},[assetSelect,rigProvider,poseAnnotation]),el('div',{class:'row'},[rigRepo,blenderExe]),
      el('div',{class:'row'},[
        el('button',{class:'secondary',onclick:async()=>{try{await queueRig(true);}catch(err){toast(err.message,false);}}},'Validate Rigging / Dry-run'),
        el('button',{class:'primary',onclick:async()=>{try{await queueRig(false);}catch(err){toast(err.message,false);}}},'Run Automatic Rigging'),
        el('a',{href:'/api/blender/plugin',target:'_blank'},'Download Blender Bridge')
      ])
    ]),
    card('Import Existing 3D Asset',[
      el('div',{class:'row'},[importPath,el('button',{class:'secondary',onclick:async()=>{try{const result=await api('/api/three-d/assets/import',{method:'POST',body:{source_path:importPath.value.trim(),copy:true,label:''}});state.threeDAssets=await api('/api/three-d/assets');state.threeDSelectedAsset=result.path;toast('3D asset imported into the managed library');render();}catch(err){toast(err.message,false);}}},'Copy into 3D Asset Library'),el('button',{class:'secondary',onclick:async()=>{try{state.threeDAssets=await api('/api/three-d/assets');toast('3D asset library refreshed');render();}catch(err){toast(err.message,false);}}},'Refresh Assets')])
    ]),
    card('Managed 3D Assets',[assetTable]),
    card('3D Workflow Guide',[
      el('ol',{},[
        el('li',{},'Choose a text-to-3D, image-to-3D, multi-image-to-3D, or video-to-3D provider and set the required local repository path, endpoint/API key, or token profile.'),
        el('li',{},'Run Validate / Dry-run first; inspect the generated command/request plan in Jobs.'),
        el('li',{},'Generate the asset, refresh this page, and select the resulting GLB/FBX/OBJ.'),
        el('li',{},'For editable humanoid/character rigs, first refine a 3D pose in Pose & 3D, save it, then choose Blender pose-driven rigging.'),
        el('li',{},'For category-general learned skeleton and skinning prediction, install UniRig and provide its repository path.'),
        el('li',{},'Open the result in Blender with the bridge for final bone, weight-paint, material, and animation edits.')
      ])
    ])
  ].filter(Boolean));
}


async function refreshFlexAvatar(deep = false, rerender = true) {
  const [status, assets] = await Promise.all([
    api(`/api/flexavatar/status?deep=${deep ? 'true' : 'false'}`),
    api('/api/flexavatar/assets')
  ]);
  state.flexAvatarStatus = status;
  state.flexAvatarAssets = assets || { inputs: [], avatar_codes: [], renderings: [], manifests: [], training_bundles: [], driver_sequences: [] };
  if (rerender) render();
  return { status, assets };
}

function flexAvatarView() {
  const status = state.flexAvatarStatus || {};
  const assets = state.flexAvatarAssets || { inputs: [], avatar_codes: [], renderings: [], manifests: [], training_bundles: [], driver_sequences: [] };
  const selectedMedia = [...state.selected];
  const selectedDataset = state.datasets.find(row => String(row.id) === String(state.filters.dataset_id || '')) || null;
  const output = state.flexAvatarOutput || {};

  const statusBadge = (label, ok, detail = '') => el('span', { class: `badge ${ok ? 'ok' : 'bad'}`, title: detail || label }, `${ok ? '✓' : '×'} ${label}`);
  const bytes = value => {
    const n = Number(value || 0);
    if (!n) return '0 B';
    if (n >= 1024 ** 3) return `${(n / 1024 ** 3).toFixed(2)} GiB`;
    if (n >= 1024 ** 2) return `${(n / 1024 ** 2).toFixed(1)} MiB`;
    if (n >= 1024) return `${(n / 1024).toFixed(1)} KiB`;
    return `${n} B`;
  };
  const queue = async (path, body, label, jump = false) => {
    try {
      const result = await api(path, { method: 'POST', body: body || {} });
      state.flexAvatarLastJob = result.job_id || null;
      state.flexAvatarOutput = { action: label, ...result };
      toast(`${label}${result.job_id ? ` queued as job ${result.job_id}` : ' complete'}`);
      if (jump && result.job_id) setTab('Jobs'); else render();
      return result;
    } catch (err) {
      state.flexAvatarOutput = { action: label, error: err.message };
      toast(err.message, false);
      render();
      return null;
    }
  };

  const mode = el('select', { onchange: e => { state.flexAvatarMode = e.target.value; render(); } }, [
    el('option', { value: 'single' }, 'Single portrait image'),
    el('option', { value: 'few_shot' }, 'Few-shot portrait images'),
    el('option', { value: 'monocular' }, 'Monocular portrait video')
  ]);
  mode.value = state.flexAvatarMode || 'single';
  const avatarName = el('input', {
    value: state.flexAvatarAvatarName || 'avatar',
    placeholder: 'avatar name',
    oninput: e => state.flexAvatarAvatarName = e.target.value,
    style: 'min-width:240px'
  });
  const sourcePaths = el('textarea', { rows: '4', placeholder: 'Optional local image/video paths, one per line' });
  const driverPath = el('input', { placeholder: 'Optional custom driver video path', style: 'min-width:420px' });
  const replaceStaged = el('input', { type: 'checkbox' });
  const sourceManifest = el('select', { onchange: e => state.flexAvatarSourceManifest = e.target.value }, [
    el('option', { value: '' }, 'Select staged source manifest'),
    ...(assets.manifests || []).filter(row => /_source\.json$/i.test(row.name)).map(row => el('option', { value: row.path }, row.name))
  ]);
  if (state.flexAvatarSourceManifest && !(assets.manifests || []).some(row => row.path === state.flexAvatarSourceManifest)) {
    sourceManifest.append(el('option', { value: state.flexAvatarSourceManifest }, `Current: ${state.flexAvatarSourceManifest}`));
  }
  sourceManifest.value = state.flexAvatarSourceManifest || '';
  const driverManifest = el('select', { onchange: e => state.flexAvatarDriverManifest = e.target.value }, [
    el('option', { value: '' }, 'No custom driver manifest'),
    ...(assets.manifests || []).filter(row => /_driver\.json$/i.test(row.name)).map(row => el('option', { value: row.path }, row.name))
  ]);
  if (state.flexAvatarDriverManifest && !(assets.manifests || []).some(row => row.path === state.flexAvatarDriverManifest)) {
    driverManifest.append(el('option', { value: state.flexAvatarDriverManifest }, `Current: ${state.flexAvatarDriverManifest}`));
  }
  driverManifest.value = state.flexAvatarDriverManifest || '';
  const sourceManifestRender = sourceManifest.cloneNode(true);
  sourceManifestRender.value = sourceManifest.value;
  sourceManifestRender.onchange = e => { state.flexAvatarSourceManifest = e.target.value; sourceManifest.value = e.target.value; };
  const driverManifestRender = driverManifest.cloneNode(true);
  driverManifestRender.value = driverManifest.value;
  driverManifestRender.onchange = e => { state.flexAvatarDriverManifest = e.target.value; driverManifest.value = e.target.value; };

  const checkpointUrl = el('input', { value: state.settings?.flexavatar_checkpoint_url || '', placeholder: 'Optional checkpoint URL override', style: 'min-width:440px' });
  const checkpointFile = el('input', { placeholder: 'Local ckpt-900k.pt path', style: 'min-width:420px' });
  const forceCheckpoint = el('input', { type: 'checkbox' });

  const driverMode = el('select', {}, [
    el('option', { value: 'builtin' }, 'Bundled tracked expression driver'),
    el('option', { value: 'custom' }, 'Custom tracked driver video'),
    el('option', { value: 'source' }, 'Use source observations as driver'),
    el('option', { value: 'neutral' }, 'Neutral / static expression')
  ]);
  const bundledDrivers = assets.driver_sequences || [];
  const driverSequence = bundledDrivers.length
    ? el('select', {}, bundledDrivers.map(name => el('option', { value: name }, name)))
    : el('input', { value: 'EMO-1-shout+laugh', placeholder: 'seed examples to load bundled drivers' });
  if (bundledDrivers.includes('EMO-1-shout+laugh')) driverSequence.value = 'EMO-1-shout+laugh';
  const device = el('input', { value: status.default_device || state.settings?.flexavatar_default_device || 'cuda:0', placeholder: 'cuda:0' });
  const runFitting = el('input', { type: 'checkbox', checked: true });
  const loadCode = el('input', { type: 'checkbox' });
  const saveHistory = el('input', { type: 'checkbox', checked: true });
  const render360 = el('input', { type: 'checkbox' });
  const fittingSteps = el('input', { type: 'number', min: '0', max: '10000', value: '200' });
  const fittingLr = el('input', { type: 'number', step: '0.0001', value: '0.01' });
  const lambdaSam = el('input', { type: 'number', min: '0', step: '0.1', value: '1.0' });
  const lambdaDino = el('input', { type: 'number', min: '0', step: '0.1', value: '1.0' });
  const lambdaLatent = el('input', { type: 'number', min: '0', step: '0.01', value: '0' });
  const maxObservations = el('input', { type: 'number', min: '1', max: '2400', value: '100' });
  const frameLimit = el('input', { type: 'number', min: '1', max: '10000', value: '240' });
  const fps = el('input', { type: 'number', min: '1', max: '120', step: '1', value: '24' });
  const resolution = el('select', {}, [256, 384, 512, 768, 1024].map(v => el('option', { value: v }, `${v} × ${v}`)));
  resolution.value = '512';

  const codeRows = assets.avatar_codes || [];
  const codeA = el('select', {}, [el('option', { value: '' }, 'First avatar code'), ...codeRows.map(row => el('option', { value: row.path }, row.name))]);
  const codeB = el('select', {}, [el('option', { value: '' }, 'Second avatar code'), ...codeRows.map(row => el('option', { value: row.path }, row.name))]);
  const alpha = el('input', { type: 'range', min: '0', max: '1', step: '0.01', value: '0.5' });
  const alphaLabel = el('span', { class: 'badge' }, 'First 0.50 / Second 0.50');
  alpha.oninput = () => alphaLabel.textContent = `First ${Number(alpha.value).toFixed(2)} / Second ${(1 - Number(alpha.value)).toFixed(2)}`;
  const blendName = el('input', { value: 'interpolated_avatar', placeholder: 'output avatar code name' });

  const bundleName = el('input', { value: 'flexavatar_training', placeholder: 'training bundle name' });
  const bundleSubject = el('input', { value: state.flexAvatarAvatarName || 'subject', placeholder: 'subject / identity id' });
  const bundleSourceType = el('select', {}, [
    el('option', { value: 'monocular_2d' }, 'Monocular / 2D supervision (bias sink 0)'),
    el('option', { value: 'multi_view_3d' }, 'Multi-view / 3D supervision (bias sink 1)'),
    el('option', { value: 'synthetic_multi_view' }, 'Synthetic multi-view supervision (bias sink 1)')
  ]);
  const bundleDataset = el('select', {}, datasetOptions());
  bundleDataset.value = state.filters.dataset_id || '';
  const trainSteps = el('input', { type: 'number', min: '1', value: '1000000' });
  const trainBatch = el('input', { type: 'number', min: '1', value: '20' });
  const perceptualStart = el('input', { type: 'number', min: '0', value: '400000' });
  const mixedPrecision = el('select', {}, ['bf16', 'fp16', 'fp32'].map(v => el('option', { value: v }, v)));
  const trainNproc = el('input', { type: 'number', min: '1', max: '16', value: '1' });
  const trainGpuIds = el('input', { value: '0', placeholder: 'GPU IDs: 0,1,2' });
  const trainerEntrypoint = el('input', { placeholder: 'External compatible trainer .py path', style: 'min-width:460px' });
  const trainingConfig = el('input', { placeholder: 'Generated training_config.json path', style: 'min-width:460px' });
  const extraArgs = el('input', { placeholder: 'Optional extra args, one per line or space-separated', style: 'min-width:420px' });

  const setupCard = card('1. Setup and Runtime Status', [
    el('p', { class: 'muted' }, 'FlexAvatar runs in a separate Conda environment so its Python 3.9 / CUDA 11.8 research stack cannot replace the main Data Curation Tool runtime. Quick setup supports the bundled/pretracked examples. Full setup adds Pixel3DMM tracking for your own portraits and videos.'),
    el('div', { class: 'row' }, [
      statusBadge('Bundled source', status.source_ready, status.source_path),
      statusBadge('Conda environment', status.environment_exists, status.environment_python || status.conda_error),
      statusBadge('FLEX-1 checkpoint', status.checkpoint_exists, status.checkpoint_path),
      statusBadge('Quick inference', status.quick_inference_ready),
      statusBadge('Custom-input tracking', status.custom_input_tracking_ready)
    ]),
    el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: () => queue('/api/flexavatar/install', { mode: 'quick' }, 'FlexAvatar quick runtime', true) }, 'Install / Update Quick Runtime'),
      el('button', { class: 'secondary', onclick: () => queue('/api/flexavatar/install', { mode: 'full' }, 'FlexAvatar full tracking runtime', true) }, 'Install Full Pixel3DMM Runtime'),
      el('button', { class: 'secondary', onclick: () => queue('/api/flexavatar/install', { mode: 'update' }, 'FlexAvatar runtime update', true) }, 'Update Runtime'),
      el('button', { class: 'secondary', onclick: async () => { try { await refreshFlexAvatar(true); toast('Deep module scan complete'); } catch (err) { toast(err.message, false); } } }, 'Deep Module Scan'),
      el('button', { class: 'secondary', onclick: () => queue('/api/flexavatar/validate', { load_checkpoint: false, device: device.value }, 'FlexAvatar runtime validation', true) }, 'Validate Isolated Runtime'),
      el('button', { class: 'secondary', onclick: () => queue('/api/flexavatar/validate', { load_checkpoint: true, device: device.value }, 'FLEX-1 checkpoint load test', true) }, 'Load-test FLEX-1 Checkpoint'),
      el('button', { class: 'secondary', onclick: async () => { try { await api('/api/system/open-path', { method: 'POST', body: { path: status.workspace } }); } catch (err) { toast(err.message, false); } } }, 'Open Workspace')
    ]),
    el('div', { class: 'row' }, [checkpointUrl, el('label', {}, [forceCheckpoint, ' replace existing'])]),
    el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: () => queue('/api/flexavatar/checkpoint', { url: checkpointUrl.value.trim() || null, force: forceCheckpoint.checked }, 'FLEX-1 checkpoint download', true) }, 'Download Official FLEX-1 Checkpoint'),
      checkpointFile,
      el('button', { class: 'secondary', onclick: () => pickFilePath(checkpointFile, 'Select ckpt-900k.pt') }, 'Browse Checkpoint...'),
      el('button', { class: 'secondary', onclick: () => queue('/api/flexavatar/checkpoint', { local_path: checkpointFile.value.trim(), force: true }, 'Local FLEX-1 checkpoint install', true) }, 'Install Local Checkpoint'),
      el('button', { class: 'secondary', onclick: () => queue('/api/flexavatar/seed-examples', {}, 'FlexAvatar example assets', true) }, 'Install Bundled Examples')
    ]),
    el('details', {}, [el('summary', {}, 'Runtime details'), el('pre', { class: 'log' }, JSON.stringify(status, null, 2))])
  ]);

  const stagingCard = card('2. Stage Portrait Inputs and Driver', [
    el('p', { class: 'muted' }, 'Use one selected portrait for single-image creation, several portraits for few-shot fitting, or one portrait video for monocular fitting. Custom inputs must be tracked before avatar creation. Staging copies/converts inputs into the isolated workspace; it does not modify the original dataset files.'),
    el('div', { class: 'row' }, [avatarName, mode, el('span', { class: 'badge' }, `${selectedMedia.length} gallery item(s) selected`), el('label', {}, [replaceStaged, ' replace staged files'])]),
    el('div', { class: 'row' }, [sourcePaths, el('button', { class: 'secondary', onclick: async () => { const picked = await pickFilePath(null, 'Select FlexAvatar portrait image or video'); if (picked) sourcePaths.value += `${sourcePaths.value.trim() ? '\n' : ''}${picked}`; } }, 'Add Local File...')]),
    el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: async () => {
        try {
          const result = await api('/api/flexavatar/stage', { method: 'POST', body: {
            avatar_name: avatarName.value, mode: mode.value, media_ids: selectedMedia,
            paths: sourcePaths.value.split(/\r?\n/).map(v => v.trim()).filter(Boolean), role: 'source', replace: replaceStaged.checked
          } });
          state.flexAvatarAvatarName = result.avatar_name; state.flexAvatarSourceManifest = result.manifest; state.flexAvatarOutput = result;
          await refreshFlexAvatar(false, false); toast(`Staged ${result.items?.length || 0} source input(s)`); render();
        } catch (err) { toast(err.message, false); }
      } }, 'Stage Selected / Local Source Inputs'),
      sourceManifest,
      el('button', { class: 'secondary', disabled: !status.custom_input_tracking_ready, title: status.custom_input_tracking_ready ? '' : 'Install the Full Pixel3DMM Runtime first', onclick: () => queue('/api/flexavatar/track', { manifest_path: sourceManifest.value }, 'Pixel3DMM source tracking', true) }, 'Track Source Manifest')
    ]),
    el('div', { class: 'row' }, [driverPath, el('button', { class: 'secondary', onclick: () => pickFilePath(driverPath, 'Select driving portrait video') }, 'Browse Driver Video...')]),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => {
        try {
          const result = await api('/api/flexavatar/stage', { method: 'POST', body: { avatar_name: avatarName.value, mode: 'monocular', media_ids: [], paths: [driverPath.value.trim()].filter(Boolean), role: 'driver', replace: replaceStaged.checked } });
          state.flexAvatarDriverManifest = result.manifest; state.flexAvatarOutput = result;
          await refreshFlexAvatar(false, false); toast('Custom driver staged'); render();
        } catch (err) { toast(err.message, false); }
      } }, 'Stage Custom Driver Video'),
      driverManifest,
      el('button', { class: 'secondary', disabled: !status.custom_input_tracking_ready, title: status.custom_input_tracking_ready ? '' : 'Install the Full Pixel3DMM Runtime first', onclick: () => queue('/api/flexavatar/track', { manifest_path: driverManifest.value }, 'Pixel3DMM driver tracking', true) }, 'Track Driver Manifest')
    ]),
    el('p', { class: 'warning' }, mode.value === 'few_shot' ? 'Few-shot mode fits one latent avatar code to all staged views.' : mode.value === 'monocular' ? 'Monocular mode samples tracked frames from the video for fitting.' : 'Single-image mode initializes an avatar from one portrait and can optionally fit it to that observation.')
  ]);

  const renderCard = card('3. Create, Fit, Animate, and Render Avatar', [
    el('p', { class: 'muted' }, 'The pretrained FLEX-1 checkpoint is sufficient for normal use—base-model training is not required. Fitting only optimizes the latent avatar code while keeping the network frozen, allowing single-image, few-shot, and monocular workflows.'),
    el('div', { class: 'row' }, [sourceManifestRender, driverManifestRender]),
    el('div', { class: 'row' }, [driverMode, driverSequence, device, resolution]),
    el('div', { class: 'row' }, [el('label', {}, [runFitting, ' fit avatar code']), el('label', {}, [loadCode, ' reuse existing avatar code']), el('label', {}, [saveHistory, ' save fitting history']), el('label', {}, [render360, ' render 360° orbit'])]),
    el('div', { class: 'row' }, [el('label', {}, ['Fitting steps', fittingSteps]), el('label', {}, ['Learning rate', fittingLr]), el('label', {}, ['Maximum observations', maxObservations]), el('label', {}, ['Frame limit', frameLimit]), el('label', {}, ['FPS', fps])]),
    el('div', { class: 'row' }, [el('label', {}, ['SAM perceptual loss', lambdaSam]), el('label', {}, ['DINO perceptual loss', lambdaDino]), el('label', {}, ['Latent regularization', lambdaLatent])]),
    el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: () => queue('/api/flexavatar/render', {
        avatar_name: avatarName.value, source_manifest: sourceManifestRender.value, driver_manifest: driverManifestRender.value || null,
        driver_mode: driverMode.value, driver_sequence: driverSequence.value, device: device.value,
        run_fitting: runFitting.checked, fitting_steps: Number(fittingSteps.value), fitting_lr: Number(fittingLr.value),
        lambda_sam: Number(lambdaSam.value), lambda_dino: Number(lambdaDino.value), lambda_latent: Number(lambdaLatent.value),
        max_observations: Number(maxObservations.value), load_avatar_code: loadCode.checked,
        save_fitting_history: saveHistory.checked, render_360: render360.checked,
        frame_limit: Number(frameLimit.value), fps: Number(fps.value), resolution: Number(resolution.value)
      }, 'FlexAvatar avatar creation/render', true) }, 'Create / Fit / Render'),
      el('button', { class: 'secondary', disabled: !status.custom_input_tracking_ready, title: status.custom_input_tracking_ready ? '' : 'The official viewer imports Pixel3DMM/PyTorch3D and requires the Full Runtime', onclick: async () => { try { const result = await api('/api/flexavatar/viewer', { method: 'POST', body: { avatar_name: avatarName.value || null } }); state.flexAvatarOutput = result; toast(`Official viewer launched (PID ${result.pid})`); render(); } catch (err) { toast(err.message, false); } } }, 'Launch Official Interactive Viewer'),
      el('button', { class: 'secondary', onclick: async () => { try { await refreshFlexAvatar(); toast('FlexAvatar assets refreshed'); } catch (err) { toast(err.message, false); } } }, 'Refresh Outputs')
    ]),
    el('details', {}, [el('summary', {}, 'Workflow guidance'), el('div', { class: 'muted' }, [
      el('p', {}, 'Single image: stage → track → create/fit → choose bundled/custom driver → render.'),
      el('p', {}, 'Few shot: stage multiple views under one avatar name → track → fit to all observations → render.'),
      el('p', {}, 'Monocular video: stage one video → track → fit from sampled observations → render.'),
      el('p', {}, 'The multi-view bias sink is used at inference to favor complete 360° heads.')
    ])])
  ]);

  const interpolationCard = card('4. Avatar Latent Codes and Identity Interpolation', [
    el('p', { class: 'muted' }, 'FlexAvatar learns a smooth latent avatar space. Blend two saved avatar codes without changing either source code.'),
    el('div', { class: 'row' }, [codeA, codeB, alpha, alphaLabel, blendName]),
    el('button', { class: 'primary', onclick: async () => {
      try {
        const result = await api('/api/flexavatar/interpolate', { method: 'POST', body: { first: codeA.value, second: codeB.value, alpha: Number(alpha.value), output_name: blendName.value } });
        state.flexAvatarOutput = result; await refreshFlexAvatar(false, false); toast('Interpolated avatar code saved'); render();
      } catch (err) { toast(err.message, false); }
    } }, 'Create Interpolated Avatar Code'),
    codeRows.length ? el('table', { class: 'table' }, [
      el('thead', {}, el('tr', {}, ['Avatar code', 'Size', 'Path'].map(v => el('th', {}, v)))),
      el('tbody', {}, codeRows.map(row => el('tr', {}, [el('td', {}, row.name), el('td', {}, bytes(row.size_bytes)), el('td', { class: 'path tiny' }, row.path)])))
    ]) : el('p', { class: 'muted' }, 'No saved avatar codes yet.')
  ]);

  const renderingsCard = card('5. Renderings and Workspace Assets', [
    (assets.renderings || []).length ? el('div', { class: 'gallery' }, (assets.renderings || []).slice(0, 24).map(row => {
      const url = `/api/flexavatar/file?path=${encodeURIComponent(row.path)}`;
      const ext = String(row.name).split('.').pop().toLowerCase();
      const preview = ['mp4', 'webm', 'mov'].includes(ext)
        ? el('video', { src: url, controls: 'controls', preload: 'metadata', style: 'width:100%;max-height:320px;background:#000;border-radius:10px' })
        : el('img', { src: url, alt: row.name, style: 'width:100%;max-height:320px;object-fit:contain;background:#000;border-radius:10px' });
      return el('article', { class: 'gallery-card' }, [preview, el('strong', {}, row.name), el('span', { class: 'muted tiny' }, bytes(row.size_bytes)), el('a', { href: url, target: '_blank' }, 'Open / Download')]);
    })) : el('p', { class: 'muted' }, 'No FlexAvatar renderings have been generated yet.'),
    el('details', {}, [el('summary', {}, 'All workspace assets'), el('pre', { class: 'log' }, JSON.stringify(assets, null, 2))])
  ]);

  const trainingCard = card('6. Training / Fine-tuning Research Support', [
    el('p', { class: 'muted' }, 'Normal avatar creation uses the pretrained FLEX-1 checkpoint and does not require training. The attached official release does not include the authors’ complete base-model training program, so this section builds a reproducible mixed-supervision manifest/config and can launch a separately supplied compatible research trainer. It never pretends that fitting one avatar code is full model training.'),
    el('div', { class: 'row' }, [bundleName, bundleSubject, bundleSourceType, bundleDataset]),
    el('div', { class: 'row' }, [el('span', { class: 'badge' }, `${selectedMedia.length} selected media`), el('span', { class: 'muted' }, selectedDataset ? `Active filtered dataset: ${selectedDataset.name}` : 'Choose a dataset if no gallery media are selected.')]),
    el('div', { class: 'row' }, [el('label', {}, ['Steps', trainSteps]), el('label', {}, ['Batch size', trainBatch]), el('label', {}, ['Perceptual losses start', perceptualStart]), mixedPrecision, el('label', {}, ['Processes', trainNproc]), trainGpuIds]),
    el('div', { class: 'row' }, [trainerEntrypoint, el('button', { class: 'secondary', onclick: () => pickFilePath(trainerEntrypoint, 'Select compatible FlexAvatar training entrypoint') }, 'Browse Trainer...')]),
    el('button', { class: 'primary', onclick: async () => {
      try {
        const result = await api('/api/flexavatar/training/bundle', { method: 'POST', body: {
          name: bundleName.value, media_ids: selectedMedia, dataset_id: bundleDataset.value ? Number(bundleDataset.value) : null,
          subject_id: bundleSubject.value, source_type: bundleSourceType.value, steps: Number(trainSteps.value), batch_size: Number(trainBatch.value),
          perceptual_start_step: Number(perceptualStart.value), mixed_precision: mixedPrecision.value,
          nproc_per_node: Number(trainNproc.value), device_ids: parseGpuIds(trainGpuIds.value), trainer_entrypoint: trainerEntrypoint.value.trim() || null
        } });
        state.flexAvatarOutput = result; trainingConfig.value = result.config; await refreshFlexAvatar(false, false); toast('FlexAvatar training bundle created'); render();
      } catch (err) { toast(err.message, false); }
    } }, 'Create Mixed-Supervision Training Bundle'),
    el('div', { class: 'row' }, [trainingConfig, el('button', { class: 'secondary', onclick: () => pickFilePath(trainingConfig, 'Select FlexAvatar training_config.json') }, 'Browse Config...')]),
    el('div', { class: 'row' }, [extraArgs, el('button', { class: 'secondary', onclick: async () => {
      try {
        const result = await api('/api/flexavatar/training/plan', { method: 'POST', body: { config_path: trainingConfig.value, trainer_entrypoint: trainerEntrypoint.value.trim() || null, nproc_per_node: Number(trainNproc.value), extra_args: extraArgs.value.trim() ? extraArgs.value.trim().split(/\s+/) : [] } });
        state.flexAvatarOutput = result; toast(result.runnable ? 'Training plan is runnable' : result.warning, result.runnable); render();
      } catch (err) { toast(err.message, false); }
    } }, 'Validate Training Plan'), el('button', { class: 'danger', onclick: () => queue('/api/flexavatar/training/run', { config_path: trainingConfig.value, trainer_entrypoint: trainerEntrypoint.value.trim() || null, nproc_per_node: Number(trainNproc.value), extra_args: extraArgs.value.trim() ? extraArgs.value.trim().split(/\s+/) : [], timeout_seconds: 2592000 }, 'FlexAvatar external training', true) }, 'Launch External Trainer')]),
    el('details', {}, [el('summary', {}, 'Paper baseline encoded in the bundle'), el('pre', { class: 'log' }, JSON.stringify(status.paper_baseline || {}, null, 2))]),
    (assets.training_bundles || []).length ? el('pre', { class: 'log' }, JSON.stringify(assets.training_bundles, null, 2)) : null
  ].filter(Boolean));

  const noticeCard = card('License and Scope', [
    el('p', { class: 'warning' }, 'FlexAvatar is bundled as an optional, separately executed research component under CC BY-NC 4.0. The checkpoint is not redistributed in this ZIP; install it from the official source or select a local copy. Review the upstream license before use.'),
    el('p', { class: 'muted' }, 'This integration exposes the upstream capabilities—single-image, few-shot, and monocular avatar creation; expression driving; novel-view rendering; latent fitting and interpolation—without replacing the main application environment.'),
    el('div', { class: 'row' }, [
      el('a', { href: 'https://tobias-kirschstein.github.io/flexavatar/', target: '_blank', rel: 'noreferrer' }, 'Official FlexAvatar Project'),
      el('a', { href: 'https://github.com/tobias-kirschstein/flexavatar', target: '_blank', rel: 'noreferrer' }, 'Official Source Repository'),
      el('button', { class: 'secondary', onclick: async () => { try { await api('/api/system/open-path', { method: 'POST', body: { path: status.source_path } }); } catch (err) { toast(err.message, false); } } }, 'Open Bundled Source')
    ])
  ]);

  return el('div', { class: 'grid' }, [
    setupCard, stagingCard, renderCard, interpolationCard, renderingsCard, trainingCard,
    card('Last FlexAvatar Action / Result', [el('pre', { class: 'log' }, JSON.stringify(output, null, 2))]),
    noticeCard
  ]);
}



function futureModalitiesView() {
  const phaseChip = (label, status = 'planned') => el('span', { class: status === 'active' ? 'badge ok' : status === 'scaffold' ? 'badge' : 'badge muted' }, label);
  return el('div', { class: 'grid' }, [
    card('Future Modalities Roadmap', [
      el('p', { class: 'muted' }, 'This page captures the intended long-term direction for the tool: image, audio, video, video-with-audio, and 3D dataset curation with model-assisted labeling, review, training preparation, and eventually guided training workflows.'),
      el('div', { class: 'row' }, [phaseChip('Images: active', 'active'), phaseChip('Audio: scaffold'), phaseChip('Video: scaffold'), phaseChip('Video + audio: planned'), phaseChip('3D assets: scaffold'), phaseChip('Training: preliminary')]),
      el('p', { class: 'warning' }, 'Voice cloning and speaker modeling are planned only for ethically sourced material with documented consent, provenance, and usage rights. The roadmap intentionally keeps these controls explicit rather than automatic.')
    ]),
    card('Audio Dataset Curation Objectives', [
      el('ul', {}, [
        el('li', {}, 'Import audio files and audio tracks extracted from video while preserving metadata and source provenance.'),
        el('li', {}, 'Create timestamped transcripts, speaker turns, captions, sound-event tags, music/SFX labels, and confidence scores.'),
        el('li', {}, 'Use STT, alignment, diarization, audio tagging, and optional speaker/voice-profile tools as separate model stages.'),
        el('li', {}, 'Export audio datasets for STT, TTS, voice-conversion, captioning, classification, and multimodal training workflows.')
      ])
    ]),
    card('Voice Cloning / Voice Conversion Future Scope', [
      el('ul', {}, [
        el('li', {}, 'Add dedicated tabs for voice dataset setup, consent/provenance manifests, reference clip review, audio cleaning, segmentation, and train/validation splits.'),
        el('li', {}, 'Support open-source voice-cloning/TTS and voice-conversion backends as optional integrations, not mandatory base-install dependencies.'),
        el('li', {}, 'Expose cloned/curated voices as selectable TTS voices only when the selected TTS backend supports them.'),
        el('li', {}, 'Track each voice with license, consent status, allowed use, source notes, dataset path, model path, and generated-output policy.')
      ])
    ]),
    card('Video + Audio Dataset Objectives', [
      el('ul', {}, [
        el('li', {}, 'Treat video as synchronized streams: frames, optical/motion cues, embedded audio, subtitles/transcripts, metadata, and derived annotations.'),
        el('li', {}, 'Generate and edit frame-level, clip-level, and timestamp-level labels for objects, actions, scenes, speech, music, and sound events.'),
        el('li', {}, 'Keep round-trip links between extracted frames/audio segments and the original video timeline.'),
        el('li', {}, 'Prepare exports for video captioning, action recognition, video VLMs, audio-video alignment, and multimodal dataset training.')
      ])
    ]),
    card('Training Roadmap', [
      el('p', { class: 'muted' }, 'Training features remain preliminary. The intended path is to keep training modular, explicit, resumable, logged, and separated from curation so users can audit data before training starts.'),
      el('ol', {}, [
        el('li', {}, 'Dataset readiness checks: licensing/consent manifest, duplicate scan, split validation, missing-label audit, duration/quality statistics.'),
        el('li', {}, 'Training planners: recommended backend, model family, GPU/VRAM estimate, storage estimate, batch size, precision, resume/checkpoint policy.'),
        el('li', {}, 'Human-approved execution: queue jobs, show logs, support pause/cancel/retry, and preserve all training configs and outputs.'),
        el('li', {}, 'Evaluation: holdout metrics, qualitative review queues, comparison to baseline models, and exportable reports.')
      ])
    ]),
    card('Planned Integration Candidates', [
      el('p', { class: 'muted' }, 'Candidate backends are tracked in the wiki so they can be evaluated without forcing fragile dependencies into the base installer. Current candidates include STT/alignment/diarization, voice cloning/TTS, and voice-conversion systems.'),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: () => setTab('Settings') }, 'Open Voice / Agent Settings'),
        el('button', { class: 'secondary', onclick: () => setTab('Media Tools') }, 'Open Media Tools'),
        el('button', { class: 'secondary', onclick: () => setTab('Models') }, 'Open Models')
      ]),
      el('p', { class: 'muted tiny' }, 'See docs/wiki/24-Future-Multimodal-Voice-and-Training-Roadmap.md and docs/templates/voice_dataset_consent_manifest_template.json inside the project ZIP for the detailed roadmap and consent/provenance template.')
    ])
  ]);
}

function helpWorkflowsView() {
  return el('div',{class:'grid'},[
    card('Application Workflow Map',[
      el('ol',{},[
        el('li',{},'Import a dataset, verify media metadata, and build/load the tag dictionary.'),
        el('li',{},'Use Gallery, Tag Editor, Compare, and Batch Tags for curation and model-assisted decisions.'),
        el('li',{},'Use Detection & Boxes, Segmentation & Masks, and Pose & 3D for persistent spatial annotation layers.'),
        el('li',{},'Use 3D Studio to generate or import assets, rig them, and hand them to Blender.'),
        el('li',{},'Review Jobs for progress/errors, then export the curated labels or training set.')
      ])
    ]),
    card('SAM / SAM-HQ / SAM2 Prompted Segmentation',[
      el('ol',{},[
        el('li',{},'Open Segmentation & Masks, choose the exact SAM-family checkpoint, and press Set Up Runtime + Weights + Load. The queued job installs that family, downloads the matching checkpoint, and validates the pairing.'),
        el('li',{},'Choose Positive Point (+ Include) and click inside the object. Add more positive points to cover disconnected or difficult regions.'),
        el('li',{},'Choose Negative Point (− Exclude) and click background or neighboring objects that must not enter the mask. Positive labels are sent as 1 and negative labels as 0.'),
        el('li',{},'Optionally combine the points with a bbox prompt. A box gives coarse extent while positive/negative points refine inclusion and exclusion.'),
        el('li',{},'Use Instance masks for separate editable candidates. Use Semantic class mask to union the best real candidate from each prompted instance into one class layer.'),
        el('li',{},'Review the generated masks, promote only valid previews to persistent layers, then refine them with the built-in mask editor or Krita bridge.')
      ]),
      el('pre',{class:'log'},'Windows CMD:\n  install_sam_runtime.bat sam\n  install_sam_runtime.bat sam_hq\n  install_sam_runtime.bat sam2\n\nLinux/macOS shell:\n  ./install_sam_runtime.sh sam\n  ./install_sam_runtime.sh sam_hq\n  ./install_sam_runtime.sh sam2'),
      el('p',{class:'warning'},'SAM-family masks are class-agnostic. A semantic label comes from your prompt, a detector guide, or another model; the application does not invent class meaning from the mask alone.')
    ]),
    card('2D / 3D Pose: Recommended Sequence',[
      el('ol',{},[
        el('li',{},'Open an image in Gallery or Tag Editor, then switch to Pose & 3D.'),
        el('li',{},'Choose 2D pose or 3D pose. Pick a model: MediaPipe is the simplest 2D+world-3D setup; MMPose supplies RTMPose, ViTPose, whole-body, animal, MotionBERT, and InterNet options.'),
        el('li',{},'Install the selected runtime. Download MediaPipe .task weights when applicable; MMPose aliases resolve official configs/checkpoints at first use.'),
        el('li',{},'Run inference, select a proposal, and apply it to the editable pose.'),
        el('li',{},'Drag joints over the image or in the 3D viewer. Connect/delete bones as needed; every bone is redrawn while its joints move.'),
        el('li',{},'Save as a persistent pose layer. Reload it later, send it to Blender, or use it for pose-driven rigging.')
      ]),
      el('pre',{class:'log'},'Windows CMD:\n  install_pose_models.bat ultralytics\n  install_pose_models.bat mediapipe\n  install_pose_models.bat mmpose\n\nLinux/macOS shell:\n  ./install_pose_models.sh ultralytics\n  ./install_pose_models.sh mediapipe\n  ./install_pose_models.sh mmpose')
    ]),
    card('Choosing a Pose Backend',[
      el('dl',{},[
        el('dt',{},'MediaPipe Pose Landmarker'),el('dd',{},'Fast human pose with 33 image landmarks plus world-space landmarks; easiest local 3D option.'),
        el('dt',{},'RTMPose / ViTPose'),el('dd',{},'General human 2D pose; RTMPose also has whole-body and animal aliases.'),
        el('dt',{},'MotionBERT (human3d)'),el('dd',{},'MMPose 3D human pose lifting with a Human3.6M-style skeleton.'),
        el('dt',{},'InterNet (hand3d)'),el('dd',{},'MMPose 3D hand pose estimation.'),
        el('dt',{},'YOLO Pose'),el('dd',{},'Lightweight 2D human keypoints; useful when Ultralytics is already installed.')
      ])
    ]),
    card('3D Generation and Rigging',[
      el('ol',{},[
        el('li',{},'Open 3D Studio and choose TripoSR, Stable Fast 3D, TRELLIS, Hunyuan3D local API, Meshy API, or the generic REST adapter.'),
        el('li',{},'Set the cloned repository path for local providers, or set endpoint/API key for API providers.'),
        el('li',{},'Run Validate / Dry-run before execution. The resulting Jobs entry contains the exact command/request plan without running a model.'),
        el('li',{},'Generate or import a GLB/FBX/OBJ asset. Results are cataloged under outputs/3d_assets.'),
        el('li',{},'Choose UniRig for learned skeleton+skinning prediction, or Blender pose-driven rigging to build an armature from a saved editable 3D pose and bind it with automatic weights.'),
        el('li',{},'Install the Blender bridge ZIP from the Pose or 3D Studio tab to exchange poses/assets and queue jobs from Blender.')
      ]),
      el('p',{class:'warning'},'Local 3D repositories have large, provider-specific CUDA dependencies. Keep each provider in its recommended environment when its requirements conflict with the main application environment.')
    ]),
    card('Pose Editing Controls',[
      el('dl',{},[
        el('dt',{},'Move / Select'),el('dd',{},'Drag a joint. Connected edges update continuously.'),
        el('dt',{},'Add Joint'),el('dd',{},'Click the image; optionally auto-connect from the selected joint.'),
        el('dt',{},'Connect Bones'),el('dd',{},'Click the first joint, then the second.'),
        el('dt',{},'Delete Joint / Bone'),el('dd',{},'Click a joint or click close to an edge. Right-click also deletes a joint.'),
        el('dt',{},'3D Viewer'),el('dd',{},'Drag a joint to change world coordinates, drag empty space to orbit, scroll to zoom, and use the depth slider for z.')
      ])
    ]),
    card('FlexAvatar: Complete Animatable 3D Head Avatars',[
      el('ol',{},[
        el('li',{},'Open FlexAvatar and install the isolated Quick Runtime. This keeps its Python 3.9 / CUDA 11.8 dependencies separate from the main Conda environment.'),
        el('li',{},'Download the official FLEX-1 checkpoint, or install a local ckpt-900k.pt copy. Use Full Pixel3DMM Runtime when processing your own portraits or videos.'),
        el('li',{},'Select one portrait for single-image mode, several portrait views for few-shot mode, or one portrait video for monocular mode. Stage the source and run Pixel3DMM tracking.'),
        el('li',{},'Choose a bundled expression driver, a custom tracked driver video, the source observations, or a neutral driver. Create/Fit/Render then follows the upstream inference and latent-fitting path.'),
        el('li',{},'Use the saved avatar code for later animation, fitting, 360° rendering, official-viewer inspection, or identity interpolation.'),
        el('li',{},'Normal use does not require base-model training. The Training section creates mixed-supervision manifests with 2D/3D bias-sink labels and the paper baseline; full model training requires a separately supplied compatible trainer because the official attached release does not contain that entrypoint.')
      ]),
      el('pre',{class:'log'},`Windows CMD:
  install_flexavatar.bat quick
  install_flexavatar.bat full
  update_flexavatar.bat

Linux/macOS shell:
  ./install_flexavatar.sh quick
  ./install_flexavatar.sh full
  ./update_flexavatar.sh`),
      el('p',{class:'warning'},'FlexAvatar is an optional non-commercial research component under CC BY-NC 4.0. The model checkpoint is downloaded separately and is not embedded in the application ZIP.'),
      el('button',{class:'secondary',onclick:()=>setTab('FlexAvatar')},'Open FlexAvatar Tab')
    ]),
    card('Troubleshooting',[
      el('ul',{},[
        el('li',{},'No pose proposal: inspect Model Status, lower the threshold, confirm the checkpoint/runtime pairing, and check the Jobs error.'),
        el('li',{},'MMPose install failure: verify the active PyTorch/CUDA build first, then reinstall through OpenMIM so MMCV matches it.'),
        el('li',{},'3D provider produced no asset: check its repository command directly and confirm the configured output format is supported.'),
        el('li',{},'Blender auto-rig failure: confirm the Blender executable path, the source mesh format, and that the saved pose contains valid joints and edges.'),
        el('li',{},'UniRig on Windows: WSL/Linux is recommended for its shell/CUDA workflow; paths must be accessible inside that environment.')
      ])
    ])
  ]);
}


function batchTagsView() {
  return el('div', { class: 'grid' }, [
    card('Selection / Quick Select', [quickSelectControls()]),
    batchOperationCard(),
    modelTagSelectionCard(),
    imageTagRatingQuickRunCard({ title: 'Quick Tag / Rating Model on Selected Batch', getMediaIds: () => [...state.selected] }),
    metadataQuickCard({ title: 'Batch Metadata Extraction / Compose', getMediaIds: () => [...state.selected] })
  ]);
}

function predictionAnalyticsView() {
  const dataset = el('select', {}, [el('option', { value: '' }, 'Selected media only'), ...datasetOptions()]);
  const limit = el('input', { type: 'number', min: '10', max: '5000', value: '300', style: 'width:100px' });
  const minScore = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: '0', style: 'width:90px' });
  const rows = state.tagScoreAnalytics?.rows || [];
  const models = state.tagScoreAnalytics?.models || [];
  const matrix = state.tagScoreAnalytics?.matrix || {};
  const tags = state.tagScoreAnalytics?.tags || [];
  return el('div', { class: 'grid' }, [
    card('Model Prediction Score Analytics', [
      el('p', { class: 'muted' }, 'Scores are persisted whenever tag/class/rating models run. Hover tag chips to inspect per-model scores, or use this view to compare model consistency per tag.'),
      el('div', { class: 'row' }, [dataset, el('label', {}, ['limit', limit]), el('label', {}, ['min score', minScore]),
        el('button', { class: 'primary', onclick: async () => { try { const body = { dataset_id: dataset.value ? Number(dataset.value) : null, media_ids: dataset.value ? [] : [...state.selected], limit: Number(limit.value || 300), min_score: Number(minScore.value || 0) }; state.tagScoreAnalytics = await api('/api/models/tag-score-analytics', { method: 'POST', body }); render(); } catch (err) { toast(err.message, false); } } }, 'Build Analytics')
      ]),
      el('div', { class: 'model-legend' }, models.map((m, idx) => el('span', { class: `legend-chip ${scoreColorClass(m, idx)}` }, m))),
      tags.length ? el('div', { class: 'score-chart' }, tags.map(tag => el('div', { class: 'score-chart-row' }, [
        el('div', { class: 'score-tag-label' }, tag),
        el('div', { class: 'score-bars' }, models.map((m, idx) => { const cell = (matrix[tag] || {})[m] || {}; const v = Number(cell.avg_score || 0); return el('div', { class: `score-bar-wrap ${scoreColorClass(m, idx)}`, title: `${m} · avg ${(v*100).toFixed(1)}% · max ${((cell.max_score || 0)*100).toFixed(1)}% · n=${cell.count || 0}` }, [el('span', { class: 'score-bar-fill', style: `width:${Math.round(v*100)}%` }, ''), el('span', { class: 'score-bar-text' }, v ? `${(v*100).toFixed(0)}%` : '')]); }))
      ]))) : el('p', { class: 'muted' }, 'No analytics loaded yet. Run one or more tag/class/rating models, then press Build Analytics.')
    ]),
    card('Raw Score Rows', [el('pre', { class: 'log' }, JSON.stringify(rows.slice(0, 500), null, 2))])
  ]);
}


function quickSelectControls() {
  const tagCtl = tagAutocompleteControl({ placeholder: 'tag to select by' });
  const cat = el('select', {}, [el('option', { value: '' }, 'Any category'), ...categories().map(c => el('option', { value: c.key }, c.label || c.key))]);
  return el('div', { class: 'grid' }, [
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: () => { for (const media of state.media.items) addSelectedMedia(media); render(); } }, 'Select Page'),
      el('button', { class: 'secondary', onclick: () => { for (const media of state.media.items) if (!media.tags.length) addSelectedMedia(media); render(); } }, 'Select Untagged Page'),
      el('button', { class: 'secondary', onclick: () => { clearSelectedMedia(); updateTileSelectionDom(); } }, 'Clear Selection'),
      el('button', { class: 'secondary', onclick: async () => { state.media.page = 1; await loadMedia(); render(); } }, 'Reload Gallery Page')
    ]),
    el('div', { class: 'row' }, [
      tagCtl.wrap,
      el('button', { class: 'secondary', onclick: () => { const t = firstTag(tagCtl.input.value); if (!t) return; for (const media of state.media.items) if ((media.tags || []).includes(t)) addSelectedMedia(media); render(); } }, 'Select With Tag'),
      el('button', { class: 'secondary', onclick: () => { const t = firstTag(tagCtl.input.value); if (!t) return; for (const media of state.media.items) if (!(media.tags || []).includes(t)) addSelectedMedia(media); render(); } }, 'Select Without Tag'),
      cat,
      el('button', { class: 'secondary', onclick: () => { if (!cat.value) return; for (const media of state.media.items) if ((media.tags || []).some(t => categoryOf(t, media) === cat.value)) addSelectedMedia(media); render(); } }, 'Select by Category')
    ])
  ]);
}

function batchOperationCard() {
  const bulkCtl = tagAutocompleteControl({ placeholder: 'tag_one, tag_two' });
  const replaceFrom = tagAutocompleteControl({ placeholder: 'replace from' });
  const replaceTo = tagAutocompleteControl({ placeholder: 'replace to' });
  return card('Batch Add / Remove / Set / Replace / Copy', [
    el('p', { class: 'muted' }, `Applies to ${state.selected.size} selected item(s).`),
    el('div', { class: 'row' }, [bulkCtl.wrap, el('button', { class: 'secondary', onclick: () => bulkTags('add', bulkCtl.input.value) }, 'Add'), el('button', { class: 'secondary', onclick: () => bulkTags('remove', bulkCtl.input.value) }, 'Remove'), el('button', { class: 'danger', onclick: () => bulkTags('set', bulkCtl.input.value) }, 'Set')]),
    el('div', { class: 'row' }, [replaceFrom.wrap, replaceTo.wrap, el('button', { class: 'secondary', onclick: () => bulkTags('replace', '', { replace_from: firstTag(replaceFrom.input.value), replace_to: firstTag(replaceTo.input.value) }) }, 'Replace')]),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: () => copyActiveToSelected() }, 'Copy Active Image Tags to Selected'),
      el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/tags/prune', { method: 'POST', body: { media_ids: [...state.selected], dry_run: false } }); toast(`Pruned ${r.filter(x => x.removed.length).length} files`); await loadMedia(); render(); } catch (err) { toast(err.message, false); } } }, 'Prune Implied Tags'),
      el('button', { class: 'secondary', onclick: () => bulkTags('add', '', { order_strategy: state.orderingStrategy }) }, 'Apply Ordering to Selected')
    ])
  ]);
}
async function bulkTags(operation, rawTags, extra = {}) {
  try {
    const media_ids = [...state.selected];
    if (!media_ids.length) throw new Error('Select one or more media items first.');
    const body = { media_ids, operation, tags: parseTagString(rawTags), tag_profile: state.tagProfile, order_strategy: extra.order_strategy || state.orderingStrategy, ...extra };
    const r = await api('/api/tags/bulk', { method: 'POST', body });
    toast(`Changed ${r.changed} files`); await loadMedia(); render();
  } catch (err) { toast(err.message, false); }
}
async function copyActiveToSelected(item = state.activeMedia) {
  if (!item) return toast('Open an active image first.', false);
  await bulkTags('copy', '', { source_media_id: item.id });
}


function imageTagRatingQuickRunCard(options = {}) {
  const opts = options || {};
  const models = state.models.filter(m => {
    const caps = new Set(m.capabilities || []);
    return caps.has('tag') || caps.has('rating') || caps.has('classify') || ['tagger','classifier','rating_classifier'].includes(m.kind);
  });
  if (!models.length) return null;
  const model = el('select', {}, models.map(m => el('option', { value: m.name }, modelLabel(m))));
  const preferredQuick = models.find(m => m.name === 'redrocket-jtp-3') || models.find(m => m.name === 'redrocket-e6-visual-ratings');
  rememberSelect('quickModelSelection', model, preferredQuick?.name || '', true);
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value };
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: opts.threshold || state.settings.classifier_threshold || 0.35, style: 'width:90px' });
  const topK = el('input', { type: 'number', min: '1', max: '1000', value: opts.topK || 200, style: 'width:90px' });
  const device = el('input', { value: state.settings.preferred_device || 'auto', placeholder: 'auto/cpu/cuda:0', style: 'width:130px' });
  const apply = el('input', { type: 'checkbox', checked: opts.applyDefault !== false });
  const ids = () => (opts.getMediaIds ? opts.getMediaIds() : [...state.selected]).filter(Boolean);
  return card(opts.title || 'Quick Tag / Rating Model Run', [
    el('p', { class: 'muted' }, opts.description || 'Run local/downloaded image taggers or rating classifiers directly on the current item(s). Results are stored as predictions; enable Apply to add emitted labels as tags.'),
    el('div', { class: 'row' }, [model, el('label', {}, ['threshold', threshold]), el('label', {}, ['top-k', topK]), el('label', {}, ['device', device]), el('label', {}, [apply, ' Apply emitted labels as tags'])]),
    modelLifecycleStrip(selectedModel(), true),
    el('button', { class: 'primary', disabled: modelBusy(selectedModel(), ['download', 'load']), onclick: async () => {
      try {
        const mediaIds = ids();
        if (modelBusy(selectedModel(), ['download', 'load'])) throw new Error('Selected model is downloading or loading. Wait for the status circle to finish before running inference.');
        if (!mediaIds.length) throw new Error('No media selected for model run.');
        const r = await api('/api/models/run', { method: 'POST', body: {
          media_ids: mediaIds,
          model_name: model.value,
          task: defaultTaskForModelName(model.value),
          threshold: Number(threshold.value || 0.35),
          device: device.value || 'auto',
          apply_tags: apply.checked,
          options: { top_k: Number(topK.value || 200), max_tags: Number(topK.value || 200), threshold: Number(threshold.value || 0.35) }
        } });
        state.lastModelRunJob = r.job_id;
        toast(`Queued ${model.value} job ${r.job_id}. Staying on this page; use Open Last Model Job if you need full logs.`);
        await refreshAll();
        await refreshCompletedModelJobById(r.job_id);
        render();
      } catch (err) { toast(err.message, false); }
    } }, 'Run Selected Tag/Rating Model')
  ]);
}


function quickCurationModelRunCard(options = {}) {
  const title = options.title || 'Quick Tag / Rating Model Run';
  const description = options.description || 'Run downloaded/local taggers and rating classifiers directly on the current target set. JTP-3 outputs tags; e6 visual ratings outputs rating classes.';
  const getMediaIds = options.getMediaIds || (() => [...state.selected]);
  const filter = m => {
    const caps = new Set(m.capabilities || []);
    return caps.has('tag') || caps.has('rating') || caps.has('multilabel') || caps.has('classify') || ['tagger','rating','classifier'].includes(m.kind);
  };
  const model = el('select', {}, modelOptions(filter));
  const preferredCuration = state.models.filter(filter).find(m => m.name === 'redrocket-jtp-3') || state.models.filter(filter).find(m => m.name === 'redrocket-e6-visual-ratings');
  rememberSelect('curationModelSelection', model, preferredCuration?.name || '', true);
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value };
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: String(state.settings.classifier_threshold ?? 0.35) });
  const topK = el('input', { type: 'number', min: '1', max: '1000', value: '75', title: 'Maximum labels/tags to keep from the model output' });
  const applyTags = el('input', { type: 'checkbox' });
  const rt = modelRuntimeControls();
  return card(title, [
    el('p', { class: 'muted' }, description),
    el('div', { class: 'muted tiny' }, `Target: ${(getMediaIds() || []).length} media item(s)`),
    el('div', { class: 'row' }, [model, el('label', {}, ['Threshold', threshold]), el('label', {}, ['Top-K', topK]), el('label', {}, [applyTags, ' Apply predicted tags/ratings'])]),
    modelLifecycleStrip(selectedModel(), true),
    el('div', { class: 'row' }, [rt.device, rt.gpuIds, rt.shard, rt.dtype, rt.quant, rt.runtime, rt.parallel]),
    rt.maxMemory,
    el('button', { class: 'primary', disabled: modelBusy(selectedModel(), ['download', 'load']), onclick: async () => {
      try {
        if (modelBusy(selectedModel(), ['download', 'load'])) throw new Error('Selected model is downloading or loading. Wait for the status circle to finish before running inference.');
        const mediaIds = [...new Set((getMediaIds() || []).map(Number).filter(Boolean))];
        if (!mediaIds.length) throw new Error('No target media selected.');
        const selected = state.models.find(m => m.name === model.value) || {};
        const task = model.value === 'redrocket-jtp-3' ? 'tag' : (selected.kind === 'rating' ? 'rating' : (selected.kind === 'captioner' ? 'caption' : 'tag'));
        setOptimisticModelStage(model.value, 'load', modelLoaded(model.value) ? 'completed' : 'running', modelLoaded(model.value) ? 1 : 0.03, modelLoaded(model.value) ? 'Model already loaded for tag selection' : 'Auto-loading selected model for tag selection');
        setOptimisticModelStage(model.value, 'inference', 'running', 0.01, 'Tag-selection request sent');
        updateLiveStatusDom();
        render(true, true);
        const body = {
          media_ids: mediaIds,
          model_name: model.value,
          task,
          threshold: Number(threshold.value || 0.35),
          apply_tags: applyTags.checked,
          apply_caption: false,
          ...runtimeBodyFromControls(rt),
          parallel_workers: Number(rt.parallel.value || 1),
          options: { tag_profile: state.tagProfile, top_k: Number(topK.value || 75) }
        };
        const r = await api('/api/models/run', { method: 'POST', body });
        state.lastModelRunJob = r.job_id;
        toast(`Model job ${r.job_id} queued. Staying on this page.`);
        await refreshAll();
        await refreshCompletedModelJobById(r.job_id);
        render();
      } catch (err) { toast(err.message, false); }
    } }, 'Run Tag/Rating Model')
  ]);
}



function taskForOrchestratorRecommendation(rec) {
  const kind = String(rec?.kind || '').toLowerCase();
  const caps = new Set(((state.models || []).find(m => m.name === rec?.model_name)?.capabilities || []).map(x => String(x).toLowerCase()));
  if (kind === 'rating' || caps.has('rating')) return 'rating';
  if (kind === 'captioner' || caps.has('caption')) return 'caption';
  if (kind === 'segmentation' || caps.has('segment')) return 'segment';
  if (kind === 'classifier' || kind === 'detection' || caps.has('classify') || caps.has('detect')) return 'classify';
  return 'tag';
}
function orchestratorPlannerCard(contextLabel = 'assistant') {
  const assistantModels = sortedModels(state.models.filter(assistantCapableModelFilter));
  const configuredOrchestrator = state.assistantConfig?.orchestrator_model_name || state.settings.orchestrator_model_name || state.settings.assistant_model_name || 'dataset-assistant';
  const orchestrator = el('select', { class: 'model-category-select', title: 'Select the LLM/VLM that will act as the user-approved orchestrator.' }, assistantModels.map(modelOptionNode));
  setSelectValue(orchestrator, configuredOrchestrator);
  const modelPick = el('select', { multiple: 'multiple', size: 8, class: 'model-category-select', title: 'Optional: choose exact models the orchestrator may run. Leave blank to let the planner recommend from the task list.' }, sortedModels(state.models).map(modelOptionNode));
  const tasks = el('select', { multiple: 'multiple', size: 7, title: 'Tasks the orchestrator should plan for.' }, ['tag_select','tag','caption','classify','rating','detection','segmentation'].map(x => el('option', { value: x }, x)));
  [...tasks.options].forEach(o => { if (['tag_select','tag'].includes(o.value)) o.selected = true; });
  const gpuIds = el('input', { value: (state.settings.default_model_device_ids || [0]).join(','), placeholder: 'preferred GPU ids: 0,1' });
  const shard = el('select', {}, ['none','auto','balanced','balanced_low_0','sequential','custom'].map(x => el('option', { value: x }, x))); shard.value = state.settings.default_model_sharding_strategy || 'none';
  const dtype = el('select', {}, ['auto','float16','bfloat16','float32'].map(x => el('option', { value: x }, x))); dtype.value = state.settings.default_model_dtype || 'auto';
  const quant = el('select', {}, ['none','8bit','4bit'].map(x => el('option', { value: x }, x))); quant.value = state.settings.default_model_quantization || 'none';
  const goal = el('textarea', { rows: 3, placeholder: 'What should the orchestrator accomplish?' }, `Recommend a user-approved ${contextLabel} plan for selected media, including which models to run and GPU placement.`);
  const approved = el('input', { type: 'checkbox' });
  const recommendations = state.orchestratorPlan?.recommendations || [];
  return card('User-Approved Assistant / Orchestrator Run Planner', [
    el('p', { class: 'muted' }, 'The orchestrator can recommend multiple model runs and GPU placements, including multi-GPU/sharded loads. Nothing is queued until you review the feedback and check user approval.'),
    el('div', { class: 'row' }, [el('label', {}, ['Orchestrator ', orchestrator]), el('label', {}, ['Tasks ', tasks]), el('label', {}, ['GPU ids ', gpuIds]), shard, dtype, quant]),
    el('label', { class: 'label' }, ['Optional exact target models', modelPick]),
    goal,
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => { try { state.assistantConfig = await api('/api/models/assistant-config', { method: 'PUT', body: { orchestrator_model_name: orchestrator.value, assistant_allow_orchestration: true } }); state.settings.orchestrator_model_name = state.assistantConfig.orchestrator_model_name; state.settings.assistant_allow_orchestration = true; toast(`${orchestrator.value} assigned as orchestrator`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Assign Selected Orchestrator'),
      el('button', { class: 'primary', onclick: async () => { try { const targetNames = [...modelPick.selectedOptions].map(o => o.value); const taskNames = [...tasks.selectedOptions].map(o => o.value); state.orchestratorPlan = await api('/api/models/orchestrator/plan', { method: 'POST', body: { orchestrator_model_name: orchestrator.value, target_model_names: targetNames, tasks: taskNames, context: contextLabel, media_ids: selectedMediaIds(), device_ids: parseGpuIds(gpuIds.value), sharding_strategy: shard.value, torch_dtype: dtype.value, quantization: quant.value, require_user_approval: true, max_models: 16 } }); toast(`Planner returned ${state.orchestratorPlan.recommendations?.length || 0} recommendation(s)`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Recommend Models + GPUs'),
      el('label', {}, [approved, ' I reviewed and approve queueing runnable recommendations']),
      el('button', { class: 'danger', disabled: !recommendations.length, onclick: async () => { try { if (!approved.checked) throw new Error('Check user approval before queueing orchestrator-planned model runs.'); const runs = (state.orchestratorPlan?.recommendations || []).filter(r => r.can_load !== false && r.queue_supported !== false).map(r => ({ model_name: r.model_name, task: taskForOrchestratorRecommendation(r), media_ids: selectedMediaIds(), threshold: state.settings.classifier_threshold || 0.35, apply_tags: false, apply_caption: false, device: 'auto', device_ids: (r.placement?.device_ids || r.placement?.selected_device_ids || []).map(Number).filter(Number.isFinite), sharding_strategy: r.placement?.sharding_strategy || shard.value || 'none', torch_dtype: dtype.value || 'auto', quantization: quant.value || 'none', runtime_engine: state.settings.default_model_runtime_engine || 'transformers', tensor_parallel_size: Math.max(1, (r.placement?.device_ids || []).length || 1), options: { orchestrated_by: orchestrator.value, tag_profile: state.tagProfile } })); if (!runs.length) throw new Error('No runnable recommendations are available to queue.'); const queued = await api('/api/models/orchestrator/queue-runs', { method: 'POST', body: { orchestrator_model_name: orchestrator.value, user_approved: true, runs } }); toast(`Queued ${queued.count} orchestrator-approved model run(s)`); await refreshAll(); setTab('Jobs'); } catch (err) { toast(err.message, false); } } }, 'Queue Approved Recommendations')
    ]),
    recommendations.length ? el('div', { class: 'orchestrator-recommendations' }, recommendations.map(rec => { const info = modelCategoryDisplay(rec); const errors = rec.errors || []; return el('div', { class: `orchestrator-rec ${errors.length ? 'blocked' : 'ok'}`, style: `--model-category-color:${info.color};` }, [el('strong', {}, `${rec.label || rec.model_name} · ${rec.kind || 'model'}`), el('div', { class: 'muted tiny' }, rec.recommendation || ''), el('div', { class: 'tiny' }, `GPU(s): ${(rec.placement?.device_ids || rec.placement?.selected_device_ids || []).map(x => 'cuda:' + x).join(', ') || 'none/API/CPU'} · can load: ${rec.can_load !== false}`), errors.length ? el('div', { class: 'bad tiny' }, errors.join(' ')) : null].filter(Boolean)); })) : (state.orchestratorPlan ? el('pre', { class: 'log' }, JSON.stringify(state.orchestratorPlan, null, 2)) : null)
  ].filter(Boolean));
}

function inlineOrchestratorControls(modelSelect, contextLabel = 'assistant') {
  const current = state.assistantConfig?.orchestrator_model_name || state.settings.orchestrator_model_name || state.settings.assistant_model_name || 'dataset-assistant';
  const allow = el('input', { type: 'checkbox', checked: state.assistantConfig?.assistant_allow_orchestration !== false && state.settings.assistant_allow_orchestration !== false });
  return el('details', { class: 'inline-orchestrator-control' }, [
    el('summary', {}, `Assistant/orchestrator control · current: ${current}`),
    el('p', { class: 'muted tiny' }, 'Use this to promote the selected LLM/VLM as the application orchestrator from this assistant-enabled tab. Orchestrator model runs are user-approved: the app can recommend model/GPU placement before anything is queued.'),
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', onclick: async () => {
        try {
          const chosen = modelSelect.value || current || 'dataset-assistant';
          state.assistantConfig = await api('/api/models/assistant-config', { method: 'PUT', body: { orchestrator_model_name: chosen, assistant_allow_orchestration: allow.checked } });
          state.settings.orchestrator_model_name = state.assistantConfig.orchestrator_model_name;
          state.settings.assistant_allow_orchestration = state.assistantConfig.assistant_allow_orchestration;
          toast(`${chosen} assigned as orchestrator for ${contextLabel}`);
          render(true, true);
        } catch (err) { toast(err.message, false); }
      } }, 'Set selected as orchestrator'),
      el('button', { class: 'secondary small', onclick: async () => {
        try {
          const chosen = modelSelect.value || current || 'dataset-assistant';
          state.orchestratorPlan = await api('/api/models/orchestrator/plan', { method: 'POST', body: { orchestrator_model_name: current, target_model_names: [chosen], tasks: ['tag_select'], media_ids: [...state.selected], goal: `Plan user-approved ${contextLabel} model run with GPU placement recommendations`, require_user_approval: true } });
          toast('Orchestrator GPU/model recommendation generated');
          render(true, true);
        } catch (err) { toast(err.message, false); }
      } }, 'Recommend GPUs / run plan'),
      el('label', {}, [allow, ' allow orchestration'])
    ]),
    state.orchestratorPlan ? el('pre', { class: 'log tiny-log' }, JSON.stringify(state.orchestratorPlan, null, 2)) : null
  ].filter(Boolean));
}


function inlineSelectedModelRuntimeControls(modelSelect, rt, contextLabel = 'assistant') {
  const m = (state.models || []).find(row => row.name === modelSelect.value) || { name: modelSelect.value, label: modelSelect.value, capabilities: [] };
  if (!m?.name) return null;
  const downloadActive = stageActive(m, 'download');
  const loadActive = stageActive(m, 'load');
  const inferenceActive = stageActive(m, 'inference');
  const isLoaded = modelLoaded(m) || Boolean(m.loaded);
  const placementControls = { body: () => ({ model_name: m.name, ...runtimeBodyFromControls(rt), options: { tag_profile: state.tagProfile, source_tab: state.tab, context: contextLabel } }) };
  const statusBits = modelStatusBits(m).join(' / ') || m.status_summary || (isLoaded ? 'loaded' : m.downloaded ? 'downloaded' : 'not downloaded');
  return el('details', { class: 'inline-model-runtime-controls' }, [
    el('summary', {}, `Selected model controls · ${m.label || m.name} · ${statusBits}`),
    el('p', { class: 'muted tiny' }, 'Use these only when you need explicit placement/download/load control from this tab. The main dropdown stays compact; GPU ids, sharding, dtype, quantization, and runtime are sent with chat/tag requests.'),
    el('div', { class: 'chips open' }, [
      el('span', { class: 'chip' }, m.kind || 'model'),
      el('span', { class: 'chip' }, m.provider || 'provider'),
      m.downloaded ? el('span', { class: 'chip downloaded-model-chip' }, 'DOWNLOADED') : (m.download_supported ? el('span', { class: 'chip missing-model-chip' }, 'NOT DOWNLOADED') : null),
      isLoaded ? el('span', { class: `chip ${(m.offloaded_to_cpu || (m.loaded_instances || []).some(x => x && x.offloaded_to_cpu)) ? 'cpu-offloaded-chip' : 'loaded-instance-chip'}` }, `${(m.offloaded_to_cpu || (m.loaded_instances || []).some(x => x && x.offloaded_to_cpu)) ? 'CPU OFFLOADED' : 'LOADED'} x${modelLoadedInstanceCount(m) || 1}`) : null,
      modelMemorySummary(m) ? el('span', { class: 'chip', title: modelMemoryTitle(m) }, modelMemorySummary(m)) : null
    ].filter(Boolean)),
    el('div', { class: 'row tight' }, [rt.device, rt.gpuIds, rt.shard, rt.dtype, rt.quant, rt.runtime, el('label', {}, ['TP', rt.tensorParallel])]),
    rt.maxMemory,
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', disabled: !m.download_supported || downloadActive || loadActive, onclick: async () => { await queueModelDownload(m, false); } }, m.downloaded ? 'Queue Update' : 'Queue Download'),
      el('button', { class: 'primary small', disabled: downloadActive || loadActive || isLoaded, onclick: async () => { await queueModelLoad(m, placementControls); } }, isLoaded ? 'Loaded' : 'Load Into Memory'),
      el('button', { class: 'secondary small', disabled: loadActive || inferenceActive, onclick: async () => { try { await api('/api/models/offload-cpu', { method: 'POST', body: { model_name: m.name } }); await refreshAll(); toast(`Moved ${m.label || m.name} to CPU RAM where supported`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Offload CPU'),
      el('button', { class: 'secondary small', disabled: loadActive || inferenceActive, onclick: async () => { try { const r = await api('/api/models/unload', { method: 'POST', body: { model_name: m.name } }); await refreshAll(); toast(r.job_id ? `Unload queued as job ${r.job_id}` : (r.message || `No loaded adapter for ${m.label || m.name}`)); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Unload'),
      el('button', { class: 'secondary small', onclick: async () => { try { state.modelPlacementPlans[m.name] = await api('/api/models/placement/plan', { method: 'POST', body: placementControls.body() }); toast('Placement check updated'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Check VRAM')
    ]),
    state.modelPlacementPlans?.[m.name] ? el('div', { class: `tiny ${state.modelPlacementPlans[m.name].errors?.length ? 'bad-text' : 'ok-text'}` }, planStatusText(state.modelPlacementPlans[m.name])) : null
  ].filter(Boolean));
}


function agentToolModelOptions() {
  const rows = sortedModels((state.models || []).filter(m => {
    const caps = modelKindSet(m);
    return caps.has('chat') || caps.has('llm') || caps.has('vlm') || caps.has('assistant') || caps.has('orchestration') || modelIsApi(m);
  }));
  return rows.length ? rows.map(modelOptionNode) : modelOptions();
}
function currentSurfaceModelName(fallback = 'dataset-assistant') {
  return state.tagSelectionModelSelection || state.assistantModelSelection || state.codeModelSelection || state.agentModelSelection || state.assistantConfig?.orchestrator_model_name || state.settings?.orchestrator_model_name || fallback;
}
async function refreshAgentToolsStatus() { state.agentStatus = await api('/api/agent-tools/status'); return state.agentStatus; }
function agentApprovalControls(compact = false) {
  const approved = el('input', { type: 'checkbox', checked: Boolean(state.agentUserApproved), onchange: e => { state.agentUserApproved = e.target.checked; } });
  const coa = el('input', { type: 'checkbox', checked: Boolean(state.agentCoaExecutionEnabled || state.settings?.agent_tools_enable_approved_coa_execution), onchange: e => { state.agentCoaExecutionEnabled = e.target.checked; } });
  const high = el('input', { type: 'checkbox', checked: Boolean(state.agentAllowHighRisk), onchange: e => { state.agentAllowHighRisk = e.target.checked; } });
  const confirmText = el('input', { value: state.agentHighRiskConfirmation || '', placeholder: 'RUN HIGH RISK ACTION', style: compact ? 'min-width:220px' : 'min-width:320px', oninput: e => { state.agentHighRiskConfirmation = e.target.value; } });
  return el('div', { class: `agent-approval row ${compact ? 'compact' : ''}` }, [
    el('label', {}, [approved, ' approve next local action']),
    el('label', { title: 'Allows a reviewed COA/tool plan to run sequentially as visible jobs after approval.' }, [coa, ' enable approved COA execution']),
    el('label', {}, [high, ' high-risk with confirmation']),
    confirmText
  ]);
}
function agentPlanStepCard(step, idx, surfaceKey = 'global') {
  const tool = String(step.tool || step.name || 'manual').toLowerCase();
  const args = step.arguments || step.args || {};
  const command = step.command || step.script || args.command || args.script || '';
  const risk = String(step.risk || 'low').toLowerCase();
  const cls = risk === 'high' ? 'bad' : risk === 'medium' ? 'warn' : 'ok';
  const toolCall = { tool: tool, arguments: Object.keys(args).length ? args : { command, script: command, cwd: step.cwd || state.agentCwd || undefined, shell: step.shell || state.agentShell || 'auto' } };
  const runButton = tool === 'manual' ? null : el('button', { class: 'primary small', onclick: async () => {
    try {
      const r = await api('/api/agent-tools/execute-tool-call', { method: 'POST', body: { tool_call: toolCall, user_approved: state.agentUserApproved, allow_high_risk: state.agentAllowHighRisk, confirmation_text: state.agentHighRiskConfirmation || '' } });
      state.agentLastResult = r; state.jobs = await api('/api/jobs'); toast(`Queued agent tool step as job #${r.job_id}`); render(true, true);
    } catch (err) { toast(err.message, false); render(true, true); }
  } }, 'Run Approved Tool Call');
  return el('div', { class: 'agent-step' }, [
    el('div', { class: 'row' }, [el('strong', {}, `${idx + 1}. ${step.title || tool || 'Plan step'}`), el('span', { class: `badge ${cls}` }, risk), el('span', { class: 'badge' }, tool)]),
    el('p', { class: 'muted' }, step.note || step.description || 'Review this step before approval.'),
    command ? el('pre', { class: 'log compact' }, command) : (Object.keys(args).length ? el('pre', { class: 'log compact' }, JSON.stringify(args, null, 2)) : null),
    runButton
  ].filter(Boolean));
}
function agentPlanPayloadForRun(planPayload) {
  if (!planPayload) return null;
  if (Array.isArray(planPayload.tool_calls) && planPayload.tool_calls.length) return planPayload.tool_calls;
  if (planPayload.plan) return planPayload.plan;
  if (Array.isArray(planPayload.steps) || Array.isArray(planPayload.actions) || Array.isArray(planPayload.tool_calls)) return planPayload;
  if (typeof planPayload === 'string') return planPayload;
  return planPayload.response || planPayload;
}
function agentToolDecisionBadge(decision) {
  if (!decision) return null;
  const mode = String(decision.mode || 'unknown');
  const needs = decision.tools_needed ? 'tools needed' : (decision.gui_action_needed ? 'GUI action' : 'no tool needed');
  const cls = decision.tools_needed ? 'warn' : decision.gui_action_needed ? 'queued' : 'ok';
  return el('div', { class: `agent-tool-decision badge ${cls}`, title: decision.reason || 'Tool-use decision' }, `Tool decision: ${mode} · ${needs}`);
}

async function runApprovedCoaPlan(planPayload, label = 'COA plan') {
  const plan = agentPlanPayloadForRun(planPayload);
  if (!plan) { toast('No COA/tool plan is available to run.', false); return null; }
  // The button itself is the explicit user approval for this reviewed COA plan.
  state.agentCoaExecutionEnabled = true;
  state.agentUserApproved = true;
  const r = await api('/api/agent-tools/run-plan', { method: 'POST', body: { plan, user_approved: state.agentUserApproved, allow_high_risk: state.agentAllowHighRisk, confirmation_text: state.agentHighRiskConfirmation || '', enable_for_this_run: Boolean(state.agentCoaExecutionEnabled) } });
  state.agentLastResult = r;
  state.jobs = await api('/api/jobs');
  toast(`Queued ${label} as job #${r.job_id}`);
  render(true, true);
  return r;
}


async function fetchCoaOptionsForMessage(conversationId, messageId) {
  if (!conversationId || !messageId) throw new Error('Conversation/message id is required to parse COAs.');
  const r = await api('/api/agent-tools/conversation-coas', { method: 'POST', body: { conversation_id: Number(conversationId), message_id: Number(messageId) } });
  state.agentCoaOptionsByMessage[String(messageId)] = r;
  return r;
}

function watchConversationCoaJob(scope, conversationId, jobId, reloadFn) {
  if (!jobId || state.agentCoaJobWatchers?.[jobId]) return;
  state.agentCoaJobWatchers = state.agentCoaJobWatchers || {};
  let tries = 0;
  const timer = setInterval(async () => {
    tries += 1;
    try {
      const job = await api(`/api/jobs/${jobId}`);
      if (['completed', 'failed', 'cancelled'].includes(String(job.status || '').toLowerCase()) || tries > 240) {
        clearInterval(timer);
        delete state.agentCoaJobWatchers[jobId];
        state.agentLastResult = job.result || state.agentLastResult;
        state.agentDebugLogs = await api('/api/agent-tools/debug-logs').catch(() => state.agentDebugLogs);
        if (conversationId && reloadFn) await reloadFn(conversationId).catch(() => null);
        toast(`COA job #${jobId} ${job.status}; tool output has been imported into the conversation when available.`, job.status === 'completed');
        render(true, true);
      }
    } catch (_) {
      if (tries > 240) { clearInterval(timer); delete state.agentCoaJobWatchers[jobId]; }
    }
  }, 1500);
  state.agentCoaJobWatchers[jobId] = timer;
}
async function runConversationCoaFromMessage(scope, conversationId, messageId, coaIndex = 0, opts = {}) {
  if (!conversationId || !messageId) throw new Error('Conversation/message id is required to run a COA.');
  // The clicked Approve + Run button is the explicit user approval for this reviewed COA.
  state.agentCoaExecutionEnabled = true;
  state.agentUserApproved = true;
  const runtime = opts.runtimeControls ? runtimeBodyFromControls(opts.runtimeControls) : defaultRuntimeBody({});
  const modelName = typeof opts.modelName === 'function' ? opts.modelName() : (opts.modelName || currentSurfaceModelName() || 'dataset-assistant');
  const body = {
    conversation_id: Number(conversationId),
    message_id: Number(messageId),
    coa_index: Number(coaIndex || 0),
    user_approved: true,
    allow_high_risk: Boolean(state.agentAllowHighRisk),
    confirmation_text: state.agentHighRiskConfirmation || '',
    enable_for_this_run: Boolean(state.agentCoaExecutionEnabled),
    relay_result: true,
    model_name: modelName,
    surface: opts.surface || scope || state.tab || 'assistant',
    context: typeof opts.context === 'function' ? opts.context() : (opts.context || ''),
    ...runtime,
    options: { max_new_tokens: 2048, auto_continue_incomplete: true, chat_assistant: true, agent_tools_chat: true, ...(opts.options || {}) }
  };
  const r = await api('/api/agent-tools/run-conversation-coa', { method: 'POST', body });
  state.agentCoaRunJobs[String(messageId)] = r.job_id;
  state.agentLastResult = r;
  state.lastModelRunJob = r.job_id;
  state.jobDetailId = r.job_id;
  toast(`Approved COA queued as job #${r.job_id}. Open Jobs for full stdout/stderr/debug details.`);
  watchConversationCoaJob(scope, conversationId, r.job_id, opts.reload);
  state.jobs = await api('/api/jobs').catch(() => state.jobs);
  render(true, true);
  return r;
}
function assistantMessageCoaControls(scope, conversationId, message, opts = {}) {
  if (!conversationId || !message?.id) return null;
  const msgId = String(message.id);
  const parsed = state.agentCoaOptionsByMessage[msgId];
  const coas = parsed?.options || [];
  return el('div', { class: 'coa-controls' }, [
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', title: 'Parse this assistant response/visible plan for PowerShell, CMD, Bash, Python, file, URL, or browser tool calls.', onclick: async () => { try { const r = await fetchCoaOptionsForMessage(conversationId, message.id); toast(r.count ? `Found ${r.count} executable COA option(s).` : 'No executable COA/tool calls were found in that message.', Boolean(r.count)); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Find COAs / Tool Calls'),
      el('label', { class: 'tiny', title: 'Whole-plan execution still requires this checkbox and user approval.' }, [el('input', { type: 'checkbox', checked: Boolean(state.agentCoaExecutionEnabled || state.settings?.agent_tools_enable_approved_coa_execution), onchange: e => { state.agentCoaExecutionEnabled = e.target.checked; } }), ' enable COA execution']),
      el('label', { class: 'tiny', title: 'Approve the next local action or plan execution.' }, [el('input', { type: 'checkbox', checked: Boolean(state.agentUserApproved), onchange: e => { state.agentUserApproved = e.target.checked; } }), ' approve next action'])
    ]),
    coas.length ? el('div', { class: 'coa-option-list' }, coas.map((coa, idx) => el('button', { class: 'primary small', title: coa.summary || coa.title || `COA ${idx + 1}`, onclick: async () => { try { await runConversationCoaFromMessage(scope, conversationId, message.id, idx, opts); } catch (err) { toast(err.message, false); } } }, `Approve + Run ${coa.title || 'COA ' + (idx + 1)} (${(coa.tool_calls || []).length} step${(coa.tool_calls || []).length === 1 ? '' : 's'})`))) : null,
    parsed && !coas.length ? el('div', { class: 'muted tiny' }, 'No executable action blocks were detected by the parser. You can keep chatting immediately, paste/correct a JSON tool_calls block, or ask the model to output PowerShell:/Python:/Bash: blocks.') : null,
    state.agentCoaRunJobs[msgId] ? el('div', { class: 'muted tiny' }, `Last COA run job: #${state.agentCoaRunJobs[msgId]}`) : null
  ].filter(Boolean));
}

function agentSurfaceContext(surfaceLabel, getMediaIds = () => []) {
  const ids = [...new Set((getMediaIds() || []).map(Number).filter(Boolean))];
  const items = ids.map(id => state.selectedMediaCache[String(id)] || (state.media.items || []).find(x => Number(x.id) === id)).filter(Boolean);
  return JSON.stringify({
    surface: surfaceLabel,
    tab: state.tab,
    tag_profile: state.tagProfile,
    selected_media_ids: ids,
    media: items.map(item => ({ id: item.id, path: item.path, relative_path: item.relative_path, tags: item.tags || [], caption: item.caption || '' })).slice(0, 8),
    selected_tags: state.tab === 'Compare' ? { left: [...state.compareSelected.left], right: [...state.compareSelected.right] } : state.editorAssistantSelection || {},
    current_model: currentSurfaceModelName()
  }, null, 2);
}
function agentToolsInlinePanel(surfaceKey, surfaceLabel, getMediaIds = () => [], modelSelect = null, rt = null) {
  const draftKey = `agent-${surfaceKey}`;
  const goalText = state.agentSurfaceDrafts[draftKey] ?? `Plan a user-approved tool workflow for ${surfaceLabel}. Inspect relevant context first, then propose commands/scripts only if needed.`;
  const goal = el('textarea', { rows: 3, style: 'width:100%', value: goalText, placeholder: 'Ask the assistant/orchestrator to plan tool use for this tab/context.', oninput: e => { state.agentSurfaceDrafts[draftKey] = e.target.value; } });
  const planPayload = state.agentSurfacePlans[draftKey];
  const plan = planPayload?.plan || null;
  const selectedModelName = modelSelect?.value || currentSurfaceModelName();
  const context = () => agentSurfaceContext(surfaceLabel, getMediaIds);
  return el('details', { class: 'agent-tools-inline' }, [
    el('summary', {}, `Agent tools for this ${surfaceLabel} assistant`),
    el('p', { class: 'muted tiny' }, 'Structured function-call style tools are available from this assistant surface. The model can propose terminal/Python/file/browser actions, but each local action still requires visible approval.'),
    agentApprovalControls(true),
    goal,
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', onclick: () => setTab('Agent Tools') }, 'Open Full Agent Tools Tab'),
      el('button', { class: 'primary small', onclick: async () => {
        try {
          const ids = [...new Set((getMediaIds() || []).map(Number).filter(Boolean))]; const mediaRows = ids.map(id => state.selectedMediaCache[String(id)] || (state.media.items || []).find(x => Number(x.id) === id)).filter(Boolean); const body = { goal: goal.value, context: context(), media_ids: ids, external_paths: mediaRows.map(x => x.path).filter(Boolean), surface: surfaceLabel, model_name: selectedModelName || 'dataset-assistant', ...(rt ? runtimeBodyFromControls(rt) : {}), options: { max_new_tokens: 2048, auto_continue_incomplete: true, ...reasoningOptionsFromControls(null, { min_chat_max_new_tokens: 2048 }) } };
          setOptimisticModelStage(body.model_name, 'inference', 'running', 0.02, 'Agent tool plan requested'); updateLiveStatusDom();
          const r = await api('/api/agent-tools/plan', { method: 'POST', body });
          state.agentSurfacePlans[draftKey] = r; state.agentConversationId = r.conversation_id || state.agentConversationId; toast('Tool-use assessment/plan generated for this assistant surface'); await refreshModelStatuses(false).catch(() => {}); render(true, true);
        } catch (err) { toast(err.message, false); render(true, true); }
      } }, 'Assess / Plan Tool Use If Needed'),
      el('button', { class: 'secondary small', onclick: async () => { try { await refreshAgentToolsStatus(); toast('Agent tool status refreshed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Refresh Tool Status'),
      state.agentLastResult?.job_id ? el('button', { class: 'secondary small', onclick: async () => { try { const r = await api('/api/agent-tools/relay-result', { method: 'POST', body: { job_id: state.agentLastResult.job_id, model_name: selectedModelName || 'dataset-assistant', conversation_id: state.agentConversationId || null, surface: surfaceLabel, context: context(), ...(rt ? runtimeBodyFromControls(rt) : {}), options: { max_new_tokens: 2048, auto_continue_incomplete: true, ...reasoningOptionsFromControls(null, { min_chat_max_new_tokens: 2048 }) } } }); state.agentConversationId = r.conversation_id || state.agentConversationId; state.agentSurfacePlans[draftKey] = { ...(state.agentSurfacePlans[draftKey] || {}), last_relay: r }; toast('Tool result relayed back to assistant'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Relay Last Tool Result') : null
    ].filter(Boolean)),
    state.agentStatus ? el('div', { class: 'muted tiny' }, `Workspace: ${state.agentStatus.workspace} · sandbox: ${state.agentStatus.sandbox_mode || 'workspace'} · docker: ${state.agentStatus.docker_available ? 'available' : 'not found'}`) : null,
    agentDebugLogsPanel(true),
    planPayload?.tool_decision ? agentToolDecisionPill(planPayload.tool_decision) : null,
    plan ? el('div', { class: 'agent-plan' }, [
      el('h3', {}, plan.summary || (planPayload?.tool_decision?.tools_needed ? 'Proposed tool plan' : 'Tool-use assessment')),
      plan.direct_answer ? el('p', { class: 'muted' }, plan.direct_answer) : null,
      el('div', { class: 'row tight' }, [
        ((planPayload?.tool_calls || []).length || (plan.steps || plan.tool_calls || plan.actions || []).length) ? el('button', { class: 'primary small', title: 'Run every executable step sequentially as a visible job after approval.', onclick: async () => { try { await runApprovedCoaPlan(planPayload, surfaceLabel + ' COA plan'); } catch (err) { toast(err.message, false); } } }, 'Approve + Run COA Plan') : null,
        el('span', { class: 'muted tiny' }, 'Clicking Approve + Run is the approval for this reviewed COA. High-risk steps still require the high-risk confirmation text.')
      ]),
      ...((plan.steps || plan.tool_calls || plan.actions || []).map((step, idx) => agentPlanStepCard(step, idx, surfaceKey))),
      (planPayload?.tool_calls || []).length ? el('details', {}, [el('summary', {}, 'Parsed tool calls from model response'), el('pre', { class: 'log compact' }, JSON.stringify(planPayload.tool_calls, null, 2))]) : null, planPayload?.debug_log_path ? el('details', {}, [el('summary', {}, 'Planner debug log path'), el('pre', { class: 'log compact' }, planPayload.debug_log_path)]) : null
    ].filter(Boolean)) : null
  ].filter(Boolean));
}
function agentDebugLogsPanel(compact = false) {
  const logs = state.agentDebugLogs?.logs || [];
  return el('div', { class: 'agent-debug-panel' }, [
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', onclick: async () => { try { state.agentDebugLogs = await api('/api/agent-tools/debug-logs'); toast('Agent debug logs refreshed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Refresh Agent Debug Logs'),
      state.agentDebugLogContent ? el('button', { class: 'secondary small', onclick: () => { state.agentDebugLogContent = null; render(true, true); } }, 'Hide Open Debug Log') : null
    ].filter(Boolean)),
    logs.length ? el('div', { class: 'debug-log-list' }, logs.slice(0, compact ? 8 : 30).map(row => el('div', { class: 'row tight' }, [
      el('span', { class: 'muted tiny', title: row.path }, `${row.name} · ${Math.round(Number(row.size_bytes || 0) / 1024)}KB`),
      el('button', { class: 'secondary tiny', onclick: async () => { try { state.agentDebugLogContent = await api(`/api/agent-tools/debug-log?path=${encodeURIComponent(row.path || row.name)}&max_chars=240000`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Open')
    ]))) : el('div', { class: 'muted tiny' }, 'No agent debug logs found yet.'),
    state.agentDebugLogContent ? el('details', { open: true }, [el('summary', {}, `Open debug log: ${state.agentDebugLogContent.path || ''}`), el('pre', { class: 'log full-log' }, state.agentDebugLogContent.content || JSON.stringify(state.agentDebugLogContent, null, 2))]) : null
  ].filter(Boolean));
}

function agentToolsView() {
  const model = el('select', {}, agentToolModelOptions());
  const preferred = (state.models || []).find(m => m.name === state.agentModelSelection) || (state.models || []).find(m => m.name === state.assistantConfig?.orchestrator_model_name) || (state.models || []).find(m => m.name === 'dataset-assistant') || (state.models || [])[0];
  rememberSelect('agentModelSelection', model, preferred?.name || 'dataset-assistant', false);
  model.addEventListener('change', () => { state.agentModelSelection = model.value || ''; primeModelLifecycleForSelection(model.value); updateLiveStatusDom(); });
  const rt = modelRuntimeControls();
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value };
  const goal = el('textarea', { rows: 5, style: 'width:100%', value: state.agentGoal || '', placeholder: 'Describe the task to plan/execute with tools.', oninput: e => { state.agentGoal = e.target.value; } });
  const context = el('textarea', { rows: 4, style: 'width:100%', value: state.agentContext || '', placeholder: 'Optional context / target paths / constraints.', oninput: e => { state.agentContext = e.target.value; } });
  const cwd = el('input', { value: state.agentCwd || state.agentStatus?.workspace || '', placeholder: 'working directory', style: 'min-width:420px', oninput: e => { state.agentCwd = e.target.value; } });
  const shell = el('select', { onchange: e => { state.agentShell = e.target.value; } }, ['auto','powershell','cmd','batch','bash','sh'].map(x => el('option', { value: x }, x))); shell.value = state.agentShell || 'auto';
  const timeout = el('input', { type: 'number', min: '1', max: String(state.agentStatus?.max_timeout_seconds || 1800), value: state.agentTimeout || 120, oninput: e => { state.agentTimeout = Number(e.target.value || 120); } });
  const command = el('textarea', { rows: 4, style: 'width:100%', value: state.agentCommand || '', placeholder: 'Approved shell/PowerShell/CMD/Bash command', oninput: e => { state.agentCommand = e.target.value; } });
  const py = el('textarea', { rows: 8, style: 'width:100%', value: state.agentPythonScript || '', placeholder: 'Approved Python script generated by you or the model. You can include # requirements: pillow requests etc.', oninput: e => { state.agentPythonScript = e.target.value; } });
  const pyReqs = el('textarea', { rows: 2, style: 'width:100%', value: state.agentPythonRequirements || '', placeholder: 'Optional pip requirements, one per line or comma-separated. Parsed model tool calls can also include requirements[].', oninput: e => { state.agentPythonRequirements = e.target.value; } });
  const pyVenv = el('input', { type: 'checkbox', checked: state.agentPythonCreateVenv !== false, onchange: e => { state.agentPythonCreateVenv = e.target.checked; } });
  const pathInput = el('input', { value: state.agentPath || state.agentCwd || state.agentStatus?.workspace || '', placeholder: 'file/folder path', style: 'min-width:420px', oninput: e => { state.agentPath = e.target.value; } });
  const url = el('input', { value: state.agentUrl || 'about:blank', placeholder: 'URL', style: 'min-width:420px', oninput: e => { state.agentUrl = e.target.value; } });
  const profile = el('input', { value: state.agentBrowserProfilePath || state.settings?.agent_tools_browser_profile_path || '', placeholder: 'optional Firefox profile path', style: 'min-width:420px', oninput: e => { state.agentBrowserProfilePath = e.target.value; } });
  const useProfile = el('input', { type: 'checkbox', checked: Boolean(state.agentUseExistingProfile), onchange: e => { state.agentUseExistingProfile = e.target.checked; } });
  const plan = state.agentPlan?.plan || null;
  const lastJob = state.agentLastResult?.job_id ? (state.jobs || []).find(j => Number(j.id) === Number(state.agentLastResult.job_id)) : null;
  return el('div', { class: 'grid' }, [
    card('Agent Tools: Function-Calling Runtime for the Assistant/Orchestrator', [
      el('p', { class: 'muted' }, 'This implements the standard tool pipeline: tool definitions → structured JSON/tool-call proposal → user approval → secure local execution → result/log relay back through jobs. It is available here and inside assistant panels on Tag Editor, Compare, Batch Tags, Code Assistant, and Assistant.'),
      el('div', { class: 'row' }, [model, el('button', { class: 'secondary', onclick: async () => { try { await refreshAgentToolsStatus(); toast('Agent tool status refreshed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Refresh Tool Status'), el('button', { class: 'secondary', onclick: async () => { try { state.agentStatus = { ...(state.agentStatus || {}), smoke_test: await api('/api/agent-tools/smoke-test', { method: 'POST' }) }; toast('Agent tool smoke test completed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Run Tool Smoke Test')]),
      modelLifecycleStrip(selectedModel(), true),
      inlineSelectedModelRuntimeControls(model, rt, 'agent-tools'),
      state.agentStatus ? el('pre', { class: 'log compact' }, JSON.stringify({ workspace: state.agentStatus.workspace, allowed_roots: state.agentStatus.allowed_roots, sandbox_mode: state.agentStatus.sandbox_mode, docker_available: state.agentStatus.docker_available, require_user_approval: state.agentStatus.require_user_approval, enable_approved_coa_execution: state.agentStatus.enable_approved_coa_execution, tool_binaries: state.agentStatus.tool_binaries, smoke_test: state.agentStatus.smoke_test }, null, 2)) : null
    ]),
    card('Plan First', [el('p', { class: 'muted tiny' }, 'The planner now explicitly decides whether the task needs no tool, an app/GUI action, external local tools, model delegation, or a mixed COA. No-tool tasks should answer normally instead of fabricating actions.'), goal, context, el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: async () => { try { const r = await api('/api/agent-tools/plan', { method: 'POST', body: { goal: goal.value, context: context.value, model_name: model.value || 'dataset-assistant', surface: 'Agent Tools', ...runtimeBodyFromControls(rt), options: { max_new_tokens: 2048, auto_continue_incomplete: true, ...reasoningOptionsFromControls(null, { min_chat_max_new_tokens: 2048 }) } } }); state.agentPlan = r; state.agentConversationId = r.conversation_id || state.agentConversationId; toast('Tool-use assessment/plan generated'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Assess / Generate Plan If Needed'),
      plan && ((state.agentPlan?.tool_calls || []).length || (plan.steps || plan.actions || plan.tool_calls || []).length) ? el('button', { class: 'primary', onclick: async () => { try { await runApprovedCoaPlan(state.agentPlan, 'Agent Tools COA plan'); } catch (err) { toast(err.message, false); } } }, 'Approve + Run COA Plan') : null,
      state.agentConversationId ? el('span', { class: 'badge' }, `conversation #${state.agentConversationId}`) : null
    ].filter(Boolean)), plan ? el('div', { class: 'agent-plan' }, [agentToolDecisionBadge(state.agentPlan?.tool_decision), el('h3', {}, plan.summary || plan.direct_answer || 'Proposed plan'), plan.direct_answer ? el('p', { class: 'muted' }, plan.direct_answer) : null, ...((plan.steps || plan.actions || plan.tool_calls || []).map((step, idx) => agentPlanStepCard(step, idx, 'global'))), (state.agentPlan?.tool_calls || []).length ? el('details', {}, [el('summary', {}, 'Parsed executable tool calls'), el('pre', { class: 'log compact' }, JSON.stringify(state.agentPlan.tool_calls, null, 2))]) : null]) : el('p', { class: 'muted' }, 'No plan generated yet.')]),
    card('Approval + Working Directory', [agentApprovalControls(false), el('div', { class: 'row' }, [cwd, shell, el('label', {}, ['timeout sec ', timeout])])]),
    card('Run Approved Command', [command, el('div', { class: 'row' }, [el('button', { class: 'secondary', onclick: async () => { try { state.agentLastResult = await api('/api/agent-tools/risk', { method: 'POST', body: { command: command.value, shell: shell.value } }); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Assess Risk'), el('button', { class: 'primary', onclick: async () => { try { const r = await api('/api/agent-tools/command', { method: 'POST', body: { command: command.value, shell: shell.value, cwd: cwd.value || undefined, timeout_seconds: Number(timeout.value || 120), user_approved: state.agentUserApproved, allow_high_risk: state.agentAllowHighRisk, confirmation_text: state.agentHighRiskConfirmation || '' } }); state.agentLastResult = r; state.jobs = await api('/api/jobs'); toast(`Queued command job #${r.job_id}`); render(true, true); } catch (err) { toast(err.message, false); render(true, true); } } }, 'Run Approved Command')])]),
    card('Run Approved Python Script', [py, pyReqs, el('label', { class: 'tiny' }, [pyVenv, ' create/use isolated agent-tools venv and install parsed requirements before running']), el('button', { class: 'primary', onclick: async () => { try { const reqs = String(pyReqs.value || '').split(/[\n,;]+/).map(x => x.trim()).filter(Boolean); const r = await api('/api/agent-tools/python', { method: 'POST', body: { script: py.value, requirements: reqs, create_venv: pyVenv.checked, cwd: cwd.value || undefined, timeout_seconds: Number(timeout.value || 120), user_approved: state.agentUserApproved, allow_high_risk: state.agentAllowHighRisk, confirmation_text: state.agentHighRiskConfirmation || '' } }); state.agentLastResult = r; state.jobs = await api('/api/jobs'); toast(`Queued Python job #${r.job_id}`); render(true, true); } catch (err) { toast(err.message, false); render(true, true); } } }, 'Run Approved Python')]),
    card('Files / URL / Browser', [el('div', { class: 'row' }, [pathInput, el('button', { class: 'secondary', onclick: async () => { try { state.agentLastResult = await api('/api/agent-tools/files/list', { method: 'POST', body: { path: pathInput.value, user_approved: state.agentUserApproved } }); render(true, true); } catch (err) { toast(err.message, false); } } }, 'List Path'), el('button', { class: 'secondary', onclick: async () => { try { state.agentLastResult = await api('/api/agent-tools/files/read', { method: 'POST', body: { path: pathInput.value, user_approved: state.agentUserApproved } }); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Read File')]), el('div', { class: 'row' }, [url, el('button', { class: 'secondary', onclick: async () => { try { state.agentLastResult = await api('/api/agent-tools/fetch-url', { method: 'POST', body: { url: url.value, user_approved: state.agentUserApproved } }); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Fetch URL Text'), el('button', { class: 'secondary', onclick: async () => { try { state.agentLastResult = await api('/api/agent-tools/browser/open', { method: 'POST', body: { url: url.value, private: true, headless: false, use_existing_profile: state.agentUseExistingProfile, profile_path: profile.value || null, user_approved: state.agentUserApproved } }); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Open Browser')]), el('div', { class: 'row' }, [el('label', {}, [useProfile, ' use existing Firefox profile']), profile])]),
    card('Latest Agent Tool Result / Job', [lastJob ? el('div', { class: 'row' }, [el('span', { class: `badge ${lastJob.status === 'completed' ? 'ok' : lastJob.status === 'failed' ? 'bad' : ''}` }, `job #${lastJob.id} ${lastJob.status}`), el('button', { class: 'secondary', onclick: () => { state.jobDetailId = lastJob.id; setTab('Jobs'); } }, 'Open Full Job Log'), el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/agent-tools/relay-result', { method: 'POST', body: { job_id: lastJob.id, model_name: model.value || 'dataset-assistant', conversation_id: state.agentConversationId || null, surface: 'Agent Tools', context: context.value || '', ...runtimeBodyFromControls(rt), options: { max_new_tokens: 2048, auto_continue_incomplete: true, ...reasoningOptionsFromControls(null, { min_chat_max_new_tokens: 2048 }) } } }); state.agentConversationId = r.conversation_id || state.agentConversationId; state.agentLastResult = { ...state.agentLastResult, relay: r }; toast('Tool result relayed back to assistant'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Relay Result to Assistant')]) : null, state.agentLastResult ? el('pre', { class: 'log full-log' }, JSON.stringify(state.agentLastResult, null, 2)) : el('p', { class: 'muted' }, 'No agent tool result yet.'), agentDebugLogsPanel(true), jobsTable(8, false)].filter(Boolean)),
    lastApiErrorCard()
  ]);
}


function mcpToolsView() {
  const status = state.mcpToolStatus || {};
  const tools = status.tools || [];
  const summary = el('div', { class: 'chips open' }, [
    el('span', { class: 'chip' }, `${Number(status.installed_count || 0)} installed/detected`),
    el('span', { class: 'chip' }, `${Number(status.enabled_count || 0)} MCP-enabled`),
    el('span', { class: 'chip' }, status.config_exists ? 'client config written' : 'client config not written')
  ]);
  const toolRows = tools.length ? el('div', { class: 'grid' }, tools.map(row => {
    const enabled = el('input', { type: 'checkbox', checked: Boolean(row.enabled_setting ?? row.enabled) });
    const exe = el('input', { value: row.executable_path || '', placeholder: `${row.label || row.key} executable path or command`, style: 'min-width:360px' });
    const endpoint = el('input', { value: row.endpoint || '', placeholder: 'optional endpoint / WebSocket URL', style: 'min-width:320px' });
    return card(`${row.label || row.key} MCP`, [
      el('div', { class: 'row' }, [
        el('span', { class: row.installed ? 'badge ok' : 'badge bad' }, row.installed ? 'installed/detected' : 'not detected'),
        el('span', { class: row.enabled ? 'badge ok' : 'badge' }, row.enabled ? 'enabled' : 'disabled'),
        el('span', { class: 'badge' }, row.kind || 'tool'),
        el('span', { class: 'badge' }, row.mcp_name || row.key)
      ]),
      el('div', { class: 'muted tiny' }, (row.supports || []).join(', ')),
      row.missing_reason ? el('p', { class: 'warning' }, row.missing_reason) : null,
      el('div', { class: 'row' }, [el('label', {}, [enabled, ' enabled when installed']), exe, endpoint]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary small', onclick: async () => { const picked = await pickFilePath(exe, `Select ${row.label || row.key} executable`); if (picked) exe.value = picked; } }, 'Browse Executable'),
        el('button', { class: 'primary small', onclick: async () => { try { state.mcpToolStatus = await api('/api/mcp-tools/settings', { method: 'PUT', body: { tools: { [row.key]: { enabled: enabled.checked, executable_path: exe.value.trim(), endpoint: endpoint.value.trim() } } } }); toast(`${row.label || row.key} MCP settings saved`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Save Tool MCP Settings')
      ]),
      el('details', {}, [el('summary', {}, 'Manual setup steps'), el('ol', {}, (row.manual_steps || []).map(step => el('li', {}, step)))]),
      el('div', { class: 'muted tiny path' }, row.mcp_bridge || '')
    ].filter(Boolean));
  })) : el('p', { class: 'muted' }, 'MCP status has not loaded yet.');
  return el('div', { class: 'grid' }, [
    card('Creative Tool MCP Control Plane', [
      el('p', { class: 'muted' }, 'Blender, Krita, Audacity, OBS Studio, and ComfyUI are enabled by default when the app detects the executable or endpoint. Missing tools remain listed with manual steps so setup is explicit.'),
      summary,
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { state.mcpToolStatus = await api('/api/mcp-tools/status'); toast('MCP tool discovery refreshed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Refresh Discovery'),
        el('button', { class: 'primary', onclick: async () => { try { state.mcpToolStatus = await api('/api/mcp-tools/write-client-config', { method: 'POST', body: {} }); toast('MCP client config written'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Write MCP Client Config'),
        el('span', { class: 'muted tiny path' }, status.config_path || 'runtime/mcp_servers/dct_mcp_client_config.json')
      ]),
      el('p', { class: 'muted tiny' }, status.manual_config_note || 'Run install_mcp_tools.bat or install_mcp_tools.sh, then copy the generated config into the MCP client you use.')
    ]),
    toolRows,
    card('Generated MCP Client Config Preview', [
      el('button', { class: 'secondary', onclick: async () => { try { const cfg = await api('/api/mcp-tools/client-config'); await copyText(JSON.stringify(cfg, null, 2), 'Copied MCP client config'); } catch (err) { toast(err.message, false); } } }, 'Copy Config JSON'),
      el('pre', { class: 'log full-log' }, JSON.stringify(status.client_config || { note: 'Click Write MCP Client Config to generate the current enabled-tool config.' }, null, 2))
    ])
  ]);
}

function modelTagSelectionCard(options = {}) {
  const opts = typeof options === 'function' ? { getMediaIds: options } : options;
  const title = opts.title || 'LLM/VLM/Assistant Tag Selection';
  const description = opts.description || 'Use criteria/category metadata, a real tagger/rating/classifier, or a loaded VLM/LLM to select/apply tags. VLMs receive the image context and return tag candidates.';
  const getMediaIds = opts.getMediaIds || (() => [...state.selected]);
  const getCandidateTags = opts.getCandidateTags || (() => []);
  const getCandidateTagsByMedia = opts.getCandidateTagsByMedia || (() => ({}));
  const targetLabel = opts.targetLabel || (() => `${getMediaIds().length} selected item(s)`);
  const tagSelectionModels = sortedTagSelectionModels(state.models.filter(m => { const caps = m.capabilities || []; return caps.includes('chat') || caps.includes('vlm') || caps.includes('tag') || caps.includes('auto_tag') || caps.includes('classify') || caps.includes('rating') || caps.includes('caption'); }));
  const model = el('select', { class: 'model-category-select', title: 'Models are sorted: local VLMs, local LLMs, tag/caption/classifier models, then API/cloud models. Hover an option to see its category.' }, tagSelectionModels.map(modelOptionNode));
  const preferredSelection = tagSelectionModels.find(m => m.name === state.assistantConfig?.orchestrator_model_name) || tagSelectionModels.find(m => m.kind === 'vlm' && !modelIsApi(m)) || tagSelectionModels.find(m => m.name === 'gemma-4-e4b-it') || tagSelectionModels.find(m => m.name === 'redrocket-jtp-3') || tagSelectionModels.find(m => m.name === 'dataset-assistant');
  rememberSelect('tagSelectionModelSelection', model, preferredSelection?.name || '', false);
  model.addEventListener('change', () => {
    state.tagSelectionModelSelection = model.value || '';
    primeModelLifecycleForSelection(selectedModel());
    updateLiveStatusDom();
    render(true, true);
    refreshModelStatuses(false).then(updateLiveStatusDom).catch(() => {});
  });
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value };
  const criteria = el('textarea', { placeholder: 'Examples: select unknown tags; select character tags; suggest missing visual tags; prune tags that are not visible; or use highlighted manual chips only', 'data-form-key': `${title}-criteria` }, opts.defaultCriteria || 'select unknown tags');
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: String(opts.threshold || state.settings.classifier_threshold || 0.35), title: 'Threshold used when the selected model is a tagger/classifier/rating model.' });
  const topK = el('input', { type: 'number', min: '1', max: '1000', value: String(opts.topK || 80), title: 'Maximum labels requested from classifier/tagger/VLM models.' });
  const operation = el('select', {}, ['preview', 'remove', 'keep_only', 'set', 'add'].map(x => el('option', { value: x }, x)));
  const cats = el('select', { multiple: 'multiple', size: opts.categorySize || '7' }, categories().map(c => el('option', { value: c.key }, c.label || c.key)));
  const manualOnly = el('input', { type: 'checkbox', checked: Boolean(opts.manualOnlyDefault), title: 'Use the manually highlighted chips from the tag strip as the candidate set instead of also selecting by text/category criteria.' });
  const allCategories = el('input', { type: 'checkbox', checked: opts.allCategoriesDefault !== false, title: 'Bypass the category multi-select and let the model consider every tag category in the active profile.' });
  const chatApplyTags = el('input', { type: 'checkbox', title: 'Apply tags from a tags:/JSON response to the target media.' });
  const chatApplyCaption = el('input', { type: 'checkbox', title: 'Apply caption from a caption:/JSON response to the target media.' });
  const chatAgentTools = el('input', { type: 'checkbox', checked: Boolean(state.tagSelectionAgentToolsChatEnabled || state.settings?.agent_tools_enable_approved_coa_execution), title: 'Tell the selected assistant model that approved local tools are available and parse its COA/tool calls.' });
  chatAgentTools.addEventListener('change', e => { state.tagSelectionAgentToolsChatEnabled = e.target.checked; state.agentCoaExecutionEnabled = e.target.checked || state.agentCoaExecutionEnabled; });
  const refreshCategoryMode = () => { cats.disabled = Boolean(allCategories.checked || manualOnly.checked); };
  allCategories.addEventListener('change', refreshCategoryMode);
  manualOnly.addEventListener('change', refreshCategoryMode);
  refreshCategoryMode();
  const rt = modelRuntimeControls();
  const reasoning = assistantReasoningControls('assistant');
  const manualCandidateSummary = () => `${[...new Set((getCandidateTags() || []).map(normalizeTag).filter(Boolean))].length} highlighted/manual candidate tag(s)`;
  const runConversationAboutTarget = async (promptText = null, chatOptions = {}) => {
    const mediaIds = [...new Set((getMediaIds() || []).map(Number).filter(Boolean))];
    if (!mediaIds.length) throw new Error('No media selected for assistant conversation.');
    const selectedName = model.value || 'dataset-assistant';
    const finalPrompt = String(promptText || '').trim() || criteria.value || 'Talk with me about the selected image/data and its tags.';
    setOptimisticModelStage(selectedName, 'load', modelLoaded(selectedName) ? 'completed' : 'running', modelLoaded(selectedName) ? 1 : 0.03, modelLoaded(selectedName) ? 'Model already loaded for chat' : 'Auto-loading selected assistant/chat model');
    setOptimisticModelStage(selectedName, 'inference', 'running', 0.01, 'Assistant conversation request sent');
    updateLiveStatusDom();
    let statusPoll = setInterval(async () => { try { await refreshModelStatuses(false); updateLiveStatusDom(); } catch (_) {} }, 850);
    try {
      const body = {
        model_name: selectedName,
        prompt: finalPrompt,
        dataset_id: Number(state.filters.dataset_id || 0) || null,
        media_ids: mediaIds,
        conversation_id: state.tagSelectionChatConversationId || null,
        include_metadata_context: true,
        use_selected_media: true,
        apply_suggested_tags: chatApplyTags.checked,
        apply_suggested_caption: chatApplyCaption.checked,
        ...runtimeBodyFromControls(rt),
        options: {
          max_new_tokens: Math.max(Number(state.settings.model_max_new_tokens || 0), 1024),
          max_continuation_rounds: chatOptions.continueLastOutput ? 2 : 1,
          auto_continue_incomplete: true,
          continue_last_output: Boolean(chatOptions.continueLastOutput),
          chat_assistant: true,
          agent_tools_chat: Boolean(chatAgentTools.checked),
          agent_tools_execute_coa_enabled: Boolean(chatAgentTools.checked || state.agentCoaExecutionEnabled || state.settings?.agent_tools_enable_approved_coa_execution),
          tag_profile: state.tagProfile,
          ...reasoningOptionsFromControls(reasoning)
        }
      };
      const r = await api('/api/models/chat', { method: 'POST', body });
      state.tagSelectionChatConversationId = r.conversation_id || state.tagSelectionChatConversationId;
      state.tagSelectionChatMessages = r.history || state.tagSelectionChatMessages || [];
      state.tagSelectionChatState = { ...(state.tagSelectionChatState || {}), memory_summary: r.memory_summary || state.tagSelectionChatState?.memory_summary || '', last_context_budget: r.context_budget || state.tagSelectionChatState?.last_context_budget || null, context_reset_message_id: r.context_reset_message_id || state.tagSelectionChatState?.context_reset_message_id || 0 };
      state.lastTagSelectionChat = r;
      state.lastTagSelectionChatError = null;
      if (chatAgentTools.checked && r.assistant_message_id && r.conversation_id) {
        try { await fetchCoaOptionsForMessage(r.conversation_id, r.assistant_message_id); } catch (_) {}
      }
      if (chatAgentTools.checked && r.response) {
        try {
          const parsed = await api('/api/agent-tools/parse-tool-calls', { method: 'POST', body: { text: r.response } });
          const draftKey = `agent-tag-selection-${title}`;
          if ((parsed.tool_calls || []).length) {
            state.agentSurfacePlans[draftKey] = {
              ...(state.agentSurfacePlans[draftKey] || {}),
              plan: { summary: 'Executable COA/tool calls parsed from assistant chat response', steps: parsed.tool_calls },
              tool_calls: parsed.tool_calls,
              response: r.response,
              conversation_id: r.conversation_id
            };
            toast(`Parsed ${parsed.tool_calls.length} executable COA/tool call(s) from assistant response`);
          }
        } catch (_) {}
      }
      if (r.applied && ((r.applied.tags || 0) || (r.applied.captions || 0))) await refreshMediaRows(mediaIds);
      if (opts.afterChat) await opts.afterChat(r, mediaIds);
      toast(`Assistant replied${r.conversation_id ? ' in conversation #' + r.conversation_id : ''}`);
      await refreshModelStatuses(false).catch(() => {});
    } catch (err) {
      state.lastTagSelectionChatError = state.lastApiError || { time: new Date().toISOString(), model_name: selectedName, error: String(err?.message || err), path: err?.path || '/api/models/chat' };
      toast(err.message, false);
    } finally {
      clearInterval(statusPoll);
      await refreshModelStatuses(false).catch(() => {});
      updateLiveStatusDom();
    }
  };
  const sendQueuedTagSelectionChat = async (text, meta = {}) => {
    resetStaleChatQueueLock('tagSelection');
    const item = { text: String(text || ''), meta: { ...(meta || {}) }, queued_at: new Date().toISOString() };
    if (state.tagSelectionChatSending) {
      state.tagSelectionChatQueue = [...(state.tagSelectionChatQueue || []), item];
      toast(`Queued chat message (${state.tagSelectionChatQueue.length} waiting).`);
      render(true, true);
      return;
    }
    state.tagSelectionChatSending = true;
    state.tagSelectionChatCurrent = item;
    render(true, true);
    try {
      let current = item;
      while (current) {
        state.tagSelectionChatCurrent = current;
        await runConversationAboutTarget(current.text, current.meta || {});
        current = (state.tagSelectionChatQueue || []).shift() || null;
        state.tagSelectionChatQueue = state.tagSelectionChatQueue || [];
        if (current) render(true, true);
      }
    } finally {
      state.tagSelectionChatSending = false;
      state.tagSelectionChatCurrent = null;
      render(true, true);
    }
  };
  return card(title, [
    el('p', { class: 'muted' }, description),
    el('div', { class: 'muted tiny' }, `Target: ${typeof targetLabel === 'function' ? targetLabel() : targetLabel} · ${manualCandidateSummary()}`),
    el('div', { class: 'model-option-legend' }, ['vlm','llm','tagger','captioner','classifier','rating','3d_generation','mcp_tool','api'].map(key => { const sample = { kind: key, capabilities: key === 'vlm' ? ['vlm'] : key === 'llm' ? ['llm'] : key === 'api' ? ['chat'] : [key], provider: key === 'api' ? 'openrouter' : 'local', cloud: key === 'api' }; const info = modelCategoryDisplay(sample); return el('span', { class: 'legend-chip model-category-chip', style: `border-color:${info.color}; color:${info.color};` }, info.label); })),
    inlineOrchestratorControls(model, 'tag-selection'),
    el('div', { class: 'row' }, [model, operation, cats, el('label', {}, ['threshold', threshold]), el('label', {}, ['top-k', topK]), el('label', {}, [allCategories, ' all categories']), el('label', {}, [manualOnly, ' highlighted/manual only'])]),
    modelLifecycleStrip(selectedModel(), true),
    inlineSelectedModelRuntimeControls(model, rt, 'tag-selection'),
    assistantReasoningPanel(reasoning, 'Think longer / visible plan controls'),
    agentToolsInlinePanel(`tag-selection-${title}`, title, getMediaIds, model, rt),
    criteria,
    el('div', { class: 'assistant-conversation-panel' }, [
      el('div', { class: 'muted tiny' }, `Conversation mode uses the same selected image/data, tag list, and metadata context, but it does not force a tag-selection operation. Conversation id: ${state.tagSelectionChatConversationId || 'new'}`),
      el('div', { class: 'row tight' }, [
        el('label', {}, [chatApplyTags, ' apply tags from response']),
        el('label', {}, [chatApplyCaption, ' apply caption from response']),
        el('label', { title: 'Adds the executable tool-call contract to chat prompts and parses COA actions from responses.' }, [chatAgentTools, ' enable approved local tools/COA when needed']),
        el('button', { class: 'secondary small', onclick: () => { state.tagSelectionChatConversationId = null; state.tagSelectionChatMessages = []; state.tagSelectionChatState = {}; state.lastTagSelectionChat = null; state.lastTagSelectionChatError = null; render(true, true); } }, 'New Conversation'),
        state.tagSelectionChatConversationId ? el('button', { class: 'secondary small', onclick: async () => { try { await loadScopedChatConversation(state.tagSelectionChatConversationId, 'tagSelection'); toast('Tag Editor conversation refreshed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Refresh History') : null,
        el('button', { class: 'secondary small', onclick: async () => { try { await runConversationAboutTarget(criteria.value || 'Talk with me about the selected image/data and its tags.'); render(true, true); } catch (err) { toast(err.message, false); render(true, true); } } }, 'Chat About Current Target')
      ].filter(Boolean)),
      conversationHistoryPanel('tagSelection', state.tagSelectionChatConversationId, state.tagSelectionChatMessages, {
        title: 'Tag Editor Assistant Chat',
        surface: 'Tag Editor assistant',
        modelName: () => model.value || 'dataset-assistant',
        runtimeControls: rt,
        context: () => agentSurfaceContext('Tag Editor assistant', getMediaIds),
        reload: async id => loadScopedChatConversation(id, 'tagSelection'),
        saveState: () => ({
          title: `Tag Editor chat · ${typeof targetLabel === 'function' ? targetLabel() : targetLabel}`,
          scope: 'tag-editor',
          tag_profile: state.tagProfile,
          media_ids: [...new Set((getMediaIds() || []).map(Number).filter(Boolean))],
          candidate_tags: [...new Set((getCandidateTags() || []).map(normalizeTag).filter(Boolean))],
          active_media_id: state.activeMedia?.id || null,
          active_media_path: state.activeMedia?.path || null,
          active_tags: state.activeMedia ? ensureDraft(state.activeMedia) : [],
          active_caption: state.activeMedia?.caption || '',
          criteria: criteria.value || '',
          selected_model: model.value || ''
        }),
        composer: {
          draftKey: 'tagSelectionChatDraft',
          placeholder: 'Chat about this image/data, current tags, captions, metadata, or ask for tag/caption cleanup. Example: explain which tags are likely wrong and why.',
          sendLabel: 'Send Chat Message',
          finishLabel: 'Finish Last Output',
          hint: 'This bottom composer is for normal conversation. The model receives condensed memory + recent history + current image/tags/captions.',
          disabled: false,
          onSend: sendQueuedTagSelectionChat
        }
      }),
      state.lastTagSelectionChat ? el('div', { class: 'chat-mini-log' }, [
        el('strong', {}, `Assistant conversation #${state.lastTagSelectionChat.conversation_id || ''}`),
        visiblePlanPanel(state.lastTagSelectionChat),
        el('pre', { class: 'log full-log' }, state.lastTagSelectionChat.response || JSON.stringify(state.lastTagSelectionChat, null, 2)),
        (state.lastTagSelectionChat.suggested_tags || []).length ? el('div', { class: 'muted tiny' }, `Suggested tags: ${(state.lastTagSelectionChat.suggested_tags || []).join(', ')}`) : null,
        state.lastTagSelectionChat.suggested_caption ? el('div', { class: 'muted tiny' }, `Suggested caption: ${state.lastTagSelectionChat.suggested_caption}`) : null
      ].filter(Boolean)) : null,
      state.lastTagSelectionChatError ? el('div', { class: 'bad-panel' }, [
        el('strong', {}, 'Last assistant conversation error'),
        el('button', { class: 'secondary small', onclick: async () => copyText(JSON.stringify(state.lastTagSelectionChatError, null, 2), 'Copied assistant chat error') }, 'Copy Chat Error'),
        el('pre', { class: 'log full-log' }, JSON.stringify(state.lastTagSelectionChatError, null, 2))
      ]) : null
    ].filter(Boolean)),
    el('button', { class: 'primary', disabled: modelBusy(selectedModel(), ['download', 'load']), onclick: async () => {
      try {
        const mediaIds = [...new Set((getMediaIds() || []).map(Number).filter(Boolean))];
        if (modelBusy(selectedModel(), ['download', 'load'])) throw new Error('Selected model is downloading or loading. Wait for the status circle to finish before tag selection.');
        if (!mediaIds.length) throw new Error('No media selected for assistant tag selection.');
        setOptimisticModelStage(model.value || 'dataset-assistant', 'load', modelLoaded(model.value) ? 'completed' : 'running', modelLoaded(model.value) ? 1 : 0.03, modelLoaded(model.value) ? 'Model already loaded for assistant tag selection' : 'Auto-loading selected assistant/tag model');
        setOptimisticModelStage(model.value || 'dataset-assistant', 'inference', 'running', 0.01, 'Assistant tag-selection request sent');
        updateLiveStatusDom();
        const manualTags = [...new Set((getCandidateTags() || []).map(normalizeTag).filter(Boolean))];
        const manualTagsByMedia = Object.fromEntries(Object.entries(getCandidateTagsByMedia() || {}).map(([key, value]) => [String(key), [...new Set((value || []).map(normalizeTag).filter(Boolean))]]));
        const body = {
          media_ids: mediaIds,
          criteria: manualOnly.checked ? '' : criteria.value,
          model_name: model.value || 'dataset-assistant',
          profile_key: state.tagProfile,
          categories: (manualOnly.checked || allCategories.checked) ? [] : [...cats.selectedOptions].map(o => o.value),
          candidate_tags: manualTags,
          candidate_tags_by_media: manualTagsByMedia,
          operation: operation.value,
          ...runtimeBodyFromControls(rt),
          options: { threshold: Number(threshold.value || 0.35), top_k: Number(topK.value || 80), manual_only: manualOnly.checked, all_categories: allCategories.checked, validate_existing_tags: Boolean(opts.validateExistingTagsDefault), max_new_tokens: Math.max(Number(state.settings.model_max_new_tokens || 0), 1024), min_tag_task_max_new_tokens: 1024, max_tag_continuation_rounds: 3, tag_profile: state.tagProfile, ...reasoningOptionsFromControls(reasoning) }
        };
        const selectedName = body.model_name || 'dataset-assistant';
        setOptimisticModelStage(selectedName, 'load', modelLoaded(selectedName) ? 'completed' : 'running', modelLoaded(selectedName) ? 1 : 0.03, modelLoaded(selectedName) ? 'Model already loaded for tag selection' : 'Model may auto-load for tag selection');
        setOptimisticModelStage(selectedName, 'inference', 'running', 0.01, 'Tag-selection request sent');
        updateLiveStatusDom();
        render(true, true);
        let statusPoll = setInterval(async () => { try { await refreshModelStatuses(false); updateLiveStatusDom(); } catch (_) {} }, 850);
        let r;
        try {
          r = await api('/api/models/select-tags', { method: 'POST', body });
        } finally {
          clearInterval(statusPoll);
          await refreshModelStatuses(false).catch(() => {});
          updateLiveStatusDom();
        }
        state.lastTagSelection = r;
        state.lastTagSelectionError = null;
        toast(operation.value === 'preview' ? `Selected ${r.selected_tags.length} distinct tags` : `Applied to ${r.applied.changed} files`);
        if (operation.value !== 'preview') await refreshMediaRows(mediaIds);
        if (opts.afterRun) await opts.afterRun(r, operation.value, mediaIds);
        await refreshModelStatuses(false).catch(() => {});
        render(true, true);
      } catch (err) {
        state.lastTagSelectionError = state.lastApiError || {
          time: new Date().toISOString(),
          model_name: model.value || 'dataset-assistant',
          operation: operation.value,
          error: String(err?.message || err),
          status: err?.status || null,
          path: err?.path || '/api/models/select-tags',
          api: state.lastApiError || null,
          hint: 'Use Copy Error / Download Error below and send it with the selected model name and current image id.'
        };
        toast(err.message, false);
        render(true, true);
      }
    } }, 'Run Tag Selection'),
    state.lastTagSelectionError ? el('div', { class: 'bad-panel' }, [
      el('strong', {}, 'Last tag-selection error'),
      el('div', { class: 'row tight' }, [
        el('button', { class: 'secondary small', onclick: async () => copyText(JSON.stringify(state.lastTagSelectionError, null, 2), 'Copied tag-selection error') }, 'Copy Error'),
        el('button', { class: 'secondary small', onclick: () => downloadTextFile('dct-tag-selection-error.json', JSON.stringify(state.lastTagSelectionError, null, 2)) }, 'Download Error')
      ]),
      el('pre', { class: 'log full-log' }, JSON.stringify(state.lastTagSelectionError, null, 2))
    ]) : null,
    state.lastTagSelection ? el('div', { class: 'result-panel' }, [
      state.lastTagSelection.visible_plans_by_media && Object.keys(state.lastTagSelection.visible_plans_by_media).length ? el('details', { class: 'visible-plan-panel', open: true }, [el('summary', {}, 'Visible tag-task plans by media'), el('pre', { class: 'log compact' }, JSON.stringify(state.lastTagSelection.visible_plans_by_media, null, 2))]) : null,
      state.lastTagSelection.completion?.enforced_for_chat_models ? el('div', { class: state.lastTagSelection.completion?.any_incomplete ? 'warn-inline' : 'good-inline' }, state.lastTagSelection.completion?.any_incomplete
        ? `Completion warning: model output may still be incomplete after ${state.lastTagSelection.completion?.continuation_rounds_total || 0} continuation attempt(s). Preview results are shown, but non-preview changes are blocked when incomplete.`
        : `Completion checked: ${state.lastTagSelection.completion?.continuation_rounds_total || 0} continuation/verification round(s) were used before returning results.`) : null,
      el('pre', { class: 'log' }, JSON.stringify(state.lastTagSelection, null, 2))
    ].filter(Boolean)) : el('p', { class: 'muted' }, 'No selection result yet.')
  ]);
}



function curationModelFilter(m) {
  const caps = new Set(m.capabilities || []);
  return caps.has('tag') || caps.has('auto_tag') || caps.has('rating') || caps.has('classify') || caps.has('caption') || caps.has('image_classification');
}
function defaultTaskForModelName(name) {
  if (name === 'redrocket-jtp-3') return 'tag';
  const m = state.models.find(x => x.name === name) || {};
  const caps = new Set(m.capabilities || []);
  if ((m.kind || '') === 'rating' || caps.has('rating')) return 'rating';
  if ((m.kind || '') === 'captioner' || caps.has('caption')) return 'caption';
  if ((m.kind || '') === 'classifier' || caps.has('classify')) return 'classify';
  return 'tag';
}
function modelPredictionRunCard(options = {}) {
  const opts = typeof options === 'function' ? { getMediaIds: options } : options;
  const getMediaIds = opts.getMediaIds || (() => [...state.selected]);
  const title = opts.title || 'Run Tagging / Rating / Caption Model';
  const description = opts.description || 'Run downloaded/local/API-supported curation models on the target media. RedRocket JTP-3 and e6 visual ratings appear here when present in the model catalog.';
  const model = el('select', {}, modelOptions(curationModelFilter));
  rememberSelect('predictionModelSelection', model, '', false);
  const task = el('select', {}, ['tag', 'rating', 'classify', 'caption'].map(x => el('option', { value: x }, x)));
  model.onchange = () => { state.predictionModelSelection = model.value || ''; task.value = defaultTaskForModelName(model.value); };
  task.value = defaultTaskForModelName(model.value);
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: state.settings.classifier_threshold || 0.35 });
  const topK = el('input', { type: 'number', min: '1', max: '1000', step: '1', value: 250, title: 'Max labels/tags returned where the adapter supports it.' });
  const applyTags = el('input', { type: 'checkbox', checked: opts.applyTagsDefault !== false });
  const applyCaption = el('input', { type: 'checkbox', checked: false });
  const rt = modelRuntimeControls();
  return card(title, [
    el('p', { class: 'muted' }, description),
    el('div', { class: 'muted tiny' }, `Target: ${opts.targetLabel ? opts.targetLabel() : `${getMediaIds().length} selected item(s)`}`),
    el('div', { class: 'row' }, [model, task, el('label', {}, ['threshold', threshold]), el('label', {}, ['top_k / max tags', topK])]),
    el('div', { class: 'row' }, [rt.device, rt.gpuIds, rt.shard, rt.dtype, rt.quant]),
    rt.maxMemory,
    el('div', { class: 'row' }, [el('label', {}, [applyTags, ' Apply predicted tags/classes/ratings']), el('label', {}, [applyCaption, ' Apply predicted caption'])]),
    el('button', { class: 'primary', onclick: async () => {
      try {
        const mediaIds = [...new Set((getMediaIds() || []).map(Number).filter(Boolean))];
        if (!mediaIds.length) throw new Error('No media selected for model run.');
        if (!model.value) throw new Error('Select a curation model first.');
        const body = {
          model_name: model.value,
          task: model.value === 'redrocket-jtp-3' ? 'tag' : task.value,
          media_ids: mediaIds,
          threshold: Number(threshold.value || 0.35),
          apply_tags: applyTags.checked,
          apply_caption: applyCaption.checked,
          ...runtimeBodyFromControls(rt),
          parallel_workers: Number(rt.parallel.value || 1),
          options: { top_k: Number(topK.value || 250), max_tags: Number(topK.value || 250), tag_profile: state.tagProfile }
        };
        const r = await api('/api/models/run', { method: 'POST', body });
        toast(`Queued ${model.value} as job ${r.job_id}. Staying here; open Jobs only if you need full logs.`);
        await refreshAll();
        await refreshCompletedModelJobById(r.job_id);
        if (opts.afterRun) await opts.afterRun(r, mediaIds);
        render();
      } catch (err) { toast(err.message, false); }
    } }, 'Queue Model Run')
  ]);
}

function markEditorAssistantSelection(result, item) {
  state.editorAssistantSelection = result || {};
  const byMedia = result?.selected_tags_by_media || {};
  const selected = byMedia[item.id] || byMedia[String(item.id)] || result?.selected_tags || [];
  setEditorSelectedTags(item, selected);
  refreshEditorSelectedTagDom(item, selected);
  toast(`Assistant highlighted ${selected.length} tag(s) for this image.`);
}
function ensureEditorSelectionPayload(item) {
  if (!state.editorAssistantSelection || !state.editorAssistantSelection.selected_tags_by_media) {
    state.editorAssistantSelection = {
      model_name: 'manual-highlight',
      criteria: 'manual tag highlight selection',
      selected_tags_by_media: {},
      selected_tags: [],
      applied: { operation: 'manual', changed: 0 }
    };
  }
  const key = String(item?.id || '');
  if (key && !Array.isArray(state.editorAssistantSelection.selected_tags_by_media[key])) {
    state.editorAssistantSelection.selected_tags_by_media[key] = [];
  }
  return state.editorAssistantSelection;
}
function editorSelectedTags(item) {
  if (!item) return [];
  const payload = state.editorAssistantSelection || {};
  const byMedia = payload.selected_tags_by_media || {};
  return [...new Set([...(byMedia[item.id] || []), ...(byMedia[String(item.id)] || [])].map(normalizeTag).filter(Boolean))];
}
function setEditorSelectedTags(item, tags = []) {
  if (!item) return [];
  const payload = ensureEditorSelectionPayload(item);
  const clean = [...new Set((tags || []).map(normalizeTag).filter(Boolean))];
  payload.selected_tags_by_media[String(item.id)] = clean;
  payload.selected_tags_by_media[item.id] = clean;
  const union = [];
  const seen = new Set();
  Object.values(payload.selected_tags_by_media || {}).forEach(list => {
    (list || []).forEach(tag => { const cleanTag = normalizeTag(tag); if (cleanTag && !seen.has(cleanTag)) { seen.add(cleanTag); union.push(cleanTag); } });
  });
  payload.selected_tags = union;
  state.editorAssistantSelection = payload;
  refreshEditorSelectedTagDom(item, clean);
  return clean;
}
function refreshEditorSelectedTagDom(item, selectedTags = null) {
  if (!item || state.tab !== 'Tag Editor') return;
  const clean = new Set((selectedTags || editorSelectedTags(item)).map(normalizeTag).filter(Boolean));
  const root = document.getElementById('app');
  if (!root) return;
  root.querySelectorAll(`[data-editor-media-id="${item.id}"][data-editor-tag]`).forEach(chip => {
    const tag = normalizeTag(chip.dataset.editorTag || '');
    const active = clean.has(tag);
    chip.classList.toggle('selected-tag', active);
    const btn = chip.querySelector('.tag-select-toggle');
    if (btn) { btn.classList.toggle('active', active); btn.textContent = active ? '✓' : '○'; btn.title = active ? 'Deselect/highlight off' : 'Select/highlight this tag'; }
  });
  root.querySelectorAll(`[data-role="editor-selected-tag-count"][data-editor-media-id="${item.id}"]`).forEach(node => { node.textContent = `${clean.size} highlighted`; });
}
function toggleEditorSelectedTag(item, tag) {
  const selected = new Set(editorSelectedTags(item));
  const clean = normalizeTag(tag);
  if (!clean) return;
  if (selected.has(clean)) selected.delete(clean); else selected.add(clean);
  setEditorSelectedTags(item, [...selected]);
}
function categoryTagsForItem(item, tags, categoryKey) {
  const wanted = normalizeCategoryKey(categoryKey || '');
  return (tags || []).filter(tag => normalizeCategoryKey(categoryOf(tag, item)) === wanted);
}
function editorManualCandidateTags(item) {
  return editorSelectedTags(item);
}

function markCompareAssistantSelection(result, left, right) {
  if (!result?.selected_tags_by_media) return;
  state.compareSelected.left.clear();
  state.compareSelected.right.clear();
  for (const tag of (result.selected_tags_by_media[left.id] || result.selected_tags_by_media[String(left.id)] || [])) state.compareSelected.left.add(tag);
  for (const tag of (result.selected_tags_by_media[right.id] || result.selected_tags_by_media[String(right.id)] || [])) state.compareSelected.right.add(tag);
}

function selectedCompareItems() {
  return selectedMediaItemsCached();
}
function normalizeCompareFocus(items) {
  if (!items.length) return;
  state.compareFocus.left = Math.max(0, Math.min(state.compareFocus.left || 0, items.length - 1));
  state.compareFocus.right = Math.max(0, Math.min(state.compareFocus.right ?? 1, items.length - 1));
  if (items.length > 1 && state.compareFocus.left === state.compareFocus.right) {
    state.compareFocus.right = state.compareFocus.left === 0 ? 1 : 0;
  }
}
function cycleCompare(side, delta) {
  const items = selectedCompareItems();
  if (items.length < 2) return;
  normalizeCompareFocus(items);
  const other = side === 'left' ? 'right' : 'left';
  let idx = state.compareFocus[side];
  for (let step = 0; step < items.length; step++) {
    idx = (idx + delta + items.length) % items.length;
    if (idx !== state.compareFocus[other]) break;
  }
  state.compareFocus[side] = idx;
  state.compareSelected[side].clear();
  render();
}
function setCompareIndex(side, value) {
  const items = selectedCompareItems();
  if (items.length < 2) return;
  const idx = Number(value);
  if (!Number.isFinite(idx)) return;
  const other = side === 'left' ? 'right' : 'left';
  state.compareFocus[side] = Math.max(0, Math.min(idx, items.length - 1));
  if (state.compareFocus[side] === state.compareFocus[other]) {
    state.compareFocus[other] = state.compareFocus[side] === 0 ? 1 : 0;
  }
  state.compareSelected[side].clear();
  render();
}
function compareIndexSelect(side, items) {
  const select = el('select', { onchange: e => setCompareIndex(side, e.target.value) }, items.map((item, idx) => el('option', { value: idx }, `${idx + 1}: ${item.relative_path || item.path}`)));
  select.value = state.compareFocus[side];
  return select;
}
function compareView() {
  const items = selectedCompareItems();
  normalizeCompareFocus(items);
  if (items.length < 2) return card('Compare', [el('p', { class: 'muted' }, 'Select two or more images in the Gallery using Ctrl/Cmd/Shift click.'), el('button', { class: 'secondary', onclick: () => setTab('Gallery') }, 'Go to Gallery')]);
  const left = items[state.compareFocus.left];
  const right = items[state.compareFocus.right];
  requestTagMetadata([...(left.tags || []), ...(right.tags || [])]);
  requestTagScores(left.id, left.tags || []);
  requestTagScores(right.id, right.tags || []);
  return el('div', { class: 'grid' }, [
    card('Compare Queue', [
      el('p', { class: 'muted' }, 'When more than two images are selected, the comparer opens the first two in gallery order. Use the left/right controls to cycle either side through the selected queue one image at a time.'),
      el('div', { class: 'row' }, [
        el('span', { class: 'badge' }, `${items.length} selected for compare`),
        el('button', { class: 'secondary', onclick: () => cycleCompare('left', -1) }, '◀ Left'),
        compareIndexSelect('left', items),
        el('button', { class: 'secondary', onclick: () => cycleCompare('left', 1) }, 'Left ▶'),
        el('button', { class: 'secondary', onclick: () => cycleCompare('right', -1) }, '◀ Right'),
        compareIndexSelect('right', items),
        el('button', { class: 'secondary', onclick: () => cycleCompare('right', 1) }, 'Right ▶')
      ])
    ]),
    el('div', { class: 'grid cols-2' }, [compareSide(left, 'left', right), compareSide(right, 'right', left)]),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => moveSelectedTags(left, right, 'left', false) }, 'Add Selected Left → Right'),
      el('button', { class: 'secondary', onclick: async () => moveSelectedTags(right, left, 'right', false) }, 'Add Selected Right → Left'),
      el('button', { class: 'secondary', onclick: async () => moveSelectedTags(left, right, 'left', true) }, 'Move Selected Left → Right'),
      el('button', { class: 'secondary', onclick: async () => moveSelectedTags(right, left, 'right', true) }, 'Move Selected Right → Left'),
      el('button', { class: 'secondary', onclick: async () => copyTags(left.id, right.id) }, 'Copy All Left → Right'),
      el('button', { class: 'secondary', onclick: async () => copyTags(right.id, left.id) }, 'Copy All Right → Left')
    ]),
    modelPredictionRunCard({
      title: 'Run Tagging / Rating Model for Current Compare Pair',
      description: 'Run a curation model on the currently displayed pair to save predictions or apply predicted tags/ratings for review.',
      getMediaIds: () => [left.id, right.id],
      targetLabel: () => `Left #${left.id} and Right #${right.id}`
    }),
    modelTagSelectionCard({
      title: 'LLM/VLM/Assistant Tag Selection for Current Compare Pair',
      description: 'Run tag-selection criteria against the currently displayed left/right images. Preview selects matching chips on each side; apply operations update only this pair.',
      getMediaIds: () => [left.id, right.id],
      targetLabel: () => `Left #${left.id} and Right #${right.id}`,
      categorySize: '5',
      afterRun: async (result, operation) => {
        if (operation === 'preview') markCompareAssistantSelection(result, left, right);
        else { await loadMedia(); state.compareSelected.left.clear(); state.compareSelected.right.clear(); }
      }
    }),
    imageTagRatingQuickRunCard({ title: 'Quick Tag / Rating Model for Compare Pair', getMediaIds: () => [left.id, right.id] }),
    metadataQuickCard({ title: 'Metadata Extraction / Compose for Current Compare Pair', getMediaIds: () => [left.id, right.id] })
  ]);
}
function compareSide(item, side, otherItem) {
  const selected = state.compareSelected[side];
  const otherTags = new Set(otherItem?.tags || []);
  return card(`${side === 'left' ? 'Left' : 'Right'} #${item.id}`, [
    mediaPreviewElement(item, 'preview'),
    el('div', { class: 'muted tiny path' }, item.relative_path || item.path),
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary small', onclick: () => { for (const t of item.tags) selected.add(t); render(); } }, 'Select All Tags'),
      el('button', { class: 'secondary small', onclick: () => { for (const t of item.tags) if (!otherTags.has(t)) selected.add(t); render(); } }, 'Select Missing on Other'),
      el('button', { class: 'secondary small', onclick: () => { selected.clear(); render(); } }, 'Clear Tag Selection')
    ]),
    el('div', { class: 'chips open selectable-tags' }, (item.tags || []).map(t => predictionChip(t, categoryOf(t, item), item.id, { onclick: () => { selected.has(t) ? selected.delete(t) : selected.add(t); render(); }, class: `chip ${selected.has(t) ? 'selected-tag' : ''}` })))
  ]);
}

async function moveSelectedTags(source, target, side, removeFromSource = false) {
  try {
    const tags = [...state.compareSelected[side]];
    if (!tags.length) throw new Error('Select one or more tags first.');
    const merged = [...(target.tags || [])];
    for (const tag of tags) if (!merged.includes(tag)) merged.push(tag);
    await api(`/api/media/${target.id}/tags`, { method: 'PUT', body: { tag_string: merged.join(', '), tag_profile: state.tagProfile, order_strategy: 'retain' } });
    if (removeFromSource) {
      const kept = (source.tags || []).filter(t => !tags.includes(t));
      await api(`/api/media/${source.id}/tags`, { method: 'PUT', body: { tag_string: kept.join(', '), tag_profile: state.tagProfile, order_strategy: 'retain' } });
    }
    state.compareSelected.left.clear(); state.compareSelected.right.clear(); await loadMedia(); toast('Tags transferred'); render();
  } catch (err) { toast(err.message, false); }
}
async function copyTags(sourceId, targetId) {
  try { const source = await api(`/api/media/${sourceId}`); await api(`/api/media/${targetId}/tags`, { method: 'PUT', body: { tag_string: (source.tags || []).join(', '), tag_profile: state.tagProfile, order_strategy: 'retain' } }); await loadMedia(); toast('Tags copied'); render(); } catch (err) { toast(err.message, false); }
}


function selectedMediaIds() { return [...state.selected].map(Number).filter(Boolean); }
function selectedVideoIds() { return (state.media.items || []).filter(x => state.selected.has(x.id) && x.media_type === 'video').map(x => x.id); }


function metadataSchemaPicker() {
  const entries = (((state.metadataSchema || {}).results || [])[0]?.schema?.entries || []).filter(e => e.selectable);
  if (!entries.length) return el('p', { class: 'muted' }, 'Inspect metadata JSON schema to show selectable paths here.');
  return el('div', { class: 'schema-scroll' }, entries.slice(0, 600).map(entry => {
    const cb = el('input', { type: 'checkbox', checked: state.metadataSelectedPaths.has(entry.path), onchange: e => { if (e.target.checked) state.metadataSelectedPaths.add(entry.path); else state.metadataSelectedPaths.delete(entry.path); } });
    return el('label', { class: 'schema-row' }, [
      cb,
      el('code', {}, entry.path),
      el('span', { class: 'muted tiny' }, `${entry.type} · ${entry.token_count || 0} tokens${entry.has_parentheses ? ' · parens' : ''}${entry.has_curly_braces ? ' · braces' : ''}${entry.has_weight_syntax ? ' · weights' : ''}`),
      el('span', { class: 'muted tiny' }, entry.preview || '')
    ]);
  }));
}

function mediaToolsView() {
  const externalPaths = el('textarea', { placeholder: 'Optional external image/video paths, one per line. Selected gallery media are used automatically.' });
  const includeRaw = el('input', { type: 'checkbox' });
  const applyTags = el('input', { type: 'checkbox' });
  const applyCaption = el('input', { type: 'checkbox' });
  const metadataOut = el('pre', { class: 'log' }, state.metadataOutput ? JSON.stringify(state.metadataOutput, null, 2) : 'No metadata extraction run yet.');
  const fieldPaths = el('textarea', { placeholder: 'JSON field paths to concatenate, one per line. Example:\n$.derived.positive_prompt\n$.normalized_metadata.normalized.generation.negative_prompt' });
  const originalDelimiter = el('input', { placeholder: 'Original delimiter: auto, comma, ;, |', value: 'auto' });
  const outputDelimiter = el('input', { placeholder: 'Output delimiter', value: ', ' });
  const splitStrings = el('input', { type: 'checkbox', checked: true });
  const keepParens = el('input', { type: 'checkbox', checked: true });
  const keepBraces = el('input', { type: 'checkbox', checked: true });
  const stripWeights = el('input', { type: 'checkbox' });
  const normalizeFieldTags = el('input', { type: 'checkbox', checked: true });
  const fieldApplyTags = el('input', { type: 'checkbox' });
  const fieldApplyCaption = el('input', { type: 'checkbox' });
  const fieldReplaceTags = el('input', { type: 'checkbox' });
  const fieldOut = el('pre', { class: 'log' }, state.metadataFieldOutput ? JSON.stringify(state.metadataFieldOutput, null, 2) : 'No JSON field inspection/compose run yet.');

  const videoPath = el('input', { placeholder: 'Optional video path if not using selected videos', style: 'min-width:360px' });
  const frameOut = el('input', { placeholder: 'Output folder for PNG frames', value: state.settings.media_frame_output_dir || '', style: 'min-width:320px' });
  const fps = el('input', { type: 'number', step: '0.01', placeholder: 'fps, e.g. 1, 2, 24' });
  const everyN = el('input', { type: 'number', min: '1', placeholder: 'or every N frames' });
  const start = el('input', { type: 'number', step: '0.01', placeholder: 'start seconds' });
  const end = el('input', { type: 'number', step: '0.01', placeholder: 'end seconds' });
  const attachFrames = el('input', { type: 'checkbox' });

  const audioPath = el('input', { placeholder: 'Optional video path if not using selected videos', style: 'min-width:360px' });
  const audioOut = el('input', { placeholder: 'Output folder for extracted audio', value: state.settings.audio_recording_dir || '', style: 'min-width:320px' });
  const audioFmt = el('select', {}, ['wav', 'flac', 'm4a', 'mp3'].map(x => el('option', { value: x }, x)));
  const sampleRate = el('input', { type: 'number', placeholder: 'sample rate, optional' });
  const channels = el('input', { type: 'number', placeholder: 'channels, optional' });
  const attachAudio = el('input', { type: 'checkbox' });

  const recName = el('input', { placeholder: 'recording filename, optional' });
  const recStatus = el('span', { class: 'badge' }, state.recorder ? 'recording...' : 'idle');
  const kritaOut = el('input', { placeholder: 'Optional Krita exchange package folder', value: state.settings.krita_handoff_dir || state.settings.krita_bridge_output_dir || '', style: 'min-width:320px' });
  const editedPath = el('input', { placeholder: 'Edited image path saved from Krita', style: 'min-width:420px' });
  const mediaOut = el('pre', { class: 'log' }, state.mediaToolOutput ? JSON.stringify(state.mediaToolOutput, null, 2) : 'No media tool action run yet.');

  async function startRecording() {
    if (!navigator.mediaDevices || !window.MediaRecorder) throw new Error('Browser audio recording is not available in this browser.');
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.recordChunks = [];
    const recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => { if (e.data && e.data.size) state.recordChunks.push(e.data); };
    recorder.onstop = async () => {
      try {
        const blob = new Blob(state.recordChunks, { type: recorder.mimeType || 'audio/webm' });
        const fd = new FormData();
        fd.append('file', blob, `${recName.value || 'recording'}.webm`);
        if (state.filters.dataset_id) fd.append('dataset_id', state.filters.dataset_id);
        const res = await fetch('/api/media-tools/audio/recording', { method: 'POST', body: fd });
        if (!res.ok) throw new Error(await res.text());
        state.mediaToolOutput = await res.json();
        stream.getTracks().forEach(t => t.stop());
        state.recorder = null;
        toast('Recording saved');
        render();
      } catch (err) { state.recorder = null; toast(err.message, false); render(); }
    };
    state.recorder = recorder;
    recorder.start();
    render();
  }

  return el('div', { class: 'grid' }, [
    card('Metadata Extraction From Images / Videos', [
      el('p', { class: 'muted' }, 'Extract tags/captions from embedded generation metadata in images and videos. This uses the reusable parser logic from the uploaded toolkit, not ComfyUI nodes.'),
      el('div', { class: 'row' }, [el('span', { class: 'badge' }, `${state.selected.size} selected media`), tagProfileSelect(), el('label', {}, [includeRaw, ' Include raw metadata']), el('label', {}, [applyTags, ' Apply tags to selected media']), el('label', {}, [applyCaption, ' Apply caption to selected media'])]),
      externalPaths,
      el('button', { class: 'primary', onclick: async () => {
        try {
          const body = { media_ids: selectedMediaIds(), external_paths: externalPaths.value.split(/\n+/).map(x => x.trim()).filter(Boolean), include_raw: includeRaw.checked };
          if (!body.media_ids.length && !body.external_paths.length) throw new Error('Select media or paste external paths.');
          body.profile_key = state.tagProfile;
          body.apply_tags = applyTags.checked;
          body.apply_caption = applyCaption.checked;
          body.save_sidecars = true;
          state.metadataOutput = await api('/api/media-tools/metadata/extract-now', { method: 'POST', body });
          if (applyTags.checked || applyCaption.checked) await loadMedia();
          toast(`Extracted metadata from ${state.metadataOutput.count || 0} item(s)`);
          render();
        } catch (err) { toast(err.message, false); }
      } }, 'Extract / Apply Metadata'),
      metadataOut
    ]),
    card('Metadata JSON Schema Field Picker / Concatenator', [
      el('p', { class: 'muted' }, 'Inspect the full extracted JSON schema, then select any fields to compose tags or captions. This is useful for ComfyUI workflows, A1111 parameters, NovelAI JSON, video tags, LoRA metadata, and any schema-like payload.'),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => {
          try {
            const ids = selectedMediaIds();
            const path = externalPaths.value.split(/\n+/).map(x => x.trim()).filter(Boolean)[0] || null;
            const body = { media_id: ids[0] || null, path, include_raw: includeRaw.checked };
            if (!body.media_id && !body.path) throw new Error('Select one image/video or paste one external path first.');
            state.metadataSchema = await api('/api/media-tools/metadata/schema', { method: 'POST', body });
            state.metadataFieldOutput = state.metadataSchema;
            const n = (((state.metadataSchema.results || [])[0] || {}).schema || {}).count || 0;
            toast(`Found ${n} metadata schema paths`);
            render();
          } catch (err) { toast(err.message, false); }
        } }, 'Inspect JSON Fields'),
        originalDelimiter, outputDelimiter
      ]),
      metadataSchemaPicker(),
      fieldPaths,
      el('div', { class: 'row' }, [el('label', {}, [splitStrings, ' Split selected strings']), el('label', {}, [keepParens, ' Keep parenthesis tokens']), el('label', {}, [keepBraces, ' Keep { } / [ ] tokens']), el('label', {}, [stripWeights, ' Strip (tag:1.2) weights']), el('label', {}, [normalizeFieldTags, ' Normalize spaces to underscores'])]),
      el('div', { class: 'row' }, [el('label', {}, [fieldApplyTags, ' Apply composed tokens as tags']), el('label', {}, [fieldApplyCaption, ' Apply composed string as caption']), el('label', {}, [fieldReplaceTags, ' Replace tags instead of merge'])]),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const ids = selectedMediaIds();
          const path = externalPaths.value.split(/\n+/).map(x => x.trim()).filter(Boolean)[0] || null;
          const body = { media_id: ids[0] || null, path, include_raw: includeRaw.checked, fields: [...new Set([...state.metadataSelectedPaths, ...fieldPaths.value.split(/\n+/).map(x => x.trim()).filter(Boolean)])], original_delimiter: originalDelimiter.value || 'auto', output_delimiter: outputDelimiter.value || ', ', split_strings: splitStrings.checked, keep_parentheses: keepParens.checked, keep_braces: keepBraces.checked, strip_weight_syntax: stripWeights.checked, normalize_tags: normalizeFieldTags.checked, apply_tags: fieldApplyTags.checked, apply_caption: fieldApplyCaption.checked, replace_tags: fieldReplaceTags.checked, save_sidecars: true, tag_profile: state.tagProfile, order_strategy: state.orderingStrategy };
          if (!body.media_id && !body.path) throw new Error('Select one media item or paste one external path first.');
          if (!body.fields.length) throw new Error('Enter at least one JSON field path.');
          state.metadataFieldOutput = await api('/api/metadata/compose', { method: 'POST', body });
          if (fieldApplyTags.checked || fieldApplyCaption.checked) await loadMedia();
          toast(`Composed ${state.metadataFieldOutput.tokens?.length || state.metadataFieldOutput.results?.[0]?.tokens?.length || 0} token(s)`);
          render();
        } catch (err) { toast(err.message, false); }
      } }, 'Compose / Apply Selected Metadata Fields'),
      fieldOut
    ]),
    card('Video Frame Extraction', [
      el('p', { class: 'muted' }, 'Decode selected videos and save frames as PNG files. PNG avoids adding extra JPEG-style loss after video decoding.'),
      el('div', { class: 'row' }, [el('span', { class: 'badge' }, `${selectedVideoIds().length} selected video(s)`), videoPath]),
      el('div', { class: 'row' }, [frameOut, el('button', { class: 'secondary', onclick: async () => await pickFolder(frameOut, 'Select frame output folder') }, 'Browse Output...')]),
      el('div', { class: 'row' }, [fps, everyN, start, end, el('label', {}, [attachFrames, ' Attach frames to same dataset'])]),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const body = { media_ids: selectedVideoIds(), video_path: videoPath.value || null, output_dir: frameOut.value || null, fps: fps.value ? Number(fps.value) : null, every_n_frames: everyN.value ? Number(everyN.value) : null, start_seconds: start.value ? Number(start.value) : null, end_seconds: end.value ? Number(end.value) : null, attach_to_dataset: attachFrames.checked };
          if (!body.media_ids.length && !body.video_path) throw new Error('Select videos or paste a video path.');
          const r = await api('/api/media-tools/video/extract-frames', { method: 'POST', body });
          toast(`Frame extraction job ${r.job_id} queued`);
          setTab('Jobs');
        } catch (err) { toast(err.message, false); }
      } }, 'Extract PNG Frames')
    ]),
    card('Audio Extraction and Custom Audio Recording', [
      el('p', { class: 'muted' }, 'Extract audio streams from videos for future audio datasets, or record custom clips directly in the browser.'),
      el('div', { class: 'row' }, [audioPath, audioFmt, sampleRate, channels]),
      el('div', { class: 'row' }, [audioOut, el('button', { class: 'secondary', onclick: async () => await pickFolder(audioOut, 'Select audio output folder') }, 'Browse Output...'), el('label', {}, [attachAudio, ' Attach audio to same dataset'])]),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const body = { media_ids: selectedVideoIds(), video_path: audioPath.value || null, output_dir: audioOut.value || null, output_format: audioFmt.value, sample_rate: sampleRate.value ? Number(sampleRate.value) : null, channels: channels.value ? Number(channels.value) : null, attach_to_dataset: attachAudio.checked };
          if (!body.media_ids.length && !body.video_path) throw new Error('Select videos or paste a video path.');
          const r = await api('/api/media-tools/video/extract-audio', { method: 'POST', body });
          toast(`Audio extraction job ${r.job_id} queued`);
          setTab('Jobs');
        } catch (err) { toast(err.message, false); }
      } }, 'Extract Audio'),
      el('hr'),
      el('div', { class: 'row' }, [recName, recStatus, el('button', { class: 'secondary', disabled: Boolean(state.recorder), onclick: async () => { try { await startRecording(); } catch (err) { toast(err.message, false); } } }, 'Start Recording'), el('button', { class: 'danger', disabled: !state.recorder, onclick: () => { if (state.recorder) state.recorder.stop(); } }, 'Stop + Save Recording')])
    ]),
    card('Krita Bridge', [
      el('p', { class: 'muted' }, 'Create an edit package for the active/first selected image, open it in Krita manually, then import the edited image back into the same dataset while preserving tags/caption.'),
      el('div', { class: 'row' }, [kritaOut, el('button', { class: 'secondary', onclick: async () => await pickFolder(kritaOut, 'Select Krita package folder') }, 'Browse Package Folder...')]),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const id = state.activeMedia?.id || selectedMediaIds()[0];
          if (!id) throw new Error('Select or open an image first.');
          state.mediaToolOutput = await api('/api/media-tools/krita/export-package', { method: 'POST', body: { media_id: id, output_dir: kritaOut.value || null, include_sidecars: true } });
          toast('Krita edit package created');
          render();
        } catch (err) { toast(err.message, false); }
      } }, 'Create Krita Edit Package'),
      el('div', { class: 'row' }, [editedPath, el('button', { class: 'secondary', onclick: async () => {
        try {
          const id = state.activeMedia?.id || selectedMediaIds()[0];
          if (!id) throw new Error('Select the source image first.');
          state.mediaToolOutput = await api('/api/media-tools/krita/import-edited', { method: 'POST', body: { source_media_id: id, edited_path: editedPath.value, as_new_media: true, copy_to_dataset: true, preserve_tags: true, preserve_caption: true } });
          await loadMedia();
          toast('Edited image imported');
          render();
        } catch (err) { toast(err.message, false); }
      } }, 'Import Edited Image')]),
      mediaOut
    ])
  ]);
}

function assistantCapableModelFilter(m) {
  const caps = new Set(m.capabilities || []);
  const kind = String(m.kind || '');
  return caps.has('chat') || caps.has('vlm') || caps.has('assistant') || caps.has('image_text_to_text') || caps.has('tag_suggestions') || caps.has('caption_suggestions') || ['assistant','llm','vlm'].includes(kind);
}

function assistantView() {
  const assistantModels = sortedTagSelectionModels(state.models.filter(assistantCapableModelFilter));
  const configuredAssistant = state.assistantConfig?.assistant_model_name || state.settings.assistant_model_name || 'dataset-assistant';
  const configuredOrchestrator = state.assistantConfig?.orchestrator_model_name || state.settings.orchestrator_model_name || configuredAssistant || 'dataset-assistant';
  const model = el('select', { class: 'model-category-select', title: 'Assistant-capable models are category-colored. Hover options for category/provider details.' }, assistantModels.map(modelOptionNode));
  rememberSelect('assistantModelSelection', model, configuredAssistant, true);
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value, capabilities: [] };
  const defaultAssistant = el('select', { class: 'model-category-select' }, assistantModels.map(modelOptionNode));
  setSelectValue(defaultAssistant, configuredAssistant);
  const defaultOrchestrator = el('select', { class: 'model-category-select' }, assistantModels.map(modelOptionNode));
  setSelectValue(defaultOrchestrator, configuredOrchestrator);
  const autoLoad = el('input', { type: 'checkbox', checked: Boolean(state.assistantConfig?.assistant_model_auto_load || state.settings.assistant_model_auto_load) });
  const allowOrch = el('input', { type: 'checkbox', checked: state.assistantConfig?.assistant_allow_orchestration !== false && state.settings.assistant_allow_orchestration !== false });
  const dataset = el('select', {}, datasetOptions()); dataset.value = state.filters.dataset_id || '';
  const modelId = el('input', { placeholder: 'Optional local path / HF repo / cloud model override', style: 'min-width:360px' });
  const external = el('input', { placeholder: 'Optional external image paths separated by ;', style: 'min-width:360px' });
  const prompt = el('textarea', { placeholder: 'Ask how to tag/caption selected data, inspect generation metadata, or format extracted fields.' }, 'Use the selected media and its generation metadata to suggest what tags/caption fields should be kept.');
  const applyTags = el('input', { type: 'checkbox' });
  const applyCaption = el('input', { type: 'checkbox' });
  const includeMetadata = el('input', { type: 'checkbox', checked: state.chatIncludeMetadata !== false, onchange: e => { state.chatIncludeMetadata = e.target.checked; } });
  const assistantAgentTools = el('input', { type: 'checkbox', checked: Boolean(state.assistantAgentToolsChatEnabled || state.settings?.agent_tools_enable_approved_coa_execution), title: 'Tell the assistant that approved local Agent Tools are available and parse COA/tool calls from its response.' });
  assistantAgentTools.addEventListener('change', e => { state.assistantAgentToolsChatEnabled = e.target.checked; state.agentCoaExecutionEnabled = e.target.checked || state.agentCoaExecutionEnabled; });
  const metadataPaths = el('textarea', { rows: '3', placeholder: 'Optional metadata JSON paths to include, one per line. Leave blank to include metadata summary/schema paths.' }, state.chatMetadataPaths || '');
  metadataPaths.addEventListener('input', e => { state.chatMetadataPaths = e.target.value; });
  const convSelect = el('select', { onchange: async e => { try { await loadChatConversation(Number(e.target.value)); render(); } catch (err) { toast(err.message, false); } } }, [el('option', { value: '' }, 'New conversation'), ...(state.chatConversations || []).map(c => el('option', { value: c.id }, `#${c.id} · ${c.title || 'Untitled'} · ${c.updated_at || ''}`))]);
  convSelect.value = state.chatConversationId || '';
  const rt = modelRuntimeControls(selectedModel());
  const reasoning = assistantReasoningControls('assistant');
  const output = el('div', { class: 'chat-log' }, (state.chatMessages || []).map(m => el('div', { class: `chat-msg ${m.role}` }, [el('strong', {}, `${m.role === 'user' ? 'You' : 'Assistant'}${m.id ? ' #' + m.id : ''}`), m.role !== 'user' && m.response?.visible_plan ? visiblePlanPanel(m.response, 'Visible plan for this assistant response') : null, el('pre', {}, m.content), m.id ? el('button', { class: 'secondary small', onclick: async () => { try { const r = await api('/api/models/chat/conversations/fork', { method: 'POST', body: { message_id: m.id } }); state.chatConversationId = r.conversation.id; await loadChatConversation(state.chatConversationId); await loadChatConversations(); toast('Conversation forked from selected message'); render(); } catch (err) { toast(err.message, false); } } }, 'Fork from here') : null].filter(Boolean))));
  if (!state.chatConversationsLoaded) setTimeout(async () => { state.chatConversationsLoaded = true; await loadChatConversations(); render(); }, 0);
  const saveAssistantConfig = async (body) => {
    state.assistantConfig = await api('/api/models/assistant-config', { method: 'PUT', body });
    state.settings.assistant_model_name = state.assistantConfig.assistant_model_name;
    state.settings.orchestrator_model_name = state.assistantConfig.orchestrator_model_name;
    state.settings.assistant_model_auto_load = state.assistantConfig.assistant_model_auto_load;
    state.settings.assistant_allow_orchestration = state.assistantConfig.assistant_allow_orchestration;
    await refreshAll();
  };
  const loadSelectedAssistant = async () => {
    const body = { model_name: model.value || configuredAssistant || 'dataset-assistant', ...runtimeBodyFromControls(rt), options: {} };
    const r = await api('/api/models/load', { method: 'POST', body });
    toast(r.already_loaded ? `${body.model_name} already loaded` : `Assistant model load queued${r.job_id ? ' as job ' + r.job_id : ''}`);
    await refreshAll();
  };
  const unloadSelectedAssistant = async () => {
    const r = await api('/api/models/unload', { method: 'POST', body: { model_name: model.value || configuredAssistant || 'dataset-assistant' } });
    toast(r.job_id ? `Unload queued as job ${r.job_id}` : 'Assistant model unloaded/no-op');
    await refreshAll();
  };
  return el('div', { class: 'grid' }, [
    card('Assistant / Orchestrator Model Control', [
      el('p', { class: 'muted' }, 'Choose which downloaded/local/API LLM or VLM acts as the app assistant. The orchestrator default is used by Orchestrate templates and assistant-driven multi-step runs; it can load/unload like any other model.'),
      el('div', { class: 'row' }, [el('label', {}, ['Current chat model ', model]), el('label', {}, ['Default assistant ', defaultAssistant]), el('label', {}, ['Default orchestrator ', defaultOrchestrator])]),
      modelLifecycleStrip(selectedModel(), true),
      inlineOrchestratorControls(model, 'assistant tab'),
      assistantReasoningPanel(reasoning, 'Think longer / visible plan controls'),
      agentToolsInlinePanel('assistant-tab', 'Assistant tab', () => [...state.selected], model, rt),
      el('div', { class: 'row tight' }, [rt.device, rt.gpuIds, rt.shard, rt.dtype, rt.quant, rt.runtime, el('label', {}, ['TP size', rt.tensorParallel])]),
      rt.maxMemory,
      el('div', { class: 'row' }, [el('label', {}, [autoLoad, ' Auto-load assistant model setting']), el('label', {}, [allowOrch, ' Allow assistant as orchestrator model'])]),
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => { try { await saveAssistantConfig({ assistant_model_name: defaultAssistant.value, orchestrator_model_name: defaultOrchestrator.value, assistant_model_auto_load: autoLoad.checked, assistant_allow_orchestration: allowOrch.checked }); toast('Assistant/orchestrator defaults saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Assistant Defaults'),
        el('button', { class: 'secondary', onclick: async () => { try { defaultAssistant.value = model.value; defaultOrchestrator.value = model.value; await saveAssistantConfig({ assistant_model_name: model.value, orchestrator_model_name: model.value }); toast(`${model.value} set as assistant and orchestrator default`); render(); } catch (err) { toast(err.message, false); } } }, 'Set Selected as Both Defaults'),
        el('button', { class: 'secondary', onclick: async () => { try { await loadSelectedAssistant(); render(); } catch (err) { toast(err.message, false); } } }, 'Load Selected Assistant Model'),
        el('button', { class: 'danger', onclick: async () => { try { await unloadSelectedAssistant(); render(); } catch (err) { toast(err.message, false); } } }, 'Unload Selected Model')
      ]),
      el('pre', { class: 'log' }, JSON.stringify({ assistant_model_name: configuredAssistant, orchestrator_model_name: configuredOrchestrator, selected_model: model.value, selected_loaded: selectedModel().loaded || false }, null, 2))
    ]),
    orchestratorPlannerCard('assistant tab'),
    card('Talk With Dataset / LLM / VLM + Metadata Context', [
      el('p', { class: 'muted' }, 'Conversations are persisted with message history and context snapshots. The selected assistant can include generation metadata/schema paths from selected media and can later serve as the user-directed orchestrator for multi-step tool/model runs.'),
      el('div', { class: 'row' }, [convSelect, el('button', { class: 'secondary', onclick: () => { state.chatConversationId = null; state.chatMessages = []; render(); } }, 'New Conversation'), el('button', { class: 'secondary', onclick: async () => { await loadChatConversations(); toast('Conversations refreshed'); render(); } }, 'Refresh Conversations'), state.chatConversationId ? el('button', { class: 'danger', onclick: async () => { try { await api(`/api/models/chat/conversations/${state.chatConversationId}`, { method: 'DELETE' }); state.chatConversationId = null; state.chatMessages = []; await loadChatConversations(); render(); } catch (err) { toast(err.message, false); } } }, 'Archive Conversation') : null].filter(Boolean)),
      el('div', { class: 'row' }, [dataset, tagProfileSelect()]),
      el('div', { class: 'row' }, [modelId, external]),
      prompt,
      el('details', { open: false }, [el('summary', {}, 'Metadata context options'), el('div', { class: 'row' }, [el('label', {}, [includeMetadata, ' Include selected media generation metadata / schema context'])]), metadataPaths]),
      el('div', { class: 'row' }, [
        el('label', {}, [applyTags, ' Apply suggested tags to selected media']),
        el('label', {}, [applyCaption, ' Apply suggested caption to selected media']),
        el('label', { title: 'Adds the local-action tool contract to this assistant chat.' }, [assistantAgentTools, ' enable approved local tools/COA when needed']),
        voiceSurfaceToggles(),
        el('button', { class: 'secondary', disabled: !voiceSurfaceSttEnabled(), onclick: () => startVoice(prompt) }, 'Voice Input'),
        el('button', { class: 'primary', onclick: async () => {
          try {
            const options = { max_new_tokens: state.settings.model_max_new_tokens || 256, max_images: 4, temperature: state.settings.model_temperature || 0.2, tag_profile: state.tagProfile, chat_assistant: true, agent_tools_chat: Boolean(assistantAgentTools.checked), agent_tools_execute_coa_enabled: Boolean(assistantAgentTools.checked || state.agentCoaExecutionEnabled || state.settings?.agent_tools_enable_approved_coa_execution), auto_continue_incomplete: true, ...reasoningOptionsFromControls(reasoning) };
            if (modelId.value.trim()) options.model_id = modelId.value.trim();
            const body = {
              model_name: model.value || configuredAssistant || 'dataset-assistant',
              prompt: prompt.value,
              conversation_id: state.chatConversationId || null,
              conversation_title: prompt.value.slice(0, 80),
              dataset_id: dataset.value ? Number(dataset.value) : null,
              media_ids: [...state.selected],
              external_paths: external.value.split(';').map(x => x.trim()).filter(Boolean),
              history: state.chatMessages.map(m => ({ role: m.role, content: m.content })),
              include_metadata_context: includeMetadata.checked,
              metadata_field_paths: metadataPaths.value.split(/\n+/).map(x => x.trim()).filter(Boolean),
              metadata_include_raw: false,
              use_selected_media: true,
              apply_suggested_tags: applyTags.checked,
              apply_suggested_caption: applyCaption.checked,
              ...runtimeBodyFromControls(rt),
              options,
            };
            const r = await api('/api/models/chat', { method: 'POST', body });
            state.chatConversationId = r.conversation_id;
            state.chatMessages = r.history || [...state.chatMessages, { role: 'user', content: prompt.value }, { role: 'assistant', content: r.response }];
            if (assistantAgentTools.checked && r.response) {
              try {
                const parsed = await api('/api/agent-tools/parse-tool-calls', { method: 'POST', body: { text: r.response } });
                if ((parsed.tool_calls || []).length) {
                  state.agentSurfacePlans['agent-assistant-tab'] = {
                    ...(state.agentSurfacePlans['agent-assistant-tab'] || {}),
                    plan: { summary: 'Executable COA/tool calls parsed from assistant chat response', steps: parsed.tool_calls },
                    tool_calls: parsed.tool_calls,
                    response: r.response,
                    conversation_id: r.conversation_id
                  };
                  toast(`Parsed ${parsed.tool_calls.length} executable COA/tool call(s) from assistant response`);
                }
              } catch (_) {}
            }
            await loadChatConversations();
            if (r.applied?.media_ids?.length) await refreshMediaRows(r.applied.media_ids);
            toast(`Assistant response from ${r.model_name}`);
            render();
          } catch (err) { toast(err.message, false); }
        } }, 'Send to Assistant')
      ]),
      lastVoiceOutputPanel(),
      output
    ].filter(Boolean))
  ]);
}

function voiceModelOptions(kind) {
  const rows = (state.models || []).filter(m => String(m.kind || '').toLowerCase() === kind);
  const fallback = kind === 'tts'
    ? [{ name: 'kokoro-82m', label: 'Kokoro 82M TTS' }]
    : [{ name: 'whisper-large-v3-turbo', label: 'Whisper Large v3 Turbo STT' }];
  return (rows.length ? rows : fallback).map(m => { const hf = modelHFAccessLabel(m); return el('option', { value: m.name, title: `${m.label || m.name} · ${m.repo_id || ''} · ${m.memory_note || ''}${modelHFAccessTitle(m) ? ' · ' + modelHFAccessTitle(m) : ''}` }, `${m.label || m.name}${hf ? ' · ' + hf : ''}${m.downloaded ? ' · downloaded' : ''}${m.loaded ? ' · loaded' : ''}`); });
}

function voiceModelSelect(kind, value, attrs = {}) {
  const select = el('select', attrs, voiceModelOptions(kind));
  select.value = value || (kind === 'tts' ? (state.settings?.voice_tts_model_name || 'kokoro-82m') : (state.settings?.voice_stt_model_name || 'whisper-large-v3-turbo'));
  if (!select.value && select.options.length) select.value = select.options[0].value;
  return select;
}

async function refreshBrowserAudioDevices({ requestPermission = false } = {}) {
  try {
    if (!navigator.mediaDevices?.enumerateDevices) throw new Error('Browser media device enumeration is unavailable.');
    if (requestPermission && navigator.mediaDevices.getUserMedia) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(t => t.stop());
    }
    const devices = await navigator.mediaDevices.enumerateDevices();
    state.browserAudioDevices = {
      inputs: devices.filter(d => d.kind === 'audioinput').map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Microphone ${i + 1}` })),
      outputs: devices.filter(d => d.kind === 'audiooutput').map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Speaker ${i + 1}` })),
    };
    return state.browserAudioDevices;
  } catch (err) {
    toast(err.message || 'Audio device scan failed.', false);
    return state.browserAudioDevices || { inputs: [], outputs: [] };
  }
}

function audioDeviceSelect(kind, selected, attrs = {}) {
  const list = kind === 'output' ? (state.browserAudioDevices?.outputs || []) : (state.browserAudioDevices?.inputs || []);
  const select = el('select', attrs, [el('option', { value: '' }, kind === 'output' ? 'Browser default speakers' : 'Browser default microphone'), ...list.map(d => el('option', { value: d.deviceId, title: d.deviceId }, d.label || d.deviceId))]);
  select.value = selected || '';
  return select;
}

function appendTextToInput(target, text) {
  if (!target || !text) return;
  const prior = target.value || '';
  const sep = prior && !/\s$/.test(prior) ? ' ' : '';
  target.value = `${prior}${sep}${text}`;
  target.dispatchEvent(new Event('input', { bubbles: true }));
  target.focus();
}

async function startVoice(target) {
  if (state.voiceRecorder && state.voiceRecorder.state !== 'inactive') {
    state.voiceRecorder.stop();
    toast('Stopping recording and transcribing...');
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    return toast('This browser does not expose MediaRecorder/getUserMedia. Use the text box or a browser with microphone recording support.', false);
  }
  if (!voiceSurfaceSttEnabled()) {
    return toast('Speech-to-text is unchecked for this assistant surface.', false);
  }
  if (state.settings?.voice_stt_enabled === false && !state.voiceStatus?.settings?.loaded_voice_models?.stt) {
    return toast('Speech-to-text is disabled in Settings → Voice Input / Speech Output.', false);
  }
  try {
    const deviceId = state.settings?.voice_browser_input_device_id || '';
    const audio = deviceId ? { deviceId: { exact: deviceId } } : true;
    const stream = await navigator.mediaDevices.getUserMedia({ audio });
    const chunks = [];
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm';
    const rec = new MediaRecorder(stream, { mimeType: mime });
    state.voiceRecorder = rec;
    state.voiceRecordTarget = target;
    state.voiceRecordStartedAt = Date.now();
    rec.ondataavailable = e => { if (e.data && e.data.size) chunks.push(e.data); };
    rec.onerror = e => { toast(e.error?.message || 'Voice recorder failed.', false); stream.getTracks().forEach(t => t.stop()); state.voiceRecorder = null; render(true, true); };
    rec.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(chunks, { type: mime });
      state.voiceRecorder = null;
      state.voiceBusy = true;
      render(true, true);
      try {
        const fd = new FormData();
        fd.append('file', blob, `voice_${Date.now()}.webm`);
        fd.append('model_name', state.settings?.voice_stt_model_name || 'whisper-large-v3-turbo');
        fd.append('language', state.settings?.voice_stt_language || '');
        fd.append('device', state.settings?.voice_stt_device || 'auto');
        fd.append('device_ids', (state.settings?.voice_stt_device_ids || []).join(','));
        fd.append('torch_dtype', state.settings?.voice_stt_torch_dtype || 'auto');
        fd.append('quantization', state.settings?.voice_stt_quantization || 'none');
        fd.append('runtime_engine', 'transformers');
        fd.append('load_policy', state.settings?.voice_stt_load_policy || 'on_demand');
        const r = await api('/api/voice/transcribe', { method: 'POST', body: fd });
        appendTextToInput(target || state.voiceRecordTarget, r.text || '');
        state.voiceStatus = await api('/api/voice/status').catch(() => state.voiceStatus);
        toast(r.text ? `Voice transcribed with ${r.model_name}` : 'Voice transcription returned empty text.', Boolean(r.text));
      } catch (err) {
        toast(err.message || 'Voice transcription failed.', false);
      } finally {
        state.voiceBusy = false;
        render(true, true);
      }
    };
    rec.start();
    toast('Recording voice. Click Stop & Transcribe when finished.');
    render(true, true);
  } catch (err) {
    state.voiceRecorder = null;
    toast(err.message || 'Could not start microphone recording.', false);
    render(true, true);
  }
}

function voiceSurfaceSttEnabled() {
  if (state.voiceSurfaceSttEnabled === null || state.voiceSurfaceSttEnabled === undefined) return state.settings?.voice_stt_enabled !== false;
  return Boolean(state.voiceSurfaceSttEnabled);
}

function voiceSurfaceTtsEnabled() {
  const loadedTts = Boolean(state.voiceStatus?.settings?.loaded_voice_models?.tts);
  if (state.voiceSurfaceTtsEnabled === null || state.voiceSurfaceTtsEnabled === undefined) return Boolean(state.settings?.voice_tts_enabled || loadedTts);
  return Boolean(state.voiceSurfaceTtsEnabled);
}

function voiceInputButton(target) {
  const active = state.voiceRecorder && state.voiceRecorder.state !== 'inactive';
  const enabled = voiceSurfaceSttEnabled();
  const label = active ? 'Stop & Transcribe' : state.voiceBusy ? 'Transcribing...' : 'Start Voice';
  return el('button', { class: active ? 'danger small' : 'secondary small', disabled: Boolean(state.voiceBusy || !enabled), title: enabled ? 'Record with your selected microphone, transcribe locally/remotely with the selected STT model, then insert editable text into this message box.' : 'STT is unchecked for this assistant surface.', onclick: () => startVoice(target) }, label);
}

function voiceSurfaceToggles() {
  const stt = el('input', { type: 'checkbox', checked: voiceSurfaceSttEnabled(), onchange: e => { state.voiceSurfaceSttEnabled = Boolean(e.target.checked); toast(`Speech-to-text ${state.voiceSurfaceSttEnabled ? 'enabled' : 'disabled'} for assistant surfaces`); render(true, true); } });
  const tts = el('input', { type: 'checkbox', checked: voiceSurfaceTtsEnabled(), onchange: e => { state.voiceSurfaceTtsEnabled = Boolean(e.target.checked); toast(`Text-to-speech ${state.voiceSurfaceTtsEnabled ? 'enabled' : 'disabled'} for assistant surfaces`); render(true, true); } });
  const loaded = state.voiceStatus?.settings?.loaded_voice_models || {};
  return el('span', { class: 'row tight voice-surface-toggles' }, [
    el('label', { class: 'tiny muted', title: `Selected STT: ${state.settings?.voice_stt_model_name || 'default'}${loaded.stt ? ' · loaded: ' + loaded.stt : ''}` }, [stt, ' STT']),
    el('label', { class: 'tiny muted', title: `Selected TTS: ${state.settings?.voice_tts_model_name || 'default'}${loaded.tts ? ' · loaded: ' + loaded.tts : ''}` }, [tts, ' TTS'])
  ]);
}

function lastVoiceOutputPanel() {
  const out = state.lastVoiceOutput;
  const err = state.lastVoiceError;
  if (!out && !err && !state.ttsBusy) return null;
  const body = [];
  if (state.ttsBusy) body.push(el('p', { class: 'muted tiny' }, 'Generating speech audio...'));
  if (out?.url) {
    const url = `${out.url}${out.url.includes('?') ? '&' : '?'}t=${encodeURIComponent(out.cacheBust || Date.now())}`;
    body.push(el('audio', { controls: true, preload: 'auto', src: url, style: 'width:100%; margin-top:0.35rem;' }));
    body.push(el('div', { class: 'row tight' }, [
      el('span', { class: 'muted tiny' }, `${out.model_name || 'TTS'} · ${(out.bytes || 0).toLocaleString()} bytes${out.chunked ? ` · stitched ${out.chunk_count} chunks` : ''}`),
      el('button', { class: 'secondary tiny', onclick: async () => { try { await playVoiceOutput(out); } catch (e) { toast(e.message || 'Browser playback failed; use the audio control.', false); } } }, 'Play again'),
      el('a', { class: 'button secondary tiny', href: url, target: '_blank', download: '' }, 'Open/Download WAV')
    ]));
  }
  if (err) body.push(el('pre', { class: 'log tiny-log bad' }, String(err).slice(0, 4000)));
  return el('details', { class: 'voice-output-panel', open: Boolean(out || err) }, [el('summary', {}, 'Last speech output / playback'), ...body]);
}

async function playVoiceOutput(out) {
  if (!out?.url) throw new Error('No TTS audio URL is available.');
  const url = `${out.url}${out.url.includes('?') ? '&' : '?'}t=${encodeURIComponent(out.cacheBust || Date.now())}`;
  const audio = new Audio(url);
  audio.preload = 'auto';
  const sink = state.settings?.voice_browser_output_device_id || '';
  if (sink && typeof audio.setSinkId === 'function') {
    try { await audio.setSinkId(sink); } catch (err) { toast('Browser refused selected output device; falling back to default speakers.', false); }
  }
  try {
    await audio.play();
  } catch (err) {
    state.lastVoiceError = `Browser did not autoplay the generated WAV. Use the visible audio player. Playback error: ${err.message || err}`;
    render(true, true);
    throw err;
  }
}

async function speakAssistantText(text, messageId = null, overrides = {}) {
  const value = String(text || '').trim();
  if (!value) return toast('No assistant text to speak.', false);
  const loadedTtsName = state.voiceStatus?.settings?.loaded_voice_models?.tts || '';
  const loadedTts = Boolean(loadedTtsName);
  const enabled = overrides.voice_tts_enabled ?? voiceSurfaceTtsEnabled();
  if (enabled === false && !loadedTts && !overrides.force_enabled) return toast('Text-to-speech is unchecked or disabled. Check TTS near the chat box, enable TTS in Settings, or load a TTS model first.', false);
  state.ttsBusy = true;
  state.lastVoiceError = null;
  render(true, true);
  try {
    const body = {
      text: value,
      model_name: overrides.model_name || (enabled === false && loadedTtsName ? loadedTtsName : state.settings?.voice_tts_model_name) || loadedTtsName || 'kokoro-82m',
      voice: overrides.voice || state.settings?.voice_tts_voice || 'af_heart',
      language: overrides.language ?? state.settings?.voice_tts_language ?? null,
      device: overrides.device || state.settings?.voice_tts_device || 'auto',
      device_ids: overrides.device_ids || state.settings?.voice_tts_device_ids || [],
      torch_dtype: overrides.torch_dtype || state.settings?.voice_tts_torch_dtype || 'auto',
      quantization: overrides.quantization || state.settings?.voice_tts_quantization || 'none',
      runtime_engine: overrides.runtime_engine || 'transformers',
      load_policy: overrides.load_policy || state.settings?.voice_tts_load_policy || 'on_demand',
      enabled: enabled !== false || loadedTts || Boolean(overrides.force_enabled),
      voice_tts_enabled: enabled !== false || loadedTts || Boolean(overrides.force_enabled),
      force_enabled: Boolean(overrides.force_enabled || loadedTts),
      options: {
        chunk_long_text: state.settings?.voice_tts_chunk_long_text !== false,
        max_chunk_chars: Number(state.settings?.voice_tts_max_chunk_chars || 360),
        chunk_pause_ms: Number(state.settings?.voice_tts_chunk_pause_ms || 180),
        ...(overrides.options || {})
      }
    };
    toast('Generating full speech audio...');
    const r = await api('/api/voice/synthesize', { method: 'POST', body });
    const out = { ...r, cacheBust: Date.now() };
    state.lastVoiceOutput = out;
    state.lastVoiceError = null;
    state.voiceStatus = await api('/api/voice/status').catch(() => state.voiceStatus);
    render(true, true);
    try {
      await playVoiceOutput(out);
      if (messageId) state.ttsSpokenMessageIds.add(String(messageId));
      toast(r.chunked ? `Speech generated and stitched from ${r.chunk_count} chunks.` : 'Speech generated.');
    } catch (playErr) {
      toast('Speech WAV was generated, but the browser did not autoplay it. Use the visible audio player.', false);
    }
  } catch (err) {
    state.lastVoiceError = err.message || 'Text-to-speech failed.';
    toast(state.lastVoiceError, false);
    render(true, true);
  } finally {
    state.ttsBusy = false;
    render(true, true);
  }
}


function parseGpuIds(value) {
  return String(value || '').split(/[;,\s]+/).map(x => x.trim().replace(/^cuda:/i, '')).filter(Boolean).map(x => Number(x)).filter(x => Number.isInteger(x) && x >= 0);
}

function nonBlank(value, fallback) {
  const text = String(value ?? '').trim();
  return text || fallback;
}
function selectValueOr(select, fallback) {
  return nonBlank(select?.value, fallback);
}
function settingValueOr(key, fallback) {
  return nonBlank(state.settings?.[key], fallback);
}
function runtimeBodyFromControls(rt, overrides = {}) {
  return {
    device: selectValueOr(rt.device, 'auto'),
    device_ids: parseGpuIds(rt.gpuIds?.value),
    sharding_strategy: selectValueOr(rt.shard, 'none'),
    max_memory: parseMaxMemory(rt.maxMemory?.value),
    torch_dtype: selectValueOr(rt.dtype, 'auto'),
    quantization: selectValueOr(rt.quant, 'none'),
    runtime_engine: selectValueOr(rt.runtime, 'transformers'),
    tensor_parallel_size: Number(rt.tensorParallel?.value || 1),
    ...overrides
  };
}
function defaultRuntimeBody(overrides = {}) {
  return {
    device: (state.settings.preferred_devices || ['auto'])[0] || 'auto',
    device_ids: state.settings.default_model_device_ids || [0],
    sharding_strategy: settingValueOr('default_model_sharding_strategy', state.settings.default_model_sharding ? 'auto' : 'none'),
    max_memory: {},
    torch_dtype: settingValueOr('default_model_dtype', 'auto'),
    quantization: settingValueOr('default_model_quantization', 'none'),
    runtime_engine: settingValueOr('default_model_runtime_engine', 'transformers'),
    tensor_parallel_size: Number(state.settings.default_model_tensor_parallel_size || state.settings.default_tensor_parallel_size || 1),
    ...overrides
  };
}
function assistantReasoningDefaults(scope = 'assistant') {
  const s = state.settings || {};
  const modeKey = scope === 'code' ? 'codeThinkingMode' : 'assistantThinkingMode';
  const effortKey = scope === 'code' ? 'codeReasoningEffort' : 'assistantReasoningEffort';
  const showKey = scope === 'code' ? 'codeShowVisiblePlan' : 'assistantShowVisiblePlan';
  const liveKey = scope === 'code' ? 'codeShowLiveActionNotes' : 'assistantShowLiveActionNotes';
  const passKey = scope === 'code' ? 'codePlanningPasses' : 'assistantPlanningPasses';
  const planTokenKey = scope === 'code' ? 'codePlanMaxTokens' : 'assistantPlanMaxTokens';
  const chatTokenKey = scope === 'code' ? 'codeMinChatTokens' : 'assistantMinChatTokens';
  return {
    mode: state[modeKey] || s.assistant_thinking_mode || 'balanced',
    effort: state[effortKey] || s.assistant_reasoning_effort || 'medium',
    showPlan: state[showKey] !== false && s.assistant_show_visible_plan !== false,
    showLiveActionNotes: (state[scope === 'code' ? 'codeShowLiveActionNotes' : 'assistantShowLiveActionNotes'] !== false) && s.assistant_show_live_action_notes !== false,
    passes: state[passKey] || s.assistant_planning_passes || 1,
    planTokens: state[planTokenKey] || s.assistant_plan_max_tokens || 768,
    chatTokens: state[chatTokenKey] || (scope === 'code' ? (s.assistant_deep_chat_tokens || 4096) : (s.assistant_min_chat_tokens || 1024))
  };
}
function assistantReasoningControls(scope = 'assistant') {
  const d = assistantReasoningDefaults(scope);
  const modeKey = scope === 'code' ? 'codeThinkingMode' : 'assistantThinkingMode';
  const effortKey = scope === 'code' ? 'codeReasoningEffort' : 'assistantReasoningEffort';
  const showKey = scope === 'code' ? 'codeShowVisiblePlan' : 'assistantShowVisiblePlan';
  const liveKey = scope === 'code' ? 'codeShowLiveActionNotes' : 'assistantShowLiveActionNotes';
  const passKey = scope === 'code' ? 'codePlanningPasses' : 'assistantPlanningPasses';
  const planTokenKey = scope === 'code' ? 'codePlanMaxTokens' : 'assistantPlanMaxTokens';
  const chatTokenKey = scope === 'code' ? 'codeMinChatTokens' : 'assistantMinChatTokens';
  const mode = el('select', { title: 'How much extra planning/continuation budget to use before the final answer.' }, ['off','fast','balanced','deep'].map(x => el('option', { value: x }, x))); mode.value = d.mode;
  const effort = el('select', { title: 'Reasoning effort hint for providers/runtimes that support it; local models use plan-before-answer prompting.' }, ['none','low','medium','high','max'].map(x => el('option', { value: x }, x))); effort.value = d.effort;
  const showPlan = el('input', { type: 'checkbox', checked: d.showPlan, title: 'Show a concise visible plan/action-notes panel. This is not hidden chain-of-thought.' });
  const showLive = el('input', { type: 'checkbox', checked: d.showLiveActionNotes !== false, title: 'Show a temporary live action-notes overlay while a response/tool run is active. This is generated status, not hidden chain-of-thought.' });
  const passes = el('input', { type: 'number', min: '0', max: '3', value: d.passes, title: 'Number of visible planning passes before final response.' });
  const planTokens = el('input', { type: 'number', min: '128', max: '4096', value: d.planTokens, title: 'Token budget for the visible plan.' });
  const chatTokens = el('input', { type: 'number', min: '256', max: '16384', value: d.chatTokens, title: 'Minimum token budget for final chat response.' });
  const remember = () => { state[modeKey] = mode.value; state[effortKey] = effort.value; state[showKey] = showPlan.checked; state[liveKey] = showLive.checked; state[passKey] = passes.value; state[planTokenKey] = planTokens.value; state[chatTokenKey] = chatTokens.value; };
  [mode, effort, showPlan, showLive, passes, planTokens, chatTokens].forEach(ctrl => ctrl.addEventListener('change', remember));
  planTokens.addEventListener('input', remember); chatTokens.addEventListener('input', remember); passes.addEventListener('input', remember);
  return { mode, effort, showPlan, showLive, passes, planTokens, chatTokens, scope };
}
function reasoningOptionsFromControls(ctrl = null, overrides = {}) {
  const d = ctrl ? {
    mode: ctrl.mode.value,
    effort: ctrl.effort.value,
    showPlan: ctrl.showPlan.checked,
    showLiveActionNotes: ctrl.showLive ? ctrl.showLive.checked : true,
    passes: Number(ctrl.passes.value || 0),
    planTokens: Number(ctrl.planTokens.value || 768),
    chatTokens: Number(ctrl.chatTokens.value || 1024)
  } : assistantReasoningDefaults();
  return {
    thinking_mode: d.mode || 'balanced',
    reasoning_effort: d.effort || 'medium',
    show_visible_plan: d.showPlan !== false,
    show_live_action_notes: d.showLiveActionNotes !== false,
    plan_before_answer: d.showPlan !== false && d.mode !== 'off',
    planning_passes: Number(d.passes || 0),
    plan_max_new_tokens: Number(d.planTokens || 768),
    min_chat_max_new_tokens: Number(d.chatTokens || 1024),
    think_longer: d.mode !== 'off',
    assistant_reasoning: d.mode !== 'off',
    ...overrides
  };
}
function assistantReasoningPanel(ctrl, label = 'Reasoning / planning controls') {
  return el('details', { class: 'reasoning-controls', open: false }, [
    el('summary', {}, label),
    el('p', { class: 'muted tiny' }, 'Think-longer mode performs an optional visible planning pass and raises token/continuation budgets. It shows user-facing plan/action notes, not provider/private hidden chain-of-thought.'),
    el('div', { class: 'row tight' }, [
      el('label', {}, ['mode ', ctrl.mode]),
      el('label', {}, ['effort ', ctrl.effort]),
      el('label', {}, [ctrl.showPlan, ' show visible plan']),
      el('label', {}, [ctrl.showLive, ' live action-notes overlay']),
      el('label', {}, ['plan passes ', ctrl.passes]),
      el('label', {}, ['plan tokens ', ctrl.planTokens]),
      el('label', {}, ['final min tokens ', ctrl.chatTokens])
    ])
  ]);
}
function visiblePlanPanel(result, title = 'Visible plan / action notes') {
  const plan = result?.visible_plan || result?.reasoning?.visible_plan || '';
  const notes = result?.action_notes || [];
  if (!plan && !(notes || []).length && !result?.reasoning) return null;
  return el('details', { class: 'visible-plan-panel', open: Boolean(plan) }, [
    el('summary', {}, title),
    el('p', { class: 'muted tiny' }, 'This is a model-generated, user-visible planning summary. It is separate from the final answer and is not hidden/private chain-of-thought.'),
    plan ? el('pre', { class: 'log compact' }, plan) : null,
    (notes || []).length ? el('ul', {}, notes.map(n => el('li', {}, n))) : null,
    result?.reasoning ? el('details', {}, [el('summary', {}, 'Reasoning/planning metadata'), el('pre', { class: 'log compact' }, JSON.stringify(result.reasoning, null, 2))]) : null
  ].filter(Boolean));
}
function parseMaxMemory(value) {
  const out = {};
  String(value || '').split(/[\n,;]+/).forEach(line => {
    const m = line.trim().match(/^(?:cuda:)?(\d+)\s*[:=]\s*(.+)$/i);
    if (m) out[Number(m[1])] = m[2].trim();
  });
  return out;
}
function cudaDeviceRows() {
  return (state.modelResource?.devices || []).filter(d => String(d.id || '').startsWith('cuda:'));
}
function modelPlacementFor(mOrName) {
  const name = typeof mOrName === 'string' ? mOrName : (mOrName?.name || '');
  const catalog = typeof mOrName === 'object' ? mOrName : (state.models || []).find(m => m.name === name);
  const lifecycle = state.modelStatuses?.models?.[name] || {};
  return catalog?.placement || lifecycle?.placement || null;
}
function defaultModelLoadPrefs(m) {
  const defaultIds = state.settings.default_model_device_ids || [0];
  const devices = cudaDeviceRows();
  const ids = defaultIds.length ? defaultIds : (devices.length ? [Number(String(devices[0].id).split(':')[1] || 0)] : []);
  const minGpus = Number(m?.min_gpus || 1);
  const needsShard = Number(m?.vram_gb || 0) > Math.max(0, ...devices.map(d => Number(d.estimated_available_gb || d.total_memory_gb || 0))) || minGpus > 1;
  const selectedIds = ids.length >= minGpus ? ids : devices.slice(0, minGpus).map(d => Number(String(d.id).split(':')[1] || 0));
  const precisionText = String(m?.precision || '').toLowerCase();
  const inferredDtype = precisionText.includes('bf16') ? 'bfloat16' : (precisionText.includes('fp16') || precisionText.includes('float16') ? 'float16' : 'auto');
  return {
    device: (state.settings.preferred_devices || ['auto'])[0] || 'auto',
    gpuIds: selectedIds.join(','),
    shard: settingValueOr('default_model_sharding_strategy', state.settings.default_model_sharding ? 'auto' : (needsShard ? 'balanced' : 'none')),
    dtype: settingValueOr('default_model_dtype', inferredDtype),
    quant: settingValueOr('default_model_quantization', 'none'),
    runtime: settingValueOr('default_model_runtime_engine', 'transformers'),
    tensorParallel: String(state.settings.default_model_tensor_parallel_size || state.settings.default_tensor_parallel_size || 1),
    maxMemory: ''
  };
}
function modelLoadPrefs(name, m) {
  if (!state.modelLoadPrefs[name]) state.modelLoadPrefs[name] = defaultModelLoadPrefs(m);
  return state.modelLoadPrefs[name];
}
function placementBodyForModel(m, prefs) {
  return {
    model_name: m.name,
    device: prefs.device || 'auto',
    device_ids: parseGpuIds(prefs.gpuIds),
    sharding_strategy: prefs.shard || 'none',
    max_memory: parseMaxMemory(prefs.maxMemory),
    torch_dtype: prefs.dtype || 'auto',
    quantization: prefs.quant || 'none',
    runtime_engine: prefs.runtime || 'transformers',
    tensor_parallel_size: Number(prefs.tensorParallel || 1),
    options: { tag_profile: state.tagProfile }
  };
}
function planStatusText(plan) {
  if (!plan) return '';
  const errors = plan.errors || [];
  const warnings = plan.warnings || [];
  const ids = (plan.device_ids || []).map(x => `cuda:${x}`).join(', ') || 'CPU/API/auto';
  const est = Number(plan.estimated_vram_gb || 0).toFixed(2);
  const fit = errors.length ? 'Placement blocked' : 'Placement OK';
  return `${fit}: ${ids}; estimated VRAM ${est} GB${warnings.length ? '; warnings: ' + warnings.join(' ') : ''}${errors.length ? '; errors: ' + errors.join(' ') : ''}`;
}
function modelPlacementSummary(m) {
  const placement = modelPlacementFor(m);
  if (!placement) return el('div', { class: 'muted tiny' }, 'Placement: not loaded/reserved yet.');
  const ids = (placement.device_ids || []).map(x => `cuda:${x}`).join(', ') || placement.device || 'CPU/API';
  const perGpu = placement.per_gpu_reserved_gb || placement.per_device_gb || {};
  const reserves = Object.keys(perGpu).length ? Object.entries(perGpu).map(([k,v]) => `cuda:${String(k).replace('cuda:', '')}≈${v}GB`).join(', ') : '';
  return el('div', { class: 'muted tiny model-placement-summary' }, `Placement: ${placement.state || (m.loaded ? 'loaded' : 'planned')} on ${ids}${placement.sharding_strategy ? ` · shard=${placement.sharding_strategy}` : ''}${placement.estimated_vram_gb ? ` · est ${placement.estimated_vram_gb}GB` : ''}${reserves ? ` · ${reserves}` : ''}`);
}
function modelLoadControls(m) {
  const prefs = modelLoadPrefs(m.name, m);
  const set = (key, value) => { prefs[key] = value; };
  const device = el('input', { value: prefs.device, placeholder: 'auto, cpu, cuda:0', 'data-form-key': `model-load-device-${m.name}`, oninput: e => set('device', e.target.value) });
  const gpuIds = el('input', { value: prefs.gpuIds, placeholder: 'GPU ids: 0,1', 'data-form-key': `model-load-gpus-${m.name}`, oninput: e => set('gpuIds', e.target.value) });
  const shard = el('select', { 'data-form-key': `model-load-shard-${m.name}`, onchange: e => set('shard', e.target.value) }, ['none','auto','balanced','balanced_low_0','sequential','custom'].map(x => el('option', { value: x }, x)));
  shard.value = prefs.shard || 'none';
  const dtype = el('select', { 'data-form-key': `model-load-dtype-${m.name}`, onchange: e => set('dtype', e.target.value) }, ['auto','float16','bfloat16','float32'].map(x => el('option', { value: x }, x)));
  dtype.value = prefs.dtype || 'auto';
  const quant = el('select', { 'data-form-key': `model-load-quant-${m.name}`, onchange: e => set('quant', e.target.value) }, ['none','8bit','4bit'].map(x => el('option', { value: x }, x)));
  quant.value = prefs.quant || 'none';
  const runtime = el('select', { 'data-form-key': `model-load-runtime-${m.name}`, onchange: e => set('runtime', e.target.value) }, ['transformers','vllm','sglang','llama.cpp','cloud','auto'].map(x => el('option', { value: x }, x)));
  runtime.value = prefs.runtime || 'transformers';
  const tensorParallel = el('input', { type: 'number', min: '1', max: '16', value: prefs.tensorParallel || '1', placeholder: 'TP', title: 'Tensor parallel size', 'data-form-key': `model-load-tp-${m.name}`, oninput: e => set('tensorParallel', e.target.value) });
  const maxMemory = el('textarea', { rows: 2, placeholder: 'Optional max memory: 0=23GiB\n1=23GiB', 'data-form-key': `model-load-maxmem-${m.name}`, oninput: e => set('maxMemory', e.target.value) }, prefs.maxMemory || '');
  const selectedGpuIds = () => new Set(parseGpuIds(prefs.gpuIds));
  const gpuPicker = cudaDeviceRows().length ? el('div', { class: 'gpu-pick-row' }, cudaDeviceRows().map(d => {
    const idx = Number(String(d.id || '').replace('cuda:', ''));
    const check = el('input', { type: 'checkbox', checked: selectedGpuIds().has(idx), onchange: e => {
      const ids = selectedGpuIds();
      if (e.target.checked) ids.add(idx); else ids.delete(idx);
      prefs.gpuIds = [...ids].sort((a,b) => a - b).join(',');
      gpuIds.value = prefs.gpuIds;
      state.modelPlacementPlans[m.name] = null;
    } });
    const physical = Number(d.physical_total_memory_gb || d.total_memory_gb || 0);
    const driverFree = d.free_memory_gb !== undefined && d.free_memory_gb !== null ? Number(d.free_memory_gb) : null;
    const planAvail = Number(d.estimated_available_gb || d.app_available_gb || 0);
    const pci = d.pci_bus_id ? ` · PCI ${d.pci_bus_id}` : '';
    const uuid = d.uuid ? ` · UUID ${String(d.uuid).slice(0, 18)}…` : '';
    const smiIdx = d.nvidia_smi_index !== undefined ? ` · nvidia-smi index ${d.nvidia_smi_index}` : '';
    return el('label', { class: 'gpu-pick-chip', title: `${d.name || d.id}: physical ${physical.toFixed(2)}GB${driverFree !== null ? ` · driver free ${driverFree.toFixed(2)}GB` : ''} · planning available ${planAvail.toFixed(2)}GB · torch-ready ${d.torch_ready !== false}${smiIdx}${pci}${uuid}. Note: Windows Task Manager GPU numbers can differ from CUDA/nvidia-smi ids.` }, [
      check,
      el('span', {}, d.id || `cuda:${idx}`),
      el('span', { class: 'muted tiny' }, `${physical.toFixed(1)}GB total${driverFree !== null ? ` · ${driverFree.toFixed(1)}GB driver-free` : ''}${d.pci_bus_id ? ` · ${d.pci_bus_id}` : ''}`)
    ]);
  })) : null;
  const plan = state.modelPlacementPlans?.[m.name];
  const panel = el('div', { class: 'model-placement-controls' }, [
    el('div', { class: 'muted tiny' }, 'Load placement controls: choose exact GPU ids, sharding, dtype/quantization, runtime, tensor parallel, and optional per-GPU memory caps before loading.'),
    gpuPicker,
    el('div', { class: 'row tight' }, [device, gpuIds, shard, dtype, quant, runtime, el('label', {}, ['TP', tensorParallel])]),
    maxMemory,
    el('div', { class: 'row tight' }, [
      el('button', { class: 'secondary small', onclick: async () => { try { state.modelPlacementPlans[m.name] = await api('/api/models/placement/plan', { method: 'POST', body: placementBodyForModel(m, prefs) }); render(); } catch (err) { toast(err.message, false); } } }, 'Check VRAM / Placement'),
      plan ? el('span', { class: `tiny ${plan.errors && plan.errors.length ? 'bad-text' : 'ok-text'}` }, planStatusText(plan)) : el('span', { class: 'muted tiny' }, 'No placement check run yet.')
    ])
  ]);
  return { node: panel, body: () => placementBodyForModel(m, prefs) };
}
function modelResourcePanel() {
  const resources = state.modelResource || {};
  const devices = resources.devices || [];
  const loaded = resources.loaded_models || [];
  const loading = resources.loading_reservations || resources.pending_models || [];
  return el('div', { class: 'resource-panel' }, [
    devices.length ? el('div', { class: 'device-grid' }, devices.map(d => el('div', { class: 'device-card' }, [
      el('strong', {}, d.id || `cuda:${d.index}`),
      el('span', { class: 'muted tiny' }, `${d.name || ''}${d.nvidia_smi_index !== undefined ? ` · nvidia-smi ${d.nvidia_smi_index}` : ''}${d.pci_bus_id ? ` · PCI ${d.pci_bus_id}` : ''}`),
      d.uuid ? el('span', { class: 'muted tiny', title: d.uuid }, `UUID ${String(d.uuid).slice(0, 24)}…`) : null,
      el('span', { class: 'tiny' }, `physical total ${Number(d.physical_total_memory_gb || d.total_memory_gb || 0).toFixed(2)}GB · planning budget ${Number(d.usable_memory_gb || 0).toFixed(2)}GB`),
      el('span', { class: 'tiny' }, `app reserved ${Number(d.app_reserved_gb || d.tracked_loaded_gb || 0).toFixed(2)}GB · planning available ${Number(d.estimated_available_gb || d.tracked_available_gb || 0).toFixed(2)}GB`),
      d.app_available_gb !== undefined ? el('span', { class: 'muted tiny' }, `app-budget available ${Number(d.app_available_gb || 0).toFixed(2)}GB · basis ${d.availability_basis || 'unknown'}`) : null,
      d.free_memory_gb !== undefined && d.free_memory_gb !== null ? el('span', { class: d.driver_free_memory_warning ? 'bad tiny' : 'muted tiny' }, `driver free ${Number(d.free_memory_gb || 0).toFixed(2)}GB${d.driver_free_memory_warning ? ' (driver-reported free is lower than app reservation budget)' : ''}`) : null,
      (d.reservations || []).length ? el('div', { class: 'tiny' }, (d.reservations || []).map(r => `${r.model_name}:${r.reserved_gb}GB`).join(' · ')) : null
    ].filter(Boolean)))) : el('p', { class: 'muted' }, 'No CUDA GPUs detected by the app. CPU/cloud model loads remain available.'),
    loaded.length ? el('div', { class: 'muted tiny' }, `Loaded: ${loaded.map(x => `${x.model_name || x.label || 'model'}${x.device ? ' on ' + x.device : ''}`).join(' · ')}`) : el('div', { class: 'muted tiny' }, 'No models are currently loaded in RAM/VRAM.'),
    loading.length ? el('div', { class: 'muted tiny' }, `Loading/reserved: ${loading.map(x => x.model_name || x.label).join(' · ')}`) : null,
    resources.cuda_visible_devices ? el('div', { class: 'muted tiny' }, `CUDA_VISIBLE_DEVICES=${resources.cuda_visible_devices}`) : null,
    el('div', { class: 'muted tiny' }, 'GPU id note: cuda:N follows PyTorch/nvidia-smi CUDA ordering. Windows Task Manager can show a different GPU number for the same physical card; use PCI bus/UUID to verify identity.'),
    (resources.warnings || []).length ? el('div', { class: 'muted tiny' }, `Warnings: ${(resources.warnings || []).join(' ')}`) : null
  ].filter(Boolean));
}
function modelRuntimeControls() {
  const device = el('input', { value: (state.settings.preferred_devices || ['auto'])[0] || 'auto', placeholder: 'auto, cpu, cuda:0' });
  const gpuIds = el('input', { value: (state.settings.default_model_device_ids || [0]).join(','), placeholder: 'GPU ids: 0,1,2' });
  const shard = el('select', {}, ['none', 'auto', 'balanced', 'balanced_low_0', 'sequential', 'custom'].map(x => el('option', { value: x }, x))); shard.value = state.settings.default_model_sharding ? 'auto' : settingValueOr('default_model_sharding_strategy', 'none');
  const dtype = el('select', {}, ['auto', 'float16', 'bfloat16', 'float32'].map(x => el('option', { value: x }, x))); dtype.value = settingValueOr('default_model_dtype', 'auto');
  const quant = el('select', {}, ['none', '8bit', '4bit'].map(x => el('option', { value: x }, x))); quant.value = settingValueOr('default_model_quantization', 'none');
  const runtime = el('select', {}, ['transformers', 'vllm', 'sglang', 'llama.cpp', 'cloud', 'auto'].map(x => el('option', { value: x }, x))); runtime.value = settingValueOr('default_model_runtime_engine', 'transformers');
  const tensorParallel = el('input', { type: 'number', min: '1', max: '16', value: state.settings.default_tensor_parallel_size || 1, title: 'Tensor parallel size for server runtimes that support it.' });
  const maxMemory = el('textarea', { rows: 2, placeholder: 'Optional max memory, one per line: 0=23GiB\n1=23GiB' });
  const parallel = el('input', { type: 'number', min: '1', max: '64', value: '1', title: 'Parallel prediction workers. Use 1 for large GPU models unless you know the adapter is thread-safe.' });
  return { device, gpuIds, shard, dtype, quant, runtime, tensorParallel, maxMemory, parallel };
}
function downloadControls() {
  const categories = el('input', { placeholder: 'categories/tags: character, artist, style', style: 'min-width:280px' });
  const allCategories = el('input', { type: 'checkbox' });
  const downloadAllPosts = el('input', { type: 'checkbox', checked: state.settings.downloader_download_all_posts_default !== false });
  const dedupe = el('input', { type: 'checkbox', checked: state.settings.downloader_dedupe_across_presets !== false });
  const membershipIndex = el('input', { type: 'checkbox', checked: state.settings.downloader_store_membership_index !== false });
  const allowDuplicateFolders = el('input', { type: 'checkbox', checked: Boolean(state.settings.downloader_allow_duplicate_category_files) });
  const mode = el('select', {}, ['preset', 'tag_category', 'folder'].map(x => el('option', { value: x }, x)));
  const from = el('input', { type: 'date' });
  const to = el('input', { type: 'date' });
  const order = el('select', {}, [el('option', { value: 'newest_to_oldest' }, 'Newest → Oldest'), el('option', { value: 'oldest_to_newest' }, 'Oldest → Newest')]);
  order.value = state.settings.download_default_sort_order || 'newest_to_oldest';
  const workers = el('input', { type: 'number', min: '1', max: '32', value: state.settings.downloader_parallel_workers || state.settings.download_max_concurrent_items || 4 });
  const parallelPresets = el('input', { type: 'checkbox', checked: Boolean(state.settings.downloader_parallel_presets) });
  const perCat = el('input', { type: 'number', min: '1', value: state.settings.downloader_category_limit || 100, placeholder: 'category tag limit' });
  const perTag = el('input', { type: 'number', min: '1', value: state.settings.downloader_per_tag_limit || 10, placeholder: 'items per tag' });
  const apiDelay = el('input', { type: 'number', min: '0', step: '0.1', value: state.settings.downloader_api_delay_seconds ?? 7, title: 'Delay after API page requests' });
  const fileDelay = el('input', { type: 'number', min: '0', step: '0.1', value: state.settings.downloader_file_delay_seconds ?? 7, title: 'Optional delay after each file download' });
  const timeout = el('input', { type: 'number', min: '5', value: state.settings.downloader_request_timeout_seconds || 60, title: 'HTTP timeout in seconds' });
  const retries = el('input', { type: 'number', min: '0', value: state.settings.downloader_max_retries ?? 3, title: 'Retries per request' });
  const backoff = el('input', { type: 'number', min: '0', step: '0.5', value: state.settings.downloader_retry_backoff_seconds ?? 2.0, title: 'Retry backoff seconds' });
  const maxPages = el('input', { type: 'number', min: '0', value: state.settings.downloader_max_pages || 0, title: '0 = no explicit page cap; recommended safety cap in Download All Posts mode' });
  const startPage = el('input', { type: 'number', min: '0', value: state.settings.downloader_start_page || '', title: 'Optional start page / pid' });
  const logicCtl = tagAutocompleteControl({ placeholder: 'Optional Boolean logic query: wolf AND (solo OR duo) AND NOT sketch. Type a tag fragment here for dictionary suggestions.', multiline: true, tokenMode: 'logic' });
  logicCtl.input.rows = 3;
  logicCtl.input.style.width = '100%';
  const logic = logicCtl.input;
  const logicWrap = logicCtl.wrap;
  const logicMode = el('select', {}, [el('option', { value: 'boolean_expand' }, 'Boolean expand: OR becomes multiple deduped queries'), el('option', { value: 'raw_append' }, 'Raw append: send expression to source tags parameter')]);
  const logicMax = el('input', { type: 'number', min: '1', max: '512', value: state.settings.downloader_logic_max_clauses || 64, title: 'Safety cap for OR expansion clauses.' });
  const ratingSafe = el('input', { type: 'checkbox', checked: true });
  const ratingQuestionable = el('input', { type: 'checkbox', checked: true });
  const ratingExplicit = el('input', { type: 'checkbox', checked: true });
  const allowAnimated = el('input', { type: 'checkbox', checked: true });
  const allowVideo = el('input', { type: 'checkbox', checked: true });
  const allow3d = el('input', { type: 'checkbox', checked: true });
  const allowBlender = el('input', { type: 'checkbox', checked: true });
  const allowRender = el('input', { type: 'checkbox', checked: true });
  const allowImages = el('input', { type: 'checkbox', checked: true });
  const allowAudio = el('input', { type: 'checkbox', checked: true });
  const allowOtherMedia = el('input', { type: 'checkbox', checked: true });
  const applySourceBlacklists = el('input', { type: 'checkbox', checked: false, title: 'Disabled by default. Enable only when you intentionally want a source/account blacklist to constrain results.' });
  const estimateTotal = el('input', { type: 'checkbox', checked: true, title: 'Fetch metadata pages first to estimate total matching posts before downloading media. For very large searches, set Max pages or turn this off.' });
  const filenameMode = el('select', {}, [
    el('option', { value: 'hash_original' }, 'Hash + original filename'),
    el('option', { value: 'post_id' }, 'Post ID only'),
    el('option', { value: 'post_id_original' }, 'Post ID + original filename'),
    el('option', { value: 'original' }, 'Original filename only')
  ]);
  filenameMode.value = state.settings.downloader_filename_mode || 'hash_original';
  const metadataJson = el('input', { type: 'checkbox', checked: state.settings.downloader_write_metadata_json_sidecar !== false, title: 'Write per-file .download.json metadata next to downloaded media.' });
  const tagTxt = el('input', { type: 'checkbox', checked: state.settings.downloader_write_tag_txt_sidecar !== false, title: 'Write per-file .txt tag sidecars next to downloaded media.' });
  return { categories, allCategories, downloadAllPosts, dedupe, membershipIndex, allowDuplicateFolders, mode, from, to, order, workers, parallelPresets, perCat, perTag, apiDelay, fileDelay, timeout, retries, backoff, maxPages, startPage, logic, logicWrap, logicMode, logicMax, ratingSafe, ratingQuestionable, ratingExplicit, allowAnimated, allowVideo, allow3d, allowBlender, allowRender, allowImages, allowAudio, allowOtherMedia, applySourceBlacklists, estimateTotal, filenameMode, metadataJson, tagTxt };
}
function buildDownloadPayload(ctrl) {
  return {
    download_all_categories: ctrl.allCategories.checked,
    download_all_posts: ctrl.downloadAllPosts.checked,
    dedupe_across_presets: ctrl.dedupe.checked,
    store_membership_index: ctrl.membershipIndex.checked,
    allow_duplicate_category_files: ctrl.allowDuplicateFolders.checked,
    group_by_tag: ctrl.allowDuplicateFolders.checked,
    categories: parseTagString(ctrl.categories.value),
    category_mode: ctrl.mode.value,
    date_from: ctrl.from.value || null,
    date_to: ctrl.to.value || null,
    sort_order: ctrl.order.value,
    max_concurrent_downloads: Number(ctrl.workers.value || 1),
    parallel_workers: Number(ctrl.workers.value || 1),
    parallel_presets: ctrl.parallelPresets.checked,
    per_category_limit: Number(ctrl.perCat.value || 0) || null,
    category_limit: Number(ctrl.perCat.value || 100),
    per_tag_limit: Number(ctrl.perTag.value || 10),
    api_delay_seconds: Number(ctrl.apiDelay.value || 0),
    file_delay_seconds: Number(ctrl.fileDelay.value || 0),
    request_timeout_seconds: Number(ctrl.timeout.value || 60),
    max_retries: Number(ctrl.retries.value || 0),
    retry_backoff_seconds: Number(ctrl.backoff.value || 0),
    max_pages: Number(ctrl.maxPages.value || 0) || null,
    start_page: ctrl.startPage.value === '' ? null : Number(ctrl.startPage.value),
    logic_query: ctrl.logic.value.trim(),
    logic_mode: ctrl.logicMode.value,
    logic_max_clauses: Number(ctrl.logicMax.value || 64),
    rating_filter: [['s', ctrl.ratingSafe], ['q', ctrl.ratingQuestionable], ['e', ctrl.ratingExplicit]].filter(([_, box]) => box.checked).map(([code]) => code).length === 3 ? [] : [['s', ctrl.ratingSafe], ['q', ctrl.ratingQuestionable], ['e', ctrl.ratingExplicit]].filter(([_, box]) => box.checked).map(([code]) => code),
    allow_animated: ctrl.allowAnimated.checked,
    allow_video: ctrl.allowVideo.checked,
    allow_3d: ctrl.allow3d.checked,
    allow_blender: ctrl.allowBlender.checked,
    allow_render: ctrl.allowRender.checked,
    allow_images: ctrl.allowImages.checked,
    allow_audio: ctrl.allowAudio.checked,
    allow_other_media: ctrl.allowOtherMedia.checked,
    apply_source_blacklists: ctrl.applySourceBlacklists.checked,
    estimate_total_before_download: ctrl.estimateTotal.checked,
    filename_mode: ctrl.filenameMode.value,
    write_metadata_json_sidecar: ctrl.metadataJson.checked,
    write_tag_txt_sidecar: ctrl.tagTxt.checked,
    tag_profile: state.tagProfile,
  };
}

function orchestrationView() {
  const searchDataset = el('select', {}, datasetOptions());
  const queryDataset = el('select', {}, datasetOptions());
  const trainDataset = el('select', {}, datasetOptions());
  const model = el('select', {}, modelOptions());
  rememberSelect('orchestrationModelSelection', model, state.assistantConfig?.orchestrator_model_name || state.settings.orchestrator_model_name || state.settings.assistant_model_name || '', false);
  const kind = el('select', {}, ['tag', 'classify', 'caption', 'vlm_check', 'llm_review', 'tag_select'].map(x => el('option', { value: x }, x)));
  const policy = el('select', {}, ['auto', 'cpu', 'single_gpu', 'multi_gpu', 'custom'].map(x => el('option', { value: x }, x)));
  const devices = el('input', { placeholder: 'devices: auto or cuda:0,cuda:1', value: (state.settings.preferred_devices || ['auto']).join(',') });
  const threshold = el('input', { type: 'number', step: '0.05', min: '0', max: '1', value: state.settings.classifier_threshold || 0.35 });
  const dry = el('input', { type: 'checkbox', checked: true });
  const applyTags = el('input', { type: 'checkbox' });
  const applyCaps = el('input', { type: 'checkbox' });
  const goal = el('textarea', { placeholder: 'Goal / instructions for this run' }, 'Check selected images for matching tags/categories and suggest cleanup.');
  const prompt = el('textarea', { placeholder: 'Step prompt or tag-selection criteria' }, 'select unknown tags');
  const template = el('select', {}, [el('option', { value: '' }, 'No template / manual'), ...state.orchestrationTemplates.map(t => el('option', { value: t.key }, t.label))]);
  return el('div', { class: 'grid' }, [
    card('Agentic Orchestration Run', [
      el('p', { class: 'muted' }, 'Create an auditable multi-step job. Dry-run is enabled by default.'),
      el('div', { class: 'row' }, [template, tagProfileSelect(), searchDataset, kind, model]),
      inlineOrchestratorControls(model, 'orchestration tab'),
      el('div', { class: 'row' }, [policy, devices, threshold, el('label', {}, [dry, ' Dry-run']), el('label', {}, [applyTags, ' Apply tags']), el('label', {}, [applyCaps, ' Apply captions'])]),
      goal, prompt,
      el('button', { class: 'primary', onclick: async () => {
        try {
          let body = null; const chosen = state.orchestrationTemplates.find(t => t.key === template.value);
          if (chosen) { body = JSON.parse(JSON.stringify(chosen.request)); body.media_ids = [...state.selected]; body.dataset_id = searchDataset.value ? Number(searchDataset.value) : body.dataset_id; body.profile_key = state.tagProfile; body.dry_run = dry.checked; body.apply_tags = applyTags.checked; body.apply_captions = applyCaps.checked; body.device_policy = policy.value; body.devices = devices.value.split(',').map(x => x.trim()).filter(Boolean); }
          else { body = { name: 'Manual orchestration run', goal: goal.value, dataset_id: searchDataset.value ? Number(searchDataset.value) : null, media_ids: [...state.selected], profile_key: state.tagProfile, device_policy: policy.value, devices: devices.value.split(',').map(x => x.trim()).filter(Boolean), dry_run: dry.checked, apply_tags: applyTags.checked, apply_captions: applyCaps.checked, steps: [{ kind: kind.value, model_name: model.value, task: kind.value, prompt: prompt.value, threshold: Number(threshold.value || 0.35), apply: applyTags.checked || applyCaps.checked, options: { temperature: state.settings.model_temperature, max_new_tokens: state.settings.model_max_new_tokens } }] }; }
          const r = await api('/api/orchestration/run', { method: 'POST', body }); toast(`Orchestration job ${r.job_id} queued`); setTab('Jobs');
        } catch (err) { toast(err.message, false); }
      } }, 'Run Orchestration')
    ]),
    card('Templates', [el('pre', { class: 'log' }, JSON.stringify(state.orchestrationTemplates, null, 2))])
  ]);
}


function customModelCatalogCard() {
  const form = state.customModelForm || (state.customModelForm = {});
  const set = (key, value) => { form[key] = value; };
  const name = el('input', { value: form.name || '', placeholder: 'unique name, e.g. my-vlm-13b', oninput: e => set('name', e.target.value), 'data-form-key': 'custom-model-name' });
  const label = el('input', { value: form.label || '', placeholder: 'display label', oninput: e => set('label', e.target.value), 'data-form-key': 'custom-model-label' });
  const category = el('select', { onchange: e => set('category', e.target.value), 'data-form-key': 'custom-model-category' }, [
    el('option', { value: '' }, 'REQUIRED: choose model category'),
    ...['classifier','tagger','rating','captioner','llm','vlm','detection','segmentation','embedding','pose2d','pose3d','custom'].map(x => el('option', { value: x }, x))
  ]);
  category.value = form.category || '';
  const provider = el('select', { onchange: e => set('provider', e.target.value), 'data-form-key': 'custom-model-provider' }, ['huggingface','local','ultralytics','direct','optional','openai','openrouter','anthropic'].map(x => el('option', { value: x }, x)));
  provider.value = form.provider || 'huggingface';
  const repo = el('input', { value: form.repo_id || '', placeholder: 'HF repo / API model / yolo*.pt', oninput: e => set('repo_id', e.target.value), 'data-form-key': 'custom-model-repo' });
  const localPath = el('input', { value: form.local_path || '', placeholder: 'optional local model path/folder', oninput: e => set('local_path', e.target.value), 'data-form-key': 'custom-model-local-path', style: 'min-width:360px' });
  const desc = el('textarea', { rows: 2, placeholder: 'description / notes', oninput: e => set('description', e.target.value), 'data-form-key': 'custom-model-description' }, form.description || '');
  const caps = el('input', { value: form.capabilities || '', placeholder: 'optional capabilities: tag, classify, vlm', oninput: e => set('capabilities', e.target.value), 'data-form-key': 'custom-model-caps', style: 'min-width:320px' });
  const size = el('input', { type: 'number', step: '0.01', min: '0', value: form.size_gb || '', placeholder: 'size GB', oninput: e => set('size_gb', e.target.value), 'data-form-key': 'custom-model-size' });
  const vram = el('input', { type: 'number', step: '0.1', min: '0', value: form.vram_gb || '', placeholder: 'VRAM GB', oninput: e => set('vram_gb', e.target.value), 'data-form-key': 'custom-model-vram' });
  const precision = el('input', { value: form.precision || 'checkpoint-defined', placeholder: 'precision', oninput: e => set('precision', e.target.value), 'data-form-key': 'custom-model-precision' });
  const backend = el('input', { value: form.recommended_backend || 'auto', placeholder: 'backend', oninput: e => set('recommended_backend', e.target.value), 'data-form-key': 'custom-model-backend' });
  const modality = el('input', { value: form.modality || 'image/text', placeholder: 'modality', oninput: e => set('modality', e.target.value), 'data-form-key': 'custom-model-modality' });
  return card('Add Custom Model to Catalog', [
    el('p', { class: 'muted' }, 'Custom models require a category. User-added models are highlighted with a distinct custom color scheme and sorted to the top of every model menu/list.'),
    el('div', { class: 'row' }, [category, provider, name, label]),
    el('div', { class: 'row' }, [repo, localPath, el('button', { class: 'secondary', onclick: async () => { const chosen = await pickFilePath(localPath, 'Select custom model file/folder'); if (chosen) { localPath.value = chosen; set('local_path', chosen); } } }, 'Browse...')]),
    el('div', { class: 'row' }, [caps, size, vram, precision, backend, modality]),
    desc,
    el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: async () => {
        try {
          if (!category.value) throw new Error('Choose the custom model category first.');
          const payload = {
            name: name.value.trim() || label.value.trim() || repo.value.trim() || localPath.value.trim(),
            label: label.value.trim() || name.value.trim() || repo.value.trim() || localPath.value.trim(),
            category: category.value,
            provider: provider.value,
            repo_id: provider.value === 'direct' ? null : (repo.value.trim() || null),
            direct_url: provider.value === 'direct' ? (repo.value.trim() || null) : null,
            local_path: localPath.value.trim() || null,
            local_source_path: localPath.value.trim() || null,
            description: desc.value.trim(),
            capabilities: parseTagString(caps.value),
            size_gb: size.value === '' ? null : Number(size.value),
            vram_gb: vram.value === '' ? null : Number(vram.value),
            precision: precision.value.trim() || 'checkpoint-defined',
            modality: modality.value.trim() || 'image/text',
            recommended_backend: backend.value.trim() || 'auto'
          };
          const r = await api('/api/models/custom', { method: 'POST', body: payload });
          state.models = r.models || await api('/api/models');
          state.customModelForm = { name: '', label: '', category: '', provider: 'huggingface', repo_id: '', local_path: '', description: '', capabilities: '', size_gb: '', vram_gb: '', precision: 'checkpoint-defined', modality: 'image/text', recommended_backend: 'auto' };
          await refreshModelStatuses();
          toast(`Custom model added: ${r.model?.label || r.model?.name}`);
          render(true, true);
        } catch (err) { toast(err.message, false); }
      } }, 'Add / Update Custom Model'),
      el('button', { class: 'secondary', onclick: () => { state.customModelForm = { name: '', label: '', category: '', provider: 'huggingface', repo_id: '', local_path: '', description: '', capabilities: '', size_gb: '', vram_gb: '', precision: 'checkpoint-defined', modality: 'image/text', recommended_backend: 'auto' }; render(true, true); } }, 'Clear')
    ])
  ]);
}

const CUSTOM_MODEL_CATEGORIES = ['llm','vlm','classifier','tagger','rating','captioner','embedding','detection','segmentation','pose2d','pose3d','upscaler','external_image_tool','custom'];
function customModelEntryCard() {
  const label = el('input', { placeholder: 'Custom model label/name', style: 'min-width:240px' });
  const category = el('select', {}, [el('option', { value: '' }, 'Required model category'), ...CUSTOM_MODEL_CATEGORIES.map(x => el('option', { value: x }, x))]);
  const sourceType = el('select', {}, [
    el('option', { value: 'huggingface' }, 'Hugging Face repo'),
    el('option', { value: 'local_path' }, 'Local path'),
    el('option', { value: 'direct_url' }, 'Direct checkpoint URL')
  ]);
  const source = el('input', { placeholder: 'repo id, local folder/file, or direct URL', style: 'min-width:360px' });
  const backend = el('input', { placeholder: 'backend: transformers, ultralytics, sam2, custom', value: 'transformers' });
  const vram = el('input', { type: 'number', step: '0.1', min: '0', placeholder: 'VRAM GB' });
  const size = el('input', { type: 'number', step: '0.1', min: '0', placeholder: 'Size GB' });
  const shards = el('input', { type: 'checkbox' });
  const desc = el('textarea', { rows: 2, placeholder: 'Optional description / notes about this custom model' });
  const browse = el('button', { class: 'secondary', onclick: async () => { const picked = sourceType.value === 'local_path' ? await pickFilePath(source, 'Select local custom model file') : null; if (picked) source.value = picked; } }, 'Browse File...');
  const browseFolder = el('button', { class: 'secondary', onclick: async () => { const picked = sourceType.value === 'local_path' ? await pickFolder(source, 'Select local custom model folder') : null; if (picked) source.value = picked; } }, 'Browse Folder...');
  sourceType.addEventListener('change', () => { const off = sourceType.value !== 'local_path'; browse.disabled = off; browseFolder.disabled = off; });
  browse.disabled = true;
  browseFolder.disabled = true;
  return card('Add Custom Model to Registry', [
    el('p', { class: 'muted' }, 'Custom models require a category so they are routed, filtered, colored, and sorted correctly. User-added custom models are always pinned to the top of model menus and cards.'),
    el('div', { class: 'row' }, [label, category, sourceType, source, browse, browseFolder]),
    el('div', { class: 'row' }, [backend, vram, size, el('label', {}, [shards, ' Supports multi-GPU/sharding'])]),
    desc,
    el('button', { class: 'primary', onclick: async () => {
      try {
        const cat = category.value.trim();
        if (!cat) throw new Error('Choose the custom model category before saving.');
        if (!label.value.trim()) throw new Error('Enter a custom model label/name.');
        if (!source.value.trim()) throw new Error('Enter a Hugging Face repo id, direct URL, or local path.');
        const body = {
          label: label.value.trim(),
          category: cat,
          description: desc.value.trim() || null,
          recommended_backend: backend.value.trim() || null,
          vram_gb: vram.value === '' ? null : Number(vram.value),
          size_gb: size.value === '' ? null : Number(size.value),
          supports_sharding: shards.checked,
        };
        if (sourceType.value === 'local_path') body.local_source_path = source.value.trim();
        else if (sourceType.value === 'direct_url') body.direct_url = source.value.trim();
        else body.repo_id = source.value.trim();
        const result = await api('/api/models/custom', { method: 'POST', body });
        await refreshAll();
        state.modelKindFilter = '';
        state.modelRunSelection = result.model?.name || state.modelRunSelection;
        toast(`Custom model saved: ${result.model?.label || label.value}`);
        render(true, true);
      } catch (err) { toast(err.message, false); }
    } }, 'Save Custom Model')
  ]);
}

function externalModelRootsCard() {
  const rootsText = el('textarea', {
    rows: 4,
    value: (state.settings.external_model_roots || []).join('\n'),
    placeholder: 'Optional external model roots, one per line. Examples:\nD:\\AI_Models\\DataCurationToolModels\nE:\\SharedModels\\hf\nF:\\Checkpoints',
    style: 'width:100%'
  });
  const parseRoots = () => String(rootsText.value || '').split(/\r?\n|;/).map(x => x.trim()).filter(Boolean);
  return card('External Model Store / Symlink Support', [
    el('p', { class: 'muted' }, 'Use this when model weights live on a larger drive. You can either point the app at external model roots, or use Install Migration in Symlink mode to create links into this install without copying/moving the model bytes.'),
    rootsText,
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => {
        try {
          const picked = await api('/api/system/pick-folder', { method: 'POST', body: { title: 'Select external model root or provider folder', initial_dir: '' } });
          if (picked?.path) {
            const roots = parseRoots();
            if (!roots.includes(picked.path)) roots.push(picked.path);
            rootsText.value = roots.join('\n');
          }
        } catch (err) { toast(err.message, false); }
      } }, 'Add External Model Folder'),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const result = await api('/api/models/external-roots', { method: 'PUT', body: { roots: parseRoots() } });
          state.settings.external_model_roots = result.roots || [];
          await refreshAll();
          toast(`External model roots saved; reconciled ${result.reconciliation?.count || 0} model(s).`);
          render(true, true);
        } catch (err) { toast(err.message, false); }
      } }, 'Save Roots + Rescan'),
      el('button', { class: 'secondary', onclick: async () => {
        try { const r = await api('/api/models/rescan', { method: 'POST', body: {} }); await refreshAll(); toast(`Model rescan complete: ${r.count || 0} model(s) reconciled.`); render(true, true); } catch (err) { toast(err.message, false); }
      } }, 'Rescan Models')
    ]),
    el('p', { class: 'muted tiny' }, `Current in-install model cache: ${state.settings.model_cache_dir || 'models/hf'}. Symlink targets are shown on model cards when detected.`)
  ]);
}


function cloudModelRuntimeDefaultsCard() {
  const defaults = state.settings.cloud_model_runtime_defaults || {};
  const jsonText = el('textarea', {
    rows: 12,
    style: 'width:100%',
    value: JSON.stringify(defaults, null, 2),
    placeholder: '{\n  "openrouter": {\n    "enabled": true,\n    "token_profile": "default",\n    "model_id": "deepseek/deepseek-v4-pro",\n    "context_shrinker_model": "deepseek/deepseek-v4-flash",\n    "provider_route": {"allow_fallbacks": true},\n    "transforms": ["middle-out"]\n  }\n}'
  });
  return card('Cloud Model Provider Defaults / Context Shrinking', [
    el('p', { class: 'muted' }, 'Provider defaults are merged into cloud model runtime options. Use this to pin OpenRouter provider routing, model ids, token profiles/API-key profiles, and a separate context-shrinking model when prompts or local context are too large.'),
    jsonText,
    el('div', { class: 'row' }, [
      el('button', { class: 'primary', onclick: async () => { try { const parsed = JSON.parse(jsonText.value || '{}'); state.settings = await api('/api/settings', { method: 'PUT', body: { values: { cloud_model_runtime_defaults: parsed } } }); toast('Cloud model runtime defaults saved'); render(true, true); } catch (err) { toast('Cloud defaults JSON error: ' + err.message, false); } } }, 'Save Cloud Defaults'),
      el('button', { class: 'secondary', onclick: () => { jsonText.value = JSON.stringify({ openrouter: { enabled: true, token_profile: 'default', model_id: 'deepseek/deepseek-v4-pro', context_shrinker_model: 'deepseek/deepseek-v4-flash', context_shrink_policy: 'auto_middle_out', max_input_tokens: 250000, max_output_tokens: 4096, provider_route: { allow_fallbacks: true, order: [] }, transforms: ['middle-out'] } }, null, 2); } }, 'OpenRouter DeepSeek V4 Pro Template')
    ]),
    el('p', { class: 'muted tiny' }, 'Secrets should stay in API token profiles or environment variables. The defaults here reference profile names and provider/model identifiers, not raw keys.')
  ]);
}

function modelsView() {
  const model = el('select', {}, modelOptions());
  const modelsLive = el('input', { type: 'checkbox', checked: state.modelsAutoRefresh !== false, onchange: e => { state.modelsAutoRefresh = e.target.checked; } });
  rememberSelect('modelRunSelection', model, '', true);
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value };
  const selectedBusy = () => modelBusy(selectedModel(), ['download', 'load']);
  const task = el('select', {}, ['tag', 'caption', 'classify', 'rating', 'embed', 'segment', 'caption_split'].map(x => el('option', { value: x }, x)));
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.05', value: state.settings.classifier_threshold || 0.35 });
  const applyTags = el('input', { type: 'checkbox' });
  const applyCaption = el('input', { type: 'checkbox' });
  const rt = modelRuntimeControls();
  const kindFilter = el('select', { onchange: e => { state.modelKindFilter = e.target.value; render(); } }, [
    el('option', { value: '' }, 'All model categories'),
    ...[...new Set(sortedModels(state.models).map(m => m.kind).filter(Boolean))].sort().map(k => el('option', { value: k }, k))
  ]);
  kindFilter.value = state.modelKindFilter || '';
  return el('div', { class: 'grid' }, [
    card('Model Operation Status / GPU Residency', [
      el('p', { class: 'muted' }, 'Circular indicators track downloads, memory load/unload, inference, and future training. The GPU residency panel shows detected CUDA devices, app-level VRAM reservations, loaded models, and loading reservations.'),
      aggregateLifecycleStrip(),
      modelResourcePanel()
    ]),
    externalModelRootsCard(),
    cloudModelRuntimeDefaultsCard(),
    card('Run Model on Selection', [
      el('p', { class: 'muted' }, 'Default behavior is no sharding: one model on one selected device, so other GPUs can run other jobs/models. Run is disabled while the selected model is still downloading or loading.'),
      el('div', { class: 'row' }, [model, task, threshold]),
      modelLifecycleStrip(selectedModel(), true),
      el('div', { class: 'row' }, [rt.device, rt.gpuIds, rt.shard, rt.dtype, rt.quant, rt.runtime, el('label', {}, ['TP size', rt.tensorParallel]), rt.parallel]),
      rt.maxMemory,
      el('div', { class: 'row' }, [
        el('label', {}, [applyTags, ' Apply tags']),
        el('label', {}, [applyCaption, ' Apply caption']),
        el('button', { class: 'primary', disabled: selectedBusy(), title: selectedBusy() ? 'Selected model is downloading or loading.' : '', onclick: async () => {
          try {
            if (selectedBusy()) throw new Error('Selected model is downloading or loading. Wait for the status circle to finish before running inference.');
            const body = {
              media_ids: [...state.selected],
              model_name: model.value,
              task: task.value,
              threshold: Number(threshold.value || 0.35),
              ...runtimeBodyFromControls(rt),
              parallel_workers: Number(rt.parallel.value || 1),
              apply_tags: applyTags.checked,
              apply_caption: applyCaption.checked,
              options: { tag_profile: state.tagProfile }
            };
            const r = await api('/api/models/run', { method: 'POST', body });
            state.lastModelRunJob = r.job_id;
            state.jobDetailId = r.job_id;
            await refreshAll();
            toast(`Model job ${r.job_id} queued`);
            await refreshCompletedModelJobById(r.job_id);
            render();
          } catch (err) { toast(err.message, false); }
        } }, 'Run')
      ])
    ]),
    customModelCatalogCard(),
    card('Download / Install Models', [
      el('p', { class: 'muted' }, 'Downloadable Hugging Face models are listed by category with approximate weight size, VRAM, modality, backend, and sharding metadata. Download uses the configured HF token and model cache directory. Load Into Memory is separate so compatibility/load failures show before inference.'),
      el('div', { class: 'row' }, [el('label', {}, [modelsLive, ' Live status refresh']), kindFilter, el('span', { class: 'badge' }, state.modelKindFilter ? `Showing ${state.modelKindFilter} models only` : 'Showing all categories'), modelDownloadModeControl(), el('span', { class: 'badge', title: 'This controls the parallel_downloads value sent to model download jobs.' }, `Download mode: ${modelDownloadModeLabel()}`), el('button', { class: 'secondary', onclick: async () => { const keep = state.modelKindFilter; await refreshAll(); state.modelKindFilter = keep; render(true, true); } }, 'Refresh Filtered Model List'), el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/models/unload', { method: 'POST', body: {} }); await refreshAll(); toast(r.job_id ? `Unload queued as job ${r.job_id}` : (r.message || 'No loaded models to unload.')); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Unload Loaded Models')]),
      el('p', { class: 'muted tiny' }, 'Use Serial queue when large downloads are fragile or you plan to pause/switch VPN/Wi-Fi. Use Parallel transfers only when you want the downloader to split bandwidth across multiple files.'),
      modelDownloadQueueSummaryPanel(),
      modelCatalog()
    ]),
    card('Model Runtime Contract Audit', [
      el('p', { class: 'muted' }, 'Offline audit that checks adapter method contracts, download-source metadata, and specialized parsers such as JTP-3 wide CSV stdout. It does not download or execute large model weights.'),
      el('button', { class: 'secondary', onclick: async () => { try { state.modelRuntimeAudit = await api('/api/models/runtime-audit'); toast(state.modelRuntimeAudit.ok ? 'Model runtime audit passed' : 'Model runtime audit found issues', state.modelRuntimeAudit.ok); render(); } catch (err) { toast(err.message, false); } } }, 'Run Runtime Audit'),
      el('pre', { class: 'log' }, state.modelRuntimeAudit ? JSON.stringify(state.modelRuntimeAudit, null, 2) : 'No audit run yet.')
    ]),
    card('Raw Model Registry', [modelsTable()])
  ]);
}


function activeModelDownloadSizeSummary() {
  const rows = (state.jobs || []).filter(j => String(j.type || '').startsWith('model_download') && ['queued','running','paused'].includes(String(j.status || '').toLowerCase()));
  let remaining = 0;
  let known = 0;
  rows.forEach(j => {
    const params = j.params || j.parameters || {};
    const est = params.size_estimate || {};
    const val = Number(params.estimated_remaining_gb ?? est.estimated_remaining_gb ?? est.estimated_total_gb ?? 0);
    if (Number.isFinite(val) && val > 0) { remaining += val; known += 1; }
  });
  return { count: rows.length, known, estimated_remaining_gb: Math.round(remaining * 1000) / 1000, rows };
}
function modelDownloadQueueSummaryPanel() {
  const s = activeModelDownloadSizeSummary();
  return el('div', { class: 'download-size-summary' }, [
    el('strong', {}, 'Model download queue size'),
    el('span', { class: 'badge' }, `${s.count} active/queued`),
    el('span', { class: 'badge', title: 'Approximate, based on catalog size metadata and existing local files. Dry-run size checks can refine this.' }, `${s.known ? '~' + s.estimated_remaining_gb.toFixed(2) + ' GB left' : 'unknown GB left'}`),
    el('span', { class: 'muted tiny' }, 'Use Dry-run Size Check for exact Hugging Face file totals when supported.')
  ]);
}

function modelCatalog() {
  const filtered = sortedModelsForModelsTab(state.models).filter(m => !state.modelKindFilter || m.kind === state.modelKindFilter);
  if (!filtered.length) return el('p', { class: 'muted' }, 'No models match the current category filter.');
  return el('div', { class: 'model-scroll' }, filtered.map(modelCard));
}
function modelCard(m) {
  const lifecycle = modelLifecycle(m);
  const isLoaded = Boolean(m.loaded || lifecycle.loaded);
  const status = isLoaded ? 'loaded in memory' : m.downloaded ? 'downloaded' : m.installed ? 'adapter ready' : m.optional ? 'optional deps/model needed' : 'built-in';
  const repo = m.repo_id || 'no external repo';
  const downloadActive = stageActive(m, 'download');
  const loadActive = stageActive(m, 'load');
  const inferenceActive = stageActive(m, 'inference');
  const cannotLoad = downloadActive || loadActive;
  const placementControls = modelLoadControls(m);
  const activeForCatalog = modelCatalogActive(m);
  const catInfo = modelCategoryDisplay(m);
  return el('div', { class: `model-card ${isUserCustomModel(m) ? 'user-custom-model' : ''} ${activeForCatalog && !isUserCustomModel(m) ? 'active-model-card' : ''}`, style: modelActiveHighlightStyle(m) }, [
    el('div', { class: 'model-main' }, [
      el('div', { class: 'model-title' }, m.label || m.name),
      el('div', { class: 'muted tiny' }, repo),
      el('div', { class: 'muted' }, m.description || ''),
      el('div', { class: 'chips open' }, [
        (activeForCatalog && !isUserCustomModel(m)) ? el('span', { class: 'chip active-model-chip', style: `border-color:${catInfo.color}; color:${catInfo.color};` }, `ACTIVE · ${catInfo.label}`) : null,
        isUserCustomModel(m) ? el('span', { class: 'chip custom-model-chip' }, `CUSTOM · ${m.custom_model_category || m.custom_category || m.kind || 'model'}`) : null,
        el('span', { class: 'chip' }, m.kind || 'model'),
        el('span', { class: 'chip' }, m.provider || 'provider'),
        modelHFAccessLabel(m) ? el('span', { class: `chip ${m.requires_hf_token ? 'hf-token-required-chip' : 'hf-token-recommended-chip'}`, title: modelHFAccessTitle(m) }, modelHFAccessLabel(m)) : null,
        el('span', { class: `chip ${m.downloaded ? 'downloaded-model-chip' : (m.download_supported ? 'missing-model-chip' : '')}` }, m.downloaded ? 'DOWNLOADED' : (m.download_supported ? 'NOT DOWNLOADED' : status)),
        modelDownloadIssues(m).length ? el('span', { class: 'chip repair-model-chip', title: modelDownloadIssues(m).join(' | ') }, 'INCOMPLETE/CORRUPT') : null,
        (!modelDownloadIssues(m).length && modelSupportWarnings(m).length) ? el('span', { class: 'chip support-warning-chip', title: modelSupportWarnings(m).join(' | ') }, 'support update available') : null,
        modelLoadedInstanceCount(m) ? el('span', { class: `chip ${(m.offloaded_to_cpu || (m.loaded_instances || []).some(x => x && x.offloaded_to_cpu)) ? 'cpu-offloaded-chip' : 'loaded-instance-chip'}` }, `${(m.offloaded_to_cpu || (m.loaded_instances || []).some(x => x && x.offloaded_to_cpu)) ? 'CPU OFFLOADED' : 'LOADED'} x${modelLoadedInstanceCount(m)}`) : null,
        m.status_summary && !m.downloaded && !modelLoadedInstanceCount(m) ? el('span', { class: 'chip' }, m.status_summary) : null,
        m.parameter_count ? el('span', { class: 'chip' }, m.parameter_count) : null,
        m.size_gb ? el('span', { class: 'chip' }, `~${m.size_gb} GB weights`) : null,
        m.vram_gb ? el('span', { class: 'chip' }, `~${m.vram_gb} GB VRAM`) : null,
        modelMemorySummary(m) ? el('span', { class: 'chip', title: modelMemoryTitle(m) }, modelMemorySummary(m)) : null,
        m.precision ? el('span', { class: 'chip' }, m.precision) : null,
        m.modality ? el('span', { class: 'chip' }, m.modality) : null,
        m.supports_sharding ? el('span', { class: 'chip' }, `shards ${m.min_gpus || 1}-${m.max_gpus || 'N'} GPU`) : null,
        m.cloud ? el('span', { class: 'chip' }, 'cloud/API') : null
      ].filter(Boolean)),
      modelLifecycleStrip(m, true),
      modelPlacementSummary(m),
      placementControls.node,
      el('div', { class: 'muted tiny' }, (m.capabilities || []).join(', ')),
      m.local_path ? el('div', { class: 'muted tiny path' }, m.local_path) : null,
      m.symlink_target ? el('div', { class: 'muted tiny path' }, `↳ symlink target: ${m.symlink_target}`) : null,
      m.memory_note ? el('div', { class: 'muted tiny' }, m.memory_note) : null,
      m.license_note ? el('div', { class: 'muted tiny' }, m.license_note) : null
    ]),
    el('div', { class: 'model-actions' }, [
      el('button', { class: 'secondary small', disabled: !m.download_supported || downloadActive || loadActive, title: downloadActive ? 'Download already running.' : '', onclick: () => queueModelDownload(m, true) }, 'Dry-run Size Check'),
      el('button', { class: 'primary small', disabled: !m.download_supported || downloadActive || loadActive, title: downloadActive ? 'Download already running.' : '', onclick: () => queueModelDownload(m, false) }, m.downloaded ? 'Queue Update' : 'Queue Download'),
      el('button', { class: 'primary small', disabled: cannotLoad || isLoaded, title: isLoaded ? 'Already loaded in memory. Use Unload before loading it again.' : (cannotLoad ? 'Wait for the active download/load/unload operation to finish.' : '') , onclick: () => queueModelLoad(m, placementControls) }, isLoaded ? 'Loaded' : 'Load Into Memory'),
      el('button', { class: 'secondary small', disabled: loadActive || inferenceActive, onclick: async () => { try { const r = await api('/api/models/offload-cpu', { method: 'POST', body: { model_name: m.name } }); await refreshAll(); toast(`Moved ${m.label || m.name} to CPU RAM where supported`); render(); } catch (err) { toast(err.message, false); } } }, 'Offload to CPU RAM'),
      el('button', { class: 'secondary small', disabled: loadActive || inferenceActive, onclick: async () => { try { const r = await api('/api/models/unload', { method: 'POST', body: { model_name: m.name } }); await refreshAll(); toast(r.job_id ? `Unload queued as job ${r.job_id}` : (r.message || `No loaded adapter for ${m.label || m.name}`)); render(); } catch (err) { toast(err.message, false); } } }, 'Unload'),
      isUserCustomModel(m) ? el('button', { class: 'danger small', disabled: isLoaded || loadActive || inferenceActive, onclick: async () => { try { await api(`/api/models/custom/${encodeURIComponent(m.name)}`, { method: 'DELETE' }); state.models = await api('/api/models'); toast(`Removed custom catalog row ${m.label || m.name}`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Remove Custom Row') : null
    ].filter(Boolean))
  ]);
}
// Compatibility audit marker: Model download'} queued as job ${r.job_id} using ${modelDownloadModeLabel()}.`);
    render();
async function queueModelDownload(m, dryRun = false) {
  try {
    if (!m.download_supported) throw new Error('This registry row is not downloadable yet.');
    if (stageActive(m, 'download')) throw new Error(`${m.label || m.name} is already downloading.`);
    const r = await api('/api/models/download', { method: 'POST', body: { model_name: m.name, dry_run: dryRun, parallel_downloads: modelDownloadWorkerCount() } });
    state.lastModelRunJob = r.job_id;
    state.jobDetailId = r.job_id;
    await refreshAll();
    const rem = r.size_estimate?.estimated_remaining_gb;
    toast(`${dryRun ? 'Download dry-run' : 'Model download'} queued as job ${r.job_id} using ${modelDownloadModeLabel()}${rem !== null && rem !== undefined ? ` · ~${Number(rem).toFixed(2)}GB remaining` : ''}.`);
    render();
  } catch (err) { toast(err.message, false); }
}
async function queueModelLoad(m, placementControls = null) {
  try {
    if (modelLoaded(m)) {
      await refreshAll();
      toast(`${m.label || m.name} is already loaded in memory; no duplicate load job was queued.`);
      render();
      return;
    }
    if (stageActive(m, 'download')) throw new Error(`${m.label || m.name} is still downloading. Wait for the download status circle to finish before loading.`);
    if (stageActive(m, 'load')) throw new Error(`${m.label || m.name} is already loading.`);
    const body = placementControls && typeof placementControls.body === 'function' ? placementControls.body() : defaultRuntimeBody({ model_name: m.name, options: { tag_profile: state.tagProfile } });
    body.model_name = m.name;
    body.options = { ...(body.options || {}), tag_profile: state.tagProfile };
    const plan = await api('/api/models/placement/plan', { method: 'POST', body });
    state.modelPlacementPlans[m.name] = plan;
    if (plan?.errors?.length || plan?.can_load === false) {
      render();
      throw new Error(plan.errors?.join(' ') || 'Selected GPU placement cannot load this model without exceeding the current VRAM budget.');
    }
    const r = await api('/api/models/load', { method: 'POST', body });
    if (r.job_id) {
      state.lastModelRunJob = r.job_id;
      state.jobDetailId = r.job_id;
    }
    await refreshAll();
    toast(r.job_id ? `Model load queued as job ${r.job_id}. Status circles and Jobs are refreshed without reloading the page.` : (r.message || `${m.label || m.name} is already loaded in memory.`));
    render();
  } catch (err) { toast(err.message, false); }
}

function modelsTable() {
  const rows = sortedModelsForModelsTab(state.models).filter(m => !state.modelKindFilter || m.kind === state.modelKindFilter);
  return el('div', { class: 'table-scroll' }, el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['Name', 'Kind', 'Provider', 'Repo/API', 'Size', 'VRAM', 'Backend', 'Shard', 'Downloaded', 'Capabilities'].map(h => el('th', {}, h)))),
    el('tbody', {}, rows.map(m => el('tr', { class: `${isUserCustomModel(m) ? 'user-custom-model-row' : ''}${modelCatalogActive(m) && !isUserCustomModel(m) ? ' active-model-row' : ''}`, style: modelActiveHighlightStyle(m) }, [
      el('td', {}, m.label || m.name), el('td', {}, m.kind), el('td', {}, m.provider), el('td', {}, m.repo_id || m.api_model_id || ''),
      el('td', {}, m.size_gb ? `~${m.size_gb} GB` : ''), el('td', {}, m.vram_gb ? `~${m.vram_gb} GB` : ''),
      el('td', {}, m.recommended_backend || ''), el('td', {}, m.supports_sharding ? `${m.min_gpus || 1}-${m.max_gpus || 'N'}` : 'no'),
      el('td', {}, [
        m.downloaded ? el('span', { class: 'chip downloaded-model-chip' }, 'downloaded') : (m.download_supported ? el('span', { class: 'chip missing-model-chip' }, 'not downloaded') : ''),
        modelLoadedInstanceCount(m) ? el('span', { class: 'chip loaded-instance-chip' }, `loaded x${modelLoadedInstanceCount(m)}`) : null,
        modelDownloadIssues(m).length ? el('span', { class: 'chip repair-model-chip', title: modelDownloadIssues(m).join(' | ') }, 'incomplete') : (!modelDownloadIssues(m).length && modelSupportWarnings(m).length ? el('span', { class: 'chip support-warning-chip', title: modelSupportWarnings(m).join(' | ') }, 'support') : null)
      ].filter(Boolean)), el('td', {}, (m.capabilities || []).join(', '))
    ])))
  ]));
}


function referenceFinderView() {
  const target = el('input', { placeholder: 'Target character / object name', value: state.referenceTarget || '', style: 'min-width:260px', oninput: e => { state.referenceTarget = e.target.value; } });
  const refs = el('textarea', { placeholder: 'Reference image paths, one per line', rows: '4', style: 'width:100%' });
  const folder = el('input', { placeholder: 'Optional folder if not using current dataset/selection', style: 'min-width:360px' });
  const dataset = el('select', {}, datasetOptions());
  const pipeline = el('select', {}, ['demo_colorhash', 'siglip2_embedding_only', 'owlv2_siglip2'].map(x => el('option', { value: x }, x)));
  const threshold = el('input', { type: 'number', min: '0', max: '1', step: '0.01', value: '0.55' });
  const recursive = el('input', { type: 'checkbox', checked: true });
  const saveAll = el('input', { type: 'checkbox' });
  const decision = el('select', {}, [el('option', { value: '' }, 'Any decision'), el('option', { value: 'match' }, 'match'), el('option', { value: 'reject' }, 'reject')]);
  const runId = el('input', { type: 'number', placeholder: 'run id', style: 'width:110px' });
  const queryDataset = el('select', {}, datasetOptions());
  const trainDataset = el('select', {}, datasetOptions());
  const query = el('textarea', { rows: '3', placeholder: '[tag:blue_hair] AND ([tag:dress] OR [tag:school_uniform])', style: 'width:100%' });
  const baseline = el('textarea', { rows: '2', placeholder: 'Optional baseline query', style: 'width:100%' });
  const queryList = el('textarea', { rows: '5', placeholder: 'One candidate query per line for batch evaluation/suggestions', style: 'width:100%' });
  const annMediaId = el('input', { type: 'number', value: state.activeMedia?.id || [...state.selected][0] || '', placeholder: 'media id' });
  const annLabel = el('input', { value: target.value || 'object', placeholder: 'label' });
  const annType = el('select', {}, ['bbox', 'polygon', 'bbox_mask', 'mask'].map(x => el('option', { value: x }, x)));
  const bbox = el('textarea', { rows: '2', placeholder: '{"x1":10,"y1":20,"x2":300,"y2":500} or {"x":10,"y":20,"w":290,"h":480}', style: 'width:100%' });
  const polygon = el('textarea', { rows: '2', placeholder: '[[100,50],[150,60],[175,120],[90,170]]', style: 'width:100%' });
  const trainName = el('input', { placeholder: 'training set name', style: 'min-width:220px' });
  const trainQuery = el('textarea', { rows: '2', placeholder: 'query for training set, blank = all in selected dataset', style: 'width:100%' });
  const trainSetId = el('input', { type: 'number', placeholder: 'training set id' });
  const yoloTask = el('select', {}, ['detection', 'segmentation'].map(x => el('option', { value: x }, x)));
  const output = el('input', { placeholder: 'Optional output folder', style: 'min-width:320px' });
  const outputBox = el('pre', { class: 'log' }, state.referenceOutput ? JSON.stringify(state.referenceOutput, null, 2) : '');
  const refreshStatus = async () => {
    state.referenceStatus = await api('/api/reference/status');
    state.referenceRuns = await api('/api/reference/runs').catch(() => []);
    render();
  };
  const loadResults = async () => {
    const p = new URLSearchParams();
    if (runId.value) p.set('run_id', runId.value);
    if (target.value) p.set('target_name', target.value);
    if (decision.value) p.set('decision', decision.value);
    p.set('limit', '200');
    state.referenceResults = await api(`/api/reference/results?${p.toString()}`);
    render();
  };
  return el('div', { class: 'grid' }, [
    card('Reference Finder: one/few-reference image search', [
      el('p', { class: 'muted' }, 'Use one or more reference images to find likely matching character/object images. The no-model ColorHash backend is available immediately; OWLv2/SigLIP2 rows are staged for optional model-backed runs.'),
      el('div', { class: 'row' }, [target, dataset, pipeline, el('label', {}, ['Threshold', threshold]), el('label', {}, [recursive, ' Recursive folder']), el('label', {}, [saveAll, ' Save annotated rejects too'])]),
      el('label', { class: 'label' }, ['Reference paths', refs]),
      el('div', { class: 'row' }, [folder, el('button', { class: 'secondary', onclick: async () => await pickFolder(folder, 'Select reference-search folder') }, 'Browse Folder...')]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: refreshStatus }, 'Refresh Reference Status'),
        el('button', { class: 'primary', onclick: async () => { try { const body = { target_name: target.value, reference_paths: refs.value.split(/\r?\n/).map(x => x.trim()).filter(Boolean), dataset_id: dataset.value ? Number(dataset.value) : null, media_ids: [...state.selected], folder: folder.value, recursive: recursive.checked, pipeline: pipeline.value, threshold: Number(threshold.value || 0.55), save_all_annotations: saveAll.checked }; const r = await api('/api/reference/run', { method: 'POST', body }); toast(`Reference search job ${r.job_id} queued`); setTab('Jobs'); } catch (err) { toast(err.message, false); } } }, 'Run Reference Search')
      ]),
      state.referenceStatus ? el('pre', { class: 'log' }, JSON.stringify(state.referenceStatus, null, 2)) : null
    ]),
    card('Results + verification memory', [
      el('div', { class: 'row' }, [runId, decision, el('button', { class: 'secondary', onclick: loadResults }, 'Load Results')]),
      referenceResultsTable()
    ]),
    card('BBCode / tag-query optimizer', [
      el('div', { class: 'row' }, [queryDataset]),
      el('p', { class: 'muted' }, 'Evaluate tag queries against verified correct/incorrect reference detections. Supports [tag:name], quoted tags, AND/OR/NOT, parentheses, and bare tags.'),
      el('label', { class: 'label' }, ['Query', query]),
      el('label', { class: 'label' }, ['Baseline query', baseline]),
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => { try { state.referenceOutput = await api('/api/reference/queries/evaluate', { method: 'POST', body: { target_name: target.value, query: query.value, baseline_query: baseline.value, dataset_id: queryDataset.value ? Number(queryDataset.value) : null } }); render(); } catch (err) { toast(err.message, false); } } }, 'Evaluate Query'),
        el('button', { class: 'secondary', onclick: async () => { try { state.referenceOutput = await api(`/api/reference/queries/suggest?target_name=${encodeURIComponent(target.value)}&dataset_id=${queryDataset.value || ''}`); render(); } catch (err) { toast(err.message, false); } } }, 'Suggest From Verified Positives')
      ]),
      el('label', { class: 'label' }, ['Batch candidate queries', queryList]),
      el('button', { class: 'secondary', onclick: async () => { try { state.referenceOutput = await api('/api/reference/queries/evaluate-many', { method: 'POST', body: { target_name: target.value, queries: queryList.value.split(/\r?\n/).map(x => x.trim()).filter(Boolean), baseline_query: baseline.value, dataset_id: queryDataset.value ? Number(queryDataset.value) : null } }); render(); } catch (err) { toast(err.message, false); } } }, 'Evaluate Candidate Queries')
    ]),
    card('Annotations: bbox / polygon / mask primitives', [
      el('p', { class: 'muted' }, 'Save manual labels for training exports. BBox and polygon masks can be rasterized to PNG masks.'),
      el('div', { class: 'row' }, [annMediaId, annLabel, annType]),
      el('label', { class: 'label' }, ['BBox JSON', bbox]),
      el('label', { class: 'label' }, ['Polygon JSON', polygon]),
      el('button', { class: 'primary', onclick: async () => { try { const body = { media_id: Number(annMediaId.value), label: annLabel.value, annotation_type: annType.value, target_name: target.value, bbox: bbox.value ? JSON.parse(bbox.value) : {}, polygon: polygon.value ? JSON.parse(polygon.value) : [] }; state.referenceOutput = await api('/api/reference/annotations', { method: 'POST', body }); toast('Annotation saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Annotation')
    ]),
    card('Training set + YOLO/caption exports', [
      el('div', { class: 'row' }, [trainName, trainDataset, el('label', {}, ['Train ratio', el('input', { id: 'trainRatioRef', type: 'number', value: '0.9', step: '0.05', min: '0.1', max: '0.99' })])]),
      el('label', { class: 'label' }, ['Training-set query', trainQuery]),
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => { try { const ratio = Number(document.querySelector('#trainRatioRef')?.value || 0.9); state.referenceOutput = await api('/api/reference/training-sets', { method: 'POST', body: { name: trainName.value || `set-${Date.now()}`, query: trainQuery.value, dataset_id: trainDataset.value ? Number(trainDataset.value) : null, train_ratio: ratio } }); render(); } catch (err) { toast(err.message, false); } } }, 'Create Training Set'),
        trainSetId, yoloTask, output,
        el('button', { class: 'secondary', onclick: async () => await pickFolder(output, 'Select export output folder') }, 'Browse Output...'),
        el('button', { class: 'primary', onclick: async () => { try { state.referenceOutput = await api('/api/reference/exports/yolo', { method: 'POST', body: { training_set_id: Number(trainSetId.value), output_dir: output.value || null, task: yoloTask.value } }); render(); } catch (err) { toast(err.message, false); } } }, 'Export YOLO'),
        el('button', { class: 'secondary', onclick: async () => { try { state.referenceOutput = await api('/api/reference/exports/captions', { method: 'POST', body: { training_set_id: Number(trainSetId.value), output_dir: output.value || null } }); render(); } catch (err) { toast(err.message, false); } } }, 'Export Captions JSONL')
      ])
    ]),
    card('Reference / annotation output', [outputBox])
  ]);
}

function referenceResultsTable() {
  const rows = state.referenceResults || [];
  if (!rows.length) return el('p', { class: 'muted' }, 'No results loaded yet.');
  return el('div', { class: 'table-scroll' }, el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['ID', 'Target', 'Score', 'Decision', 'Verified', 'Path', 'Actions'].map(h => el('th', {}, h)))),
    el('tbody', {}, rows.map(r => el('tr', {}, [
      el('td', {}, r.id), el('td', {}, r.target_name || ''), el('td', {}, Number(r.score_final || 0).toFixed(3)), el('td', {}, r.decision), el('td', {}, r.user_label || ''), el('td', { class: 'path' }, r.path || ''),
      el('td', {}, el('div', { class: 'row compact' }, ['correct', 'incorrect', 'uncertain'].map(label => el('button', { class: 'secondary small', onclick: async () => { try { await api('/api/reference/verify', { method: 'POST', body: { detection_id: r.id, label } }); toast(`Marked ${label}`); state.referenceResults = await api('/api/reference/results?limit=200'); render(); } catch (err) { toast(err.message, false); } } }, label))))
    ])))
  ]));
}

function sourceBrowserView() {
  const url = el('input', { value: 'about:blank', placeholder: 'URL to open', style: 'min-width:420px' });
  const privateMode = el('input', { type: 'checkbox', checked: true });
  const headless = el('input', { type: 'checkbox' });
  return el('div', { class: 'grid' }, [
    card('Firefox / geckodriver source browser', [
      el('p', { class: 'muted' }, 'Local Firefox private-mode launcher for source review and authorized dataset browsing. run.bat defaults to Firefox/geckodriver; this panel also installs, validates, and launches it manually.'),
      el('div', { class: 'row' }, [url, el('label', {}, [privateMode, ' Private mode']), el('label', {}, [headless, ' Headless'])]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { state.browserStatus = await api('/api/browser/status'); render(); } catch (err) { toast(err.message, false); } } }, 'Check Status'),
        el('button', { class: 'secondary', onclick: async () => { try { state.browserOutput = await api('/api/browser/geckodriver/install', { method: 'POST', body: { force: false } }); toast('geckodriver installed/verified'); state.browserStatus = await api('/api/browser/status'); render(); } catch (err) { toast(err.message, false); } } }, 'Install / Verify geckodriver'),
        el('button', { class: 'secondary', onclick: async () => { try { state.browserOutput = await api('/api/browser/visible-self-test', { method: 'POST', body: { url: url.value || 'about:blank', private: true, headless: false } }); toast('Visible Firefox/geckodriver self-test launched'); state.browserStatus = await api('/api/browser/status'); render(); } catch (err) { toast(err.message, false); } } }, 'Visible geckodriver Self-Test'),
        el('button', { class: 'primary', onclick: async () => { try { state.browserOutput = await api('/api/browser/launch', { method: 'POST', body: { url: url.value, private: privateMode.checked, headless: headless.checked } }); render(); } catch (err) { toast(err.message, false); } } }, 'Launch Firefox via geckodriver'),
        el('button', { class: 'secondary', onclick: async () => { try { state.browserOutput = await api('/api/browser/launch-direct', { method: 'POST', body: { url: url.value, private: privateMode.checked, headless: headless.checked } }); render(); } catch (err) { toast(err.message, false); } } }, 'Launch Direct Firefox Fallback'),
        el('button', { class: 'secondary', onclick: async () => { try { state.browserOutput = await api('/api/browser/stop', { method: 'POST', body: {} }); state.browserStatus = await api('/api/browser/status'); render(); } catch (err) { toast(err.message, false); } } }, 'Stop Browser')
      ]),
      el('pre', { class: 'log' }, JSON.stringify({ status: state.browserStatus, output: state.browserOutput }, null, 2))
    ])
  ]);
}

function externalAppsStatusTable() {
  const rows = state.externalApps?.tools || [];
  if (!rows.length) return el('p', { class: 'muted' }, 'Discovery has not run yet. The first Gallery launch also auto-discovers the selected application.');
  return el('div', { class: 'table-scroll' }, el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, ['Application','Status','Resolved path','Source'].map(h => el('th', {}, h)))),
    el('tbody', {}, rows.map(row => el('tr', {}, [
      el('td', {}, row.label || row.key),
      el('td', {}, el('span', { class: row.available ? 'badge ok' : 'badge bad' }, row.available ? 'available' : 'not found')),
      el('td', { class: 'path tiny' }, row.path || ''),
      el('td', { class: 'tiny' }, row.source || '')
    ])))
  ]));
}

function augmentView() {
  const output = el('input', { placeholder: 'Output folder', style: 'min-width:320px' });
  const includeOriginal = el('input', { type: 'checkbox', checked: true });
  const attach = el('input', { type: 'checkbox', checked: false });
  const flip = el('input', { type: 'checkbox' });
  const vflip = el('input', { type: 'checkbox' });
  const rotate = el('input', { type: 'number', value: '0', style: 'width:80px' });
  const brightness = el('input', { type: 'number', step: '0.05', value: '1.0', style: 'width:80px' });
  const contrast = el('input', { type: 'number', step: '0.05', value: '1.0', style: 'width:80px' });
  const saturation = el('input', { type: 'number', step: '0.05', value: '1.0', style: 'width:80px' });
  const sharpen = el('input', { type: 'checkbox' });
  const denoise = el('input', { type: 'checkbox' });
  const gray = el('input', { type: 'checkbox' });
  const cropSquare = el('input', { type: 'checkbox' });
  const padSquare = el('input', { type: 'checkbox' });
  const longSide = el('input', { type: 'number', min: '0', value: '0', style: 'width:90px' });
  const upscale = el('input', { type: 'number', min: '0', step: '0.25', value: '1', style: 'width:90px' });
  const format = el('select', {}, ['jpg','png','webp'].map(x => el('option', { value: x }, x)));
  const tool = el('select', {}, [...EXTERNAL_APP_OPTIONS, ['custom','Custom external tool']].map(([v,l]) => el('option', { value: v }, l)));
  tool.value = state.quickExternalTool || 'topaz_photo_ai';
  const exe = el('input', { placeholder: 'Auto-discovered path or browse to executable / ComfyUI launcher', style: 'min-width:480px' });
  const mode = el('select', {}, [el('option', { value: 'open' }, 'Interactive launch now'), el('option', { value: 'cli' }, 'Queue command-template processing')]);
  const command = el('input', { placeholder: 'CLI template: "{exe}" "{input}" "{output}"', value: '"{exe}" "{input}"', style: 'min-width:520px' });
  const wait = el('input', { type: 'checkbox' });
  const extAttach = el('input', { type: 'checkbox' });
  const copyInputs = el('input', { type: 'checkbox', checked: true });
  const deepScan = el('input', { type: 'checkbox' });
  const extOut = el('input', { placeholder: 'Optional handoff/output folder', style: 'min-width:360px' });
  function syncExternalFields() {
    const found = externalAppRow(tool.value);
    const configured = state.settings?.external_image_tools?.[tool.value] || {};
    exe.value = found?.path || configured.executable_path || (tool.value === 'krita' ? (state.settings?.krita_executable || '') : '');
    command.value = configured.command_template || command.value || '"{exe}" "{input}"';
    state.quickExternalTool = tool.value;
  }
  tool.addEventListener('change', syncExternalFields);
  syncExternalFields();
  return el('div', { class: 'grid' }, [
    card('Image Augmentation / Editing', [
      el('p', { class: 'muted' }, 'Non-destructive batch image edits for dataset prep. Outputs are written to a new folder and can optionally be attached back to the active dataset.'),
      el('div', { class: 'row' }, [output, el('button', { class: 'secondary', onclick: async () => await pickFolder(output, 'Select augmentation output folder') }, 'Browse Output...'), format, el('label', {}, [attach, ' Attach outputs to dataset'])]),
      el('div', { class: 'row' }, [el('label', {}, [includeOriginal, ' Include original']), el('label', {}, [flip, ' Horizontal flip']), el('label', {}, [vflip, ' Vertical flip']), el('label', {}, ['Rotate°', rotate]), el('label', {}, [cropSquare, ' Center crop square']), el('label', {}, [padSquare, ' Pad square'])]),
      el('div', { class: 'row' }, [el('label', {}, ['Brightness', brightness]), el('label', {}, ['Contrast', contrast]), el('label', {}, ['Saturation', saturation]), el('label', {}, [sharpen, ' Sharpen']), el('label', {}, [denoise, ' Denoise']), el('label', {}, [gray, ' Grayscale'])]),
      el('div', { class: 'row' }, [el('label', {}, ['Resize long side', longSide]), el('label', {}, ['Lanczos upscale factor', upscale])]),
      el('button', { class: 'primary', onclick: async () => { try { const ops = { flip_horizontal: flip.checked, flip_vertical: vflip.checked, rotate: Number(rotate.value || 0), crop_square: cropSquare.checked, pad_square: padSquare.checked, brightness: Number(brightness.value || 1), contrast: Number(contrast.value || 1), saturation: Number(saturation.value || 1), sharpen: sharpen.checked, denoise: denoise.checked, grayscale: gray.checked }; if (Number(longSide.value || 0) > 0) ops.resize_long_side = Number(longSide.value); if (Number(upscale.value || 1) !== 1) ops.upscale_lanczos = Number(upscale.value); const r = await api('/api/augment/run', { method: 'POST', body: { media_ids: [...state.selected], output_dir: output.value || null, include_original: includeOriginal.checked, attach_to_dataset: attach.checked, output_format: format.value, operations: ops } }); toast(`Augment job ${r.job_id} queued`); setTab('Jobs'); } catch (err) { toast(err.message, false); } } }, 'Run Augment/Edit')
    ]),
    card('Installed Apps / Topaz / Krita / ComfyUI Handoff', [
      el('p', { class: 'muted' }, 'The Gallery quick action now launches immediately instead of only changing tabs. Discovery checks configured paths, the user home directory, Desktop/Documents/Downloads, project folders, Program Files, and common portable-app layouts. Selected images are copied to a timestamped handoff folder by default so originals stay untouched.'),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { await discoverExternalApps(deepScan.checked); syncExternalFields(); toast('External application discovery finished'); render(); } catch (err) { toast(err.message, false); } } }, 'Discover Home / Common Locations'),
        el('label', {}, [deepScan, ' deeper home scan']),
        el('span', { class: 'muted' }, `Selected: ${state.selected.size} image(s)`)
      ]),
      externalAppsStatusTable(),
      el('div', { class: 'row' }, [tool, mode, el('label', {}, [copyInputs, ' use safe handoff copies']), el('label', {}, [wait, ' wait for CLI completion']), el('label', {}, [extAttach, ' attach CLI output to dataset'])]),
      el('div', { class: 'row' }, [exe, el('button', { class: 'secondary', onclick: async () => { const chosen = await pickFilePath(exe, 'Select external application executable or launcher'); if (chosen) state.externalApps = null; } }, 'Browse Executable / Launcher...')]),
      command,
      el('div', { class: 'row' }, [extOut, el('button', { class: 'secondary', onclick: async () => await pickFolder(extOut, 'Select handoff/output folder') }, 'Browse Handoff Folder...')]),
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => { if (mode.value === 'cli') { try { const r = await api('/api/augment/external-tool', { method: 'POST', body: { media_ids: [...state.selected], tool_name: tool.value, mode: 'cli', executable_path: exe.value || null, command_template: command.value, output_dir: extOut.value || null, wait_for_completion: wait.checked, attach_to_dataset: extAttach.checked, copy_inputs: copyInputs.checked, auto_discover: true, save_discovered_path: true } }); toast(`External CLI job ${r.job_id} queued`); setTab('Jobs'); } catch (err) { toast(err.message, false); } } else { await launchExternalToolNow(tool.value, [...state.selected], { executable_path: exe.value || null, output_dir: extOut.value || null, copy_inputs: copyInputs.checked, deep_scan: deepScan.checked }); } } }, mode.value === 'cli' ? 'Queue CLI Processing' : 'Launch Selected Now'),
        state.externalAppOutput?.handoff_dir ? el('button', { class: 'secondary', onclick: async () => { try { await api('/api/system/open-path', { method: 'POST', body: { path: state.externalAppOutput.handoff_dir } }); } catch (err) { toast(err.message, false); } } }, 'Open Last Handoff Folder') : null
      ].filter(Boolean)),
      el('pre', { class: 'log' }, JSON.stringify(state.externalAppOutput || { message: 'No external application launch has run in this session.' }, null, 2))
    ]),
    exportCard()
  ]);
}

async function pickFilePath(targetInput, title = 'Select file') {
  try {
    const result = await api('/api/system/pick-file', { method: 'POST', body: { title, initial_dir: targetInput?.value || null } });
    if (!result.available) throw new Error(result.error || 'File picker is not available.');
    if (result.path && targetInput) targetInput.value = result.path;
    return result.path;
  } catch (err) { toast(err.message, false); return null; }
}

function downloadsView() {
  const source = el('select', { onchange: e => { if (state.tagProfiles.some(p => p.key === e.target.value)) state.tagProfile = e.target.value; render(); } }, state.downloadSources.map(s => el('option', { value: s.key }, s.label || s.key)));
  const preferredDirectSource = state.downloadSources.some(s => s.key === state.tagProfile) ? state.tagProfile : (state.downloadSources.some(s => s.key === 'e621') ? 'e621' : (state.downloadSources[0]?.key || 'generic-json'));
  source.value = preferredDirectSource;
  const directApiUrl = el('input', { placeholder: 'Required only when Source is Generic JSON/custom', style: 'min-width:320px' });
  const posCtl = tagAutocompleteControl({ placeholder: 'positive tags', multiline: true });
  const negCtl = tagAutocompleteControl({ placeholder: 'negative tags', multiline: true });
  const max = el('input', { type: 'number', value: '100', min: '1', max: '5000' });
  const directCtl = downloadControls();
  const presetCtl = downloadControls();
  const outDirect = el('input', { placeholder: 'Output folder', style: 'min-width:320px' });
  const authDirect = el('input', { type: 'checkbox' });
  const preset = el('select', { multiple: 'multiple', size: '8', style: 'min-width:320px' }, state.presets.map(p => el('option', { value: p.name }, p.name)));
  const out = el('input', { placeholder: 'Output folder', style: 'min-width:320px' });
  const auth = el('input', { type: 'checkbox' });
  const advancedControls = ctrl => [
    el('div', { class: 'row' }, [el('label', {}, [ctrl.downloadAllPosts, ' DOWNLOAD ALL POSTS until source is exhausted']), el('label', {}, [ctrl.allCategories, ' Download all tags in selected category/categories']), ctrl.categories, ctrl.mode]),
    el('div', { class: 'row' }, [el('label', {}, ['Category tag limit', ctrl.perCat]), el('label', {}, ['Items per expanded tag', ctrl.perTag]), el('label', {}, [ctrl.dedupe, ' Deduplicate across categories/presets']), el('label', {}, [ctrl.membershipIndex, ' Write membership index']), el('label', {}, [ctrl.allowDuplicateFolders, ' Legacy duplicate tag folders'])]),
    el('p', { class: 'muted tiny' }, 'Default behavior stores each media file once and writes _download_index/download_membership.json showing which categories/tags matched it. Only enable legacy duplicate tag folders when you intentionally want repeated media copies.'),
    el('div', { class: 'row' }, [el('label', {}, ['Filename mode', ctrl.filenameMode]), el('label', {}, [ctrl.metadataJson, ' Write .download.json sidecars']), el('label', {}, [ctrl.tagTxt, ' Write .txt tag sidecars'])]),
    el('p', { class: 'muted tiny' }, 'Post ID filenames are useful for booru/e621 archives. Keep hash-prefixed names when you need maximum collision resistance across generic sources.'),
    el('div', { class: 'row' }, [el('label', {}, ['Date from', ctrl.from]), el('label', {}, ['Date to', ctrl.to]), ctrl.order, el('label', {}, ['Parallel downloads / jobs', ctrl.workers]), el('label', {}, [ctrl.parallelPresets, ' Parallelize presets/category jobs'])]),
    el('div', { class: 'row' }, [el('label', {}, ['API/page delay sec', ctrl.apiDelay]), el('label', {}, ['File delay sec', ctrl.fileDelay]), el('label', {}, ['Timeout sec', ctrl.timeout]), el('label', {}, ['Retries', ctrl.retries]), el('label', {}, ['Backoff sec', ctrl.backoff])]),
    el('div', { class: 'row' }, [el('label', {}, ['Max pages safety cap (0 = source exhausted)', ctrl.maxPages]), el('label', {}, ['Start page/pid', ctrl.startPage])]),
    el('details', { class: 'details-card', open: true }, [
      el('summary', {}, 'Logic gates for e621 / booru queries'),
      el('p', { class: 'muted tiny' }, 'Use either the logic expression OR the Positive/Negative fields. When logic is filled in, you do not need to repeat those tags above; the downloader expands the logic into source queries and dedupes overlaps.'),
      ctrl.logicWrap,
      el('div', { class: 'row' }, [ctrl.logicMode, el('label', {}, ['Max expanded clauses', ctrl.logicMax]), el('button', { class: 'secondary small', onclick: async () => { try { const q = ctrl.logic.value.trim(); if (!q) throw new Error('Enter a logic expression first.'); const r = await api(`/api/downloads/logic/preview?query=${encodeURIComponent(q)}&max_clauses=${encodeURIComponent(ctrl.logicMax.value || 64)}`); toast(`Logic expands to ${r.count} source query clause(s).`); state.downloadValidation = { logic_preview: r }; render(true, true); } catch (err) { toast(err.message, false); } } }, 'Preview logic expansion')])
    ]),
    el('details', { class: 'details-card', open: true }, [
      el('summary', {}, 'Ratings, media/content filters, and blacklist policy'),
      el('p', { class: 'muted tiny' }, 'All ratings and media/content types are allowed by default. Uncheck a box to disallow that class. Source/account blacklists are disabled by default so hidden site filters do not silently reduce totals.'),
      el('div', { class: 'row' }, [el('label', {}, [ctrl.ratingSafe, ' safe']), el('label', {}, [ctrl.ratingQuestionable, ' questionable']), el('label', {}, [ctrl.ratingExplicit, ' explicit'])]),
      el('div', { class: 'row' }, [el('label', {}, [ctrl.allowAnimated, ' allow animated']), el('label', {}, [ctrl.allowVideo, ' allow video']), el('label', {}, [ctrl.allow3d, ' allow 3D']), el('label', {}, [ctrl.allowBlender, ' allow Blender']), el('label', {}, [ctrl.allowRender, ' allow render'])]),
      el('div', { class: 'row' }, [el('label', {}, [ctrl.allowImages, ' allow images']), el('label', {}, [ctrl.allowAudio, ' allow audio']), el('label', {}, [ctrl.allowOtherMedia, ' allow other/unknown media']), el('label', {}, [ctrl.applySourceBlacklists, ' apply source/account blacklists'])]),
      el('div', { class: 'row' }, [el('label', {}, [ctrl.estimateTotal, ' preflight-count total before download'])])
    ])
  ];
  const makeDirectDownloadBody = () => {
    const sourceKey = source.value || preferredDirectSource || 'e621';
    const options = {};
    if (sourceKey === 'generic-json') {
      if (!directApiUrl.value.trim()) throw new Error('Generic JSON source requires options.api_url. Choose e621/e926/etc. for built-in booru downloads, or enter a Generic JSON API URL.');
      options.api_url = directApiUrl.value.trim();
    }
    return { ...buildDownloadPayload(directCtl), preset: { name: `direct-${sourceKey}-${Date.now()}`, source: sourceKey, positive_tags: parseTagString(posCtl.input.value), negative_tags: parseTagString(negCtl.input.value), options }, output_dir: outDirect.value || null, confirmed_authorized: authDirect.checked, max_items: Number(max.value || 100), tag_profile: state.tagProfile };
  };
  const makePresetDownloadBody = () => {
    const names = [...preset.selectedOptions].map(o => o.value);
    return { ...buildDownloadPayload(presetCtl), preset_names: names, output_dir: out.value || null, confirmed_authorized: auth.checked, tag_profile: state.tagProfile };
  };
  const previewPreflight = async body => {
    const r = await api('/api/downloads/preflight', { method: 'POST', body: { ...body, confirmed_authorized: true } });
    state.downloadValidation = { preflight: r };
    toast(`Preflight estimate: ${r.estimated_total || 0} unique downloadable post(s) across ${r.expanded_presets || 0} expanded query clause(s).`);
    render(true, true);
  };
  return el('div', { class: 'grid cols-2' }, [
    card('Booru Source Diagnostics', [
      el('p', { class: 'muted' }, 'Offline validation checks every configured booru/downloader plugin. Live smoke testing performs a tiny metadata request without downloading media.'),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { state.downloadValidation = await api('/api/downloads/validate-sources?live=false'); render(); } catch (err) { toast(err.message, false); } } }, 'Validate Source Configs'),
        el('button', { class: 'secondary', onclick: async () => { try { state.downloadValidation = await api('/api/downloads/validate-sources?live=true'); render(); } catch (err) { toast(err.message, false); } } }, 'Live Smoke Test Sources')
      ]),
      state.downloadValidation ? el('pre', { class: 'log' }, JSON.stringify(state.downloadValidation, null, 2)) : el('p', { class: 'muted' }, 'No source diagnostics run yet.')
    ]),
    card('Direct Booru / JSON Download', [el('p', { class: 'muted' }, 'Tag fields use active dictionary autocomplete. Date/order/category controls are folded into the source query where supported. Generic JSON requires an explicit API URL; e621/e926/etc. use built-in endpoints.'), el('div', { class: 'row' }, [source, max, tagProfileSelect()]), directApiUrl, ...advancedControls(directCtl), el('label', { class: 'label' }, ['Positive tags', posCtl.wrap]), el('label', { class: 'label' }, ['Negative tags', negCtl.wrap]), el('div', { class: 'row' }, [outDirect, el('button', { class: 'secondary', onclick: async () => await pickFolder(outDirect, 'Select download output folder') }, 'Browse Output...')]), el('label', {}, [authDirect, ' I am authorized to download from this source']), el('button', { class: 'primary', onclick: async () => { try { const body = makeDirectDownloadBody(); const r = await api('/api/downloads/run', { method: 'POST', body }); toast(`Download job ${r.job_id} queued. Staying on Downloads; open Jobs when you want details.`); } catch (err) { toast(err.message, false); } } }, 'Run Direct Download'), el('button', { class: 'secondary', onclick: async () => { try { await previewPreflight(makeDirectDownloadBody()); } catch (err) { toast(err.message, false); } } }, 'Preflight Count / Estimate Total')]),
    card('Preset Download Runner', [el('div', { class: 'row' }, [preset, out, el('button', { class: 'secondary', onclick: async () => await pickFolder(out, 'Select download output folder') }, 'Browse Output...')]), ...advancedControls(presetCtl), el('label', {}, [auth, ' I am authorized to download from this source']), el('button', { class: 'primary', onclick: async () => { try { const body = makePresetDownloadBody(); const r = await api('/api/downloads/run', { method: 'POST', body }); toast(`Download job ${r.job_id} queued. Staying on Downloads; open Jobs when you want details.`); } catch (err) { toast(err.message, false); } } }, 'Run Presets'), el('button', { class: 'secondary', onclick: async () => { try { await previewPreflight(makePresetDownloadBody()); } catch (err) { toast(err.message, false); } } }, 'Preflight Count / Estimate Total')]),
    card('Source Config Validation', [
      el('p', { class: 'muted' }, 'Offline fixture validation for every supported source. This checks parser keys, tag extraction, URL extraction, page/limit params, and avoids treating only e621 as validated.'),
      el('button', { class: 'secondary', onclick: async () => { try { state.sourceValidation = await api('/api/downloads/source-validation'); render(); } catch (err) { toast(err.message, false); } } }, 'Validate Source Parsers'),
      el('pre', { class: 'log' }, JSON.stringify(state.sourceValidation || {}, null, 2))
    ])
  ]);
}

function presetsView() {
  const name = el('input', { placeholder: 'Preset name' });
  const source = el('select', { onchange: e => { if (state.tagProfiles.some(p => p.key === e.target.value)) state.tagProfile = e.target.value; render(); } }, state.downloadSources.map(s => el('option', { value: s.key }, s.label || s.key)));
  const posCtl = tagAutocompleteControl({ placeholder: 'positive tags', multiline: true });
  const negCtl = tagAutocompleteControl({ placeholder: 'negative tags', multiline: true });
  const apiUrl = el('input', { placeholder: 'options.api_url for generic-json/custom sources', style: 'width:100%' });
  const logicCtl = tagAutocompleteControl({ placeholder: 'Optional logic query: character_a AND (solo OR portrait) AND NOT sketch. Tag suggestions work here too.', multiline: true, tokenMode: 'logic' });
  logicCtl.input.rows = 3;
  logicCtl.input.style.width = '100%';
  const logicQuery = logicCtl.input;
  const logicMode = el('select', {}, [el('option', { value: 'boolean_expand' }, 'Boolean expand'), el('option', { value: 'raw_append' }, 'Raw append')]);
  const logicMax = el('input', { type: 'number', min: '1', max: '512', value: state.settings.downloader_logic_max_clauses || 64 });
  const importText = el('textarea', { placeholder: 'name: example\npositive: tag_one tag_two\nnegative: bad_tag\nlogic: tag_one AND (solo OR portrait) AND NOT sketch\n;;;\nname: second...' });
  return el('div', { class: 'grid cols-2' }, [
    card('Create / Update Preset', [name, source, tagProfileSelect(), el('label', { class: 'label' }, ['Positive', posCtl.wrap]), el('label', { class: 'label' }, ['Negative', negCtl.wrap]), apiUrl, el('details', { open: true }, [el('summary', {}, 'Optional e621 / booru logic gates'), el('p', { class: 'muted tiny' }, 'Use either this logic expression OR the positive/negative fields; you do not need to fill both. Spaces inside tag names are preserved, so use AND / OR / NOT, commas, or parentheses to separate tags.'), logicCtl.wrap, el('div', { class: 'row' }, [logicMode, el('label', {}, ['Max clauses', logicMax]), el('button', { class: 'secondary small', onclick: async () => { try { if (!logicQuery.value.trim()) throw new Error('Enter a logic expression first.'); const r = await api(`/api/downloads/logic/preview?query=${encodeURIComponent(logicQuery.value.trim())}&max_clauses=${encodeURIComponent(logicMax.value || 64)}`); toast(`Logic expands to ${r.count} source query clause(s).`); state.downloadValidation = { logic_preview: r }; render(true, true); } catch (err) { toast(err.message, false); } } }, 'Preview')])]), el('button', { class: 'primary', onclick: async () => { try { const options = apiUrl.value ? { api_url: apiUrl.value } : {}; const body = { name: name.value, source: source.value, positive_tags: parseTagString(posCtl.input.value), negative_tags: parseTagString(negCtl.input.value), logic_query: logicQuery.value.trim(), logic_mode: logicMode.value, logic_max_clauses: Number(logicMax.value || 64), options }; await api('/api/presets', { method: 'POST', body }); toast('Preset saved'); await refreshAll(); render(); } catch (err) { toast(err.message, false); } } }, 'Save Preset')]),
    card('Import Preset Text', [importText, el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/presets/import-text', { method: 'POST', body: { content: importText.value, source: source.value || 'e621' } }); toast(`Created ${r.created.length} presets`); await refreshAll(); render(); } catch (err) { toast(err.message, false); } } }, 'Import')]),
    card('Presets', [presetsTable()])
  ]);
}
function presetsTable() { return el('table', { class: 'table' }, [el('thead', {}, el('tr', {}, ['Name', 'Source', 'Positive', 'Negative', 'Logic'].map(h => el('th', {}, h)))), el('tbody', {}, state.presets.map(p => el('tr', {}, [el('td', {}, p.name), el('td', {}, p.source), el('td', {}, (p.positive_tags || []).join(' ')), el('td', {}, (p.negative_tags || []).join(' ')), el('td', { class: 'tiny' }, p.logic_query || p.options?.logic_query || '')])))]); }

function dictionaryView() {
  const file = el('input', { type: 'file', accept: '.csv,.tsv,.txt,.gz' });
  const url = el('input', { placeholder: 'Direct CSV/TSV/db-export URL (.csv, .tsv, .csv.gz)', style: 'min-width:420px' });
  const categoryKey = el('input', { placeholder: 'new category key, e.g. artstyle_names' });
  const categoryLabel = el('input', { placeholder: 'label, e.g. Artstyle Names' });
  const categoryColorInput = el('input', { type: 'color', value: '#22c55e', title: 'Custom category color' });
  const customTagName = el('input', { placeholder: 'tag override, e.g. popular_tv_character' });
  const customTagCategory = el('input', { placeholder: 'category key, e.g. character' });
  const customTagColor = el('input', { type: 'color', value: '#22c55e', title: 'Optional color for category' });
  const precedence = el('textarea', {}, (activeProfile().precedence || []).join('\n'));
  const profileKey = el('input', { placeholder: 'profile key, e.g. my_custom_lora_profile' });
  const profileLabel = el('input', { placeholder: 'profile label' });
  const status = state.dictionaryStatus;
  return el('div', { class: 'grid' }, [
    card('Active Booru/Profile Dictionary', [
      el('div', { class: 'row' }, [tagProfileSelect(), el('button', { class: 'secondary', onclick: async () => { await loadDictionaryStatus(); render(); } }, 'Refresh Status'), el('button', { class: 'secondary', onclick: async () => { try { const r = await api('/api/tags/dictionary/import-default', { method: 'POST', body: { profile_key: state.tagProfile } }); toast(`Dictionary import job ${r.job_id} queued`); setTab('Jobs'); } catch (err) { toast(err.message, false); } } }, 'Load Default DB Export')]),
      status ? dictionaryStatusTable(status) : el('p', { class: 'muted' }, 'Press Refresh Status to see dictionary counts.'),
      categoryLegend()
    ]),
    card('Import Tags from File or URL', [
      el('p', { class: 'muted' }, 'Imports CSV/TSV/DB-export rows into the active profile. Suggestions use the selected profile and are color-coded by category.'),
      el('div', { class: 'row' }, [file, el('button', { class: 'secondary', onclick: async () => { try { if (!file.files?.length) throw new Error('Choose a tag dictionary file first.'); const fd = new FormData(); fd.append('file', file.files[0]); const r = await fetch(`/api/tags/dictionary/import?profile_key=${encodeURIComponent(state.tagProfile)}`, { method: 'POST', body: fd }); if (!r.ok) throw new Error(await r.text()); const data = await r.json(); state.tagMeta[state.tagProfile] = {}; await loadDictionaryStatus(); toast(`Imported ${data.imported} tags into ${data.profile_key}`); render(); } catch (err) { toast(err.message, false); } } }, 'Import File')]),
      el('div', { class: 'row' }, [url, el('button', { class: 'secondary', onclick: async () => { try { if (!url.value.trim()) throw new Error('Paste a direct tag export URL first.'); const data = await api('/api/tags/dictionary/import-url', { method: 'POST', body: { profile_key: state.tagProfile, url: url.value.trim() } }); state.tagMeta[state.tagProfile] = {}; await loadDictionaryStatus(); toast(`Imported ${data.imported} tags from URL into ${data.profile_key}`); render(); } catch (err) { toast(err.message, false); } } }, 'Import URL Now')])
    ]),
    card('Global Custom Category / Color Overrides', [
      el('p', { class: 'muted' }, 'These custom categories and tag overrides are global and take priority over every selected booru profile. Use this for artstyle names, recurring character names, trigger tokens, or project-specific categories.'),
      el('div', { class: 'row' }, [categoryKey, categoryLabel, categoryColorInput, el('button', { class: 'secondary', onclick: async () => { try { if (!categoryKey.value.trim()) throw new Error('Enter a category key first.'); await api('/api/tags/categories/custom', { method: 'POST', body: { profile_key: 'custom', key: categoryKey.value.trim(), label: categoryLabel.value.trim() || null, css_class: 'cat-custom', color: categoryColorInput.value } }); await refreshAll(); toast('Global category/color saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Add Global Category + Color')]),
      el('div', { class: 'row' }, [customTagName, customTagCategory, customTagColor, el('button', { class: 'secondary', onclick: async () => { try { if (!customTagName.value.trim()) throw new Error('Enter a tag first.'); if (!customTagCategory.value.trim()) throw new Error('Enter a category key first.'); const r = await api('/api/tags/custom', { method: 'POST', body: { profile_key: state.tagProfile, tag: customTagName.value.trim(), category: customTagCategory.value.trim(), color: customTagColor.value } }); const colors = { ...(state.settings.category_colors || {}) }; colors[r.category] = customTagColor.value; state.settings = await api('/api/settings', { method: 'PUT', body: { values: { category_colors: colors } } }); state.tagMeta[state.tagProfile] = {}; await reapplyVisibleCategories(false); toast('Global custom tag/category override saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Global Tag Override')]),
      el('div', { class: 'row' }, [el('button', { class: 'secondary', onclick: async () => { await reapplyVisibleCategories(false); } }, 'Apply Overrides to Gallery/Selection')]),
      el('p', { class: 'muted' }, 'Custom tags are persisted in runtime/custom_tags.json and also mirrored into the SQLite autocomplete/search tables.')
    ]),
    card('Profile and Precedence Editor', [
      el('p', { class: 'muted' }, 'Tag ordering strategies use this precedence list. One category key per line.'),
      precedence,
      el('div', { class: 'row' }, [el('button', { class: 'primary', onclick: async () => { try { const r = await api(`/api/tags/profiles/${encodeURIComponent(state.tagProfile)}/precedence`, { method: 'PUT', body: { precedence: precedence.value.split(/\n+/).map(x => x.trim()).filter(Boolean) } }); state.tagProfiles = state.tagProfiles.map(p => p.key === r.key ? r : p); toast('Precedence saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Active Precedence')]),
      el('div', { class: 'row' }, [profileKey, profileLabel, el('button', { class: 'secondary', onclick: async () => { try { if (!profileKey.value.trim()) throw new Error('Enter a profile key.'); const base = activeProfile(); const r = await api('/api/tags/profiles', { method: 'POST', body: { key: profileKey.value.trim(), label: profileLabel.value.trim() || profileKey.value.trim(), categories: base.categories, precedence: base.precedence } }); state.tagProfiles.push(r); state.tagProfile = r.key; toast('Profile created'); render(); } catch (err) { toast(err.message, false); } } }, 'Clone Active Profile')])
    ])
  ]);
}
function dictionaryStatusTable(status) {
  const cachedRows = Number(status.cached_tag_rows || 0);
  const effectiveRows = Number(status.effective_found_total || status.total || cachedRows || 0);
  return el('div', { class: 'grid' }, [
    el('div', { class: 'row' }, [
      el('span', { class: 'badge' }, `${status.total || 0} imported tags`),
      cachedRows ? el('span', { class: 'badge ok' }, `${cachedRows} cached export rows found`) : null,
      el('span', { class: 'badge' }, `${effectiveRows} effective found`),
      el('span', { class: 'badge' }, `${status.custom_total || 0} custom`),
      el('span', { class: status.stale ? 'badge bad' : 'badge ok' }, status.stale ? 'stale / needs sync' : 'fresh'),
      el('span', { class: 'muted tiny' }, `latest: ${status.latest_imported_at || 'never'} · ${status.db_export_url || 'No default DB exports URL configured'}`)
    ]),
    el('table', { class: 'table' }, [el('thead', {}, el('tr', {}, ['Category', 'Count'].map(h => el('th', {}, h)))), el('tbody', {}, (status.by_category || []).map(r => el('tr', {}, [el('td', {}, chip(r.category, r.category)), el('td', {}, r.n)])))])
  ]);
}

function databaseView() { const sql = el('textarea', {}, 'SELECT * FROM media LIMIT 20'); const out = el('pre', { class: 'log' }, ''); return el('div', { class: 'grid' }, [card('Read-only SQL Console', [sql, el('button', { class: 'primary', onclick: async () => { try { const r = await api('/api/database/query', { method: 'POST', body: { sql: sql.value } }); out.textContent = JSON.stringify(r.rows, null, 2); } catch (err) { out.textContent = err.message; } } }, 'Run Query'), out])]); }


function migrationSourcePathsFromText(text) {
  return String(text || '').split(/\r?\n|;/).map(x => x.trim()).filter(Boolean);
}
function migrationDefaultInclude() {
  return { models: true, tag_exports: true, tag_database: true, custom_tags: true, custom_models: true, presets: false, downloads: false, outputs: false, ...(state.settings.migration_include_assets || {}) };
}
function migrationPayload(ctrl, dryRun = false) {
  return {
    source_paths: migrationSourcePathsFromText(ctrl.sources.value),
    include: {
      models: ctrl.models.checked,
      tag_exports: ctrl.tagExports.checked,
      tag_database: ctrl.tagDatabase.checked,
      custom_tags: ctrl.customTags.checked,
      custom_models: ctrl.customModels.checked,
      presets: ctrl.presets.checked,
      downloads: ctrl.downloads.checked,
      outputs: ctrl.outputs.checked,
    },
    mode: ctrl.mode.value,
    conflict: ctrl.conflict.value,
    dry_run: Boolean(dryRun),
    newest_first: ctrl.newestFirst.checked,
    delete_source_duplicates: ctrl.deleteDupes.checked,
  };
}
function migrationSummary(scan) {
  if (!scan) return null;
  const sources = scan.sources || [];
  return el('div', { class: 'grid' }, [
    el('div', { class: 'row' }, [
      el('span', { class: 'badge' }, `${sources.length} source install(s)`),
      el('span', { class: 'badge' }, `${scan.totals?.files || 0} reusable file(s)`),
      el('span', { class: 'badge' }, `${Math.round((scan.totals?.bytes || 0) / (1024 * 1024))} MB`),
      el('span', { class: 'badge' }, `${scan.totals?.tag_rows || 0} prior tag DB row(s)`)
    ]),
    el('pre', { class: 'log' }, JSON.stringify(scan, null, 2))
  ]);
}

function migrationView() {
  const include = migrationDefaultInclude();
  if (!state.migrationSourceText && (state.settings.previous_install_paths || []).length) state.migrationSourceText = (state.settings.previous_install_paths || []).join('\n');
  const sources = el('textarea', { rows: '6', value: state.migrationSourceText || '', placeholder: 'One previous install path per line. Pick the folder that contains runtime/ and models/, or the outer folder containing DataCurationToolModern.', style: 'width:100%', oninput: e => { state.migrationSourceText = e.target.value; } });
  const mode = el('select', {}, [['move','Move files into this install'], ['copy','Copy files into this install'], ['symlink','Create symlinks into this install (no copy/move)']].map(([value,label]) => el('option', { value }, label)));
  mode.value = state.settings.migration_mode || 'move';
  const conflict = el('select', {}, [['skip_existing','Keep current/latest target; skip conflicts'], ['replace_if_newer','Replace target only if source file is newer'], ['replace','Replace target on conflicts']].map(([value,label]) => el('option', { value }, label)));
  conflict.value = state.settings.migration_conflict_policy || 'skip_existing';
  const newestFirst = el('input', { type: 'checkbox', checked: state.settings.migration_newest_first !== false });
  const deleteDupes = el('input', { type: 'checkbox', checked: Boolean(state.settings.migration_delete_source_duplicates) });
  const models = el('input', { type: 'checkbox', checked: include.models !== false });
  const tagExports = el('input', { type: 'checkbox', checked: include.tag_exports !== false });
  const tagDatabase = el('input', { type: 'checkbox', checked: include.tag_database !== false });
  const customTags = el('input', { type: 'checkbox', checked: include.custom_tags !== false });
  const customModels = el('input', { type: 'checkbox', checked: include.custom_models !== false });
  const presets = el('input', { type: 'checkbox', checked: Boolean(include.presets) });
  const downloads = el('input', { type: 'checkbox', checked: Boolean(include.downloads) });
  const outputs = el('input', { type: 'checkbox', checked: Boolean(include.outputs) });
  const autoStartup = el('input', { type: 'checkbox', checked: Boolean(state.settings.migrate_assets_on_startup) });
  const autoSyncStartup = el('input', { type: 'checkbox', checked: state.settings.auto_sync_tag_db_on_startup !== false });
  const ctrl = { sources, mode, conflict, newestFirst, deleteDupes, models, tagExports, tagDatabase, customTags, customModels, presets, downloads, outputs };
  const scanOrRun = async (dryRun, queue = true) => {
    const body = migrationPayload(ctrl, dryRun);
    if (!body.source_paths.length) throw new Error('Add at least one previous install folder first.');
    if (!queue) {
      state.migrationOutput = await api('/api/migration/scan', { method: 'POST', body });
      return;
    }
    const r = await api('/api/migration/run', { method: 'POST', body });
    state.migrationLastJob = r.job_id;
    state.lastModelRunJob = r.job_id;
    toast(`${dryRun ? 'Migration dry-run' : 'Asset migration'} queued as job ${r.job_id}`);
    await refreshAll();
  };
  return el('div', { class: 'grid' }, [
    card('Reuse Assets from Previous Installs', [
      el('p', { class: 'muted' }, 'Point the new build at one or more older installs. The newest source is processed first, then older installs contribute only files/database rows that are still unique. This avoids re-downloading model weights and cached tag DB-export files after every test build.'),
      sources,
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => {
          const picked = await api('/api/system/pick-folder', { method: 'POST', body: { title: 'Select previous DataCurationToolModern install folder', initial_dir: '' } }).catch(err => { toast(err.message, false); return null; });
          if (picked?.path) { const current = migrationSourcePathsFromText(sources.value); if (!current.includes(picked.path)) current.push(picked.path); sources.value = current.join('\n'); state.migrationSourceText = sources.value; render(); }
        } }, 'Add Previous Install Folder'),
        mode,
        conflict,
        el('label', {}, [newestFirst, ' Newest install first']),
        el('label', {}, [deleteDupes, ' Delete identical duplicate source files when moving'])
      ]),
      el('div', { class: 'row' }, [
        el('label', {}, [models, ' Models']),
        el('label', {}, [tagExports, ' Tag export files']),
        el('label', {}, [tagDatabase, ' Imported tag DB rows']),
        el('label', {}, [customTags, ' Custom tags']),
        el('label', {}, [customModels, ' Custom model registry']),
        el('label', {}, [presets, ' Presets']),
        el('label', {}, [downloads, ' Downloaded media cache']),
        el('label', {}, [outputs, ' Outputs'])
      ]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { await scanOrRun(false, false); toast('Previous installs scanned'); render(); } catch (err) { toast(err.message, false); } } }, 'Scan Sources'),
        el('button', { class: 'secondary', onclick: async () => { try { await scanOrRun(true, true); render(); } catch (err) { toast(err.message, false); } } }, 'Queue Dry-run'),
        el('button', { class: 'primary', onclick: async () => { try { await scanOrRun(false, true); render(); } catch (err) { toast(err.message, false); } } }, mode.value === 'copy' ? 'Copy Selected Assets' : (mode.value === 'symlink' ? 'Create Symlinks' : 'Move Selected Assets'))
      ]),
      migrationSummary(state.migrationOutput)
    ]),
    card('Startup Migration / Stop Re-downloading on Next Launch', [
      el('p', { class: 'muted' }, 'Save these source paths for the next app launch. Startup migration runs before the tag DB-export startup sync, so existing tag export files and imported dictionary rows can be reused before the app decides whether it needs the network.'),
      el('div', { class: 'row' }, [el('label', {}, [autoStartup, ' Run asset migration on startup']), el('label', {}, [autoSyncStartup, ' Allow tag DB-export startup sync after migration'])]),
      el('button', { class: 'primary', onclick: async () => {
        try {
          const payload = migrationPayload(ctrl, false);
          const saved = await api('/api/migration/startup-settings', { method: 'PUT', body: { source_paths: payload.source_paths, migrate_on_startup: autoStartup.checked, include: payload.include, mode: payload.mode, conflict: payload.conflict, newest_first: payload.newest_first, delete_source_duplicates: payload.delete_source_duplicates } });
          state.settings = await api('/api/settings', { method: 'PUT', body: { values: { auto_sync_tag_db_on_startup: autoSyncStartup.checked } } });
          state.settings = { ...state.settings, previous_install_paths: saved.source_paths, migrate_assets_on_startup: saved.migrate_on_startup, migration_include_assets: saved.include, migration_mode: saved.mode, migration_conflict_policy: saved.conflict, migration_newest_first: saved.newest_first, migration_delete_source_duplicates: saved.delete_source_duplicates };
          toast('Migration startup settings saved'); render();
        } catch (err) { toast(err.message, false); }
      } }, 'Save Migration Startup Settings'),
      el('p', { class: 'muted tiny' }, 'Advanced launch override: set DCT_PREVIOUS_INSTALLS to a path-list and DCT_MIGRATE_ON_STARTUP=1 before run.bat/run.sh. Set DCT_SKIP_STARTUP_TAG_SYNC=1 when you want to prevent any startup tag DB network sync while testing.')
    ]),
    card('Migration Job Status', [
      state.migrationLastJob ? el('button', { class: 'secondary', onclick: () => { state.jobDetailId = state.migrationLastJob; setTab('Jobs'); } }, `Open Migration Job #${state.migrationLastJob}`) : el('p', { class: 'muted' }, 'No migration job queued this session.'),
      jobsTable(12)
    ])
  ]);
}


function codeAssistantView() {
  const root = el('input', { value: state.codeProjectRoot || '', placeholder: 'Project root path, e.g. C:\Users\CK\Desktop\my_project', style: 'min-width:420px', oninput: e => { state.codeProjectRoot = e.target.value; } });
  const chatModels = sortedModels(state.models.filter(m => { const caps = new Set(m.capabilities || []); return caps.has('chat') || caps.has('llm') || caps.has('assistant') || caps.has('orchestration') || m.cloud; }));
  const model = el('select', {}, chatModels.length ? chatModels.map(modelOptionNode) : modelOptions());
  const preferred = chatModels.find(m => m.name === state.assistantConfig?.orchestrator_model_name) || chatModels.find(m => String(m.name || '').includes('kimi')) || chatModels.find(m => m.name === 'openrouter-auto') || chatModels[0];
  rememberSelect('codeModelSelection', model, preferred?.name || '', false);
  model.addEventListener('change', () => { state.codeModelSelection = model.value || ''; primeModelLifecycleForSelection(model.value); updateLiveStatusDom(); });
  const selectedModel = () => state.models.find(m => m.name === model.value) || { name: model.value, label: model.value };
  const prompt = el('textarea', { rows: 8, style: 'width:100%', placeholder: 'Ask for a code review, bug fix, new feature, refactor, or patch. The assistant can return a unified diff; you choose whether to apply it.', value: state.codePrompt || '', oninput: e => { state.codePrompt = e.target.value; } });
  const tokenProfile = el('input', { value: '', placeholder: 'optional token profile name', title: 'Use a non-default named token from Settings → Runtime / Tokens / Devices.' });
  const codeAgentTools = el('input', { type: 'checkbox', checked: Boolean(state.codeAgentToolsChatEnabled || state.settings?.agent_tools_enable_approved_coa_execution), title: 'Tell the coding model that approved local tools are available and parse COA/tool calls from its response.' });
  codeAgentTools.addEventListener('change', e => { state.codeAgentToolsChatEnabled = e.target.checked; state.agentCoaExecutionEnabled = e.target.checked || state.agentCoaExecutionEnabled; });
  const rt = modelRuntimeControls(selectedModel());
  const reasoning = assistantReasoningControls('code');
  const scan = state.codeProjectScan || {};
  const files = scan.files || [];
  const fileFilter = el('input', { placeholder: 'filter files', value: state.codeFileFilter || '', oninput: e => { state.codeFileFilter = e.target.value; render(true, true); } });
  const filtered = files.filter(f => !state.codeFileFilter || String(f.path || '').toLowerCase().includes(String(state.codeFileFilter).toLowerCase())).slice(0, 250);
  const selectedFiles = () => [...state.codeSelectedFiles];
  const fileList = files.length ? el('div', { class: 'file-list compact-list' }, filtered.map(f => {
    const cb = el('input', { type: 'checkbox', checked: state.codeSelectedFiles.has(f.path), onchange: e => { if (e.target.checked) state.codeSelectedFiles.add(f.path); else state.codeSelectedFiles.delete(f.path); } });
    return el('label', { class: 'file-row' }, [cb, el('span', {}, f.path), el('span', { class: 'muted tiny' }, ` ${Math.round(Number(f.size_bytes || 0)/1024)} KB`)]);
  })) : el('p', { class: 'muted' }, 'Scan a project folder to list source files.');
  const sendCodeChat = async (promptText = null, chatOptions = {}) => {
    if (!root.value.trim()) throw new Error('Choose a project root first.');
    const finalPrompt = String(promptText || '').trim() || prompt.value.trim();
    if (!finalPrompt) throw new Error('Type a coding request first.');
    const body = {
      root_path: root.value.trim(),
      prompt: finalPrompt,
      model_name: model.value || 'dataset-assistant',
      files: selectedFiles(),
      conversation_id: state.codeConversationId || null,
      token_profile: tokenProfile.value.trim() || null,
      ...runtimeBodyFromControls(rt),
      options: {
        max_new_tokens: Math.max(Number(state.settings.model_max_new_tokens || 0), 2048),
        max_continuation_rounds: chatOptions.continueLastOutput ? 2 : 1,
        auto_continue_incomplete: true,
        continue_last_output: Boolean(chatOptions.continueLastOutput),
        code_assistant: true,
        agent_tools_chat: Boolean(codeAgentTools.checked),
        agent_tools_execute_coa_enabled: Boolean(codeAgentTools.checked || state.agentCoaExecutionEnabled || state.settings?.agent_tools_enable_approved_coa_execution),
        temperature: state.settings.model_temperature || 0.2,
        ...reasoningOptionsFromControls(reasoning, { min_chat_max_new_tokens: Math.max(Number(reasoning.chatTokens.value || 0), 2048) })
      }
    };
    setOptimisticModelStage(body.model_name, 'inference', 'running', 0.02, 'Code assistant request sent');
    updateLiveStatusDom();
    const r = await api('/api/code/chat', { method: 'POST', body });
    state.codeConversationId = r.conversation_id;
    state.codeMessages = r.history || state.codeMessages || [];
    state.codeConversationState = { ...(state.codeConversationState || {}), memory_summary: r.memory_summary || state.codeConversationState?.memory_summary || '', last_context_budget: r.context_budget || state.codeConversationState?.last_context_budget || null, context_reset_message_id: r.context_reset_message_id || state.codeConversationState?.context_reset_message_id || 0, project_root: root.value.trim(), selected_files: selectedFiles() };
    state.codeLastResponse = r;
    state.codeLastError = null;
    if (codeAgentTools.checked && r.assistant_message_id && r.conversation_id) {
      try { await fetchCoaOptionsForMessage(r.conversation_id, r.assistant_message_id); } catch (_) {}
    }
    if (codeAgentTools.checked && r.response) {
      try {
        const parsed = await api('/api/agent-tools/parse-tool-calls', { method: 'POST', body: { text: r.response } });
        if ((parsed.tool_calls || []).length) {
          state.agentSurfacePlans['agent-code-assistant'] = {
            ...(state.agentSurfacePlans['agent-code-assistant'] || {}),
            plan: { summary: 'Executable COA/tool calls parsed from code assistant response', steps: parsed.tool_calls },
            tool_calls: parsed.tool_calls,
            response: r.response,
            conversation_id: r.conversation_id
          };
          toast(`Parsed ${parsed.tool_calls.length} executable COA/tool call(s) from code assistant response`);
        }
      } catch (_) {}
    }
    toast(`Code assistant replied using ${r.model_name}`);
    await refreshModelStatuses(false).catch(() => {});
    updateLiveStatusDom();
  };
  const sendQueuedCodeChat = async (text, meta = {}) => {
    resetStaleChatQueueLock('code');
    const item = { text: String(text || ''), meta: { ...(meta || {}) }, queued_at: new Date().toISOString() };
    if (state.codeChatSending) {
      state.codeChatQueue = [...(state.codeChatQueue || []), item];
      toast(`Queued code chat message (${state.codeChatQueue.length} waiting).`);
      render(true, true);
      return;
    }
    state.codeChatSending = true;
    state.codeChatCurrent = item;
    render(true, true);
    try {
      let current = item;
      while (current) {
        state.codeChatCurrent = current;
        await sendCodeChat(current.text, current.meta || {});
        current = (state.codeChatQueue || []).shift() || null;
        state.codeChatQueue = state.codeChatQueue || [];
        if (current) render(true, true);
      }
    } finally {
      state.codeChatSending = false;
      state.codeChatCurrent = null;
      render(true, true);
    }
  };
  const lastText = state.codeLastResponse?.response || (state.codeMessages || []).slice().reverse().find(m => m.role === 'assistant')?.content || '';
  return el('div', { class: 'grid' }, [
    card('Code Assistant / Project-Aware Developer Workspace', [
      el('p', { class: 'muted' }, 'Point this at a local project, select relevant files, chat with a configured LLM/API model, and apply user-approved unified-diff patches. Patch application creates backups by default.'),
      el('div', { class: 'row' }, [root, el('button', { class: 'secondary', onclick: async () => { try { const picked = await api('/api/system/pick-folder', { method: 'POST', body: { title: 'Select project root', initial_dir: root.value || '' } }); if (picked?.path) { state.codeProjectRoot = picked.path; root.value = picked.path; } } catch (err) { toast(err.message, false); } } }, 'Browse Project')]),
      el('div', { class: 'row' }, [model, tokenProfile, el('label', { title: 'Adds the executable tool-call contract to code chat prompts and parses COA actions.' }, [codeAgentTools, ' enable approved local tools/COA when needed']), el('button', { class: 'secondary', onclick: async () => { try { if (!root.value.trim()) throw new Error('Choose a project root first.'); state.codeProjectScan = await api('/api/code/scan', { method: 'POST', body: { root_path: root.value.trim(), max_files: 900 } }); state.codeSelectedFiles = new Set((state.codeProjectScan.files || []).slice(0, 8).map(f => f.path)); toast(`Scanned ${state.codeProjectScan.file_count || 0} source file(s)`); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Scan Project')]),
      modelLifecycleStrip(selectedModel(), true),
      inlineSelectedModelRuntimeControls(model, rt, 'code-assistant'),
      assistantReasoningPanel(reasoning, 'Think longer / visible coding plan controls'),
      agentToolsInlinePanel('code-assistant', 'Code Assistant', () => [], model, rt),
      scan.root_path ? el('pre', { class: 'log compact' }, JSON.stringify({ root_path: scan.root_path, file_count: scan.file_count, total_text_bytes: scan.total_text_bytes, language_counts: scan.language_counts }, null, 2)) : null
    ].filter(Boolean)),
    card('Project Files for Context', [
      el('div', { class: 'row' }, [fileFilter, el('button', { class: 'secondary small', onclick: () => { filtered.forEach(f => state.codeSelectedFiles.add(f.path)); render(true, true); } }, 'Select Visible'), el('button', { class: 'secondary small', onclick: () => { state.codeSelectedFiles.clear(); render(true, true); } }, 'Deselect All'), el('span', { class: 'badge' }, `${state.codeSelectedFiles.size} selected`)]),
      fileList
    ]),
    card('Chat / Patch Request', [
      prompt,
      el('div', { class: 'row' }, [
        el('button', { class: 'primary', onclick: async () => { try { await sendQueuedCodeChat(prompt.value); state.codePrompt = ''; prompt.value = ''; render(true, true); } catch (err) { state.codeLastError = state.lastApiError || { error: err.message }; toast(err.message, false); render(true, true); } } }, state.codeChatSending ? 'Queue Coding Request' : 'Send Coding Request'),
        el('button', { class: 'secondary', onclick: () => { state.codeConversationId = null; state.codeMessages = []; state.codeConversationState = {}; state.codeLastResponse = null; render(true, true); } }, 'New Code Conversation'),
        state.codeConversationId ? el('button', { class: 'secondary', onclick: async () => { try { await loadScopedChatConversation(state.codeConversationId, 'code'); toast('Code conversation refreshed'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Refresh History') : null,
        el('button', { class: 'secondary', disabled: !lastText, onclick: async () => { try { const r = await api('/api/code/apply-patch', { method: 'POST', body: { root_path: root.value.trim(), patch_text: lastText, create_backup: true, check_only: true } }); state.codePatchResult = r; toast(r.error ? 'Patch check failed' : 'Patch check passed', !r.error); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Check Diff'),
        el('button', { class: 'danger', disabled: !lastText, onclick: async () => { try { if (!confirm('Apply the first unified diff from the last assistant response to this project? Backups will be created.')) return; const r = await api('/api/code/apply-patch', { method: 'POST', body: { root_path: root.value.trim(), patch_text: lastText, create_backup: true, check_only: false } }); state.codePatchResult = r; toast(r.applied ? 'Patch applied' : 'Patch failed', Boolean(r.applied)); state.codeProjectScan = await api('/api/code/scan', { method: 'POST', body: { root_path: root.value.trim(), max_files: 900 } }).catch(() => state.codeProjectScan); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Apply Last Diff')
      ].filter(Boolean)),
      state.codePatchResult ? el('pre', { class: 'log compact' }, JSON.stringify(state.codePatchResult, null, 2)) : null,
      state.codeLastError ? errorLogCard('Last Code Assistant Error', state.codeLastError) : null,
      state.codeLastResponse ? visiblePlanPanel(state.codeLastResponse, 'Visible coding plan / action notes') : null,
      conversationHistoryPanel('code', state.codeConversationId, state.codeMessages, {
        title: 'Code Assistant Chat',
        surface: 'Code Assistant',
        modelName: () => model.value || 'dataset-assistant',
        runtimeControls: rt,
        context: () => JSON.stringify({ surface: 'Code Assistant', project_root: root.value.trim(), selected_files: selectedFiles(), scan_summary: state.codeProjectScan || null }, null, 2),
        reload: async id => loadScopedChatConversation(id, 'code'),
        saveState: () => ({
          title: `Code Assistant · ${root.value.trim() || 'project'}`,
          scope: 'code-assistant',
          project_root: root.value.trim(),
          selected_files: selectedFiles(),
          file_filter: state.codeFileFilter || '',
          scan_summary: state.codeProjectScan ? { root_path: state.codeProjectScan.root_path, file_count: state.codeProjectScan.file_count, total_text_bytes: state.codeProjectScan.total_text_bytes, language_counts: state.codeProjectScan.language_counts } : {},
          selected_model: model.value || '',
          token_profile: tokenProfile.value.trim() || ''
        }),
        composer: {
          draftKey: 'codeChatDraft',
          placeholder: 'Continue chatting about this project/codebase. Ask for a fix, feature, refactor, explanation, test, or continuation of the previous answer.',
          sendLabel: 'Send Code Chat',
          finishLabel: 'Finish Last Output',
          hint: 'The code assistant receives persistent condensed memory + recent turns + selected project files.',
          disabled: false,
          onSend: sendQueuedCodeChat
        }
      }),
      lastText ? el('pre', { class: 'log full-log' }, lastText) : el('p', { class: 'muted' }, 'No code assistant response yet.')
    ].filter(Boolean))
  ]);
}

function settingsView() {
  const s = state.settings || {};
  function input(key, placeholder = '', type = 'text') { return el('input', { placeholder, value: s[key] ?? '', type }); }
  const hf = input('huggingface_token', 'HF token'); const openrouter = input('openrouter_token', 'OpenRouter token'); const openai = input('openai_api_key', 'OpenAI API key'); const anthropic = input('anthropic_api_key', 'Anthropic API key');
  const devices = el('input', { value: (s.preferred_devices || ['auto']).join(','), placeholder: 'auto,cuda:0,cuda:1' });
  const cache = input('model_cache_dir', 'Model cache directory'); const tagCount = input('tag_suggestion_count', 'Tag suggestion count', 'number'); const temp = input('model_temperature', 'Temperature', 'number'); temp.step = '0.05'; const maxTokens = input('model_max_new_tokens', 'Max new tokens', 'number'); const threshold = input('classifier_threshold', 'Classifier threshold', 'number'); threshold.step = '0.05'; const workers = input('backend_worker_count', 'Backend workers', 'number'); const maxJobs = input('max_concurrent_jobs', 'Max queued jobs running', 'number');
  const importWorkers = input('import_worker_count', 'Parallel import workers, 0 = auto', 'number'); const dlWorkers = input('downloader_parallel_workers', 'Downloader parallel workers', 'number');
  const modelDlWorkers = input('model_download_parallel_workers', 'Model file transfer workers', 'number'); modelDlWorkers.value = s.model_download_parallel_workers || 1;
  const modelDlSerial = el('input', { type: 'checkbox', checked: s.model_download_serial_queue !== false });
  const apiProfiles = el('textarea', { rows: 11, style: 'width:100%', placeholder: 'Named provider tokens JSON. Example: {"openrouter":[{"name":"main","token":"sk-or-...","default":true}],"huggingface":[{"name":"hf1","token":"hf_..."}],"runpod":[{"name":"serverless","token":"..."}]}' }, JSON.stringify(s.api_token_profiles || { huggingface: [], openrouter: [], openai: [], anthropic: [], xai: [], runpod: [], vastai: [], lambda_labs: [] }, null, 2));
  const autoSyncStartup = el('input', { type: 'checkbox', checked: Boolean(s.auto_sync_tag_db_on_startup) });
  const syncEmptyOnly = el('input', { type: 'checkbox', checked: s.tag_db_sync_if_empty_only !== false });
  const cacheHours = input('tag_db_export_cache_hours', 'Tag DB export cache hours', 'number');
  const defaultProfile = tagProfileSelect(); defaultProfile.value = s.default_tag_profile || state.tagProfile;
  const defaultOrder = el('select', {}, ['retain', 'booru', 'custom_profile', 'lora_purpose'].map(x => el('option', { value: x }, x))); defaultOrder.value = s.default_ordering_strategy || state.orderingStrategy;
  const retain = el('input', { type: 'checkbox', checked: Boolean(s.retain_imported_tag_order) });
  const tagTextMode = el('select', { title: 'Controls whether app-owned tags are stored/displayed as blue_eyes or blue eyes. Applied on startup so dictionaries, aliases, implications, media tags, and sidecars stay consistent.' }, [
    el('option', { value: 'underscores' }, 'Use underscores: blue_eyes'),
    el('option', { value: 'spaces' }, 'Use spaces: blue eyes')
  ]);
  tagTextMode.value = s.tag_text_mode || 'underscores';
  const tagModeRestartNeeded = Boolean(s.tag_text_mode_restart_required || ((s.tag_text_mode || 'underscores') !== (s.tag_text_mode_active || 'underscores')));
  const metaExtractImport = el('input', { type: 'checkbox', checked: Boolean(s.metadata_extract_on_import) });
  const metaApplyFallback = el('input', { type: 'checkbox', checked: s.metadata_apply_when_no_sidecar !== false });
  const metaTagSource = el('select', {}, ['positive_prompt', 'all', 'character_prompts', 'lora_refs', 'training_tags', 'negative_prompt'].map(x => el('option', { value: x }, x))); metaTagSource.value = s.metadata_default_tag_source || 'positive_prompt';
  const metaCaptionSource = el('select', {}, ['positive_prompt', 'caption', 'summary', 'character_prompts', 'negative_prompt', 'all'].map(x => el('option', { value: x }, x))); metaCaptionSource.value = s.metadata_default_caption_source || 'positive_prompt';
  const frameDir = input('media_frame_output_dir', 'Default frame output dir');
  const audioDir = input('audio_recording_dir', 'Default audio recording/extract dir');
  const kritaExe = input('krita_executable', 'Krita executable path');
  const kritaDir = input('krita_handoff_dir', 'Krita handoff directory');
  const defShard = el('select', {}, ['none','auto','balanced','balanced_low_0','sequential','custom'].map(x => el('option', { value: x }, x))); defShard.value = s.default_model_sharding_strategy || (s.default_model_sharding ? 'auto' : 'none');
  const defGpuIds = el('input', { value: (s.default_model_device_ids || [0]).join(','), placeholder: 'Default GPU ids: 0,1,2' });
  const defDtype = el('select', {}, ['auto','float16','bfloat16','float32'].map(x => el('option', { value: x }, x))); defDtype.value = s.default_model_dtype || 'auto';
  const defQuant = el('select', {}, ['none','8bit','4bit'].map(x => el('option', { value: x }, x))); defQuant.value = s.default_model_quantization || 'none';
  const flexEnv = input('flexavatar_conda_env', 'FlexAvatar Conda environment name'); flexEnv.value = s.flexavatar_conda_env || 'dct-flexavatar';
  const flexConda = input('flexavatar_conda_executable', 'Optional conda executable path');
  const flexPython = input('flexavatar_python', 'Optional FlexAvatar environment Python path');
  const flexSource = input('flexavatar_source_dir', 'Optional FlexAvatar source override');
  const flexWorkspace = input('flexavatar_workspace_dir', 'Optional FlexAvatar workspace override');
  const flexDevice = input('flexavatar_default_device', 'FlexAvatar default device'); flexDevice.value = s.flexavatar_default_device || 'cuda:0';
  const flexTimeout = input('flexavatar_job_timeout_seconds', 'FlexAvatar job timeout seconds', 'number'); flexTimeout.value = s.flexavatar_job_timeout_seconds || 86400;
  const flexCheckpointUrl = input('flexavatar_checkpoint_url', 'Optional FLEX-1 checkpoint URL override');
  const agentEnabled = el('input', { type: 'checkbox', checked: s.agent_tools_enabled !== false });
  const agentRequireApproval = el('input', { type: 'checkbox', checked: s.agent_tools_require_approval !== false });
  const agentShell = el('input', { type: 'checkbox', checked: s.agent_tools_allow_shell !== false });
  const agentPython = el('input', { type: 'checkbox', checked: s.agent_tools_allow_python !== false });
  const agentWrite = el('input', { type: 'checkbox', checked: s.agent_tools_allow_file_write !== false });
  const agentBrowser = el('input', { type: 'checkbox', checked: s.agent_tools_allow_browser !== false });
  const agentProfile = el('input', { type: 'checkbox', checked: Boolean(s.agent_tools_allow_existing_browser_profile) });
  const agentHighRisk = el('input', { type: 'checkbox', checked: Boolean(s.agent_tools_allow_high_risk) });
  const agentAnyPath = el('input', { type: 'checkbox', checked: Boolean(s.agent_tools_allow_any_path) });
  const agentCoaExecution = el('input', { type: 'checkbox', checked: Boolean(s.agent_tools_enable_approved_coa_execution) });
  const agentAutoRelay = el('input', { type: 'checkbox', checked: s.agent_tools_auto_relay_after_execution !== false });
  const agentConfirmMode = el('select', { title: 'How much approval is required for COA execution and automatic reattempts.' }, [
    ['always','Always get confirmation on every COA/action'],
    ['high_risk_only','Only confirm high-risk/new-section COAs'],
    ['full_access_high_risk_confirm','Full computer access, confirm high-risk COAs'],
    ['full_auto','Full auto, including high-risk COAs']
  ].map(([v,l]) => el('option', { value: v }, l))); agentConfirmMode.value = s.agent_tools_confirmation_mode || 'always';
  const agentAutoRetry = el('input', { type: 'checkbox', checked: s.agent_tools_auto_reattempt_enabled !== false });
  const agentMaxRetries = input('agent_tools_max_reattempts', 'Max automatic re-attempts', 'number'); agentMaxRetries.value = s.agent_tools_max_reattempts ?? 2;
  const agentInfiniteRetries = el('input', { type: 'checkbox', checked: Boolean(s.agent_tools_allow_infinite_reattempts) });
  const agentSpawnModels = el('input', { type: 'checkbox', checked: s.agent_tools_orchestrator_can_spawn_models !== false });
  const agentModelDecidesTools = el('input', { type: 'checkbox', checked: s.agent_tools_model_decides_when_to_use_tools !== false });
  const agentPlainChatAllowed = el('input', { type: 'checkbox', checked: s.agent_tools_allow_plain_chat_without_tools !== false });
  const agentGuiRouting = el('input', { type: 'checkbox', checked: s.agent_tools_app_gui_action_routing !== false });
  const agentShowDecisionBadges = el('input', { type: 'checkbox', checked: s.agent_tools_show_tool_decision_badges !== false });
  const agentSandbox = el('select', {}, ['workspace','local','docker'].map(x => el('option', { value: x }, x))); agentSandbox.value = s.agent_tools_sandbox_mode || 'local';
  const agentWorkspace = input('agent_tools_workspace', 'Agent tools workspace directory');
  const agentAllowedRoots = el('textarea', { rows: 4, style: 'width:100%', placeholder: 'Allowed roots, one per line. Defaults: Downloads, Desktop, Documents.' }, (s.agent_tools_allowed_roots || []).join('\n'));
  const agentBrowserProfile = input('agent_tools_browser_profile_path', 'Optional Firefox profile path');
  const agentDockerImage = input('agent_tools_docker_image', 'Docker image for sandbox'); agentDockerImage.value = s.agent_tools_docker_image || 'python:3.11-slim';
  const agentTimeout = input('agent_tools_default_timeout_seconds', 'Default timeout seconds', 'number'); agentTimeout.value = s.agent_tools_default_timeout_seconds || 120;
  const agentMaxTimeout = input('agent_tools_max_timeout_seconds', 'Max timeout seconds', 'number'); agentMaxTimeout.value = s.agent_tools_max_timeout_seconds || 1800;
  const agentOutputChars = input('agent_tools_max_output_chars', 'Max output chars', 'number'); agentOutputChars.value = s.agent_tools_max_output_chars || 120000;
  const agentSmoke = el('input', { type: 'checkbox', checked: s.agent_tools_smoke_test_on_startup !== false });
  const agentPipVenv = el('input', { type: 'checkbox', checked: s.agent_tools_allow_python_venv_install !== false });
  const agentDefaultVenv = input('agent_tools_default_python_venv', 'Default Python venv name'); agentDefaultVenv.value = s.agent_tools_default_python_venv || 'agent-tools-default';
  const thinkMode = el('select', {}, ['off','fast','balanced','deep'].map(x => el('option', { value: x }, x))); thinkMode.value = s.assistant_thinking_mode || 'balanced';
  const reasoningEffort = el('select', {}, ['none','low','medium','high','max'].map(x => el('option', { value: x }, x))); reasoningEffort.value = s.assistant_reasoning_effort || 'medium';
  const showVisiblePlan = el('input', { type: 'checkbox', checked: s.assistant_show_visible_plan !== false });
  const showLiveActionNotes = el('input', { type: 'checkbox', checked: s.assistant_show_live_action_notes !== false });
  const planningPasses = input('assistant_planning_passes', 'Planning passes', 'number'); planningPasses.value = s.assistant_planning_passes ?? 1;
  const planMaxTokens = input('assistant_plan_max_tokens', 'Plan max tokens', 'number'); planMaxTokens.value = s.assistant_plan_max_tokens || 768;
  const minChatTokens = input('assistant_min_chat_tokens', 'Min chat tokens', 'number'); minChatTokens.value = s.assistant_min_chat_tokens || 1024;
  const deepChatTokens = input('assistant_deep_chat_tokens', 'Deep chat tokens', 'number'); deepChatTokens.value = s.assistant_deep_chat_tokens || 4096;
  const maxReflect = input('assistant_max_auto_reflection_rounds', 'Auto reflection rounds', 'number'); maxReflect.value = s.assistant_max_auto_reflection_rounds ?? 1;
  const vramCleanup = el('input', { type: 'checkbox', checked: s.model_vram_cleanup_after_inference !== false });
  const vramAggressive = el('input', { type: 'checkbox', checked: s.model_vram_aggressive_gc_after_inference !== false });
  const vramResetPeaks = el('input', { type: 'checkbox', checked: s.model_vram_reset_peak_stats_after_inference !== false });
  const vramAutoOffload = el('input', { type: 'checkbox', checked: s.model_vram_auto_cpu_offload_enabled !== false });
  const vramOffloadPolicy = el('select', {}, [
    ['disabled','Disabled: keep models in VRAM'],
    ['on_pressure','On pressure: offload to CPU only when VRAM is high'],
    ['after_chat','After chat: move chat model to CPU RAM after each response'],
    ['after_every_inference','After every inference: move model to CPU RAM after every run']
  ].map(([v,l]) => el('option', { value: v }, l))); vramOffloadPolicy.value = s.model_vram_auto_cpu_offload_policy || 'on_pressure';
  const vramOffloadThreshold = input('model_vram_auto_cpu_offload_threshold', 'VRAM pressure threshold 0.50-0.98', 'number'); vramOffloadThreshold.step = '0.01'; vramOffloadThreshold.value = s.model_vram_auto_cpu_offload_threshold ?? 0.82;
  const vramIdleSeconds = input('model_vram_idle_cpu_offload_seconds', 'Idle CPU offload seconds', 'number'); vramIdleSeconds.value = s.model_vram_idle_cpu_offload_seconds ?? 300;
  const vramDisableCache = el('input', { type: 'checkbox', checked: s.model_vram_disable_generation_cache_on_pressure !== false });
  const vramContextThreshold = input('model_vram_context_pressure_threshold', 'Disable KV cache when context >=', 'number'); vramContextThreshold.step = '0.01'; vramContextThreshold.value = s.model_vram_context_pressure_threshold ?? 0.70;
  const voiceSttEnabled = el('input', { type: 'checkbox', checked: s.voice_stt_enabled !== false });
  const voiceTtsEnabled = el('input', { type: 'checkbox', checked: Boolean(s.voice_tts_enabled) });
  const voiceSttModel = voiceModelSelect('stt', s.voice_stt_model_name || 'whisper-large-v3-turbo');
  const voiceTtsModel = voiceModelSelect('tts', s.voice_tts_model_name || 'kokoro-82m');
  const voiceSttPolicy = el('select', {}, [['on_demand','On demand: load only when I click Stop & Transcribe'], ['always','Always loaded/resident when possible']].map(([v,l]) => el('option', { value: v }, l))); voiceSttPolicy.value = s.voice_stt_load_policy || 'on_demand';
  const voiceTtsPolicy = el('select', {}, [['on_demand','On demand: load only when speaking'], ['always','Always loaded/resident when possible']].map(([v,l]) => el('option', { value: v }, l))); voiceTtsPolicy.value = s.voice_tts_load_policy || 'on_demand';
  const voiceSttDevice = el('select', {}, ['auto','cpu','cuda:0','cuda:1'].map(x => el('option', { value: x }, x))); voiceSttDevice.value = s.voice_stt_device || 'auto';
  const voiceTtsDevice = el('select', {}, ['auto','cpu','cuda:0','cuda:1'].map(x => el('option', { value: x }, x))); voiceTtsDevice.value = s.voice_tts_device || 'auto';
  const voiceSttGpuIds = el('input', { value: (s.voice_stt_device_ids || []).join(','), placeholder: 'STT GPU ids e.g. 0 or 1' });
  const voiceTtsGpuIds = el('input', { value: (s.voice_tts_device_ids || []).join(','), placeholder: 'TTS GPU ids e.g. 0 or 1' });
  const voiceSttDtype = el('select', {}, ['auto','float16','bfloat16','float32'].map(x => el('option', { value: x }, x))); voiceSttDtype.value = s.voice_stt_torch_dtype || 'auto';
  const voiceTtsDtype = el('select', {}, ['auto','float16','bfloat16','float32'].map(x => el('option', { value: x }, x))); voiceTtsDtype.value = s.voice_tts_torch_dtype || 'auto';
  const voiceSttQuant = el('select', {}, ['none','8bit','4bit'].map(x => el('option', { value: x }, x))); voiceSttQuant.value = s.voice_stt_quantization || 'none';
  const voiceTtsQuant = el('select', {}, ['none','8bit','4bit'].map(x => el('option', { value: x }, x))); voiceTtsQuant.value = s.voice_tts_quantization || 'none';
  const voiceSttLang = el('input', { value: s.voice_stt_language || '', placeholder: 'STT language hint e.g. en, blank=auto' });
  const voiceTtsLang = el('input', { value: s.voice_tts_language || '', placeholder: 'TTS language e.g. en, blank=default' });
  const voiceTtsVoice = el('input', { value: s.voice_tts_voice || 'af_heart', placeholder: 'TTS voice/speaker e.g. af_heart' });
  const voiceTtsAuto = el('input', { type: 'checkbox', checked: Boolean(s.voice_tts_auto_speak) });
  const voiceTtsChunk = el('input', { type: 'checkbox', checked: s.voice_tts_chunk_long_text !== false });
  const voiceTtsChunkChars = el('input', { type: 'number', min: '80', max: '2000', value: s.voice_tts_max_chunk_chars || 360, title: 'Maximum text characters per TTS chunk. Lower values are safer for Bark-like models.' });
  const voiceTtsChunkPause = el('input', { type: 'number', min: '0', max: '2000', value: s.voice_tts_chunk_pause_ms ?? 180, title: 'Silence in milliseconds inserted between stitched TTS chunks.' });
  const voiceInDevice = audioDeviceSelect('input', s.voice_browser_input_device_id || '');
  const voiceOutDevice = audioDeviceSelect('output', s.voice_browser_output_device_id || '');
  const currentVoiceSettings = (overrides = {}) => ({
    voice_stt_enabled: voiceSttEnabled.checked,
    voice_tts_enabled: voiceTtsEnabled.checked,
    voice_stt_model_name: voiceSttModel.value,
    voice_tts_model_name: voiceTtsModel.value,
    voice_stt_load_policy: voiceSttPolicy.value,
    voice_tts_load_policy: voiceTtsPolicy.value,
    voice_stt_device: voiceSttDevice.value,
    voice_tts_device: voiceTtsDevice.value,
    voice_stt_device_ids: parseGpuIds(voiceSttGpuIds.value),
    voice_tts_device_ids: parseGpuIds(voiceTtsGpuIds.value),
    voice_stt_torch_dtype: voiceSttDtype.value,
    voice_tts_torch_dtype: voiceTtsDtype.value,
    voice_stt_quantization: voiceSttQuant.value,
    voice_tts_quantization: voiceTtsQuant.value,
    voice_stt_language: voiceSttLang.value || null,
    voice_tts_language: voiceTtsLang.value || null,
    voice_tts_voice: voiceTtsVoice.value || 'af_heart',
    voice_tts_auto_speak: voiceTtsAuto.checked,
    voice_tts_chunk_long_text: voiceTtsChunk.checked,
    voice_tts_max_chunk_chars: Number(voiceTtsChunkChars.value || 360),
    voice_tts_chunk_pause_ms: Number(voiceTtsChunkPause.value || 0),
    voice_browser_input_device_id: voiceInDevice.value || null,
    voice_browser_output_device_id: voiceOutDevice.value || null,
    ...overrides,
  });
  const saveVoiceSettingsFromControls = async (overrides = {}) => {
    state.settings = await api('/api/settings', { method: 'PUT', body: { values: currentVoiceSettings(overrides) } });
    state.voiceStatus = await api('/api/voice/status').catch(() => state.voiceStatus);
    return state.settings;
  };
  const vramDebug = el('input', { type: 'checkbox', checked: Boolean(s.model_vram_cleanup_debug) });
  return el('div', { class: 'grid' }, [
    card('Runtime / Tokens / Devices', [
      el('p', { class: 'muted' }, 'Secrets are masked when loaded. Leave a masked field unchanged to preserve the existing stored value. Named token profiles let you keep multiple Hugging Face/OpenRouter/xAI/Runpod/Vast/Lambda keys and choose one in model options.'),
      el('div', { class: 'row' }, [hf, openrouter, openai, anthropic]),
      el('div', { class: 'row' }, [devices, cache, workers, maxJobs, importWorkers, dlWorkers, modelDlWorkers, el('label', {}, [modelDlSerial, ' queue model downloads serially'])]),
      el('details', { open: false }, [el('summary', {}, 'Named API token profiles / provider keys'), apiProfiles, el('p', { class: 'muted tiny' }, 'Supported providers: huggingface, openrouter, openai, anthropic, xai, runpod, vastai, lambda_labs. Use token_profile in advanced model options when you want a non-default key.')]),
      el('button', { class: 'primary', onclick: async () => { try {
        let parsedProfiles = null;
        try { parsedProfiles = JSON.parse(apiProfiles.value || '{}'); } catch (profileErr) { throw new Error('Named API token profiles must be valid JSON: ' + profileErr.message); }
        const values = { preferred_devices: devices.value.split(',').map(x => x.trim()).filter(Boolean), model_cache_dir: cache.value || null, backend_worker_count: Number(workers.value || 1), max_concurrent_jobs: Number(maxJobs.value || workers.value || 1), import_worker_count: Number(importWorkers.value || 0), downloader_parallel_workers: Number(dlWorkers.value || 4), model_download_parallel_workers: Number(modelDlWorkers.value || 1), model_download_serial_queue: modelDlSerial.checked, api_token_profiles: parsedProfiles };
        if (hf.value && hf.value !== '********') values.huggingface_token = hf.value; if (openrouter.value && openrouter.value !== '********') values.openrouter_token = openrouter.value; if (openai.value && openai.value !== '********') values.openai_api_key = openai.value; if (anthropic.value && anthropic.value !== '********') values.anthropic_api_key = anthropic.value;
        state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); toast('Runtime settings saved'); render();
      } catch (err) { toast(err.message, false); } } }, 'Save Runtime Settings')
    ]),
    card('Frontend / Model Defaults', [
      el('div', { class: 'row' }, [defaultProfile, defaultOrder, el('label', {}, [retain, ' Retain imported tag order by default'])]),
      el('div', { class: 'row' }, [el('label', {}, ['Tag text format ', tagTextMode]), el('span', { class: tagModeRestartNeeded ? 'badge failed' : 'badge ok' }, tagModeRestartNeeded ? 'restart required' : `active: ${s.tag_text_mode_active || 'underscores'}`)]),
      tagModeRestartNeeded ? el('div', { class: 'bad-panel' }, [
        el('strong', {}, 'Tag text format change is pending.'),
        el('p', { class: 'muted tiny' }, 'Press the red restart button to apply it immediately. Otherwise, the migration runs the next time you start the app. The startup migration updates tag dictionaries, aliases, implications, media tag rows, and .txt sidecars.'),
        el('button', { class: 'danger', onclick: async () => { try { await api('/api/system/restart', { method: 'POST', body: {} }); toast('Restart requested; the app will briefly disconnect.'); } catch (err) { toast(err.message, false); } } }, 'Restart Tool Now + Apply Tag Format')
      ]) : null,
      el('div', { class: 'row' }, [tagCount, temp, maxTokens, threshold]),
      el('div', { class: 'row' }, [defGpuIds, defShard, defDtype, defQuant]),
      el('button', { class: 'primary', onclick: async () => { try { const values = { default_tag_profile: defaultProfile.value, default_ordering_strategy: defaultOrder.value, retain_imported_tag_order: retain.checked, tag_text_mode: tagTextMode.value, tag_suggestion_count: Number(tagCount.value || 40), model_temperature: Number(temp.value || 0.2), model_max_new_tokens: Number(maxTokens.value || 512), classifier_threshold: Number(threshold.value || 0.35), default_model_device_ids: parseGpuIds(defGpuIds.value), default_model_sharding_strategy: defShard.value, default_model_sharding: defShard.value !== 'none', default_model_dtype: defDtype.value, default_model_quantization: defQuant.value }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); state.tagProfile = values.default_tag_profile; state.orderingStrategy = values.default_ordering_strategy; toast((state.settings.tag_text_mode_restart_required || state.settings.tag_text_mode !== state.settings.tag_text_mode_active) ? 'Default settings saved; restart required to apply tag text format.' : 'Default settings saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Defaults')
    ].filter(Boolean)),
    card('Assistant Thinking / Visible Planning Defaults', [
      el('p', { class: 'muted' }, 'Controls how assistant-capable models think longer. The app can run a separate user-visible planning pass before the final answer and raise token/continuation budgets. This does not expose provider/private hidden chain-of-thought.'),
      el('div', { class: 'row' }, [el('label', {}, ['thinking mode ', thinkMode]), el('label', {}, ['reasoning effort ', reasoningEffort]), el('label', {}, [showVisiblePlan, ' show visible plan/action notes']), el('label', {}, [showLiveActionNotes, ' show live action-notes overlay'])]),
      el('div', { class: 'row' }, [planningPasses, planMaxTokens, minChatTokens, deepChatTokens, maxReflect]),
      el('button', { class: 'primary', onclick: async () => { try { const values = { assistant_thinking_mode: thinkMode.value, assistant_reasoning_effort: reasoningEffort.value, assistant_show_visible_plan: showVisiblePlan.checked, assistant_show_live_action_notes: showLiveActionNotes.checked, assistant_planning_passes: Number(planningPasses.value || 0), assistant_plan_max_tokens: Number(planMaxTokens.value || 768), assistant_min_chat_tokens: Number(minChatTokens.value || 1024), assistant_deep_chat_tokens: Number(deepChatTokens.value || 4096), assistant_max_auto_reflection_rounds: Number(maxReflect.value || 0) }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); toast('Assistant thinking/planning defaults saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Thinking / Planning Defaults')
    ]),
    card('Model VRAM / Long Chat Memory Management', [
      el('p', { class: 'muted' }, 'Prevents long chat/inference sessions from gradually consuming VRAM with temporary CUDA allocations/KV cache. CPU offload keeps model objects in RAM and reactivates them on the selected GPU for the next request.'),
      el('div', { class: 'row' }, [el('label', {}, [vramCleanup, ' cleanup CUDA cache after inference']), el('label', {}, [vramAggressive, ' aggressive Python GC']), el('label', {}, [vramResetPeaks, ' reset peak CUDA stats']), el('label', {}, [vramAutoOffload, ' enable CPU offload policy'])]),
      el('div', { class: 'row' }, [el('label', {}, ['CPU offload policy ', vramOffloadPolicy]), vramOffloadThreshold, vramIdleSeconds]),
      el('div', { class: 'row' }, [el('label', { title: 'When estimated context pressure is high, pass use_cache=false to Transformers generation. This is slower, but can reduce temporary KV-cache VRAM spikes.' }, [vramDisableCache, ' disable generation KV cache under context pressure']), vramContextThreshold, el('label', {}, [vramDebug, ' debug cleanup snapshots'])]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary', onclick: async () => { try { state.vramCleanupResult = await api('/api/models/memory/cleanup', { method: 'POST', body: { offload_to_cpu: false } }); await refreshAll(); toast('CUDA cache cleanup requested'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Clean CUDA Cache Now'),
        el('button', { class: 'secondary', onclick: async () => { try { state.vramCleanupResult = await api('/api/models/memory/cleanup', { method: 'POST', body: { offload_to_cpu: true } }); await refreshAll(); toast('Loaded models moved to CPU RAM where supported'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Move Loaded Models to CPU RAM')
      ]),
      state.vramCleanupResult ? el('pre', { class: 'log tiny-log' }, JSON.stringify(state.vramCleanupResult, null, 2)) : null,
      el('button', { class: 'primary', onclick: async () => { try { const values = { model_vram_cleanup_after_inference: vramCleanup.checked, model_vram_aggressive_gc_after_inference: vramAggressive.checked, model_vram_reset_peak_stats_after_inference: vramResetPeaks.checked, model_vram_auto_cpu_offload_enabled: vramAutoOffload.checked, model_vram_auto_cpu_offload_policy: vramOffloadPolicy.value, model_vram_auto_cpu_offload_threshold: Number(vramOffloadThreshold.value || 0.82), model_vram_idle_cpu_offload_seconds: Number(vramIdleSeconds.value || 300), model_vram_disable_generation_cache_on_pressure: vramDisableCache.checked, model_vram_context_pressure_threshold: Number(vramContextThreshold.value || 0.70), model_vram_cleanup_debug: vramDebug.checked }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); toast('Model VRAM memory policy saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save VRAM Memory Policy')
    ].filter(Boolean)),
    card('Voice Input / Speech Output', [
      el('p', { class: 'muted' }, 'Push-to-record voice input lets you replace keyboard typing when chatting with LLM/VLM assistants. Click Start Voice in any assistant chat composer, click Stop & Transcribe, edit the generated text, then manually send it. TTS can optionally read assistant replies back through the selected output device.'),
      el('div', { class: 'row' }, [el('label', {}, [voiceSttEnabled, ' enable speech-to-text']), el('label', {}, ['STT model ', voiceSttModel]), el('label', {}, ['STT policy ', voiceSttPolicy]), el('label', {}, ['STT device ', voiceSttDevice]), voiceSttGpuIds, el('label', {}, ['dtype ', voiceSttDtype]), el('label', {}, ['quant ', voiceSttQuant]), voiceSttLang]),
      el('div', { class: 'row' }, [el('label', {}, [voiceTtsEnabled, ' enable text-to-speech']), el('label', {}, ['TTS model ', voiceTtsModel]), el('label', {}, ['TTS policy ', voiceTtsPolicy]), el('label', {}, ['TTS device ', voiceTtsDevice]), voiceTtsGpuIds, el('label', {}, ['dtype ', voiceTtsDtype]), el('label', {}, ['quant ', voiceTtsQuant]), voiceTtsLang, voiceTtsVoice, el('label', {}, [voiceTtsAuto, ' auto-speak assistant replies'])]),
      el('div', { class: 'row' }, [el('label', {}, [voiceTtsChunk, ' chunk/stitch long TTS text']), el('label', {}, ['max chars/chunk ', voiceTtsChunkChars]), el('label', {}, ['pause ms ', voiceTtsChunkPause]), el('span', { class: 'muted tiny' }, 'Chunking prevents Bark-like/local TTS models from reading only the first part of a long message.')]),
      el('div', { class: 'row' }, [el('label', {}, ['microphone ', voiceInDevice]), el('label', {}, ['speakers ', voiceOutDevice]), el('button', { class: 'secondary small', onclick: async () => { await refreshBrowserAudioDevices({ requestPermission: true }); toast('Browser audio devices refreshed'); render(true, true); } }, 'Refresh Browser Audio Devices')]),
      el('div', { class: 'row' }, [
        el('button', { class: 'secondary small', onclick: async () => { try { voiceSttEnabled.checked = true; await saveVoiceSettingsFromControls({ voice_stt_enabled: true }); await api('/api/voice/load', { method: 'POST', body: { kind: 'stt', model_name: voiceSttModel.value, device: voiceSttDevice.value, device_ids: parseGpuIds(voiceSttGpuIds.value), torch_dtype: voiceSttDtype.value, quantization: voiceSttQuant.value, runtime_engine: 'transformers' } }); await refreshAll(); toast('STT enabled and model loaded'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Enable + Load STT Now'),
        el('button', { class: 'secondary small', onclick: async () => { try { await api('/api/voice/unload', { method: 'POST', body: { kind: 'stt', model_name: voiceSttModel.value } }); await refreshAll(); toast('STT model unloaded'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Unload STT'),
        el('button', { class: 'secondary small', onclick: async () => { try { voiceTtsEnabled.checked = true; await saveVoiceSettingsFromControls({ voice_tts_enabled: true }); await api('/api/voice/load', { method: 'POST', body: { kind: 'tts', model_name: voiceTtsModel.value, device: voiceTtsDevice.value, device_ids: parseGpuIds(voiceTtsGpuIds.value), torch_dtype: voiceTtsDtype.value, quantization: voiceTtsQuant.value, runtime_engine: 'transformers' } }); await refreshAll(); toast('TTS enabled and model loaded'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Enable + Load TTS Now'),
        el('button', { class: 'secondary small', onclick: async () => { try { await api('/api/voice/unload', { method: 'POST', body: { kind: 'tts', model_name: voiceTtsModel.value } }); await refreshAll(); toast('TTS model unloaded'); render(true, true); } catch (err) { toast(err.message, false); } } }, 'Unload TTS'),
        el('button', { class: 'secondary small', onclick: async () => { try { voiceTtsEnabled.checked = true; await saveVoiceSettingsFromControls({ voice_tts_enabled: true }); await speakAssistantText('Voice output test from the Data Curation Tool assistant.', null, { force_enabled: true, voice_tts_enabled: true, model_name: voiceTtsModel.value, voice: voiceTtsVoice.value || 'af_heart', language: voiceTtsLang.value || null, device: voiceTtsDevice.value || 'auto', device_ids: parseGpuIds(voiceTtsGpuIds.value), torch_dtype: voiceTtsDtype.value || 'auto', quantization: voiceTtsQuant.value || 'none', load_policy: voiceTtsPolicy.value || 'on_demand', output_device_id: voiceOutDevice.value || '' }); } catch (err) { toast(err.message, false); } } }, 'Enable + Test TTS Output')
      ]),
      state.voiceStatus ? el('pre', { class: 'log tiny-log' }, JSON.stringify({ loaded: state.voiceStatus.settings?.loaded_voice_models, backend_devices: state.voiceStatus.backend }, null, 2)) : null,
      el('button', { class: 'primary', onclick: async () => { try { await saveVoiceSettingsFromControls(); toast('Voice STT/TTS settings saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Voice Settings')
    ].filter(Boolean)),
    card('Tag DB Exports Startup Sync', [el('p', { class: 'muted' }, 'For txt-only custom datasets, the app can load the selected booru DB exports tag table at startup so autocomplete and category colors are available before import.'), el('div', { class: 'row' }, [el('label', {}, [autoSyncStartup, ' Auto-sync tag DB exports on startup']), el('label', {}, [syncEmptyOnly, ' Legacy: sync only if dictionary is empty']), cacheHours]), el('button', { class: 'primary', onclick: async () => { try { const values = { auto_sync_tag_db_on_startup: autoSyncStartup.checked, tag_db_sync_if_empty_only: syncEmptyOnly.checked, tag_db_export_cache_hours: Number(cacheHours.value || 336) }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); toast('Tag DB sync settings saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Tag DB Sync Settings')]),
    card('Metadata / Media / Krita Defaults', [el('p', { class: 'muted' }, 'Controls the standalone generation-metadata parser, media extraction defaults, and Krita handoff paths.'), el('div', { class: 'row' }, [el('label', {}, [metaExtractImport, ' Extract embedded metadata during import']), el('label', {}, [metaApplyFallback, ' Use metadata when sidecars are missing']), metaTagSource, metaCaptionSource]), el('div', { class: 'row' }, [frameDir, audioDir]), el('div', { class: 'row' }, [kritaExe, kritaDir]), el('button', { class: 'primary', onclick: async () => { try { const values = { metadata_extract_on_import: metaExtractImport.checked, metadata_apply_when_no_sidecar: metaApplyFallback.checked, metadata_default_tag_source: metaTagSource.value, metadata_default_caption_source: metaCaptionSource.value, media_frame_output_dir: frameDir.value || null, audio_recording_dir: audioDir.value || null, krita_executable: kritaExe.value || null, krita_handoff_dir: kritaDir.value || null }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); toast('Metadata/media defaults saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Metadata / Media Defaults')]),
    card('FlexAvatar Optional Runtime', [
      el('p', { class: 'muted' }, 'FlexAvatar uses an isolated Conda environment because the upstream research stack targets Python 3.9 and CUDA 11.8. Source/workspace changes take effect after restarting the main app.'),
      el('div', { class: 'row' }, [flexEnv, flexConda, flexPython, flexDevice, flexTimeout]),
      el('div', { class: 'row' }, [flexSource, flexWorkspace, flexCheckpointUrl]),
      el('button', { class: 'primary', onclick: async () => { try { const values = { flexavatar_conda_env: flexEnv.value || 'dct-flexavatar', flexavatar_conda_executable: flexConda.value || null, flexavatar_python: flexPython.value || null, flexavatar_source_dir: flexSource.value || null, flexavatar_workspace_dir: flexWorkspace.value || null, flexavatar_default_device: flexDevice.value || 'cuda:0', flexavatar_job_timeout_seconds: Number(flexTimeout.value || 86400), flexavatar_checkpoint_url: flexCheckpointUrl.value || null }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); toast('FlexAvatar settings saved; restart for source/workspace changes'); render(); } catch (err) { toast(err.message, false); } } }, 'Save FlexAvatar Settings'),
      el('button', { class: 'secondary', onclick: () => setTab('FlexAvatar') }, 'Open FlexAvatar Tab')
    ]),
    card('Agent Tools Safety / Function-Calling Runtime', [
      el('p', { class: 'muted' }, 'Controls the human-approved tool runtime available from the Agent Tools tab and assistant panels in Tag Editor, Compare, Batch Tags, Assistant, and Code Assistant. Docker mode is optional and only used when Docker is installed.'),
      el('div', { class: 'row' }, [el('label', {}, [agentEnabled, ' enabled']), el('label', {}, [agentRequireApproval, ' require approval per action']), el('label', {}, [agentShell, ' shell/cmd/bash']), el('label', {}, [agentPython, ' Python scripts']), el('label', {}, [agentWrite, ' file writes']), el('label', {}, [agentBrowser, ' browser actions'])]),
      el('div', { class: 'row' }, [el('label', {}, [agentProfile, ' allow existing Firefox profile']), el('label', {}, [agentHighRisk, ' allow high-risk with confirmation']), el('label', {}, [agentAnyPath, ' allow any path']), el('label', { title: 'Required for the one-click Approve + Run COA Plan button. Individual per-step actions still use explicit approval.' }, [agentCoaExecution, ' enable approved COA execution']), el('label', {}, [agentAutoRelay, ' auto-relay after plan jobs']), el('label', {}, ['sandbox ', agentSandbox]), agentDockerImage]),
      el('div', { class: 'row' }, [el('label', {}, ['COA confirmation mode ', agentConfirmMode]), el('label', {}, [agentAutoRetry, ' auto re-attempt failed COAs']), el('label', {}, ['max re-attempts ', agentMaxRetries]), el('label', {}, [agentInfiniteRetries, ' experimental infinite re-attempts']), el('label', {}, [agentSpawnModels, ' orchestrator may spawn other models'])]),
      el('div', { class: 'row' }, [
        el('label', { title: 'When local tools are visible, the model must first decide whether this prompt needs no tool, an in-app GUI action, external tools, model delegation, or a mixed plan.' }, [agentModelDecidesTools, ' model decides if tools are needed']),
        el('label', { title: 'Allow normal chat/direct answers when no tool is necessary; do not force COAs for every prompt.' }, [agentPlainChatAllowed, ' allow no-tool/direct chat']),
        el('label', { title: 'Expose app_gui_action so the assistant can route app/GUI work separately from OS shell/Python commands.' }, [agentGuiRouting, ' enable app/GUI action routing']),
        el('label', { title: 'Show the model/tool-use decision badge on assistant responses and plan results.' }, [agentShowDecisionBadges, ' show tool-decision badges'])
      ]),
      el('div', { class: 'row' }, [agentWorkspace, agentBrowserProfile, agentTimeout, agentMaxTimeout, agentOutputChars, agentDefaultVenv]),
      el('div', { class: 'row' }, [el('label', {}, [agentSmoke, ' run tool smoke test at startup']), el('label', {}, [agentPipVenv, ' allow generated Python venv + pip installs'])]),
      agentAllowedRoots,
      el('button', { class: 'primary', onclick: async () => { try { const values = { agent_tools_enabled: agentEnabled.checked, agent_tools_require_approval: agentRequireApproval.checked, agent_tools_allow_shell: agentShell.checked, agent_tools_allow_python: agentPython.checked, agent_tools_allow_file_write: agentWrite.checked, agent_tools_allow_browser: agentBrowser.checked, agent_tools_allow_existing_browser_profile: agentProfile.checked, agent_tools_allow_high_risk: agentHighRisk.checked, agent_tools_allow_any_path: agentAnyPath.checked, agent_tools_enable_approved_coa_execution: agentCoaExecution.checked, agent_tools_auto_relay_after_execution: agentAutoRelay.checked, agent_tools_confirmation_mode: agentConfirmMode.value, agent_tools_auto_reattempt_enabled: agentAutoRetry.checked, agent_tools_max_reattempts: Number(agentMaxRetries.value || 0), agent_tools_allow_infinite_reattempts: agentInfiniteRetries.checked, agent_tools_orchestrator_can_spawn_models: agentSpawnModels.checked, agent_tools_model_decides_when_to_use_tools: agentModelDecidesTools.checked, agent_tools_allow_plain_chat_without_tools: agentPlainChatAllowed.checked, agent_tools_app_gui_action_routing: agentGuiRouting.checked, agent_tools_show_tool_decision_badges: agentShowDecisionBadges.checked, agent_tools_sandbox_mode: agentSandbox.value, agent_tools_docker_image: agentDockerImage.value || 'python:3.11-slim', agent_tools_workspace: agentWorkspace.value || null, agent_tools_allowed_roots: agentAllowedRoots.value.split(/\n+/).map(x => x.trim()).filter(Boolean), agent_tools_browser_profile_path: agentBrowserProfile.value || null, agent_tools_default_timeout_seconds: Number(agentTimeout.value || 120), agent_tools_max_timeout_seconds: Number(agentMaxTimeout.value || 1800), agent_tools_max_output_chars: Number(agentOutputChars.value || 120000), agent_tools_smoke_test_on_startup: agentSmoke.checked, agent_tools_allow_python_venv_install: agentPipVenv.checked, agent_tools_default_python_venv: agentDefaultVenv.value || 'agent-tools-default' }; state.settings = await api('/api/settings', { method: 'PUT', body: { values } }); state.agentStatus = await api('/api/agent-tools/status').catch(() => state.agentStatus); toast('Agent tool settings saved'); render(); } catch (err) { toast(err.message, false); } } }, 'Save Agent Tools Settings'),
      el('button', { class: 'secondary', onclick: () => setTab('Agent Tools') }, 'Open Agent Tools')
    ]),
    card('Devices', [el('button', { class: 'secondary', onclick: async () => { const d = await api('/api/system/devices'); toast('Device scan complete'); document.querySelector('#devicesOut').textContent = JSON.stringify(d, null, 2); } }, 'Detect Devices'), el('pre', { id: 'devicesOut', class: 'log' }, '')]),
    card('Settings JSON', [el('pre', { class: 'log' }, JSON.stringify(state.settings, null, 2))])
  ]);
}


function showFatalFrontendError(err, secondary = null) {
  try {
    const app = document.getElementById('app');
    if (!app) return;
    const detail = [err, secondary]
      .filter(Boolean)
      .map(value => String(value && value.stack ? value.stack : value))
      .join('\n\n--- secondary error ---\n\n');
    const section = document.createElement('section');
    section.className = 'card frontend-fatal';
    const h = document.createElement('h2');
    h.textContent = 'Frontend failed to render';
    const p = document.createElement('p');
    p.className = 'muted';
    p.textContent = 'The backend is running, but the browser UI hit a JavaScript startup/render error. Copy this message if you need to report it.';
    const row = document.createElement('div');
    row.className = 'row';
    const reload = document.createElement('button');
    reload.className = 'secondary';
    reload.textContent = 'Reload Page';
    reload.addEventListener('click', () => window.location.reload());
    const copy = document.createElement('button');
    copy.className = 'secondary';
    copy.textContent = 'Copy Error';
    copy.addEventListener('click', async () => {
      try { await navigator.clipboard?.writeText(detail); } catch (_) {}
    });
    row.append(reload, copy);
    const pre = document.createElement('pre');
    pre.className = 'log full-log debug-log';
    pre.textContent = detail || 'Unknown frontend startup error';
    section.append(h, p, row, pre);
    app.replaceChildren(section);
  } catch (fatal) {
    console.error('Failed to display frontend fatal error', fatal, err, secondary);
  }
}

function lastApiErrorCard() {
  if (!state.lastApiError) return null;
  return card('Last API / Inference Error Details', [
    el('p', { class: 'muted' }, 'Full local error details are shown here so failed VLM/LLM calls and server errors can be copied without relying on the short toast message.'),
    el('div', { class: 'row' }, [
      el('span', { class: 'badge bad' }, `${state.lastApiError.status || ''} ${state.lastApiError.statusText || ''}`.trim() || 'error'),
      el('span', { class: 'muted tiny' }, `${state.lastApiError.method || 'GET'} ${state.lastApiError.path || ''} · ${state.lastApiError.when || state.lastApiError.time || ''}`),
      el('button', { class: 'secondary small', onclick: async () => { await navigator.clipboard?.writeText(JSON.stringify(state.lastApiError, null, 2)); toast('Copied last API error details'); } }, 'Copy Error Details'),
      el('button', { class: 'secondary small', onclick: () => { state.lastApiError = null; render(); } }, 'Clear Error')
    ]),
    el('pre', { class: 'log full-log' }, state.lastApiError.detail || JSON.stringify(state.lastApiError, null, 2))
  ]);
}

function jobsView() {
  const jobsLive = el('input', { type: 'checkbox', checked: state.jobsAutoRefresh !== false, onchange: e => { state.jobsAutoRefresh = e.target.checked; } });
  return el('div', { class: 'grid' }, [
    card('Jobs', [
      el('div', { class: 'row' }, [
        el('label', {}, [jobsLive, ' Live job refresh']),
        el('button', { class: 'secondary', onclick: async () => { state.jobs = await api('/api/jobs'); render(true, true); } }, 'Refresh Jobs'),
        el('button', { class: 'secondary', onclick: async () => { await api('/api/jobs/clear', { method: 'POST', body: { statuses: ['completed'] } }); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Completed'),
        el('button', { class: 'secondary', onclick: async () => { await api('/api/jobs/clear', { method: 'POST', body: { statuses: ['failed'] } }); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Failed'),
        el('button', { class: 'secondary', onclick: async () => { await api('/api/jobs/clear', { method: 'POST', body: { statuses: ['queued'] } }); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Queued'),
        el('button', { class: 'danger', onclick: async () => { const r = await api('/api/jobs/cancel', { method: 'POST', body: { download_only: true, include_running: true } }); state.jobs = await api('/api/jobs'); toast(`Cancelled/requested stop for ${r.count || 0} download job(s)`); render(); } }, 'Stop Queued/Running Downloads'),
        el('button', { class: 'danger', onclick: async () => { if (!confirm('Clear all non-running jobs?')) return; await api('/api/jobs/clear', { method: 'POST', body: { clear_all: true, include_running: false } }); state.jobs = await api('/api/jobs'); render(); } }, 'Clear All Non-running'),
        el('button', { class: 'danger', onclick: async () => { if (!confirm('Clear every job record, including running jobs? This does not kill an external process, but it clears stuck records.')) return; await api('/api/jobs/clear', { method: 'POST', body: { clear_all: true, include_running: true } }); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Absolutely All')
      ]),
      jobsTable(100, true)
    ]),
    errorLogCard('Last API / Model Error Details')
  ].filter(Boolean));
}

function jobDownloadSizeBadge(j) {
  const params = j?.params || j?.parameters || {};
  const est = params.size_estimate || {};
  const remaining = Number(params.estimated_remaining_gb ?? est.estimated_remaining_gb ?? NaN);
  const total = Number(params.estimated_total_gb ?? est.estimated_total_gb ?? est.size_gb ?? NaN);
  if (!Number.isFinite(remaining) && !Number.isFinite(total)) return null;
  const parts = [];
  if (Number.isFinite(remaining)) parts.push(`~${remaining.toFixed(2)}GB left`);
  if (Number.isFinite(total)) parts.push(`${total.toFixed(2)}GB total`);
  return el('div', { class: 'muted tiny', title: 'Approximate model-download size estimate for disk planning.' }, parts.join(' · '));
}

function jobsTable(limit = 100, selectable = false) {
  const rows = (state.jobs || []).slice(0, limit);
  if (!state.jobSelections) state.jobSelections = new Set();
  const selected = state.jobSelections;
  const detailJob = rows.find(j => j.id === state.jobDetailId) || (state.jobs || []).find(j => j.id === state.jobDetailId);
  const isRetryableJob = j => ['failed', 'cancelled', 'canceled'].includes(String(j.status || '').toLowerCase()) && (String(j.type || '').toLowerCase().includes('download') || String(j.type || '').toLowerCase().startsWith('tag_dictionary') || String(j.type || '').toLowerCase().startsWith('db_export'));
  const retryJobs = async ids => {
    const retryIds = (ids || []).map(Number).filter(Boolean);
    if (!retryIds.length) { toast('Select one or more failed/cancelled download jobs first.', false); return; }
    const r = await api('/api/jobs/retry', { method: 'POST', body: { job_ids: retryIds, failed_only: true, force_download: true } });
    retryIds.forEach(id => selected.delete(id));
    state.jobs = await api('/api/jobs');
    toast(`Requeued ${r.count || 0} job(s)` + ((r.skipped || []).length ? `; skipped ${(r.skipped || []).length}` : ''));
    render();
  };
  const table = el('table', { class: 'table' }, [
    el('thead', {}, el('tr', {}, [selectable ? el('th', {}, 'Pick') : null, ...['ID', 'Type', 'Status', 'Progress', 'Message / Full Details'].map(h => el('th', {}, h))].filter(Boolean))),
    el('tbody', {}, rows.map(j => {
      const jobId = Number(j.id);
      const rememberJobPick = e => { if (e.target.checked) selected.add(jobId); else selected.delete(jobId); };
      const cb = el('input', { type: 'checkbox', 'data-no-persist': '1', checked: selected.has(jobId), onchange: rememberJobPick, oninput: rememberJobPick, onclick: rememberJobPick });
      const message = j.error ? String(j.error).slice(0, 260) : (j.message || '');
      const actions = [el('button', { class: 'secondary small', onclick: async () => { state.jobDetailId = jobId; state.jobDetails[String(jobId)] = await api(`/api/jobs/${jobId}`).catch(() => j); render(); } }, 'View full log')];
      if (j.error) actions.push(el('button', { class: 'secondary small', onclick: async () => copyText(j.error, 'Copied job error') }, 'Copy Error'));
      if (isRetryableJob(j)) actions.push(el('button', { class: 'secondary small', onclick: async () => retryJobs([jobId]) }, 'Retry from scratch'));
      return el('tr', {}, [
        selectable ? el('td', {}, cb) : null,
        el('td', {}, j.id), el('td', {}, [j.type, jobDownloadSizeBadge(j)].filter(Boolean)), el('td', { 'data-job-status-id': jobId }, j.status),
        el('td', {}, el('div', { class: 'progress' }, el('span', { 'data-job-progress-id': jobId, style: `width:${Math.round((j.progress || 0) * 100)}%` }))),
        el('td', {}, [el('div', { class: j.error ? 'bad-text' : '', 'data-job-message-id': jobId }, message), el('div', { class: 'row' }, actions)])
      ].filter(Boolean));
    }))
  ]);
  const freshDetail = detailJob && (state.jobDetails[String(detailJob.id)] || detailJob);
  const detailText = freshDetail ? JSON.stringify(freshDetail, null, 2) : '';
  const detail = freshDetail ? card(`Full Job #${freshDetail.id} Details`, [
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => { state.jobDetails[String(freshDetail.id)] = await api(`/api/jobs/${freshDetail.id}`).catch(() => freshDetail); render(); } }, 'Refresh This Log'),
      el('button', { class: 'secondary', onclick: async () => copyText(detailText, 'Copied full job details') }, 'Copy Full Details'),
      el('button', { class: 'secondary', onclick: () => downloadTextFile(`dct-job-${freshDetail.id}.json`, detailText) }, 'Download Log File'),
      el('button', { class: 'secondary', onclick: () => { state.jobDetailId = null; render(); } }, 'Hide Details')
    ]),
    el('pre', { class: 'log full-log' }, detailText)
  ]) : null;
  if (!selectable) return el('div', {}, [table, detail]);
  return el('div', {}, [
    el('div', { class: 'row' }, [
      el('button', { class: 'secondary', onclick: async () => { const ids = rows.map(j => Number(j.id)); await api('/api/jobs/clear', { method: 'POST', body: { job_ids: ids, include_running: false } }); ids.forEach(id => selected.delete(id)); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Visible Non-running'),
      el('button', { class: 'secondary', onclick: async () => { const ids = [...selected]; await api('/api/jobs/clear', { method: 'POST', body: { job_ids: ids, include_running: false } }); ids.forEach(id => selected.delete(id)); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Checked Non-running'),
      el('button', { class: 'secondary', onclick: async () => { await retryJobs([...selected]); } }, 'Retry Checked Failed Downloads'),
      el('button', { class: 'secondary', onclick: () => { rows.forEach(j => selected.add(Number(j.id))); render(); } }, 'Select Visible'),
      el('button', { class: 'secondary', onclick: () => { selected.clear(); render(); } }, 'Deselect Jobs'),
      el('button', { class: 'secondary', onclick: async () => { const ids = [...selected]; if (!ids.length) { toast('Check one or more running/queued jobs first.', false); return; } const r = await api('/api/jobs/pause', { method: 'POST', body: { job_ids: ids, include_running: true } }); state.jobs = await api('/api/jobs'); toast(`Paused/requested pause for ${r.count || 0} checked job(s)`); render(); } }, 'Pause Checked'),
      el('button', { class: 'secondary', onclick: async () => { const ids = [...selected]; if (!ids.length) { toast('Check one or more paused jobs first.', false); return; } const r = await api('/api/jobs/resume', { method: 'POST', body: { job_ids: ids } }); state.jobs = await api('/api/jobs'); toast(`Resumed ${r.count || 0} checked job(s)`); render(); } }, 'Resume Checked'),
      el('button', { class: 'secondary', onclick: async () => { const r = await api('/api/jobs/pause', { method: 'POST', body: { download_only: true, include_running: true } }); state.jobs = await api('/api/jobs'); toast(`Paused/requested pause for ${r.count || 0} download job(s)`); render(); } }, 'Pause Downloads'),
      el('button', { class: 'secondary', onclick: async () => { const r = await api('/api/jobs/resume', { method: 'POST', body: { download_only: true } }); state.jobs = await api('/api/jobs'); toast(`Resumed ${r.count || 0} paused download job(s)`); render(); } }, 'Resume Downloads'),
      el('button', { class: 'danger', onclick: async () => { const ids = [...selected]; if (!ids.length) { toast('Check one or more queued/running/paused jobs first.', false); return; } const r = await api('/api/jobs/cancel', { method: 'POST', body: { job_ids: ids, include_running: true } }); ids.forEach(id => selected.delete(id)); state.jobs = await api('/api/jobs'); toast(`Cancelled/requested stop for ${r.count || 0} checked job(s)`); render(); } }, 'Stop Checked Jobs'),
      el('button', { class: 'danger', onclick: async () => { if (!confirm('Clear checked job records including running?')) return; const ids = [...selected]; await api('/api/jobs/clear', { method: 'POST', body: { job_ids: ids, include_running: true } }); ids.forEach(id => selected.delete(id)); state.jobs = await api('/api/jobs'); render(); } }, 'Clear Checked Any Status')
    ]),
    table,
    detail
  ]);
}

function render(shouldSnapshot = true, force = false) {
  if (!force && shouldSnapshot && shouldDeferControlRender()) {
    state.renderDeferredForEditing = true;
    return false;
  }
  const tab = state.tab;
  const focusSnapshot = shouldSnapshot ? activeControlSnapshot(tab) : null;
  if (shouldSnapshot) {
    snapshotFormState(tab);
    snapshotScrollState(tab);
  }
  const views = { Dashboard: dashboard, Import: importView, Gallery: galleryView, 'Tag Editor': tagEditorView, 'Detection & Boxes': detectionEditorView, 'Segmentation & Masks': segmentationEditorView, 'Pose & 3D': poseEditorView, '3D Studio': threeDStudioView, '3D Viewport': threeDViewportView, 'ComfyUI Bridge': comfyBridgeView, FlexAvatar: flexAvatarView, 'Annotation Editor': detectionEditorView, Compare: compareView, 'Batch Tags': batchTagsView, 'Prediction Analytics': predictionAnalyticsView, 'Media Tools': mediaToolsView, 'Reference Finder': referenceFinderView, 'Source Browser': sourceBrowserView, Assistant: assistantView, Orchestrate: orchestrationView, Models: modelsView, Augment: augmentView, Downloads: downloadsView, Presets: presetsView, 'Tag Dictionaries': dictionaryView, Database: databaseView, 'Install Migration': migrationView, 'Code Assistant': codeAssistantView, 'Agent Tools': agentToolsView, 'MCP Tools': mcpToolsView, 'Future Modalities': futureModalitiesView, Settings: settingsView, 'Help & Workflows': helpWorkflowsView, Jobs: jobsView };
  try {
    document.getElementById('app').replaceChildren(shell((views[tab] || dashboard)()));
    if (typeof window !== 'undefined') window.__DCT_APP_RENDERED = true;
    restoreFormState(tab);
    restoreActiveControl(focusSnapshot, tab);
    restoreScrollState(tab);
  } catch (err) {
    console.error(err);
    try {
      document.getElementById('app').replaceChildren(shell(el('section', { class: 'card' }, [el('h2', {}, `${tab} failed to render`), el('pre', { class: 'log' }, String(err && err.stack ? err.stack : err))])));
      if (typeof window !== 'undefined') window.__DCT_APP_RENDERED = true;
    } catch (fatal) {
      showFatalFrontendError(fatal, err);
    }
    restoreActiveControl(focusSnapshot, tab);
    restoreScrollState(tab);
  }
}

async function boot() {
  await refreshAll();
  await Promise.all([loadMedia().catch(() => {}), loadDictionaryStatus().catch(() => {})]);
  render();
  state.lastCompletedModelJobIds = new Set((state.jobs || []).filter(isCompletedModelJob).map(j => j.id));
  setInterval(async () => {
    const [jobs, modelStatuses] = await Promise.all([
      api('/api/jobs').catch(() => state.jobs),
      api('/api/models/status').catch(() => state.modelStatuses)
    ]);
    const oldById = new Map((state.jobs || []).map(j => [j.id, j.status]));
    const completedModelJobs = (jobs || []).filter(j => isCompletedModelJob(j) && (oldById.get(j.id) !== j.status || !state.lastCompletedModelJobIds.has(j.id)));
    const completedDownloadLike = (jobs || []).filter(j => {
      const type = String(j.type || '');
      return j.status === 'completed' && oldById.get(j.id) !== j.status && (type.includes('download') || type.includes('tag_dictionary') || type.includes('db_export') || type.includes('migration'));
    });
    if (completedModelJobs.length) invalidateTagScoreCache();
    state.jobs = jobs;
    state.modelStatuses = modelStatuses || state.modelStatuses;
    if (state.modelStatuses?.placement) state.modelResource = state.modelStatuses.placement;
    const mediaRefreshed = await refreshMediaAfterCompletedModelJobs(completedModelJobs).catch(err => { console.warn('model media refresh failed', err); return false; });
    for (const job of completedModelJobs) state.lastCompletedModelJobIds.add(job.id);
    const modelRelatedTabs = ['Models', 'Tag Editor', 'Batch Tags', 'Compare', 'Assistant', 'Orchestrate', 'Jobs', 'Install Migration'];
    const modelJobChanged = (jobs || []).some(j => {
      const type = String(j.type || '');
      return (type.startsWith('model_') || type.includes('model_download') || type.includes('annotation_model')) && oldById.get(j.id) !== j.status;
    });
    const shouldRefreshModelList = modelRelatedTabs.includes(state.tab) && (modelJobChanged || completedDownloadLike.length || Date.now() - Number(state.lastModelListRefreshAt || 0) > 12000);
    if (shouldRefreshModelList) {
      const [models, assistantConfig, resource] = await Promise.all([
        api('/api/models').catch(() => state.models || []),
        api('/api/models/assistant-config').catch(() => state.assistantConfig),
        api('/api/models/resource-status').catch(() => state.modelResource)
      ]);
      state.models = models || state.models || [];
      state.assistantConfig = assistantConfig || state.assistantConfig;
      state.modelResource = resource || state.modelResource;
      state.lastModelListRefreshAt = Date.now();
    }
    updateLiveStatusDom();
    const jobsFingerprint = JSON.stringify((jobs || []).slice(0, 150).map(j => [j.id, j.type, j.status, Math.round(Number(j.progress || 0) * 100), j.message || '', Boolean(j.error)]));
    const modelFingerprint = JSON.stringify({ aggregate: state.modelStatuses?.aggregate || {}, loaded: (state.models || []).filter(m => m.loaded).map(m => m.name).sort(), downloaded: (state.models || []).filter(m => m.downloaded).map(m => m.name).sort(), selected: state.modelRunSelection || '', tagSelection: state.tagSelectionModelSelection || '', quick: state.quickModelSelection || '', assistant: state.assistantModelSelection || '' });
    const jobsChanged = jobsFingerprint !== state.lastJobsFingerprint;
    const modelsChanged = modelFingerprint !== state.lastModelStatusFingerprint;
    state.lastJobsFingerprint = jobsFingerprint;
    state.lastModelStatusFingerprint = modelFingerprint;
    const renderTabs = ['Dashboard', 'Tag Editor', 'Batch Tags', 'Compare', 'Annotation Editor', 'Detection & Boxes', 'Segmentation & Masks', 'Pose & 3D'];
    let shouldRender = renderTabs.includes(state.tab);
    if (state.tab === 'Jobs') shouldRender = state.jobsAutoRefresh !== false && jobsChanged;
    if (state.tab === 'Models') shouldRender = state.modelsAutoRefresh !== false && (modelsChanged || shouldRefreshModelList);
    if (shouldRender || mediaRefreshed || (shouldRefreshModelList && state.tab !== 'Gallery')) renderOrDeferForEditing();
  }, 3000);
}
boot().catch(err => showFatalFrontendError(err));

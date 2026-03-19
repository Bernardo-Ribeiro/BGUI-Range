const {
  DEFAULT_FONT_BASE,
  DEFAULT_THEME_CANDIDATES,
  PY_WIDGET_DEFAULTS,
  REQUIRED_ATTRS
} = window.UI_BUILDER_CONSTANTS;

const widgets = [];
let editingWidgetId = null;
let loadedTheme = null;
let loadedThemeName = 'internal fallback';
let currentXmlFileName = 'interface.xml';
let xmlFileHandle = null;
const fontFamilyByFile = {};
const registeredFontUrls = new Set();
const STORAGE_KEY = 'bgui_xml_builder_state_v1';
const HANDLE_DB_NAME = 'bgui_xml_builder_db';
const HANDLE_STORE_NAME = 'file_handles';
const HANDLE_XML_KEY = 'current_xml_file_handle';

const dynamicFontStyle = document.createElement('style');
dynamicFontStyle.id = 'dynamicThemeFonts';
document.head.appendChild(dynamicFontStyle);

const refs = {
  type: document.getElementById('widgetType'),
  name: document.getElementById('widgetName'),
  parent: document.getElementById('widgetParent'),
  text: document.getElementById('widgetText'),
  pos: document.getElementById('widgetPos'),
  size: document.getElementById('widgetSize'),
  ptSize: document.getElementById('widgetPt'),
  color: document.getElementById('widgetColor'),
  minValue: document.getElementById('widgetMin'),
  maxValue: document.getElementById('widgetMax'),
  value: document.getElementById('widgetValue'),
  percent: document.getElementById('widgetPercent'),
  subTheme: document.getElementById('widgetSubTheme'),
  extra: document.getElementById('widgetExtra'),
  list: document.getElementById('widgetList'),
  output: document.getElementById('xmlOutput'),
  xmlFileInput: document.getElementById('xmlFileInput'),
  status: document.getElementById('status'),
  previewStage: document.getElementById('previewStage'),
  themeFileInput: document.getElementById('themeFileInput'),
  themeInfo: document.getElementById('themeInfo'),
  themeFontBaseInput: document.getElementById('themeFontBaseInput')
};

const controls = {
  add: document.getElementById('addWidgetBtn'),
  cancelEdit: document.getElementById('cancelEditBtn'),
  saveXml: document.getElementById('saveXmlBtn'),
  generate: document.getElementById('generateXmlBtn'),
  copy: document.getElementById('copyXmlBtn'),
  download: document.getElementById('downloadXmlBtn'),
  clear: document.getElementById('clearWidgetsBtn'),
  loadXml: document.getElementById('loadXmlBtn'),
  loadDefaultTheme: document.getElementById('loadDefaultThemeBtn')
};

const KNOWN_ATTR_FIELDS = [
  'text',
  'pos',
  'size',
  'pt_size',
  'color',
  'min_value',
  'max_value',
  'value',
  'percent',
  'sub_theme'
];

function findWidgetById(id) {
  return widgets.find(w => w.id === id) || null;
}

function knownAndExtraAttrs(attrs) {
  const known = {};
  const extra = {};
  for (const [k, v] of Object.entries(attrs || {})) {
    if (KNOWN_ATTR_FIELDS.includes(k)) {
      known[k] = v;
    } else {
      extra[k] = v;
    }
  }
  return { known, extra };
}

function extraAttrsToInput(extraAttrs) {
  const pairs = [];
  for (const [k, v] of Object.entries(extraAttrs || {})) {
    pairs.push(`${k}=${v}`);
  }
  return pairs.join(';');
}

function setEditMode(enabled) {
  if (enabled) {
    controls.add.textContent = 'Save changes';
    controls.cancelEdit.style.display = '';
  } else {
    controls.add.textContent = 'Add widget';
    controls.cancelEdit.style.display = 'none';
  }
}

function exitEditMode(clearInspector = false) {
  editingWidgetId = null;
  setEditMode(false);
  if (clearInspector) {
    clearForm();
  }
}

function enterEditMode(widgetId) {
  const widget = findWidgetById(widgetId);
  if (!widget) {
    return;
  }

  editingWidgetId = widget.id;
  setEditMode(true);

  const split = knownAndExtraAttrs(widget.attrs);
  refs.type.value = widget.type;
  refs.name.value = widget.name || '';
  refs.parent.value = widget.parent || '';

  refs.text.value = split.known.text || '';
  refs.pos.value = split.known.pos || '';
  refs.size.value = split.known.size || '';
  refs.ptSize.value = split.known.pt_size || '';
  refs.color.value = split.known.color || '';
  refs.minValue.value = split.known.min_value || '';
  refs.maxValue.value = split.known.max_value || '';
  refs.value.value = split.known.value || '';
  refs.percent.value = split.known.percent || '';
  refs.subTheme.value = split.known.sub_theme || '';
  refs.extra.value = extraAttrsToInput(split.extra);

  syncDefaultHintsForType();
  setStatus(`Editing widget: ${widget.name}`, 'ok');
}

function makeUniqueName(baseName, usedNames) {
  const base = (baseName && String(baseName).trim()) ? String(baseName).trim() : 'widget';
  if (!usedNames.has(base)) {
    usedNames.add(base);
    return base;
  }

  let i = 1;
  let candidate = `${base}_${i}`;
  while (usedNames.has(candidate)) {
    i += 1;
    candidate = `${base}_${i}`;
  }
  usedNames.add(candidate);
  return candidate;
}

function openHandleDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(HANDLE_DB_NAME, 1);

    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(HANDLE_STORE_NAME)) {
        db.createObjectStore(HANDLE_STORE_NAME);
      }
    };

    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function saveXmlHandleToDb(handle) {
  try {
    if (!handle) {
      return;
    }

    const db = await openHandleDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE_NAME, 'readwrite');
      tx.objectStore(HANDLE_STORE_NAME).put(handle, HANDLE_XML_KEY);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
    db.close();
  } catch {
    // Ignore handle persistence errors.
  }
}

async function clearXmlHandleFromDb() {
  try {
    const db = await openHandleDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE_NAME, 'readwrite');
      tx.objectStore(HANDLE_STORE_NAME).delete(HANDLE_XML_KEY);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
    db.close();
  } catch {
    // Ignore handle cleanup errors.
  }
}

async function loadXmlHandleFromDb() {
  try {
    const db = await openHandleDb();
    const handle = await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE_NAME, 'readonly');
      const req = tx.objectStore(HANDLE_STORE_NAME).get(HANDLE_XML_KEY);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
    db.close();
    return handle;
  } catch {
    return null;
  }
}

async function ensureReadWritePermission(handle) {
  if (!handle || !handle.queryPermission || !handle.requestPermission) {
    return false;
  }

  const options = { mode: 'readwrite' };
  if (await handle.queryPermission(options) === 'granted') {
    return true;
  }
  if (await handle.requestPermission(options) === 'granted') {
    return true;
  }
  return false;
}

function saveStateToStorage() {
  try {
    const payload = {
      widgets,
      themeFontBase: refs.themeFontBaseInput.value || '',
      output: refs.output.value || '',
      currentXmlFileName
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage failures (quota/private mode).
  }
}

function restoreStateFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return false;
    }

    const parsed = JSON.parse(raw);
    if (!parsed || !Array.isArray(parsed.widgets)) {
      return false;
    }

    widgets.length = 0;
    for (const w of parsed.widgets) {
      if (!w || !w.type || !w.name) {
        continue;
      }
      widgets.push({
        id: w.id || crypto.randomUUID(),
        type: String(w.type),
        name: String(w.name),
        parent: w.parent ? String(w.parent) : '',
        attrs: (w.attrs && typeof w.attrs === 'object') ? w.attrs : {}
      });
    }

    if (parsed.themeFontBase && String(parsed.themeFontBase).trim()) {
      refs.themeFontBaseInput.value = String(parsed.themeFontBase).trim();
    }

    if (parsed.currentXmlFileName && String(parsed.currentXmlFileName).trim()) {
      currentXmlFileName = String(parsed.currentXmlFileName).trim();
    }

    renderWidgetList();
    renderPreview();
    refs.output.value = parsed.output && String(parsed.output).trim() ? String(parsed.output) : generateXml();
    setStatus(`State restored (${widgets.length} widgets).`, 'ok');
    return true;
  } catch {
    return false;
  }
}

function importWidgetsFromXmlText(xmlText, sourceLabel = 'arquivo XML', fileName = 'interface.xml') {
  let root;
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlText, 'text/xml');
    const parseError = doc.querySelector('parsererror');
    if (parseError) {
      setStatus('Invalid XML: parse error.', 'error');
      return;
    }
    root = doc.documentElement;
  } catch {
    setStatus('Failed to read XML.', 'error');
    return;
  }

  if (!root) {
    setStatus('XML has no root element.', 'error');
    return;
  }

  const usedNames = new Set();
  const imported = [];

  function visitElement(elem, parentName = '') {
    const type = elem.tagName;
    const attrs = {};
    let rawName = '';

    for (const attr of Array.from(elem.attributes)) {
      if (attr.name === 'name') {
        rawName = attr.value;
      } else {
        attrs[attr.name] = attr.value;
      }
    }

    const generatedBase = type ? type.toLowerCase() : 'widget';
    const name = makeUniqueName(rawName || generatedBase, usedNames);

    imported.push({
      id: crypto.randomUUID(),
      type,
      name,
      parent: parentName,
      attrs
    });

    for (const child of Array.from(elem.children)) {
      visitElement(child, name);
    }
  }

  if (root.tagName === 'UI') {
    for (const child of Array.from(root.children)) {
      visitElement(child, '');
    }
  } else {
    visitElement(root, '');
  }

  widgets.length = 0;
  for (const w of imported) {
    widgets.push(w);
  }

  currentXmlFileName = fileName || 'interface.xml';
  exitEditMode(true);
  renderWidgetList();
  renderPreview();
  refs.output.value = generateXml();
  saveStateToStorage();
  setStatus(`XML loaded: ${sourceLabel} (${imported.length} widgets).`, 'ok');
}

function setStatus(message, type = '') {
  refs.status.textContent = message;
  refs.status.className = `status ${type}`.trim();
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function parseExtraAttributes(extraRaw) {
  const out = {};
  if (!extraRaw.trim()) {
    return out;
  }

  const pairs = extraRaw.split(';').map(v => v.trim()).filter(Boolean);
  for (const pair of pairs) {
    const idx = pair.indexOf('=');
    if (idx <= 0) {
      continue;
    }
    const key = pair.slice(0, idx).trim();
    const value = pair.slice(idx + 1).trim();
    if (key) {
      out[key] = value;
    }
  }
  return out;
}

function getWidgetDefaults(type) {
  return PY_WIDGET_DEFAULTS[type] || {};
}

function getAttrRaw(widget, key) {
  return widget && widget.attrs && widget.attrs[key] !== undefined ? String(widget.attrs[key]).trim() : '';
}

function getEffectiveAttr(widget, key) {
  const raw = getAttrRaw(widget, key);
  if (raw !== '') {
    return raw;
  }
  const defaults = getWidgetDefaults(widget.type);
  return defaults[key] !== undefined ? String(defaults[key]) : '';
}

function getDefaultLabel(type) {
  const defaults = getWidgetDefaults(type);
  const pieces = [];
  if (defaults.pos !== undefined) {
    pieces.push(`pos=${defaults.pos}`);
  }
  if (defaults.size !== undefined) {
    pieces.push(`size=${defaults.size}`);
  }
  if (defaults.percent !== undefined) {
    pieces.push(`percent=${defaults.percent}`);
  }
  if (defaults.value !== undefined) {
    pieces.push(`value=${defaults.value}`);
  }
  return pieces.length ? pieces.join(' | ') : 'no explicit defaults in constructor';
}

function syncDefaultHintsForType() {
  const type = refs.type.value;
  const defaults = getWidgetDefaults(type);

  refs.pos.placeholder = `ex: ${defaults.pos !== undefined ? defaults.pos : '0,0'}`;
  refs.size.placeholder = `ex: ${defaults.size !== undefined ? defaults.size : '1,1'}`;
  refs.value.placeholder = `ex: ${defaults.value !== undefined ? defaults.value : '0'}`;
  refs.minValue.placeholder = `ex: ${defaults.min_value !== undefined ? defaults.min_value : '0'}`;
  refs.maxValue.placeholder = `ex: ${defaults.max_value !== undefined ? defaults.max_value : '1'}`;
  refs.percent.placeholder = `ex: ${defaults.percent !== undefined ? defaults.percent : '1.0'}`;

  if (!refs.status.textContent || refs.status.classList.contains('ok')) {
    setStatus(`Python defaults for ${type}: ${getDefaultLabel(type)}.`, 'ok');
  }
}

function validateRequiredAttributes(type, attrs) {
  const required = REQUIRED_ATTRS[type] || [];
  if (!required.length) {
    return true;
  }

  for (const key of required) {
    const raw = attrs[key] !== undefined ? String(attrs[key]).trim() : '';
    if (!raw) {
      setStatus(`Widget ${type} requires attribute ${key}. Fill it in extra attributes (ex: ${key}=file).`, 'error');
      return false;
    }
  }
  return true;
}

function collectFormData(existingWidgetId = null) {
  const name = refs.name.value.trim();
  if (!name) {
    setStatus('Enter the widget name.', 'error');
    return null;
  }
  if (widgets.some(w => w.name === name && w.id !== existingWidgetId)) {
    setStatus(`A widget named "${name}" already exists.`, 'error');
    return null;
  }

  const current = existingWidgetId ? findWidgetById(existingWidgetId) : null;

  const data = {
    id: current ? current.id : crypto.randomUUID(),
    type: refs.type.value,
    name,
    parent: refs.parent.value || '',
    attrs: {
      text: refs.text.value.trim(),
      pos: refs.pos.value.trim(),
      size: refs.size.value.trim(),
      pt_size: refs.ptSize.value.trim(),
      color: refs.color.value.trim(),
      min_value: refs.minValue.value.trim(),
      max_value: refs.maxValue.value.trim(),
      value: refs.value.value.trim(),
      percent: refs.percent.value.trim(),
      sub_theme: refs.subTheme.value.trim(),
      ...parseExtraAttributes(refs.extra.value)
    }
  };

  if (!validateRequiredAttributes(data.type, data.attrs)) {
    return null;
  }

  if (data.parent && data.parent === name) {
    setStatus('A widget cannot be its own parent.', 'error');
    return null;
  }

  return data;
}

function clearForm() {
  refs.name.value = '';
  refs.text.value = '';
  refs.pos.value = '';
  refs.size.value = '';
  refs.ptSize.value = '';
  refs.color.value = '';
  refs.minValue.value = '';
  refs.maxValue.value = '';
  refs.value.value = '';
  refs.percent.value = '';
  refs.subTheme.value = '';
  refs.extra.value = '';
  refs.name.focus();
}

function getAttributePairs(widget) {
  const pairs = [['name', widget.name]];
  for (const [k, v] of Object.entries(widget.attrs)) {
    if (v !== '' && v !== null && v !== undefined) {
      pairs.push([k, v]);
    }
  }
  return pairs;
}

function renderWidgetList() {
  refs.list.innerHTML = '';
  for (let i = 0; i < widgets.length; i += 1) {
    const widget = widgets[i];
    const el = document.createElement('div');
    el.className = 'widget-item';

    const attrsPreview = getAttributePairs(widget)
      .filter(([k]) => k !== 'name')
      .map(([k, v]) => `${k}=${v}`)
      .join(' | ');

    el.innerHTML = `
      <div class="widget-top">
        <div><span class="tag">${widget.type}</span> <strong>${widget.name}</strong></div>
        <div class="mini-actions">
          <button class="btn-secondary" data-action="edit" data-id="${widget.id}">Edit</button>
          <button class="btn-secondary" data-action="up" data-id="${widget.id}">Up</button>
          <button class="btn-secondary" data-action="down" data-id="${widget.id}">Down</button>
          <button class="btn-danger" data-action="delete" data-id="${widget.id}">Delete</button>
        </div>
      </div>
      <div class="widget-meta">parent: ${widget.parent || '(UI root)'}</div>
      <div class="widget-meta">${attrsPreview || '(no extra attributes)'}</div>
    `;

    refs.list.appendChild(el);
  }

  syncParentOptions();
}

function syncParentOptions() {
  const previous = refs.parent.value;
  const options = ['<option value="">(UI root)</option>'];
  for (const w of widgets) {
    options.push(`<option value="${escapeXml(w.name)}">${escapeXml(w.name)} (${escapeXml(w.type)})</option>`);
  }
  refs.parent.innerHTML = options.join('');
  if (widgets.some(w => w.name === previous)) {
    refs.parent.value = previous;
  }
}

function findChildren(parentName) {
  return widgets.filter(w => w.parent === parentName);
}

function parsePair(value, fallbackA, fallbackB) {
  if (!value || !String(value).trim()) {
    return [fallbackA, fallbackB];
  }
  const parts = String(value).split(',').map(v => Number(v.trim()));
  if (parts.length < 2 || Number.isNaN(parts[0]) || Number.isNaN(parts[1])) {
    return [fallbackA, fallbackB];
  }
  return [parts[0], parts[1]];
}

function parseBool(value, fallback = false) {
  if (value === undefined || value === null || String(value).trim() === '') {
    return fallback;
  }
  const v = String(value).trim().toLowerCase();
  if (v === '1' || v === 'true' || v === 'yes' || v === 'on') {
    return true;
  }
  if (v === '0' || v === 'false' || v === 'no' || v === 'off') {
    return false;
  }
  return fallback;
}

function toCssColor(raw, fallback = 'rgba(100, 116, 139, 0.45)') {
  if (!raw || !String(raw).trim()) {
    return fallback;
  }
  const nums = String(raw).split(',').map(v => Number(v.trim()));
  if (nums.length < 3 || nums.some(v => Number.isNaN(v))) {
    return fallback;
  }
  const r = Math.round(Math.min(1, Math.max(0, nums[0])) * 255);
  const g = Math.round(Math.min(1, Math.max(0, nums[1])) * 255);
  const b = Math.round(Math.min(1, Math.max(0, nums[2])) * 255);
  const a = nums.length >= 4 && !Number.isNaN(nums[3]) ? Math.min(1, Math.max(0, nums[3])) : 1;
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function parseIni(text) {
  const config = {};
  let section = '';
  const lines = String(text || '').split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith(';') || line.startsWith('#')) {
      continue;
    }
    if (line.startsWith('[') && line.endsWith(']')) {
      section = line.slice(1, -1).trim();
      if (!config[section]) {
        config[section] = {};
      }
      continue;
    }
    const idx = line.indexOf('=');
    if (idx <= 0 || !section) {
      continue;
    }
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    config[section][key] = value;
  }
  return config;
}

function getThemeSectionNames(widget) {
  const names = [];
  const type = widget.type;
  const sub = widget.attrs.sub_theme;
  if (sub) {
    names.push(`${type}:${sub}`);
  }
  if (type === 'Button') {
    names.push('FrameButton');
  }
  names.push(type);
  return names;
}

function getThemeSection(widget) {
  if (!loadedTheme) {
    return null;
  }
  const names = getThemeSectionNames(widget);
  for (const name of names) {
    if (loadedTheme[name]) {
      return loadedTheme[name];
    }
  }
  return null;
}

function getThemeSectionByName(name) {
  if (!loadedTheme || !name || !loadedTheme[name]) {
    return null;
  }
  return loadedTheme[name];
}

function getThemeColor(section, keys, fallback) {
  if (!section) {
    return fallback;
  }
  for (const key of keys) {
    if (section[key]) {
      return toCssColor(section[key], fallback);
    }
  }
  return fallback;
}

function encodePathSegment(segment) {
  return encodeURIComponent(segment).replace(/%2F/g, '/');
}

function normalizeBasePath(path) {
  const trimmed = String(path || '').trim();
  if (!trimmed) {
    return '';
  }
  return trimmed.replace(/\\/g, '/').replace(/\/+$/, '');
}

function buildFontUrl(basePath, fontFileName) {
  const base = normalizeBasePath(basePath);
  const safeName = encodePathSegment(String(fontFileName || '').trim());
  return base ? `${base}/${safeName}` : safeName;
}

function getFontMimeType(fileName) {
  const lower = String(fileName || '').toLowerCase();
  if (lower.endsWith('.otf')) {
    return 'opentype';
  }
  if (lower.endsWith('.woff')) {
    return 'woff';
  }
  if (lower.endsWith('.woff2')) {
    return 'woff2';
  }
  return 'truetype';
}

function makeFontFamilyName(fileName) {
  const safe = String(fileName || 'ThemeFont').replace(/[^a-zA-Z0-9]+/g, '_');
  return `BGUI_${safe}`;
}

function registerThemeFonts(fontBasePath) {
  if (!loadedTheme) {
    return 0;
  }

  let cssChunk = '';
  let added = 0;
  const seen = new Set();

  for (const [sectionName, section] of Object.entries(loadedTheme)) {
    const fontFile = section && section.Font;
    if (!fontFile || seen.has(fontFile)) {
      continue;
    }
    seen.add(fontFile);

    const url = buildFontUrl(fontBasePath, fontFile);
    const family = makeFontFamilyName(fontFile);
    fontFamilyByFile[fontFile] = family;

    if (!registeredFontUrls.has(url)) {
      registeredFontUrls.add(url);
      const format = getFontMimeType(fontFile);
      cssChunk += `\n@font-face { font-family: '${family}'; src: url('${url}') format('${format}'); font-display: swap; }`;
      added += 1;
    }

    if (!loadedTheme[sectionName]) {
      loadedTheme[sectionName] = section;
    }
  }

  if (cssChunk) {
    dynamicFontStyle.textContent += cssChunk;
  }

  return added;
}

function getThemeFontFamily(section, fallbackSectionNames = []) {
  if (section && section.Font && fontFamilyByFile[section.Font]) {
    return fontFamilyByFile[section.Font];
  }

  for (const name of fallbackSectionNames) {
    const sec = getThemeSectionByName(name);
    if (sec && sec.Font && fontFamilyByFile[sec.Font]) {
      return fontFamilyByFile[sec.Font];
    }
  }

  return null;
}

function deriveFontBaseFromThemePath(themePath) {
  const p = String(themePath || '').replace(/\\/g, '/');
  const idx = p.indexOf('/themes/');
  if (idx > 0) {
    return `${p.slice(0, idx)}/fonts`;
  }
  return normalizeBasePath(refs.themeFontBaseInput.value) || DEFAULT_FONT_BASE;
}

function getThemeSizePx(section, fallback) {
  const stageRect = refs.previewStage.getBoundingClientRect();
  const previewHeight = Math.max(120, stageRect.height || 0);

  let sourceValue = fallback;
  if (section) {
    const raw = section.FontSize || section.Size;
    const parsed = Number(raw);
    if (!Number.isNaN(parsed) && parsed > 0) {
      sourceValue = parsed;
    }
  }

  // Mirrors bgui.System.normalize_text + Label.pt_size setter:
  // rendered_size = pt_size * (screen_height / 1000)
  const scaled = Number(sourceValue) * (previewHeight / 1000);
  return Math.max(1, scaled);
}

function measureLabelSizePx(text, fontPx, fontFamily = 'sans-serif') {
  const safeText = String(text || '');
  const lines = safeText.split('\n');
  const longestLine = lines.reduce((acc, line) => (line.length > acc.length ? line : acc), '');

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.font = `${Math.max(8, fontPx)}px ${fontFamily}`;
  const measured = ctx.measureText(longestLine || ' ');

  const width = Math.max(2, Math.ceil(measured.width));
  const height = Math.max(2, Math.ceil(Math.max(1, lines.length) * fontPx * 1.2));
  return [width, height];
}

function getPreviewNormalizedPtSize(rawPtSize, fallbackPtSize) {
  const stageRect = refs.previewStage.getBoundingClientRect();
  const previewHeight = Math.max(120, stageRect.height || 0);

  const parsed = Number(rawPtSize);
  const source = (!Number.isNaN(parsed) && parsed > 0) ? parsed : fallbackPtSize;
  const scaled = Number(source) * (previewHeight / 1000);
  return Math.max(1, scaled);
}

function applyThemeInfo() {
  refs.themeInfo.textContent = `Theme: ${loadedThemeName} | active fonts: ${registeredFontUrls.size}`;
}

function applyThemeFromText(text, displayName, themePathHint = '') {
  const parsed = parseIni(text);
  const sectionCount = Object.keys(parsed).length;
  if (!sectionCount) {
    setStatus('Could not read theme sections.', 'error');
    return;
  }
  loadedTheme = parsed;
  const chosenFontBase = normalizeBasePath(refs.themeFontBaseInput.value) || deriveFontBaseFromThemePath(themePathHint);
  refs.themeFontBaseInput.value = chosenFontBase;
  registerThemeFonts(chosenFontBase);
  loadedThemeName = `${displayName} (${sectionCount} sections)`;
  applyThemeInfo();
  renderPreview();
  setStatus('Theme loaded and applied to preview.', 'ok');
}

function defaultsByType(type) {
  const defaults = getWidgetDefaults(type);
  if (defaults.size) {
    const [w, h] = parsePair(defaults.size, 1, 1);
    return [w, h];
  }
  if (type === 'Label') {
    return [0.0, 0.0];
  }
  return [1, 1];
}

function createWidgetVisual(widget, parentGeometry, parentOrigin, trail = new Set()) {
  if (trail.has(widget.name)) {
    return;
  }

  const [posX, posY] = parsePair(getEffectiveAttr(widget, 'pos'), 0, 0);
  const [defaultW, defaultH] = defaultsByType(widget.type);
  const sizeRaw = getAttrRaw(widget, 'size');
  const [sizeW, sizeH] = parsePair(sizeRaw, defaultW, defaultH);

  const px = parentOrigin.x + (parentGeometry.width * posX);
  const py = parentOrigin.y + (parentGeometry.height * posY);

  let pw = Math.max(8, parentGeometry.width * sizeW);
  let ph = Math.max(8, parentGeometry.height * sizeH);

  const el = document.createElement('div');
  el.className = 'preview-widget';
  el.style.left = `${px}px`;
  el.style.bottom = `${py}px`;
  el.style.width = `${pw}px`;
  el.style.height = `${ph}px`;

  const label = document.createElement('div');
  label.className = 'preview-widget-label';
  label.textContent = `${widget.type} - ${widget.name}`;

  const content = document.createElement('div');
  content.className = 'preview-widget-content';
  content.textContent = widget.attrs.text || widget.name;

  const themeSection = getThemeSection(widget);
  const fontFamily = getThemeFontFamily(themeSection, ['Label', 'Button', 'TextInput']);
  if (fontFamily) {
    content.style.fontFamily = `'${fontFamily}', 'Segoe UI', Tahoma, Verdana, sans-serif`;
  }

  const colorRaw = getEffectiveAttr(widget, 'color');
  const color = colorRaw
    ? toCssColor(colorRaw)
    : getThemeColor(themeSection, ['FillColor1', 'BGColor1', 'Color1', 'Color'], 'rgba(100, 116, 139, 0.45)');

  const borderColor = getThemeColor(themeSection, ['BorderColor'], 'rgba(148, 163, 184, 0.8)');
  el.style.borderColor = borderColor;

  if (widget.type === 'Label') {
    const textValue = getEffectiveAttr(widget, 'text') || widget.name;
    const themeBasePt = themeSection ? (Number(themeSection.Size) || 20) : 20;
    const fontPx = getPreviewNormalizedPtSize(getEffectiveAttr(widget, 'pt_size'), themeBasePt);
    const centerText = parseBool(getEffectiveAttr(widget, 'center_text'), true);

    if (!sizeRaw) {
      const canvasFontFamily = fontFamily || 'sans-serif';
      const [autoW, autoH] = measureLabelSizePx(textValue, fontPx, canvasFontFamily);
      pw = autoW;
      ph = autoH;
      el.style.width = `${pw}px`;
      el.style.height = `${ph}px`;
    }

    if (centerText) {
      el.style.left = `${px - (pw / 2)}px`;
    }

    content.style.background = 'transparent';
    content.style.color = colorRaw
      ? toCssColor(colorRaw, 'rgba(248, 250, 252, 1)')
      : getThemeColor(themeSection, ['TextColor', 'Color'], 'rgba(248, 250, 252, 1)');
    content.textContent = textValue;
    content.style.fontSize = `${fontPx}px`;
    content.style.padding = '0';
    content.style.whiteSpace = 'pre';
    content.style.wordBreak = 'normal';
    content.style.overflow = 'visible';
    content.style.placeItems = centerText ? 'center' : 'start center';
    el.style.border = 'none';
  } else if (widget.type === 'ProgressBar') {
    const percent = Number(getEffectiveAttr(widget, 'percent'));
    const p = Number.isNaN(percent) ? 1 : Math.min(1, Math.max(0, percent));
    const bg = getThemeColor(themeSection, ['BGColor1', 'Color1'], 'rgba(15, 23, 42, 0.5)');
    const fill = getThemeColor(themeSection, ['FillColor1', 'Color'], color);
    content.style.background = bg;
    content.style.justifyItems = 'stretch';
    content.innerHTML = `<div style="width:${Math.round(p * 100)}%;height:72%;background:${fill};border-radius:3px;"></div>`;
  } else if (widget.type === 'Slider') {
    const min = Number(getEffectiveAttr(widget, 'min_value'));
    const max = Number(getEffectiveAttr(widget, 'max_value'));
    const val = Number(getEffectiveAttr(widget, 'value'));
    const range = Number.isNaN(min) || Number.isNaN(max) || max === min ? 1 : max - min;
    const pos = Number.isNaN(val) ? 0.5 : Math.min(1, Math.max(0, (val - min) / range));
    const sliderBg = getThemeColor(themeSection, ['BGColor1', 'Color1'], 'rgba(148,163,184,0.55)');
    const sliderFill = getThemeColor(themeSection, ['FillColor1', 'Color'], color);
    content.innerHTML = `
      <div style="width:100%;height:30%;background:${sliderBg};border-radius:3px;position:relative;">
        <div style="position:absolute;left:${Math.round(pos * 100)}%;top:-50%;transform:translateX(-50%);width:10px;height:10px;border-radius:50%;background:${sliderFill};border:1px solid rgba(255,255,255,.8);"></div>
      </div>
    `;
  } else if (widget.type === 'Frame') {
    content.style.background = getThemeColor(themeSection, ['Color1', 'BGColor1'], 'rgba(15, 23, 42, 0.35)');
    el.style.border = `1px solid ${borderColor}`;
  } else if (widget.type === 'TextInput') {
    content.style.background = getThemeColor(themeSection, ['FrameColor', 'BGColor1', 'Color1'], color);
    content.style.color = getThemeColor(themeSection, ['TextColor', 'Color'], 'rgba(248, 250, 252, 1)');
    const textInputFontPx = getThemeSizePx(themeSection, 20);
    content.style.fontSize = `${textInputFontPx}px`;
  } else if (widget.type === 'Button') {
    content.style.background = getThemeColor(themeSection, ['BGColor1', 'Color1'], color);
    content.style.color = getThemeColor(themeSection, ['TextColor', 'Color'], 'rgba(248, 250, 252, 1)');
    const buttonFontPx = getThemeSizePx(themeSection, 20);
    content.style.fontSize = `${buttonFontPx}px`;
  } else {
    content.style.background = color;
  }

  el.appendChild(label);
  el.appendChild(content);
  refs.previewStage.appendChild(el);

  const children = findChildren(widget.name);
  trail.add(widget.name);
  const childGeometry = { width: pw, height: ph };
  const childOrigin = { x: px, y: py };
  for (const child of children) {
    const nextTrail = new Set(trail);
    createWidgetVisual(child, childGeometry, childOrigin, nextTrail);
  }
}

function renderPreview() {
  refs.previewStage.innerHTML = '';
  const stageRect = refs.previewStage.getBoundingClientRect();
  const stageGeometry = {
    width: Math.max(120, stageRect.width),
    height: Math.max(120, stageRect.height)
  };

  const roots = widgets.filter(w => !w.parent || !widgets.some(c => c.name === w.parent));
  for (const w of roots) {
    createWidgetVisual(w, stageGeometry, { x: 0, y: 0 });
  }
}

function serializeWidget(widget, depth, path = new Set()) {
  const indent = '  '.repeat(depth);
  const attrs = getAttributePairs(widget)
    .map(([k, v]) => ` ${k}="${escapeXml(v)}"`)
    .join('');

  if (path.has(widget.name)) {
    return `${indent}<!-- Cycle detected at ${escapeXml(widget.name)} -->`;
  }

  const children = findChildren(widget.name);
  if (!children.length) {
    return `${indent}<${widget.type}${attrs} />`;
  }

  path.add(widget.name);
  const inner = children.map(child => serializeWidget(child, depth + 1, new Set(path))).join('\n');
  return `${indent}<${widget.type}${attrs}>\n${inner}\n${indent}</${widget.type}>`;
}

function getCurrentXmlText() {
  const xml = refs.output.value.trim() ? refs.output.value : generateXml();
  refs.output.value = xml;
  return xml;
}

function forceDownloadXml(xml, fileName = 'interface.xml') {
  const blob = new Blob([xml], { type: 'application/xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function saveXmlToFile() {
  const xml = getCurrentXmlText();

  if (window.showSaveFilePicker) {
    try {
      if (xmlFileHandle) {
        const hasPermission = await ensureReadWritePermission(xmlFileHandle);
        if (!hasPermission) {
          throw new Error('No write permission for the current file.');
        }
      }

      if (!xmlFileHandle) {
        xmlFileHandle = await window.showSaveFilePicker({
          suggestedName: currentXmlFileName || 'interface.xml',
          types: [{
            description: 'XML',
            accept: {
              'application/xml': ['.xml'],
              'text/xml': ['.xml']
            }
          }]
        });
        await saveXmlHandleToDb(xmlFileHandle);
      }

      const writable = await xmlFileHandle.createWritable();
      await writable.write(xml);
      await writable.close();
      currentXmlFileName = xmlFileHandle.name || currentXmlFileName;
      setStatus(`XML saved to file (${currentXmlFileName}).`, 'ok');
      saveStateToStorage();
      return;
    } catch (err) {
      if (err && err.name === 'AbortError') {
        setStatus('Save canceled.', 'error');
        return;
      }
      // Fall through to download fallback.
    }
  }

  forceDownloadXml(xml, currentXmlFileName || 'interface.xml');
  setStatus('Browser without direct write: XML downloaded so you can replace it manually in the project.', 'ok');
  saveStateToStorage();
}

function generateXml() {
  const roots = widgets.filter(w => !w.parent || !widgets.some(c => c.name === w.parent));
  const body = roots.map(w => serializeWidget(w, 1)).join('\n');
  const xml = `<UI>\n${body}${body ? '\n' : ''}</UI>`;
  refs.output.value = xml;
  return xml;
}

function saveWidgetFromForm() {
  const data = collectFormData(editingWidgetId);
  if (!data) {
    return;
  }

  if (editingWidgetId) {
    const idx = widgets.findIndex(w => w.id === editingWidgetId);
    if (idx >= 0) {
      widgets[idx] = data;
      setStatus(`Widget updated: ${data.name}`, 'ok');
    } else {
      widgets.push(data);
      setStatus(`Widget added: ${data.name}`, 'ok');
    }
    exitEditMode(true);
  } else {
    widgets.push(data);
    clearForm();
    setStatus(`Widget added: ${data.name}`, 'ok');
  }

  renderWidgetList();
  renderPreview();
  refs.output.value = generateXml();
  saveStateToStorage();
}

function deleteWidget(id) {
  const idx = widgets.findIndex(w => w.id === id);
  if (idx === -1) {
    return;
  }
  const removedName = widgets[idx].name;
  widgets.splice(idx, 1);

  if (editingWidgetId === id) {
    exitEditMode(true);
  }

  for (const w of widgets) {
    if (w.parent === removedName) {
      w.parent = '';
    }
  }
  renderWidgetList();
  renderPreview();
  refs.output.value = generateXml();
  saveStateToStorage();
  setStatus('Widget deleted. Children were moved to root.', 'ok');
}

function moveWidget(id, direction) {
  const idx = widgets.findIndex(w => w.id === id);
  if (idx === -1) {
    return;
  }
  const target = direction === 'up' ? idx - 1 : idx + 1;
  if (target < 0 || target >= widgets.length) {
    return;
  }
  [widgets[idx], widgets[target]] = [widgets[target], widgets[idx]];
  renderWidgetList();
  renderPreview();
  refs.output.value = generateXml();
  saveStateToStorage();
}

controls.add.addEventListener('click', saveWidgetFromForm);

controls.cancelEdit.addEventListener('click', () => {
  exitEditMode(true);
  setStatus('Edit canceled.', 'ok');
});

controls.clear.addEventListener('click', () => {
  widgets.length = 0;
  exitEditMode(true);
  refs.list.innerHTML = '';
  refs.output.value = '';
  syncParentOptions();
  renderPreview();
  saveStateToStorage();
  setStatus('List cleared.', 'ok');
});

controls.generate.addEventListener('click', () => {
  generateXml();
  saveStateToStorage();
  setStatus('XML updated.', 'ok');
});

controls.saveXml.addEventListener('click', async () => {
  await saveXmlToFile();
});

controls.copy.addEventListener('click', async () => {
  const xml = refs.output.value.trim() ? refs.output.value : generateXml();
  try {
    await navigator.clipboard.writeText(xml);
    setStatus('XML copied to clipboard.', 'ok');
  } catch {
    setStatus('Failed to copy. Use Ctrl+C in the XML field.', 'error');
  }
});

controls.download.addEventListener('click', () => {
  const xml = getCurrentXmlText();
  forceDownloadXml(xml, currentXmlFileName || 'interface.xml');
  setStatus('interface.xml file downloaded.', 'ok');
});

controls.loadDefaultTheme.addEventListener('click', async () => {
  for (const candidate of DEFAULT_THEME_CANDIDATES) {
    try {
      const response = await fetch(candidate);
      if (!response.ok) {
        continue;
      }
      const text = await response.text();
      refs.themeFontBaseInput.value = deriveFontBaseFromThemePath(candidate);
      applyThemeFromText(text, candidate, candidate);
      return;
    } catch {
      // Try next path.
    }
  }
  setStatus('Could not auto-load theme.cfg. Use the file picker.', 'error');
});

refs.themeFileInput.addEventListener('change', async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }
  try {
    const text = await file.text();
    applyThemeFromText(text, file.name);
  } catch {
    setStatus('Failed to read theme file.', 'error');
  }
});

refs.type.addEventListener('change', () => {
  syncDefaultHintsForType();
});

refs.list.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) {
    return;
  }
  const { action, id } = btn.dataset;
  if (action === 'edit') {
    enterEditMode(id);
  } else if (action === 'delete') {
    deleteWidget(id);
  } else if (action === 'up') {
    moveWidget(id, 'up');
  } else if (action === 'down') {
    moveWidget(id, 'down');
  }
});

controls.loadXml.addEventListener('click', () => {
  if (window.showOpenFilePicker) {
    (async () => {
      try {
        const handles = await window.showOpenFilePicker({
          multiple: false,
          types: [{
            description: 'XML',
            accept: {
              'application/xml': ['.xml'],
              'text/xml': ['.xml']
            }
          }]
        });

        if (!handles || !handles.length) {
          return;
        }

        xmlFileHandle = handles[0];
        await saveXmlHandleToDb(xmlFileHandle);
        const file = await xmlFileHandle.getFile();
        const xmlText = await file.text();
        importWidgetsFromXmlText(xmlText, file.name, file.name);
      } catch (err) {
        if (!err || err.name !== 'AbortError') {
          setStatus('Failed to open XML.', 'error');
        }
      }
    })();
    return;
  }

  clearXmlHandleFromDb();
  xmlFileHandle = null;
  refs.xmlFileInput.value = '';
  refs.xmlFileInput.click();
});

refs.xmlFileInput.addEventListener('change', async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }

  try {
    const xmlText = await file.text();
    currentXmlFileName = file.name || 'interface.xml';
    xmlFileHandle = null;
    await clearXmlHandleFromDb();
    importWidgetsFromXmlText(xmlText, file.name, currentXmlFileName);
  } catch {
    setStatus('Failed to read the XML file.', 'error');
  }
});

if (!refs.themeFontBaseInput.value.trim()) {
  refs.themeFontBaseInput.value = DEFAULT_FONT_BASE;
}

refs.themeFontBaseInput.addEventListener('change', saveStateToStorage);

setEditMode(false);
syncParentOptions();
syncDefaultHintsForType();
applyThemeInfo();
renderPreview();
if (!restoreStateFromStorage()) {
  refs.output.value = '<UI>\n</UI>';
}

(async () => {
  if (!window.showOpenFilePicker) {
    return;
  }

  const restoredHandle = await loadXmlHandleFromDb();
  if (!restoredHandle) {
    return;
  }

  xmlFileHandle = restoredHandle;
  if (xmlFileHandle.name) {
    currentXmlFileName = xmlFileHandle.name;
  }
  saveStateToStorage();
})();

window.addEventListener('resize', renderPreview);
window.addEventListener('focus', renderPreview);
window.addEventListener('pageshow', renderPreview);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    renderPreview();
  } else {
    saveStateToStorage();
  }
});
window.addEventListener('beforeunload', saveStateToStorage);

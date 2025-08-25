// ===== Bootstrapped values from HTML =====
const CSRF_TOKEN = window.CSRF_TOKEN || '';
const {
  CAL_WEEK_TEMPLATE,
  CREATE_SESS_TEMPLATE,
  UPDATE_SESS_TEMPLATE,
  DELETE_SESS_TEMPLATE,
  LIST_VENUES_TEMPLATE,
  CREATE_OR_GET_DRAFT,
  UPLOAD_SETUP_CSV
} = window.FLASK_ROUTES || {};

// ===== Helpers to inject ids into route templates =====
function withUnitId(tpl, id)     { return tpl.replace(/\/0(\/|$)/, `/${id}$1`); }
function withSessionId(tpl, id)  { return tpl.replace(/0(\/|$)/, `${id}$1`); }
function getUnitId() {
  return document.getElementById('unit_id')?.value || '';
}

// ===== Modal open/close =====
function openCreateUnitModal() {
  setStep(1);
  document.getElementById('unit_id').value = '';
  document.getElementById('setup_complete').value = 'false';

  if (calendar) {
    try { calendar.destroy(); } catch {}
    calendar = null;
  }
  window.__calendarInitRan = false;

  const modal = document.getElementById("createUnitModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

// ===== Custom select (Semester) =====
document.querySelectorAll('.select').forEach(initSelect);
function initSelect(root) {
  const trigger = root.querySelector('.select-trigger');
  const hidden = root.querySelector('input[type="hidden"]');
  const valueEl = root.querySelector('.select-value');
  const options = Array.from(root.querySelectorAll('.option'));

  trigger.addEventListener('click', () => {
    const open = root.classList.toggle('open');
    trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  options.forEach(opt => {
    opt.addEventListener('click', () => {
      options.forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      const val = opt.getAttribute('data-value');
      hidden.value = val;
      valueEl.textContent = val;
      root.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    });
  });

  document.addEventListener('click', (e) => {
    if (!root.contains(e.target)) {
      root.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }
  });

  trigger.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); trigger.click(); }
    else if (e.key === 'Escape') { root.classList.remove('open'); trigger.setAttribute('aria-expanded', 'false'); }
  });
}

// ===== Date utils =====
const DATE_FMT = "d/m/Y"; // what we show/store in hidden inputs

function parseDMY(str) {
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(str);
  if (!m) return null;
  const [_, dd, mm, yyyy] = m;
  const d = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
  return isNaN(d) ? null : d;
}
function toIsoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function formatUS(d) { // DD/MM/YYYY
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  return `${day}/${month}/${d.getFullYear()}`;
}
function updateDateSummary() {
  const startEl = document.querySelector('[name="start_date"]');
  const endEl = document.querySelector('[name="end_date"]');
  const box = document.getElementById('date-summary');
  const textEl = document.getElementById('date-summary-text');
  if (!startEl || !endEl) return;

  const sv = (startEl.value || '').trim();
  const ev = (endEl.value || '').trim();
  const start = parseDMY(sv);
  const end = parseDMY(ev);

  if (!start || !end) { box.classList.add('hidden'); return; }
  if (end < start) {
    textEl.textContent = '⚠️ End date must be after start date.';
    box.classList.remove('hidden');
    return;
  }

  const diffMs = end - start;
  const diffDays = Math.ceil(diffMs / 86400000);
  const weeks = Math.ceil(diffDays / 7);

  textEl.textContent =
    `Unit will run from ${formatUS(start)} to ${formatUS(end)} (${diffDays} day${diffDays !== 1 ? 's' : ''}, ${weeks} week${weeks !== 1 ? 's' : ''})`;
  box.classList.remove('hidden');
}

// ===== Flatpickr calendars =====
const startInput = document.getElementById("start_date_input");
const endInput = document.getElementById("end_date_input");
const today = new Date();

const startPicker = flatpickr("#start_calendar", {
  inline: true,
  dateFormat: DATE_FMT,
  defaultDate: today,
  onChange: (selectedDates, dateStr) => {
    startInput.value = dateStr;
    endPicker.set("minDate", selectedDates[0] || null);
    if (endPicker.selectedDates[0] && selectedDates[0] && endPicker.selectedDates[0] < selectedDates[0]) {
      endPicker.setDate(selectedDates[0], true);
    }
    updateDateSummary();
  }
});

const endPicker = flatpickr("#end_calendar", {
  inline: true,
  dateFormat: DATE_FMT,
  defaultDate: today,
  onChange: (selectedDates, dateStr) => {
    endInput.value = dateStr;
    startPicker.set("maxDate", selectedDates[0] || null);
    updateDateSummary();
  }
});

startInput.value = startPicker.formatDate(startPicker.selectedDates[0] || today, DATE_FMT);
endInput.value = endPicker.formatDate(endPicker.selectedDates[0] || today, DATE_FMT);
updateDateSummary();

// ===== Step navigation =====
let currentStep = 1;
const TOTAL_STEPS = 4;

function setStep(n) {
  currentStep = n;
  document.querySelectorAll('.wizard-step').forEach(s => {
    s.classList.toggle('hidden', parseInt(s.dataset.step) !== currentStep);
  });
  document.querySelectorAll('.modal-steps .step').forEach((el, idx) => {
    el.classList.toggle('active', idx + 1 === currentStep);
  });

  const nextBtn = document.getElementById('next-btn');
  const submitBtn = document.getElementById('submit-btn');
  nextBtn.classList.remove('hidden');
  submitBtn.classList.add('hidden');
  if (currentStep === TOTAL_STEPS) {
    nextBtn.classList.add('hidden');
    submitBtn.classList.remove('hidden');
  }
}

async function nextStep() {
  if (currentStep === 1) {
    const f = document.getElementById('create-unit-form');
    const required = ['unit_name', 'unit_code', 'year', 'semester'];
    for (const name of required) {
      const el = f.querySelector(`[name="${name}"]`);
      if (!el || !el.value.trim()) { el?.focus(); return; }
    }
    return setStep(2);
  }

  if (currentStep === 2) {
    const start = document.querySelector('[name="start_date"]')?.value?.trim();
    const end = document.querySelector('[name="end_date"]')?.value?.trim();
    if (!start || !end) return;
    try {
      const unitId = await ensureDraftAndSetUnitId();
      console.debug('Draft unit id:', unitId);
    } catch (e) {
      alert('Could not create/get unit draft: ' + e.message);
      return;
    }
    return setStep(3);
  }

  if (currentStep === 3) {
    const ok = document.getElementById('setup_complete')?.value === 'true';
    if (!ok) {
      const box = document.getElementById('upload_status');
      box.classList.remove('hidden');
      box.textContent = 'Please upload the facilitators & venues CSV before continuing.';
      return;
    }
    return setStep(4);
  }
}
function prevStep() { setStep(Math.max(1, currentStep - 1)); }

// ===== Draft helper =====
function readUnitBasics() {
  const f = document.getElementById('create-unit-form');
  return {
    unit_code: f.querySelector('[name="unit_code"]')?.value?.trim() || '',
    unit_name: f.querySelector('[name="unit_name"]')?.value?.trim() || '',
    year: f.querySelector('[name="year"]')?.value?.trim() || '',
    semester: f.querySelector('[name="semester"]')?.value?.trim() || '',
    start_date: f.querySelector('[name="start_date"]')?.value?.trim() || '',
    end_date: f.querySelector('[name="end_date"]')?.value?.trim() || '',
  };
}

async function ensureDraftAndSetUnitId() {
  const basic = readUnitBasics();
  if (!basic.unit_code || !basic.unit_name || !basic.year || !basic.semester) {
    throw new Error('Missing unit basics');
  }

  const sd = parseDMY(basic.start_date);
  const ed = parseDMY(basic.end_date);
  if (!sd || !ed) throw new Error('Invalid start/end date');

  const startISO = toIsoDate(sd);
  const endISO   = toIsoDate(ed);

  const form = new FormData();
  form.append('unit_code', basic.unit_code);
  form.append('unit_name', basic.unit_name);
  form.append('year',      basic.year);
  form.append('semester',  basic.semester);
  form.append('start_date', startISO);
  form.append('end_date',   endISO);
  form.append('unit_start_date', startISO);
  form.append('unit_end_date',   endISO);

  const res = await fetch(CREATE_OR_GET_DRAFT, {
    method: 'POST',
    headers: { 'X-CSRFToken': CSRF_TOKEN },
    body: form
  });

  const data = await res.json();
  if (!res.ok || !data.ok) throw new Error(data.error || 'Failed to create/fetch draft');

  document.getElementById('unit_id').value = data.unit_id;

  if (data.start_date && data.end_date) {
    const [y1,m1,d1] = data.start_date.split('-').map(Number);
    const [y2,m2,d2] = data.end_date.split('-').map(Number);
    const start = new Date(y1, m1-1, d1);
    const end   = new Date(y2, m2-1, d2);
    startPicker.setDate(start, true);
    endPicker.setDate(end, true);
    document.querySelector('[name="start_date"]').value = startPicker.formatDate(start, DATE_FMT);
    document.querySelector('[name="end_date"]').value   = endPicker.formatDate(end, DATE_FMT);
    updateDateSummary();
  }

  return data.unit_id;
}

// ===== CSV Upload (Step 3a) =====
const uploadInput = document.getElementById('setup_csv');
const statusBox = document.getElementById('upload_status');
const setupFlagEl = document.getElementById('setup_complete');
const unitIdEl = document.getElementById('unit_id');
const fileNameEl = document.getElementById('file_name');

if (uploadInput) {
  uploadInput.addEventListener('change', async (e) => {
    statusBox.classList.remove('hidden', 'success', 'error');
    statusBox.textContent = 'Uploading…';
    setupFlagEl.value = 'false';

    const file = e.target.files?.[0];
    const unitId = unitIdEl.value;
    if (!file) {
      statusBox.textContent = 'No file selected.';
      statusBox.classList.add('error');
      fileNameEl.textContent = 'No file selected';
      return;
    }
    fileNameEl.textContent = file.name;
    if (!unitId) {
      statusBox.textContent = 'Missing unit id. Go back to Step 2 and try again.';
      statusBox.classList.add('error');
      fileNameEl.textContent = 'No file selected';
      return;
    }

    const form = new FormData();
    form.append('unit_id', unitId);
    form.append('setup_csv', file);

    try {
      const res = await fetch(UPLOAD_SETUP_CSV, {
        method: "POST",
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
          "X-CSRF-Token": CSRF_TOKEN,
        },
        body: form,
      });

      let data;
      try {
        data = await res.clone().json();
      } catch (e2) {
        const text = await res.text();
        throw new Error(`Non-JSON response (${res.status}): ${text.slice(0, 300)}`);
      }

      if (!res.ok || !data.ok) {
        const errs = (data.errors || [data.error]).filter(Boolean);
        statusBox.classList.add("error");
        statusBox.innerHTML = `
          <div class="font-semibold mb-1">Upload failed</div>
          <ul class="list-disc list-inside text-sm">
            ${errs.map((x) => `<li>${x}</li>`).join("")}
          </ul>`;
        setupFlagEl.value = "false";
        fileNameEl.textContent = "No file selected";
        statusBox.scrollIntoView({ block: "nearest", behavior: "smooth" });
        return;
      }

      statusBox.classList.add("success");
      statusBox.innerHTML = `
        <div class="font-semibold">Upload successful</div>
        <div class="text-sm mt-1">
          Facilitators created: ${data.created_users} · Linked: ${data.linked_facilitators}<br/>
          Venues created: ${data.created_venues} · Linked: ${data.linked_venues} · Updated: ${data.updated_venues}
        </div>`;
      setupFlagEl.value = "true";
      fileNameEl.textContent = file.name;
      statusBox.scrollIntoView({ block: "nearest", behavior: "smooth" });

      showCalendarIfReady();
      setTimeout(() => statusBox.classList.add("hidden"), 300);
      if (!window.__calendarInitRan) {
        window.__calendarInitRan = true;
        initCalendar();
      } else {
        refreshCalendarRange();
      }
    } catch (err) {
      console.error(err);
      statusBox.textContent = String(err.message || "Unexpected error during upload.");
      statusBox.classList.add("error");
      setupFlagEl.value = "false";
      fileNameEl.textContent = "No file selected";
      statusBox.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  });

  uploadInput.addEventListener('change', (e) => {
    const f = e.target.files?.[0];
    fileNameEl.textContent = f ? f.name : 'No file selected';
  });
}

// ===== Calendar =====
let calendar;

function initCalendar() {
  const calendarEl = document.getElementById('calGrid');
  const inspector  = document.getElementById('calInspector');

  calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'timeGridWeek',
    headerToolbar: false,
    firstDay: 1,
    allDaySlot: false,
    slotDuration: '00:30:00',
    nowIndicator: true,

    slotMinTime: '06:00:00',
    slotMaxTime: '21:00:00',
    scrollTime: '08:00:00',

    height: 'auto',
    contentHeight: 'auto',
    expandRows: true,
    handleWindowResize: true,

    editable: true,
    eventStartEditable: true,
    eventDurationEditable: true,
    eventResizableFromStart: true,
    selectable: true,
    selectMirror: true,
    selectOverlap: true,

    events: async (fetchInfo, successCallback, failureCallback) => {
      try {
        const uid = getUnitId();
        const weekStart = fetchInfo.startStr.split('T')[0];
        const res = await fetch(`${withUnitId(CAL_WEEK_TEMPLATE, uid)}?week_start=${weekStart}`, {
          headers: { 'X-CSRFToken': CSRF_TOKEN }
        });
        const data = await res.json();
        if (res.ok && data.ok) {
          successCallback(data.sessions);
        } else {
          failureCallback(new Error(data.error || 'Failed to load sessions'));
        }
      } catch (err) {
        failureCallback(err);
      }
    },

    datesSet: () => {
      updateToolbarTitle();
      setTimeout(() => { stampOutsideOnBody(); }, 0);
    },

    dayHeaderDidMount: (arg) => {
      const out = isOutOfRange(arg.date);
      const existing = arg.el.querySelector('.fc-outside-chip');
      if (existing) existing.remove();
      if (out) {
        const chip = document.createElement('span');
        chip.className = 'fc-outside-chip';
        chip.textContent = 'Outside range';
        arg.el.appendChild(chip);
      }
    },

    selectAllow: (sel) => {
      return !isOutOfRange(sel.start) && !isOutOfRange(new Date(sel.end.getTime() - 1));
    },
    eventAllow: (dropInfo) => {
      return !isOutOfRange(dropInfo.start) && !isOutOfRange(new Date(dropInfo.end.getTime() - 1));
    },

    select: async (selectionInfo) => {
      const uid = getUnitId();
      const start = fmtLocalYYYYMMDDHHMM(selectionInfo.start);
      const end   = fmtLocalYYYYMMDDHHMM(selectionInfo.end);

        try {
        const res = await fetch(withUnitId(CREATE_SESS_TEMPLATE, uid), {
            method: 'POST',
            headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN 
            },
            body: JSON.stringify({
            start,
            end,
            venue: '',
            session_name: '',
            // staffing defaults
            lead_required: DEFAULT_LEAD_REQUIRED,
            support_required: DEFAULT_SUPPORT_REQUIRED,
            // recurrence default
            recurrence: { occurs: 'none' }
            })
        });
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || 'Failed to create session');

        await calendar.refetchEvents();

        let ev = null;
        if (data.session_id) ev = calendar.getEventById(String(data.session_id));
        if (!ev) {
          ev = calendar.getEvents().find(e =>
            e.start && e.start.getTime() === selectionInfo.start.getTime() &&
            e.end && e.end.getTime() === selectionInfo.end.getTime()
          );
        }
        if (ev) openInspector(ev);
      } catch (err) {
        console.error(err);
        alert(String(err.message || 'Could not create session.'));
      } finally {
        calendar.unselect();
      }
    },

    eventDrop: async (info) => {
      try {
        await updateEventTimesOnServer(info.event);
      } catch (err) {
        alert(String(err.message || 'Failed to update time'));
        info.revert();
      }
    },

    eventResize: async (info) => {
      try {
        await updateEventTimesOnServer(info.event);
      } catch (err) {
        alert(String(err.message || 'Failed to update time'));
        info.revert();
      }
    },

    dateClick: async (info) => {
    const d = new Date(info.dateStr);
    if (isOutOfRange(d)) return;

    const start = fmtLocalYYYYMMDDHHMM(info.date);
    const end   = fmtLocalYYYYMMDDHHMM(new Date(info.date.getTime() + 60 * 60 * 1000));
    const uid = getUnitId();

    try {
        const res = await fetch(withUnitId(CREATE_SESS_TEMPLATE, uid), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
        start,
        end,
        venue: '',
        session_name: '',
        // staffing defaults
        lead_required: DEFAULT_LEAD_REQUIRED,
        support_required: DEFAULT_SUPPORT_REQUIRED,
        // recurrence default
        recurrence: { occurs: 'none' }
        })
        });


        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || 'Failed to create session');

        await calendar.refetchEvents();

        // Try to find the newly created event and open the inspector
        let ev = null;
        if (data.session_id) {
        ev = calendar.getEventById(String(data.session_id));
        }
        if (!ev) {
        ev = calendar.getEvents().find(e =>
            e.start && e.start.getTime() === new Date(start).getTime()
        );
        }
        if (ev) openInspector(ev);
    } catch (err) {
        console.error(err);
        alert(String(err.message || 'Could not create session.'));
    }
    },


    eventClick: (info) => { openInspector(info.event); }
  });

  calendar.render();

  document.getElementById('prevWeek').onclick = () => calendar.prev();
  document.getElementById('nextWeek').onclick = () => calendar.next();
  document.getElementById('goToday').onclick  = () => calendar.today();

  refreshCalendarRange();
}

async function updateEventTimesOnServer(ev) {
  const startOut = fmtLocalYYYYMMDDHHMM(ev.start);
  const endOut   = fmtLocalYYYYMMDDHHMM(ev.end || new Date(ev.start.getTime() + 60*60*1000));
  const res = await fetch(withSessionId(UPDATE_SESS_TEMPLATE, ev.id), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
    body: JSON.stringify({ start: startOut, end: endOut })
  });
  const data = await res.json();
  if (!res.ok || !data.ok) throw new Error(data.error || 'Server rejected update');
}

// ===== Calendar helpers & globals =====
function getUnitRange() {
  const s = document.querySelector('[name="start_date"]')?.value?.trim();
  const e = document.querySelector('[name="end_date"]')?.value?.trim();
  const start = s ? parseDMY(s) : null;
  const end   = e ? parseDMY(e) : null;
  return { start, end };
}

function fmtLocalYYYYMMDDHHMM(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fmtRange(start, end){
  const t = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return `${t(start)}–${t(end)}`;
}

function isOutOfRange(d) {
  const { start, end } = getUnitRange();
  if (!start || !end) return false;
  return d < start || d > end;
}

function updateToolbarTitle() {
  const titleEl = document.getElementById('calWeekTitle');
  const rangeEl = document.getElementById('calWeekRange');
  if (!calendar || !titleEl || !rangeEl) return;

  const view = calendar.view;
  const fmt = (dt, opts) => dt.toLocaleDateString(undefined, opts);
  const s = view.currentStart;
  const e = new Date(view.currentEnd.getTime() - 1);
  const sameMonth = s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear();
  const title = sameMonth
    ? `${fmt(s, { month: 'short' })} ${s.getDate()}–${e.getDate()}, ${e.getFullYear()}`
    : `${fmt(s, { month: 'short' })} ${s.getDate()} – ${fmt(e, { month: 'short' })} ${e.getDate()}, ${e.getFullYear()}`;
  titleEl.textContent = title;

  const { start, end } = getUnitRange();
  rangeEl.textContent = (start && end)
    ? `Unit range: ${fmt(start, { month:'short', day:'numeric', year:'numeric' })} → ${fmt(end, { month:'short', day:'numeric', year:'numeric' })}`
    : '';
}

function stampOutsideOnBody() {
  if (!calendar) return;
  const { start, end } = getUnitRange();
  if (!start || !end) return;

  document.querySelectorAll('.fc-timegrid-col').forEach((col) => {
    const dateStr = col.getAttribute('data-date');
    if (!dateStr) return;
    const d = new Date(dateStr + 'T00:00:00');
    col.classList.toggle('out-of-range', isOutOfRange(d));
  });

  document.querySelectorAll('.fc-daygrid-day').forEach((cell) => {
    const dateStr = cell.getAttribute('data-date');
    if (!dateStr) return;
    const d = new Date(dateStr + 'T00:00:00');
    cell.classList.toggle('out-of-range', isOutOfRange(d));
  });
}

function refreshCalendarRange() {
  if (!calendar) return;
  const { start, end } = getUnitRange();
  if (start && end) {
    const endExclusive = new Date(end.getTime());
    endExclusive.setDate(endExclusive.getDate() + 1);
    calendar.setOption('validRange', {
      start: toIsoDate(start),
      end: toIsoDate(endExclusive),
    });
  }
  updateToolbarTitle();
  stampOutsideOnBody();
  calendar.refetchEvents();
}

// ===== Venues dropdown helpers =====
window.__venueCache = window.__venueCache || {};

async function fetchVenuesForUnit(unitId) {
  if (window.__venueCache[unitId]) return window.__venueCache[unitId];

  try {
    if (!unitId) return []; // no draft yet
    const res = await fetch(withUnitId(LIST_VENUES_TEMPLATE, unitId), {
      headers: { 'X-CSRFToken': CSRF_TOKEN }
    });

    if (!res.ok) {
      // don’t try to parse non-JSON error bodies
      console.warn('list_venues not OK:', res.status);
      return [];
    }

    const data = await res.json();
    const list = (data && data.ok && Array.isArray(data.venues)) ? data.venues : [];
    window.__venueCache[unitId] = list;
    return list;
  } catch (err) {
    console.error('fetchVenuesForUnit error:', err);
    return [];
  }
}


function upgradeVenueInputToSelect() {
  const old = document.getElementById('inspVenue');
  if (!old || old.tagName === 'SELECT') return old;
  const sel = document.createElement('select');
  sel.id = 'inspVenue';
  sel.className = old.className + ' select-native';
  sel.innerHTML = `<option value="">— Select a venue —</option>`;
  old.parentNode.replaceChild(sel, old);
  return sel;
}

function populateVenueSelect(selectEl, venues, selectedId, selectedName) {
  const opts = [
    '<option value="" disabled selected hidden>Select a venue</option>'
  ].concat(venues.map(v => `<option value="${v.id}">${v.name}</option>`));
  selectEl.innerHTML = opts.join('');

  if (selectedId) {
    selectEl.value = String(selectedId);
  } else if (selectedName) {
    const match = venues.find(v => (v.name || '').toLowerCase() === selectedName.toLowerCase());
    if (match) selectEl.value = String(match.id);
  }

  if (!selectEl.value) {
    selectEl.setAttribute('required', 'required');
  }
}

// One-time upgrade on load so the element exists for openInspector
upgradeVenueInputToSelect();

// ===== Inspector =====
async function openInspector(ev) {
  const inspector = document.getElementById('calInspector');
  if (!ev || !inspector) return;

  // Make panel visible immediately so errors don’t hide it
  inspector.classList.remove('hidden');
  requestAnimationFrame(() => inspector.classList.add('open'));

  // keep a handle to the event being edited (for live preview)
  window.__editingEvent = ev;

  // ---- safe times ----
  const start = ev.start ? new Date(ev.start) : new Date();
  const end   = ev.end   ? new Date(ev.end)   : new Date(start.getTime() + 60 * 60 * 1000);

  const fmt = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const mins = Math.max(0, Math.round((end - start) / 60000));

  // Top bar subtitle + blue "Session Overview" card
  document.getElementById('inspSub').textContent =
    `${start.toLocaleDateString('en-US', { weekday: 'long' })} • ${fmt(start)}–${fmt(end)}`;
  document.getElementById('inspDay').textContent  =
    start.toLocaleDateString('en-US', { weekday: 'long' });
  document.getElementById('inspTime').textContent = `${fmt(start)}–${fmt(end)}`;
  document.getElementById('inspDur').textContent  = `${mins} minutes`;
  document.getElementById('inspDate').textContent = start.toLocaleDateString();
  document.getElementById('inspDelete').classList.remove('hidden');

  // ---- name field (supports multiple backends) ----
  const name = ev.extendedProps?.session_name
            || ev.extendedProps?.module_name
            || ev.title
            || '';
  const nameInput = document.getElementById('inspName');
  nameInput.placeholder = 'New Session';
  nameInput.value = name;

  // ---- venue select (fault-tolerant) ----
  try {
    const sel = upgradeVenueInputToSelect();
    const unitId = getUnitId();
    const venues = await fetchVenuesForUnit(unitId);
    const selectedId   = ev.extendedProps?.venue_id || null;
    const selectedName = ev.extendedProps?.venue
                      || ev.extendedProps?.location
                      || ev.title
                      || '';
    populateVenueSelect(sel, venues, selectedId, selectedName);
  } catch (err) {
    console.warn('Venue population failed (non-blocking):', err);
  }

  // ---- timing controls (start/end + presets) ----
  ensureTimePickers();
  setTimesIntoPickers(start, end);
    ensureRecurrencePickers();
    document.getElementById('recOccurs').onchange = () => updateRecurrencePreview(start, end);
    document.getElementById('recCount').oninput   = () => updateRecurrencePreview(start, end);
    document.getElementById('recUntil').oninput   = () => updateRecurrencePreview(start, end);
    updateRecurrencePreview(start, end);

  document.querySelectorAll('#calInspector .insp-preset').forEach(btn => {
    btn.onclick = () => {
      const range = btn.getAttribute('data-range');
      const [s, e] = applyPresetTo(start, range);
      setTimesIntoPickers(s, e);
      if (calendar && window.__editingEvent) {
        window.__editingEvent.setStart(s);
        window.__editingEvent.setEnd(e);
      }
    };
  });

  // ---- staffing (seed + buttons) ----
  const leadReq    = ev.extendedProps?.lead_required ?? DEFAULT_LEAD_REQUIRED;
  const supportReq = ev.extendedProps?.support_required ?? DEFAULT_SUPPORT_REQUIRED;
  setStaffingInUI(leadReq, supportReq);
  wireStaffingButtons();

  // ---- actions ----
  wireInspectorButtons(ev);

  // top-right
  document.getElementById('inspCloseBtn').onclick = closeInspector;
  document.getElementById('inspNextBtn').onclick  = () => {};
}



function wireInspectorButtons(ev) {
  const inspector = document.getElementById('calInspector');

  // Save
    document.getElementById('inspSave').onclick = async () => {
    const sel  = document.getElementById('inspVenue');
    const name = document.getElementById('inspName')?.value?.trim() || '';

    // pull times from the timing controls
    const times   = getPendingTimes();
    const pStart  = times.start || ev.start;
    const pEnd    = times.end   || ev.end || new Date(ev.start.getTime() + 60*60*1000);
    const startOut = fmtLocalYYYYMMDDHHMM(pStart);
    const endOut   = fmtLocalYYYYMMDDHHMM(pEnd);

    // staffing
    const { lead_required, support_required } = getStaffingFromUI();

    const payload = {
        start: startOut,
        end:   endOut,
        session_name: name,
        module_name:  name,
        title:        name,
        // include staffing
        lead_required,
        support_required
    };

    // recurrence from inspector UI
    payload.recurrence = readRecurrenceFromUI(pStart, pEnd);
    payload.apply_to   = 'series';

    // venue
    if (sel && sel.tagName === 'SELECT' && sel.value) {
        payload.venue_id = Number(sel.value);
    } else {
        payload.venue = (sel?.value || '').trim();
    }

    const res = await fetch(withSessionId(UPDATE_SESS_TEMPLATE, ev.id), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!data.ok) {
        alert(data.error || 'Failed to update');
    } else {
        closeInspector();
        calendar.refetchEvents();
    }
    };


  // Delete
  document.getElementById('inspDelete').onclick = async () => {
    if (!confirm('Delete this session?')) return;
    const res = await fetch(withSessionId(DELETE_SESS_TEMPLATE, ev.id), {
      method: 'DELETE',
      headers: { 'X-CSRFToken': CSRF_TOKEN }
    });
    const data = await res.json();
    if (!data.ok) {
      alert(data.error || 'Failed to delete');
    } else {
      closeInspector();
      calendar.refetchEvents();
    }
  };

  // Cancel
  document.getElementById('inspCancel').onclick = closeInspector;

  // ESC to close
  document.addEventListener('keydown', function esc(e){
    if (e.key === 'Escape') { closeInspector(); document.removeEventListener('keydown', esc); }
  }, { once:true });

  // Click outside to close (inside calendar wrapper)
  const wrap = document.getElementById('calendar_wrap');
  function outside(e){
    if (!inspector.contains(e.target)) { closeInspector(); wrap.removeEventListener('mousedown', outside); }
  }
  wrap.addEventListener('mousedown', outside, { once:true });
}


function showCalendarIfReady() {
  const ready = document.getElementById('setup_complete')?.value === 'true';
  const wrapUpload = document.getElementById('setup_wrap');
  const wrapCal = document.getElementById('calendar_wrap');

  if (ready) {
    wrapUpload.classList.add('hidden');
    wrapCal.classList.remove('hidden');
    if (window.__calendarInitRan && calendar) {
      setTimeout(() => calendar.updateSize(), 0);
    }
  } else {
    wrapCal.classList.add('hidden');
    wrapUpload.classList.remove('hidden');
  }
}

// Show calendar on step 3
const _origNextStep = nextStep;
nextStep = async function() {
  await _origNextStep();
  if (currentStep === 3) {
    showCalendarIfReady();
    if (!window.__calendarInitRan && document.getElementById('setup_complete')?.value === 'true') {
      window.__calendarInitRan = true;
      initCalendar();
    } else if (window.__calendarInitRan) {
      refreshCalendarRange();
    }
  }
};

// ===== Inspector time pickers & presets =====
let _startTP = null;
let _endTP = null;
let _pendingStart = null; // Date objects for the inspector’s current edit
let _pendingEnd = null;

function ensureTimePickers() {
  if (!_startTP) {
    _startTP = flatpickr("#inspStartTime", {
      enableTime: true, noCalendar: true,
      dateFormat: "h:i K", time_24hr: false,
      minuteIncrement: 5,
      onChange: () => { onTimeChange(); }
    });
  }
  if (!_endTP) {
    _endTP = flatpickr("#inspEndTime", {
      enableTime: true, noCalendar: true,
      dateFormat: "h:i K", time_24hr: false,
      minuteIncrement: 5,
      onChange: () => { onTimeChange(); }
    });
  }
}

function setTimesIntoPickers(startDate, endDate) {
  ensureTimePickers();
  _pendingStart = new Date(startDate);
  _pendingEnd   = new Date(endDate);
  _startTP.setDate(_pendingStart, true);
  _endTP.setDate(_pendingEnd, true);
  updateInspectorTimeOverview();
}

function onTimeChange() {
  if (_startTP && _pendingStart) {
    const t = _startTP.selectedDates[0];
    if (t) { _pendingStart.setHours(t.getHours(), t.getMinutes(), 0, 0); }
  }
  if (_endTP && _pendingEnd) {
    const t = _endTP.selectedDates[0];
    if (t) { _pendingEnd.setHours(t.getHours(), t.getMinutes(), 0, 0); }
  }
  updateInspectorTimeOverview();
  if (calendar && window.__editingEvent) {
    window.__editingEvent.setStart(_pendingStart);
    window.__editingEvent.setEnd(_pendingEnd);
  }
}

function updateInspectorTimeOverview() {
  if (!_pendingStart || !_pendingEnd) return;
  const fmt = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const mins = Math.max(0, Math.round((_pendingEnd - _pendingStart)/60000));
  document.getElementById('inspTime').textContent = `${fmt(_pendingStart)}–${fmt(_pendingEnd)}`;
  document.getElementById('inspDur').textContent  = `${mins} minutes`;
  document.getElementById('inspSub').textContent  =
    `${_pendingStart.toLocaleDateString('en-US', { weekday: 'long' })} • ${fmt(_pendingStart)}–${fmt(_pendingEnd)}`;
}

// Parse "HH:MM-HH:MM" like "09:00-12:00" to Date objects on the same day
function applyPresetTo(dateBase, rangeStr) {
  const [a,b] = rangeStr.split('-');
  const [h1,m1] = a.split(':').map(Number);
  const [h2,m2] = b.split(':').map(Number);
  const s = new Date(dateBase); s.setHours(h1, m1, 0, 0);
  const e = new Date(dateBase); e.setHours(h2, m2, 0, 0);
  return [s,e];
}

function getPendingTimes() {
  return {
    start: _pendingStart ? new Date(_pendingStart) : null,
    end:   _pendingEnd   ? new Date(_pendingEnd)   : null
  };
}

function closeCreateUnitModal() {
  const modal = document.getElementById("createUnitModal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

// ===== Staffing: defaults + helpers =========================================
const DEFAULT_LEAD_REQUIRED = 1;
const DEFAULT_SUPPORT_REQUIRED = 0;

function setStaffingInUI(lead = DEFAULT_LEAD_REQUIRED, support = DEFAULT_SUPPORT_REQUIRED) {
  const leadEl = document.getElementById('leadCount');
  const supEl  = document.getElementById('supportCount');
  const totalEl = document.getElementById('totalStaffText');

  const safeLead = Math.max(0, Number.isFinite(+lead) ? +lead : DEFAULT_LEAD_REQUIRED);
  const safeSup  = Math.max(0, Number.isFinite(+support) ? +support : DEFAULT_SUPPORT_REQUIRED);
  const total = safeLead + safeSup;

  if (leadEl) leadEl.textContent = String(safeLead);
  if (supEl)  supEl.textContent  = String(safeSup);
  if (totalEl) totalEl.textContent = `${total} ${total === 1 ? 'facilitator' : 'facilitators'}`;
}

function getStaffingFromUI() {
  const lead = parseInt(document.getElementById('leadCount')?.textContent || DEFAULT_LEAD_REQUIRED, 10);
  const support = parseInt(document.getElementById('supportCount')?.textContent || DEFAULT_SUPPORT_REQUIRED, 10);
  return {
    lead_required: Math.max(0, isNaN(lead) ? DEFAULT_LEAD_REQUIRED : lead),
    support_required: Math.max(0, isNaN(support) ? DEFAULT_SUPPORT_REQUIRED : support)
  };
}

function wireStaffingButtons() {
  const leadMinus = document.getElementById('leadMinusBtn');
  const leadPlus  = document.getElementById('leadPlusBtn');
  const supMinus  = document.getElementById('supportMinusBtn');
  const supPlus   = document.getElementById('supportPlusBtn');

  const adjust = (id, delta, min = 0) => {
    const el = document.getElementById(id);
    if (!el) return;
    const cur = parseInt(el.textContent || '0', 10) || 0;
    const next = Math.max(min, cur + delta);
    el.textContent = String(next);
    // refresh total
    const { lead_required, support_required } = getStaffingFromUI();
    setStaffingInUI(lead_required, support_required);
  };

  if (leadMinus) leadMinus.onclick = () => adjust('leadCount', -1, 0);
  if (leadPlus)  leadPlus.onclick  = () => adjust('leadCount', +1, 0);
  if (supMinus)  supMinus.onclick  = () => adjust('supportCount', -1, 0);
  if (supPlus)   supPlus.onclick   = () => adjust('supportCount', +1, 0);
}

// ==== Recurrence UI helpers ===============================================
let _recUntilPicker = null;

function ensureRecurrencePickers() {
  const untilEl = document.getElementById('recUntil');
  if (untilEl && !_recUntilPicker) {
    _recUntilPicker = flatpickr(untilEl, {
      dateFormat: DATE_FMT,
      allowInput: true
    });
  }
}

function readRecurrenceFromUI(startDate, endDate) {
  const occurs = document.getElementById('recOccurs')?.value || 'none';
  if (occurs !== 'weekly') return { occurs: 'none' };

  const count = Math.max(1, parseInt(document.getElementById('recCount')?.value || '12', 10));
  const untilStr = (document.getElementById('recUntil')?.value || '').trim();
  const u = untilStr ? parseDMY(untilStr) : null;
  const until = u ? toIsoDate(u) : null;

  const weekday = startDate.getDay(); // 0=Sun ... 6=Sat

  return {
    occurs: 'weekly',
    interval: 1,
    byweekday: [weekday],
    count,
    until, // ISO yyyy-mm-dd or null
  };
}

function updateRecurrencePreview(startDate, endDate) {
  const occurs = document.getElementById('recOccurs')?.value || 'none';
  const box = document.getElementById('recPreview');
  if (!box) return;

  if (occurs !== 'weekly') { box.classList.add('hidden'); return; }

  const count = Math.max(1, parseInt(document.getElementById('recCount')?.value || '12', 10));
  const untilStr = (document.getElementById('recUntil')?.value || '').trim();
  const firstDate = startDate;
  document.getElementById('recPatternText').textContent =
    `${firstDate.toLocaleDateString(undefined, { weekday: 'long' })} ` +
    `${firstDate.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}–` +
    `${endDate.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}, weekly`;

  document.getElementById('recFirst').textContent =
    firstDate.toLocaleDateString();

  document.getElementById('recTotal').textContent = String(count);
  box.classList.remove('hidden');
}


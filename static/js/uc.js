// ===== Bootstrapped values from HTML =====
const CSRF_TOKEN = window.CSRF_TOKEN || '';
const {
  CAL_WEEK_TEMPLATE,
  CREATE_SESS_TEMPLATE,
  UPDATE_SESS_TEMPLATE,
  DELETE_SESS_TEMPLATE,
  LIST_VENUES_TEMPLATE,
  LIST_FACILITATORS_TEMPLATE,
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
    resetCreateUnitWizard();
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
    
    // Wire the close button (X) to show warning
    const closeBtn = modal.querySelector('.modal-close');
    if (closeBtn) {
        // Remove existing event listeners by replacing the element
        const newCloseBtn = closeBtn.cloneNode(true);
        closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
        
        // Add the new event listener
        newCloseBtn.onclick = handleCloseUnitModal;
        console.log('Close button wired to handleCloseUnitModal');
    }
    
    // Also handle ESC key
    const handleEscKey = (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        handleCloseUnitModal();
      }
    };
    
    // Remove existing ESC listeners and add new one
    document.removeEventListener('keydown', handleEscKey);
    document.addEventListener('keydown', handleEscKey);
}

// Also add this to handle clicking outside the modal
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById("createUnitModal");
  if (modal) {
    modal.addEventListener('click', (e) => {
      // Check if the click was on the modal backdrop (not the modal content)
      if (e.target === modal) {
        handleCloseUnitModal();
      }
    });
  }
});

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

// --- Shade “in between” dates on the two inline calendars ---
function refreshMiniRangeShading() {
  const start = parseDMY(document.getElementById('start_date_input').value || '');
  const end   = parseDMY(document.getElementById('end_date_input').value || '');

  [startPicker, endPicker].forEach(fp => {
    if (!fp || !fp.calendarContainer) return;
    const days = fp.calendarContainer.querySelectorAll('.flatpickr-day');
    days.forEach(el => {
      // flatpickr attaches a Date object to each day element
      const d = el.dateObj;
      if (!d) return;

      // strictly between start & end → shade
      const inBetween = start && end && d > start && d < end;
      el.classList.toggle('inRange', !!inBetween);

      // optional: mark endpoints for nice rounded pills
      const isStart = start && d.getTime() === start.getTime();
      const isEnd   = end   && d.getTime() === end.getTime();
      el.classList.toggle('startRange', !!isStart);
      el.classList.toggle('endRange',   !!isEnd);
    });
  });
}

// Hook it up to all the moments the view or value can change
[startPicker, endPicker].forEach(fp => {
  if (!fp) return;
  fp.config.onDayCreate = (sel, d, fpInstance, dayElem) => { /* keep default */ };
  fp.config.onMonthChange = [...(fp.config.onMonthChange || []), refreshMiniRangeShading];
  fp.config.onYearChange  = [...(fp.config.onYearChange  || []), refreshMiniRangeShading];
  fp.config.onReady       = [...(fp.config.onReady       || []), refreshMiniRangeShading];
});

// Also call after either picker changes value (you already set inputs here)
const _origStartOnChange = startPicker.config.onChange;
startPicker.set('onChange', [
  ...(_origStartOnChange || []),
  () => { updateDateSummary(); refreshMiniRangeShading(); }
]);

const _origEndOnChange = endPicker.config.onChange;
endPicker.set('onChange', [
  ...(_origEndOnChange || []),
  () => { updateDateSummary(); refreshMiniRangeShading(); }
]);

// Paint once on load
refreshMiniRangeShading();


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

      console.log('Creating new session:', { start, end });

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

        console.log('Session created successfully:', data);
        
        const newEvent = {
          id: String(data.session_id),
          title: 'New Session',
          start: selectionInfo.start,
          end: selectionInfo.end,
          extendedProps: {
            session_name: '',
            venue: '',
            venue_id: null,
            lead_required: DEFAULT_LEAD_REQUIRED,
            support_required: DEFAULT_SUPPORT_REQUIRED
          }
        };

        calendar.addEvent(newEvent);
        const ev = calendar.getEventById(String(data.session_id));
        
        
        if (ev) {
          console.log('Opening inspector for event:', ev.id, 'with title:', ev.title);
          openInspector(ev);
        } else {
          console.warn('Could not find the newly created event');
        }
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

  // Make panel visible immediately so errors don't hide it
  inspector.classList.remove('hidden');
  requestAnimationFrame(() => inspector.classList.add('open'));

  // keep a handle to the event being edited (for live preview)
  window.__editingEvent = ev;

  // ---- safe times ----
  const start = ev.start ? new Date(ev.start) : new Date();
  const end   = ev.end   ? new Date(ev.end)   : new Date(start.getTime() + 60 * 60 * 1000);

  // IMPORTANT: Set the pending times BEFORE any UI updates
  _pendingStart = new Date(start);
  _pendingEnd = new Date(end);

  console.log('Opening inspector for event:', ev.id, {
    title: ev.title,
    sessionName: ev.extendedProps?.session_name,
    venue: ev.extendedProps?.venue,
    venueId: ev.extendedProps?.venue_id
  });

  const fmt = (d) => d.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    hour12: true 
  }).replace(/am|pm/gi, (match) => match.toUpperCase());
  const totalMins = Math.max(0, Math.round((_pendingEnd - _pendingStart) / 60000));


  // Convert minutes to hours and minutes
  const hours = Math.floor(totalMins / 60);
  const mins = totalMins % 60;

  // Format duration as "2 hours 30 minutes", "1 hour", "30 minutes", etc.
  let durationText = '';
  if (hours > 0 && mins > 0) {
    durationText = `${hours} hour${hours !== 1 ? 's' : ''} ${mins} minute${mins !== 1 ? 's' : ''}`;
  } else if (hours > 0) {
    durationText = `${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    durationText = `${mins} minute${mins !== 1 ? 's' : ''}`;
  }

  // Format date as DD/MM/YYYY
  const formatDateDDMMYYYY = (d) => {
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  };

  // Top bar subtitle + blue "Session Overview" card - USE PENDING TIMES
  document.getElementById('inspSub').textContent =
    `${_pendingStart.toLocaleDateString('en-US', { weekday: 'long' })} • ${fmt(_pendingStart)}–${fmt(_pendingEnd)}`;
  document.getElementById('inspDay').textContent  =
    _pendingStart.toLocaleDateString('en-US', { weekday: 'long' });
  document.getElementById('inspTime').textContent = `${fmt(_pendingStart)}–${fmt(_pendingEnd)}`;
  document.getElementById('inspDur').textContent  = durationText;
  document.getElementById('inspDate').textContent = formatDateDDMMYYYY(_pendingStart);
  document.getElementById('inspDelete').classList.remove('hidden');

  // ---- name field - FIX: Extract ONLY the session name, not venue ----
  let sessionName = ev.extendedProps?.session_name || ev.extendedProps?.module_name || '';
  
  // If no session name in extendedProps, try to extract from title (but remove venue)
  if (!sessionName && ev.title) {
    // If title contains newline, take only the first part (session name)
    sessionName = ev.title.split('\n')[0].trim();
  }
  
  // Default to 'New Session' if still empty
  if (!sessionName) {
    sessionName = 'New Session';
  }
  
  console.log('Extracted session name:', sessionName, 'from event:', ev.id);
  
  const nameInput = document.getElementById('inspName');
  nameInput.placeholder = 'New Session';
  nameInput.value = sessionName; // Use the extracted session name only

  // Remove existing event listeners and add new ones
  nameInput.removeEventListener('input', updateSessionOverview);
  nameInput.addEventListener('input', updateSessionOverview);

  // ---- venue select (fault-tolerant) ----
  try {
    const sel = upgradeVenueInputToSelect();
    const unitId = getUnitId();
    const venues = await fetchVenuesForUnit(unitId);
    const selectedId   = ev.extendedProps?.venue_id || null;
    const selectedName = ev.extendedProps?.venue
                      || ev.extendedProps?.location
                      || '';
    
    // If no venue in extendedProps but title has venue, try to extract it
    if (!selectedName && ev.title && ev.title.includes('\n')) {
      const titleParts = ev.title.split('\n');
      if (titleParts.length > 1) {
        const potentialVenue = titleParts[1].trim();
        // Check if this venue exists in our venues list
        const venueMatch = venues.find(v => v.name === potentialVenue);
        if (venueMatch) {
          console.log('Extracted venue from title:', potentialVenue);
          // Don't set selectedName here, let populateVenueSelect handle it
        }
      }
    }
    
    console.log('Setting up venue:', { selectedId, selectedName, venues: venues.length });
    
    populateVenueSelect(sel, venues, selectedId, selectedName);
  
    // Remove existing event listeners and add new ones
    sel.removeEventListener('change', updateSessionOverview);
    sel.addEventListener('change', updateSessionOverview);

    // DON'T call updateSessionOverview automatically AT ALL
    // It will only be called when user changes name or venue
    console.log('NOT calling updateSessionOverview - preserving all existing session data');
    
  } catch (err) {
    console.warn('Venue population failed (non-blocking):', err);
  }

  // ---- timing controls (start/end + presets) ----
  ensureTimePickers();
  _startTP.setDate(_pendingStart, false); // false = don't trigger onChange
  _endTP.setDate(_pendingEnd, false);     // false = don't trigger onChange

  ensureRecurrencePickers();
  document.getElementById('recOccurs').onchange = () => updateRecurrencePreview(_pendingStart, _pendingEnd);
  document.getElementById('recCount').oninput   = () => updateRecurrencePreview(_pendingStart, _pendingEnd);
  document.getElementById('recUntil').oninput   = () => updateRecurrencePreview(_pendingStart, _pendingEnd);
  updateRecurrencePreview(_pendingStart, _pendingEnd);

  document.querySelectorAll('#calInspector .insp-preset').forEach(btn => {
    btn.onclick = () => {
      const range = btn.getAttribute('data-range');
      const [s, e] = applyPresetTo(_pendingStart, range);
      setTimesIntoPickers(s, e);
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
    let selectedVenueName = '';
    if (sel && sel.tagName === 'SELECT' && sel.value) {
        payload.venue_id = Number(sel.value);
        // Get the venue name from the selected option
        const selectedOption = sel.options[sel.selectedIndex];
        selectedVenueName = selectedOption ? selectedOption.textContent.trim() : '';
    } else {
        payload.venue = (sel?.value || '').trim();
        selectedVenueName = payload.venue;
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
        // Update the current event with the new data
        if (window.__editingEvent) {
          // Update the event properties
          window.__editingEvent.setStart(pStart);
          window.__editingEvent.setEnd(pEnd);
          window.__editingEvent.setExtendedProp('session_name', name);
          window.__editingEvent.setExtendedProp('venue', selectedVenueName);
          window.__editingEvent.setExtendedProp('venue_id', payload.venue_id || null);
          window.__editingEvent.setExtendedProp('lead_required', lead_required);
          window.__editingEvent.setExtendedProp('support_required', support_required);
          
          // Update the title with proper formatting
          let displayTitle = name;
          if (selectedVenueName && 
              selectedVenueName !== 'Select a venue' && 
              selectedVenueName !== '— Select a venue —' && 
              selectedVenueName !== '') {
            displayTitle = `${name}\n${selectedVenueName}`;
          }
          window.__editingEvent.setProp('title', displayTitle);
          
          console.log('Updated event locally:', {
            id: window.__editingEvent.id,
            title: displayTitle,
            venue: selectedVenueName
          });
        }
        
        closeInspector();
    }
  };

  // Delete - FIXED APPROACH: Use a unique handler for each session
  const deleteBtn = document.getElementById('inspDelete');
  if (deleteBtn) {
    // Remove ALL existing event listeners by cloning without them
    const newDeleteBtn = deleteBtn.cloneNode(true);
    deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
    
    // Create a unique delete handler for this specific session
    const deleteHandler = async () => {
      console.log('Delete button clicked for session:', ev.id);
      
      if (!confirm('Delete this session?')) {
        console.log('Delete cancelled by user');
        return;
      }

      newDeleteBtn.disabled = true;
      console.log('Starting delete process for session:', ev.id);

      try {
        const res = await fetch(withSessionId(DELETE_SESS_TEMPLATE, ev.id), {
          method: 'DELETE',
          headers: { 'X-CSRFToken': CSRF_TOKEN }
        });
        
        console.log('Delete response status:', res.status);
        
        const data = await res.json();
        console.log('Delete response data:', data);

        if (!data.ok) {
          console.error('Delete failed on server:', data.error);
          alert(data.error || 'Failed to delete');
          newDeleteBtn.disabled = false;
          return;
        }

        console.log('Session deleted successfully on server');

        // Remove the event from the calendar immediately
        const eventId = String(ev.id);
        const eventToDelete = calendar.getEventById(eventId);
        if (eventToDelete) {
          eventToDelete.remove();
          console.log('Event removed from calendar:', eventId);
        } else {
          console.warn('Could not find event in calendar to remove:', eventId);
        }

        // Clear the editing handle
        window.__editingEvent = null;

        // Close the inspector
        closeInspector();

        console.log('Delete operation completed successfully for:', eventId);

      } catch (err) {
        console.error('Delete error:', err);
        alert(String(err?.message || err || 'Failed to delete'));
        newDeleteBtn.disabled = false;
      }
    };

    // Attach the handler
    newDeleteBtn.onclick = deleteHandler;
    
    // Also add via addEventListener as backup
    newDeleteBtn.addEventListener('click', (e) => {
      console.log('Delete button addEventListener triggered for:', ev.id);
    });
  }

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
  updateInspectorTimeOverview(); // This should update the Session Overview display
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
}

function updateInspectorTimeOverview() {
  if (!_pendingStart || !_pendingEnd) return;
  
  console.log('Updating time overview:', {
    pendingStart: _pendingStart,
    pendingEnd: _pendingEnd,
    duration: (_pendingEnd - _pendingStart) / (1000 * 60) + ' minutes'
  });
  
  // Use 12-hour format with AM/PM 
  const fmt = (d) => d.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: true 
  }).replace(/am|pm/gi, (match) => match.toUpperCase());
  
  const totalMins = Math.max(0, Math.round((_pendingEnd - _pendingStart)/60000));
  
  // Convert minutes to hours and minutes
  const hours = Math.floor(totalMins / 60);
  const mins = totalMins % 60;
  
  // Format duration as "2 hours 30 minutes", "1 hour", "30 minutes", etc.
  let durationText = '';
  if (hours > 0 && mins > 0) {
    durationText = `${hours} hour${hours !== 1 ? 's' : ''} ${mins} minute${mins !== 1 ? 's' : ''}`;
  } else if (hours > 0) {
    durationText = `${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    durationText = `${mins} minute${mins !== 1 ? 's' : ''}`;
  }
  
  // Format date as DD/MM/YYYY
  const formatDateDDMMYYYY = (d) => {
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  };
  
  document.getElementById('inspTime').textContent = `${fmt(_pendingStart)}–${fmt(_pendingEnd)}`;
  document.getElementById('inspDur').textContent = durationText;
  document.getElementById('inspDate').textContent = formatDateDDMMYYYY(_pendingStart);
  document.getElementById('inspSub').textContent =
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
  console.log('Closing modal and resetting all data');
  
  // Reset all modal state
  resetCreateUnitWizard();

  // Clear any server-side draft data by clearing the unit ID
  const unitIdEl = document.getElementById('unit_id');
  if (unitIdEl) {
    const oldUnitId = unitIdEl.value;
    unitIdEl.value = '';
    console.log('Cleared unit ID:', oldUnitId);
  }

  // Clear setup completion flag
  const setupFlagEl = document.getElementById('setup_complete');
  if (setupFlagEl) {
    setupFlagEl.value = 'false';
  }

  // Destroy calendar completely
  if (calendar) {
    try { 
      calendar.destroy(); 
      console.log('Calendar destroyed');
    } catch (e) {
      console.warn('Error destroying calendar:', e);
    }
    calendar = null;
  }
  window.__calendarInitRan = false;

  // Clear venue cache
  window.__venueCache = {};

  // Clear any editing state
  window.__editingEvent = null;
  _pendingStart = null;
  _pendingEnd = null;

  // Clear time pickers
  if (_startTP) {
    try { _startTP.destroy(); } catch (e) {}
    _startTP = null;
  }
  if (_endTP) {
    try { _endTP.destroy(); } catch (e) {}
    _endTP = null;
  }
  if (_recUntilPicker) {
    try { _recUntilPicker.destroy(); } catch (e) {}
    _recUntilPicker = null;
  }

  // Hide the modal
  const modal = document.getElementById("createUnitModal");
  if (modal) {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    console.log('Modal hidden');
  }
  
  console.log('Modal completely closed and reset');
}


function handleCloseUnitModal() {
  // Check if user has entered any data
  const form = document.getElementById('create-unit-form');
  const unitName = form?.querySelector('[name="unit_name"]')?.value?.trim() || '';
  const unitCode = form?.querySelector('[name="unit_code"]')?.value?.trim() || '';
  const year = form?.querySelector('[name="year"]')?.value?.trim() || '';
  const startDate = form?.querySelector('[name="start_date"]')?.value?.trim() || '';
  const endDate = form?.querySelector('[name="end_date"]')?.value?.trim() || '';
  const setupComplete = document.getElementById('setup_complete')?.value === 'true';
  
  // Check if there are any sessions in the calendar
  const hasCalendarSessions = calendar && calendar.getEvents && calendar.getEvents().length > 0;
  
  // Check if any significant data has been entered
  const hasData = unitName || unitCode || year || startDate || endDate || setupComplete || hasCalendarSessions;
  
  if (hasData) {
    showCloseConfirmationPopup();
  } else {
    // No data to lose, close immediately
    closeCreateUnitModal();
  }
}

// Add this new function to show the popup
function showCloseConfirmationPopup() {
  // Create popup HTML
  const popup = document.createElement('div');
  popup.className = 'simple-popup';
  popup.innerHTML = `
    <div class="popup-content">
      <div class="popup-title">Unsaved Changes</div>
      <div class="popup-message">
        Are you sure you want to close? All unsaved changes will be lost.
      </div>
      <div class="popup-buttons">
        <button class="popup-btn popup-btn-cancel" onclick="closeConfirmationPopup()">
          Cancel
        </button>
        <button class="popup-btn popup-btn-confirm" onclick="confirmCloseModal()">
          Close & Lose Changes
        </button>
      </div>
    </div>
  `;
  
  // Add to body
  document.body.appendChild(popup);
  
  // Close on backdrop click
  popup.addEventListener('click', (e) => {
    if (e.target === popup) {
      closeConfirmationPopup();
    }
  });
  
  // Close on ESC key
  const handleEscKey = (e) => {
    if (e.key === 'Escape') {
      closeConfirmationPopup();
      document.removeEventListener('keydown', handleEscKey);
    }
  };
  document.addEventListener('keydown', handleEscKey);
}

// Add these helper functions
function closeConfirmationPopup() {
  const popup = document.querySelector('.simple-popup');
  if (popup) {
    popup.remove();
  }
}

function confirmCloseModal() {
  closeConfirmationPopup();
  closeCreateUnitModal();
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

function resetCreateUnitWizard() {
  // 1) Form fields
  const form = document.getElementById('create-unit-form');
  if (form) form.reset();

  // Unit id + flags
  const unitIdEl = document.getElementById('unit_id');
  if (unitIdEl) unitIdEl.value = '';
  const setupFlagEl = document.getElementById('setup_complete');
  if (setupFlagEl) setupFlagEl.value = 'false';

  // 2) Custom Semester select visuals
  const semRoot = document.querySelector('.select[data-name="semester"]');
  if (semRoot) {
    const valueEl = semRoot.querySelector('.select-value');
    const hidden  = semRoot.querySelector('input[type="hidden"]');
    const options = [...semRoot.querySelectorAll('.option')];
    options.forEach(o => o.classList.remove('selected'));
    const first = options[0];
    if (first) first.classList.add('selected');
    if (valueEl && first) valueEl.textContent = first.getAttribute('data-value') || 'Semester 1';
    if (hidden && first) hidden.value = first.getAttribute('data-value') || 'Semester 1';
    semRoot.classList.remove('open');
  }

  // 3) Year default (optional: current year)
  const yearEl = form?.querySelector('[name="year"]');
  if (yearEl && !yearEl.value) yearEl.value = String(new Date().getFullYear());

  // 4) Dates -> today
  const today = new Date();
  if (typeof startPicker !== 'undefined' && startPicker) {
    startPicker.setDate(today, true);
  }
  if (typeof endPicker !== 'undefined' && endPicker) {
    endPicker.setDate(today, true);
  }
  const startInput = document.getElementById('start_date_input');
  const endInput   = document.getElementById('end_date_input');
  if (startInput && startPicker) startInput.value = startPicker.formatDate(today, DATE_FMT);
  if (endInput && endPicker)     endInput.value   = endPicker.formatDate(today, DATE_FMT);
  updateDateSummary?.();

  // 5) CSV upload area reset
  const uploadInput = document.getElementById('setup_csv');
  const fileNameEl  = document.getElementById('file_name');
  const statusBox   = document.getElementById('upload_status');
  if (uploadInput) uploadInput.value = '';
  if (fileNameEl) fileNameEl.textContent = 'No file selected';
  if (statusBox) {
    statusBox.classList.add('hidden');
    statusBox.classList.remove('success', 'error');
    statusBox.textContent = '';
  }

  // 6) Hide calendar section & destroy calendar
  const wrapUpload = document.getElementById('setup_wrap');
  const wrapCal    = document.getElementById('calendar_wrap');
  wrapCal?.classList.add('hidden');
  wrapUpload?.classList.remove('hidden');

  if (typeof calendar !== 'undefined' && calendar) {
    try { calendar.destroy(); } catch {}
  }
  window.__calendarInitRan = false;
  window.__venueCache = {}; // clear cached venues

  // 7) Inspector/staffing/recurrence small resets (safe no-ops if missing)
  setStaffingInUI?.(1, 0);
  const recOccurs = document.getElementById('recOccurs');
  const recCount  = document.getElementById('recCount');
  const recUntil  = document.getElementById('recUntil');
  const recPreview= document.getElementById('recPreview');
  if (recOccurs) recOccurs.value = 'none';
  if (recCount)  recCount.value  = '12';
  if (recUntil)  recUntil.value  = '';
  recPreview?.classList.add('hidden');

  // 8) Back to step 1
  setStep?.(1);
}

function closeInspector() {
  const inspector = document.getElementById('calInspector');
  if (!inspector) return;

  console.log('Closing inspector for event:', window.__editingEvent?.id);

  // hide panel
  inspector.classList.remove('open');
  inspector.classList.add('hidden');

  // IMPORTANT: Clear the editing event reference
  window.__editingEvent = null;

  // clear pending time edits (safe if null)
  _pendingStart = null;
  _pendingEnd = null;
}

async function populateReview() {
  const { unit_name, unit_code, semester, year, start_date, end_date } = readUnitBasics();

  // Fill Unit Details
  document.getElementById('rv_name').textContent = unit_name || '—';
  document.getElementById('rv_code').textContent = unit_code || '—';
  document.getElementById('rv_sem').textContent  = `${semester || ''} ${year || ''}`.trim();

  document.getElementById('rv_start').textContent = start_date || '—';
  document.getElementById('rv_end').textContent   = end_date || '—';

  // Duration (weeks, rounded up)
  const toDate = (s) => {
    const [d,m,y] = (s || '').split('/').map(Number);
    return (y && m && d) ? new Date(y, m-1, d) : null;
  };
  const sd = toDate(start_date), ed = toDate(end_date);
  if (sd && ed) {
    const days = Math.max(1, Math.round((ed - sd) / 86400000) + 1);
    const weeks = Math.ceil(days / 7);
    document.getElementById('rv_weeks').textContent = `${weeks} week${weeks>1?'s':''}`;
  } else {
    document.getElementById('rv_weeks').textContent = '—';
  }

  const unitId = document.getElementById('unit_id').value;

  // Facilitators
  try {
    if (LIST_FACILITATORS_TEMPLATE) {
      const resF = await fetch(withUnitId(LIST_FACILITATORS_TEMPLATE, unitId), { headers: { 'X-CSRFToken': CSRF_TOKEN }});
      const dataF = await resF.json();
      const ulF = document.getElementById('rv_facilitators');
      ulF.innerHTML = '';
      if (dataF.ok) {
        dataF.facilitators.forEach(email => {
          const li = document.createElement('li'); li.textContent = email; ulF.appendChild(li);
        });
        document.getElementById('rv_fac_count').textContent = dataF.facilitators.length;
      }
    } else {
      // No facilitators route available yet
      document.getElementById('rv_fac_count').textContent = 0;
      document.getElementById('rv_facilitators').innerHTML = '<li>No facilitators data available</li>';
    }
  } catch (err) {
    console.warn('Failed to load facilitators:', err);
    document.getElementById('rv_fac_count').textContent = 0;
    document.getElementById('rv_facilitators').innerHTML = '<li>Error loading facilitators</li>';
  }

  // Venues
  try {
    const resV = await fetch(withUnitId(LIST_VENUES_TEMPLATE, unitId), { headers: { 'X-CSRFToken': CSRF_TOKEN }});
    const dataV = await resV.json();
    const ulV = document.getElementById('rv_venues');
    ulV.innerHTML = '';
    if (dataV.ok) {
      (dataV.venues || []).forEach(v => {
        const li = document.createElement('li'); li.textContent = v.name || v; ulV.appendChild(li);
      });
      document.getElementById('rv_ven_count').textContent = (dataV.venues || []).length;
    }
  } catch {}

  // Sessions: PRIORITIZE CALENDAR FIRST, then try API as fallback
  let sessions = [];

  if (calendar && calendar.getEvents) {
    // Get sessions from the current calendar instance (they exist in memory)
    const calendarEvents = calendar.getEvents();
    console.log('Getting sessions from calendar:', calendarEvents.length, 'events found');
    
    sessions = calendarEvents.map(e => ({
      id: e.id, 
      start: e.start.toISOString(), 
      end: e.end.toISOString(), 
      title: e.title,
      extendedProps: e.extendedProps || {}
    }));
  } else if (sd && ed && unitId) {
    // Fallback to API if calendar not available
    console.log('Calendar not available, trying API fetch');
    
    async function fetchAllSessions(unitId, startISO, endISO) {
      const uniq = new Map();
      const start = new Date(startISO), end = new Date(endISO);
      if (!(start && end)) return [];
      // align to Monday for weekly stepping
      const day = start.getDay(); // 0 Sun … 6 Sat
      const monday = new Date(start);
      monday.setDate(start.getDate() - ((day + 6) % 7));
      for (let d = new Date(monday); d <= end; d.setDate(d.getDate()+7)) {
        const y = d.getFullYear(), m = String(d.getMonth()+1).padStart(2,'0'), dd = String(d.getDate()).padStart(2,'0');
        const weekStart = `${y}-${m}-${dd}`;
        const url = withUnitId(CAL_WEEK_TEMPLATE, unitId) + `?week_start=${weekStart}`;
        try {
          const r = await fetch(url, { headers: { 'X-CSRFToken': CSRF_TOKEN }});
          const j = await r.json();
          if (j.ok && Array.isArray(j.sessions)) {
            j.sessions.forEach(s => uniq.set(String(s.id), s));
          }
        } catch {}
      }
      return Array.from(uniq.values());
    }

    const toISO = (s) => {
      const [d,m,y] = (s || '').split('/').map(Number);
      return (y && m && d) ? `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}` : null;
    };

    sessions = await fetchAllSessions(unitId, toISO(start_date), toISO(end_date));
  } else {
    console.log('No calendar and no valid date range, sessions will be empty');
    sessions = [];
  }

  console.log('Final sessions count for review:', sessions.length);

  // Render sessions like the screenshot
  const ulS = document.getElementById('rv_sessions');
  ulS.innerHTML = '';
  const dayName = (d) => ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][d];
  const timeHM = (dt) => dt.toTimeString().slice(0,5);
  
  sessions.sort((a,b)=> a.start.localeCompare(b.start)).forEach(s => {
    const st = new Date(s.start), en = new Date(s.end);
    const sessionName = s.extendedProps?.session_name || s.title?.split('\n')[0] || 'New Session';
    const venueName = s.extendedProps?.venue || (s.title?.includes('\n') ? s.title.split('\n')[1] : '');
    const staffCount = (s.extendedProps?.lead_required || 1) + (s.extendedProps?.support_required || 0);
    
    const li = document.createElement('li');
    li.className = 'flex items-center justify-between border border-gray-200 rounded-xl px-4 py-3';
    li.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="w-2.5 h-2.5 rounded-full bg-gray-300 inline-block"></span>
        <div>
          <div class="font-medium">${sessionName}</div>
          <div class="text-sm text-gray-600">${dayName(st.getDay())} • ${timeHM(st)}–${timeHM(en)} • Starting ${st.toLocaleDateString()}${venueName ? ' • ' + venueName : ''}</div>
        </div>
      </div>
      <div class="text-sm text-gray-500">${staffCount} staff</div>
    `;
    ulS.appendChild(li);
  });
  document.getElementById('rv_sess_count').textContent = sessions.length;
}

// Hook into step changes
const __origSetStep = setStep;
setStep = function(n){
  __origSetStep(n);
  if (n === 4) { populateReview(); }
};

// Update the blue Session Overview card
function updateSessionOverview() {
  const nameInput = document.getElementById('inspName');
  const venueSelect = document.getElementById('inspVenue');
  
  if (!nameInput || !venueSelect || !window.__editingEvent) {
    console.warn('updateSessionOverview: missing elements or no editing event');
    return;
  }
  
  // Get current values
  const sessionName = nameInput.value.trim() || 'New Session';
  let venueName = '';
  
  if (venueSelect.tagName === 'SELECT') {
    const selectedOption = venueSelect.options[venueSelect.selectedIndex];
    venueName = selectedOption ? selectedOption.textContent.trim() : '';
  } else {
    venueName = venueSelect.value.trim();
  }
  
  console.log('updateSessionOverview called for event:', window.__editingEvent.id, {
    sessionName,
    venueName,
    currentTitle: window.__editingEvent.title
  });
  
  // ONLY update if this is the currently edited event
  if (window.__editingEvent) {
    let displayTitle = sessionName;
    if (venueName && 
        venueName !== 'Select a venue' && 
        venueName !== '— Select a venue —' && 
        venueName !== '' &&
        venueName !== 'Select a venue') {
      displayTitle = `${sessionName}\n${venueName}`;
    }
    
    console.log('Setting title for event', window.__editingEvent.id, 'from:', window.__editingEvent.title, 'to:', displayTitle);
    
    // Update ONLY the specific event being edited
    window.__editingEvent.setProp('title', displayTitle);
  }
}

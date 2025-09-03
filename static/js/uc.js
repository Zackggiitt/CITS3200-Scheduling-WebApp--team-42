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
  UPLOAD_SETUP_CSV,
  UPLOAD_SESSIONS_TEMPLATE
} = window.FLASK_ROUTES || {};

// ===== Helpers to inject ids into route templates =====
function withUnitId(tpl, id)     { return tpl.replace(/\/0(\/|$)/, `/${id}$1`); }
function withSessionId(tpl, id)  { return tpl.replace(/0(\/|$)/, `${id}$1`); }
function getUnitId() {
  return document.getElementById('unit_id')?.value || '';
}

// ===== Modal open/close =====
function openCreateUnitModal() {
    
  window.__venueCache = {};
  window.__editingEvent = null;
  _pendingStart = null;
  _pendingEnd = null;
  if (calendar) {
    calendar.removeAllEvents();
    calendar.destroy();
    calendar = null;
  }
  window.__calendarInitRan = false;

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
        const newCloseBtn = closeBtn.cloneNode(true);
        closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
        
        // Add the new event listener
        newCloseBtn.onclick = showCloseConfirmationPopup;
        console.log('Close button wired to showCloseConfirmationPopup');
    }
    
    // Also handle ESC key
    const handleEscKey = (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        showCloseConfirmationPopup();
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
        showCloseConfirmationPopup();
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

  form.append('force_new', 'true');
  form.append('timestamp', Date.now().toString());

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
          Facilitators created: ${data.created_users} · Linked: ${data.linked_facilitators}
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

// ===== Sessions CSV Upload (Step 3b) =====
const sessionsInput = document.getElementById('sessions_csv');
const sessionsFileName = document.getElementById('sessions_file_name');
const sessionsStatus = document.getElementById('sessions_upload_status');
const uploadSessionsBtn = document.getElementById('uploadSessionsBtn');

if (sessionsInput) {
  sessionsInput.addEventListener('change', () => {
    sessionsFileName.textContent = sessionsInput.files?.[0]?.name || 'No file selected';
  });
}

async function uploadSessionsCsv() {
  const unitId = document.getElementById('unit_id').value;
  if (!unitId) {
    sessionsStatus.className = 'upload-status error';
    sessionsStatus.classList.remove('hidden');
    sessionsStatus.textContent = 'Please complete Step 1 (Unit Information) first.';
    return;
  }
  if (!sessionsInput.files?.length) {
    sessionsStatus.className = 'upload-status error';
    sessionsStatus.classList.remove('hidden');
    sessionsStatus.textContent = 'Choose a CSV file to upload.';
    return;
  }

  const fd = new FormData();
  fd.append('sessions_csv', sessionsInput.files[0]);

  sessionsStatus.className = 'upload-status';
  sessionsStatus.classList.remove('hidden');
  sessionsStatus.textContent = 'Uploading…';

  const url = withUnitId(window.FLASK_ROUTES.UPLOAD_SESSIONS_TEMPLATE, unitId);
  try {
    const res = await fetch(url, {
      method: 'POST',
      body: fd,
      headers: { 'X-CSRFToken': CSRF_TOKEN }
    });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      const errs = (data.errors || [data.error]).filter(Boolean);
      sessionsStatus.className = 'upload-status error';
      sessionsStatus.innerHTML = `
        <div class="font-semibold">Upload failed</div>
        <ul class="list-disc list-inside text-sm">
          ${errs.map((x) => `<li>${x}</li>`).join("")}
        </ul>`;
      return;
    }

    sessionsStatus.className = 'upload-status success';
    sessionsStatus.innerHTML = `
      <div class="font-semibold">Upload successful</div>
      <div class="text-sm mt-1">Sessions created: ${data.created || 0}, Skipped: ${data.skipped || 0}</div>`;

    // Refresh calendar so new sessions appear
    if (window.calendar) {
      window.calendar.refetchEvents?.();
    }
  } catch (err) {
    sessionsStatus.className = 'upload-status error';
    sessionsStatus.textContent = String(err.message || 'Unexpected error during upload.');
  }
}

if (uploadSessionsBtn) {
  uploadSessionsBtn.addEventListener('click', uploadSessionsCsv);
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

  // Delete 
  const deleteBtn = document.getElementById('inspDelete');
  if (deleteBtn) {
    // Clear all existing event handlers completely
    deleteBtn.onclick = null;
    deleteBtn.removeAttribute('onclick');
    
    // Remove any existing event listeners
    const newDeleteBtn = deleteBtn.cloneNode(true);
    deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
    
    // Create a fresh delete handler for this specific session
    let isDeleting = false; 

    const deleteHandler = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (isDeleting) {
        console.log('Delete already in progress, ignoring click');
        return;
      }
      
      console.log('Delete button clicked for session:', ev.id)

      newDeleteBtn.disabled = true;
      newDeleteBtn.textContent = 'Deleting...';
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
          // Re-enable button on error
          isDeleting = false;
          newDeleteBtn.disabled = false;
          newDeleteBtn.textContent = 'Delete';
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

        // Clear the editing handle IMMEDIATELY
        window.__editingEvent = null;

        // Close the inspector IMMEDIATELY
        closeInspector();

        console.log('Delete operation completed successfully for:', eventId);

      } catch (err) {
        console.error('Delete error:', err);
        alert(`Failed to delete: ${err.message}`);
        
        // Re-enable button on error
        isDeleting = false;
        newDeleteBtn.disabled = false;
        newDeleteBtn.textContent = 'Delete';
      }
    };

    // Attach the handler to the NEW button
    newDeleteBtn.addEventListener('click', deleteHandler, { once: false });
    
    console.log('Delete button wired for session:', ev.id);
  }

  // Cancel
  document.getElementById('inspCancel').onclick = closeInspector;

  // ESC to close
  document.addEventListener('keydown', function esc(e){
    if (e.key === 'Escape') { 
      closeInspector(); 
      document.removeEventListener('keydown', esc); 
    }
  }, { once: true });

  // Click outside to close
  const wrap = document.getElementById('calendar_wrap');
  function outside(e){
    if (!inspector.contains(e.target)) { 
      closeInspector(); 
      wrap.removeEventListener('mousedown', outside); 
    }
  }
  wrap.addEventListener('mousedown', outside, { once: true });
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
    unitIdEl.value = '';
  }

  // Clear setup completion flag
  const setupFlagEl = document.getElementById('setup_complete');
  if (setupFlagEl) {
    setupFlagEl.value = 'false';
  }

  // Destroy calendar completely and clear its events
  if (calendar) {
    calendar.removeAllEvents(); // Clear all events to prevent double-ups
    calendar.destroy();
    calendar = null;
  }
  window.__calendarInitRan = false;

  // Clear venue cache and any other global caches
  window.__venueCache = {};
  window.__editingEvent = null; // Ensure no lingering edit state

  // Clear any editing state
  _pendingStart = null;
  _pendingEnd = null;

  // Clear time pickers
  if (_startTP) {
    _startTP.destroy();
    _startTP = null;
  }
  if (_endTP) {
    _endTP.destroy();
    _endTP = null;
  }
  if (_recUntilPicker) {
    _recUntilPicker.destroy();
    _recUntilPicker = null;
  }

  // Hide the modal
  const form = document.getElementById('create-unit-form');
  if (form) {
    form.reset(); // Fully reset the form to clear all inputs
  }

  const setupCsv = document.getElementById('setup_csv');
  const sessionsInput = document.getElementById('sessions_csv');
  const fileName = document.getElementById('file_name');
  const sessionsFileName = document.getElementById('sessions_file_name');

  if (setupCsv) setupCsv.value = '';
  if (sessionsInput) sessionsInput.value = '';
  if (fileName) fileName.textContent = '';
  if (sessionsFileName) sessionsFileName.textContent = '';
  
  // Hide all status messages
  const uploadStatus = document.getElementById('upload_status');
  const sessionsStatus = document.getElementById('sessions_upload_status');
  if (uploadStatus) uploadStatus.classList.add('hidden');
  if (sessionsStatus) sessionsStatus.classList.add('hidden');

  // Reset date pickers to today
  const today = new Date();
  if (startPicker) {
    startPicker.setDate(today);
    startInput.value = startPicker.formatDate(today, DATE_FMT);
  }
  if (endPicker) {
    endPicker.setDate(today);
    endInput.value = endPicker.formatDate(today, DATE_FMT);
  }
  
  // Hide date summary
  const dateSummary = document.getElementById('date-summary');
  if (dateSummary) dateSummary.classList.add('hidden');

  // Hide the modal
  const modal = document.getElementById("createUnitModal");
  if (modal) {
    modal.classList.remove("flex");
    modal.classList.add("hidden");
  }

  // Reset to step 1
  setStep(1);
  
  console.log('Modal completely closed and reset');
}


function handleCloseUnitModal() {
  const modal = document.getElementById("createUnitModal");

  // Reset wizard fields (unit info, date pickers, etc.)
  resetCreateUnitWizard();
  document.getElementById('unit_id').value = '';
  document.getElementById('setup_complete').value = 'false';

  // Reset date inputs + summary
  if (startPicker) startPicker.clear();
  if (endPicker) endPicker.clear();
  document.getElementById('start_date_input').value = '';
  document.getElementById('end_date_input').value = '';
  document.getElementById('date-summary').classList.add('hidden');

  // Reset / destroy the session calendar
  if (calendar) {
    try { calendar.destroy(); } catch (err) { console.warn('Error destroying calendar', err); }
    calendar = null;
  }
  window.__calendarInitRan = false;

  // Hide the modal
  modal.classList.remove("flex");
  modal.classList.add("hidden");

  // Reset step navigation to step 1
  setStep(1);

  console.log("Create Unit modal closed and state reset.");
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
        <button class="popup-btn popup-btn-confirm-close" onclick="confirmCloseModal()">
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

async function confirmCloseModal() {
  closeConfirmationPopup();
  
  // Mark draft as cancelled instead of trying to delete
  const unitId = document.getElementById('unit_id').value;
  if (unitId) {
    try {
      console.log('Marking draft as cancelled on backend:', unitId);
      
      const form = new FormData();
      form.append('unit_id', unitId);
      form.append('action', 'cancel_draft');
      form.append('cancelled', 'true');
      
      const response = await fetch(CREATE_OR_GET_DRAFT, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN },
        body: form
      });
      
      if (response.ok) {
        console.log('Draft successfully marked as cancelled');
      } else {
        console.warn('Failed to cancel draft on backend, but continuing with close');
      }
    } catch (error) {
      console.error('Error cancelling draft:', error);
      // Continue with close even if backend call fails
    }
  }
  
  closeCreateUnitModal();
}

async function createUnit() {
  // Validate required fields first
  const { unit_name, unit_code, semester, year, start_date, end_date } = readUnitBasics();
  const unitId = document.getElementById('unit_id').value;
  
  if (!unitId) {
    alert('No unit ID found. Please go back and complete the previous steps.');
    return;
  }
  
  if (!unit_name || !unit_code || !semester || !year || !start_date || !end_date) {
    alert('Please complete all required fields before creating the unit.');
    return;
  }
  
  // Call createUnitFinal directly 
  createUnitFinal();
}

async function createUnitFinal() {
  const createBtn = document.getElementById('submit-btn');
  
  if (createBtn) {
    createBtn.disabled = true;
    createBtn.textContent = 'Creating Unit...';
  }

  try {
    const unitId = document.getElementById('unit_id').value;
    
    if (!unitId) {
      throw new Error('No unit ID found. Please go back and complete the previous steps.');
    }

    console.log('Finalizing unit with ID:', unitId);

    // Since the unit draft already exists and sessions are created,
    // we just need to mark it as complete
    document.getElementById('setup_complete').value = 'true';
    
    // Simulate a brief delay to show the "Creating..." state
    await new Promise(resolve => setTimeout(resolve, 1000));

    console.log('Unit creation process completed');

    // MAKE SURE THIS LINE IS HERE:
    showUnitCreatedSuccessPopup();

  } catch (error) {
    console.error('Error creating unit:', error);
    alert(`Failed to create unit: ${error.message}`);
    
    // Re-enable button on error
    if (createBtn) {
      createBtn.disabled = false;
      createBtn.textContent = 'Create Unit';
    }
  }
}

// Wire up the Create Unit button when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const createUnitBtn = document.getElementById('submit-btn');
  if (createUnitBtn) {
    createUnitBtn.onclick = createUnit;
    console.log('Create Unit button wired successfully');
  } else {
    console.warn('Create Unit button not found');
  }
});

// Add this function to show the success popup
function showUnitCreatedSuccessPopup() {
  // Create popup HTML
  const popup = document.createElement('div');
  popup.className = 'simple-popup';
  popup.innerHTML = `
    <div class="popup-content">
      <div class="popup-title" style="color: #059669;">Success</div>
      <div class="popup-message">
        Unit created successfully!
      </div>
      <div class="popup-buttons">
        <button class="popup-btn popup-btn-confirm" onclick="closeSuccessPopup()">
          OK
        </button>
      </div>
    </div>
  `;
  
  // Add to body
  document.body.appendChild(popup);
  
  // Close on backdrop click
  popup.addEventListener('click', (e) => {
    if (e.target === popup) {
      closeSuccessPopup();
    }
  });
  
  // Close on ESC key
  const handleEscKey = (e) => {
    if (e.key === 'Escape') {
      closeSuccessPopup();
      document.removeEventListener('keydown', handleEscKey);
    }
  };
  document.addEventListener('keydown', handleEscKey);
}

// Add helper function to close success popup
function closeSuccessPopup() {
  const popup = document.querySelector('.simple-popup');
  if (popup) {
    popup.remove();
  }
  
  // Close the modal and refresh after popup is closed
  closeCreateUnitModal();
  window.location.reload();
}

// Update your createUnitFinal function around line 1170
async function createUnitFinal() {
  const createBtn = document.getElementById('submit-btn');
  
  if (createBtn) {
    createBtn.disabled = true;
    createBtn.textContent = 'Creating Unit...';
  }

  try {
    const unitId = document.getElementById('unit_id').value;
    
    if (!unitId) {
      throw new Error('No unit ID found. Please go back and complete the previous steps.');
    }

    console.log('Finalizing unit with ID:', unitId);

    // Since the unit draft already exists and sessions are created,
    // we just need to mark it as complete
    document.getElementById('setup_complete').value = 'true';
    
    // Simulate a brief delay to show the "Creating..." state
    await new Promise(resolve => setTimeout(resolve, 1000));

    console.log('Unit creation process completed');

    // Show success popup instead of closing immediately
    showUnitCreatedSuccessPopup();

  } catch (error) {
    console.error('Error creating unit:', error);
    alert(`Failed to create unit: ${error.message}`);
    
    // Re-enable button on error
    if (createBtn) {
      createBtn.disabled = false;
      createBtn.textContent = 'Create Unit';
    }
  }
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

  // Clean up delete button completely - find the current delete button
  const deleteBtn = document.getElementById('inspDelete');
  if (deleteBtn) {
    // Clone to remove ALL event listeners
    const cleanDeleteBtn = deleteBtn.cloneNode(true);
    deleteBtn.parentNode.replaceChild(cleanDeleteBtn, deleteBtn);
    
    // Reset button state
    cleanDeleteBtn.disabled = false;
    cleanDeleteBtn.textContent = 'Delete';
    cleanDeleteBtn.onclick = null;
  }

  // Hide panel
  inspector.classList.remove('open');
  inspector.classList.add('hidden');
  
  // Clear the editing event reference
  window.__editingEvent = null;

  // Clear pending time edits
  _pendingStart = null;
  _pendingEnd = null;
  
  console.log('Inspector closed and cleaned up');
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

// --- Completed Unit banner: dismiss + remember (per unit) ---
function initCompletedUnitBanners() {
  const banners = document.querySelectorAll('[id^="unit-complete-"]');
  if (!banners.length) return;

  banners.forEach((banner) => {
    const id = banner.id;
    const key = `uc_notice_dismissed_${id}`;

    // If previously dismissed, hide it immediately
    try {
      if (localStorage.getItem(key) === '1') {
        banner.style.display = 'none';
        return;
      }
    } catch (e) { /* ignore storage errors */ }

    // Wire the close button
    const closeBtn = banner.querySelector('.uc-banner__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        banner.remove();
        try { localStorage.setItem(key, '1'); } catch (e) { /* ignore */ }
      });
    }
  });
}


document.addEventListener('DOMContentLoaded', initCompletedUnitBanners);

function initFacilitatorFilters() {
  const filterDropdown = document.querySelector('.fac-list details');
  const searchInput = document.querySelector('.fac-list input[type="search"]');
  const facilitatorCards = document.querySelectorAll('.fac-list article');
  
  if (!filterDropdown) return;

  let currentStatusFilter = 'all';

  // Search functionality
  function filterFacilitators() {
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    facilitatorCards.forEach(card => {
      const name = card.querySelector('h4')?.textContent?.toLowerCase() || '';
      const email = card.querySelector('a[href^="mailto:"]')?.textContent?.toLowerCase() || '';
      
      // Get status from badges
      const badges = card.querySelectorAll('.status-badge, [class*="badge"]');
      let cardStatus = 'inactive';
      
      badges.forEach(badge => {
        const text = badge.textContent.toLowerCase();
        if (text.includes('ready') || text.includes('complete')) {
          cardStatus = 'ready';
        } else if (text.includes('needs availability') || text.includes('availability')) {
          cardStatus = 'needs_availability';
        } else if (text.includes('pending') || text.includes('setup')) {
          cardStatus = 'pending_setup';
        }
      });

      // Check search match
      const searchMatch = !searchTerm || 
        name.includes(searchTerm) || 
        email.includes(searchTerm);

      // Check status filter match
      const statusMatch = currentStatusFilter === 'all' || 
        currentStatusFilter === cardStatus;

      // Show/hide card
      if (searchMatch && statusMatch) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });

    // Update visible count
    const visibleCards = Array.from(facilitatorCards).filter(card => 
      card.style.display !== 'none'
    );
    
    const countEl = document.querySelector('.fac-list .ml-2');
    if (countEl) {
      const totalCount = facilitatorCards.length;
      countEl.textContent = `${visibleCards.length} of ${totalCount}`;
    }
  }

  // Wire up search input if it exists
  if (searchInput) {
    searchInput.addEventListener('input', filterFacilitators);
  }

  // Wire up status filter buttons
  const filterButtons = filterDropdown.querySelectorAll('button[type="button"]');
  filterButtons.forEach(button => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const text = button.textContent.toLowerCase().trim();
      
      if (text === 'all status') {
        currentStatusFilter = 'all';
      } else if (text === 'ready') {
        currentStatusFilter = 'ready';
      } else if (text === 'needs availability') {
        currentStatusFilter = 'needs_availability';
      } else if (text === 'pending setup') {
        currentStatusFilter = 'pending_setup';
      }

      // Update the summary text to show selected filter
      const summary = filterDropdown.querySelector('summary');
      if (summary && text !== 'all status') {
        summary.innerHTML = `${button.textContent} <span class="material-icons text-base">expand_more</span>`;
      } else if (summary) {
        summary.innerHTML = `All Status <span class="material-icons text-base">expand_more</span>`;
      }

      // Close the dropdown
      filterDropdown.removeAttribute('open');
      
      // Apply filter
      filterFacilitators();
    });
  });

  // Close dropdown when clicking outside - FIXED VERSION
  const closeHandler = (e) => {
    if (!filterDropdown.contains(e.target)) {
      filterDropdown.removeAttribute('open');
    }
  };
  
  // Remove any existing listeners and add the new one
  document.removeEventListener('click', closeHandler, true);
  document.addEventListener('click', closeHandler, true);

  // Prevent dropdown from closing when clicking inside
  filterDropdown.addEventListener('click', (e) => {
    e.stopPropagation();
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && filterDropdown.hasAttribute('open')) {
      filterDropdown.removeAttribute('open');
    }
  });
}

// --- Unit Tabs (switch panels, remember per unit) ---
function initUnitTabs() {
  const tabsRail = document.querySelector('.uc-tabs');
  if (!tabsRail) return;

  const unitId = tabsRail.getAttribute('data-unit-id') || '0';
  const tabs = Array.from(tabsRail.querySelectorAll('.uc-tab'));
  const panels = {
    dashboard: document.getElementById('panel-dashboard'),
    schedule:  document.getElementById('panel-schedule'),
    staffing:  document.getElementById('panel-staffing'),
    team:      document.getElementById('panel-team')
  };

  function showTab(key, focus = false) {
    tabs.forEach(tab => {
      const active = tab.dataset.tab === key;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.tabIndex = active ? 0 : -1;
      if (active && focus) tab.focus();
    });

    Object.entries(panels).forEach(([k, el]) => {
      if (!el) return;
      if (k === key) el.removeAttribute('hidden'); else el.setAttribute('hidden', '');
    });

    try { localStorage.setItem(`uc_tab_${unitId}`, key); } catch (e) {}

    if (key === 'staffing') {
      setTimeout(initFacilitatorFilters, 100);
    }
  }

  // Click to activate
  tabs.forEach(tab => {
    tab.addEventListener('click', () => showTab(tab.dataset.tab, false));
  });

  // Keyboard: arrows/Home/End
  tabsRail.addEventListener('keydown', (e) => {
    const idx = tabs.findIndex(t => t.classList.contains('is-active'));
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      const dir = e.key === 'ArrowRight' ? 1 : -1;
      const next = (idx + dir + tabs.length) % tabs.length;
      showTab(tabs[next].dataset.tab, true);
    } else if (e.key === 'Home') {
      e.preventDefault();
      showTab(tabs[0].dataset.tab, true);
    } else if (e.key === 'End') {
      e.preventDefault();
      showTab(tabs[tabs.length - 1].dataset.tab, true);
    }
  });

  // Initial tab: last chosen for this unit, else Dashboard
  let initial = 'dashboard';
  try {
    const saved = localStorage.getItem(`uc_tab_${unitId}`);
    if (saved && panels[saved]) initial = saved;
  } catch (e) {}
  showTab(initial, false);
}

document.addEventListener('DOMContentLoaded', initUnitTabs);



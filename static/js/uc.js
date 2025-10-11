// ===== Bootstrapped values from HTML =====
const CSRF_TOKEN = window.CSRF_TOKEN || '';
const {
  CAL_WEEK_TEMPLATE,
  CREATE_SESS_TEMPLATE,
  UPDATE_SESS_TEMPLATE,
  DELETE_SESS_TEMPLATE,
  LIST_FACILITATORS_TEMPLATE,
  CREATE_OR_GET_DRAFT,
  UPLOAD_SETUP_CSV,
  REMOVE_FACILITATORS_TEMPLATE,
  UPLOAD_SESSIONS_TEMPLATE,
  UPLOAD_CAS_TEMPLATE
} = window.FLASK_ROUTES || {};

const CHART_JS_URL = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';


// ===== Helpers to inject ids into route templates =====
function withUnitId(tpl, id)     { return tpl.replace(/\/0(\/|$)/, `/${id}$1`); }
function withSessionId(tpl, id)  { return tpl.replace(/0(\/|$)/, `${id}$1`); }
function getUnitId() {
  // Try to get from unit_id input first (for create unit modal)
  const unitIdInput = document.getElementById('unit_id');
  if (unitIdInput && unitIdInput.value) {
    return unitIdInput.value;
  }
  
  // Try to get from the tabs navigation data attribute
  const tabsNav = document.querySelector('[data-unit-id]');
  if (tabsNav) {
    return tabsNav.getAttribute('data-unit-id');
  }
  
  return '';
}

// ===== Global event handlers =====
let handleEscKey, handleEnterKey;

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
  
  // Reset modal title and button text for create mode
  const modalTitle = document.querySelector('#create-unit-title');
  if (modalTitle) {
    modalTitle.textContent = 'Create New Unit';
  }
  const submitBtn = document.querySelector('#submit-btn');
  if (submitBtn) {
    submitBtn.textContent = 'Create Unit';
  }


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
    
    // Define event handlers
    handleEscKey = (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        showCloseConfirmationPopup();
      }
    };
    
    handleEnterKey = (e) => {
      if (e.key === 'Enter' && !modal.classList.contains('hidden')) {
        e.preventDefault(); // Prevent form submission
        nextStep(); // Go to next step instead
      }
    };
    
    // Remove existing listeners and add new ones
    document.removeEventListener('keydown', handleEscKey);
    document.removeEventListener('keydown', handleEnterKey);
    document.addEventListener('keydown', handleEscKey);
    document.addEventListener('keydown', handleEnterKey);
}

function openEditUnitModal() {
  // Get current unit data from the page
  const unitCode = document.querySelector('.unit-card h2').textContent.trim();
  const unitName = document.querySelector('.unit-card p.font-medium').textContent.trim();
  const semesterYear = document.querySelector('.chip--neutral').textContent.trim();
  const [semester, year] = semesterYear.split(', ');
  
  // Extract dates from the unit card display
  const dateText = document.querySelector('.unit-card p.text-gray-500.text-sm')?.textContent?.trim();
  const dateMatch = dateText ? dateText.match(/(\d{1,2}\/\d{1,2}\/\d{4})\s*-\s*(\d{1,2}\/\d{1,2}\/\d{4})/) : null;
  let startDate = null;
  let endDate = null;
  
  if (dateMatch && dateMatch.length >= 3) {
    startDate = dateMatch[1]; // MM/DD/YYYY format
    endDate = dateMatch[2];    // MM/DD/YYYY format
  }
  
  // Get current unit ID from the URL or data attribute
  const currentUnitId = getUnitId();
  
  // Open the create modal
  openCreateUnitModal();
  
  // Pre-populate the form with current unit data
  setTimeout(() => {
    // Set the unit ID for update
    document.getElementById('unit_id').value = currentUnitId;
    
    // Pre-populate form fields
    document.querySelector('input[name="unit_code"]').value = unitCode;
    document.querySelector('input[name="unit_name"]').value = unitName;
    document.querySelector('input[name="semester"]').value = semester;
    document.querySelector('input[name="year"]').value = year;
    
    // Set the dates if they were found
    if (startDate && endDate) {
      try {
        // Convert MM/DD/YYYY to DD/MM/YYYY format for flatpickr
        const startParts = startDate.split('/');
        const endParts = endDate.split('/');
        
        if (startParts.length === 3 && endParts.length === 3) {
          const startDateFormatted = `${startParts[1]}/${startParts[0]}/${startParts[2]}`;
          const endDateFormatted = `${endParts[1]}/${endParts[0]}/${endParts[2]}`;
          
          // Ensure date pickers are available before setting dates
          if (typeof startPicker !== 'undefined' && startPicker) {
            startPicker.setDate(startDateFormatted, true);
          }
          if (typeof endPicker !== 'undefined' && endPicker) {
            endPicker.setDate(endDateFormatted, true);
          }
          
          // Update the hidden input values
          const startInput = document.getElementById('start_date_input');
          const endInput = document.getElementById('end_date_input');
          if (startInput) startInput.value = startDateFormatted;
          if (endInput) endInput.value = endDateFormatted;
          
          // Update the date summary
          if (typeof updateDateSummary === 'function') {
            updateDateSummary();
          }
        }
      } catch (error) {
        console.warn('Error setting unit dates in edit modal:', error);
      }
    }
    
    // Update the modal title to indicate editing
    const modalTitle = document.querySelector('#create-unit-title');
    if (modalTitle) {
      modalTitle.textContent = 'Edit Unit';
    }
    
    // Change the submit button text
    const submitBtn = document.querySelector('#submit-btn');
    if (submitBtn) {
      submitBtn.textContent = 'Update Unit';
    }
    
    // Skip to step 1 (Unit Information) since we're editing
    setStep(1);
  }, 200);
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
const TOTAL_STEPS = 5;

function setStep(n) {
  currentStep = n;
  document.querySelectorAll('.wizard-step').forEach(s => {
    s.classList.toggle('hidden', parseInt(s.dataset.step) !== currentStep);
  });
  
  // Ensure CSV upload card remains visible on step 3 after successful upload
  if (n === 3) {
    const setupComplete = document.getElementById('setup_complete')?.value === 'true';
    const wrapUpload = document.getElementById('setup_wrap');
    if (setupComplete && wrapUpload) {
      wrapUpload.classList.remove('hidden');
    }
  }
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

  if (currentStep === 4) {
    // Bulk staffing step - no validation required, can proceed to review
    return setStep(5);
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
        <div class="flex items-center justify-between">
          <div>
            <div class="font-semibold">Upload successful</div>
            <div class="text-sm mt-1">
              Facilitators created: ${data.created_users} · Linked: ${data.linked_facilitators}
            </div>
          </div>
          <button 
            id="remove_csv_btn" 
            class="ml-3 text-red-600 hover:text-red-800 transition-colors"
            title="Remove CSV data"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>`;
      setupFlagEl.value = "true";
      fileNameEl.textContent = file.name;
      statusBox.scrollIntoView({ block: "nearest", behavior: "smooth" });

      // Ensure CSV upload card remains visible after successful upload
      const wrapUpload = document.getElementById('setup_wrap');
      if (wrapUpload) {
        wrapUpload.classList.remove('hidden');
      }
      
      showCalendarIfReady();
      if (!window.__calendarInitRan) {
        window.__calendarInitRan = true;
        initCalendar();
      } else {
        refreshCalendarRange();
      }
      
      // Add event listener for remove button
      const removeBtn = document.getElementById('remove_csv_btn');
      if (removeBtn) {
        removeBtn.addEventListener('click', removeFacilitatorsCsv);
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

// ===== Remove Facilitators CSV =====
async function removeFacilitatorsCsv() {
  const unitId = unitIdEl.value;
  if (!unitId) {
    statusBox.textContent = 'Missing unit id.';
    statusBox.classList.add('error');
    return;
  }

  if (!confirm('Are you sure you want to remove all facilitators from this unit? This action cannot be undone.')) {
    return;
  }

  statusBox.classList.remove('hidden', 'success', 'error');
  statusBox.textContent = 'Removing facilitators...';
  statusBox.classList.add('error'); // Use error styling for removal

  try {
    const url = withUnitId(REMOVE_FACILITATORS_TEMPLATE, unitId);
    const res = await fetch(url, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': CSRF_TOKEN,
        'X-CSRF-Token': CSRF_TOKEN,
      },
    });

    let data;
    try {
      const text = await res.text();
      data = JSON.parse(text);
    } catch (e) {
      throw new Error(`Non-JSON response (${res.status}): ${text.slice(0, 300)}`);
    }

    if (!res.ok || !data.ok) {
      statusBox.textContent = data.error || 'Failed to remove facilitators';
      return;
    }

    // Success - reset everything
    statusBox.classList.remove('error');
    statusBox.classList.add('success');
    statusBox.innerHTML = `
      <div class="font-semibold">Facilitators removed</div>
      <div class="text-sm mt-1">Removed ${data.removed_facilitators} facilitator(s) from unit</div>
    `;
    
    // Reset form elements
    setupFlagEl.value = 'false';
    fileNameEl.textContent = 'No file selected';
    uploadInput.value = '';
    
    // Hide the status after a delay
    setTimeout(() => {
      statusBox.classList.add('hidden');
      statusBox.classList.remove('success', 'error');
      statusBox.textContent = '';
    }, 3000);

  } catch (err) {
    console.error(err);
    statusBox.textContent = String(err.message || 'Unexpected error during removal.');
    statusBox.classList.add('error');
  }
}

// ===== Remove Individual Facilitator =====
async function removeIndividualFacilitator(email, buttonElement) {
  if (!confirm(`Are you sure you want to remove ${email} from this unit?`)) {
    return;
  }

  const unitId = unitIdEl.value;
  if (!unitId) {
    alert('Missing unit id.');
    return;
  }

  try {
    // Construct the URL manually to avoid template issues
    const url = `/unitcoordinator/units/${unitId}/facilitators/${encodeURIComponent(email)}`;
    const res = await fetch(url, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': CSRF_TOKEN,
        'X-CSRF-Token': CSRF_TOKEN,
      },
    });

    let data;
    try {
      const text = await res.text();
      data = JSON.parse(text);
    } catch (e) {
      throw new Error(`Non-JSON response (${res.status}): ${text.slice(0, 300)}`);
    }

    if (!res.ok || !data.ok) {
      alert(data.error || 'Failed to remove facilitator');
      return;
    }

    // Remove the facilitator from the UI immediately
    const listItem = buttonElement.closest('li');
    if (listItem) {
      listItem.remove();
      
      // Update the count
      const facilitatorList = document.getElementById('rv_facilitators');
      const remainingCount = facilitatorList.querySelectorAll('li').length;
      document.getElementById('rv_fac_count').textContent = remainingCount;
      
      // Show success message
      const statusBox = document.getElementById('upload_status');
      if (statusBox) {
        statusBox.classList.remove('hidden', 'success', 'error');
        statusBox.classList.add('success');
        statusBox.innerHTML = `
          <div class="font-semibold">Facilitator removed</div>
          <div class="text-sm mt-1">${email} has been removed from the unit</div>
        `;
        
        // Hide message after 3 seconds
        setTimeout(() => {
          statusBox.classList.add('hidden');
          statusBox.classList.remove('success', 'error');
          statusBox.textContent = '';
        }, 3000);
      }
    }

  } catch (err) {
    console.error(err);
    alert(`Error removing facilitator: ${err.message || 'Unexpected error'}`);
  }
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

    // Ensure calendar section is visible and refresh/init calendar
    const setupFlagEl = document.getElementById('setup_complete');
    if (setupFlagEl) setupFlagEl.value = 'true';
    showCalendarIfReady();
    if (window.calendar) {
      window.calendar.refetchEvents?.();
    } else if (!window.__calendarInitRan) {
      window.__calendarInitRan = true;
      initCalendar();
    }
    
    // Also refresh list view data
    loadListSessionData();
  } catch (err) {
    sessionsStatus.className = 'upload-status error';
    sessionsStatus.textContent = String(err.message || 'Unexpected error during upload.');
  }
}

if (uploadSessionsBtn) {
  uploadSessionsBtn.addEventListener('click', uploadSessionsCsv);
}

// ===== CAS CSV Upload =====
const casInput = document.getElementById('cas_csv');
const casFileName = document.getElementById('cas_file_name');
const casStatus = document.getElementById('cas_upload_status');
const uploadCasBtn = document.getElementById('uploadCasBtn');

if (casInput) {
  casInput.addEventListener('change', () => {
    casFileName.textContent = casInput.files?.[0]?.name || 'No file selected';
  });
}

async function uploadCasCsv() {
  const unitId = document.getElementById('unit_id').value;
  if (!unitId) {
    casStatus.className = 'upload-status error';
    casStatus.classList.remove('hidden');
    casStatus.textContent = 'Please complete Step 1 (Unit Information) first.';
    return;
  }
  if (!casInput.files?.length) {
    casStatus.className = 'upload-status error';
    casStatus.classList.remove('hidden');
    casStatus.textContent = 'Choose a CSV file to upload.';
    return;
  }

  const fd = new FormData();
  fd.append('cas_csv', casInput.files[0]);

  casStatus.className = 'upload-status';
  casStatus.classList.remove('hidden');
  casStatus.textContent = 'Uploading…';

  const url = withUnitId(UPLOAD_CAS_TEMPLATE, unitId);
  try {
    const res = await fetch(url, {
      method: 'POST',
      body: fd,
      headers: { 'X-CSRFToken': CSRF_TOKEN }
    });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      const errs = (data.errors || [data.error]).filter(Boolean);
      casStatus.className = 'upload-status error';
      casStatus.innerHTML = `
        <div class="font-semibold">Upload failed</div>
        <ul class="list-disc list-inside text-sm">
          ${errs.map((x) => `<li>${x}</li>`).join("")}
        </ul>`;
      return;
    }

    casStatus.className = 'upload-status success';
    casStatus.innerHTML = `
      <div class="font-semibold">Upload successful</div>
      <div class="text-sm mt-1">Sessions created: ${data.created || 0}, Skipped: ${data.skipped || 0}</div>`;

    // Mark setup complete so the calendar section is shown, then refresh/init
    const setupFlagEl = document.getElementById('setup_complete');
    if (setupFlagEl) setupFlagEl.value = 'true';
    showCalendarIfReady();

    if (window.calendar) {
      window.calendar.refetchEvents?.();
    } else {
      if (!window.__calendarInitRan) {
        window.__calendarInitRan = true;
        initCalendar();
      }
    }
    
    // Also refresh list view data
    loadListSessionData();
  } catch (err) {
    casStatus.className = 'upload-status error';
    casStatus.textContent = String(err.message || 'Unexpected error during upload.');
  }
}

if (uploadCasBtn) {
  uploadCasBtn.addEventListener('click', uploadCasCsv);
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
            venue_id: null
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

  // ---- staffing fields ----
  const leadStaffInput = document.getElementById('inspLeadStaff');
  const supportStaffInput = document.getElementById('inspSupportStaff');
  
  if (leadStaffInput) {
    leadStaffInput.value = ev.extendedProps?.lead_staff_required || 1;
  }
  if (supportStaffInput) {
    supportStaffInput.value = ev.extendedProps?.support_staff_required || 0;
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


  // ---- actions ----
  wireInspectorButtons(ev);

  // top-right
  document.getElementById('inspCloseBtn').onclick = closeInspector;
}


function wireInspectorButtons(ev) {
  const inspector = document.getElementById('calInspector');

  // Save
  document.getElementById('inspSave').onclick = async () => {
    const name = document.getElementById('inspName')?.value?.trim() || '';

    // pull times from the timing controls
    const times   = getPendingTimes();
    const pStart  = times.start || ev.start;
    const pEnd    = times.end   || ev.end || new Date(ev.start.getTime() + 60*60*1000);
    const startOut = fmtLocalYYYYMMDDHHMM(pStart);
    const endOut   = fmtLocalYYYYMMDDHHMM(pEnd);


    const leadStaff = document.getElementById('inspLeadStaff')?.value || 1;
    const supportStaff = document.getElementById('inspSupportStaff')?.value || 0;

    const payload = {
        start: startOut,
        end:   endOut,
        session_name: name,
        module_name:  name,
        title:        name,
        lead_staff_required: parseInt(leadStaff),
        support_staff_required: parseInt(supportStaff)
    };

    // recurrence from inspector UI
    payload.recurrence = readRecurrenceFromUI(pStart, pEnd);
    payload.apply_to   = 'series';

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
          window.__editingEvent.setExtendedProp('venue', '');
          window.__editingEvent.setExtendedProp('venue_id', null);
          window.__editingEvent.setExtendedProp('lead_staff_required', leadStaff);
          window.__editingEvent.setExtendedProp('support_staff_required', supportStaff);
          
          // Update the title with proper formatting
          let displayTitle = name;
          window.__editingEvent.setProp('title', displayTitle);
          
          console.log('Updated event locally:', {
            id: window.__editingEvent.id,
            title: displayTitle,
            venue: ''
          });
          
          // Refresh review step if we're on it
          if (currentStep === 5) {
            populateReview();
          }
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
    // Keep the facilitator upload section visible, only show calendar
    wrapCal.classList.remove('hidden');
    if (window.__calendarInitRan && calendar) {
      setTimeout(() => calendar.updateSize(), 0);
    }
  } else {
    wrapCal.classList.add('hidden');
  }
  // Always keep the facilitator upload section visible when on step 3
  if (wrapUpload && currentStep === 3) {
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

  // Clean up event listeners
  if (handleEscKey) {
    document.removeEventListener('keydown', handleEscKey);
  }
  if (handleEnterKey) {
    document.removeEventListener('keydown', handleEnterKey);
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

  // Reset / destroy the session calendar AND remove all events
  if (calendar) {
    try { calendar.removeAllEvents(); } catch (err) {}
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
  
  // Ensure the UI fully resets after backend cancel
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

  // 7) Inspector/recurrence small resets (safe no-ops if missing)
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
    const resF = await fetch(withUnitId(LIST_FACILITATORS_TEMPLATE, unitId), { headers: { 'X-CSRFToken': CSRF_TOKEN }});
    const dataF = await resF.json();
    const ulF = document.getElementById('rv_facilitators');
    ulF.innerHTML = '';
    if (dataF.ok) {
      (dataF.facilitators || []).forEach(f => {
        const li = document.createElement('li');
        li.className = 'flex items-center justify-between border border-gray-200 rounded-xl px-4 py-3';
        li.innerHTML = `
          <div class="flex items-center gap-3">
            <span class="w-2.5 h-2.5 rounded-full bg-blue-300 inline-block"></span>
            <div>
              <div class="font-medium">${f}</div>
              <div class="text-sm text-gray-600">Facilitator</div>
            </div>
          </div>
          <button 
            class="remove-facilitator-btn text-red-600 hover:text-red-800 transition-colors p-1 rounded"
            title="Remove facilitator"
            data-email="${f}"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        `;
        ulF.appendChild(li);
      });
      document.getElementById('rv_fac_count').textContent = (dataF.facilitators || []).length;
      
      // Add event listeners for remove buttons
      ulF.querySelectorAll('.remove-facilitator-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const email = btn.getAttribute('data-email');
          removeIndividualFacilitator(email, btn);
        });
      });
    }
  } catch {}

  // Sessions: Fetch all sessions for the review
  let sessions = [];

  const toISO = (s) => {
    const [d,m,y] = (s || '').split('/').map(Number);
    return (y && m && d) ? `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}` : null;
  };

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
      } catch (err) {
        console.warn(`Failed to fetch sessions for week ${weekStart}:`, err);
      }
    }
    return Array.from(uniq.values());
  }

  const startISO = toISO(start_date);
  const endISO = toISO(end_date);

  if (unitId && startISO && endISO) {
    sessions = await fetchAllSessions(unitId, startISO, endISO);
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
    const leadCount = s.extendedProps?.lead_staff_required || 1;
    const supportCount = s.extendedProps?.support_staff_required || 0;
    
    // Create staffing display text
    let staffingText = '';
    if (leadCount > 0 && supportCount > 0) {
      staffingText = `${leadCount} lead, ${supportCount} support`;
    } else if (leadCount > 0) {
      staffingText = `${leadCount} lead`;
    } else if (supportCount > 0) {
      staffingText = `${supportCount} support`;
    } else {
      staffingText = 'No staff';
    }
    
    const li = document.createElement('li');
    li.className = 'flex items-center justify-between border border-gray-200 rounded-xl px-4 py-3';
    li.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="w-2.5 h-2.5 rounded-full bg-gray-300 inline-block"></span>
        <div>
          <div class="font-medium">${sessionName}</div>
          <div class="text-sm text-gray-600">${dayName(st.getDay())} • ${timeHM(st)}–${timeHM(en)} • ${st.toLocaleDateString()} (${st.getDate()}/${st.getMonth() + 1})${s.extendedProps.location ? ' • ' + s.extendedProps.location : ''}</div>
        </div>
      </div>
      <div class="text-sm text-gray-500">${staffingText}</div>
    `;
    ulS.appendChild(li);
  });
  document.getElementById('rv_sess_count').textContent = sessions.length;
}

// Hook into step changes
const __origSetStep = setStep;
setStep = function(n){
  __origSetStep(n);
  if (n === 5) { populateReview(); }
};

// Update the blue Session Overview card
function updateSessionOverview() {
  const nameInput = document.getElementById('inspName');
  
  if (!nameInput || !window.__editingEvent) {
    console.warn('updateSessionOverview: missing elements or no editing event');
    return;
  }
  
  // Get current values
  const sessionName = nameInput.value.trim() || 'New Session';
  
  console.log('updateSessionOverview called for event:', window.__editingEvent.id, {
    sessionName,
    currentTitle: window.__editingEvent.title
  });
  
  // ONLY update if this is the currently edited event
  if (window.__editingEvent) {
    let displayTitle = sessionName;
    
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
    
    if (key === 'dashboard') {
      setTimeout(initSessionsOverview, 100);
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

// ===== Bulk Staffing Functionality =====
function initBulkStaffing() {
  const leadCountInput = document.getElementById('lead_count');
  const supportCountInput = document.getElementById('support_count');
  const leadDecreaseBtn = document.getElementById('lead_decrease');
  const leadIncreaseBtn = document.getElementById('lead_increase');
  const supportDecreaseBtn = document.getElementById('support_decrease');
  const supportIncreaseBtn = document.getElementById('support_increase');
  const filterSelect = document.getElementById('bulk_filter_select');
  const previewBtn = document.getElementById('preview_bulk');
  const applyBtn = document.getElementById('apply_bulk');
  const resetBtn = document.getElementById('reset_bulk');
  const moduleSelection = document.getElementById('module_selection');

  if (!leadCountInput || !supportCountInput) return;

  // Counter controls
  function updateCounter(input, delta) {
    const current = parseInt(input.value) || 0;
    const newValue = Math.max(0, current + delta);
    input.value = newValue;
  }

  leadDecreaseBtn?.addEventListener('click', () => updateCounter(leadCountInput, -1));
  leadIncreaseBtn?.addEventListener('click', () => updateCounter(leadCountInput, 1));
  supportDecreaseBtn?.addEventListener('click', () => updateCounter(supportCountInput, -1));
  supportIncreaseBtn?.addEventListener('click', () => updateCounter(supportCountInput, 1));

  // Handle radio button changes for filter type
  const filterTypeRadios = document.querySelectorAll('input[name="bulk_filter_type"]');
  filterTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      if (e.target.value === 'all_sessions') {
        moduleSelection.classList.add('hidden');
      } else if (e.target.value === 'module') {
        moduleSelection.classList.remove('hidden');
        updateFilterOptions();
      }
    });
  });

  // Update filter options (only modules now)
  async function updateFilterOptions() {
    const select = filterSelect;
    
    if (!select) return;

    // Clear existing options
    select.innerHTML = '<option value="">Choose an option...</option>';

    // Get unique modules
    const modules = await getModules();
    modules.forEach(module => {
      const option = document.createElement('option');
      option.value = module.value;
      option.textContent = module.label;
      select.appendChild(option);
    });
  }


  // Get modules from the current unit
  async function getModules() {
    const unitId = document.getElementById('unit_id')?.value;
    if (!unitId) return [];
    
    try {
      const response = await fetch(`/unitcoordinator/units/${unitId}/bulk-staffing/filters?type=module`);
      const data = await response.json();
      return data.ok ? data.options : [];
    } catch (e) {
      console.error('Failed to fetch modules:', e);
      return [];
    }
  }

  // Preview functionality
  previewBtn?.addEventListener('click', async () => {
    const selectedFilterType = document.querySelector('input[name="bulk_filter_type"]:checked')?.value;
    const selectedFilter = filterSelect.value;
    const leadCount = parseInt(leadCountInput.value) || 0;
    const supportCount = parseInt(supportCountInput.value) || 0;
    
    if (selectedFilterType === 'module' && !selectedFilter) {
      alert('Please select a module first.');
      return;
    }

    // Show preview of what will be updated
    const sessions = await getFilteredSessions(selectedFilterType, selectedFilter);
    alert(`Preview: ${sessions.length} sessions will be updated with ${leadCount} lead staff and ${supportCount} support staff.`);
  });

  // Apply functionality
  applyBtn?.addEventListener('click', async () => {
    const selectedFilterType = document.querySelector('input[name="bulk_filter_type"]:checked')?.value;
    const selectedFilter = filterSelect.value;
    const leadCount = parseInt(leadCountInput.value) || 0;
    const supportCount = parseInt(supportCountInput.value) || 0;
    
    if (selectedFilterType === 'module' && !selectedFilter) {
      alert('Please select a module first.');
      return;
    }

    // Apply bulk staffing to filtered sessions
    await applyBulkStaffing(selectedFilterType, selectedFilter, leadCount, supportCount);
  });

  // Reset functionality
  resetBtn?.addEventListener('click', () => {
    leadCountInput.value = '0';
    supportCountInput.value = '0';
  });

  // Get filtered sessions based on selected filter
  async function getFilteredSessions(filterType, filterValue) {
    const unitId = document.getElementById('unit_id')?.value;
    if (!unitId) return [];
    
    try {
      let url = `/unitcoordinator/units/${unitId}/bulk-staffing/sessions?type=${filterType}`;
      if (filterType === 'module' && filterValue) {
        url += `&value=${encodeURIComponent(filterValue)}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      return data.ok ? data.sessions : [];
    } catch (e) {
      console.error('Failed to fetch filtered sessions:', e);
      return [];
    }
  }

  // Apply bulk staffing to sessions
  async function applyBulkStaffing(filterType, filterValue, leadCount, supportCount) {
    const unitId = document.getElementById('unit_id')?.value;
    if (!unitId) {
      alert('No unit ID found. Please complete the previous steps first.');
      return;
    }
    
    const respectOverrides = document.getElementById('respect_overrides')?.checked || false;
    
    try {
      const requestBody = {
        type: filterType,
        lead_staff_required: leadCount,
        support_staff_required: supportCount,
        respect_overrides: respectOverrides
      };
      
      // Only add value for module type
      if (filterType === 'module') {
        requestBody.value = filterValue;
      }
      
      const response = await fetch(`/unitcoordinator/units/${unitId}/bulk-staffing/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.CSRF_TOKEN
        },
        body: JSON.stringify(requestBody)
      });
      
      const data = await response.json();
      if (data.ok) {
        alert(`Bulk staffing applied: ${data.updated_sessions} out of ${data.total_sessions} sessions updated with ${leadCount} lead staff and ${supportCount} support staff.`);
        // Refresh the review step if we're currently on it
        if (currentStep === 5) {
          populateReview();
        }
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (e) {
      console.error('Failed to apply bulk staffing:', e);
      alert('Failed to apply bulk staffing. Please try again.');
    }
  }

  // Initialize filter options when step 4 is shown
  const step4Section = document.querySelector('[data-step="4"]');
  if (step4Section) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          if (!step4Section.classList.contains('hidden')) {
            updateFilterOptions();
          }
        }
      });
    });
    observer.observe(step4Section, { attributes: true });
  }
}

// Initialize bulk staffing when DOM is loaded
document.addEventListener('DOMContentLoaded', initBulkStaffing);

// ===== Unit Code Auto-Uppercase =====
function initUnitCodeUppercase() {
  const unitCodeInput = document.querySelector('input[name="unit_code"]');
  
  if (unitCodeInput) {
    unitCodeInput.addEventListener('input', function(e) {
      // Store cursor position
      const cursorPosition = e.target.selectionStart;
      
      // Convert to uppercase
      const uppercaseValue = e.target.value.toUpperCase();
      
      // Update the value
      e.target.value = uppercaseValue;
      
      // Restore cursor position
      e.target.setSelectionRange(cursorPosition, cursorPosition);
    });
    
    // Also handle paste events
    unitCodeInput.addEventListener('paste', function(e) {
      // Allow the paste to complete, then convert to uppercase
      setTimeout(() => {
        const cursorPosition = e.target.selectionStart;
        const uppercaseValue = e.target.value.toUpperCase();
        e.target.value = uppercaseValue;
        e.target.setSelectionRange(cursorPosition, cursorPosition);
      }, 0);
    });
  }
}

// Initialize unit code uppercase when DOM is loaded
document.addEventListener('DOMContentLoaded', initUnitCodeUppercase);


document.addEventListener('DOMContentLoaded', initUnitTabs);

// --- Greeting Banner ---
function initGreetingBanner() {
  const greetingEl = document.getElementById('greeting-message');
  if (!greetingEl) return;

  const iconEl = document.querySelector('.greeting-icon .material-icons');
  const userName = greetingEl.dataset.userName || 'User';
  const now = new Date();
  const hour = now.getHours();

  let greetingText = '';
  let iconName = 'wb_sunny'; 

  if (hour < 12) {
    greetingText = 'Good morning';
    iconName = 'wb_sunny';
  } else if (hour < 18) {
    greetingText = 'Good afternoon';
    iconName = 'brightness_5';
  } else {
    greetingText = 'Good evening';
    iconName = 'nights_stay';
  }

  greetingEl.innerHTML = `${greetingText}, ${userName}! 👋`;
  if (iconEl) {
    iconEl.textContent = iconName;
  }
}

document.addEventListener('DOMContentLoaded', initGreetingBanner);

function updateTodaysSessions(sessions) {
  const container = document.getElementById('todaySessionsList');
  const countElement = document.getElementById('todaySessionCount');
  console.log('Today sessions container found:', !!container);
  console.log('Number of sessions:', sessions?.length);

  if (!container) return;

  // Update session count
  if (countElement) {
    countElement.textContent = sessions?.length || 0;
  }

  if (!sessions || sessions.length === 0) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <div class="flex gap-4 overflow-x-auto today-sessions-scroll" style="height: 100%; width: 100%;">
      ${sessions.map(session => {
        const isConfirmed = String(session.status || '').toLowerCase() === 'confirmed';
        const statusEl = isConfirmed
          ? `<span class="material-icons text-green-600 text-xs leading-none" title="Confirmed" aria-label="Confirmed">task_alt</span>`
          : `<span class="text-xs text-gray-500">${session.status || 'Scheduled'}</span>`;
        return `
        <div class="session-card">
          <div>
            <div class="session-card-header">
              <div class="session-card-title-container">
                <div class="session-card-dot"></div>
                <h5 class="session-card-title">${session.name}</h5>
              </div>
              <div class="session-card-status">${statusEl}</div>
            </div>

            <div class="session-card-details">
              <!-- Time -->
              <div class="session-card-detail">
                <span class="material-icons session-card-icon">schedule</span>
                <span>${session.time}</span>
              </div>
              <!-- Venue -->
              <div class="session-card-detail">
                <span class="material-icons session-card-icon">location_on</span>
                <span>${session.location || 'TBA'}</span>
              </div>
            </div>
          </div>

          <div class="session-card-facilitator">
            <span class="session-card-fac-label">Facilitator:</span>
            <div class="session-card-fac-value">
              ${session.facilitators?.map(f => f.name || f.initials || 'Unknown').join(', ') || 'None'}
            </div>
          </div>
        </div>
        `;
      }).join('')}
      
    </div>
  `;
  
}
function loadScriptOnce(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement('script');
    s.src = src; s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(s);
  });
}
let chartJsReady = null;
function ensureChartJs() {
  if (window.Chart) return Promise.resolve(window.Chart);
  if (!chartJsReady) chartJsReady = loadScriptOnce(CHART_JS_URL).then(() => window.Chart);
  return chartJsReady;
}
window.ensureChartJs = ensureChartJs;

// --- Attendance gauge (semi‑circle doughnut) ---
let attendanceGaugeChart = null;

// Wait until an element has a visible size before drawing
function waitForVisible(el, tries = 20) {
  return new Promise((resolve, reject) => {
    function tick(left) {
      const rect = el.getBoundingClientRect();
      const visible = rect.width > 0 && rect.height > 0;
      if (visible) return resolve();
      if (left <= 0) return reject(new Error('Gauge container never became visible'));
      setTimeout(() => tick(left - 1), 100);
    }
    tick(tries);
  });
}

function renderAttendanceGauge(today = [], upcoming = []) {
  const canvas = document.getElementById('attendanceGauge');
  const label = document.getElementById('attendanceGaugeLabel');
  if (!canvas || !label) return;

  const all = [...(today || []), ...(upcoming || [])];
  const total = all.length || 0;
  const attended = all.filter(s => {
    const a = String(s.attendance || s.attendance_status || '').toLowerCase();
    return ['attended', 'present', 'checked-in', 'checked in'].includes(a);
  }).length;

  const pct = total ? Math.round((attended / total) * 1000) / 10 : 0;
  label.textContent = `${pct}%`;

  const wrap = canvas.closest('.gauge-wrap') || canvas.parentElement;

  // Defer draw until sized and Chart.js is ready
   Promise.all([ensureChartJs(), waitForVisible(wrap)])
    .then(() => {
      if (attendanceGaugeChart) attendanceGaugeChart.destroy();
      attendanceGaugeChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [attended, Math.max(0, total - attended)],
            backgroundColor: ['#16a34a', '#e5e7eb'],
            borderWidth: 0,
            hoverOffset: 0,
            // Rounded ends and a small gap between segments
            borderRadius: 999,   // max rounding for arc ends
            spacing: 4           // subtle gap to emphasize rounded caps
          }]
        },
        options: {
          rotation: -90,
          circumference: 180,
          cutout: '88%',        // thinner ring (was 70%)
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          responsive: true,
          maintainAspectRatio: false,
          // ensure arcs render smoothly
          elements: { arc: { borderAlign: 'inner' } }
        }
      });

      // Ensure it sizes correctly after first paint and on resize
      setTimeout(() => attendanceGaugeChart?.resize(), 0);
      window.addEventListener('resize', () => attendanceGaugeChart?.resize());
    })
    .catch((e) => console.warn('Gauge render deferred:', e.message));
}

// Keep last data so we can re-render when tab becomes visible
window.__attData = { today: [], upcoming: [] };
// Sessions Overview Widget Functions 
function initSessionsOverview() {
  console.log('Initializing sessions overview...');
  ensureActivityLogCard();
  const dashboardPanel = document.getElementById('panel-dashboard');
  if (!dashboardPanel) {
    console.warn('Dashboard panel not found');
    return;
  }
  loadRealSessionsData();
}

async function loadRealSessionsData() {
  console.log('Loading real sessions data...');
  
  const unitId = getUnitId();
  if (!unitId) {
    console.warn('No unit ID available for loading sessions');
    return;
  }

  try {
    const response = await fetch(`/unitcoordinator/units/${unitId}/dashboard-sessions`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    if (!data.ok) {
      throw new Error(data.error || 'Failed to load session data');
    }

    // Store for later re-render
    window.__attData.today = data.today_sessions;
    window.__attData.upcoming = data.upcoming_sessions;

    updateTodaysSessions(data.today_sessions);
    updateUpcomingSessions(data.upcoming_sessions);
    updateMiniCalendar({ weekTotal: data.week_session_count, days: {} });
    
    console.log('=== INITIAL DATA LOAD ===');
    console.log('Today sessions:', data.today_sessions);
    console.log('Upcoming sessions:', data.upcoming_sessions);
    console.log('Facilitator counts data:', data.facilitator_counts);
    
    // Log each upcoming session in detail
    if (data.upcoming_sessions && data.upcoming_sessions.length > 0) {
      console.log('=== DETAILED UPCOMING SESSIONS ===');
      data.upcoming_sessions.forEach((session, index) => {
        console.log(`Session ${index}:`, {
          id: session.id,
          name: session.name,
          date: session.date,
          time: session.time,
          location: session.location,
          status: session.status,
          facilitators: session.facilitators
        });
      });
      console.log('=== END DETAILED UPCOMING SESSIONS ===');
    }
    
    console.log('=== END INITIAL DATA LOAD ===');
    
    renderActivityLog(data.facilitator_counts);
    
    // Update week session count in both cards
    const weekCountElement = document.getElementById('weekSessionCount');
    const todayCountElement = document.getElementById('todaySessionCount');
    if (weekCountElement) {
      weekCountElement.textContent = data.week_session_count;
    }
    if (todayCountElement) {
      todayCountElement.textContent = data.today_sessions.length;
    }
    
    console.log('Real sessions data loaded successfully');
  } catch (error) {
    console.error('Error loading real sessions data:', error);
    // Fallback to sample data if real data fails
    showSampleSessionsData();
  }
}

function showSampleSessionsData() {
  console.log('Loading sample sessions data...');
  const sampleData = {
    today: [
      { name: "Workshop-01", time: "8:00 AM - 9:00 AM", location: "Private session - home", status: "confirmed", attendance: "Attended",
        facilitators: [{ name: "Maya K", initials: "MK" }] },
      { name: "Workshop-02", time: "11:30 AM - 12:30 PM", location: "Zen Studio", status: "confirmed", attendance: "Pending",
        facilitators: [{ name: "Sarah J" }, { name: "Mike R" }, { name: "Lisa T" }, { name: "Tom B" }] }
    ],
    upcoming: [
      { name: "Tutorial B", date: "Tomorrow",  time: "10:00 AM", location: "Room 3.21", attendance: "Pending" },
      { name: "Workshop",   date: "Wednesday", time: "1:00 PM",  location: "EZONE 2.15", attendance: "Cancelled" }
    ],
    calendar: { weekTotal: 8, days: {} }
  };

  // Store for later re-render
  window.__attData.today = sampleData.today;
  window.__attData.upcoming = sampleData.upcoming;

  updateTodaysSessions(sampleData.today);
  updateUpcomingSessions(sampleData.upcoming);
  updateMiniCalendar(sampleData.calendar);
  
  // Update week session count in both cards
  const weekCountElement = document.getElementById('weekSessionCount');
  const todayCountElement = document.getElementById('todaySessionCount');
  if (weekCountElement) {
    weekCountElement.textContent = sampleData.calendar.weekTotal;
  }
  if (todayCountElement) {
    todayCountElement.textContent = sampleData.today.length;
  }
  
  // Load real attendance data from the API
  loadAttendanceData();
}

function waitForVisible(el, tries = 20) {
  return new Promise((resolve, reject) => {
    function tick(left) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) return resolve();
      if (left <= 0) return reject(new Error('element not visible'));
      setTimeout(() => tick(left - 1), 80);
    }
    tick(tries);
  });
}

function ensureActivityLogCard() {
  // If card already inserted, stop
  if (document.getElementById('activityLogCard')) return;

  // Find the dashboard panel
  const dashboardPanel = document.getElementById('panel-dashboard');
  if (!dashboardPanel) return;

  // Find the grid container that holds the Today's Sessions and Upcoming Sessions
  const grid = dashboardPanel.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2.gap-6');
  if (!grid) return;

  // Insert the activity log card as a full-width section below the existing cards
  const sec = document.createElement('section');
  sec.id = 'activityLogCard';
  sec.className = 'w-full mt-6';
  sec.innerHTML = `
    <div class="bg-white border border-gray-200 rounded-2xl p-6">
      <!-- Header Section -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <h2 class="text-lg font-bold text-gray-900 mb-1">Attendance Summary</h2>
          <p class="text-gray-500 text-xs">Complete Overview</p>
          <p class="text-gray-400 text-xs mt-1">Week of ${getCurrentWeek()}</p>
      </div>
        
        <!-- Controls -->
        <div class="flex items-center gap-3">
          <!-- Search Bar -->
          <div class="relative">
            <span class="material-icons absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xs">search</span>
            <input type="text" id="attendanceSearchInput" placeholder="Search employees..." class="pl-8 pr-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
          </div>
          
          <!-- Export Button -->
          <button class="export-btn" id="exportPdfBtn">
            <span class="material-icons text-xs">download</span>
            Export PDF
          </button>
        </div>
      </div>

      <!-- Attendance Table -->
      <div class="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <!-- Table Header -->
        <div class="bg-green-50 px-6 py-3 sticky top-0 z-10">
          <div class="grid grid-cols-5 gap-4 text-xs font-semibold text-gray-700">
            <div>Name</div>
            <div>Student Number</div>
            <div>Date</div>
            <div class="text-center">Session Hours</div>
            <div class="text-center">Total Weekly Hours</div>
          </div>
        </div>

        <!-- Scrollable Table Body -->
        <div class="max-h-80 overflow-y-auto divide-y divide-gray-100">
          <!-- Rows will be populated dynamically -->
        </div>
      </div>
    </div>
  `;
  
  // Insert after the grid
  grid.parentElement.insertBefore(sec, grid.nextSibling);
  
  // Initialize search and export functionality
  initializeAttendanceFeatures();
}

function initializeAttendanceFeatures() {
  // Initialize search functionality
  const searchInput = document.getElementById('attendanceSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', handleAttendanceSearch);
  }
  
  // Initialize PDF export functionality
  const exportBtn = document.getElementById('exportPdfBtn');
  if (exportBtn) {
    exportBtn.addEventListener('click', handlePdfExport);
  }
}

function handleAttendanceSearch(event) {
  const searchTerm = event.target.value.toLowerCase();
  const tableBody = document.querySelector('#activityLogCard .max-h-80.overflow-y-auto.divide-y');
  
  if (!tableBody) return;
  
  const rows = tableBody.querySelectorAll('.grid.grid-cols-5');
  
  rows.forEach(row => {
    // Search in name and student number
    const nameElement = row.querySelector('.text-xs.font-medium.text-gray-900');
    const studentNumberElement = row.querySelector('.font-mono');
    
    const name = nameElement?.textContent.toLowerCase() || '';
    const studentNumber = studentNumberElement?.textContent.toLowerCase() || '';
    
    const isVisible = name.includes(searchTerm) || studentNumber.includes(searchTerm);
    row.style.display = isVisible ? 'grid' : 'none';
  });
}

function handlePdfExport() {
  // Create a new window for PDF generation
  const printWindow = window.open('', '_blank');
  
  // Get the attendance table data
  const tableBody = document.querySelector('#activityLogCard .divide-y');
  if (!tableBody) {
    alert('No attendance data to export');
    return;
  }
  
  const rows = tableBody.querySelectorAll('.grid.grid-cols-5');
  if (rows.length === 0) {
    alert('No attendance data to export');
    return;
  }
  
  // Generate HTML content for PDF
  let tableRows = '';
  rows.forEach(row => {
    if (row.style.display !== 'none') {
      const cells = row.querySelectorAll('div');
      const name = cells[0]?.querySelector('.text-xs.font-medium.text-gray-900')?.textContent || '';
      const studentNumber = cells[1]?.textContent || '';
      const date = cells[2]?.textContent || '';
      const assignedHours = cells[3]?.textContent || '';
      const totalHours = cells[4]?.textContent || '';
      
      tableRows += `
        <tr>
          <td style="padding: 8px; border: 1px solid #ddd;">${name}</td>
          <td style="padding: 8px; border: 1px solid #ddd; font-family: monospace;">${studentNumber}</td>
          <td style="padding: 8px; border: 1px solid #ddd;">${date}</td>
          <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">${assignedHours}</td>
          <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">${totalHours}</td>
        </tr>
      `;
    }
  });
  
  const currentDate = new Date().toLocaleDateString();
  
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Attendance Summary Report</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .report-info { margin-bottom: 20px; text-align: center; color: #666; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background-color: #f0f9ff; padding: 12px; border: 1px solid #ddd; text-align: left; font-weight: bold; }
        td { padding: 8px; border: 1px solid #ddd; }
        .footer { margin-top: 30px; text-align: center; color: #666; font-size: 12px; }
      </style>
    </head>
    <body>
      <h1>Attendance Summary Report</h1>
      <div class="report-info">
        <p>Generated on: ${currentDate}</p>
        <p>Complete Overview</p>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Student Number</th>
            <th>Date</th>
            <th style="text-align: center;">Hours per Session</th>
            <th style="text-align: center;">Weekly Hours</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
      
      <div class="footer">
        <p>This report was generated from the Unit Coordinator Portal</p>
      </div>
    </body>
    </html>
  `;
  
  printWindow.document.write(htmlContent);
  printWindow.document.close();
  
  // Wait for content to load, then trigger print
  printWindow.onload = function() {
    printWindow.print();
    printWindow.close();
  };
}

// Aggregate daily counts from raw swap events
function buildDailySwapSeries(raw = []) {
  const dayKey = (d) => new Date(d).toISOString().slice(0,10);
  const map = new Map();

  raw.forEach(item => {
    let dateStr = null, count = 1;
    if (typeof item === 'string' || item instanceof Date) {
      dateStr = dayKey(item);
    } else if (item?.date || item?.created || item?.created_at) {
      dateStr = dayKey(item.date || item.created || item.created_at);
      if (Number.isFinite(item.count)) count = item.count;
    }
    if (!dateStr) return;
    map.set(dateStr, (map.get(dateStr) || 0) + count);
  });

  // Sort by date
  const days = Array.from(map.keys()).sort();
  const data = days.map(d => map.get(d));

  // Pretty labels (e.g., 04 Sep)
  const labels = days.map(d => {
    const dt = new Date(d + 'T00:00:00');
    return dt.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
  });

  return { labels, data, days };
}

let swapLineChart = null;
function renderActivityLog(facilitatorData = []) {
  console.log('renderActivityLog called with:', facilitatorData);
  ensureActivityLogCard();
  
  // Update the table with real facilitator data
  const tableBody = document.querySelector('#activityLogCard .max-h-80.overflow-y-auto.divide-y');
  console.log('Table body found:', !!tableBody);
  
  if (tableBody && facilitatorData.length > 0) {
    console.log('Rendering', facilitatorData.length, 'facilitators');
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Create rows for each facilitator
    facilitatorData.forEach((facilitator, index) => {
      const row = createFacilitatorRow(facilitator, index);
      tableBody.appendChild(row);
    });
  } else if (tableBody && facilitatorData.length === 0) {
    console.log('No facilitator data, showing empty state');
    // Show empty state
    tableBody.innerHTML = `
      <div class="px-6 py-8 text-center">
        <span class="material-icons text-gray-400 text-4xl mb-2">person_add</span>
        <div class="text-xs text-gray-500 mb-2">No facilitators assigned to sessions yet</div>
        <div class="text-xs text-gray-400">Assign facilitators to sessions in the Schedule tab</div>
      </div>
    `;
  } else {
    console.log('Table body not found or no data');
  }
}

function createFacilitatorRow(facilitator, index) {
  const row = document.createElement('div');
  row.className = 'grid grid-cols-5 gap-4 px-6 py-3 hover:bg-gray-50';
  
  // Use real data from the API
  const assignedHours = facilitator.assigned_hours || 0;
  const totalHours = facilitator.total_hours || 0;
  const studentNumber = facilitator.student_number || facilitator.email.split('@')[0] || `STU${String(index + 1).padStart(4, '0')}`;
  const sessionDate = facilitator.date || 'N/A';
  
  row.innerHTML = `
    <div class="flex items-center">
      <span class="text-xs font-medium text-gray-900">${facilitator.name}</span>
    </div>
    <div class="text-xs text-gray-600 font-mono">${studentNumber}</div>
    <div class="text-xs text-gray-600">${sessionDate}</div>
    <div class="text-xs text-gray-600 text-center">${assignedHours}h</div>
    <div class="text-xs text-gray-600 text-center">${totalHours}h</div>
  `;
  
  return row;
}


function getStatusClasses(status) {
  switch (status.bg) {
    case 'green':
      return 'bg-green-100 text-green-800';
    case 'red':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}


function generateRandomTime(start, end) {
  const startHour = parseInt(start.split(':')[0]);
  const endHour = parseInt(end.split(':')[0]);
  const hour = Math.floor(Math.random() * (endHour - startHour + 1)) + startHour;
  const minute = Math.floor(Math.random() * 60);
  const period = hour >= 12 ? 'pm' : 'am';
  const displayHour = hour > 12 ? hour - 12 : hour;
  return `${displayHour.toString().padStart(2, '0')}.${minute.toString().padStart(2, '0')} ${period}`;
}

function calculateHours(clockIn, clockOut) {
  // Simple calculation for demo purposes
  const inHour = parseInt(clockIn.split('.')[0]);
  const outHour = parseInt(clockOut.split('.')[0]);
  const inPeriod = clockIn.includes('pm') ? 12 : 0;
  const outPeriod = clockOut.includes('pm') ? 12 : 0;
  
  const inTotal = inHour + inPeriod;
  const outTotal = outHour + outPeriod;
  
  let hours = outTotal - inTotal;
  if (hours < 0) hours += 24;
  
  const minutes = Math.floor(Math.random() * 60);
  return `${hours}.${minutes.toString().padStart(2, '0')}`;
}

function getCurrentDate() {
  const today = new Date();
  const day = today.getDate();
  const month = today.toLocaleDateString('en-US', { month: 'short' });
  const year = today.getFullYear();
  return `${day}${getOrdinalSuffix(day)} ${month} ${year}`;
}

function getOrdinalSuffix(day) {
  if (day >= 11 && day <= 13) return 'th';
  switch (day % 10) {
    case 1: return 'st';
    case 2: return 'nd';
    case 3: return 'rd';
    default: return 'th';
  }
}

function generateAssignedHours() {
  // Generate realistic assigned hours (typically 6-8 hours for facilitators)
  const hours = Math.floor(Math.random() * 3) + 6; // 6, 7, or 8 hours
  const minutes = Math.floor(Math.random() * 60);
  return `${hours}.${minutes.toString().padStart(2, '0')}`;
}

function generateTotalHours() {
  // Generate total hours worked (usually slightly more than assigned)
  const hours = Math.floor(Math.random() * 4) + 7; // 7, 8, 9, or 10 hours
  const minutes = Math.floor(Math.random() * 60);
  return `${hours}.${minutes.toString().padStart(2, '0')}`;
}

function getCurrentWeek() {
  const today = new Date();
  const startOfWeek = new Date(today);
  const day = today.getDay();
  const diff = today.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
  startOfWeek.setDate(diff);
  
  const month = startOfWeek.toLocaleDateString('en-US', { month: 'short' });
  const dayOfMonth = startOfWeek.getDate();
  const year = startOfWeek.getFullYear();
  
  return `${month} ${dayOfMonth}, ${year}`;
}

window.__facilitatorData = [];
window.setFacilitatorData = function(dataArray) {
  window.__facilitatorData = Array.isArray(dataArray) ? dataArray : [];
  renderActivityLog(window.__facilitatorData);
};

// Facilitator Session Count Bar Chart
let facilitatorBarChart = null;
function renderFacilitatorBar(facilitatorData) {
  const canvas = document.getElementById('facilitatorBarChart');
  if (!canvas) {
    console.warn('Facilitator bar chart canvas not found');
    return;
  }

  // Handle empty data
  if (!facilitatorData || facilitatorData.length === 0) {
    if (facilitatorBarChart) {
      facilitatorBarChart.destroy();
      facilitatorBarChart = null;
    }
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#6b7280';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('No facilitator data available', canvas.width / 2, canvas.height / 2);
    return;
  }

  ensureChartJs().then(Chart => {
    if (facilitatorBarChart) {
      facilitatorBarChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    const labels = facilitatorData.map(f => f.name);
    const data = facilitatorData.map(f => f.session_count);

    facilitatorBarChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Sessions',
          data: data,
          backgroundColor: '#3b82f6',
          borderColor: '#2563eb',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.parsed.y} session${ctx.parsed.y === 1 ? '' : 's'}`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { 
              maxRotation: 45,
              color: '#6b7280',
              font: { size: 10 }
            }
          },
          y: {
            beginAtZero: true,
            ticks: { precision: 0, color: '#6b7280' },
            grid: { color: 'rgba(0,0,0,.06)' }
          }
        }
      }
    });
  }).catch(console.warn);
}

function updateUpcomingSessions(sessions) {
  const container = document.getElementById('upcomingSessionsList');
  console.log('Upcoming sessions container found:', !!container);
  
  if (!container) return;
  
  if (!sessions || sessions.length === 0) {
    container.innerHTML = '<div class="text-xs text-gray-500">No upcoming sessions</div>';
    return;
  }
  
  container.innerHTML = `
    <div class="flex flex-col gap-2 overflow-y-auto upcoming-sessions-scroll" style="height: 100%; width: 100%;">
      ${sessions.map(session => {
        // Handle placeholder sessions (empty state)
        if (session.isPlaceholder) {
          return `
            <div class="bg-white rounded-md p-4 border border-purple-200 flex-shrink-0 text-center">
              <div class="text-xs text-gray-500">${session.title}</div>
            </div>
          `;
        }
        
        // Handle regular sessions
        const sessionDate = session.date;
        let displayDate = sessionDate;
        
        // If it's a day name, add the actual date
        if (sessionDate && !['Today', 'Tomorrow'].includes(sessionDate)) {
          // Try to find the date for this day name
          const today = new Date();
          const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
          const dayIndex = dayNames.indexOf(sessionDate);
          
          if (dayIndex !== -1) {
            // Find the next occurrence of this day
            const daysUntilTarget = (dayIndex - today.getDay() + 7) % 7;
            const targetDate = new Date(today);
            targetDate.setDate(today.getDate() + daysUntilTarget);
            
            // Date display removed as requested
            displayDate = sessionDate;
          }
        }
        
        return `
        <div class="bg-white rounded-md p-2 border border-purple-200 flex-shrink-0 h-[50px] flex flex-col justify-center">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-purple-500"></div>
              <span class="text-xs font-medium truncate">${session.name}</span>
            </div>
            <div class="text-xs text-gray-500 text-right">${displayDate}</div>
          </div>
          <div class="text-xs text-gray-600 mt-0.5 truncate">
            ${session.time} • ${session.location || 'TBA'}
          </div>
        </div>
        `;
      }).join('')}
      
      ${sessions.length > 3 && !sessions.some(s => s.isPlaceholder) ? `
        <div class="w-full h-8 flex-shrink-0 flex items-center justify-center">
          <button class="scroll-button-upcoming w-6 h-6 rounded-full bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-600 transition-colors" title="Scroll to see more sessions">
            <span class="material-icons text-xs">expand_more</span>
          </button>
        </div>
      ` : ''}
    </div>
  `;
  
  console.log('Upcoming scroll button should be visible:', sessions.length > 3);
  
  const scrollButton = container.querySelector('.scroll-button-upcoming');
  const scrollContainer = container.querySelector('.upcoming-sessions-scroll');
  
  console.log('Upcoming scroll button found:', !!scrollButton);
  console.log('Upcoming scroll container found:', !!scrollContainer);
  
  if (scrollButton && scrollContainer) {
    // Add scroll event listener to show/hide scroll button based on scroll position
    const updateScrollButton = () => {
      const isAtEnd = scrollContainer.scrollTop >= (scrollContainer.scrollHeight - scrollContainer.clientHeight - 10);
      scrollButton.style.opacity = isAtEnd ? '0.5' : '1';
      scrollButton.disabled = isAtEnd;
    };
    
    scrollContainer.addEventListener('scroll', updateScrollButton);
    
    scrollButton.addEventListener('click', () => {
      scrollContainer.scrollBy({ top: 100, behavior: 'smooth' });
    });
    
    // Initial check
    updateScrollButton();
  }
}

function updateMiniCalendar(calendarData) {
  const weekCountEl = document.getElementById('weekSessionCount');
  const daysContainer = document.getElementById('miniCalendarDays');
  
  if (!weekCountEl || !daysContainer) return;
  
  weekCountEl.textContent = calendarData.weekTotal || 0;
  
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay() + 1);
  
  const dayAbbreviations = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  
  let daysHTML = '';
  for (let i = 0; i < 7; i++) {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i);
    const dayAbbr = dayAbbreviations[i];
    const isToday = date.toDateString() === today.toDateString();
    const hasSession = calendarData.days && calendarData.days[date.toISOString().split('T')[0]];
    
    const classes = [
      'text-center py-1 rounded text-xs font-medium cursor-pointer hover:bg-gray-100 transition-colors',
      isToday ? 'bg-blue-600 text-white hover:bg-blue-700' : 'text-gray-700',
      hasSession ? 'relative' : ''
    ].filter(Boolean).join(' ');
    
    daysHTML += `
      <div class="${classes}" data-day-index="${i}" data-date="${date.toISOString().split('T')[0]}">
        ${dayAbbr}
        ${hasSession ? '<div class="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-purple-500 rounded-full"></div>' : ''}
      </div>
    `;
  }
  
  daysContainer.innerHTML = daysHTML;
  
  // Add click event listeners to filter sessions by day
  const dayElements = daysContainer.querySelectorAll('[data-day-index]');
  dayElements.forEach(dayEl => {
    dayEl.addEventListener('click', () => {
      // Remove active class from all days
      dayElements.forEach(el => {
        el.classList.remove('bg-blue-600', 'text-white', 'hover:bg-blue-700');
        el.style.color = '';
      });
      
      // Add active class to clicked day
      dayEl.classList.add('bg-blue-600', 'hover:bg-blue-700');
      dayEl.style.color = 'white';
      
      // Filter upcoming sessions by selected day
      const selectedDate = dayEl.getAttribute('data-date');
      filterUpcomingSessionsByDay(selectedDate);
    });
  });
  
  // Add double-click to show all sessions
  dayElements.forEach(dayEl => {
    dayEl.addEventListener('dblclick', () => {
      // Remove active class from all days
      dayElements.forEach(el => {
        el.classList.remove('bg-blue-600', 'text-white', 'hover:bg-blue-700');
        el.style.color = '';
      });
      
      // Show all upcoming sessions
      const allSessions = window.__attData?.upcoming || [];
      updateUpcomingSessions(allSessions);
    });
  });
}

// Function to filter upcoming sessions by selected day
function filterUpcomingSessionsByDay(selectedDate) {
  const container = document.getElementById('upcomingSessionsList');
  if (!container) return;
  
  // Get both today's and upcoming sessions data
  const upcomingSessions = window.__attData?.upcoming || [];
  const todaySessions = window.__attData?.today || [];
  
  // Convert selected date to day name
  const selectedDayName = new Date(selectedDate).toLocaleDateString('en-US', { weekday: 'long' });
  
  console.log('=== FILTERING DEBUG ===');
  console.log('Selected date:', selectedDate);
  console.log('Selected day name:', selectedDayName);
  console.log('Today sessions:', todaySessions);
  console.log('Upcoming sessions:', upcomingSessions);
  
  // Calculate what "Tomorrow" actually means
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  const tomorrowDayName = tomorrow.toLocaleDateString('en-US', { weekday: 'long' });
  const todayDayName = today.toLocaleDateString('en-US', { weekday: 'long' });
  
  console.log('Today:', today.toDateString());
  console.log('Today day name:', todayDayName);
  console.log('Tomorrow date:', tomorrow.toDateString());
  console.log('Tomorrow day name:', tomorrowDayName);
  
  // Combine sessions from both today and upcoming
  let allSessions = [];
  
  // Add today's sessions with "Today" as the date
  todaySessions.forEach(session => {
    allSessions.push({
      ...session,
      date: 'Today'
    });
  });
  
  // Add upcoming sessions as-is
  allSessions = allSessions.concat(upcomingSessions);
  
  console.log('All combined sessions:', allSessions);
  
  // Filter sessions for the selected day
  const filteredSessions = allSessions.filter(session => {
    const sessionDay = session.date;
    
    console.log(`Checking session "${session.name}":`, {
      sessionDay: sessionDay,
      selectedDayName: selectedDayName,
      todayDayName: todayDayName,
      tomorrowDayName: tomorrowDayName,
      matchesToday: sessionDay === 'Today' && selectedDayName === todayDayName,
      matchesTomorrow: sessionDay === 'Tomorrow' && selectedDayName === tomorrowDayName,
      matchesDayName: sessionDay === selectedDayName
    });
    
    // Multiple matching strategies:
    // 1. "Today" match if selected day is today
    // 2. "Tomorrow" match if selected day is tomorrow
    // 3. Exact day name match
    // 4. Case-insensitive match
    const todayMatch = sessionDay === 'Today' && selectedDayName === todayDayName;
    const tomorrowMatch = sessionDay === 'Tomorrow' && selectedDayName === tomorrowDayName;
    const exactMatch = sessionDay === selectedDayName;
    const caseInsensitiveMatch = sessionDay && sessionDay.toLowerCase() === selectedDayName.toLowerCase();
    
    const matches = todayMatch || tomorrowMatch || exactMatch || caseInsensitiveMatch;
    
    console.log(`Session "${session.name}" matches:`, {
      todayMatch,
      tomorrowMatch,
      exactMatch,
      caseInsensitiveMatch,
      finalMatch: matches
    });
    
    return matches;
  });
  
  console.log('Filtered sessions result:', filteredSessions);
  console.log('=== END FILTERING DEBUG ===');
  
  // Always use updateUpcomingSessions to maintain proper structure
  if (filteredSessions.length === 0) {
    console.log('No sessions found, showing empty state');
    // Create a temporary empty state that still uses the proper structure
    const emptyState = [{
      title: `No sessions scheduled for ${selectedDayName}`,
      time: '',
      location: '',
      facilitator: '',
      isPlaceholder: true
    }];
    updateUpcomingSessions(emptyState);
  } else {
    console.log('Found sessions, updating display');
  // Update the display with filtered sessions
  updateUpcomingSessions(filteredSessions);
  }
}

// ===== Schedule Panel Functionality =====
let currentWeekStart = new Date();
let scheduleSessions = [];

// Initialize schedule panel
function initSchedulePanel() {
  // Set current week to start of week (Monday)
  const today = new Date();
  const dayOfWeek = today.getDay();
  const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  currentWeekStart = new Date(today);
  currentWeekStart.setDate(today.getDate() + daysToMonday);
  currentWeekStart.setHours(0, 0, 0, 0);

  // Load sessions for current week
  loadScheduleSessions();
  
  // Also load data for list view
  loadListSessionData();
  
  // Set up event listeners
  setupScheduleEventListeners();
}

// Load sessions for the current week
async function loadScheduleSessions() {
  const unitId = getUnitId();
  if (!unitId) return;

  try {
    const weekStart = currentWeekStart.toISOString().split('T')[0];
    const url = withUnitId(CAL_WEEK_TEMPLATE, unitId) + `?week_start=${weekStart}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.ok) {
      scheduleSessions = data.sessions || [];
      renderScheduleGrid();
    }
  } catch (error) {
    console.error('Error loading schedule sessions:', error);
  }
}

// Render the schedule grid
function renderScheduleGrid() {
  const grid = document.getElementById('schedule-grid');
  if (!grid) return;

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const today = new Date();
  
  let gridHTML = '';
  
  for (let i = 0; i < 7; i++) {
    const dayDate = new Date(currentWeekStart);
    dayDate.setDate(currentWeekStart.getDate() + i);
    
    const isToday = dayDate.toDateString() === today.toDateString();
    const daySessions = getSessionsForDay(dayDate);
    const pendingCount = daySessions.filter(s => s.status === 'pending').length;
    const totalCount = daySessions.length;
    
    gridHTML += `
      <div class="schedule-day">
        <div class="schedule-day-header">
          <div>
            <div class="day-name">${days[i]}</div>
            <div class="day-date">${dayDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
            ${isToday ? '<div class="today-label">Today</div>' : ''}
          </div>
          <div class="day-status ${pendingCount > 0 ? 'pending' : 'info'}">
            <span class="material-icons">${pendingCount > 0 ? 'warning' : 'info'}</span>
            ${pendingCount}/${totalCount}
          </div>
        </div>
        <div class="day-sessions">
          ${renderDaySessions(daySessions)}
        </div>
      </div>
    `;
  }
  
  grid.innerHTML = gridHTML;
  updateCurrentWeekDisplay();
}

// Get sessions for a specific day
function getSessionsForDay(date) {
  return scheduleSessions.filter(session => {
    const sessionDate = new Date(session.start);
    return sessionDate.toDateString() === date.toDateString();
  });
}

// Render sessions for a specific day
function renderDaySessions(sessions) {
  if (sessions.length === 0) {
    return `
      <div class="empty-day">
        <span class="material-icons">add</span>
        <div class="empty-day-text">No sessions scheduled.<br>Sessions will appear when CSV is uploaded.</div>
        <button class="create-session-btn" onclick="openCreateSessionModal()">
          Create Session
        </button>
      </div>
    `;
  }

  return sessions.map((session, index) => `
    <div class="session-card" data-session-id="${session.id || `temp-${index}`}" data-session-name="${session.session_name || session.title || 'New Session'}" data-session-time="${formatTime(session.start)} - ${formatTime(session.end)}" data-session-location="${session.location || 'TBA'}">
      <div class="session-header">
        <div class="session-facilitator ${session.facilitator ? '' : 'unassigned'}" ${!session.facilitator ? 'onclick="openFacilitatorModal(this)"' : ''}>
          ${session.facilitator ? getInitials(session.facilitator) : 'Unassigned'}
        </div>
        <div class="session-time">
          ${formatTime(session.start)} - ${formatTime(session.end)}
        </div>
      </div>
      <div class="session-title">${session.session_name || session.title || 'New Session'}</div>
      <div class="session-details">
        <div class="session-detail">
          <span class="material-icons">place</span>
          <span>${session.location || 'TBA'}</span>
        </div>
        <div class="session-detail">
          <span class="material-icons">book</span>
          <span>${session.module_type || 'Workshop'}</span>
        </div>
        ${session.attendees ? `
          <div class="session-detail">
            <span class="material-icons">people</span>
            <span>${session.attendees} students</span>
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

// Helper functions
function getInitials(name) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase();
}

function formatTime(timeString) {
  const date = new Date(timeString);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
}

function updateCurrentWeekDisplay() {
  const weekEnd = new Date(currentWeekStart);
  weekEnd.setDate(currentWeekStart.getDate() + 6);
  
  const weekDisplay = document.getElementById('current-week');
  if (weekDisplay) {
    weekDisplay.textContent = `Week of ${currentWeekStart.toLocaleDateString('en-US', { 
      month: 'long', 
      day: 'numeric', 
      year: 'numeric' 
    })}`;
  }
}

// Set up event listeners for schedule panel
function setupScheduleEventListeners() {
  // Week navigation
  const prevWeekBtn = document.getElementById('prev-week');
  const nextWeekBtn = document.getElementById('next-week');
  
  if (prevWeekBtn) {
    prevWeekBtn.addEventListener('click', () => {
      currentWeekStart.setDate(currentWeekStart.getDate() - 7);
      loadScheduleSessions();
      loadListSessionData(); // Also refresh list view data
    });
  }
  
  if (nextWeekBtn) {
    nextWeekBtn.addEventListener('click', () => {
      currentWeekStart.setDate(currentWeekStart.getDate() + 7);
      loadScheduleSessions();
      loadListSessionData(); // Also refresh list view data
    });
  }

  // View toggle
  const viewBtns = document.querySelectorAll('.view-btn');
  viewBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      // TODO: Implement list view
    });
  });

  // Auto assign button
  const autoAssignBtn = document.querySelector('.auto-assign-btn');
  if (autoAssignBtn) {
    autoAssignBtn.addEventListener('click', () => {
      // TODO: Implement auto-assign functionality
      console.log('Auto-assign clicked');
    });
  }
}

// ===== List View Functions =====

// Session data will be injected from the backend
let sessionData = [];

// Function to set session data from backend
function setSessionData(data) {
  sessionData = data || [];
  // Re-render list view if it's currently active
  const listView = document.getElementById('list-view');
  if (listView && listView.style.display !== 'none') {
    renderListView();
  }
}

// Load session data for list view from the same API as calendar
async function loadListSessionData() {
  const unitId = getUnitId();
  if (!unitId) return;

  try {
    const weekStart = currentWeekStart.toISOString().split('T')[0];
    const url = withUnitId(CAL_WEEK_TEMPLATE, unitId) + `?week_start=${weekStart}`;
    
    const response = await fetch(url, {
      headers: { 'X-CSRFToken': CSRF_TOKEN }
    });
    const data = await response.json();
    
    if (data.ok && data.sessions) {
      // Transform calendar session data to list view format
      sessionData = data.sessions.map(session => ({
        id: session.id,
        title: session.extendedProps?.session_name || session.title || 'New Session',
        status: getSessionStatus(session),
        day: new Date(session.start).toLocaleDateString('en-US', { weekday: 'long' }),
        time: formatTimeRange(session.start, session.end),
        location: session.extendedProps?.location || session.extendedProps?.venue || 'TBA',
        facilitator: getSessionFacilitator(session),
        moduleType: session.extendedProps?.module_type || 'Workshop',
        students: session.extendedProps?.students || 0
      }));
      
      // Re-render list view if it's currently active
      const listView = document.getElementById('list-view');
      if (listView && listView.style.display !== 'none') {
        renderListView();
      }
    }
  } catch (error) {
    console.error('Error loading list session data:', error);
  }
}

// Helper function to determine session status
function getSessionStatus(session) {
  // This would need to be determined based on your business logic
  // For now, we'll use a simple heuristic
  if (session.extendedProps?.facilitator_id) {
    return 'approved';
  } else if (session.extendedProps?.pending) {
    return 'pending';
  } else {
    return 'unassigned';
  }
}

// Helper function to get facilitator name
function getSessionFacilitator(session) {
  return session.extendedProps?.facilitator_name || null;
}

// Helper function to format time range
function formatTimeRange(start, end) {
  const startTime = new Date(start).toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
  const endTime = new Date(end).toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
  return `${startTime} - ${endTime}`;
}

// Initialize List View
function initListView() {
  const viewToggle = document.querySelector('.view-toggle');
  const calendarView = document.getElementById('calendar-view');
  const listView = document.getElementById('list-view');
  
  if (!viewToggle || !calendarView || !listView) return;

  // Handle view toggle
  viewToggle.addEventListener('click', (e) => {
    if (e.target.closest('.view-btn')) {
      const btn = e.target.closest('.view-btn');
      const view = btn.dataset.view;
      
      // Update button states
      document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Show/hide views
      if (view === 'calendar') {
        calendarView.style.display = 'block';
        listView.style.display = 'none';
      } else {
        calendarView.style.display = 'none';
        listView.style.display = 'block';
        // Load data from the same source as calendar view
        loadListSessionData();
      }
    }
  });

  // Initialize filters
  initFilters();
  
  // Render initial list
  renderListView();
}

// Initialize filters and search
function initFilters() {
  const searchInput = document.getElementById('session-search');
  const statusFilter = document.getElementById('status-filter');
  const dayFilter = document.getElementById('day-filter');
  const sortFilter = document.getElementById('sort-filter');
  const sortDirection = document.getElementById('sort-direction');
  
  if (searchInput) {
    searchInput.addEventListener('input', filterSessions);
  }
  
  if (statusFilter) {
    statusFilter.addEventListener('change', filterSessions);
  }
  
  if (dayFilter) {
    dayFilter.addEventListener('change', filterSessions);
  }
  
  if (sortFilter) {
    sortFilter.addEventListener('change', sortSessions);
  }
  
  if (sortDirection) {
    sortDirection.addEventListener('click', toggleSortDirection);
  }
}

// Render the list view
function renderListView() {
  const container = document.getElementById('sessions-container');
  if (!container) return;

  const filteredSessions = getFilteredSessions();
  updateSessionStats(filteredSessions);
  
  if (filteredSessions.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <span class="material-icons">event_note</span>
        </div>
        <div class="empty-state-title">No sessions found</div>
        <div class="empty-state-text">
          ${sessionData.length === 0 
            ? 'No sessions have been created yet. Sessions will appear here when they are added to the schedule.'
            : 'No sessions match your current filters. Try adjusting your search criteria.'
          }
        </div>
      </div>
    `;
  } else {
    container.innerHTML = filteredSessions.map(session => `
      <div class="session-item" data-session-id="${session.id}">
        <div class="session-item-header">
          <div class="session-title">
            <span class="material-icons">menu_book</span>
            ${session.title}
            <span class="session-status ${session.status}">
              <span class="material-icons">${getStatusIcon(session.status)}</span>
              ${session.status.charAt(0).toUpperCase() + session.status.slice(1)}
            </span>
          </div>
          <div class="session-actions">
            <button class="action-btn" title="View Details">
              <span class="material-icons">visibility</span>
            </button>
            <button class="action-btn" title="More Options">
              <span class="material-icons">more_vert</span>
            </button>
          </div>
        </div>
        
        <div class="session-details">
          <div class="session-detail">
            <span class="material-icons">schedule</span>
            <span class="session-detail-value">${session.day}</span>
            <span>${session.time}</span>
          </div>
          
          <div class="session-detail">
            <span class="material-icons">place</span>
            <span class="session-detail-value">${session.location}</span>
          </div>
          
          <div class="session-detail">
            <span class="material-icons">person</span>
            <span class="session-detail-value">${session.facilitator || 'Unassigned'}</span>
          </div>
          
          <div class="session-detail">
            <span class="material-icons">book</span>
            <span class="session-detail-value">${session.moduleType}</span>
          </div>
        </div>
      </div>
    `).join('');
  }
  
  updateSessionCount(filteredSessions.length);
}

// Get filtered sessions based on current filters
function getFilteredSessions() {
  const searchTerm = document.getElementById('session-search')?.value.toLowerCase() || '';
  const statusFilter = document.getElementById('status-filter')?.value || '';
  const dayFilter = document.getElementById('day-filter')?.value || '';
  
  let filtered = sessionData.filter(session => {
    const matchesSearch = !searchTerm || 
      session.title.toLowerCase().includes(searchTerm) ||
      session.location.toLowerCase().includes(searchTerm) ||
      (session.facilitator && session.facilitator.toLowerCase().includes(searchTerm)) ||
      session.moduleType.toLowerCase().includes(searchTerm);
    
    const matchesStatus = !statusFilter || session.status === statusFilter;
    const matchesDay = !dayFilter || session.day.toLowerCase() === dayFilter;
    
    return matchesSearch && matchesStatus && matchesDay;
  });
  
  return sortSessions(filtered);
}

// Sort sessions
function sortSessions(sessions) {
  const sortBy = document.getElementById('sort-filter')?.value || 'time';
  const isAscending = !document.getElementById('sort-direction')?.classList.contains('desc');
  
  return sessions.sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
      case 'facilitator':
        comparison = (a.facilitator || '').localeCompare(b.facilitator || '');
        break;
      case 'status':
        comparison = a.status.localeCompare(b.status);
        break;
      case 'time':
      default:
        comparison = a.time.localeCompare(b.time);
        break;
    }
    
    return isAscending ? comparison : -comparison;
  });
}

// Toggle sort direction
function toggleSortDirection() {
  const btn = document.getElementById('sort-direction');
  const icon = btn.querySelector('.material-icons');
  
  if (btn.classList.contains('desc')) {
    btn.classList.remove('desc');
    btn.innerHTML = '<span class="material-icons">unfold_more</span> Ascending';
  } else {
    btn.classList.add('desc');
    btn.innerHTML = '<span class="material-icons">unfold_less</span> Descending';
  }
  
  filterSessions();
}

// Filter sessions (called by filter controls)
function filterSessions() {
  renderListView();
}

// Update session statistics
function updateSessionStats(sessions) {
  const total = sessions.length;
  const approved = sessions.filter(s => s.status === 'approved').length;
  const pending = sessions.filter(s => s.status === 'pending').length;
  const unassigned = sessions.filter(s => s.status === 'unassigned').length;
  
  // Update stat cards
  const totalEl = document.getElementById('total-sessions');
  const approvedEl = document.getElementById('approved-sessions');
  const pendingEl = document.getElementById('pending-sessions');
  const unassignedEl = document.getElementById('unassigned-sessions');
  
  if (totalEl) totalEl.textContent = total;
  if (approvedEl) approvedEl.textContent = approved;
  if (pendingEl) pendingEl.textContent = pending;
  if (unassignedEl) unassignedEl.textContent = unassigned;
}

// Update session count display
function updateSessionCount(count) {
  const filteredCount = document.getElementById('filtered-count');
  const sessionCount = document.getElementById('session-count');
  
  if (filteredCount) filteredCount.textContent = count;
  if (sessionCount) sessionCount.textContent = `${count} sessions`;
}

// Get status icon
function getStatusIcon(status) {
  switch (status) {
    case 'approved': return 'check_circle';
    case 'pending': return 'warning';
    case 'unassigned': return 'person';
    case 'proposed': return 'schedule';
    default: return 'help';
  }
}

// Initialize schedule panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Check if we're on the unit coordinator dashboard
  if (document.getElementById('schedule-grid')) {
    initSchedulePanel();
    initListView();
  }
});



  // Load real attendance data from database
  async function loadAttendanceData() {
    try {
      const unitId = getUnitId();
      if (!unitId) {
        console.warn('No unit ID available for attendance data');
        return;
      }

      const response = await fetch(`/unitcoordinator/units/${unitId}/attendance-summary`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.ok && data.facilitators) {
        console.log('Loaded attendance data:', data.facilitators.length, 'facilitators');
        
        // Store in global data object
        if (window.__attData) {
          window.__attData.facilitators = data.facilitators;
        }
        
        // Render the attendance summary
        renderActivityLog(data.facilitators);
        
        // Update the week display with real data
        updateAttendanceWeekDisplay(data.facilitators);
        
      } else {
        console.error('Failed to load attendance data:', data.error);
        showAttendanceError('Failed to load attendance data');
      }
      
    } catch (error) {
      console.error('Error loading attendance data:', error);
      showAttendanceError('Error loading attendance data');
    }
  }

  // Update the week display with real data
  function updateAttendanceWeekDisplay(facilitators) {
    const weekElement = document.querySelector('#activityLogCard .text-gray-400.text-xs.mt-1');
    if (weekElement && facilitators.length > 0) {
      // Get the most recent date from facilitators
      const dates = facilitators
        .map(f => f.date)
        .filter(d => d)
        .sort()
        .reverse();
      
      if (dates.length > 0) {
        const latestDate = new Date(dates[0]);
        const weekStart = new Date(latestDate);
        weekStart.setDate(latestDate.getDate() - latestDate.getDay()); // Start of week
        
        const weekText = `Week of ${weekStart.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        })}`;
        
        weekElement.textContent = weekText;
      }
    }
  }

  // Show error message in attendance summary
  function showAttendanceError(message) {
    const tableBody = document.querySelector('#activityLogCard .max-h-80.overflow-y-auto.divide-y');
    if (tableBody) {
      tableBody.innerHTML = `
        <div class="p-6 text-center text-gray-500">
          <span class="material-icons text-4xl mb-2">error_outline</span>
          <p>${message}</p>
          <button onclick="loadAttendanceData()" class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Retry
          </button>
        </div>
      `;
    }
  }

  // Load attendance data when the page loads
  setTimeout(() => {
    loadAttendanceData();
  }, 1000);

// Create Session Modal Functions
function openCreateSessionModal() {
  // Set today's date as default
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('session-date').value = today;
  
  // Show modal
  document.getElementById('create-session-modal').style.display = 'flex';
}

function closeCreateSessionModal() {
  document.getElementById('create-session-modal').style.display = 'none';
  
  // Clear form
  document.getElementById('session-name').value = '';
  document.getElementById('session-date').value = '';
  document.getElementById('session-module').value = '';
  document.getElementById('session-start-time').value = '';
  document.getElementById('session-end-time').value = '';
  document.getElementById('session-location').value = '';
  document.getElementById('session-description').value = '';
}

function validateSessionForm() {
  const requiredFields = [
    'session-name',
    'session-date', 
    'session-module',
    'session-start-time',
    'session-end-time',
    'session-location'
  ];
  
  let isValid = true;
  
  requiredFields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (!field.value.trim()) {
      field.style.borderColor = '#ef4444';
      isValid = false;
    } else {
      field.style.borderColor = '#d1d5db';
    }
  });
  
  // Validate time range
  const startTime = document.getElementById('session-start-time').value;
  const endTime = document.getElementById('session-end-time').value;
  
  if (startTime && endTime && startTime >= endTime) {
    document.getElementById('session-end-time').style.borderColor = '#ef4444';
    showSimpleNotification('End time must be after start time', 'error');
    isValid = false;
  }
  
  return isValid;
}

async function createSession() {
  if (!validateSessionForm()) {
    return;
  }
  
  const sessionData = {
    name: document.getElementById('session-name').value.trim(),
    date: document.getElementById('session-date').value,
    module_type: document.getElementById('session-module').value,
    start_time: document.getElementById('session-start-time').value,
    end_time: document.getElementById('session-end-time').value,
    location: document.getElementById('session-location').value.trim(),
    description: document.getElementById('session-description').value.trim()
  };
  
  try {
    // Get current unit ID
    const tabsNav = document.querySelector('.uc-tabs[data-unit-id]');
    const currentUnitId = tabsNav ? tabsNav.getAttribute('data-unit-id') : null;
    
    if (!currentUnitId) {
      showSimpleNotification('No unit selected', 'error');
      return;
    }
    
    const response = await fetch(`/unitcoordinator/units/${currentUnitId}/sessions/manual`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken
      },
      body: JSON.stringify(sessionData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.ok) {
      showSimpleNotification('Session created successfully!', 'success');
      closeCreateSessionModal();
      
      // Refresh the schedule
      setTimeout(() => {
        loadScheduleSessions();
      }, 1000);
    } else {
      throw new Error(result.error || 'Failed to create session');
    }
    
  } catch (error) {
    console.error('Error creating session:', error);
    showSimpleNotification(`Error creating session: ${error.message}`, 'error');
  }
}

// Open facilitator selection modal
function openFacilitatorModal(element) {
  const sessionCard = element.closest('.session-card');
  currentSessionData = {
    id: sessionCard.dataset.sessionId,
    name: sessionCard.dataset.sessionName,
    time: sessionCard.dataset.sessionTime,
    location: sessionCard.dataset.sessionLocation
  };
  
  // Reset selection
  selectedFacilitators = [];
  
  // Update modal content
  document.getElementById('modal-session-name').textContent = currentSessionData.name;
  document.getElementById('modal-session-time').textContent = `Time: ${currentSessionData.time}`;
  document.getElementById('modal-session-location').textContent = `Location: ${currentSessionData.location}`;
  
  // Show modal
  document.getElementById('facilitator-modal').style.display = 'flex';
  
  // Load facilitators
  loadFacilitators();
}

// Close facilitator modal
function closeFacilitatorModal() {
  document.getElementById('facilitator-modal').style.display = 'none';
  currentSessionData = null;
  allFacilitators = [];
  filteredFacilitators = [];
  selectedFacilitators = [];
}

// Load facilitators from API
async function loadFacilitators() {
  const facilitatorList = document.getElementById('facilitator-list');
  
  // Get current unit ID from multiple possible sources
  let currentUnitId = null;
  
  // Try to get from tabs navigation data attribute
  const tabsNav = document.querySelector('.uc-tabs[data-unit-id]');
  if (tabsNav) {
    currentUnitId = tabsNav.getAttribute('data-unit-id');
  }
  
  // Try to get from URL parameters
  if (!currentUnitId) {
    const urlParams = new URLSearchParams(window.location.search);
    currentUnitId = urlParams.get('unit');
  }
  
  // Try to get from unit_id input (for create unit modal)
  if (!currentUnitId) {
    const unitIdInput = document.getElementById('unit_id');
    if (unitIdInput && unitIdInput.value) {
      currentUnitId = unitIdInput.value;
    }
  }
  
  if (!currentUnitId) {
    facilitatorList.innerHTML = `
      <div class="facilitator-loading">
        <span class="material-icons">error</span>
        <p>No unit selected</p>
      </div>
    `;
    return;
  }
  
  try {
    facilitatorList.innerHTML = `
      <div class="facilitator-loading">
        <span class="material-icons">hourglass_empty</span>
        <p>Loading facilitators...</p>
      </div>
    `;
    
    const response = await fetch(`/unitcoordinator/units/${currentUnitId}/facilitators`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.ok) {
      allFacilitators = data.facilitators;
      filteredFacilitators = [...allFacilitators];
      renderFacilitatorList();
    } else {
      throw new Error(data.error || 'Failed to load facilitators');
    }
    
  } catch (error) {
    console.error('Error loading facilitators:', error);
    facilitatorList.innerHTML = `
      <div class="facilitator-loading">
        <span class="material-icons">error</span>
        <p>Error loading facilitators: ${error.message}</p>
      </div>
    `;
  }
}

// Render facilitator list
function renderFacilitatorList() {
  const facilitatorList = document.getElementById('facilitator-list');
  
  if (filteredFacilitators.length === 0) {
    facilitatorList.innerHTML = `
      <div class="facilitator-loading">
        <span class="material-icons">person_off</span>
        <p>No facilitators found</p>
      </div>
    `;
    return;
  }
  
  facilitatorList.innerHTML = filteredFacilitators.map((facilitator, index) => `
    <div class="facilitator-item" data-facilitator-id="${facilitator.id}" data-facilitator-name="${facilitator.name}" data-facilitator-email="${facilitator.email}">
      <input type="checkbox" class="facilitator-checkbox" id="facilitator-${facilitator.id}" onchange="toggleFacilitatorSelection('${facilitator.id}', '${facilitator.name}', '${facilitator.email}')">
      <div class="facilitator-avatar">
        ${getFacilitatorInitials(facilitator.name)}
      </div>
      <div class="facilitator-info">
        <div class="facilitator-name">${facilitator.name}</div>
        <div class="facilitator-email">${facilitator.email}</div>
      </div>
    </div>
  `).join('');
  
  // Update select button state
  updateSelectButton();
}

// Get facilitator initials
function getFacilitatorInitials(name) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase();
}

// Toggle facilitator selection
function toggleFacilitatorSelection(facilitatorId, facilitatorName, facilitatorEmail) {
  const checkbox = document.getElementById(`facilitator-${facilitatorId}`);
  const facilitatorItem = checkbox.closest('.facilitator-item');
  
  if (checkbox.checked) {
    // Add to selection if not already selected
    if (!selectedFacilitators.find(f => f.id === facilitatorId)) {
      selectedFacilitators.push({
        id: facilitatorId,
        name: facilitatorName,
        email: facilitatorEmail
      });
      facilitatorItem.classList.add('selected');
    }
  } else {
    // Remove from selection
    selectedFacilitators = selectedFacilitators.filter(f => f.id !== facilitatorId);
    facilitatorItem.classList.remove('selected');
  }
  
  updateSelectButton();
}

// Update select button state
function updateSelectButton() {
  const selectButton = document.getElementById('facilitator-modal-select');
  const count = selectedFacilitators.length;
  
  selectButton.textContent = `Select (${count})`;
  selectButton.disabled = count === 0;
}

// Select multiple facilitators
function selectMultipleFacilitators() {
  if (selectedFacilitators.length === 0) return;
  
  console.log('Selected facilitators:', selectedFacilitators);
  
  // Update the session card to show "Pending" status with multiple facilitators
  updateSessionStatusMultiple(currentSessionData.id, 'pending', selectedFacilitators);
  
  // Show assignment confirmation popup for multiple facilitators
  showMultipleAssignmentConfirmation(selectedFacilitators, currentSessionData.name);
  
  // Close modal
  closeFacilitatorModal();
}

// Update session status for multiple facilitators
function updateSessionStatusMultiple(sessionId, status, facilitators) {
  const sessionCard = document.querySelector(`[data-session-id="${sessionId}"]`);
  if (!sessionCard) return;
  
  const facilitatorElement = sessionCard.querySelector('.session-facilitator');
  if (!facilitatorElement) return;
  
  // Remove existing status classes
  facilitatorElement.classList.remove('unassigned', 'pending', 'assigned');
  
  // Add new status class and update content
  switch (status) {
    case 'pending':
      facilitatorElement.classList.add('pending');
      facilitatorElement.textContent = 'Pending';
      facilitatorElement.title = `Assigned to: ${facilitators.map(f => f.name).join(', ')}`;
      break;
    case 'assigned':
      facilitatorElement.classList.add('assigned');
      facilitatorElement.textContent = facilitators.length > 1 ? `${facilitators.length} Facilitators` : getInitials(facilitators[0].name);
      facilitatorElement.title = `Assigned to: ${facilitators.map(f => f.name).join(', ')}`;
      break;
    case 'unassigned':
    default:
      facilitatorElement.classList.add('unassigned');
      facilitatorElement.textContent = 'Unassigned';
      facilitatorElement.title = 'Click to assign facilitators';
      break;
  }
}

// Show assignment confirmation for multiple facilitators
function showMultipleAssignmentConfirmation(facilitators, sessionName) {
  const popup = document.createElement('div');
  popup.className = 'assignment-confirmation-popup';
  popup.innerHTML = `
    <div class="assignment-popup-content">
      <div class="assignment-popup-header">
        <span class="material-icons assignment-success-icon">check_circle</span>
        <h3>Assignment Confirmed</h3>
      </div>
      <div class="assignment-popup-body">
        <p>This session has been assigned to:</p>
        <div class="assigned-facilitators">
          ${facilitators.map(facilitator => `
            <div class="assigned-facilitator">
              <div class="facilitator-avatar-large">
                ${getFacilitatorInitials(facilitator.name)}
              </div>
              <div class="facilitator-details">
                <div class="facilitator-name-large">${facilitator.name}</div>
                <div class="session-name">${sessionName}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
      <div class="assignment-popup-footer">
        <button class="btn btn-primary" onclick="closeAssignmentConfirmation()">OK</button>
      </div>
    </div>
  `;
  
  // Style the popup
  popup.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
  `;
  
  // Add to page
  document.body.appendChild(popup);
  
  // Auto-close after 5 seconds
  setTimeout(() => {
    closeAssignmentConfirmation();
  }, 5000);
}

// Assignment confirmation popup
function showAssignmentConfirmation(facilitatorName, sessionName) {
  // Create popup modal
  const popup = document.createElement('div');
  popup.className = 'assignment-confirmation-popup';
  popup.innerHTML = `
    <div class="assignment-popup-content">
      <div class="assignment-popup-header">
        <span class="material-icons assignment-success-icon">check_circle</span>
        <h3>Assignment Confirmed</h3>
      </div>
      <div class="assignment-popup-body">
        <p>This session has been assigned to:</p>
        <div class="assigned-facilitator">
          <div class="facilitator-avatar-large">
            ${getFacilitatorInitials(facilitatorName)}
          </div>
          <div class="facilitator-details">
            <div class="facilitator-name-large">${facilitatorName}</div>
            <div class="session-name">${sessionName}</div>
          </div>
        </div>
      </div>
      <div class="assignment-popup-footer">
        <button class="btn btn-primary" onclick="closeAssignmentConfirmation()">OK</button>
      </div>
    </div>
  `;
  
  // Style the popup
  popup.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
  `;
  
  // Add to page
  document.body.appendChild(popup);
  
  // Auto-close after 5 seconds
  setTimeout(() => {
    closeAssignmentConfirmation();
  }, 5000);
}

// Close assignment confirmation popup
function closeAssignmentConfirmation() {
  const popup = document.querySelector('.assignment-confirmation-popup');
  if (popup && popup.parentNode) {
    popup.parentNode.removeChild(popup);
  }
}

// Search facilitators
function searchFacilitators() {
  const searchTerm = document.getElementById('facilitator-search').value.toLowerCase();
  
  if (searchTerm === '') {
    filteredFacilitators = [...allFacilitators];
  } else {
    filteredFacilitators = allFacilitators.filter(facilitator => 
      facilitator.name.toLowerCase().includes(searchTerm) ||
      facilitator.email.toLowerCase().includes(searchTerm)
    );
  }
  
  renderFacilitatorList();
}

// Publish Schedule Functions
function openPublishConfirmation() {
  // Count sessions and facilitators
  const sessionCards = document.querySelectorAll('.session-card');
  const assignedSessions = Array.from(sessionCards).filter(card => {
    const facilitatorElement = card.querySelector('.session-facilitator');
    return facilitatorElement && !facilitatorElement.classList.contains('unassigned');
  });
  
  // Count unique facilitators
  const facilitatorNames = new Set();
  assignedSessions.forEach(card => {
    const facilitatorElement = card.querySelector('.session-facilitator');
    if (facilitatorElement && facilitatorElement.title) {
      const title = facilitatorElement.title;
      if (title.includes('Assigned to:')) {
        const facilitators = title.replace('Assigned to: ', '').split(', ');
        facilitators.forEach(fac => facilitatorNames.add(fac.trim()));
      }
    }
  });
  
  // Update summary
  document.getElementById('publish-session-count').textContent = `${assignedSessions.length} sessions`;
  document.getElementById('publish-facilitator-count').textContent = `${facilitatorNames.size} facilitators`;
  
  // Show modal
  document.getElementById('publish-confirmation-modal').style.display = 'flex';
}

function closePublishConfirmation() {
  document.getElementById('publish-confirmation-modal').style.display = 'none';
}

async function confirmPublish() {
  try {
    // Get current unit ID
    const tabsNav = document.querySelector('.uc-tabs[data-unit-id]');
    const currentUnitId = tabsNav ? tabsNav.getAttribute('data-unit-id') : null;
    
    if (!currentUnitId) {
      showSimpleNotification('No unit selected', 'error');
      return;
    }
    
    const response = await fetch(`/unitcoordinator/units/${currentUnitId}/publish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': window.csrfToken
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.ok) {
      showSimpleNotification('Schedule published successfully! Facilitators have been notified.', 'success');
      closePublishConfirmation();
      
      // Update publish button state
      const publishBtn = document.getElementById('publish-schedule-btn');
      publishBtn.disabled = true;
      publishBtn.innerHTML = '<span class="material-icons">check</span>Published';
    } else {
      throw new Error(result.error || 'Failed to publish schedule');
    }
    
  } catch (error) {
    console.error('Error publishing schedule:', error);
    showSimpleNotification(`Error publishing schedule: ${error.message}`, 'error');
  }
}

// Initialize modal event listeners
document.addEventListener('DOMContentLoaded', function() {
  // Publish Confirmation Modal
  document.getElementById('publish-confirmation-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      closePublishConfirmation();
    }
  });
  
  document.getElementById('publish-confirmation-close').addEventListener('click', closePublishConfirmation);
  document.getElementById('publish-cancel').addEventListener('click', closePublishConfirmation);
  document.getElementById('publish-confirm').addEventListener('click', confirmPublish);
  
  // Publish Button
  document.getElementById('publish-schedule-btn').addEventListener('click', openPublishConfirmation);
  
  // Create Session Modal
  document.getElementById('create-session-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      closeCreateSessionModal();
    }
  });
  
  document.getElementById('create-session-modal-close').addEventListener('click', closeCreateSessionModal);
  document.getElementById('create-session-cancel').addEventListener('click', closeCreateSessionModal);
  document.getElementById('create-session-submit').addEventListener('click', createSession);
  
  // Facilitator Modal
  document.getElementById('facilitator-modal').addEventListener('click', function(e) {
    if (e.target === this) {
      closeFacilitatorModal();
    }
  });
  
  document.getElementById('facilitator-modal-close').addEventListener('click', closeFacilitatorModal);
  document.getElementById('facilitator-modal-cancel').addEventListener('click', closeFacilitatorModal);
  document.getElementById('facilitator-modal-select').addEventListener('click', selectMultipleFacilitators);
  
  // Search functionality
  document.getElementById('facilitator-search').addEventListener('input', searchFacilitators);
});

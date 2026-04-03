/* ============================================================
   S3 Backup — Frontend SPA
   ============================================================ */

const BASE = document.querySelector('meta[name="ingress-path"]')?.content || "";

let _allLogs = [];
let _logRefreshTimer = null;
let _statusRefreshTimer = null;
let _pendingDeleteFn = null;

// ------------------------------------------------------------------ //
// Utilities                                                            //
// ------------------------------------------------------------------ //

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "–";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(1) + " " + units[i];
}

function formatDate(iso) {
  if (!iso) return "–";
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function timeAgo(iso) {
  if (!iso) return "Never";
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60)    return "Just now";
  if (diff < 3600)  return Math.floor(diff / 60) + " min ago";
  if (diff < 86400) return Math.floor(diff / 3600) + " hr ago";
  return Math.floor(diff / 86400) + " days ago";
}

function timeUntil(iso) {
  if (!iso) return "N/A";
  const diff = (new Date(iso) - Date.now()) / 1000;
  if (diff <= 0)    return "Overdue";
  if (diff < 3600)  return "in " + Math.floor(diff / 60) + " min";
  if (diff < 86400) return "in " + Math.floor(diff / 3600) + " hr";
  return "in " + Math.floor(diff / 86400) + " days";
}

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str ?? "";
  return d.innerHTML;
}

function toast(msg, type = "blue darken-1") {
  const icon = type.startsWith("red") ? "error" : type.startsWith("green") ? "check_circle" : "info";
  M.toast({
    html: `<i class="material-icons left tiny">${icon}</i>${esc(msg)}`,
    classes: type,
    displayLength: 3500,
  });
}

// ------------------------------------------------------------------ //
// API                                                                  //
// ------------------------------------------------------------------ //

async function api(path, options = {}) {
  const resp = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => resp.statusText);
    throw new Error(`HTTP ${resp.status}: ${text}`);
  }
  return resp.json();
}

// ------------------------------------------------------------------ //
// Dashboard: Status Cards                                              //
// ------------------------------------------------------------------ //

function setCardState(cardId, iconId, valueId, value, state /* healthy|warning|error|neutral */) {
  document.getElementById(valueId).textContent = value;
  const card = document.getElementById(cardId);
  const icon = document.getElementById(iconId);
  card.className = "card status-card " + state;
  icon.className = "material-icons status-icon " + state;
}

function updateStatusCards(data) {
  // Last backup
  if (data.last_backup) {
    const hrs = (Date.now() - new Date(data.last_backup)) / 3600000;
    const state = hrs < 25 ? "healthy" : hrs < 72 ? "warning" : "error";
    setCardState("card-last-backup", "icon-last-backup", "val-last-backup", timeAgo(data.last_backup), state);
  } else {
    setCardState("card-last-backup", "icon-last-backup", "val-last-backup", "Never", "warning");
  }

  // Next backup
  if (data.next_backup) {
    const overdue = Date.now() > new Date(data.next_backup);
    setCardState("card-next-backup", "icon-next-backup", "val-next-backup",
      timeUntil(data.next_backup), overdue ? "error" : "neutral");
  } else {
    setCardState("card-next-backup", "icon-next-backup", "val-next-backup", "Disabled", "neutral");
  }

  document.getElementById("val-ha-count").textContent = data.ha_count ?? "–";
  document.getElementById("val-s3-count").textContent = data.s3_count ?? "–";

  // Global spinner
  const spinning = data.syncing || data.backing_up;
  document.getElementById("loading-spinner").style.display = spinning ? "block" : "none";
  const syncIcon = document.getElementById("sync-icon");
  syncIcon.classList.toggle("rotating", spinning);
}

// ------------------------------------------------------------------ //
// Dashboard: Backup Table                                              //
// ------------------------------------------------------------------ //

function updateBackupTable(backups) {
  const tbody = document.getElementById("backup-tbody");
  if (!backups || backups.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="center-align grey-text" style="padding:32px;">
      No backups found. Click <b>Backup Now</b> to create one.
    </td></tr>`;
    return;
  }

  tbody.innerHTML = backups.map(b => {
    const size = b.in_ha ? formatBytes(b.size * 1024 * 1024) : formatBytes(b.s3_size);
    const date = b.in_ha ? formatDate(b.date) : formatDate(b.s3_date);

    const haBadge = b.in_ha
      ? `<span class="badge-location badge-present"><i class="material-icons" style="font-size:12px;">check</i>HA</span>`
      : `<span class="badge-location badge-missing"><i class="material-icons" style="font-size:12px;">close</i>HA</span>`;

    const s3Badge = b.in_s3
      ? `<span class="badge-location badge-present"><i class="material-icons" style="font-size:12px;">cloud_done</i>S3</span>`
      : `<span class="badge-location badge-missing"><i class="material-icons" style="font-size:12px;">cloud_off</i>S3</span>`;

    const uploadBtn = b.in_ha && !b.in_s3
      ? `<a href="#" class="btn-small blue darken-2 waves-effect waves-light action-btn tooltipped"
           data-tooltip="Upload to S3" onclick="doUpload(event,'${b.slug}')">
           <i class="material-icons">cloud_upload</i></a>`
      : "";

    const delHaBtn = b.in_ha
      ? `<a href="#" class="btn-small red lighten-1 waves-effect action-btn tooltipped"
           data-tooltip="Delete from HA" onclick="doDeleteHA(event,'${b.slug}','${esc(b.name)}')">
           <i class="material-icons">home</i></a>`
      : "";

    const delS3Btn = b.in_s3
      ? `<a href="#" class="btn-small red waves-effect action-btn tooltipped"
           data-tooltip="Delete from S3" onclick="doDeleteS3(event,'${b.slug}','${esc(b.name)}')">
           <i class="material-icons">cloud</i></a>`
      : "";

    return `<tr>
      <td><b>${esc(b.name)}</b></td>
      <td style="white-space:nowrap;">${date}</td>
      <td>${size}</td>
      <td>${haBadge}</td>
      <td>${s3Badge}</td>
      <td style="white-space:nowrap;">${uploadBtn}${delHaBtn}${delS3Btn}</td>
    </tr>`;
  }).join("");

  // Re-init tooltips on new elements
  M.Tooltip.init(document.querySelectorAll(".tooltipped"));
}

// ------------------------------------------------------------------ //
// Load / refresh                                                       //
// ------------------------------------------------------------------ //

async function loadStatus() {
  try {
    const data = await api("/api/status");
    updateStatusCards(data);
    updateBackupTable(data.backups || []);
    if (data.error)        showBanner(data.error, "error");
    else if (data.warning) showBanner(data.warning, "warning");
    else                   hideBanner();
  } catch (err) {
    showError("Failed to load status: " + err.message);
  }
}

function showBanner(msg, type = "error") {
  const isWarn = type === "warning";
  document.getElementById("error-banner").style.display = "block";
  document.getElementById("error-message").textContent = msg;
  document.getElementById("error-icon").textContent = isWarn ? "info" : "error";
  const card = document.getElementById("error-card");
  const content = document.getElementById("error-card-content");
  card.style.borderLeftColor = isWarn ? "#fb8c00" : "#e53935";
  content.className = "card-content " + (isWarn ? "orange-text text-darken-3" : "red-text text-darken-2");
  if (isWarn) card.className = "card orange lighten-5";
  else        card.className = "card red lighten-5";
}

function hideBanner() {
  document.getElementById("error-banner").style.display = "none";
}

// ------------------------------------------------------------------ //
// Actions: Backup / Sync                                               //
// ------------------------------------------------------------------ //

async function triggerBackup(event) {
  event.preventDefault();
  const btn = document.getElementById("btn-backup-now");
  btn.classList.add("disabled");
  toast("Starting backup…");
  try {
    const result = await api("/api/backup", { method: "POST", body: "{}" });
    if (result.error) { toast(result.error, "red darken-1"); }
    else {
      toast("Backup created!", "green darken-1");
      setTimeout(loadStatus, 2000);
    }
  } catch (err) {
    toast("Backup failed: " + err.message, "red darken-1");
  } finally {
    btn.classList.remove("disabled");
  }
}

async function triggerSync(event) {
  event.preventDefault();
  const btn = document.getElementById("btn-sync-now");
  btn.classList.add("disabled");
  document.getElementById("sync-icon").classList.add("rotating");
  toast("Syncing…");
  try {
    const result = await api("/api/sync", { method: "POST", body: "{}" });
    if (result.error) { toast(result.error, "red darken-1"); }
    else { toast(`Sync complete — ${result.uploaded ?? 0} uploaded`, "green darken-1"); }
    await loadStatus();
  } catch (err) {
    toast("Sync failed: " + err.message, "red darken-1");
  } finally {
    btn.classList.remove("disabled");
    document.getElementById("sync-icon").classList.remove("rotating");
  }
}

async function doUpload(event, slug) {
  event.preventDefault();
  toast("Uploading to S3…");
  try {
    const result = await api(`/api/upload/${slug}`, { method: "POST", body: "{}" });
    if (result.error) { toast(result.error, "red darken-1"); }
    else { toast("Uploaded to S3!", "green darken-1"); await loadStatus(); }
  } catch (err) {
    toast("Upload failed: " + err.message, "red darken-1");
  }
}

function doDeleteHA(event, slug, name) {
  event.preventDefault();
  document.getElementById("modal-delete-msg").textContent =
    `Delete "${name}" from Home Assistant? This cannot be undone.`;
  _pendingDeleteFn = async () => {
    try {
      const result = await api(`/api/ha/${slug}`, { method: "DELETE" });
      if (result.error) toast(result.error, "red darken-1");
      else { toast("Deleted from HA", "green darken-1"); await loadStatus(); }
    } catch (err) { toast("Delete failed: " + err.message, "red darken-1"); }
  };
  M.Modal.getInstance(document.getElementById("modal-delete")).open();
}

function doDeleteS3(event, slug, name) {
  event.preventDefault();
  document.getElementById("modal-delete-msg").textContent =
    `Delete "${name}" from S3? This cannot be undone.`;
  _pendingDeleteFn = async () => {
    try {
      const result = await api(`/api/s3/${slug}`, { method: "DELETE" });
      if (result.error) toast(result.error, "red darken-1");
      else { toast("Deleted from S3", "green darken-1"); await loadStatus(); }
    } catch (err) { toast("Delete failed: " + err.message, "red darken-1"); }
  };
  M.Modal.getInstance(document.getElementById("modal-delete")).open();
}

// ------------------------------------------------------------------ //
// Settings                                                             //
// ------------------------------------------------------------------ //

async function loadSettings() {
  try {
    const s = await api("/api/settings");
    const fields = [
      "s3_endpoint", "s3_bucket", "s3_region", "s3_access_key",
      "s3_prefix", "days_between_backups", "max_backups_in_ha", "max_backups_in_s3",
    ];
    fields.forEach(f => {
      const el = document.getElementById(f);
      if (el) el.value = s[f] ?? "";
    });
    // Secret key: never filled, show placeholder
    const secretEl = document.getElementById("s3_secret_key");
    secretEl.placeholder = s.s3_secret_key_set ? "(saved — leave empty to keep)" : "(not set)";

    const chk = document.getElementById("delete_after_upload");
    if (chk) chk.checked = !!s.delete_after_upload;

    M.updateTextFields();
  } catch (err) {
    toast("Failed to load settings: " + err.message, "red darken-1");
  }
}

function collectSettings() {
  return {
    s3_endpoint:           document.getElementById("s3_endpoint").value.trim(),
    s3_bucket:             document.getElementById("s3_bucket").value.trim(),
    s3_region:             document.getElementById("s3_region").value.trim() || "us-east-1",
    s3_access_key:         document.getElementById("s3_access_key").value.trim(),
    s3_secret_key:         document.getElementById("s3_secret_key").value,  // empty = keep existing
    s3_prefix:             document.getElementById("s3_prefix").value.trim(),
    days_between_backups:  parseInt(document.getElementById("days_between_backups").value) || 3,
    max_backups_in_ha:     parseInt(document.getElementById("max_backups_in_ha").value) || 4,
    max_backups_in_s3:     parseInt(document.getElementById("max_backups_in_s3").value) || 4,
    delete_after_upload:   document.getElementById("delete_after_upload").checked,
  };
}

async function saveSettings(event) {
  event.preventDefault();
  try {
    const result = await api("/api/settings", { method: "POST", body: JSON.stringify(collectSettings()) });
    if (result.error) toast(result.error, "red darken-1");
    else toast("Settings saved!", "green darken-1");
  } catch (err) {
    toast("Save failed: " + err.message, "red darken-1");
  }
}

async function testConnection(event) {
  event.preventDefault();
  toast("Testing connection…");
  try {
    const body = { ...collectSettings(), test_only: true };
    const result = await api("/api/settings", { method: "POST", body: JSON.stringify(body) });
    if (result.ok) toast("Connection successful! Bucket accessible.", "green darken-1");
    else toast("Connection failed: " + (result.error || "unknown error"), "red darken-1");
  } catch (err) {
    toast("Test failed: " + err.message, "red darken-1");
  }
}

// ------------------------------------------------------------------ //
// Logs                                                                 //
// ------------------------------------------------------------------ //

async function loadLogs() {
  try {
    _allLogs = await api("/api/logs");
    renderLogs();
  } catch (err) {
    console.warn("Failed to load logs:", err);
  }
}

function renderLogs() {
  const level = document.getElementById("log-level-filter").value;
  const filtered = level === "ALL" ? _allLogs : _allLogs.filter(l => l.level === level);
  const tbody = document.getElementById("log-tbody");

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="center-align grey-text" style="padding:32px;">No log entries</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.slice(0, 300).map(log => {
    const time = log.time ? new Date(log.time * 1000).toLocaleString() : "–";
    return `<tr>
      <td style="white-space:nowrap;">${time}</td>
      <td class="level-${log.level}"><b>${log.level}</b></td>
      <td>${esc(log.message)}</td>
    </tr>`;
  }).join("");
}

function filterLogs() { renderLogs(); }

function toggleLogRefresh() {
  const enabled = document.getElementById("log-auto-refresh").checked;
  if (enabled) startLogRefresh(); else stopLogRefresh();
}

function startLogRefresh() {
  if (!_logRefreshTimer) _logRefreshTimer = setInterval(loadLogs, 4000);
}

function stopLogRefresh() {
  clearInterval(_logRefreshTimer);
  _logRefreshTimer = null;
}

// ------------------------------------------------------------------ //
// Init                                                                 //
// ------------------------------------------------------------------ //

document.addEventListener("DOMContentLoaded", () => {
  // Materialize init
  M.Tabs.init(document.querySelectorAll(".tabs"), {
    onShow(el) {
      if (el.id === "tab-settings") loadSettings();
      if (el.id === "tab-logs")     { loadLogs(); startLogRefresh(); }
      if (el.id !== "tab-logs")     stopLogRefresh();
    },
  });

  M.Modal.init(document.querySelectorAll(".modal"));
  M.FormSelect.init(document.querySelectorAll("select"));

  document.getElementById("modal-delete-confirm").addEventListener("click", () => {
    M.Modal.getInstance(document.getElementById("modal-delete")).close();
    if (_pendingDeleteFn) { _pendingDeleteFn(); _pendingDeleteFn = null; }
  });

  // Initial load
  loadStatus();

  // Auto-refresh status every 30 s
  _statusRefreshTimer = setInterval(loadStatus, 30000);
});

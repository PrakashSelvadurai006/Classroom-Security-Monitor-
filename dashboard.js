/* =============================================
   CLASSROOM FACE MONITOR — Dashboard Live Stats
   ============================================= */

const Dashboard = (() => {
    const POLL_MS = 3000;

    function init() {
        if (!document.getElementById('stat-students')) return; // not on dashboard
        pollStats();
        setInterval(pollStats, POLL_MS);
    }

    async function pollStats() {
        try {
            const res = await fetch('/dashboard_stats');
            const data = await res.json();
            if (data.status !== 'success') return;
            const d = data.data;

            setText('stat-students', d.total_students);
            setText('stat-entries', d.today_entries);
            setText('stat-alerts', d.active_alerts_count);
            setText('stat-monitoring', d.monitoring_active ? '🟢 Active' : '🔴 Inactive');

            renderRecentEntries(d.recent_entries || []);
            renderActiveAlerts(d.active_alerts || []);
        } catch (err) {
            console.warn('Stats poll error:', err);
        }
    }

    function setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val ?? '—';
    }

    function renderRecentEntries(entries) {
        const tbody = document.getElementById('recent-entries-body');
        if (!tbody) return;
        if (!entries.length) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="4">No entries yet</td></tr>';
            return;
        }
        tbody.innerHTML = entries.map(e => `
      <tr>
        <td>${fmtTime(e.entry_time)}</td>
        <td>${esc(e.student_name)}</td>
        <td>${e.is_recognized
                ? '<span class="badge badge-green">✅ Recognised</span>'
                : '<span class="badge badge-red">❌ Unknown</span>'}</td>
        <td>${e.confidence_score ? (e.confidence_score * 100).toFixed(0) + '%' : '—'}</td>
      </tr>`).join('');
    }

    function renderActiveAlerts(alerts) {
        const list = document.getElementById('active-alerts-list');
        if (!list) return;
        if (!alerts.length) {
            list.innerHTML = '<p class="text-muted text-center mt-3">No active alerts 🎉</p>';
            return;
        }
        const iconMap = { high: '🚨', medium: '⚠️', low: 'ℹ️' };
        list.innerHTML = alerts.map(a => `
      <div class="alert-item">
        <div class="alert-icon ${a.severity}">${iconMap[a.severity] || '⚠️'}</div>
        <div class="alert-body">
          <div class="alert-msg">${esc(a.message)}</div>
          <div class="alert-meta">${fmtTime(a.created_at)} · <span class="badge badge-${severityBadge(a.severity)}">${a.severity}</span></div>
          <div class="mt-2">
            <button class="btn btn-sm btn-success" onclick="resolveAlert(${a.id})">✔ Resolve</button>
            <button class="btn btn-sm btn-danger" style="margin-left:6px" onclick="stopAlarm()">🔕 Stop Alarm</button>
          </div>
        </div>
      </div>`).join('');
    }

    function severityBadge(s) {
        return { high: 'red', medium: 'yellow', low: 'blue' }[s] || 'grey';
    }

    function esc(str) {
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(str || ''));
        return d.innerHTML;
    }

    return { init };
})();

async function resolveAlert(id) {
    const data = await postJson(`/resolve_alert/${id}`);
    showToast(data.status === 'success' ? '✔ Alert resolved' : '❌ ' + data.message,
        data.status === 'success' ? 'success' : 'error');
}

async function stopAlarm() {
    const data = await postJson('/stop_alarm');
    showToast(data.status === 'success' ? '🔕 Alarm stopped' : '❌ ' + data.message,
        data.status === 'success' ? 'info' : 'error');
}

async function clearAllData() {
    if (!confirmAction('This will clear ALL entry logs and alerts. Students are kept. Continue?')) return;
    const data = await postJson('/clear_all_data');
    showToast(data.message, data.status === 'success' ? 'success' : 'error');
}

document.addEventListener('DOMContentLoaded', () => Dashboard.init());

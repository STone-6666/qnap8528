const statusEl = document.getElementById('status');
const alertsEl = document.getElementById('alerts');
const curveSelect = document.getElementById('curveSelect');
const modeSelect = document.getElementById('modeSelect');
const manualPercent = document.getElementById('manualPercent');
const manualValue = document.getElementById('manualValue');
const channelInput = document.getElementById('channel');
const pointBox = document.getElementById('points');

const editor = new CurveEditor(document.getElementById('curveCanvas'));
let currentCurve = { name: 'balanced', points: [] };

manualPercent.addEventListener('input', () => manualValue.textContent = `${manualPercent.value}%`);

function renderPoints(points) {
  pointBox.innerHTML = points.map((p, i) => `
    <div class="point">点${i + 1}<br/>${p.temp}°C -> ${p.pwm}%</div>
  `).join('');
}

editor.onchange = (points) => {
  currentCurve.points = points;
  renderPoints(points);
};

async function refreshStatus() {
  try {
    const s = await api.get('/api/status');
    modeSelect.value = s.mode;
    const tempHtml = (s.temperatures || []).map(t => `<li>${t.sensor}: ${t.celsius}°C</li>`).join('');
    const fanHtml = (s.fans || []).map(f => `<li>fan${f.channel}: ${f.rpm} RPM | PWM ${f.pwm_percent}% | ${f.mode}</li>`).join('');
    statusEl.innerHTML = `<ul>${tempHtml}${fanHtml}</ul>`;
    alertsEl.textContent = (s.alerts || []).join(' | ');
  } catch (e) {
    alertsEl.textContent = `状态读取失败: ${e.message}`;
  }
}

async function loadCurveList() {
  const data = await api.get('/api/curves');
  curveSelect.innerHTML = data.curves.map(c => `<option>${c}</option>`).join('');
}

async function loadCurve(name) {
  const curve = await api.get(`/api/curves/${name}`);
  currentCurve = { name, points: curve.points || [] };
  editor.setPoints(currentCurve.points);
  renderPoints(currentCurve.points);
}

document.getElementById('applyManual').onclick = async () => {
  await api.post('/api/fan/manual', {
    channel: Number(channelInput.value),
    percent: Number(manualPercent.value),
  });
  await api.post('/api/mode', { mode: 'manual' });
  refreshStatus();
};

document.getElementById('applyAuto').onclick = async () => {
  await api.post('/api/fan/auto', { channel: Number(channelInput.value) });
  await api.post('/api/mode', { mode: 'auto' });
  refreshStatus();
};

document.getElementById('loadCurve').onclick = async () => loadCurve(curveSelect.value);
document.getElementById('applyCurve').onclick = async () => {
  await api.post('/api/curves/apply', { name: curveSelect.value });
  refreshStatus();
};

document.getElementById('saveCurve').onclick = async () => {
  const name = document.getElementById('curveName').value || currentCurve.name;
  await api.post(`/api/curves/${name}`, { name, points: currentCurve.points });
  await loadCurveList();
};

(async function boot() {
  await loadCurveList();
  await loadCurve('balanced').catch(() => {});
  await refreshStatus();
  setInterval(refreshStatus, 3000);
})();

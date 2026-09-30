function cred() {
  const u = document.getElementById('user').value;
  const p = document.getElementById('pass').value;
  return 'Basic ' + btoa(u + ':' + p);
}
function base() {
  return 'http://' + location.hostname + ':8000';
}
function status(msg, isErr) {
  const el = document.getElementById('statusline');
  el.textContent = msg;
  el.classList.toggle('err', !!isErr);
}
async function api(path, opts) {
  opts = opts || {};
  opts.headers = Object.assign({}, opts.headers, { 'Authorization': cred() });
  const r = await fetch(base() + path, opts);
  if (r.status === 401) { status('Login prüfen', true); throw new Error('auth'); }
  return r;
}
async function send(e) {
  e.preventDefault();
  const agent = document.getElementById('agent').value;
  const prompt = document.getElementById('prompt').value;
  try {
    const r = await api('/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: prompt.slice(0, 40), agent: agent, prompt: prompt })
    });
    if (r.ok) { status('Task ' + (await r.json()).id); tick(); }
    else { status('Fehler ' + r.status, true); }
  } catch (err) {
    if (String(err.message) !== 'auth') status('offline?', true);
  }
}
const AGENTS = Array.from(document.getElementById('agent').options).map((o) => o.value);
const seen = new Set();
function stamp() {
  return new Date().toTimeString().slice(0, 8);
}
function feed(text) {
  const ul = document.getElementById('ticker');
  const li = document.createElement('li');
  const t = document.createElement('time');
  t.textContent = stamp();
  const s = document.createElement('span');
  s.textContent = text;
  li.appendChild(t);
  li.appendChild(s);
  ul.prepend(li);
  while (ul.children.length > 30) ul.removeChild(ul.lastChild);
}
function renderAgents(ts) {
  const strip = document.getElementById('agents');
  strip.innerHTML = '';
  AGENTS.forEach((a) => {
    const mine = ts.filter((t) => t.agent === a);
    const running = mine.filter((t) => t.status === 'running').length;
    const failed = mine.filter((t) => t.status === 'failed').length;
    const chip = document.createElement('div');
    chip.className = 'agent-chip';
    chip.setAttribute('role', 'listitem');
    const dot = document.createElement('span');
    dot.className = 'dot' + (running ? ' on' : failed ? ' warn' : '');
    const name = document.createElement('span');
    name.textContent = a;
    const cnt = document.createElement('span');
    cnt.className = 'cnt';
    cnt.textContent = mine.length + ' tasks';
    chip.appendChild(dot);
    chip.appendChild(name);
    chip.appendChild(cnt);
    strip.appendChild(chip);
  });
}
function renderTasks(ts) {
  const cols = ['inbox', 'running', 'review', 'done', 'failed'];
  const counts = {};
  cols.forEach((c) => {
    counts[c] = 0;
    const col = document.getElementById(c);
    col.querySelectorAll('.task-card,.empty').forEach((n) => n.remove());
  });
  ts.forEach((t) => {
    if (t.id && !seen.has(t.id)) {
      seen.add(t.id);
      feed(t.agent + ' → ' + t.title);
    }
    const col = document.getElementById(t.status) || document.getElementById('inbox');
    counts[col.id] = (counts[col.id] || 0) + 1;
    const d = document.createElement('div');
    d.className = 'task-card st-' + col.id;
    d.setAttribute('data-id', t.id);
    d.setAttribute('tabindex', '0');
    d.setAttribute('role', 'button');
    const title = document.createElement('div');
    title.textContent = t.title;
    const meta = document.createElement('span');
    meta.className = 'meta';
    meta.textContent = t.agent + ' · ' + t.status;
    d.appendChild(title);
    d.appendChild(meta);
    col.appendChild(d);
    if (t.status === 'failed' && !seen.has(t.id + ':failed')) {
      seen.add(t.id + ':failed');
      feed(t.agent + ' ✕ ' + t.title);
    }
  });
  cols.forEach((c) => {
    const col = document.getElementById(c);
    col.querySelector('h2 .n').textContent = counts[c] || 0;
    if (!counts[c]) {
      const e = document.createElement('div');
      e.className = 'empty';
      e.textContent = c === 'inbox' ? 'Keine Tasks – oben anlegen' : 'Leer';
      col.appendChild(e);
    }
  });
  const live = document.getElementById('livedot');
  const lt = document.getElementById('livetext');
  const running = ts.filter((t) => t.status === 'running').length;
  live.className = 'dot' + (running ? ' on' : '');
  lt.textContent = running ? running + ' aktiv' : ts.length ? 'bereit · ' + ts.length + ' tasks' : 'bereit';
}
async function showDetail(id) {
  try {
    const d = await (await api('/tasks/' + id)).json();
    const rids = d.run_ids || [];
    let logtxt = '';
    if (rids.length) {
      const rid = rids[rids.length - 1];
      const logs = await (await api('/runs/' + rid + '/logs')).json();
      logtxt = (logs.lines || []).join('\n');
    }
    document.querySelectorAll('.task-card.active').forEach((n) => n.classList.remove('active'));
    const card = document.querySelector('[data-id="' + id + '"]');
    if (card) card.classList.add('active');
    document.getElementById('detail').textContent = d.title + ' (' + d.status + ')\n' + logtxt;
  } catch (err) {
    if (String(err.message) !== 'auth') status('offline?', true);
  }
}
async function tick() {
  try {
    const ts = await (await api('/tasks')).json();
    renderTasks(ts);
    renderAgents(ts);
    const mem = await (await api('/memory')).json();
    document.getElementById('memory').innerHTML = mem.map((m) => '<li>' + m.name + '</li>').join('');
    const cj = await fetch('/sched/jobs', { headers: { 'Authorization': cred() } });
    if (cj.status === 401) { status('Login prüfen', true); return; }
    const jobs = await cj.json();
    document.getElementById('cron').innerHTML = jobs.map((j) => '<li>' + (j.name || j.id) + '</li>').join('');
  } catch (err) {
    if (String(err.message) !== 'auth') status('offline?', true);
  }
}
document.getElementById('f').addEventListener('submit', send);
document.addEventListener('click', (ev) => {
  const el = ev.target.closest ? ev.target.closest('[data-id]') : null;
  if (el) showDetail(el.getAttribute('data-id'));
});
document.addEventListener('keydown', (ev) => {
  if (ev.key === 'Enter' && ev.target.classList && ev.target.classList.contains('task-card')) {
    showDetail(ev.target.getAttribute('data-id'));
  }
});
setInterval(tick, 2500);
tick();

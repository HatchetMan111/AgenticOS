function cred() {
  const u = document.getElementById('user').value;
  const p = document.getElementById('pass').value;
  return 'Basic ' + btoa(u + ':' + p);
}
function base() {
  return 'http://' + location.hostname + ':8000';
}
function status(msg) {
  document.getElementById('statusline').textContent = msg;
}
async function api(path, opts) {
  opts = opts || {};
  opts.headers = Object.assign({}, opts.headers, { 'Authorization': cred() });
  const r = await fetch(base() + path, opts);
  if (r.status === 401) { status('Login prüfen'); throw new Error('auth'); }
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
    if (r.ok) { status('Task ' + (await r.json()).id); }
    else { status('Fehler ' + r.status); }
  } catch (err) {
    if (String(err.message) !== 'auth') status('offline?');
  }
}
function renderTasks(ts) {
  const cols = ['inbox', 'running', 'review', 'done', 'failed'];
  cols.forEach((c) => { document.getElementById(c).innerHTML = '<h2>' + c + '</h2>'; });
  ts.forEach((t) => {
    const col = document.getElementById(t.status) || document.getElementById('inbox');
    const d = document.createElement('div');
    d.setAttribute('data-id', t.id);
    d.textContent = t.title + ' [' + t.agent + '] ' + t.status;
    col.appendChild(d);
  });
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
    document.getElementById('detail').textContent = d.title + ' (' + d.status + ')\n' + logtxt;
  } catch (err) {
    if (String(err.message) !== 'auth') status('offline?');
  }
}
async function tick() {
  try {
    const ts = await (await api('/tasks')).json();
    renderTasks(ts);
    const mem = await (await api('/memory')).json();
    document.getElementById('memory').innerHTML = mem.map((m) => '<li>' + m.name + '</li>').join('');
    const cj = await fetch('/sched/jobs', { headers: { 'Authorization': cred() } });
    if (cj.status === 401) { status('Login prüfen'); return; }
    const jobs = await cj.json();
    document.getElementById('cron').innerHTML = jobs.map((j) => '<li>' + (j.name || j.id) + '</li>').join('');
  } catch (err) {
    if (String(err.message) !== 'auth') status('offline?');
  }
}
document.getElementById('f').addEventListener('submit', send);
document.addEventListener('click', (ev) => {
  const el = ev.target.closest ? ev.target.closest('[data-id]') : null;
  if (el) showDetail(el.getAttribute('data-id'));
});
setInterval(tick, 2500);
tick();

import { api } from './api.js';
import { renderFiles } from './pages/files.js';
import { renderPlans } from './pages/plans.js';
import { renderRewrite } from './pages/rewrite.js';
import { renderReconcile } from './pages/reconcile.js';
import { renderSettings } from './pages/settings.js';

const view = document.getElementById('view');
const msg = document.getElementById('msg');

function setMsg(text, err = false) {
  msg.textContent = text || '';
  msg.className = err ? 'err' : 'muted';
}

async function show(page) {
  setMsg('');
  const map = {
    files: renderFiles,
    plans: renderPlans,
    rewrite: renderRewrite,
    reconcile: renderReconcile,
    settings: renderSettings,
  };
  const fn = map[page];
  if (!fn) {
    view.innerHTML = '<p class="err">未知页面</p>';
    return;
  }
  try {
    await fn(view, setMsg);
  } catch (e) {
    view.innerHTML = `<section class="card"><h2>页面加载失败</h2><p class="err">${e.message || e}</p></section>`;
    setMsg(e.message || String(e), true);
  }
}

document.querySelectorAll('.timeline button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.timeline button').forEach(b => b.classList.remove('on'));
    btn.classList.add('on');
    show(btn.dataset.tab);
  };
});

document.getElementById('btn-logout').onclick = async () => {
  await api('/api/logout', { method:'POST', body:'{}' });
  location.href = '/login';
};

api('/api/meta').then(j => {
  document.getElementById('lab-name').textContent = j.lab || '湖表压实台';
}).catch(() => {});

show('files');

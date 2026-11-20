import { api } from '../api.js';

export async function renderRewrite(view, setMsg) {
  const plans = await api('/api/plans');
  const jobs = await api('/api/rewrite/jobs');
  const options = (plans.items || []).map(p => `<option value="${p.id}">${p.plan_code} · ${p.status}</option>`).join('');
  view.innerHTML = `
    <section class="card">
      <h2>重写合并</h2>
      <p class="muted">对已发布计划启动合并；成功后碎文件变为已合并。</p>
      <div class="row">
        <label>计划<select id="pid">${options}</select></label>
        <button class="primary" id="go" type="button">启动合并</button>
      </div>
    </section>
    <section class="wall" style="margin-top:1rem">
      ${(jobs.items || []).map(j => `<article class="card">
        <h3>${j.plan_code || ('计划#'+j.plan_id)}</h3>
        <span class="tag">${j.status}</span>
        <p class="muted">${j.message}</p>
        <p>合并字节 ${j.merged_bytes}</p>
      </article>`).join('') || '<p class="muted">尚无合并任务</p>'}
    </section>`;
  document.getElementById('go').onclick = async () => {
    try {
      const pid = document.getElementById('pid').value;
      const r = await api('/api/rewrite/plans/' + pid + '/start', { method:'POST', body:'{}' });
      setMsg('合并完成 · ' + r.job.status);
      await renderRewrite(view, setMsg);
    } catch (e) { setMsg(e.message, true); }
  };
}

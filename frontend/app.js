const form = document.querySelector('#plan-form');
const formView = document.querySelector('#form-view');
const planView = document.querySelector('#plan-view');
const goalLabels = { lose: 'Perder peso', maintain: 'Manter o peso', gain: 'Ganhar massa' };
const formatDate = value => new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(`${value}T12:00:00`));

function showView(view) {
  const hasPlan = Boolean(localStorage.getItem('nutriplan:last-plan'));
  if (view === 'plan' && !hasPlan) view = 'form';
  formView.hidden = view !== 'form';
  planView.hidden = view !== 'plan';
  document.querySelectorAll('[data-view-link]').forEach(link => link.classList.toggle('active', link.dataset.viewLink === view));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function escapeHtml(value) {
  const div = document.createElement('div'); div.textContent = String(value); return div.innerHTML;
}

function renderPlan(plan) {
  document.querySelector('#plan-title').textContent = `Plano de ${plan.person.name}`;
  document.querySelector('#plan-date').textContent = `Criado em ${formatDate(plan.created_at)} · ID ${plan.id}`;
  document.querySelector('#heading-metrics').innerHTML = `
    <div class="metric"><span>OBJETIVO</span><strong>${goalLabels[plan.goal]}</strong></div>
    <div class="metric"><span>REFEIÇÕES</span><strong>${plan.meal_count} por dia</strong></div>
    <div class="metric"><span>PESO ATUAL</span><strong>${plan.person.weight} kg</strong></div>`;
  document.querySelector('#meal-list').innerHTML = plan.meals.map(meal => `
    <article class="meal-card">
      <div class="meal-cover" style="--food-position:${meal.image_position}">
        <div><h2>Refeição ${meal.order}</h2><p>${escapeHtml(meal.name)} · ${meal.time}</p></div>
      </div>
      <div class="meal-body">
        ${meal.items.map(item => `<div class="food-row"><span>${escapeHtml(item.name)}</span><span>${escapeHtml(item.amount)}</span><strong>${item.kcal} kcal</strong></div>`).join('')}
        <div class="meal-total"><span>Total da refeição</span><div class="pills"><span class="pill">${meal.totals.protein}g prot</span><span class="pill">${meal.totals.kcal} kcal</span></div></div>
      </div>
    </article>`).join('');
  document.querySelector('#substitution-list').innerHTML = plan.substitutions.map(item => `<div class="sub-item"><strong>${escapeHtml(item.food)}</strong>${item.options.map(option => `<span>→ ${escapeHtml(option)}</span>`).join('')}</div>`).join('');
  const targetPercent = Math.min(100, Math.round(plan.totals.kcal / plan.target_kcal * 100));
  const macroTotal = plan.totals.protein * 4 + plan.totals.carbs * 4 + plan.totals.fat * 9;
  const macro = (key, label, unit, calories) => {
    const percentage = Math.round(calories / macroTotal * 100);
    return `<div class="macro"><div class="macro-head"><span>${label} (${plan.totals[key]}${unit})</span><strong>${percentage}%</strong></div><div class="bar"><i style="width:${percentage}%"></i></div></div>`;
  };
  document.querySelector('#summary-card').innerHTML = `<h2>Resumo diário <small class="ai-badge">✦ gerado por IA</small></h2><div class="calorie-ring" style="--progress:${targetPercent}%"><div><strong>${plan.totals.kcal}</strong><span>de ${plan.target_kcal} kcal</span></div></div>${macro('protein','Proteínas','g',plan.totals.protein*4)}${macro('carbs','Carboidratos','g',plan.totals.carbs*4)}${macro('fat','Gorduras','g',plan.totals.fat*9)}<div class="strategy"><strong>Estratégia do plano</strong><p>${escapeHtml(plan.strategy)}</p></div><div class="summary-actions"><button class="button button-light" onclick="window.print()">Imprimir / salvar PDF</button><button class="button button-outline" data-new-plan>Criar novo plano</button></div><p class="notice">${escapeHtml(plan.notice)}</p>`;
  document.querySelector('#summary-card [data-new-plan]').addEventListener('click', () => showView('form'));
  showView('plan');
}

function showErrors(fields = {}) {
  document.querySelectorAll('.field-error').forEach(el => el.textContent = fields[el.dataset.error] || '');
  const first = Object.keys(fields)[0];
  if (first && form.elements[first]) form.elements[first].focus();
}

form.addEventListener('submit', async event => {
  event.preventDefault(); showErrors();
  const alert = document.querySelector('#form-alert'); alert.hidden = true;
  const submit = form.querySelector('[type="submit"]'); const text = submit.querySelector('.button-text');
  const values = Object.fromEntries(new FormData(form));
  ['age','weight','height','meal_count'].forEach(key => values[key] = Number(values[key]));
  submit.disabled = true; text.textContent = 'Montando seu plano…';
  try {
    const response = await fetch('/api/plans', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) });
    const data = await response.json();
    if (!response.ok) { showErrors(data.fields); throw new Error(data.message || data.error || 'Revise os dados informados.'); }
    localStorage.setItem('nutriplan:last-plan', JSON.stringify(data)); renderPlan(data);
  } catch (error) {
    alert.textContent = error.message === 'Failed to fetch' ? 'Não foi possível acessar a API. Inicie o projeto com “python app.py” e tente novamente.' : error.message;
    alert.hidden = false;
  } finally { submit.disabled = false; text.textContent = 'Gerar meu plano'; }
});

document.addEventListener('click', event => {
  const newPlan = event.target.closest('[data-new-plan]'); if (newPlan) showView('form');
  const viewLink = event.target.closest('[data-view-link]');
  if (viewLink) { event.preventDefault(); const saved = localStorage.getItem('nutriplan:last-plan'); if (viewLink.dataset.viewLink === 'plan' && saved) renderPlan(JSON.parse(saved)); else showView('form'); }
});

const savedPlan = localStorage.getItem('nutriplan:last-plan');
if (location.hash === '#meu-plano' && savedPlan) renderPlan(JSON.parse(savedPlan));

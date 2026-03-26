// ==================== 예산 히트맵 ====================
function heatColor(v) {
  const clamped = Math.max(-100, Math.min(100, v));
  const intensity = Math.abs(clamped) / 100;
  if (clamped >= 0) return `rgba(22,163,74,${0.1 + intensity * 0.6})`;
  return `rgba(220,38,38,${0.1 + intensity * 0.6})`;
}

function renderBudgetHeatmap(rows) {
  const container = document.getElementById('heatmap-container');
  if (!container) return;

  let html = `<table style="width:100%;border-collapse:collapse;font-size:12px">
    <thead><tr style="border-bottom:2px solid var(--border)">
      <th style="text-align:left;padding:8px 12px;font-weight:600;white-space:nowrap">부처</th>
      <th style="text-align:right;padding:8px 12px;font-weight:600;white-space:nowrap">2024 결산</th>
      <th style="text-align:right;padding:8px 12px;font-weight:600;white-space:nowrap">2025 본예산</th>
      <th style="text-align:right;padding:8px 12px;font-weight:600;white-space:nowrap">2026 확정</th>
      <th style="text-align:center;padding:8px 12px;font-weight:600;min-width:100px">2024&#8594;2025</th>
      <th style="text-align:center;padding:8px 12px;font-weight:600;min-width:100px">2025&#8594;2026</th>
    </tr></thead><tbody>`;

  rows.forEach(r => {
    html += `<tr style="border-bottom:1px solid var(--border)">
      <td style="padding:6px 12px;white-space:nowrap;max-width:150px;overflow:hidden;text-overflow:ellipsis" title="${r.dept}">${r.dept.substring(0, 10)}</td>
      <td style="padding:6px 12px;text-align:right">${formatBillion(r.b2024)}</td>
      <td style="padding:6px 12px;text-align:right">${formatBillion(r.b2025)}</td>
      <td style="padding:6px 12px;text-align:right">${formatBillion(r.b2026)}</td>
      <td style="padding:6px 12px;text-align:center;background:${heatColor(r.chg1)};color:var(--text-primary);font-weight:600;border-radius:4px">${r.chg1 > 0 ? '+' : ''}${r.chg1.toFixed(1)}%</td>
      <td style="padding:6px 12px;text-align:center;background:${heatColor(r.chg2)};color:var(--text-primary);font-weight:600;border-radius:4px">${r.chg2 > 0 ? '+' : ''}${r.chg2.toFixed(1)}%</td>
    </tr>`;
  });

  html += '</tbody></table>';
  container.innerHTML = html;
}

// ==================== 이상치 탐지 ====================
function renderAnomalyDetection(projects) {
  const anomalies = projects.filter(p => {
    const cr = getChangeRate(p);
    return cr !== 0 && Math.abs(cr) >= 50;
  }).sort((a, b) => Math.abs(getChangeRate(b)) - Math.abs(getChangeRate(a)));

  const container = document.getElementById('anomaly-list-container');
  if (!container) return;

  const showCount = 20;
  const renderList = (items) => {
    let html = `<table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead><tr style="border-bottom:2px solid var(--border)">
        <th style="text-align:left;padding:6px 8px">사업명</th>
        <th style="text-align:left;padding:6px 4px">부처</th>
        <th style="text-align:right;padding:6px 4px">2025</th>
        <th style="text-align:right;padding:6px 4px">2026</th>
        <th style="text-align:right;padding:6px 8px">증감률</th>
      </tr></thead><tbody>`;
    items.forEach(p => {
      const cr = getChangeRate(p);
      const color = cr > 0 ? 'var(--green)' : 'var(--red)';
      html += `<tr style="border-bottom:1px solid var(--border)">
        <td style="padding:5px 8px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${(p.name || '').replace(/"/g, '&quot;')}">${p.name || p.project_name}</td>
        <td style="padding:5px 4px;white-space:nowrap;color:var(--text-secondary)">${p.department}</td>
        <td style="padding:5px 4px;text-align:right">${formatBillion(getBudgetPrev(p))}</td>
        <td style="padding:5px 4px;text-align:right">${formatBillion(getBudgetBase(p))}</td>
        <td style="padding:5px 8px;text-align:right;font-weight:700;color:${color}">${formatRate(cr, p)}</td>
      </tr>`;
    });
    html += '</tbody></table>';
    return html;
  };

  let expanded = false;
  container.innerHTML = renderList(anomalies.slice(0, showCount));
  if (anomalies.length > showCount) {
    const btnDiv = document.createElement('div');
    btnDiv.style.cssText = 'text-align:center;padding:8px';
    const btn = document.createElement('button');
    btn.textContent = `더보기 (${anomalies.length - showCount}개 더)`;
    btn.style.cssText = 'background:var(--bg-tertiary);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);padding:6px 16px;cursor:pointer;font-size:12px';
    btn.addEventListener('click', () => {
      expanded = !expanded;
      container.innerHTML = renderList(expanded ? anomalies : anomalies.slice(0, showCount));
      btn.textContent = expanded ? '접기' : `더보기 (${anomalies.length - showCount}개 더)`;
      container.appendChild(btnDiv);
    });
    btnDiv.appendChild(btn);
    container.appendChild(btnDiv);
  }

  // Anomaly histogram
  const canvas = document.getElementById('chart-anomaly-hist');
  if (!canvas) return;
  if (chartInstances['chart-anomaly-hist']) chartInstances['chart-anomaly-hist'].destroy();

  const bins = [
    { label: '-100~-80%', min: -Infinity, max: -80 },
    { label: '-80~-50%', min: -80, max: -50 },
    { label: '-50~-20%', min: -50, max: -20 },
    { label: '-20~0%', min: -20, max: 0 },
    { label: '0~20%', min: 0, max: 20 },
    { label: '20~50%', min: 20, max: 50 },
    { label: '50~80%', min: 50, max: 80 },
    { label: '80~100%', min: 80, max: 100 },
    { label: '100%+', min: 100, max: Infinity }
  ];
  const counts = bins.map(b => projects.filter(p => {
    const cr = getChangeRate(p);
    return cr > b.min && cr <= b.max;
  }).length);
  const bgColors = bins.map(b => {
    if (b.max <= -50) return '#ef4444';
    if (b.max <= 0) return '#f87171';
    if (b.max <= 50) return '#60a5fa';
    return '#f59e0b';
  });

  chartInstances['chart-anomaly-hist'] = new Chart(canvas, {
    type: 'bar',
    data: { labels: bins.map(b => b.label), datasets: [{ data: counts, backgroundColor: bgColors, borderRadius: 3 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw + '개 사업' } } },
      scales: {
        x: { ticks: { color: getChartLabelColor(), font: { size: 10 }, maxRotation: 45 }, grid: { display: false } },
        y: { ticks: { color: getChartLabelColor() }, grid: { color: 'var(--chart-grid)' }, title: { display: true, text: '사업 수', color: getChartLabelColor() } }
      }
    }
  });
}

// ==================== 예산 집중도 (HHI) ====================
function renderHHIAnalysis(projects) {
  const totalBudget = projects.reduce((s, p) => s + getBudgetBase(p), 0);
  if (totalBudget <= 0) return;

  const deptBudget = {};
  projects.forEach(p => { deptBudget[p.department] = (deptBudget[p.department] || 0) + getBudgetBase(p); });
  const deptShares = Object.values(deptBudget).map(v => v / totalBudget);
  const deptHHI = Math.round(deptShares.reduce((s, sh) => s + sh * sh, 0) * 10000);

  const fieldBudget = {};
  projects.forEach(p => { const f = p.field || '미분류'; fieldBudget[f] = (fieldBudget[f] || 0) + getBudgetBase(p); });
  const fieldShares = Object.values(fieldBudget).map(v => v / totalBudget);
  const fieldHHI = Math.round(fieldShares.reduce((s, sh) => s + sh * sh, 0) * 10000);

  function hhiLabel(hhi) {
    if (hhi < 1500) return { text: '분산형', color: 'var(--green)' };
    if (hhi <= 2500) return { text: '중간집중', color: 'var(--yellow)' };
    return { text: '고집중', color: 'var(--red)' };
  }

  const deptInfo = hhiLabel(deptHHI);
  const hhiContainer = document.getElementById('hhi-container');
  if (hhiContainer) {
    hhiContainer.innerHTML = `<div style="text-align:center;padding:12px 0 8px">
      <div style="font-size:28px;font-weight:800;color:${deptInfo.color}">${formatNumber(deptHHI)}</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">HHI (부처별) &mdash; <span style="color:${deptInfo.color};font-weight:600">${deptInfo.text}</span></div>
    </div>`;
  }

  const fieldInfo = hhiLabel(fieldHHI);
  const hhiFieldContainer = document.getElementById('hhi-field-container');
  if (hhiFieldContainer) {
    hhiFieldContainer.innerHTML = `<div style="text-align:center;padding:12px 0 8px">
      <div style="font-size:28px;font-weight:800;color:${fieldInfo.color}">${formatNumber(fieldHHI)}</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">HHI (분야별) &mdash; <span style="color:${fieldInfo.color};font-weight:600">${fieldInfo.text}</span></div>
    </div>`;
  }

  // Top 5 departments horizontal bar
  const deptSorted = Object.entries(deptBudget).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const canvas1 = document.getElementById('chart-hhi-dept');
  if (canvas1) {
    if (chartInstances['chart-hhi-dept']) chartInstances['chart-hhi-dept'].destroy();
    chartInstances['chart-hhi-dept'] = new Chart(canvas1, {
      type: 'bar',
      data: {
        labels: deptSorted.map(d => d[0].length > 8 ? d[0].slice(0, 8) + '..' : d[0]),
        datasets: [{ data: deptSorted.map(d => +(d[1] / totalBudget * 100).toFixed(1)), backgroundColor: COLORS.slice(0, 5), borderRadius: 3 }]
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw + '% (' + formatBillion(deptSorted[ctx.dataIndex][1]) + ')' } } },
        scales: {
          x: { ticks: { color: getChartLabelColor(), callback: v => v + '%' }, grid: { color: 'var(--chart-grid)' } },
          y: { ticks: { color: getChartLabelColor(), font: { size: 11 } }, grid: { display: false } }
        }
      }
    });
  }

  // Top 5 fields horizontal bar
  const fieldSorted = Object.entries(fieldBudget).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const canvas2 = document.getElementById('chart-hhi-field');
  if (canvas2) {
    if (chartInstances['chart-hhi-field']) chartInstances['chart-hhi-field'].destroy();
    chartInstances['chart-hhi-field'] = new Chart(canvas2, {
      type: 'bar',
      data: {
        labels: fieldSorted.map(d => d[0].length > 10 ? d[0].slice(0, 10) + '..' : d[0]),
        datasets: [{ data: fieldSorted.map(d => +(d[1] / totalBudget * 100).toFixed(1)), backgroundColor: COLORS.slice(0, 5), borderRadius: 3 }]
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw + '% (' + formatBillion(fieldSorted[ctx.dataIndex][1]) + ')' } } },
        scales: {
          x: { ticks: { color: getChartLabelColor(), callback: v => v + '%' }, grid: { color: 'var(--chart-grid)' } },
          y: { ticks: { color: getChartLabelColor(), font: { size: 11 } }, grid: { display: false } }
        }
      }
    });
  }
}

// ==================== 사업 규모 분포 분석 ====================
function renderBudgetDistDetail(projects) {
  const budgets = projects.map(p => getBudgetBase(p)).filter(b => b > 0);
  if (budgets.length === 0) return;

  const sorted = [...budgets].sort((a, b) => a - b);
  const mean = budgets.reduce((s, v) => s + v, 0) / budgets.length;
  const median = sorted.length % 2 === 0 ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2 : sorted[Math.floor(sorted.length / 2)];
  const variance = budgets.reduce((s, v) => s + (v - mean) ** 2, 0) / budgets.length;
  const stddev = Math.sqrt(variance);

  const statsEl = document.getElementById('budget-dist-stats');
  if (statsEl) {
    statsEl.innerHTML = `<div style="display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--text-secondary);padding:4px 0">
      <span>평균: <strong style="color:var(--text-primary)">${formatBillion(mean)}</strong></span>
      <span>중앙값: <strong style="color:var(--text-primary)">${formatBillion(median)}</strong></span>
      <span>표준편차: <strong style="color:var(--text-primary)">${formatBillion(stddev)}</strong></span>
    </div>`;
  }

  // Bins in 백만원: 10억=1000, 50억=5000, 100억=10000, 500억=50000, 1000억=100000
  const bins = [
    { label: '0~10억', min: 0, max: 1000 },
    { label: '10~50억', min: 1000, max: 5000 },
    { label: '50~100억', min: 5000, max: 10000 },
    { label: '100~500억', min: 10000, max: 50000 },
    { label: '500~1000억', min: 50000, max: 100000 },
    { label: '1000억+', min: 100000, max: Infinity }
  ];

  const binData = bins.map(b => {
    const items = budgets.filter(v => v >= b.min && v < b.max);
    return { count: items.length, total: items.reduce((s, v) => s + v, 0) };
  });

  const canvas = document.getElementById('chart-budget-dist-detail');
  if (!canvas) return;
  if (chartInstances['chart-budget-dist-detail']) chartInstances['chart-budget-dist-detail'].destroy();

  chartInstances['chart-budget-dist-detail'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: bins.map(b => b.label),
      datasets: [
        { label: '사업 수', data: binData.map(d => d.count), backgroundColor: '#60a5fa', borderRadius: 3, yAxisID: 'y' },
        { label: '총 예산', data: binData.map(d => d.total / 100), backgroundColor: '#f59e0b44', borderColor: '#f59e0b', borderWidth: 1, borderRadius: 3, yAxisID: 'y1' }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: getChartLabelColor(), font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + (ctx.datasetIndex === 0 ? ctx.raw + '개' : formatBillion(ctx.raw * 100)) } }
      },
      scales: {
        x: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } },
        y: { position: 'left', ticks: { color: getChartLabelColor() }, grid: { color: 'var(--chart-grid)' }, title: { display: true, text: '사업 수', color: getChartLabelColor() } },
        y1: { position: 'right', ticks: { color: '#f59e0b', callback: v => formatBillion(v * 100) }, grid: { display: false }, title: { display: true, text: '총 예산', color: '#f59e0b' } }
      }
    }
  });
}

// ==================== Waste Risk Scoring ====================
function getDuplicateProjectIds() {
  const ids = new Set();
  const dups = DATA?.analysis?.duplicates || [];
  dups.forEach(g => {
    (g.projects || []).forEach(p => { if (p.id != null) ids.add(p.id); });
  });
  if (ids.size === 0 && DATA) {
    const dupNames = new Set();
    dups.forEach(g => (g.projects || []).forEach(p => dupNames.add(p.name)));
    DATA.projects.forEach(p => {
      if (dupNames.has(p.project_name || p.name)) ids.add(p.id);
    });
  }
  return ids;
}

function calcWasteRiskScore(project, duplicateProjectIds) {
  if (!duplicateProjectIds) duplicateProjectIds = getDuplicateProjectIds();
  let score = 0;
  if (duplicateProjectIds.has(project.id)) score += 30;
  const rate = Math.abs(getChangeRate(project) || 0);
  if (rate >= 100) score += 40;
  else if (rate >= 50) score += 25;
  else if (rate >= 30) score += 10;
  const isNew = project.status === '신규' || formatRate(getChangeRate(project), project) === '순증';
  const isLarge = getBudgetBase(project) >= 10000;
  if (isNew && isLarge) score += 20;
  else if (isNew) score += 10;
  if (!getBudgetBase(project) || getBudgetBase(project) === 0) score += 10;
  return Math.min(score, 100);
}

function getWasteRiskGrade(score) {
  if (score >= 60) return { label: '높음', color: 'var(--red)', bg: 'var(--red-dim)' };
  if (score >= 30) return { label: '중간', color: 'var(--yellow)', bg: 'var(--yellow-dim)' };
  return { label: '낮음', color: 'var(--green)', bg: 'var(--green-dim)' };
}

let wasteRiskSortCol = 'score';
let wasteRiskSortAsc = false;

function renderWasteRisk(projects) {
  const container = document.getElementById('waste-risk-container');
  if (!container) return;

  const dupIds = getDuplicateProjectIds();
  const scored = projects.map(p => ({
    project: p,
    score: calcWasteRiskScore(p, dupIds),
    grade: null
  }));
  scored.forEach(s => s.grade = getWasteRiskGrade(s.score));

  const high = scored.filter(s => s.score >= 60);
  const mid = scored.filter(s => s.score >= 30 && s.score < 60);
  const low = scored.filter(s => s.score < 30);

  const deptScores = {};
  scored.forEach(s => {
    const d = s.project.department;
    if (!deptScores[d]) deptScores[d] = { total: 0, count: 0 };
    deptScores[d].total += s.score;
    deptScores[d].count++;
  });
  const deptAvg = Object.entries(deptScores)
    .map(([d, v]) => ({ dept: d, avg: Math.round(v.total / v.count * 10) / 10 }))
    .sort((a, b) => b.avg - a.avg)
    .slice(0, 15);

  let html = `
    <div class="kpi-grid" style="margin-bottom:16px">
      <div class="kpi-card">
        <div class="icon" style="background:var(--red-dim);color:var(--red)">!</div>
        <div class="value" style="color:var(--red)">${high.length}</div>
        <div class="label">고위험 사업 (60+)</div>
        <div class="change negative">${formatBillion(high.reduce((s, h) => s + getBudgetBase(h.project), 0))}</div>
      </div>
      <div class="kpi-card">
        <div class="icon" style="background:var(--yellow-dim);color:var(--yellow)">&#9888;</div>
        <div class="value" style="color:var(--yellow)">${mid.length}</div>
        <div class="label">중위험 사업 (30-60)</div>
        <div class="change" style="color:var(--yellow)">${formatBillion(mid.reduce((s, m) => s + getBudgetBase(m.project), 0))}</div>
      </div>
    </div>
    <div class="card" style="padding:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <h3 style="font-size:14px">부처별 평균 위험도 (Top 15)</h3>
      </div>
      <div style="height:250px"><canvas id="chart-waste-dept-avg"></canvas></div>
    </div>
    <div class="table-container" style="margin-top:16px">
      <table class="data-table">
        <thead><tr>
          <th>사업명</th><th>부처</th><th style="text-align:right">위험점수</th><th>등급</th>
        </tr></thead>
        <tbody>
          ${scored.sort((a, b) => b.score - a.score).slice(0, 50).map(s => `
            <tr onclick="showProjectModal(${s.project.id})">
              <td>${s.project.project_name || s.project.name}</td>
              <td>${s.project.department}</td>
              <td style="text-align:right;font-weight:700;color:${s.grade.color}">${s.score}</td>
              <td><span class="tag" style="background:${s.grade.bg};color:${s.grade.color}">${s.grade.label}</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>`;

  container.innerHTML = html;

  // Render Dept Avg Chart
  const canvas = document.getElementById('chart-waste-dept-avg');
  if (canvas) {
    destroyChart('chart-waste-dept-avg');
    chartInstances['chart-waste-dept-avg'] = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: deptAvg.map(d => d.dept),
        datasets: [{ data: deptAvg.map(d => d.avg), backgroundColor: '#f8717199', borderRadius: 4 }]
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { max: 100, ticks: { color: getChartLabelColor() }, grid: { color: 'var(--chart-grid)' } },
          y: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } }
        }
      }
    });
  }
}

// Global scope initialization
window.calcWasteRiskScore = calcWasteRiskScore;
window.getWasteRiskGrade = getWasteRiskGrade;
window.renderWasteRisk = renderWasteRisk;
window.getDuplicateProjectIds = getDuplicateProjectIds;


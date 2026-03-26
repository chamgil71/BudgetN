/**
 * KAIB2026 Cross-Compare Feature Logic
 */

function toggleCompare(id, checkbox) {
  if (checkbox.checked) {
    if (compareSet.size >= 4) {
      checkbox.checked = false;
      alert('최대 4개까지 비교할 수 있습니다.');
      return;
    }
    compareSet.add(id);
  } else {
    compareSet.delete(id);
  }
  updateCompareToolbar();
}

function updateCompareToolbar() {
  const toolbar = document.getElementById('compare-toolbar');
  const countEl = document.getElementById('compare-count');
  const btnEl = document.getElementById('btn-compare');
  if (!toolbar) return;

  const n = compareSet.size;
  if (n > 0) {
    toolbar.classList.add('visible');
    if (countEl) countEl.textContent = `${n}개 선택`;
    if (btnEl) btnEl.disabled = n < 2;
  } else {
    toolbar.classList.remove('visible');
  }
}

function clearCompareSelection() {
  compareSet.clear();
  document.querySelectorAll('.compare-cb').forEach(cb => cb.checked = false);
  updateCompareToolbar();
}

function openCompareModal() {
  if (compareSet.size < 2 || !DATA) return;
  const projects = [...compareSet].map(id => DATA.projects.find(p => p.id === id)).filter(Boolean);

  let html = `<div class="modal-header">
    <h2>사업 비교 (${projects.length}개)</h2>
    <button class="modal-close" onclick="closeCompareModal()">&times;</button>
  </div>
  <div class="compare-cards">`;

  projects.forEach(p => {
    const b = p.budget || {};
    const fields = classifyProject(p);
    const subs = p.sub_projects || [];
    const cr = b.change_rate;

    html += `<div class="compare-card">
      <h3>${p.project_name || p.name}</h3>
      <div class="dept">${p.department}</div>
      <div class="compare-row"><span class="label">유형</span><span class="value"><span class="tag ${getProjectTypeClass(p)}">${getProjectType(p)}</span></span></div>
      <div class="compare-row"><span class="label">분야</span><span class="value">${fields.join(', ')}</span></div>
      <div class="compare-row"><span class="label">상태</span><span class="value">${p.status || '-'}</span></div>
      <div class="compare-row"><span class="label">2024 결산</span><span class="value">${formatBillion(b['2024_settlement'])}</span></div>
      <div class="compare-row"><span class="label">2025 본예산</span><span class="value">${formatBillion(b['2025_original'])}</span></div>
      <div class="compare-row"><span class="label">2026 확정</span><span class="value" style="color:var(--accent);font-weight:700">${formatBillion(b['2026_budget'])}</span></div>
      <div class="compare-row"><span class="label">증감률</span><span class="value" style="color:${(cr || 0) >= 0 ? 'var(--green)' : 'var(--red)'}">${formatRate(cr, p)}</span></div>
      ${p.purpose ? `<div style="margin-top:10px;font-size:12px;color:var(--text-secondary);border-top:1px solid var(--border);padding-top:8px"><strong style="color:var(--text-primary)">사업목적</strong><br>${p.purpose.substring(0, 200)}${p.purpose.length > 200 ? '...' : ''}</div>` : ''}
      ${subs.length > 0 ? `<div class="sub-list" style="border-top:1px solid var(--border);padding-top:8px;margin-top:8px">
        <strong style="font-size:12px;color:var(--text-primary)">내역사업 (${subs.length}건)</strong>
        ${subs.slice(0, 8).map(sp => `<div class="sub-item"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:65%" title="${sp.name}">${sp.name}</span><span style="white-space:nowrap;color:var(--accent)">${formatBillion(sp.budget_base)}</span></div>`).join('')}
        ${subs.length > 8 ? `<div style="text-align:center;color:var(--text-muted);font-size:11px;padding-top:4px">외 ${subs.length - 8}건</div>` : ''}
      </div>` : ''}
    </div>`;
  });

  html += '</div>';
  const contentEl = document.getElementById('compare-modal-content');
  const modalEl = document.getElementById('compare-modal');
  if (contentEl) contentEl.innerHTML = html;
  if (modalEl) {
    modalEl.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeCompareModal() {
  const modalEl = document.getElementById('compare-modal');
  if (modalEl) {
    modalEl.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Global scope initialization
window.toggleCompare = toggleCompare;
window.updateCompareToolbar = updateCompareToolbar;
window.clearCompareSelection = clearCompareSelection;
window.openCompareModal = openCompareModal;
window.closeCompareModal = closeCompareModal;

document.getElementById('compare-modal')?.addEventListener('click', function (e) {
  if (e.target === this) closeCompareModal();
});

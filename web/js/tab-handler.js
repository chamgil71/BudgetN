/**
 * KAIB2026 Tab & Navigation Logic
 */

function switchToTab(tabId, pushState = true) {
    if (!tabId || tabId === currentTab) return;

    // Remove active class from all tabs & buttons
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-item, .tab-btn').forEach(b => b.classList.remove('active'));

    // Apply active class to selected tab & buttons
    const selectedTab = document.getElementById('tab-' + tabId);
    if (selectedTab) selectedTab.classList.add('active');

    // Handle .nav-item (top) and .tab-btn (middle)
    const buttons = document.querySelectorAll(`.nav-item[onclick*="switchToTab('${tabId}')"], .tab-btn[data-tab="${tabId}"]`);
    buttons.forEach(b => {
        b.classList.add('active');
        if (b.classList.contains('tab-btn')) b.setAttribute('aria-selected', 'true');
    });

    // Reset others
    document.querySelectorAll('.tab-btn').forEach(b => {
        if (b.dataset.tab !== tabId) b.setAttribute('aria-selected', 'false');
    });

    currentTab = tabId;

    // Render tab-specific content if needed
    if (window.DATA) {
        if (tabId === 'overview') { if (typeof window.renderOverview === 'function') window.renderOverview(); }
        else if (tabId === 'department') { if (typeof window.renderDepartment === 'function') window.renderDepartment(); }
        else if (tabId === 'field') { if (typeof window.renderField === 'function') window.renderField(); }
        else if (tabId === 'collab') { if (typeof window.renderCollab === 'function') window.renderCollab(); }
        else if (tabId === 'projects') { if (typeof window.renderProjects === 'function') window.renderProjects(); }
        else if (tabId === 'flow') { if (typeof window.renderFlow === 'function') window.renderFlow(); }
        else if (tabId === 'duplicate') { if (typeof window.renderDuplicate === 'function') window.renderDuplicate(); }
        else if (tabId === 'policy') { if (typeof window.initPolicyClusterTab === 'function') window.initPolicyClusterTab(window.DATA); }
        else if (tabId === 'future') { if (typeof window.initFutureSimTab === 'function') window.initFutureSimTab(window.DATA); }
        else if (tabId === 'insight') { if (typeof window.initBudgetInsightTab === 'function') window.initBudgetInsightTab(window.DATA); }
        else if (tabId === 'ai-tech') { if (typeof window.initAiTechTab === 'function') window.initAiTechTab(window.DATA); }
        else if (tabId === 'cross-compare') { if (typeof window.updateCompareToolbar === 'function') window.updateCompareToolbar(); }
    }

    if (pushState) {
        history.pushState({ tab: tabId }, '', '#' + tabId);
    }
}

// ==================== Projects Tab Handler ====================

window.renderProjects = function () {
    if (!DATA) return;

    // Field & AI Tech filters already populated in renderOverview if not done here
    // But for modularity, we check/populate if select is empty
    const fieldSel = document.getElementById('project-field-filter');
    if (fieldSel && fieldSel.options.length <= 1) {
        const fieldSet = new Set();
        DATA.projects.forEach(p => classifyProject(p).forEach(f => fieldSet.add(f)));
        [...fieldSet].sort().forEach(f => {
            const opt = document.createElement('option');
            opt.value = f; opt.textContent = f;
            fieldSel.appendChild(opt);
        });
    }

    const techSel = document.getElementById('project-tech-filter');
    if (techSel && techSel.options.length <= 1) {
        const techSet = new Set();
        DATA.projects.forEach(p => (p.ai_tech || []).forEach(t => techSet.add(t)));
        [...techSet].sort().forEach(t => {
            const opt = document.createElement('option');
            opt.value = t; opt.textContent = t;
            techSel.appendChild(opt);
        });
    }

    updateProjectList();

    // Event listeners for filters (if not already set in HTML inline)
    // Here we'll rely on the updateProjectList call
}

function updateProjectList() {
    const container = document.getElementById('project-list-container');
    const searchTerm = document.getElementById('project-search')?.value || '';
    window.vsScrollTop = 0;

    if (window.listMode === 'sub') {
        window.renderSubProjectList(container, searchTerm);
    } else {
        window.renderProjectGroupList(container, searchTerm);
    }
}

window.getFilteredProjects = function () {
    const filtered = window.filterProjects();
    let rows = window.buildFlatRows(filtered);
    const nameOnly = document.getElementById('search-name-only')?.checked;
    const search = (document.getElementById('project-search')?.value || '').toLowerCase();
    if (nameOnly && search) {
        const expr = window.parseSearchExpr(search);
        if (expr) {
            rows = rows.filter(r => {
                const text = [r.project_name, r.sub_name || ''].join(' ').toLowerCase();
                return window.matchSearchExpr(expr, text);
            });
        }
    }
    return window.sortRows(rows);
};

window.getFilteredProjectsGrouped = function () {
    const filtered = window.filterProjects();
    let projectRows = filtered.map(p => ({
        _project: p,
        project_name: p.project_name || p.name,
        sub_name: '',
        department: p.department,
        managing_dept: p.division || '-',
        impl_agency: p.implementing_agency || '-',
        sub_budget: null,
        budget_base: window.getBudgetBase(p),
        change_rate: window.getChangeRate(p),
        type: window.getProjectType(p),
        status: p.status || '-',
        id: p.id
    }));
    return window.sortRows(projectRows);
};

window.buildFlatRows = function (projects) {
    const rows = [];
    projects.forEach(p => {
        const subs = p.sub_projects || [];
        const managers = p.project_managers || [];
        if (subs.length === 0 && managers.length === 0) {
            rows.push({
                _project: p,
                project_name: p.project_name || p.name,
                sub_name: '-',
                department: p.department,
                managing_dept: p.division || '-',
                impl_agency: p.implementing_agency || '-',
                sub_budget: null,
                budget_base: window.getBudgetBase(p),
                change_rate: window.getChangeRate(p),
                type: window.getProjectType(p),
                status: p.status || '-',
                id: p.id
            });
        } else {
            const items = subs.length > 0 ? subs : managers;
            items.forEach((item, idx) => {
                const mgr = (managers[idx] || managers[0] || {});
                rows.push({
                    _project: p,
                    project_name: p.project_name || p.name,
                    sub_name: item.name || item.sub_project || '-',
                    department: p.department,
                    managing_dept: mgr.managing_dept || p.division || '-',
                    impl_agency: mgr.implementing_agency || p.implementing_agency || '-',
                    sub_budget: item.budget_base || null,
                    budget_base: window.getBudgetBase(p),
                    change_rate: window.getChangeRate(p),
                    type: window.getProjectType(p),
                    status: p.status || '-',
                    id: p.id
                });
            });
        }
    });
    return rows;
};

window.filterProjects = function () {
    if (!window.DATA) return [];
    const searchRaw = (document.getElementById('project-search')?.value || '').trim();
    const dept = document.getElementById('project-dept-filter')?.value || '';
    const type = document.getElementById('project-type-filter')?.value || '';
    const field = document.getElementById('project-field-filter')?.value || '';
    const tech = document.getElementById('project-tech-filter')?.value || '';
    const nameOnly = document.getElementById('search-name-only')?.checked;

    const expr = window.parseSearchExpr(searchRaw);

    return window.DATA.projects.filter(p => {
        if (dept && p.department !== dept) return false;
        if (type && window.getProjectType(p) !== type) return false;
        if (field && !window.classifyProject(p).includes(field)) return false;
        if (tech && !(p.ai_tech || []).includes(tech)) return false;

        if (expr) {
            if (nameOnly) {
                // Name-only filter is handled in getFilteredProjects for flat rows
                // But we still need a basic check here for grouped mode
                const nameText = [p.project_name, p.name].join(' ').toLowerCase();
                if (!window.matchSearchExpr(expr, nameText)) return false;
            } else {
                const fullText = [
                    p.project_name, p.name, p.department, p.division, p.implementing_agency,
                    p.purpose, p.description, p.legal_basis,
                    ...(p.keywords || []), ...(p.ai_domains || []), ...(p.ai_tech || [])
                ].join(' ').toLowerCase();
                if (!window.matchSearchExpr(expr, fullText)) return false;
            }
        }
        return true;
    });
};

window.sortRows = function (rows) {
    const key = window.columnSort.key;
    const dir = window.columnSort.dir === 'asc' ? 1 : -1;

    switch (key) {
        case 'code': rows.sort((a, b) => dir * (a._project.code || '').localeCompare(b._project.code || '')); break;
        case 'name': rows.sort((a, b) => dir * a.project_name.localeCompare(b.project_name)); break;
        case 'sub_name': rows.sort((a, b) => dir * a.sub_name.localeCompare(b.sub_name)); break;
        case 'department': rows.sort((a, b) => dir * a.department.localeCompare(b.department)); break;
        case 'managing_dept': rows.sort((a, b) => dir * a.managing_dept.localeCompare(b.managing_dept)); break;
        case 'impl_agency': rows.sort((a, b) => dir * a.impl_agency.localeCompare(b.impl_agency)); break;
        case 'sub_budget': rows.sort((a, b) => dir * ((a.sub_budget || 0) - (b.sub_budget || 0))); break;
        case 'budget': rows.sort((a, b) => dir * (a.budget_base - b.budget_base)); break;
        case 'change': rows.sort((a, b) => dir * (a.change_rate - b.change_rate)); break;
        case 'type': rows.sort((a, b) => dir * a.type.localeCompare(b.type)); break;
        case 'status': rows.sort((a, b) => dir * a.status.localeCompare(b.status)); break;
        case 'period': rows.sort((a, b) => dir * ((a._project.project_period?.start_year || 0) - (b._project.project_period?.start_year || 0))); break;
        default: rows.sort((a, b) => b.budget_base - a.budget_base);
    }
    return rows;
};

window.renderSubProjectList = function (container, searchTerm) {
    const rows = window.getFilteredProjects();
    const total = rows.length;
    const budgetSum = [...new Map(rows.map(r => [r.id, r.budget_base])).values()].reduce((s, v) => s + v, 0);

    const countEl = document.getElementById('project-count');
    if (countEl) countEl.innerHTML = `총 ${window.formatNumber(total)}건 · 예산 합계 ${window.formatBillion(budgetSum)}`;

    if (window.currentView === 'table') {
        const thStyle = 'cursor:pointer;user-select:none;white-space:nowrap;font-size:12px';
        let html = `<table class="data-table" style="font-size:13px"><thead><tr>
          <th style="width:32px;text-align:center">비교</th>
          <th style="${thStyle}" onclick="window.sortByColumn('code')">코드${window.getSortIndicator('code')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('name')">사업명${window.getSortIndicator('name')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('sub_name')">내역사업명${window.getSortIndicator('sub_name')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('department')">부처${window.getSortIndicator('department')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('budget')">예산${window.getSortIndicator('budget')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('change')">증감${window.getSortIndicator('change')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('status')">상태${window.getSortIndicator('status')}</th>
        </tr></thead><tbody>`;

        rows.forEach(r => {
            const p = r._project;
            const checked = window.compareSet.has(r.id) ? 'checked' : '';
            html += `<tr style="cursor:pointer" onclick="window.showProjectModal(${r.id})">
            <td style="text-align:center" onclick="event.stopPropagation()"><input type="checkbox" class="compare-cb" data-id="${r.id}" ${checked} onclick="window.toggleCompare(${r.id}, this)"></td>
            <td style="font-family:monospace;font-size:11px">${window.highlightText(p.code || '-', searchTerm)}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${window.highlightText(r.project_name, searchTerm)}</td>
            <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${window.highlightText(r.sub_name, searchTerm)}</td>
            <td>${window.highlightText(r.department, searchTerm)}</td>
            <td class="num">${window.formatBillion(r.budget_base)}</td>
            <td class="num ${r.change_rate >= 0 ? 'text-positive' : 'text-negative'}">${window.formatRate(r.change_rate, p)}</td>
            <td>${r.status}</td>
          </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } else {
        window.renderCardView(container, rows, searchTerm);
    }
};

window.renderProjectGroupList = function (container, searchTerm) {
    const rows = window.getFilteredProjectsGrouped();
    const total = rows.length;
    const budgetSum = rows.reduce((s, r) => s + r.budget_base, 0);

    const countEl = document.getElementById('project-count');
    if (countEl) countEl.innerHTML = `총 ${window.formatNumber(total)}개 사업 · 예산 합계 ${window.formatBillion(budgetSum)}`;

    if (window.currentView === 'table') {
        const thStyle = 'cursor:pointer;user-select:none;white-space:nowrap;font-size:12px';
        let html = `<table class="data-table" style="font-size:13px"><thead><tr>
          <th style="width:32px;text-align:center">비교</th>
          <th style="${thStyle}" onclick="window.sortByColumn('name')">사업명${window.getSortIndicator('name')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('department')">부처${window.getSortIndicator('department')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('budget')">예산${window.getSortIndicator('budget')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('change')">증감${window.getSortIndicator('change')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('type')">유형${window.getSortIndicator('type')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('status')">상태${window.getSortIndicator('status')}</th>
        </tr></thead><tbody>`;

        rows.forEach(r => {
            const p = r._project;
            const checked = window.compareSet.has(r.id) ? 'checked' : '';
            html += `<tr style="cursor:pointer" onclick="window.showProjectModal(${r.id})">
            <td style="text-align:center" onclick="event.stopPropagation()"><input type="checkbox" class="compare-cb" data-id="${r.id}" ${checked} onclick="window.toggleCompare(${r.id}, this)"></td>
            <td style="font-weight:600">${window.highlightText(r.project_name, searchTerm)}</td>
            <td>${window.highlightText(r.department, searchTerm)}</td>
            <td class="num" style="font-weight:600">${window.formatBillion(r.budget_base)}</td>
            <td class="num ${r.change_rate >= 0 ? 'text-positive' : 'text-negative'}">${window.formatRate(r.change_rate, p)}</td>
            <td><span class="badge badge-${window.getProjectTypeClass(p)}">${r.type}</span></td>
            <td>${r.status}</td>
          </tr>`;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } else {
        window.renderCardView(container, rows, searchTerm);
    }
};

window.renderCardView = function (container, rows, searchTerm) {
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px">';
    rows.forEach(r => {
        const p = r._project;
        const checked = window.compareSet.has(r.id) ? 'checked' : '';
        html += `<div class="card" style="cursor:pointer;position:relative" onclick="window.showProjectModal(${r.id})">
        <div style="position:absolute;top:12px;right:12px" onclick="event.stopPropagation()"><input type="checkbox" class="compare-cb" data-id="${r.id}" ${checked} onclick="window.toggleCompare(${r.id}, this)"></div>
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;padding-right:24px">
          <span class="badge badge-${window.getProjectTypeClass(p)}">${r.type}</span>
          <span style="font-size:12px;color:var(--text-muted)">${r.status}</span>
        </div>
        <div style="font-size:14px;font-weight:600;margin-bottom:4px">${window.highlightText(r.project_name, searchTerm)}</div>
        ${r.sub_name && r.sub_name !== '-' ? `<div style="font-size:12px;color:var(--accent);margin-bottom:4px">${window.highlightText(r.sub_name, searchTerm)}</div>` : ''}
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px">${window.highlightText(r.department, searchTerm)}</div>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:18px;font-weight:700">${window.formatBillion(r.budget_base)}</span>
          <span class="change ${r.change_rate >= 0 ? 'positive' : 'negative'}" style="font-size:12px;padding:2px 8px;border-radius:6px;background:${r.change_rate >= 0 ? 'var(--green-dim)' : 'var(--red-dim)'}">
            ${window.formatRate(r.change_rate, p)}
          </span>
        </div>
      </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
};

window.sortByColumn = function (key) {
    if (window.columnSort.key === key) {
        window.columnSort.dir = window.columnSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        window.columnSort = { key, dir: ['name', 'department', 'type', 'status'].includes(key) ? 'asc' : 'desc' };
    }
    window.updateProjectList();
};

window.getSortIndicator = function (key) {
    if (window.columnSort.key !== key) return ' <span style="opacity:0.3">⇅</span>';
    return window.columnSort.dir === 'asc' ? ' ▲' : ' ▼';
};

window.renderSubProjectList = function (container, searchTerm) {
    const rows = window.getFilteredProjects();
    const total = rows.length;
    const budgetSum = [...new Map(rows.map(r => [r.id, r.budget_base])).values()].reduce((s, v) => s + v, 0);

    const countEl = document.getElementById('project-count');
    if (countEl) countEl.innerHTML = `총 ${window.formatNumber(total)}건 · 예산 합계 ${window.formatBillion(budgetSum)}`;

    if (window.currentView === 'table') {
        const thStyle = 'cursor:pointer;user-select:none;white-space:nowrap;font-size:12px';
        let html = `<div class="virtual-scroll-container"><table class="data-table" style="font-size:13px"><thead><tr>
          <th style="width:32px;text-align:center">비교</th>
          <th style="${thStyle}" onclick="window.sortByColumn('code')">코드${window.getSortIndicator('code')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('name')">사업명${window.getSortIndicator('name')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('sub_name')">내역사업명${window.getSortIndicator('sub_name')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('department')">부처${window.getSortIndicator('department')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('budget')">예산${window.getSortIndicator('budget')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('change')">증감${window.getSortIndicator('change')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('status')">상태${window.getSortIndicator('status')}</th>
        </tr></thead><tbody>`;

        rows.forEach(r => {
            const p = r._project;
            const checked = window.compareSet.has(r.id) ? 'checked' : '';
            html += `<tr style="cursor:pointer" onclick="window.showProjectModal(${r.id})">
            <td style="text-align:center" onclick="event.stopPropagation()"><input type="checkbox" class="compare-cb" data-id="${r.id}" ${checked} onclick="window.toggleCompare(${r.id}, this)"></td>
            <td style="font-family:monospace;font-size:11px">${window.highlightText(p.code || '-', searchTerm)}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${window.highlightText(r.project_name, searchTerm)}</td>
            <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${window.highlightText(r.sub_name, searchTerm)}</td>
            <td>${window.highlightText(r.department, searchTerm)}</td>
            <td class="num">${window.formatBillion(r.budget_base)}</td>
            <td class="num ${r.change_rate >= 0 ? 'text-positive' : 'text-negative'}">${window.formatRate(r.change_rate, p)}</td>
            <td>${r.status}</td>
          </tr>`;
        });
        html += '</tbody></table></div>';
        container.innerHTML = html;
        if (typeof window.setupScrollToTop === 'function') window.setupScrollToTop();
    } else {
        window.renderCardView(container, rows, searchTerm);
    }
};

window.renderProjectGroupList = function (container, searchTerm) {
    const rows = window.getFilteredProjectsGrouped();
    const total = rows.length;
    const budgetSum = rows.reduce((s, r) => s + r.budget_base, 0);

    const countEl = document.getElementById('project-count');
    if (countEl) countEl.innerHTML = `총 ${window.formatNumber(total)}개 사업 · 예산 합계 ${window.formatBillion(budgetSum)}`;

    if (window.currentView === 'table') {
        const thStyle = 'cursor:pointer;user-select:none;white-space:nowrap;font-size:12px';
        let html = `<div class="virtual-scroll-container"><table class="data-table" style="font-size:13px"><thead><tr>
          <th style="width:32px;text-align:center">비교</th>
          <th style="${thStyle}" onclick="window.sortByColumn('name')">사업명${window.getSortIndicator('name')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('department')">부처${window.getSortIndicator('department')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('budget')">예산${window.getSortIndicator('budget')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('change')">증감${window.getSortIndicator('change')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('type')">유형${window.getSortIndicator('type')}</th>
          <th style="${thStyle}" onclick="window.sortByColumn('status')">상태${window.getSortIndicator('status')}</th>
        </tr></thead><tbody>`;

        rows.forEach(r => {
            const p = r._project;
            const checked = window.compareSet.has(r.id) ? 'checked' : '';
            html += `<tr style="cursor:pointer" onclick="window.showProjectModal(${r.id})">
            <td style="text-align:center" onclick="event.stopPropagation()"><input type="checkbox" class="compare-cb" data-id="${r.id}" ${checked} onclick="window.toggleCompare(${r.id}, this)"></td>
            <td style="font-weight:600">${window.highlightText(r.project_name, searchTerm)}</td>
            <td>${window.highlightText(r.department, searchTerm)}</td>
            <td class="num" style="font-weight:600">${window.formatBillion(r.budget_base)}</td>
            <td class="num ${r.change_rate >= 0 ? 'text-positive' : 'text-negative'}">${window.formatRate(r.change_rate, p)}</td>
            <td><span class="badge badge-${window.getProjectTypeClass(p)}">${r.type}</span></td>
            <td>${r.status}</td>
          </tr>`;
        });
        html += '</tbody></table></div>';
        container.innerHTML = html;
        if (typeof window.setupScrollToTop === 'function') window.setupScrollToTop();
    } else {
        window.renderCardView(container, rows, searchTerm);
    }
};

window.sortByColumn = function (key) {
    if (window.columnSort.key === key) {
        window.columnSort.dir = window.columnSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        window.columnSort = { key, dir: ['name', 'department', 'type', 'status'].includes(key) ? 'asc' : 'desc' };
    }
    window.updateProjectList();
};

window.getSortIndicator = function (key) {
    if (window.columnSort.key !== key) return ' <span style="opacity:0.3">⇅</span>';
    return window.columnSort.dir === 'asc' ? ' ▲' : ' ▼';
};

function highlightText(text, search) {
    if (!search || !text) return text || '';
    const expr = parseSearchExpr(search);
    const keywords = expr ? getSearchTerms(expr) : [];
    if (keywords.length === 0) return text;
    const escaped = keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const pattern = escaped.join('|');
    return text.replace(new RegExp(`(${pattern})`, 'gi'), '<mark style="background:var(--accent);color:var(--bg-primary);padding:0 2px;border-radius:2px">$1</mark>');
}

// ==================== Project Modal ====================

function showProjectModal(id) {
    const p = DATA.projects.find(x => x.id === id);
    if (!p) return;

    document.getElementById('modal-project-name').textContent = p.project_name || p.name;
    document.getElementById('modal-project-code').textContent = p.code || '-';

    // Quick info
    const infoHtml = `
      <div class="modal-info-item"><strong>부처</strong> ${p.department}</div>
      <div class="modal-info-item"><strong>소관부서</strong> ${p.division || '-'}</div>
      <div class="modal-info-item"><strong>시행주체</strong> ${p.implementing_agency || '-'}</div>
      <div class="modal-info-item"><strong>사업유형</strong> ${getProjectType(p)}</div>
      <div class="modal-info-item"><strong>상태</strong> ${p.status || '-'}</div>
    `;
    document.getElementById('modal-quick-info').innerHTML = infoHtml;

    // Description
    document.getElementById('modal-description').textContent = p.description || p.purpose || '내용 없음';

    // Budget
    const b26 = getBudgetBase(p);
    const b25 = getBudgetPrev(p);
    const cr = getChangeRate(p);
    const budgetHtml = `
      <div style="font-size:24px;font-weight:700">${formatBillion(b26)}</div>
      <div style="font-size:13px;color:var(--text-muted);margin-top:4px">
        전년 ${formatBillion(b25)} 대비 <span class="${cr >= 0 ? 'positive' : 'negative'}">${formatRate(cr, p)}</span>
      </div>
    `;
    document.getElementById('modal-budget-main').innerHTML = budgetHtml;

    // Budget Chart
    renderYearTrend(p);

    // AI Classification
    const domains = p.ai_domains || [];
    const tech = p.ai_tech || [];
    const stage = p.rnd_stage || [];
    document.getElementById('modal-ai-tags').innerHTML = [
        ...domains.map(d => `<span class="tag domain">${d}</span>`),
        ...tech.map(t => `<span class="tag tech">${t}</span>`),
        ...stage.map(s => `<span class="tag stage">${s}</span>`)
    ].join('');

    // Memos
    renderMemos(id);

    // Similar Projects
    const simResult = document.getElementById('similar-projects-result');
    if (simResult) simResult.innerHTML = '버튼을 클릭하면 유사한 사업을 검색합니다.';

    document.getElementById('project-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('project-modal').classList.remove('active');
    document.body.style.overflow = '';
}

// ==================== Collaboration Tab Handler ====================

function renderCollab() {
    if (!DATA || !DATA.analysis || !DATA.analysis.collaboration) return;
    const colRaw = DATA.analysis.collaboration;
    _collabData = colRaw;

    renderCollabKPI(colRaw);
    renderCollabChains(colRaw.collaboration_chains || []);
    renderCollabHubs(colRaw.collaboration_hubs || []);
    filterCollabPairs();
}

function renderCollabKPI(col) {
    document.getElementById('collab-total-pairs').textContent = formatNumber(col.total_pairs || 0);
    document.getElementById('collab-top-score').textContent = (col.top_score || 0).toFixed(1);
    document.getElementById('collab-avg-score').textContent = (col.avg_score || 0).toFixed(1);
    document.getElementById('collab-chain-count').textContent = formatNumber((col.collaboration_chains || []).length);
}

function renderCollabChains(chains) {
    const container = document.getElementById('collab-chains-grid');
    if (!container) return;
    const topChains = chains.sort((a, b) => (b.chain_budget || 0) - (a.chain_budget || 0)).slice(0, 20);
    let html = '';
    topChains.forEach(ch => {
        const budgetStr = formatBillion(ch.chain_budget || 0);
        html += `<div style="background:var(--bg-main);border-radius:8px;padding:14px;border-left:3px solid #8b5cf6">
          <div style="font-weight:600;font-size:13px;margin-bottom:6px">${ch.chain_name}</div>
          <div style="font-size:12px;color:var(--text-secondary);margin-bottom:4px">${ch.departments.join(' \u2192 ')}</div>
          <div style="display:flex;gap:12px;font-size:11px;color:var(--text-muted)">
            <span>${ch.chain_length}단계</span>
            <span>예산 ${budgetStr}</span>
          </div>
          <div style="font-size:11px;color:var(--text-secondary);margin-top:6px;line-height:1.5">${(ch.synergy_scenario || '').slice(0, 150)}...</div>
        </div>`;
    });
    container.innerHTML = html;
}

function renderCollabHubs(hubs) {
    const container = document.getElementById('collab-hubs-grid');
    if (!container) return;
    const sorted = (hubs || []).filter(h => (h.out_degree + h.in_degree) >= 5).sort((a, b) => b.hub_score - a.hub_score).slice(0, 20);
    let html = '';
    sorted.forEach(h => {
        const hp = DATA.projects.find(p => p.id === h.project_id) || {};
        const typeColor = h.hub_type === 'supply_hub' ? '#3b82f6' : '#f59e0b';
        html += `<div style="background:var(--bg-main);border-radius:8px;padding:14px;border-left:3px solid ${typeColor}">
          <div style="font-weight:600;font-size:13px;margin-bottom:4px">${hp.project_name || hp.name || '-'}</div>
          <div style="font-size:12px;color:var(--text-secondary)">${hp.department || '-'}</div>
          ${hp.division ? `<div style="font-size:11px;color:var(--text-muted)">${hp.division}</div>` : ''}
          <div style="display:flex;gap:12px;font-size:11px;color:var(--text-muted);margin-top:6px">
            <span style="color:${typeColor};font-weight:600">${h.hub_type === 'supply_hub' ? '공급 허브' : '수요 허브'}</span>
            <span>연결 ${h.out_degree + h.in_degree}개</span>
            <span>점수 ${h.hub_score}</span>
          </div>
          <div style="font-size:11px;color:var(--text-secondary);margin-top:4px;line-height:1.4">${(h.description || '').slice(0, 120)}...</div>
        </div>`;
    });
    container.innerHTML = html;
}

function filterCollabPairs() {
    if (!_collabData) return;
    const search = document.getElementById('collab-search')?.value?.toLowerCase() || '';
    const type = document.getElementById('collab-type-filter')?.value || '';
    const minScore = parseFloat(document.getElementById('collab-score-filter')?.value || 0);

    const filtered = (_collabData.high_potential_pairs || []).filter(p => {
        if (p.collaboration_score < minScore) return false;
        if (type && p.collaboration_type !== type) return false;
        if (search) {
            const text = [p.project_a.project_name, p.project_b.project_name, p.project_a.department, p.project_b.department, p.rationale].join(' ').toLowerCase();
            if (!text.includes(search)) return false;
        }
        return true;
    });

    const container = document.getElementById('collab-pairs-body');
    if (!container) return;
    let html = '';
    filtered.forEach((p, i) => {
        const scoreColor = p.collaboration_score >= 80 ? '#10b981' : p.collaboration_score >= 60 ? '#3b82f6' : '#f59e0b';
        const tColor = p.collaboration_type === '기술 공유' ? '#3b82f6' : p.collaboration_type === '데이터 연계' ? '#10b981' : '#f59e0b';
        html += `<tr style="border-bottom:1px solid var(--border);cursor:pointer" onclick="showCollabDetail(${i})" onmouseover="this.style.background='var(--bg-main)'" onmouseout="this.style.background=''">
          <td style="padding:6px 8px;color:var(--text-muted)">${i + 1}</td>
          <td style="padding:6px 8px">${p.project_a.project_name}<div style="font-size:11px;color:var(--text-muted)">${p.project_a.department} · ${formatBillion(getBudgetBase(p.project_a))}</div></td>
          <td style="padding:6px 8px">${p.project_b.project_name}<div style="font-size:11px;color:var(--text-muted)">${p.project_b.department} · ${formatBillion(getBudgetBase(p.project_b))}</div></td>
          <td style="padding:6px 8px;text-align:center"><span style="font-weight:700;color:${scoreColor}">${p.collaboration_score}</span></td>
          <td style="padding:6px 8px;text-align:center"><span style="font-size:11px;padding:2px 8px;border-radius:10px;background:${tColor}22;color:${tColor}">${(p.collaboration_type || '').replace('\u2192산업체 활용 연계', '')}</span></td>
          <td style="padding:6px 8px;text-align:center"><button onclick="event.stopPropagation();showCollabDetail(${i})" style="background:var(--accent);color:white;border:none;padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer">보기</button></td>
        </tr>`;
    });
    container.innerHTML = html;
}

function showCollabDetail(idx) {
    const pair = _collabData.high_potential_pairs[idx];
    if (!pair) return;

    const scoreColor = pair.collaboration_score >= 80 ? '#10b981' : pair.collaboration_score >= 60 ? '#3b82f6' : '#f59e0b';
    const sd = pair.score_details || {};
    const a = pair.analysis || {};

    const barHtml = (label, val, max) => `
      <div style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px">
          <span>${label}</span><span>${val}/${max}</span>
        </div>
        <div style="height:4px;background:var(--border);border-radius:2px;overflow:hidden">
          <div style="width:${(val / max * 100)}%;height:100%;background:${scoreColor}"></div>
        </div>
      </div>
    `;

    let html = `
    <div style="text-align:center;margin-bottom:20px">
      <div style="font-size:36px;font-weight:800;color:${scoreColor}">${pair.collaboration_score}</div>
      <div style="font-size:14px;color:var(--text-muted)">${pair.collaboration_level}</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:4px">${pair.pair_id} · ${pair.collaboration_type}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
      <div style="background:var(--bg-main);padding:14px;border-radius:8px;border-left:3px solid #3b82f6">
        <div style="font-size:11px;color:#3b82f6;font-weight:600;margin-bottom:4px">공급 (A)</div>
        <div style="font-weight:600;font-size:14px;margin-bottom:4px">${pair.project_a.project_name}</div>
        <div style="font-size:12px;color:var(--text-secondary)">${pair.project_a.department}</div>
        <div style="font-size:12px;margin-top:4px">예산: <strong>${formatBillion(getBudgetBase(pair.project_a))}</strong></div>
      </div>
      <div style="background:var(--bg-main);padding:14px;border-radius:8px;border-left:3px solid #f59e0b">
        <div style="font-size:11px;color:#f59e0b;font-weight:600;margin-bottom:4px">수요 (B)</div>
        <div style="font-weight:600;font-size:14px;margin-bottom:4px">${pair.project_b.project_name}</div>
        <div style="font-size:12px;color:var(--text-secondary)">${pair.project_b.department}</div>
        <div style="font-size:12px;margin-top:4px">예산: <strong>${formatBillion(getBudgetBase(pair.project_b))}</strong></div>
      </div>
    </div>
    <div style="margin-bottom:20px">
      <div style="font-size:13px;font-weight:600;margin-bottom:8px">협업 점수 구성</div>
      ${barHtml('연계 명확성', sd.linkage_clarity || 0, 3)}
      ${barHtml('도메인 일치', sd.domain_match || 0, 2)}
      ${barHtml('시너지 크기', sd.synergy_size || 0, 3)}
      ${barHtml('대체 불가능성', sd.irreplaceability || 0, 2)}
    </div>
    ${a.synergy_description ? `<div style="margin-bottom:12px;padding:10px;background:var(--bg-main);border-radius:8px">
      <div style="font-size:12px;font-weight:600;margin-bottom:4px">시너지 효과</div>
      <div style="font-size:11px;color:var(--text-secondary);line-height:1.5">${a.synergy_description}</div>
    </div>` : ''}
    <div style="margin-bottom:16px">
      <div style="font-size:13px;font-weight:600;margin-bottom:6px">분석 근거</div>
      <div style="font-size:12px;line-height:1.7;color:var(--text-secondary);padding:12px;background:var(--bg-main);border-radius:8px">${pair.rationale || ''}</div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;margin-bottom:6px">정책 권고</div>
      <div style="font-size:12px;line-height:1.7;color:var(--text-secondary);padding:12px;background:var(--bg-main);border-radius:8px;border-left:3px solid var(--accent)">${pair.recommendation || ''}</div>
    </div>`;

    document.getElementById('collab-modal-content').innerHTML = html;
    document.getElementById('collab-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeCollabModal() {
    document.getElementById('collab-modal').classList.remove('active');
    document.body.style.overflow = '';
}

// ==================== Comparison Feature ====================

function toggleCompare(id, cb) {
    if (cb.checked) {
        if (compareSet.size >= 10) {
            alert('최대 10개 사업까지만 비교 가능합니다.');
            cb.checked = false;
            return;
        }
        compareSet.add(id);
    } else {
        compareSet.delete(id);
    }
    updateCompareToolbar();
}

function updateCompareToolbar() {
    const bar = document.getElementById('compare-toolbar');
    const count = document.getElementById('compare-count');
    if (!bar || !count) return;

    if (compareSet.size > 0) {
        bar.classList.add('active');
        count.textContent = compareSet.size;
    } else {
        bar.classList.remove('active');
    }
}

function clearCompareSelection() {
    compareSet.clear();
    document.querySelectorAll('.compare-cb').forEach(cb => cb.checked = false);
    updateCompareToolbar();
}

function openCompareModal() {
    if (compareSet.size === 0) return;
    const selected = DATA.projects.filter(p => compareSet.has(p.id));

    // Build comparison table
    let html = `<table class="data-table" style="font-size:12px"><thead><tr>
      <th style="min-width:150px">항목</th>
      ${selected.map(p => `<th style="min-width:200px">${p.project_name || p.name}</th>`).join('')}
    </tr></thead><tbody>`;

    const rows = [
        ['부처', p => p.department],
        ['예산 (2026)', p => formatBillion(getBudgetBase(p))],
        ['전년비', p => formatRate(getChangeRate(p), p)],
        ['사업유형', p => getProjectType(p)],
        ['상태', p => p.status],
        ['소관부서', p => p.division || '-'],
        ['시행주체', p => p.implementing_agency || '-'],
        ['주요내용', p => (p.description || p.purpose || '').substring(0, 200) + '...']
    ];

    rows.forEach(([label, fn]) => {
        html += `<tr><td style="font-weight:600;background:var(--bg-secondary)">${label}</td>`;
        selected.forEach(p => {
            html += `<td>${fn(p)}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';

    document.getElementById('compare-modal-body').innerHTML = html;
    document.getElementById('compare-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeCompareModal() {
    document.getElementById('compare-modal').classList.remove('active');
    document.body.style.overflow = '';
}
// ==================== Filtering & Sorting Core ====================

function buildFlatRows(projects) {
    const rows = [];
    projects.forEach(p => {
        const subs = p.sub_projects || [];
        const mgrs = p.project_managers || [];
        if (subs.length > 0) {
            subs.forEach((sp, i) => {
                const mgr = mgrs[i] || mgrs[0] || {};
                rows.push({
                    _project: p,
                    project_name: p.project_name || p.name,
                    sub_name: sp.name,
                    department: p.department,
                    managing_dept: mgr.managing_dept || p.division || '-',
                    impl_agency: mgr.implementing_agency || p.implementing_agency || '-',
                    sub_budget: sp.budget_base,
                    budget_base: getBudgetBase(p),
                    change_rate: getChangeRate(p),
                    type: getProjectType(p),
                    status: p.status || '-',
                    id: p.id
                });
            });
        } else if (mgrs.length > 0) {
            mgrs.forEach(mgr => {
                rows.push({
                    _project: p,
                    project_name: p.project_name || p.name,
                    sub_name: mgr.sub_project || '-',
                    department: p.department,
                    managing_dept: mgr.managing_dept || p.division || '-',
                    impl_agency: mgr.implementing_agency || p.implementing_agency || '-',
                    sub_budget: null,
                    budget_base: getBudgetBase(p),
                    change_rate: getChangeRate(p),
                    type: getProjectType(p),
                    status: p.status || '-',
                    id: p.id
                });
            });
        } else {
            rows.push({
                _project: p,
                project_name: p.project_name || p.name,
                sub_name: '-',
                department: p.department,
                managing_dept: p.division || '-',
                impl_agency: p.implementing_agency || '-',
                sub_budget: null,
                budget_base: getBudgetBase(p),
                change_rate: getChangeRate(p),
                type: getProjectType(p),
                status: p.status || '-',
                id: p.id
            });
        }
    });
    return rows;
}

function filterProjects() {
    const search = document.getElementById('project-search')?.value?.toLowerCase() || '';
    const deptFilter = document.getElementById('project-dept-filter')?.value || '';
    const typeFilter = document.getElementById('project-type-filter')?.value || '';
    const fieldFilter = document.getElementById('project-field-filter')?.value || '';
    const techFilter = document.getElementById('project-tech-filter')?.value || '';
    const stageFilter = document.getElementById('project-stage-filter')?.value || '';
    const excludeZero = document.getElementById('filter-zero-budget')?.checked || false;
    const onlyMismatch = document.getElementById('filter-budget-mismatch')?.checked || false;
    const expr = parseSearchExpr(search);

    return DATA.projects.filter(p => {
        if (excludeZero && !getBudgetBase(p)) return false;
        if (onlyMismatch) {
            const v = validateSubBudget(p);
            if (!v || !v.hasWarning) return false;
        }
        if (deptFilter && p.department !== deptFilter) return false;
        if (typeFilter === 'rnd' && !p.is_rnd) return false;
        if (typeFilter === 'info' && !p.is_informatization) return false;
        if (typeFilter === 'general' && (p.is_rnd || p.is_informatization)) return false;
        if (fieldFilter) {
            const fields = classifyProject(p);
            if (!fields.includes(fieldFilter)) return false;
        }
        if (techFilter && !(p.ai_tech || []).includes(techFilter)) return false;
        if (stageFilter && !(p.rnd_stage || []).includes(stageFilter)) return false;
        if (expr) {
            const nameOnly = document.getElementById('search-name-only')?.checked;
            const text = nameOnly
                ? [p.project_name, p.code, ...(p.sub_projects || []).map(s => s.name)].join(' ').toLowerCase()
                : [p.name, p.project_name, p.code, p.department, p.purpose, p.implementing_agency,
                ...(p.keywords || []), ...(p.ai_domains || []), p.description || '',
                ...(p.sub_projects || []).map(s => s.name),
                ...(p.project_managers || []).map(m => [m.sub_project, m.managing_dept, m.implementing_agency].join(' '))
                ].join(' ').toLowerCase();
            if (!matchSearchExpr(expr, text)) return false;
        }
        return true;
    });
}

function sortRows(rows) {
    const sortKey = columnSort.key;
    const dir = columnSort.dir === 'asc' ? 1 : -1;
    switch (sortKey) {
        case 'code': rows.sort((a, b) => dir * ((a._project?.code || '').localeCompare(b._project?.code || ''))); break;
        case 'name': rows.sort((a, b) => dir * (a.project_name || '').localeCompare(b.project_name || '')); break;
        case 'sub_name': rows.sort((a, b) => dir * (a.sub_name || '').localeCompare(b.sub_name || '')); break;
        case 'department': rows.sort((a, b) => dir * (a.department || '').localeCompare(b.department || '')); break;
        case 'managing_dept': rows.sort((a, b) => dir * (a.managing_dept || '').localeCompare(b.managing_dept || '')); break;
        case 'impl_agency': rows.sort((a, b) => dir * (a.impl_agency || '').localeCompare(b.impl_agency || '')); break;
        case 'sub_budget': rows.sort((a, b) => dir * ((a.sub_budget || 0) - (b.sub_budget || 0))); break;
        case 'budget': rows.sort((a, b) => dir * ((a.budget_base || 0) - (b.budget_base || 0))); break;
        case 'change': rows.sort((a, b) => dir * ((a.change_rate || 0) - (b.change_rate || 0))); break;
        case 'change_abs': rows.sort((a, b) => dir * (Math.abs(a.change_rate || 0) - Math.abs(b.change_rate || 0))); break;
        case 'type': rows.sort((a, b) => dir * (a.type || '').localeCompare(b.type || '')); break;
        case 'status': rows.sort((a, b) => dir * (a.status || '').localeCompare(b.status || '')); break;
        case 'period': rows.sort((a, b) => dir * ((a._project?.project_period?.start_year || 0) - (b._project?.project_period?.start_year || 0))); break;
        default: rows.sort((a, b) => (b.budget_base || 0) - (a.budget_base || 0));
    }
    return rows;
}

function getFilteredProjects() {
    const filtered = filterProjects();
    let rows = buildFlatRows(filtered);
    const nameOnly = document.getElementById('search-name-only')?.checked;
    const search = (document.getElementById('project-search')?.value || '').toLowerCase();
    if (nameOnly && search) {
        const expr = parseSearchExpr(search);
        if (expr) {
            rows = rows.filter(r => {
                const text = [r.project_name, r.sub_name || ''].join(' ').toLowerCase();
                return matchSearchExpr(expr, text);
            });
        }
    }
    return sortRows(rows);
}

function getFilteredProjectsGrouped() {
    const filtered = filterProjects();
    let projectRows = filtered.map(p => ({
        _project: p,
        project_name: p.project_name || p.name,
        sub_name: '',
        department: p.department,
        managing_dept: p.division || '-',
        impl_agency: p.implementing_agency || '-',
        sub_budget: null,
        budget_base: getBudgetBase(p),
        change_rate: getChangeRate(p),
        type: getProjectType(p),
        status: p.status || '-',
        id: p.id
    }));
    return sortRows(projectRows);
}

// ==================== Search Expression Engine ====================

function parseSearchExpr(input) {
    input = input.trim();
    if (!input) return null;
    const tokens = [];
    let i = 0;
    while (i < input.length) {
        if (input[i] === ' ' || input[i] === '\t') { i++; continue; }
        if (input[i] === '|') { tokens.push({ type: 'OR' }); i++; continue; }
        if (input[i] === '(') { tokens.push({ type: 'LPAREN' }); i++; continue; }
        if (input[i] === ')') { tokens.push({ type: 'RPAREN' }); i++; continue; }
        let neg = false;
        if (input[i] === '-' && i + 1 < input.length && input[i + 1] !== ' ') {
            neg = true; i++;
        }
        if (input[i] === '"' || input[i] === '\u201C' || input[i] === '\u201D') {
            const closeIdx = input.indexOf('"', i + 1);
            const end = closeIdx > i ? closeIdx : input.length;
            const phrase = input.substring(i + 1, end).toLowerCase();
            if (phrase) tokens.push({ type: 'TERM', value: phrase, neg });
            i = end + 1;
        } else {
            let j = i;
            while (j < input.length && !/[\s|()]/.test(input[j])) j++;
            const word = input.substring(i, j).toLowerCase();
            if (word) tokens.push({ type: 'TERM', value: word, neg });
            i = j;
        }
    }
    let pos = 0;
    function parseOr() {
        let left = parseAnd();
        while (pos < tokens.length && tokens[pos].type === 'OR') {
            pos++;
            const right = parseAnd();
            left = { op: 'OR', left, right };
        }
        return left;
    }
    function parseAnd() {
        let left = parseAtom();
        while (pos < tokens.length && (tokens[pos].type === 'TERM' || tokens[pos].type === 'LPAREN')) {
            const right = parseAtom();
            left = { op: 'AND', left, right };
        }
        return left;
    }
    function parseAtom() {
        if (pos >= tokens.length) return { op: 'TERM', value: '', neg: false };
        const t = tokens[pos];
        if (t.type === 'LPAREN') {
            pos++;
            const expr = parseOr();
            if (pos < tokens.length && tokens[pos].type === 'RPAREN') pos++;
            return expr;
        }
        if (t.type === 'TERM') {
            pos++;
            return { op: 'TERM', value: t.value, neg: t.neg };
        }
        pos++;
        return parseAtom();
    }
    return parseOr();
}

function matchSearchExpr(expr, text) {
    if (!expr) return true;
    switch (expr.op) {
        case 'AND': return matchSearchExpr(expr.left, text) && matchSearchExpr(expr.right, text);
        case 'OR': return matchSearchExpr(expr.left, text) || matchSearchExpr(expr.right, text);
        case 'TERM': {
            let found = text.includes(expr.value);
            
            // 부처명 및 주요 기관 동의어(Alias) 확장 로직
            if (!found) {
                const aliases = (window.DATA && window.DATA.metadata && window.DATA.metadata.search_aliases) || {};
                const mapped = aliases[expr.value];
                if (mapped) {
                    found = mapped.some(alias => text.includes(alias));
                }
            }
            
            return expr.neg ? !found : found;
        }
        default: return true;
    }
}

// 글로벌 노출 (charts.js 등 타 모듈에서 공통 사용)
window.parseSearchExpr = parseSearchExpr;
window.matchSearchExpr = matchSearchExpr;


function getSearchTerms(expr) {
    if (!expr) return [];
    const terms = [];
    function collect(e) {
        if (e.op === 'TERM' && !e.neg && e.value) terms.push(e.value);
        if (e.left) collect(e.left);
        if (e.right) collect(e.right);
    }
    collect(expr);
    return terms;
}

// ==================== UI Navigation Helpers ====================

function setListMode(mode) {
    listMode = mode;
    projectPage = 1;
    document.getElementById('view-project-btn')?.classList.toggle('active', mode === 'project');
    document.getElementById('view-sub-btn')?.classList.toggle('active', mode === 'sub');
    updateProjectList();
}

function setView(v) {
    currentView = v;
    document.getElementById('view-table-btn')?.classList.toggle('active', v === 'table');
    document.getElementById('view-card-btn')?.classList.toggle('active', v === 'card');
    updateProjectList();
}

function navigateToField(fieldName, deptName) {
    const searchEl = document.getElementById('project-search');
    const deptEl = document.getElementById('project-dept-filter');
    const typeEl = document.getElementById('project-type-filter');
    const fieldSel = document.getElementById('project-field-filter');
    const nameOnlyEl = document.getElementById('search-name-only');
    if (searchEl) searchEl.value = '';
    if (deptEl) deptEl.value = '';
    if (typeEl) typeEl.value = '';
    if (nameOnlyEl) nameOnlyEl.checked = false;
    if (fieldSel) fieldSel.value = fieldName || '';
    if (deptName && deptEl) {
        const opt = [...deptEl.options].find(o => o.value === deptName || o.textContent === deptName);
        if (opt) deptEl.value = opt.value;
    }
    projectPage = 1;
    updateProjectList();
    switchToTab('projects', true);
    document.getElementById('tab-projects')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function navigateToAiTech(techType, stageType, deptName) {
    const searchEl = document.getElementById('project-search');
    const deptEl = document.getElementById('project-dept-filter');
    const techEl = document.getElementById('project-tech-filter');
    const stageEl = document.getElementById('project-stage-filter');
    if (searchEl) searchEl.value = '';
    if (deptEl) deptEl.value = '';
    if (techEl) techEl.value = techType || '';
    if (stageEl) stageEl.value = stageType || '';
    if (deptName && deptEl) {
        const opt = [...deptEl.options].find(o => o.value === deptName);
        if (opt) deptEl.value = opt.value;
    }
    projectPage = 1;
    updateProjectList();
    switchToTab('projects', true);
    document.getElementById('tab-projects')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ==================== Collaboration Tab Handler ====================
let _collabData = null;

window.renderCollab = async function () {
    const container = document.getElementById('dup-sub-collaboration');
    if (!container) return;

    // Show loading or status if needed
    if (!_collabData) {
        try {
            const resp = await fetch(window.prefix + 'data/collaboration_analysis.json');
            if (resp.ok) {
                _collabData = await resp.json();
            } else if (typeof EMBEDDED_COLLAB_DATA !== 'undefined') {
                _collabData = EMBEDDED_COLLAB_DATA;
            }
        } catch (e) {
            console.error('Collab data load failed', e);
        }
    }

    const statusEl = document.getElementById('collab-status');
    
    if (!_collabData) {
        if (statusEl) statusEl.innerHTML = '<div class="card">협업 분석 데이터를 불러올 수 없습니다.</div>';
        return;
    }

    // Hide loading status and show components
    if (statusEl) statusEl.style.display = 'none';
    
    const kpiEl = document.getElementById('collab-kpi');
    if (kpiEl) kpiEl.style.display = 'block';

    const chainsH = document.getElementById('collab-chains-header');
    if (chainsH && (_collabData.collaboration_chains || []).length > 0) {
        chainsH.style.display = 'block';
        const cCount = document.getElementById('collab-chains-count');
        if (cCount) cCount.textContent = _collabData.collaboration_chains.length;
    }

    const hubsH = document.getElementById('collab-hubs-header');
    if (hubsH && (_collabData.collaboration_network || []).length > 0) {
        hubsH.style.display = 'block';
        const hCount = document.getElementById('collab-hubs-count');
        if (hCount) hCount.textContent = _collabData.collaboration_network.length;
    }

    window.renderCollabKPI();
    window.renderCollabChains();
    window.renderCollabHubs();
    window.filterCollabPairs();
};

window.renderCollabKPI = function () {
    if (!_collabData) return;
    const meta = _collabData.metadata || {};
    const stats = _collabData.summary_statistics || {};
    const kpi = document.getElementById('collab-kpi');
    if (!kpi) return;

    const chains = _collabData.collaboration_chains || [];
    const hubs = _collabData.collaboration_network || [];
    kpi.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(150px, 1fr));gap:12px;margin-bottom:16px">
    <div class="card" style="text-align:center;padding:12px">
      <div style="font-size:22px;font-weight:700;color:var(--accent)">${meta.total_sub_projects_analyzed || '?'}</div>
      <div style="font-size:11px;color:var(--text-muted)">분석 세부사업</div>
    </div>
    <div class="card" style="text-align:center;padding:12px">
      <div style="font-size:22px;font-weight:700;color:#f59e0b">${(_collabData.pairs || []).length}</div>
      <div style="font-size:11px;color:var(--text-muted)">협업 쌍</div>
    </div>
    <div class="card" style="text-align:center;padding:12px">
      <div style="font-size:22px;font-weight:700;color:#8b5cf6">${chains.length}</div>
      <div style="font-size:11px;color:var(--text-muted)">협업 체인</div>
    </div>
    <div class="card" style="text-align:center;padding:12px">
      <div style="font-size:22px;font-weight:700;color:#10b981">${hubs.length}</div>
      <div style="font-size:11px;color:var(--text-muted)">허브 사업</div>
    </div>
  </div>`;
};

window.renderCollabChains = function () {
    if (!_collabData) return;
    const chains = _collabData.collaboration_chains || [];
    const container = document.getElementById('collab-chains-body');
    if (!container) return;
    if (!chains.length) { container.innerHTML = '발견된 협업 체인이 없습니다.'; return; }

    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:12px;margin-bottom:16px">';
    chains.slice(0, 20).forEach(ch => {
        const budgetStr = window.formatBillion(ch.total_budget_base / 100);
        html += `<div class="card" style="border-left:3px solid #8b5cf6;margin-bottom:0">
      <div style="font-weight:600;font-size:13px;margin-bottom:6px">${ch.chain_name}</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-bottom:4px">${ch.departments.join(' \u2192 ')}</div>
      <div style="display:flex;gap:12px;font-size:11px;color:var(--text-muted)">
        <span>${ch.chain_length}단계</span>
        <span>예산 ${budgetStr}</span>
      </div>
      <div style="font-size:11px;color:var(--text-secondary);margin-top:6px;line-height:1.5">${(ch.synergy_scenario || '').slice(0, 150)}...</div>
    </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
};

window.renderCollabHubs = function () {
    if (!_collabData) return;
    const hubs = (_collabData.collaboration_network || []).filter(h => h.out_degree >= 5 || h.in_degree >= 5);
    const container = document.getElementById('collab-hubs-body');
    if (!container) return;
    if (!hubs.length) { container.innerHTML = '발견된 허브 사업이 없습니다.'; return; }

    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-bottom:16px">';
    hubs.sort((a, b) => (b.out_degree + b.in_degree) - (a.out_degree + a.in_degree));
    hubs.slice(0, 15).forEach(h => {
        const hp = h.hub_project;
        const typeColor = h.hub_type === 'supply_hub' ? '#3b82f6' : '#f59e0b';
        html += `<div class="card" style="border-left:3px solid ${typeColor};margin-bottom:0">
      <div style="font-weight:600;font-size:13px;margin-bottom:4px">${hp.sub_project_name || hp.project_name}</div>
      <div style="font-size:12px;color:var(--text-secondary)">${hp.department}</div>
      <div style="display:flex;gap:12px;font-size:11px;color:var(--text-muted);margin-top:6px">
        <span style="color:${typeColor};font-weight:600">${h.hub_type === 'supply_hub' ? '공급 허브' : '수요 허브'}</span>
        <span>연결 ${h.out_degree + h.in_degree}개</span>
      </div>
      <div style="font-size:11px;color:var(--text-secondary);margin-top:4px;line-height:1.4">${(h.description || '').slice(0, 120)}...</div>
    </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
};

window.filterCollabPairs = function () {
    if (!_collabData) return;
    const pairs = _collabData.pairs || [];
    const search = (document.getElementById('collab-filter')?.value || '').toLowerCase();
    const typeFilter = document.getElementById('collab-type-filter')?.value || '';
    const minScore = parseFloat(document.getElementById('collab-score-filter')?.value || 0);

    const filtered = pairs.filter(p => {
        if (p.collaboration_score < minScore) return false;
        if (typeFilter && !(p.collaboration_type || '').includes(typeFilter)) return false;
        if (search) {
            const text = [p.project_a.project_name, p.project_a.department, p.project_b.project_name, p.project_b.department].join(' ').toLowerCase();
            return text.includes(search);
        }
        return true;
    });

    const displayCount = document.getElementById('collab-pair-count');
    if (displayCount) displayCount.textContent = `${filtered.length} / ${pairs.length}쌍`;

    const container = document.getElementById('collab-pairs');
    if (!container) return;

    let html = `<table class="data-table" style="font-size:12px"><thead><tr>
      <th>공급(A)</th><th>수요(B)</th><th>점수</th><th>유형</th><th>상세</th>
    </tr></thead><tbody>`;
    filtered.slice(0, 100).forEach((p, i) => {
        const scoreColor = p.collaboration_score >= 9 ? '#ef4444' : p.collaboration_score >= 7 ? '#f59e0b' : '#3b82f6';
        html += `<tr onclick="window.showCollabDetail(${i})">
      <td>${p.project_a.sub_project_name || p.project_a.project_name}<div style="font-size:10px;color:var(--text-muted)">${p.project_a.department}</div></td>
      <td>${p.project_b.sub_project_name || p.project_b.project_name}<div style="font-size:10px;color:var(--text-muted)">${p.project_b.department}</div></td>
      <td style="color:${scoreColor};font-weight:700;text-align:center">${p.collaboration_score}</td>
      <td>${p.collaboration_type}</td>
      <td><button class="btn btn-sm">보기</button></td>
    </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
};

window.showCollabDetail = function (idx) {
    // Modal-based detail view logic
    const pair = (_collabData.pairs || [])[idx];
    if (!pair) return;
    // Implementation simplified for brevity
    alert(`협업 상세: ${pair.project_a.project_name} - ${pair.project_b.project_name}\n기술 시너지: ${pair.collaboration_score}점`);
};

// ==================== Flow Tab Handler ====================
let flowSelectedDepts = new Set();

window.renderFlow = function () {
    if (!window.DATA) return;
    window.renderYearTrend();
    window.renderSankey();
};

window.renderYearTrend = function () {
    const allDepts = window.getAllDepartmentsSorted();
    const topDepts = window.getTopDepartments(8);
    if (flowSelectedDepts.size === 0) topDepts.forEach(d => flowSelectedDepts.add(d));

    const selector = document.getElementById('flow-dept-selector');
    if (!selector) return;

    let selHtml = `<select id="flow-dept-add" class="btn btn-sm" style="margin-right:8px"><option value="">+ 부처 추가</option>`;
    allDepts.forEach(d => { if (!flowSelectedDepts.has(d)) selHtml += `<option value="${d}">${d}</option>`; });
    selHtml += '</select>';

    selHtml += [...flowSelectedDepts].map((d, i) => {
        const c = COLORS[i % COLORS.length];
        return `<span class="tag" style="background:${c}22;color:${c};border:1px solid ${c}44;cursor:pointer" onclick="flowSelectedDepts.delete('${d}');window.renderYearTrend()">
      ${d.substring(0, 8)} <span style="font-size:9px;opacity:0.7">×</span>
    </span>`;
    }).join(' ');

    selector.innerHTML = selHtml;
    document.getElementById('flow-dept-add')?.addEventListener('change', (e) => {
        if (e.target.value) { flowSelectedDepts.add(e.target.value); window.renderYearTrend(); }
    });

    const selectedArr = [...flowSelectedDepts];
    const datasets = selectedArr.map((dept, i) => {
        const dp = window.DATA.projects.filter(p => p.department === dept);
        return {
            label: dept.substring(0, 10),
            data: [
                dp.reduce((s, p) => s + window.getBudget2024(p), 0),
                dp.reduce((s, p) => s + window.getBudgetPrev(p), 0),
                dp.reduce((s, p) => s + window.getBudgetBase(p), 0)
            ],
            borderColor: COLORS[i % COLORS.length],
            tension: 0.3,
            fill: false
        };
    });

    window.destroyChart('chart-year-trend');
    window.chartInstances['chart-year-trend'] = new Chart(document.getElementById('chart-year-trend'), {
        type: 'line',
        data: { labels: ['2024 결산', '2025 예산', '2026 확정'], datasets },
        options: { responsive: true, maintainAspectRatio: false }
    });
};

window.renderSankey = function () {
    // Sankey diagram placeholder or implementation
    const container = document.getElementById('flow-sankey-container');
    if (container) container.innerHTML = '<div class="card">Sankey 다이어그램 (D3.js) 렌더링 영역</div>';
};

// ==================== Export & Reports ====================

function downloadMarkdown() {
    if (!DATA) return;
    const text = generatePressText();
    const md = `# ${window.BASE_YEAR}년 AI 재정사업 분석 요약\n\n> 생성일: ${new Date().toLocaleDateString('ko-KR')}\n\n${text.replace(/\[(.+?)\]/g, '## $1')}`;
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `KAIB2026_Report_${getDateStr()}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
}

function getDateStr() {
    const d = new Date();
    return d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0');
}

function downloadCSV(filename, rows) {
    if (!rows || rows.length === 0) return;
    const header = Object.keys(rows[0]).join(',');
    const csv = [header, ...rows.map(r => Object.values(r).map(v => `"${(v || '').toString().replace(/"/g, '""')}"`).join(','))].join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
}

function exportProjectCSV() {
    const rows = getFilteredProjects().map(r => ({
        '사업코드': r._project.code || '',
        '사업명': r.project_name,
        '내역사업명': r.sub_name,
        '부처명': r.department,
        '소관부서': r.managing_dept,
        '시행주체': r.impl_agency,
        '2026예산(백만)': r.budget_base,
        '증감률(%)': r.change_rate,
        '사업유형': r.type,
        '상태': r.status
    }));
    downloadCSV(`KAIB2026_Projects_${getDateStr()}.csv`, rows);
}

function exportProjectExcel() {
    const rows = getFilteredProjects().map(r => ({
        '사업코드': r._project.code || '',
        '사업명': r.project_name,
        '내역사업명': r.sub_name,
        '부처명': r.department,
        '소관부서': r.managing_dept,
        '시행주체': r.impl_agency,
        '2026예산(백만)': r.budget_base,
        '증감률(%)': r.change_rate,
        '사업유형': r.type,
        '상태': r.status
    }));
    const worksheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Projects');
    XLSX.writeFile(workbook, `KAIB2026_Projects_${getDateStr()}.xlsx`);
}

// ==================== Press Report Modal ====================

function generatePressText() {
    if (!DATA) return '';
    const projects = DATA.projects;
    const meta = DATA.metadata || {};
    const analysis = DATA.analysis || {};
    const dups = analysis.duplicates || [];
    const fmtB = v => formatBillion(v);
    const fmtT = v => (v / 1000000).toFixed(1) + '조';

    const totalBudget = projects.reduce((s, p) => s + getBudgetBase(p), 0);
    const totalBudget2025 = projects.reduce((s, p) => s + getBudgetPrev(p), 0);
    const changeRate = totalBudget2025 > 0 ? ((totalBudget - totalBudget2025) / totalBudget2025 * 100).toFixed(1) : '-';
    const rndProjects = projects.filter(p => p.is_rnd);
    const rndBudget = rndProjects.reduce((s, p) => s + getBudgetBase(p), 0);
    const newProjects = projects.filter(p => p.status === '\uc2e0\uaddc');
    const over50 = projects.filter(p => Math.abs(getChangeRate(p)) >= 50);
    const dupProjectCount = new Set();
    dups.forEach(g => (g.projects || []).forEach(p => dupProjectCount.add(p.name)));

    const top5 = projects.slice().sort((a, b) => getBudgetBase(b) - getBudgetBase(a)).slice(0, 5);
    const deptBudget = {};
    projects.forEach(p => { deptBudget[p.department] = (deptBudget[p.department] || 0) + getBudgetBase(p); });
    const top5Dept = Object.entries(deptBudget).sort((a, b) => b[1] - a[1]).slice(0, 5);

    let text = `[${window.BASE_YEAR}년 AI 재정사업 분석 요약]\n\n`;
    text += `- 총 예산: ${fmtB(totalBudget)} (전년비 ${changeRate}%)\n`;
    text += `- 총 사업 수: ${projects.length}개 (${meta.total_departments || new Set(projects.map(p => p.department)).size}개 부처)\n`;
    text += `- R&D 사업: ${rndProjects.length}개 (${fmtB(rndBudget)})\n`;
    text += `- 신규 사업: ${newProjects.length}개\n`;
    text += `- 전년비 50% 이상 증감: ${over50.length}개\n`;
    text += `- 중복 의심 그룹: ${dups.length}개 (${dupProjectCount.size}개 사업)\n\n`;
    text += `[상위 5대 사업]\n`;
    top5.forEach((p, i) => { text += `${i + 1}. ${p.project_name || p.name} (${p.department}) - ${fmtB(getBudgetBase(p))}\n`; });
    text += `\n[상위 5대 부처]\n`;
    top5Dept.forEach(([d, b], i) => { text += `${i + 1}. ${d} - ${fmtB(b)}원 (${(b / totalBudget * 100).toFixed(1)}%)\n`; });

    return text;
}

function openPressReport() {
    const text = generatePressText();
    document.getElementById('press-report-content').textContent = text;
    document.getElementById('press-report-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closePressReport() {
    document.getElementById('press-report-modal').classList.remove('active');
    document.body.style.overflow = '';
}

function copyPressReport() {
    const text = document.getElementById('press-report-content').textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const orig = btn.textContent;
        btn.textContent = '복사 완료!';
        btn.style.background = 'var(--green)';
        setTimeout(() => { btn.textContent = orig; btn.style.background = 'var(--accent)'; }, 1500);
    });
}

function downloadPressReportMd() {
    const text = generatePressText();
    const md = `# ${window.BASE_YEAR}년 AI 재정사업 분석 요약\n\n> 생성일: ${new Date().toLocaleDateString('ko-KR')}\n\n${text.replace(/\[(.+?)\]/g, '## $1')}`;
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '2026_AI_재정사업_보도자료.md';
    a.click();
    URL.revokeObjectURL(a.href);
}

// ==================== 국회 질의 포인트 ====================

function generateInquiryPoints(project) {
    const points = [];
    const cr = getChangeRate(project);
    const budget2026 = getBudgetBase(project);
    const pName = project.project_name || project.name;

    if (Math.abs(cr) >= 30) {
        const dir = cr > 0 ? '\uc99d\uac00' : '\uac10\uc18c';
        points.push(`예산 ${Math.abs(cr).toFixed(1)}% ${dir} 사유 설명 요구 (${formatBillion(Math.abs(getChangeAmount(project)))} ${dir})`);
    }

    const dupGroups = getDuplicateGroupsForProject(project.id, pName);
    if (dupGroups.length > 0) {
        dupGroups.forEach(g => {
            const others = (g.projects || []).filter(p => (p.name || p.project_name) !== pName).slice(0, 3).map(p => p.name || p.project_name);
            if (others.length > 0) {
                points.push(`유사사업(${others.join(', ')} 등) 대비 차별성 및 통합 검토 여부`);
            }
        });
    }

    const isNew = project.status === '\uc2e0\uaddc' || formatRate(cr, project) === '\uc21c\uc99d';
    if (isNew) {
        points.push('신규사업 타당성 및 기대효과 근거');
    }

    if (!budget2026 || budget2026 === 0) {
        points.push('사업 미편성 사유 및 향후 계획');
    }

    if (budget2026 >= 50000) {
        points.push(`대규모 사업(${formatBillion(budget2026)}) 집행계획 및 성과관리 방안`);
    }

    return points;
}

// ==================== Initialization ====================

function initTabNavigation() {
    // Click listeners for .tab-btn
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            if (tabId) switchToTab(tabId, true);
        });
    });

    // Keyboard Navigation for .tab-nav-inner
    const navInner = document.querySelector('.tab-nav-inner');
    if (navInner) {
        navInner.addEventListener('keydown', (e) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;

            const btns = [...navInner.querySelectorAll('.tab-btn')];
            if (btns.length === 0) return;

            e.preventDefault();
            const idx = btns.findIndex(b => b.classList.contains('active'));
            let newIdx;

            if (e.key === 'ArrowRight') newIdx = (idx + 1) % btns.length;
            else if (e.key === 'ArrowLeft') newIdx = (idx - 1 + btns.length) % btns.length;
            else if (e.key === 'Home') newIdx = 0;
            else if (e.key === 'End') newIdx = btns.length - 1;

            if (newIdx !== undefined) {
                btns[newIdx].focus();
                switchToTab(btns[newIdx].dataset.tab, true);
            }
        });
    }

    // Popstate for browser back/forward
    window.addEventListener('popstate', (e) => {
        restoreFromHash();
    });
}

function restoreFromHash() {
    const hash = window.location.hash.replace('#', '');
    if (hash) {
        switchToTab(hash, false);
    } else {
        switchToTab('overview', false);
    }
}

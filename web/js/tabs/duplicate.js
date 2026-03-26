/**
 * KAIB2026 Duplicate & Similarity Analysis Tab Logic
 */

const GRADE_COLORS = { 1: '#dc2626', 2: '#ea580c', 3: '#ca8a04', 4: '#2563eb', 5: '#6b7280' };
const GRADE_LABELS = { 1: '완전중복', 2: '고유사', 3: '부분중복', 4: '약유사', 5: '비유사' };

window.getGradeFromSim = function (sim) {
    if (sim >= 0.9) return 1;
    if (sim >= 0.75) return 2;
    if (sim >= 0.5) return 3;
    if (sim >= 0.3) return 4;
    return 5;
};

window.gradeHtml = function (sim) {
    const g = window.getGradeFromSim(sim);
    return `<span class="badge badge-${GRADE_COLORS[g]}" style="background:${GRADE_COLORS[g]}22;color:${GRADE_COLORS[g]};border:1px solid ${GRADE_COLORS[g]}aa">${g}등급 ${GRADE_LABELS[g]}</span>`;
};

window.switchDupSubTab = function (tabName) {
    if (!tabName) return;
    document.querySelectorAll('.dup-sub-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.subtab === tabName);
    });
    document.querySelectorAll('.dup-sub-content').forEach(div => {
        const id = div.id.replace('dup-sub-', '');
        const isActive = id === tabName;
        div.classList.toggle('active', isActive);
        div.style.display = isActive ? '' : 'none';
    });

    if (tabName === 'network') {
        if (typeof window.initNetworkViz === 'function') {
            setTimeout(() => window.initNetworkViz(window.DATA), 100);
        }
    }
};

window.renderDuplicate = function () {
    if (!window.DATA) return;

    const duplicateGroups = window.analyzeDuplicates(window.DATA.projects);
    const presetDuplicates = (window.DATA.analysis && window.DATA.analysis.duplicates) || [];

    // EMBEDDED_SIM_V10_DATA (v10 인력양성 등 고도화 데이터) 연동
    const simV10Clusters = (typeof EMBEDDED_SIM_V10_DATA !== 'undefined' && EMBEDDED_SIM_V10_DATA.clusters) || [];
    const simV10Groups = simV10Clusters.map(c => ({
        group_name: c.cluster_name || c.top_keywords?.join(', ') || '유사 사업 그룹',
        projects: c.projects.map(p => {
            const fullP = window.DATA.projects.find(px => String(px.id) === String(p.id)) || p;
            return {
                id: p.id,
                name: fullP.project_name || fullP.name,
                department: fullP.department,
                budget_base: window.getBudgetBase(fullP)
            };
        }),
        total_budget: c.projects.reduce((s, p) => {
            const fullP = window.DATA.projects.find(px => String(px.id) === String(p.id)) || p;
            return s + window.getBudgetBase(fullP);
        }, 0),
        reason: '인력양성/AI기술 고도화 분석 기반'
    }));

    const allGroups = [...presetDuplicates.filter(g => g.projects && g.projects.length > 1), ...simV10Groups, ...duplicateGroups];
    const uniqueGroups = window.deduplicateGroups(allGroups);

    // KPI Update
    const totalDupBudget = uniqueGroups.reduce((s, g) => {
        // Calculate total budget for this group by looking up current budgets by project ID
        return s + g.projects.reduce((ss, p) => {
            const projectObj = window.DATA.projects.find(px => px.id === p.id);
            return ss + (projectObj ? window.getBudgetBase(projectObj) : (p.budget_base || 0));
        }, 0);
    }, 0);
    const totalDupProjects = new Set(uniqueGroups.flatMap(g => g.projects.map(p => p.id))).size;

    const kpiEl = document.getElementById('dup-kpi-grid');
    if (kpiEl) {
        kpiEl.innerHTML = `
            <div class="kpi-card">
                <div class="value">${uniqueGroups.length}</div>
                <div class="label">중복 의심 그룹</div>
            </div>
            <div class="kpi-card">
                <div class="value">${totalDupProjects}</div>
                <div class="label">관련 사업 수</div>
            </div>
            <div class="kpi-card">
                <div class="value">${window.formatBillion(totalDupBudget)}</div>
                <div class="label">중복 관련 예산</div>
            </div>
        `;
    }

    if (typeof window.renderDupGroups === 'function') {
        window.renderDupGroups(uniqueGroups, 'dup-groups-container');
    }
};

window.analyzeDuplicates = function (projects) {
    if (projects.length > 2000) {
        console.warn('Dataset > 2000. Skipping heavy O(N^2) similarity detection to save UI thread. Using preset data.');
        return [];
    }
    const groups = [];
    const paired = new Set();
    const similarGroups = {};
    let groupId = 0;

    // Jaccard Tokenization
    function tokenize(name) {
        return (name || '').replace(/\([^)]*\)/g, '').replace(/[^가-힣a-zA-Z0-9\s]/g, '')
            .split(/\s+/).filter(w => w.length > 1);
    }

    function jaccard(a, b) {
        const setA = new Set(a), setB = new Set(b);
        const intersection = new Set([...setA].filter(x => setB.has(x)));
        const union = new Set([...setA, ...setB]);
        return union.size > 0 ? intersection.size / union.size : 0;
    }

    const tokenized = projects.map(p => ({ project: p, tokens: tokenize(p.project_name || p.name) }));

    for (let i = 0; i < tokenized.length; i++) {
        for (let j = i + 1; j < tokenized.length; j++) {
            if (tokenized[i].project.department === tokenized[j].project.department) continue;
            const sim = jaccard(tokenized[i].tokens, tokenized[j].tokens);
            if (sim >= 0.4) {
                let foundGroup = null;
                for (const gid in similarGroups) {
                    if (similarGroups[gid].projectIds.has(i) || similarGroups[gid].projectIds.has(j)) {
                        foundGroup = gid; break;
                    }
                }
                if (foundGroup) {
                    similarGroups[foundGroup].projectIds.add(i);
                    similarGroups[foundGroup].projectIds.add(j);
                } else {
                    similarGroups[groupId++] = { projectIds: new Set([i, j]), similarity: sim };
                }
            }
        }
    }

    for (const g of Object.values(similarGroups)) {
        const gProjects = [...g.projectIds].map(idx => tokenized[idx].project);
        if (gProjects.length > 1) {
            groups.push({
                group_name: (gProjects[0].project_name || gProjects[0].name || '유사그룹').substring(0, 15),
                projects: gProjects.map(p => ({ id: p.id, name: p.project_name || p.name || '알 수 없음', department: p.department, budget_base: window.getBudgetBase(p) })),
                total_budget: gProjects.reduce((s, p) => s + window.getBudgetBase(p), 0),
                reason: '사업명 유사도 기반 탐지'
            });
        }
    }

    return groups;
};

window.deduplicateGroups = function (groups) {
    const result = [];
    for (const g of groups) {
        const gIds = new Set(g.projects.map(p => p.id || p.name));
        let isDup = false;
        for (const existing of result) {
            const eIds = new Set(existing.projects.map(p => p.id || p.name));
            const overlap = [...gIds].filter(id => eIds.has(id)).length;
            if (overlap / Math.min(gIds.size, eIds.size) > 0.8) { isDup = true; break; }
        }
        if (!isDup) result.push(g);
    }
    return result;
};

window.renderDupGroups = function (groups, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!groups || groups.length === 0) {
        container.innerHTML = '<div class="empty-state">검출된 유사/중복 의심 그룹이 없습니다.</div>';
        return;
    }

    let html = '';
    groups.forEach((g, idx) => {
        const avgSim = g.similarity || 0.7; // Fallback if not provided
        html += `
            <div class="dup-group-card">
                <div class="group-header">
                    <div class="group-title">${idx + 1}. ${g.group_name}</div>
                    <div class="group-meta">
                        ${window.gradeHtml ? window.gradeHtml(avgSim) : ''}
                        <span class="budget-tag">${window.formatBillion(g.total_budget)}</span>
                    </div>
                </div>
                <div class="group-reason">${g.reason || '유사도 기반 자동 검출'}</div>
                <div class="group-projects">
                    <table class="dup-table">
                        <thead>
                            <tr>
                                <th>사업명</th>
                                <th>부처</th>
                                <th class="num">예산(26)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${g.projects.map(p => `
                                <tr onclick="window.showProjectModal(${p.id})">
                                    <td class="name-cell">${p.name}</td>
                                    <td class="dept-cell">${p.department}</td>
                                    <td class="num">${window.formatBillion(p.budget_base)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
};

/**
 * KAIB2026 Global State & Constants
 */
window.DATA = window.DATA || null;
window.chartInstances = window.chartInstances || {};
window.currentTab = '';
window.currentView = 'table';
window.listMode = 'project';
window.projectPage = 1;
window.vsScrollTop = 0;
window.columnSort = { key: 'budget-desc', dir: 'desc' };
window.compareSet = new Set();

// Color Palettes
window.COLORS = [
    '#4a9eff', '#a78bfa', '#34d399', '#fbbf24', '#f87171',
    '#fb923c', '#f472b6', '#22d3ee', '#818cf8', '#a3e635',
    '#e879f9', '#2dd4bf', '#facc15', '#38bdf8', '#c084fc',
];

/**
 * Budget Extraction (Standardized for budget_db.json)
 */
window.getBudgetBase = p => {
    if (!p) return 0;
    const by = window.BASE_YEAR || 2026;
    return p.budget?.[`budget_${by}`] ?? p.budget?.[`${by}_budget`] ?? p[`budget_${by}`] ?? p.budget_base ?? 0;
};
window.getBudgetPrev = p => {
    if (!p) return 0;
    const py = (window.BASE_YEAR || 2026) - 1;
    return p.budget?.[`budget_${py}`] ?? p.budget?.[`${py}_original`] ?? p[`budget_${py}`] ?? p.budget_prev ?? 0;
};
window.getBudget2024 = p => {
    if (!p) return 0;
    const sy = (window.BASE_YEAR || 2026) - 2;
    return p.budget?.[`budget_${sy}`] ?? p.budget?.[`${sy}_settlement`] ?? p[`budget_${sy}`] ?? 0;
};

window.getChangeRate = function (p) {
    if (!p) return 0;
    const b25 = window.getBudgetPrev(p);
    const b26 = window.getBudgetBase(p);
    if (b25 === 0) return b26 > 0 ? 1000 : 0; // 1000 = "New" marker
    return ((b26 - b25) / b25) * 100;
};

window.getChangeAmount = function (p) {
    if (!p) return 0;
    return window.getBudgetBase(p) - window.getBudgetPrev(p);
};

window.isZeroBudget = function (p) {
    return window.getBudgetBase(p) === 0;
};

/**
 * Formatting Utilities
 */
window.formatNumber = function (n) {
    if (n == null || isNaN(n)) return '-';
    return Number(n).toLocaleString('ko-KR');
};

window.formatBillion = function (millionWon) {
    if (millionWon == null || isNaN(millionWon) || millionWon === 0) {
        return millionWon === 0 ? '0억원' : '-';
    }
    const billion = millionWon / 100;
    if (Math.abs(billion) >= 10000) return (billion / 10000).toFixed(1) + '조';
    if (Math.abs(billion) >= 1) return billion.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 }) + '억원';
    return millionWon.toFixed(0) + '백만원';
};

window.formatRate = function (r, p) {
    if (r == null || isNaN(r)) return '-';
    if (r === 1000 || (p && p.status === '신규' && r > 500)) return '신규';
    return (r > 0 ? '+' : '') + r.toFixed(1) + '%';
};

window.nlToBr = function (text) {
    if (!text) return '';
    return text.toString().replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
};

window.highlightText = function (text, term) {
    if (!text || !term) return text || '';
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const reg = new RegExp(`(${escaped})`, 'gi');
    return text.toString().replace(reg, '<mark>$1</mark>');
};

/**
 * Classification & Domain Helpers
 */
window.getProjectType = function (p) {
    if (!p) return '일반';
    if (p.is_rnd || (p.project_name && p.project_name.includes('R&D'))) return 'R&D';
    if (p.is_informatization || (p.project_name && p.project_name.includes('(정보화)'))) return '정보화';
    return '일반';
};

window.getProjectTypeClass = function (p) {
    const type = window.getProjectType(p);
    if (type === 'R&D') return 'rnd';
    if (type === '정보화') return 'info';
    return 'general';
};

window.classifyProject = function (p) {
    if (!p) return ['기타'];
    const domains = p.ai_domains;
    if (domains && domains.length > 0) return domains;

    // Fallback simple classifier
    const name = (p.project_name || p.name || '').toLowerCase();
    if (name.includes('반도체')) return ['AI반도체'];
    if (name.includes('의료') || name.includes('바이오')) return ['AI의료/바이오'];
    if (name.includes('제조') || name.includes('공정')) return ['AI제조/산업'];
    if (name.includes('교육') || name.includes('인력')) return ['인력양성/교육'];
    return ['기타'];
};

/**
 * UI & Modal Helpers
 */
window.populateSelect = function (id, items) {
    const sel = document.getElementById(id);
    if (!sel) return;
    const firstOpt = sel.options[0];
    sel.innerHTML = '';
    if (firstOpt) sel.appendChild(firstOpt);
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item; opt.textContent = item;
        sel.appendChild(opt);
    });
};

window.getDisplayName = function (proj, tabId) {
    if (!proj) return { primary: '-', secondary: '' };
    const pName = proj.project_name || proj.name || '-';
    const sName = proj.sub_project_name || proj.sub_name || '';
    if (tabId === 'collab') {
        return { primary: sName || pName, secondary: sName ? pName : '' };
    }
    return { primary: pName, secondary: sName };
};

window.fmtName = function (proj, tabId) {
    const dn = window.getDisplayName(proj, tabId);
    return `<div class="name-primary">${dn.primary}</div>${dn.secondary ? `<div class="name-secondary">${dn.secondary}</div>` : ''}`;
};

/**
 * Analysis Helpers
 */
window.validateSubBudget = function (p) {
    if (!p || !p.sub_projects || p.sub_projects.length === 0) return { hasWarning: false };
    const sum = p.sub_projects.reduce((s, sp) => s + (sp.budget_base || 0), 0);
    const total = window.getBudgetBase(p);
    if (total === 0) return { hasWarning: false };
    const diffPct = (Math.abs(sum - total) / total) * 100;
    return { hasWarning: diffPct > 1, sum, total, diffPct: diffPct.toFixed(1) };
};

window.calcWasteRiskScore = function (p, dupIds) {
    if (!p) return 0;
    let score = 0;
    if (dupIds && dupIds.has(p.id)) score += 40;
    const cr = Math.abs(window.getChangeRate(p) || 0);
    if (cr >= 100) score += 30;
    else if (cr >= 50) score += 20;
    if (p.status === '신규' && window.getBudgetBase(p) >= 10000) score += 30;
    return Math.min(100, score);
};

window.getWasteRiskGrade = function (score) {
    if (score >= 80) return '위험';
    if (score >= 50) return '주의';
    return '보통';
};

window.hasMemo = function (id) {
    try {
        const notes = JSON.parse(localStorage.getItem('project-notes') || '{}');
        return !!notes[id];
    } catch (e) { return false; }
};

/**
 * Chart Helpers
 */
window.destroyChart = function (id) {
    if (window.chartInstances && window.chartInstances[id]) {
        window.chartInstances[id].destroy();
        delete window.chartInstances[id];
    }
};

window.getChartLabelColor = function () {
    return getComputedStyle(document.documentElement).getPropertyValue('--chart-label').trim() || '#8899aa';
};

window.getChartGridColor = function () {
    return getComputedStyle(document.documentElement).getPropertyValue('--chart-grid').trim() || '#2a3a4e33';
};

/**
 * UI & Theme Helpers
 */
window.toggleDocMenu = function (event) {
    const menu = document.getElementById('doc-menu');
    if (!menu) return;
    const isVisible = menu.style.display === 'block';
    menu.style.display = isVisible ? 'none' : 'block';
    if (event) event.stopPropagation();
};

window.closeDocMenu = function () {
    const menu = document.getElementById('doc-menu');
    if (menu) menu.style.display = 'none';
};

window.changeAppTheme = function (theme) {
    const link = document.getElementById('theme-link');
    if (!link) return;
    if (theme === 'default' || !theme) {
        link.href = '';
    } else {
        link.href = `css/${theme}.css`;
    }
    localStorage.setItem('app-theme', theme);
};

// Close menu when clicking outside
document.addEventListener('click', () => {
    window.closeDocMenu();
});

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('app-theme');
    if (savedTheme) {
        window.changeAppTheme(savedTheme);
        const selector = document.getElementById('theme-selector');
        if (selector) selector.value = savedTheme;
    }
});

/**
 * KAIB2026 Main Application Entry
 * (Reconstructed after corruption)
 */

window.loadData = async function () {
    console.log("Starting loadData...");
    try {
        const cacheBust = `?v=${Date.now()}`;
        const resp = await fetch('data/budget_db.json' + cacheBust);
        if (!resp.ok) throw new Error('fetch failed');
        window.DATA = await resp.json();
    } catch (e) {
        console.warn("Fetch failed, falling back to EMBEDDED_DATA:", e);
        window.DATA = typeof EMBEDDED_DATA !== 'undefined' ? EMBEDDED_DATA : null;
    }

    if (window.DATA) {
        window.BASE_YEAR = window.DATA?.metadata?.base_year || 2026;
        document.title = `${window.BASE_YEAR} NIPA 사업분석 플랫폼(테스트중)`;
        document.querySelectorAll('.dyn-year').forEach(el => el.textContent = window.BASE_YEAR);
        window.initDashboard();
    } else {
        console.error("Critical: DATA is null. Retrying in 1s...");
        setTimeout(() => { if (typeof EMBEDDED_DATA !== 'undefined') { window.DATA = EMBEDDED_DATA; window.initDashboard(); } }, 1000);
    }
};

window.initDashboard = function () {
    console.log("initDashboard starting. DATA projects count:", window.DATA?.projects?.length);
    if (!window.DATA || !window.DATA.projects) return;

    try {
        const projects = window.DATA.projects;
        const metadata = window.DATA.metadata || {};

        // Stats
        const statProjects = document.getElementById('stat-projects');
        const statBudget = document.getElementById('stat-budget');
        const statDepts = document.getElementById('stat-depts');
        const statSubs = document.getElementById('stat-subs');

        // Always calculate from projects array to ensure synchronization
        const calculatedProjectCount = projects.length;
        const calculatedBudget = projects.reduce((s, p) => s + getBudgetBase(p), 0);
        const calculatedDepts = new Set(projects.map(p => p.department)).size;

        if (statProjects) statProjects.textContent = formatNumber(calculatedProjectCount);
        if (statBudget) statBudget.textContent = formatBillion(calculatedBudget);
        if (statDepts) statDepts.textContent = formatNumber(calculatedDepts);

        const calculatedSubs = projects.reduce((s, p) => s + (p.sub_projects?.length || 0), 0);
        if (statSubs) statSubs.textContent = formatNumber(calculatedSubs);

        // Populate Selects
        const depts = [...new Set(projects.map(p => p.department))].sort();
        if (typeof populateSelect === 'function') {
            populateSelect('dept-select', depts);
            populateSelect('project-dept-filter', depts);
        }

        // Initialize Tab Navigation & Hash
        if (typeof initTabNavigation === 'function') initTabNavigation();
        if (typeof restoreFromHash === 'function') {
            restoreFromHash();
        } else if (typeof renderOverview === 'function') {
            renderOverview();
        }

        // Search Event
        const searchInput = document.getElementById('overview-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(window.searchTimer);
                window.searchTimer = setTimeout(() => renderOverview(), 300);
            });
        }
    } catch (e) {
        console.error("initDashboard error:", e);
    }
};

// Entry Point
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded - loading data...");
    if (typeof window.loadData === 'function') window.loadData();
});

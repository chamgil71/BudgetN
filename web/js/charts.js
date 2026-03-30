/**
 * KAIB2026 Chart Rendering Logic
 * (Full Implementation Reconstructed)
 */

window.chartInstances = window.chartInstances || {};

/**
 * Overview Data & KPI Helpers
 */
window.getOverviewProjects = function () {
    if (!window.DATA || !window.DATA.projects) return [];
    // Basic filtering can be added here (e.g., from a search input)
    const searchInput = document.getElementById('overview-search');
    const search = searchInput ? searchInput.value.trim().toLowerCase() : '';
    if (!search) return window.DATA.projects;

    // Utilize parseSearchExpr if available from common.js
    const expr = typeof window.parseSearchExpr === 'function' ? window.parseSearchExpr(search) : null;

    return window.DATA.projects.filter(p => {
        const text = [
            p.name, p.project_name, p.code, p.department, p.purpose, p.implementing_agency,
            ...(p.keywords || []), ...(p.ai_domains || []), p.description || '',
            ...(p.sub_projects || []).map(s => s.name),
            ...(p.project_managers || []).map(m => [m.sub_project, m.managing_dept, m.implementing_agency].join(' '))
        ].join(' ').toLowerCase();

        return expr ? window.matchSearchExpr(expr, text) : text.includes(search);
    });
};

window.renderOverview = function () {
    if (!window.DATA) return;
    const projects = window.getOverviewProjects();
    const totalBudget = projects.reduce((s, p) => s + window.getBudgetBase(p), 0);
    const totalBudget2025 = projects.reduce((s, p) => s + window.getBudgetPrev(p), 0);
    const budgetChange = totalBudget - totalBudget2025;
    const budgetChangeRate = totalBudget2025 > 0 ? (budgetChange / totalBudget2025 * 100) : 0;
    const deptCount = new Set(projects.map(p => p.department)).size;
    const newCount = projects.filter(p => p.status === '신규').length;
    const rndCount = projects.filter(p => p.is_rnd).length;

    // Search Result Count
    const countEl = document.getElementById('overview-search-count');
    if (countEl) {
        countEl.textContent = projects.length < window.DATA.projects.length ?
            `${window.formatNumber(projects.length)} / ${window.formatNumber(window.DATA.projects.length)}개 사업` : '';
    }

    // KPI Cards
    const kpiGrid = document.getElementById('kpi-grid');
    if (kpiGrid) {
        const colors = window.COLORS;
        kpiGrid.innerHTML = `
            <div class="kpi-card">
                <div class="icon" style="background:${colors[0]}22;color:${colors[0]}">$</div>
                <div class="value">${window.formatBillion(totalBudget)}</div>
                <div class="label">${window.BASE_YEAR}년 총 예산</div>
                <div class="change ${budgetChange >= 0 ? 'positive' : 'negative'}">
                    ${budgetChange >= 0 ? '▲' : '▼'} ${window.formatRate(budgetChangeRate)} (${window.formatBillion(Math.abs(budgetChange))})
                </div>
            </div>
            <div class="kpi-card">
                <div class="icon" style="background:${colors[1]}22;color:${colors[1]}">#</div>
                <div class="value">${window.formatNumber(projects.length)}</div>
                <div class="label">총 사업 수</div>
                <div class="change positive">신규 ${newCount}개</div>
            </div>
            <div class="kpi-card">
                <div class="icon" style="background:${colors[2]}22;color:${colors[2]}">B</div>
                <div class="value">${deptCount}</div>
                <div class="label">참여 부처 수</div>
            </div>
            <div class="kpi-card">
                <div class="icon" style="background:${colors[3]}22;color:${colors[3]}">R</div>
                <div class="value">${rndCount}</div>
                <div class="label">R&D 사업</div>
                <div class="change">${window.formatBillion(projects.filter(p => p.is_rnd).reduce((s, p) => s + window.getBudgetBase(p), 0))}</div>
            </div>
        `;
    }

    // Call Chart Engine
    window.renderOverviewCharts(projects);
};

/**
 * Main entry point for rendering the Overview tab charts.
 */
window.renderOverviewCharts = function (projects) {
    const data = projects || window.DATA?.projects;
    if (!data) return;

    try {
        window.renderDeptDonut(data);
        window.renderTypeDist(data);
        window.renderAccountType(data);
        window.renderStatusDist(data);
        window.renderTopChange(data);
        window.renderChangeDist(data);
        window.renderBudgetHist(data);
        window.renderReqVsBudget(data);

        // Advanced / New Widgets
        window.renderFieldBubble(data);
        window.renderWaterfall(data);
        window.renderDeptPortfolio(data);
        window.renderNewProjects(data);
        window.renderDomainHeatmap(data);
        window.renderSubProjectWidgets(data);
        window.renderAnomalyDetection(data);
        window.renderHHIAnalysis(data);
        window.renderBudgetDistDetail(data);
        window.renderWasteRisk(data);
        window.renderGlobalBenchmark();
    } catch (err) {
        console.error("Error rendering overview charts:", err);
    }
};

// --- Basic Charts ---

window.renderDeptDonut = function (projects) {
    const canvas = document.getElementById('chart-dept-donut');
    if (!canvas) return;
    destroyChart('chart-dept-donut');

    const deptData = {};
    projects.forEach(p => {
        const d = p.department || '미분류';
        deptData[d] = (deptData[d] || 0) + window.getBudgetBase(p);
    });

    const sorted = Object.entries(deptData).sort((a, b) => b[1] - a[1]).slice(0, 10);

    window.chartInstances['chart-dept-donut'] = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: sorted.map(x => x[0]),
            datasets: [{
                data: sorted.map(x => x[1]),
                backgroundColor: window.COLORS
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 }, color: getChartLabelColor() } },
                tooltip: { callbacks: { label: ctx => `${ctx.label}: ${window.formatBillion(ctx.raw)}` } }
            }
        }
    });
};

window.renderAccountType = function (projects) {
    const canvas = document.getElementById('chart-account-type');
    if (!canvas) return;
    destroyChart('chart-account-type');

    const accData = {};
    projects.forEach(p => {
        const t = p.account_type || '기타';
        accData[t] = (accData[t] || 0) + window.getBudgetBase(p);
    });

    window.chartInstances['chart-account-type'] = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: Object.keys(accData),
            datasets: [{
                data: Object.values(accData),
                backgroundColor: window.COLORS
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, color: getChartLabelColor() } }
            }
        }
    });
};

window.renderTypeDist = function (projects) {
    const canvas = document.getElementById('chart-type-dist');
    if (!canvas) return;
    destroyChart('chart-type-dist');

    const types = { 'R&D': 0, '정보화': 0, '일반': 0 };
    projects.forEach(p => {
        if (p.is_rnd === true || p.type === 'rnd') types['R&D']++;
        else if (p.is_informatization === true || p.type === 'info') types['정보화']++;
        else types['일반']++;
    });

    window.chartInstances['chart-type-dist'] = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: Object.keys(types),
            datasets: [{
                data: Object.values(types),
                backgroundColor: [window.COLORS[1], window.COLORS[2], window.COLORS[3]]
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { color: getChartLabelColor() } } }
        }
    });
};

window.renderStatusDist = function (projects) {
    const canvas = document.getElementById('chart-status-dist');
    if (!canvas) return;
    destroyChart('chart-status-dist');

    const counts = { '계속': 0, '신규': 0 };
    projects.forEach(p => {
        const s = p.status === '신규' ? '신규' : '계속';
        counts[s]++;
    });

    window.chartInstances['chart-status-dist'] = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                data: Object.values(counts),
                backgroundColor: [window.COLORS[5], window.COLORS[6]]
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { position: 'bottom', labels: { color: getChartLabelColor() } } }
        }
    });
};

window.renderTopChange = function (projects) {
    const withChange = projects.filter(p => window.getChangeAmount(p) !== 0);
    const sorted = [...withChange].sort((a, b) => window.getChangeAmount(b) - window.getChangeAmount(a));

    const top10Inc = sorted.slice(0, 10);
    const top10Dec = sorted.slice(-10).reverse();

    // Increase
    const canvasInc = document.getElementById('chart-top-increase');
    if (canvasInc) {
        destroyChart('chart-top-increase');
        window.chartInstances['chart-top-increase'] = new Chart(canvasInc, {
            type: 'bar',
            data: {
                labels: top10Inc.map(p => (p.project_name || p.name).substring(0, 12)),
                datasets: [{ data: top10Inc.map(p => window.getChangeAmount(p)), backgroundColor: '#34d39977', borderColor: '#34d399', borderWidth: 1, borderRadius: 4 }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => `증가: ${window.formatBillion(ctx.raw)} (${window.formatRate(window.getChangeRate(top10Inc[ctx.dataIndex]), top10Inc[ctx.dataIndex])})` } }
                },
                scales: {
                    x: { ticks: { color: getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: getChartGridColor() } },
                    y: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } }
                }
            }
        });
    }

    // Decrease
    const canvasDec = document.getElementById('chart-top-decrease');
    if (canvasDec) {
        destroyChart('chart-top-decrease');
        window.chartInstances['chart-top-decrease'] = new Chart(canvasDec, {
            type: 'bar',
            data: {
                labels: top10Dec.map(p => (p.project_name || p.name).substring(0, 12)),
                datasets: [{ data: top10Dec.map(p => window.getChangeAmount(p)), backgroundColor: '#f8717177', borderColor: '#f87171', borderWidth: 1, borderRadius: 4 }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => `감소: ${window.formatBillion(ctx.raw)} (${window.formatRate(window.getChangeRate(top10Dec[ctx.dataIndex]), top10Dec[ctx.dataIndex])})` } }
                },
                scales: {
                    x: { ticks: { color: getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: getChartGridColor() } },
                    y: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } }
                }
            }
        });
    }
};

window.renderChangeDist = function (projects) {
    const canvas = document.getElementById('chart-change-dist');
    if (!canvas) return;
    destroyChart('chart-change-dist');

    const bins = { '급락(<-50%)': 0, '감소(-50~-5%)': 0, '유지(-5~5%)': 0, '증가(5~50%)': 0, '급증(>50%)': 0 };
    projects.forEach(p => {
        const r = window.getChangeRate(p);
        if (r <= -50) bins['급락(<-50%)']++;
        else if (r <= -5) bins['감소(-50~-5%)']++;
        else if (r < 5) bins['유지(-5~5%)']++;
        else if (r < 50) bins['증가(5~50%)']++;
        else bins['급증(>50%)']++;
    });

    window.chartInstances['chart-change-dist'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: Object.keys(bins),
            datasets: [{
                data: Object.values(bins),
                backgroundColor: ['#ef444499', '#f8717199', '#94a3b899', '#34d39999', '#10b98199'],
                borderColor: ['#ef4444', '#f87171', '#94a3b8', '#34d399', '#10b981'],
                borderWidth: 1, borderRadius: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } },
                y: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

window.renderBudgetHist = function (projects) {
    const canvas = document.getElementById('chart-budget-hist');
    if (!canvas) return;
    destroyChart('chart-budget-hist');

    const bins = { '~10억': 0, '10~50억': 0, '50~100억': 0, '100~500억': 0, '500억~': 0 };
    projects.forEach(p => {
        const b = window.getBudgetBase(p);
        if (b < 1000) bins['~10억']++;
        else if (b < 5000) bins['10~50억']++;
        else if (b < 10000) bins['50~100억']++;
        else if (b < 50000) bins['100~500억']++;
        else bins['500억~']++;
    });

    window.chartInstances['chart-budget-hist'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: Object.keys(bins),
            datasets: [{ data: Object.values(bins), backgroundColor: (window.COLORS ? window.COLORS[2] : '#fbbf24') + 'cc', borderRadius: 4 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } },
                y: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

window.renderReqVsBudget = function (projects) {
    const canvas = document.getElementById('chart-req-vs-budget');
    if (!canvas) return;
    destroyChart('chart-req-vs-budget');

    const points = [];
    projects.forEach(p => {
        const req = p.budget?.['2026_request'];
        const bud = p.budget?.['2026_budget'];
        if (req && bud && req > 0) {
            points.push({ x: req, y: bud });
        }
    });

    const cut = points.filter(p => Math.abs(p.x - p.y) / p.x > 0.05);
    const same = points.filter(p => Math.abs(p.x - p.y) / p.x <= 0.05);

    window.chartInstances['chart-req-vs-budget'] = new Chart(canvas, {
        type: 'scatter',
        data: {
            datasets: [
                { label: '삭감/증액', data: cut, backgroundColor: (window.COLORS ? window.COLORS[3] : '#f87171') + '88', pointRadius: 4 },
                { label: '요구=편성', data: same, backgroundColor: (window.COLORS ? window.COLORS[0] : '#2563eb') + '44', pointRadius: 3 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { labels: { color: getChartLabelColor(), font: { size: 10 } } } },
            scales: {
                x: { type: 'logarithmic', title: { display: true, text: '요구액(백만원)', color: getChartLabelColor() }, ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } },
                y: { type: 'logarithmic', title: { display: true, text: '편성액(백만원)', color: getChartLabelColor() }, ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

// --- Advanced Charts ---

window.renderFieldBubble = function (projects) {
    const canvas = document.getElementById('chart-field-bubble');
    if (!canvas) return;
    destroyChart('chart-field-bubble');

    const fieldData = {};
    projects.forEach(p => {
        const fields = typeof window.classifyProject === 'function' ? window.classifyProject(p) : ['미분류'];
        fields.forEach(f => {
            if (!fieldData[f]) fieldData[f] = { count: 0, total: 0 };
            fieldData[f].count++;
            fieldData[f].total += window.getBudgetBase(p) / fields.length;
        });
    });

    const entries = Object.entries(fieldData).filter(([, v]) => v.total > 0).sort((a, b) => b[1].total - a[1].total);
    const maxTotal = Math.max(...entries.map(e => e[1].total), 1);

    const bubbleData = entries.map(([name, v], i) => ({
        x: v.count,
        y: v.total / v.count,
        r: Math.max(6, Math.sqrt(v.total / maxTotal) * 35),
        label: name,
        total: v.total
    }));

    window.chartInstances['chart-field-bubble'] = new Chart(canvas, {
        type: 'bubble',
        data: {
            datasets: bubbleData.map((d, i) => ({
                label: d.label,
                data: [{ x: d.x, y: d.y, r: d.r }],
                backgroundColor: (window.COLORS ? window.COLORS[i % window.COLORS.length] : '#2563eb') + '77',
                borderColor: (window.COLORS ? window.COLORS[i % window.COLORS.length] : '#2563eb'),
                borderWidth: 1
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'right', labels: { boxWidth: 10, font: { size: 10 }, color: getChartLabelColor() } },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const d = bubbleData[ctx.datasetIndex];
                            return [`${d.label}`, `사업 수: ${d.x}개`, `평균 예산: ${window.formatBillion(d.y)}`, `총 예산: ${window.formatBillion(d.total)}`];
                        }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: '사업 수', color: getChartLabelColor() }, ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } },
                y: { title: { display: true, text: '평균 예산', color: getChartLabelColor() }, ticks: { color: getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

window.renderWaterfall = function (projects) {
    const canvas = document.getElementById('chart-waterfall');
    if (!canvas) return;
    destroyChart('chart-waterfall');

    const deptChange = {};
    projects.forEach(p => {
        const d = p.department;
        if (!deptChange[d]) deptChange[d] = 0;
        deptChange[d] += window.getBudgetBase(p) - window.getBudgetPrev(p);
    });

    const sorted = Object.entries(deptChange).sort((a, b) => b[1] - a[1]);
    const topInc = sorted.filter(e => e[1] > 0).slice(0, 7);
    const topDec = sorted.filter(e => e[1] < 0).slice(-7).reverse();
    const items = [...topInc, ...topDec];

    const total2025 = projects.reduce((s, p) => s + window.getBudgetPrev(p), 0);
    const total2026 = projects.reduce((s, p) => s + window.getBudgetBase(p), 0);

    const labels = [`${window.BASE_YEAR - 1} 예산`, ...items.map(e => e[0].substring(0, 6)), '기타', `${window.BASE_YEAR} 예산`];
    const baseData = [], incData = [], decData = [];
    let running = total2025;

    baseData.push(0); incData.push(total2025); decData.push(0);

    items.forEach(([, change]) => {
        if (change >= 0) {
            baseData.push(running); incData.push(change); decData.push(0);
        } else {
            baseData.push(running + change); incData.push(0); decData.push(-change);
        }
        running += change;
    });

    const otherChange = (total2026 - total2025) - items.reduce((s, e) => s + e[1], 0);
    if (otherChange >= 0) {
        baseData.push(running); incData.push(otherChange); decData.push(0);
    } else {
        baseData.push(running + otherChange); incData.push(0); decData.push(-otherChange);
    }
    baseData.push(0); incData.push(total2026); decData.push(0);

    window.chartInstances['chart-waterfall'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { data: baseData, backgroundColor: 'transparent', stack: 'a' },
                { data: incData, backgroundColor: incData.map((v, i) => (i === 0 || i === labels.length - 1) ? (window.COLORS ? window.COLORS[0] : '#2563eb') + 'bb' : '#34d399bb'), stack: 'a', borderRadius: 3 },
                { data: decData, backgroundColor: '#f87171bb', stack: 'a', borderRadius: 3 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { filter: item => item.datasetIndex !== 0 } },
            scales: {
                x: { stacked: true, ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } },
                y: { stacked: true, ticks: { color: getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

window.renderDeptPortfolio = function (projects) {
    const canvas = document.getElementById('chart-dept-portfolio');
    if (!canvas) return;
    destroyChart('chart-dept-portfolio');

    const deptData = {};
    projects.forEach(p => {
        const d = p.department;
        if (!deptData[d]) deptData[d] = { rnd: 0, info: 0, gen: 0, total: 0 };
        const b = window.getBudgetBase(p);
        deptData[d].total += b;
        if (p.is_rnd) deptData[d].rnd += b;
        else if (p.is_informatization) deptData[d].info += b;
        else deptData[d].gen += b;
    });

    const sorted = Object.entries(deptData).sort((a, b) => b[1].total - a[1].total).slice(0, 15);

    window.chartInstances['chart-dept-portfolio'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: sorted.map(e => e[0].substring(0, 8)),
            datasets: [
                { label: 'R&D', data: sorted.map(e => e[1].rnd), backgroundColor: (window.COLORS ? window.COLORS[1] : '#7c3aed') + 'cc', stack: 'a', borderRadius: 2 },
                { label: '정보화', data: sorted.map(e => e[1].info), backgroundColor: (window.COLORS ? window.COLORS[2] : '#2563eb') + 'cc', stack: 'a', borderRadius: 2 },
                { label: '일반', data: sorted.map(e => e[1].gen), backgroundColor: (window.COLORS ? window.COLORS[4] : '#ca8a04') + 'cc', stack: 'a', borderRadius: 2 }
            ]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top', labels: { boxWidth: 10, color: getChartLabelColor() } } },
            scales: {
                x: { stacked: true, ticks: { color: getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: getChartGridColor() } },
                y: { stacked: true, ticks: { color: getChartLabelColor() }, grid: { display: false } }
            }
        }
    });
};

window.renderNewProjects = function (projects) {
    const canvas = document.getElementById('chart-new-projects');
    if (!canvas) return;
    destroyChart('chart-new-projects');

    const deptNew = {};
    projects.forEach(p => {
        const d = p.department;
        if (!deptNew[d]) deptNew[d] = { count: 0, budget: 0 };
        if (p.status === '신규') {
            deptNew[d].count++;
            deptNew[d].budget += window.getBudgetBase(p);
        }
    });

    const sorted = Object.entries(deptNew).sort((a, b) => b[1].budget - a[1].budget).slice(0, 15);

    window.chartInstances['chart-new-projects'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: sorted.map(e => e[0].substring(0, 8)),
            datasets: [
                { label: '신규 예산', data: sorted.map(e => e[1].budget), backgroundColor: '#10b981aa', borderRadius: 3, yAxisID: 'y' },
                { label: '신규 건수', data: sorted.map(e => e[1].count), type: 'line', borderColor: '#f59e0b', pointBackgroundColor: '#f59e0b', borderWidth: 2, yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top', labels: { color: getChartLabelColor() } } },
            scales: {
                x: { ticks: { color: getChartLabelColor() }, grid: { display: false } },
                y: { position: 'left', ticks: { color: getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: getChartGridColor() } },
                y1: { position: 'right', ticks: { color: '#f59e0b' }, grid: { display: false } }
            }
        }
    });
};

window.renderDomainHeatmap = function (projects) {
    const canvas = document.getElementById('chart-domain-heatmap');
    if (!canvas) return;
    destroyChart('chart-domain-heatmap');

    const depts = [...new Set(projects.map(p => p.department))].slice(0, 12);
    const domains = ['제조', '의료', '금융', '에너지', '공공', '교육', '안전', '기타'];

    const matrix = depts.map(d => {
        return domains.map(dom => {
            return projects.filter(p => p.department === d && (p.ai_domains || []).includes(dom)).length;
        });
    });

    window.chartInstances['chart-domain-heatmap'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: depts.map(d => d.substring(0, 6)),
            datasets: domains.map((dom, i) => ({
                label: dom,
                data: matrix.map(row => row[i]),
                backgroundColor: (window.COLORS ? window.COLORS[i % window.COLORS.length] : '#1e3a5f') + '99',
                stack: 'a'
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 9 }, color: getChartLabelColor() } } },
            scales: {
                x: { stacked: true, ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } },
                y: { stacked: true, ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

window.renderSubProjectWidgets = function (projects) {
    const canvasHist = document.getElementById('chart-sub-hist');
    if (canvasHist) {
        destroyChart('chart-sub-hist');
        const subs = [];
        projects.forEach(p => (p.sub_projects || []).forEach(s => { if (s.budget_base > 0) subs.push(s.budget_base); }));
        const bins = [1000, 5000, 10000, 50000, Infinity];
        const labels = ['~10억', '10~50억', '50~100억', '100~500억', '500억~'];
        const counts = labels.map((_, i) => {
            const min = i === 0 ? 0 : bins[i - 1];
            const max = bins[i];
            return subs.filter(v => v >= min && v < max).length;
        });
        window.chartInstances['chart-sub-hist'] = new Chart(canvasHist, {
            type: 'bar',
            data: { labels, datasets: [{ data: counts, backgroundColor: (window.COLORS ? window.COLORS[0] : '#2563eb') + 'aa', borderRadius: 4 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: getChartLabelColor() }, grid: { display: false } },
                    y: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
                }
            }
        });
    }

    // Concentration (HHI-like for subprojects)
    const canvasConc = document.getElementById('chart-concentration');
    if (canvasConc) {
        destroyChart('chart-concentration');
        const conc = projects.filter(p => (p.sub_projects || []).length > 1).map(p => {
            const total = p.sub_projects.reduce((s, x) => s + x.budget_base, 0);
            const max = Math.max(...p.sub_projects.map(x => x.budget_base));
            return { name: (p.project_name || p.name).substring(0, 15), pct: total > 0 ? (max / total * 100) : 0 };
        }).sort((a, b) => b.pct - a.pct).slice(0, 15);

        window.chartInstances['chart-concentration'] = new Chart(canvasConc, {
            type: 'bar',
            data: {
                labels: conc.map(c => c.name),
                datasets: [{ data: conc.map(c => c.pct), backgroundColor: (window.COLORS ? window.COLORS[5] : '#ca8a04') + 'aa', borderRadius: 3 }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${ctx.raw.toFixed(1)}%` } } },
                scales: {
                    x: { max: 100, ticks: { color: getChartLabelColor(), callback: v => v + '%' }, grid: { color: getChartGridColor() } },
                    y: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } }
                }
            }
        });
    }
};

window.renderAnomalyDetection = function (projects) {
    const container = document.getElementById('anomaly-list-container');
    if (!container) return;

    const anomalies = projects.filter(p => Math.abs(window.getChangeRate(p)) >= 50).sort((a, b) => Math.abs(window.getChangeRate(b)) - Math.abs(window.getChangeRate(a)));

    let html = `<table class="bi-table" style="width:100%;font-size:12px">
    <thead><tr><th>사업명</th><th class="num">2026</th><th class="num">증감률</th></tr></thead>
    <tbody>`;
    anomalies.slice(0, 15).forEach(p => {
        const cr = window.getChangeRate(p);
        html += `<tr onclick="window.showProjectModal(${p.id})">
      <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p.project_name || p.name}</td>
      <td class="num">${window.formatBillion(window.getBudgetBase(p))}</td>
      <td class="num" style="color:${cr > 0 ? 'var(--green)' : 'var(--red)'};font-weight:700">${window.formatRate(cr, p)}</td>
    </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;

    const canvas = document.getElementById('chart-anomaly-hist');
    if (canvas) {
        destroyChart('chart-anomaly-hist');
        const bins = [-100, -50, -20, 0, 20, 50, 100, Infinity];
        const labels = ['<-50%', '-50~-20%', '-20~0%', '0~20%', '20~50%', '50~100%', '>100%'];
        const counts = labels.map((_, i) => {
            const min = bins[i], max = bins[i + 1];
            return projects.filter(p => { const r = window.getChangeRate(p); return r >= min && r < max; }).length;
        });
        window.chartInstances['chart-anomaly-hist'] = new Chart(canvas, {
            type: 'bar',
            data: { labels, datasets: [{ data: counts, backgroundColor: labels.map((_, i) => i < 3 ? '#f87171aa' : (i < 4 ? '#94a3b8aa' : '#34d399aa')), borderRadius: 3 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: getChartLabelColor(), font: { size: 9 } }, grid: { display: false } },
                    y: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
                }
            }
        });
    }
};

window.renderHHIAnalysis = function (projects) {
    const total = projects.reduce((s, p) => s + window.getBudgetBase(p), 0);
    if (total <= 0) return;

    const deptBudgets = {};
    projects.forEach(p => {
        const d = p.department;
        deptBudgets[d] = (deptBudgets[d] || 0) + window.getBudgetBase(p);
    });

    const shares = Object.values(deptBudgets).map(v => v / total);
    const hhi = Math.round(shares.reduce((s, v) => s + v * v, 0) * 10000);

    const container = document.getElementById('hhi-container');
    if (container) {
        let color = 'var(--green)';
        let status = '분산형';
        if (hhi > 2500) { color = 'var(--red)'; status = '고집중'; }
        else if (hhi > 1500) { color = 'var(--yellow)'; status = '중집중'; }

        container.innerHTML = `<div style="text-align:center">
      <div style="font-size:24px;font-weight:800;color:${color}">${hhi}</div>
      <div style="font-size:11px;color:var(--text-secondary)">HHI 부처 집중도 (${status})</div>
    </div>`;
    }

    const canvas = document.getElementById('chart-hhi-dept');
    if (canvas) {
        destroyChart('chart-hhi-dept');
        const top5 = Object.entries(deptBudgets).sort((a, b) => b[1] - a[1]).slice(0, 5);
        window.chartInstances['chart-hhi-dept'] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: top5.map(x => x[0].substring(0, 8)),
                datasets: [{ data: top5.map(x => (x[1] / total * 100).toFixed(1)), backgroundColor: (window.COLORS ? window.COLORS.slice(0, 5) : []), borderRadius: 3 }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw + '%' } } },
                scales: {
                    x: { max: 100, ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { color: getChartGridColor() } },
                    y: { ticks: { color: getChartLabelColor(), font: { size: 10 } }, grid: { display: false } }
                }
            }
        });
    }
};

window.renderBudgetDistDetail = function (projects) {
    const canvas = document.getElementById('chart-budget-dist-detail');
    if (!canvas) return;
    destroyChart('chart-budget-dist-detail');

    const bins = [100, 500, 1000, 5000, 10000, 50000];
    const labels = ['<1억', '1~5억', '5~10억', '10~50억', '50~100억', '100~500억', '>500억'];
    const counts = labels.map((_, i) => {
        const min = i === 0 ? 0 : bins[i - 1];
        const max = bins[i] || Infinity;
        return projects.filter(p => { const b = window.getBudgetBase(p); return b >= min && b < max; }).length;
    });

    window.chartInstances['chart-budget-dist-detail'] = new Chart(canvas, {
        type: 'bar',
        data: { labels, datasets: [{ data: counts, backgroundColor: (window.COLORS ? window.COLORS[0] : '#2563eb') + 'aa', borderRadius: 4 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: getChartLabelColor(), font: { size: 9 } }, grid: { display: false } },
                y: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } }
            }
        }
    });
};

window.renderWasteRisk = function (projects) {
    const container = document.getElementById('waste-risk-container');
    if (!container) return;

    const scored = projects.map(p => {
        const cr = Math.abs(window.getChangeRate(p));
        let score = 0;
        if (cr >= 100) score += 40;
        else if (cr >= 50) score += 20;
        if (p.status === '신규') score += 20;
        if (window.getBudgetBase(p) >= 10000) score += 20;
        if (window.getBudgetBase(p) === 0) score += 10;
        return { p, score };
    }).sort((a, b) => b.score - a.score);

    const high = scored.filter(x => x.score >= 50);

    let html = `<table class="bi-table" style="width:100%;font-size:11px">
    <thead><tr><th>사업명</th><th>부처</th><th class="num">리스크</th></tr></thead>
    <tbody>`;
    high.slice(0, 12).forEach(x => {
        html += `<tr onclick="window.showProjectModal(${x.p.id})">
      <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${x.p.project_name || x.p.name}</td>
      <td>${x.p.department}</td>
      <td class="num" style="color:var(--red);font-weight:700">${x.score}</td>
    </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
};

window.renderGlobalBenchmark = function () {
    const canvas = document.getElementById('chart-global-budget');
    if (!canvas) return;
    destroyChart('chart-global-budget');

    const data = [
        { country: '미국', val: 32.0 }, { country: '중국', val: 15.3 }, { country: '영국', val: 3.5 },
        { country: 'EU', val: 4.2 }, { country: '일본', val: 2.8 }, { country: '한국', val: 2.1 }
    ].sort((a, b) => b.val - a.val);

    window.chartInstances['chart-global-budget'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.map(d => d.country),
            datasets: [{
                data: data.map(d => d.val),
                backgroundColor: data.map(d => d.country === '한국' ? (window.COLORS ? window.COLORS[0] : '#2563eb') : '#94a3b899'),
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, title: { display: true, text: 'AI 예산 규모 (USD Billion)', color: getChartLabelColor(), font: { size: 12 } } },
            scales: {
                x: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } },
                y: { ticks: { color: getChartLabelColor(), font: { weight: (ctx) => data[ctx.index]?.country === '한국' ? 'bold' : 'normal' } }, grid: { display: false } }
            }
        }
    });

    const canvasGdp = document.getElementById('chart-global-gdp');
    if (canvasGdp) {
        destroyChart('chart-global-gdp');
        const gdpData = [
            { country: '미국', val: 0.12 }, { country: '중국', val: 0.09 }, { country: '영국', val: 0.10 },
            { country: '한국', val: 0.10 }, { country: '일본', val: 0.06 }
        ].sort((a, b) => b.val - a.val);

        window.chartInstances['chart-global-gdp'] = new Chart(canvasGdp, {
            type: 'bar',
            data: {
                labels: gdpData.map(d => d.country),
                datasets: [{
                    data: gdpData.map(d => d.val),
                    backgroundColor: gdpData.map(d => d.country === '한국' ? (window.COLORS ? window.COLORS[0] : '#2563eb') : '#94a3b899'),
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, title: { display: true, text: 'GDP 대비 AI 투자 비율 (%)', color: getChartLabelColor(), font: { size: 12 } } },
                scales: {
                    x: { ticks: { color: getChartLabelColor() }, grid: { color: getChartGridColor() } },
                    y: { ticks: { color: getChartLabelColor() }, grid: { display: false } }
                }
            }
        });
    }
};

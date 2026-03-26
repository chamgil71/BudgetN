/**
 * KAIB2026 Department Tab Logic
 */

let deptSort = { key: 'budget', dir: 'desc' };
let currentDept = '';

window.renderDepartment = function () {
    if (!window.DATA) return;
    const projects = window.DATA.projects;

    // Department bar chart
    const deptData = {};
    projects.forEach(p => {
        if (!deptData[p.department]) deptData[p.department] = { count: 0, budget: 0, budget2025: 0, budget2026_existing: 0, budget2025_existing: 0 };
        deptData[p.department].count++;
        deptData[p.department].budget += window.getBudgetBase(p);
        deptData[p.department].budget2025 += window.getBudgetPrev(p);
        const b25 = window.getBudgetPrev(p), b26 = window.getBudgetBase(p);
        if (b25 > 0 || b26 === 0) {
            deptData[p.department].budget2026_existing += b26;
            deptData[p.department].budget2025_existing += b25;
        }
    });

    const sortedDepts = Object.entries(deptData).sort((a, b) => b[1].budget - a[1].budget);
    const topDepts = sortedDepts.slice(0, 20);

    window.destroyChart('chart-dept-bar');
    window.chartInstances['chart-dept-bar'] = new Chart(document.getElementById('chart-dept-bar'), {
        type: 'bar',
        data: {
            labels: topDepts.map(d => d[0].substring(0, 10)),
            datasets: [
                { label: `${window.BASE_YEAR} 예산`, data: topDepts.map(d => d[1].budget), backgroundColor: window.COLORS[0] + '99', borderColor: window.COLORS[0], borderWidth: 1, borderRadius: 4 },
                { label: '2025 예산', data: topDepts.map(d => d[1].budget2025), backgroundColor: window.COLORS[4] + '44', borderColor: window.COLORS[4] + '88', borderWidth: 1, borderRadius: 4 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: window.getChartLabelColor(), font: { size: 11, family: 'Pretendard Variable' } } },
                tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${window.formatBillion(ctx.raw)}` } }
            },
            scales: {
                x: { ticks: { color: window.getChartLabelColor(), font: { size: 10 }, maxRotation: 45 }, grid: { display: false } },
                y: { ticks: { color: window.getChartLabelColor(), callback: v => window.formatBillion(v) }, grid: { color: window.getChartGridColor() } }
            }
        }
    });

    // Scatter plot (D3)
    window.renderScatterPlot(deptData);

    // Change rate chart
    const deptChanges = sortedDepts.map(([name, d]) => ({
        name: name.substring(0, 10),
        rate: d.budget2025_existing > 0 ? ((d.budget2026_existing - d.budget2025_existing) / d.budget2025_existing * 100) : 0
    })).sort((a, b) => b.rate - a.rate);

    window.destroyChart('chart-dept-change');
    window.chartInstances['chart-dept-change'] = new Chart(document.getElementById('chart-dept-change'), {
        type: 'bar',
        data: {
            labels: deptChanges.map(d => d.name),
            datasets: [{
                data: deptChanges.map(d => d.rate),
                backgroundColor: deptChanges.map(d => d.rate >= 0 ? '#34d39966' : '#f8717166'),
                borderColor: deptChanges.map(d => d.rate >= 0 ? '#34d399' : '#f87171'),
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `증감률: ${window.formatRate(ctx.raw)}` } } },
            scales: {
                x: { ticks: { color: window.getChartLabelColor(), font: { size: 10 }, maxRotation: 45 }, grid: { display: false } },
                y: { ticks: { color: window.getChartLabelColor(), callback: v => v + '%' }, grid: { color: window.getChartGridColor() } }
            }
        }
    });
};

window.renderScatterPlot = function (deptData) {
    const container = document.getElementById('scatter-container');
    if (!container) return;
    container.innerHTML = '';

    const entries = Object.entries(deptData);
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = 360 - margin.top - margin.bottom;

    const svg = d3.select(container).append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
        .domain([0, d3.max(entries, d => d[1].count) * 1.1])
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(entries, d => d[1].budget) * 1.1])
        .range([height, 0]);

    const rSize = d3.scaleSqrt()
        .domain([0, d3.max(entries, d => d[1].budget)])
        .range([4, 20]);

    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(5))
        .selectAll('text').style('fill', window.getChartLabelColor()).style('font-size', '10px');

    svg.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(v => window.formatBillion(v)))
        .selectAll('text').style('fill', window.getChartLabelColor()).style('font-size', '10px');

    svg.selectAll('.domain, .tick line').style('stroke', '#2a3a4e');

    // Axis labels
    svg.append('text').attr('x', width / 2).attr('y', height + 35).attr('text-anchor', 'middle').style('fill', window.getChartLabelColor()).style('font-size', '11px').text('사업 수');
    svg.append('text').attr('transform', 'rotate(-90)').attr('x', -height / 2).attr('y', -45).attr('text-anchor', 'middle').style('fill', window.getChartLabelColor()).style('font-size', '11px').text('예산 규모');

    const tooltip = d3.select('#tooltip');

    svg.selectAll('circle')
        .data(entries)
        .join('circle')
        .attr('cx', d => x(d[1].count))
        .attr('cy', d => y(d[1].budget))
        .attr('r', d => rSize(d[1].budget))
        .attr('fill', (d, i) => window.COLORS[i % window.COLORS.length] + '88')
        .attr('stroke', (d, i) => window.COLORS[i % window.COLORS.length])
        .attr('stroke-width', 1.5)
        .style('cursor', 'pointer')
        .on('mouseover', (e, d) => {
            tooltip.style('display', 'block')
                .html(`<strong>${d[0]}</strong><br>사업 수: ${d[1].count}개<br>예산: ${window.formatBillion(d[1].budget)}`)
                .style('left', (e.clientX + 12) + 'px')
                .style('top', (e.clientY - 10) + 'px');
        })
        .on('mousemove', (e) => {
            tooltip.style('left', (e.clientX + 12) + 'px').style('top', (e.clientY - 10) + 'px');
        })
        .on('mouseout', () => tooltip.style('display', 'none'))
        .on('click', (e, d) => {
            window.showDeptProjects(d[0]);
        });
};

window.showDeptProjects = function (dept) {
    if (dept) { currentDept = dept; deptSort = { key: 'budget', dir: 'desc' }; }
    const card = document.getElementById('dept-project-list-card');
    if (!card) return;
    card.style.display = 'block';
    const titleEl = document.getElementById('dept-project-list-title');
    if (titleEl) titleEl.textContent = `${currentDept} 사업 목록`;

    const deptProjects = window.DATA.projects.filter(p => p.department === currentDept);
    const dir = deptSort.dir === 'asc' ? 1 : -1;
    switch (deptSort.key) {
        case 'name': deptProjects.sort((a, b) => dir * (a.project_name || a.name).localeCompare(b.project_name || b.name)); break;
        case 'budget': deptProjects.sort((a, b) => dir * (window.getBudgetBase(a) - window.getBudgetBase(b))); break;
        case 'change': deptProjects.sort((a, b) => dir * ((window.getChangeRate(a) || 0) - (window.getChangeRate(b) || 0))); break;
        case 'type': deptProjects.sort((a, b) => dir * window.getProjectType(a).localeCompare(window.getProjectType(b))); break;
        case 'status': deptProjects.sort((a, b) => dir * (a.status || '').localeCompare(b.status || '')); break;
        default: deptProjects.sort((a, b) => window.getBudgetBase(b) - window.getBudgetBase(a));
    }

    function dsi(key) {
        if (deptSort.key !== key) return ' <span style="opacity:0.3">⇅</span>';
        return deptSort.dir === 'asc' ? ' ▲' : ' ▼';
    }
    const ths = 'cursor:pointer;user-select:none;white-space:nowrap';

    let html = `<table class="data-table"><thead><tr>
    <th style="${ths}" onclick="window.sortDeptCol('name')">사업명${dsi('name')}</th>
    <th class="num" style="${ths}" onclick="window.sortDeptCol('budget')">${window.BASE_YEAR} 예산${dsi('budget')}</th>
    <th class="num" style="${ths}" onclick="window.sortDeptCol('change')">증감률${dsi('change')}</th>
    <th style="${ths}" onclick="window.sortDeptCol('type')">유형${dsi('type')}</th>
    <th style="${ths}" onclick="window.sortDeptCol('status')">상태${dsi('status')}</th>
  </tr></thead><tbody>`;
    deptProjects.forEach(p => {
        const change = window.getChangeRate(p);
        html += `<tr style="cursor:pointer" onclick="window.showProjectModal(${p.id})">
      <td>${p.project_name || p.name}</td>
      <td class="num">${window.formatBillion(window.getBudgetBase(p))}</td>
      <td class="num ${change >= 0 ? 'text-positive' : 'text-negative'}">${window.formatRate(change, p)}</td>
      <td><span class="badge badge-${window.getProjectTypeClass(p)}">${window.getProjectType(p)}</span></td>
      <td>${p.status || '-'}</td>
    </tr>`;
    });
    html += '</tbody></table>';
    const listEl = document.getElementById('dept-project-list');
    if (listEl) listEl.innerHTML = html;
};

window.sortDeptCol = function (key) {
    if (deptSort.key === key) {
        deptSort.dir = deptSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
        deptSort = { key, dir: ['name', 'type', 'status'].includes(key) ? 'asc' : 'desc' };
    }
    window.showDeptProjects();
};

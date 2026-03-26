/**
 * KAIB2026 Field Analysis Tab Logic
 */

window.renderField = function () {
    if (!window.DATA) return;
    window.renderTreemap();
    window.renderFieldHeatmap();
};

window.renderTreemap = function () {
    const container = document.getElementById('treemap-container');
    if (!container) return;
    container.innerHTML = '';

    const fieldBudgets = {};
    window.DATA.projects.forEach(p => {
        const fields = window.classifyProject(p);
        const budget = window.getBudgetBase(p);
        if (!fields || fields.length === 0) return;

        fields.forEach(f => {
            let fieldName = '기타';
            if (typeof f === 'string') fieldName = f;
            else if (f && typeof f === 'object') {
                fieldName = f.name || f.themeId || f.label || f.category || JSON.stringify(f);
            }

            if (!fieldBudgets[fieldName]) fieldBudgets[fieldName] = { budget: 0, count: 0, projects: [] };
            // 분야가 여러 개인 경우 산술적으로 배분하여 전체 합계가 맞도록 수정 (Pro-rata)
            fieldBudgets[fieldName].budget += (budget / fields.length);
            fieldBudgets[fieldName].count++;
            fieldBudgets[fieldName].projects.push(p);
        });
    });

    const data = {
        name: 'root',
        children: Object.entries(fieldBudgets)
            .filter(([name, v]) => v.budget > 0 && name && name !== 'undefined')
            .map(([name, v]) => ({
                name: String(name),
                value: v.budget,
                count: v.count
            }))
            .sort((a, b) => b.value - a.value)
    };

    const width = container.clientWidth || 800;
    const height = 500;

    // Use d3 global which should be loaded in index.html
    const root = d3.hierarchy(data).sum(d => d.value);
    d3.treemap().size([width, height]).padding(3).round(true)(root);

    const tooltip = d3.select('#tooltip');

    root.leaves().forEach((leaf, i) => {
        const div = document.createElement('div');
        div.className = 'treemap-cell';
        div.style.left = leaf.x0 + 'px';
        div.style.top = leaf.y0 + 'px';
        div.style.width = (leaf.x1 - leaf.x0) + 'px';
        div.style.height = (leaf.y1 - leaf.y0) + 'px';
        div.style.background = window.COLORS[i % window.COLORS.length] + 'cc';

        const cellWidth = leaf.x1 - leaf.x0;
        const cellHeight = leaf.y1 - leaf.y0;
        const fontSize = Math.max(11, Math.min(20, Math.floor(cellWidth / 8), Math.floor(cellHeight / 4)));
        div.style.fontSize = fontSize + 'px';

        if (cellWidth > 50 && cellHeight > 28) {
            div.innerHTML = `<div class="cell-name">${leaf.data.name}</div>${cellHeight > 45 ? `<div class="cell-value">${window.formatBillion(leaf.data.value)} (${leaf.data.count}건)</div>` : ''}`;
        }

        div.addEventListener('mouseover', e => {
            tooltip.style('display', 'block')
                .html(`<strong>${leaf.data.name}</strong><br>예산: ${window.formatBillion(leaf.data.value)}<br>사업 수: ${leaf.data.count}건`)
                .style('left', (e.clientX + 12) + 'px')
                .style('top', (e.clientY - 10) + 'px');
        });
        div.addEventListener('mousemove', e => {
            tooltip.style('left', (e.clientX + 12) + 'px').style('top', (e.clientY - 10) + 'px');
        });
        div.addEventListener('mouseout', () => tooltip.style('display', 'none'));
        div.addEventListener('click', () => {
            tooltip.style('display', 'none');
            if (typeof window.navigateToField === 'function') window.navigateToField(leaf.data.name);
        });
        div.style.cursor = 'pointer';
        container.appendChild(div);
    });
};

window.renderFieldHeatmap = function () {
    const container = document.getElementById('field-heatmap-container');
    if (!container) return;

    const fieldDeptBudget = {};
    const allFields = new Set();
    const allDepts = new Set();

    window.DATA.projects.forEach(p => {
        const fields = window.classifyProject(p);
        const budget = window.getBudgetBase(p);
        if (!fields || fields.length === 0) return;
        const splitBudget = budget / fields.length;
        
        fields.forEach(f => {
            let fieldName = '기타';
            if (typeof f === 'string') fieldName = f;
            else if (f && typeof f === 'object') {
                fieldName = f.name || f.themeId || f.label || f.category || JSON.stringify(f);
            }
            
            allFields.add(fieldName);
            allDepts.add(p.department);
            const key = `${fieldName}|${p.department}`;
            fieldDeptBudget[key] = (fieldDeptBudget[key] || 0) + splitBudget;
        });
    });

    const fields = [...allFields].sort();
    const depts = [...allDepts].sort((a, b) => {
        const aTotal = fields.reduce((s, f) => s + (fieldDeptBudget[`${f}|${a}`] || 0), 0);
        const bTotal = fields.reduce((s, f) => s + (fieldDeptBudget[`${f}|${b}`] || 0), 0);
        return bTotal - aTotal;
    }).slice(0, 20);

    const maxVal = Math.max(...Object.values(fieldDeptBudget), 1);

    let html = '<table class="data-table" style="font-size:11px"><thead><tr><th style="min-width:80px">부처 \\ 분야</th>';
    fields.forEach(f => {
        html += `<th style="text-align:center;font-size:10px;padding:6px 4px;cursor:pointer" onclick="window.navigateToField('${f}')">${f}</th>`;
    });
    html += '</tr></thead><tbody>';

    depts.forEach(dept => {
        html += `<tr><td style="white-space:nowrap;font-size:11px">${dept.substring(0, 8)}</td>`;
        fields.forEach(f => {
            const val = fieldDeptBudget[`${f}|${dept}`] || 0;
            const intensity = val > 0 ? Math.max(0.1, val / maxVal) : 0;
            const bg = val > 0 ? `rgba(74,158,255,${intensity})` : 'transparent';
            html += `<td style="text-align:center;background:${bg};padding:6px 4px;font-size:10px;cursor:pointer"
                onmouseover="window.showTooltip(event,'${dept} - ${f}: ${window.formatBillion(val)}')"
                onmouseout="window.hideTooltip()"
                onclick="window.navigateToField('${f}','${dept}')">${val > 0 ? window.formatBillion(val) : ''}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
};

window.navigateToField = function (field, dept) {
    // Navigate to projects tab with filter
    const fieldSel = document.getElementById('project-field-filter');
    const deptSel = document.getElementById('project-dept-filter');

    if (fieldSel) fieldSel.value = field;
    if (deptSel) deptSel.value = dept || '';

    window.switchToTab('projects');
    if (typeof window.renderProjects === 'function') window.renderProjects();
};

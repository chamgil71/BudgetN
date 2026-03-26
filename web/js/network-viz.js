/**
 * KAIB2026 Network Visualization (Sankey Diagram)
 */

function renderSankey() {
  const container = document.getElementById('sankey-container');
  if (!container) return;
  container.innerHTML = '';

  // Build sankey data: Department -> Field -> Type
  const links = [];
  const nodeSet = new Set();
  const nodeProjects = {};

  if (!DATA) return;

  DATA.projects.forEach(p => {
    const dept = p.department;
    const deptShort = dept.substring(0, 8);
    const fields = classifyProject(p);
    const type = getProjectType(p);
    const budget = getBudgetBase(p);
    if (budget <= 0) return;

    fields.forEach(field => {
      const b = budget / fields.length;
      const deptNode = 'D:' + deptShort;
      const fieldNode = 'F:' + field;
      const typeNode = 'T:' + type;

      nodeSet.add(deptNode);
      nodeSet.add(fieldNode);
      nodeSet.add(typeNode);

      if (!nodeProjects[deptNode]) nodeProjects[deptNode] = new Set();
      if (!nodeProjects[fieldNode]) nodeProjects[fieldNode] = new Set();
      if (!nodeProjects[typeNode]) nodeProjects[typeNode] = new Set();
      nodeProjects[deptNode].add(p.id);
      nodeProjects[fieldNode].add(p.id);
      nodeProjects[typeNode].add(p.id);

      links.push({ source: deptNode, target: fieldNode, value: b });
      links.push({ source: fieldNode, target: typeNode, value: b });
    });
  });

  const linkMap = {};
  links.forEach(l => {
    const key = `${l.source}|${l.target}`;
    if (!linkMap[key]) linkMap[key] = { source: l.source, target: l.target, value: 0 };
    linkMap[key].value += l.value;
  });

  const aggLinks = Object.values(linkMap).filter(l => l.value > 0);
  const nodes = [...nodeSet].map(name => ({ name }));

  const width = container.clientWidth || 1100;
  const height = Math.max(700, nodes.length * 16);

  const svg = d3.select(container).append('svg')
    .attr('width', width)
    .attr('height', height);

  const columns = [
    nodes.filter(n => n.name.startsWith('D:')),
    nodes.filter(n => n.name.startsWith('F:')),
    nodes.filter(n => n.name.startsWith('T:'))
  ];

  const labelPad = [140, 0, 120];
  const colX = [labelPad[0] + 20, width / 2, width - labelPad[2] - 20];
  const nodeWidth = 10;

  columns.forEach((col, ci) => {
    col.forEach(n => {
      const nodeLinks = aggLinks.filter(l => l.source === n.name || l.target === n.name);
      n.value = nodeLinks.reduce((s, l) => s + l.value, 0) / 2;
    });
    col.sort((a, b) => b.value - a.value);

    const totalValue = col.reduce((s, n) => s + n.value, 0);
    const padding = 3;
    const usableHeight = height - 40 - padding * (col.length - 1);

    let y = 30;
    col.forEach(n => {
      const h = Math.max(4, (n.value / totalValue) * usableHeight);
      n.x = colX[ci];
      n.y = y;
      n.height = h;
      y += h + padding;
    });
  });

  const allNodes = columns.flat();
  const maxLinkVal = Math.max(...aggLinks.map(l => l.value));

  aggLinks.forEach(l => {
    const source = allNodes.find(n => n.name === l.source);
    const target = allNodes.find(n => n.name === l.target);
    if (!source || !target) return;

    const thickness = Math.max(1, (l.value / maxLinkVal) * 30);
    const sourceColor = source.name.startsWith('D:') ? '#4a9eff' : source.name.startsWith('F:') ? '#a78bfa' : '#34d399';
    const sx = source.x + nodeWidth;
    const tx = target.x;
    const sy = source.y + source.height / 2;
    const ty = target.y + target.height / 2;
    const mx = (sx + tx) / 2;

    svg.append('path')
      .attr('d', `M${sx},${sy} C${mx},${sy} ${mx},${ty} ${tx},${ty}`)
      .attr('fill', 'none')
      .attr('stroke', sourceColor)
      .attr('stroke-width', thickness)
      .attr('stroke-opacity', 0.15)
      .on('mouseover', function (e) {
        d3.select(this).attr('stroke-opacity', 0.5);
        d3.select('#tooltip').style('display', 'block')
          .html(`${l.source.substring(2)} → ${l.target.substring(2)}<br><b>${formatBillion(l.value)}</b>`)
          .style('left', (e.clientX + 12) + 'px').style('top', (e.clientY - 10) + 'px');
      })
      .on('mouseout', function () {
        d3.select(this).attr('stroke-opacity', 0.15);
        d3.select('#tooltip').style('display', 'none');
      });
  });

  const colorMap = { 'D:': '#4a9eff', 'F:': '#a78bfa', 'T:': '#34d399' };

  allNodes.forEach(n => {
    const prefix = n.name.substring(0, 2);
    const color = colorMap[prefix] || '#8899aa';
    const label = n.name.substring(2);
    const ids = nodeProjects[n.name] ? [...nodeProjects[n.name]] : [];

    const g = svg.append('g').attr('cursor', 'pointer')
      .on('click', () => showSankeyDetail(label, prefix, ids));

    g.append('rect')
      .attr('x', n.x)
      .attr('y', n.y)
      .attr('width', nodeWidth)
      .attr('height', n.height)
      .attr('fill', color)
      .attr('rx', 3);

    g.on('mouseover', function () { d3.select(this).select('rect').attr('fill-opacity', 0.7); })
      .on('mouseout', function () { d3.select(this).select('rect').attr('fill-opacity', 1); });

    if (n.height > 10) {
      const textX = prefix === 'D:' ? n.x - 6 : prefix === 'T:' ? n.x + nodeWidth + 6 : n.x + nodeWidth / 2;
      const anchor = prefix === 'D:' ? 'end' : prefix === 'T:' ? 'start' : 'middle';
      const displayLabel = `${label} (${formatBillion(n.value)})`;

      g.append('text')
        .attr('x', textX)
        .attr('y', n.y + n.height / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', anchor)
        .attr('fill', getChartLabelColor())
        .attr('font-size', n.height > 20 ? '12px' : '10px')
        .attr('font-family', 'Pretendard Variable')
        .text(displayLabel);
    }
  });

  const headers = ['부처', '분야', '사업유형'];
  colX.forEach((x, i) => {
    svg.append('text')
      .attr('x', x + nodeWidth / 2)
      .attr('y', 16)
      .attr('text-anchor', 'middle')
      .attr('fill', getChartLabelColor())
      .attr('font-size', '13px')
      .attr('font-weight', '700')
      .attr('font-family', 'Pretendard Variable')
      .text(headers[i]);
  });
}

function showSankeyDetail(label, prefix, projectIds) {
  const modal = document.getElementById('sankey-detail-modal');
  const title = document.getElementById('sankey-detail-title');
  const body = document.getElementById('sankey-detail-body');
  if (!modal || !DATA) return;

  const typeLabel = prefix === 'D:' ? '부처' : prefix === 'F:' ? '분야' : '사업유형';
  title.textContent = `${typeLabel}: ${label}`;

  const projectMap = {};
  DATA.projects.forEach(p => { projectMap[p.id] = p; });
  const projects = projectIds.map(id => projectMap[id]).filter(Boolean);
  projects.sort((a, b) => (getBudgetBase(b) || 0) - (getBudgetBase(a) || 0));

  const totalBudget = projects.reduce((s, p) => s + (getBudgetBase(p) || 0), 0);

  let html = `<div style="margin-bottom:12px;font-size:13px;color:var(--text-secondary)">
    ${projects.length}개 사업 · 총 ${formatBillion(totalBudget)}
  </div>`;
  html += `<table style="width:100%;border-collapse:collapse;font-size:12px">
    <thead><tr style="background:var(--bg-main)">
      <th style="padding:8px;text-align:left">사업명</th>
      <th style="padding:8px;text-align:left;white-space:nowrap">부처</th>
      <th style="padding:8px;text-align:right;white-space:nowrap">${window.BASE_YEAR} 예산</th>
      <th style="padding:8px;text-align:right;white-space:nowrap">증감률</th>
      <th style="padding:8px;text-align:center;white-space:nowrap">유형</th>
    </tr></thead><tbody>`;

  projects.forEach(p => {
    const b = getBudgetBase(p) || 0;
    const cr = getChangeRate(p);
    html += `<tr style="border-bottom:1px solid var(--border);cursor:pointer" onclick="document.getElementById('sankey-detail-modal').style.display='none';document.body.style.overflow='';showProjectModal(${p.id})">
      <td style="padding:6px 8px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${p.project_name}">${p.project_name}</td>
      <td style="padding:6px 8px;white-space:nowrap;font-size:11px">${p.department}</td>
      <td style="padding:6px 8px;text-align:right;font-weight:600">${formatBillion(b)}</td>
      <td style="padding:6px 8px;text-align:right;color:${cr >= 0 ? 'var(--green)' : 'var(--red)'}">${formatRate(cr, p)}</td>
      <td style="padding:6px 8px;text-align:center"><span class="tag ${getProjectTypeClass(p)}">${getProjectType(p)}</span></td>
    </tr>`;
  });
  html += '</tbody></table>';

  body.innerHTML = html;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

// Global scope initialization
window.renderSankey = renderSankey;
window.showSankeyDetail = showSankeyDetail;

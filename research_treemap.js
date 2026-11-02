/* Embedded by build_network.py. Native SVG; no CDN or automatic requests. */
(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const inventory = D.research;
  if (!inventory) {
    get('researchTab').hidden = true;
    return;
  }
  const records = inventory.records;
  const palette = ['#397e76','#5a6eaa','#b66d48','#8571a0','#927a34','#317fa1','#9a5975','#64824c','#5b7a8a','#a1735a','#72649a','#558b83','#9b6e89'];
  const themes = [...new Set(records.map(r => r.theme))].sort();
  const themeColor = new Map(themes.map((t,i) => [t,palette[i % palette.length]]));
  let focusPath = [], selectedId = null;
  const make = (tag,text,cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const dollars = cents => cents === null ? 'Not reported' : (cents / 100).toLocaleString('en-CA', {style:'currency',currency:'CAD',minimumFractionDigits:0,maximumFractionDigits:2});
  const sum = items => items.reduce((total,r) => total + (r.cents || 0),0);
  const basisLabels = {award:'Total / published awards',payment:'Fiscal 2024 payments',supplement:'One-time supplements',annual:'Annual supplements',uncertain:'Unconfirmed period',missing:'Value not reported',all:'All reported values (mixed bases)'};
  const basisNotes = {
    award:'Award amounts span different competitions and terms. These are reported project awards, not annual spending. Separately identified supplements, payments and uncertain periods are excluded.',
    payment:'Payments / expenditures for fiscal 2024 only, as supplied. These are not total project awards or current annual funding.',
    supplement:'Separately identified launch and early-career supplements only. Base grants are not inferred or added.',
    annual:'Reported annual supplement amounts only. The generator does not multiply annual values by the stated number of years.',
    uncertain:'The source does not confirm whether these values are annual or full-term. Interpret this subset separately.',
    all:'Mixed bases: this total combines full awards, fiscal-year payments, supplements and unconfirmed periods. It is a sum of reported values, not a comparable funding or spending total.',
  };
  themes.forEach(theme => {const option = make('option',theme);option.value = theme;get('fundingTheme').append(option);});
  inventory.notes.forEach(note => get('fundingMethods').append(make('p',note,'subtle')));
  get('fundingMethods').append(make('p','Source: '+inventory.source+'. Original CSV row numbers and all supplied fields are retained in project details. Funding sources are opened only when you choose their links.','subtle'));

  function scopeRecords() {
    const region = get('fundingRegion').value, universities = get('fundingInstitutions').value === 'universities';
    const theme = get('fundingTheme').value, query = get('fundingSearch').value.trim().toLocaleLowerCase();
    return records.filter(r =>
      (region === 'all' || (region === 'bc' ? r.region === 'bc' : ['bc','canada'].includes(r.region))) &&
      (!universities || r.university) && (!theme || r.theme === theme) &&
      (!query || [r.title,r.pi,r.institution,r.raw['Project ID']].join(' ').toLocaleLowerCase().includes(query)));
  }
  function basisRecords(scope) {
    const basis = get('fundingBasis').value;
    // Missing values remain in the record list and coverage count in every basis.
    return scope.filter(r => r.cents === null || basis === 'all' || r.basis === basis);
  }
  function valueBand(cents) {
    if (cents === null) return 'Value not reported';
    if (cents < 10000000) return 'Under $100,000';
    if (cents < 50000000) return '$100,000–under $500,000';
    if (cents < 100000000) return '$500,000–under $1 million';
    return '$1 million and above';
  }
  function compare(a,b) {
    const order = get('fundingOrder').value;
    return order === 'name' ? a.name.localeCompare(b.name) :
      (order === 'asc' ? a.value-b.value : b.value-a.value) || a.name.localeCompare(b.name);
  }
  function groupRecords(items) {
    const group = get('fundingGroup').value, map = new Map();
    for (const r of items) {
      const name = group === 'theme' ? r.theme : group === 'objective' ? r.objective : group === 'university' ? r.institution : valueBand(r.cents);
      if (!map.has(name)) map.set(name,[]);
      map.get(name).push(r);
    }
    return [...map].map(([name,members]) => ({name,value:sum(members),records:members})).sort(compare);
  }
  // Squarified treemap. Every item gets area proportional to its positive value.
  // In name/value-ascending modes the chosen order is preserved during packing.
  function layout(items,x,y,w,h) {
    const result = [], total = items.reduce((s,d) => s+d.value,0);
    if (!(total > 0 && w > 0 && h > 0)) return result;
    const pending = items.map(d => ({...d,area:d.value/total*w*h}));
    const worst = (row,side) => {
      if (!row.length || side <= 0) return Infinity;
      const area = row.reduce((s,d) => s+d.area,0), smallest = Math.min(...row.map(d => d.area)), biggest = Math.max(...row.map(d => d.area));
      return Math.max(side*side*biggest/(area*area),area*area/(side*side*smallest));
    };
    const place = row => {
      const area = row.reduce((s,d) => s+d.area,0);
      if (w >= h) {
        const dx = Math.min(w,area/h);let offset = y;
        for (const d of row) {const dy = d.area/dx;result.push({...d,x,y:offset,w:dx,h:dy});offset += dy;}
        x += dx;w = Math.max(0,w-dx);
      } else {
        const dy = Math.min(h,area/w);let offset = x;
        for (const d of row) {const dx = d.area/dy;result.push({...d,x:offset,y,w:dx,h:dy});offset += dx;}
        y += dy;h = Math.max(0,h-dy);
      }
    };
    let row = [];
    while (pending.length) {
      const candidate = pending[0], side = Math.min(w,h);
      if (!row.length || worst([...row,candidate],side) <= worst(row,side)) row.push(pending.shift());
      else {place(row);row = [];}
    }
    if (row.length) place(row);
    return result;
  }
  const svgNode = (tag,attrs,text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg',tag);
    Object.entries(attrs || {}).forEach(([key,value]) => node.setAttribute(key,value));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  let clipId = 0;
  function clippedText(svg,rect,text,color,size=12,lines=2) {
    if (rect.w < 38 || rect.h < 20) return;
    const id = 'fundingClip'+clipId++, clip = svgNode('clipPath',{id});
    clip.append(svgNode('rect',{x:rect.x+5,y:rect.y+2,width:Math.max(0,rect.w-10),height:Math.max(0,rect.h-4)}));
    svg.append(clip);
    const label = svgNode('text',{x:rect.x+7,y:rect.y+16,fill:color,'font-size':size,'clip-path':`url(#${id})`,'pointer-events':'none'});
    const limit = Math.max(4,Math.floor((rect.w-14)/(size*.6))), words = text.split(/\s+/), output = [];let line = '';
    words.forEach(word => {if (line && (line+' '+word).length > limit) {output.push(line);line = word;} else line += (line?' ':'')+word;});
    if (line) output.push(line);
    const available = Math.max(1,Math.min(lines,Math.floor((rect.h-6)/(size+3))));
    output.slice(0,available).forEach((line,i) => label.append(svgNode('tspan',{x:rect.x+7,dy:i?size+3:0},line.slice(0,limit)+(line.length>limit || (i===available-1 && output.length>available)?'…':''))));
    svg.append(label);
  }
  function hideFundingTip() {get('fundingTip').style.display = 'none';}
  function showTip(r,x,y) {
    const tip = get('fundingTip');
    tip.textContent = r.title+'\nPI / named lead: '+r.pi+'\n'+r.institution+'\n'+dollars(r.cents)+' · '+basisLabels[r.basis]+'\n'+r.objective;
    tip.style.display = 'block';
    const bounds = tip.getBoundingClientRect();
    tip.style.left = Math.max(8,Math.min(x+12,window.innerWidth-bounds.width-8))+'px';
    tip.style.top = Math.max(8,Math.min(y+12,window.innerHeight-bounds.height-8))+'px';
  }
  function projectDetails(r) {
    selectedId = r.id;
    const box = get('fundingDetails');box.replaceChildren(make('div',r.id+' · SOURCE ROW '+r.source_row,'eyebrow'),make('h3',r.title),make('p',dollars(r.cents)));
    const dl = make('dl');
    for (const [label,value] of [
      ['PI / named lead',r.pi],['University / lead institution at award',r.original_institution || 'Not supplied'],
      ['Primary objective',r.objective],['Theme',r.theme],['Funding basis',r.raw['Grant dollar value basis'] || 'Not supplied'],
      ['Funder / competition year',[r.raw.Funder,r.raw['Award / competition year']].filter(Boolean).join(' · ')],
      ['Record category',r.raw['Record category']],['Mapping confidence (source rating, not effectiveness)',r.raw['Confidence (1-5)']],
      ['Match rationale',r.raw['Match rationale']],['Verification status',r.raw['Verification status']],['Notes / caveats',r.raw['Notes / caveats']],
    ]) {if (value) dl.append(make('dt',label),make('dd',value));}
    box.append(dl);
    for (const [label,field] of [['Project evidence','Evidence URL'],['Grant value source','Grant value source']]) {
      const url = r.raw[field];
      if (/^https?:\/\/\S+$/i.test(url || '')) {const link = make('a',label);link.href = url;link.target = '_blank';link.rel = 'noopener noreferrer';box.append(make('p'),link);}
    }
    const all = make('details');all.append(make('summary','All original CSV fields'));
    const original = make('dl');Object.entries(r.raw).forEach(([label,value]) => original.append(make('dt',label),make('dd',value || 'Not supplied')));all.append(original);box.append(all);
  }
  function drawProjects(svg,items,rect) {
    const leaves = items.map(r => ({name:r.title,value:r.cents,record:r})).sort(compare);
    layout(leaves,rect.x,rect.y,rect.w,rect.h).forEach(cell => {
      const r = cell.record, tile = svgNode('g',{class:'funding-tile',tabindex:0,role:'button','aria-label':r.title+'; PI: '+r.pi+'; '+dollars(r.cents)});
      tile.append(svgNode('title',{},r.title+'\nPI / named lead: '+r.pi+'\n'+dollars(r.cents)));
      // Tiny values remain real, proportional slivers; the table offers a larger target.
      tile.append(svgNode('rect',{x:cell.x,y:cell.y,width:Math.max(0,cell.w),height:Math.max(0,cell.h),fill:themeColor.get(r.theme),stroke:'#fff','stroke-width':1}));
      clippedText(tile,cell,r.title,'white',11,3);
      if (cell.h>80 && cell.w>100) clippedText(tile,{...cell,y:cell.y+cell.h-24,h:23},dollars(r.cents),'white',11,1);
      tile.onclick = () => {hideFundingTip();projectDetails(r);};
      tile.onkeydown = event => {if (['Enter',' '].includes(event.key)) {event.preventDefault();tile.onclick();}};
      tile.onpointermove = event => showTip(r,event.clientX,event.clientY);
      tile.onpointerleave = hideFundingTip;
      tile.onfocus = () => {const b = tile.getBoundingClientRect();showTip(r,b.x,b.y);};
      tile.onblur = hideFundingTip;
      svg.append(tile);
    });
  }
  function objectiveGroups(items) {
    const map = new Map();items.forEach(r => {if (!map.has(r.objective)) map.set(r.objective,[]);map.get(r.objective).push(r);});
    return [...map].map(([name,records]) => ({name,records,value:sum(records)})).sort(compare);
  }
  function drawGroups(svg,groups,rect,depth) {
    layout(groups,rect.x,rect.y,rect.w,rect.h).forEach(cell => {
      const headerHeight = Math.min(34,cell.h*.24), header = svgNode('g',{tabindex:0,role:'button','aria-label':'Focus '+cell.name+'; '+dollars(cell.value)});
      header.append(svgNode('rect',{x:cell.x,y:cell.y,width:cell.w,height:headerHeight,fill:'#e2eae3',stroke:'white','stroke-width':2}));
      clippedText(header,{...cell,h:headerHeight},cell.name+' · '+dollars(cell.value),'#18332f',11,1);
      header.append(svgNode('title',{},cell.name+'\n'+dollars(cell.value)+' · '+cell.records.length+' records\nClick to focus this group'));
      header.onclick = () => {focusPath = [...focusPath.slice(0,depth),cell.name];renderResearch();};
      header.onkeydown = e => {if (['Enter',' '].includes(e.key)) {e.preventDefault();header.onclick();}};
      svg.append(header);
      // Relative padding keeps even the smallest funded group visible.
      const padding = Math.min(2,cell.w/20,cell.h/20);
      const inner = {x:cell.x+padding,y:cell.y+headerHeight,w:cell.w-2*padding,h:cell.h-headerHeight-padding};
      if (get('fundingGroup').value==='theme' && depth===0 && inner.h>70 && inner.w>90) drawGroups(svg,objectiveGroups(cell.records),inner,1);
      else drawProjects(svg,cell.records,inner);
    });
  }
  function renderTable(items) {
    const table = make('table',undefined,'funding-table'), head = make('thead'), hrow = make('tr');
    ['Project / PI','Institution','Primary objective','Reported CAD','Basis'].forEach(label => {const th = make('th',label);th.scope = 'col';hrow.append(th);});head.append(hrow);table.append(head);
    const body = make('tbody');
    [...items].sort((a,b) => compare({name:a.title,value:a.cents??-1},{name:b.title,value:b.cents??-1})).forEach(r => {
      const row = make('tr'), title = make('td'), button = make('button',r.title);button.onclick = () => projectDetails(r);
      title.append(button,make('div',r.pi,'subtle'));row.append(title,...[r.institution,r.objective,dollars(r.cents),basisLabels[r.basis]].map(v => make('td',v)));body.append(row);
    });table.append(body);get('fundingTable').replaceChildren(table);
    get('fundingTableSummary').textContent = 'Project list · '+items.length+' records (including missing / zero values)';
  }
  function renderResearch() {
    hideFundingTip();
    const scope = scopeRecords(), eligible = basisRecords(scope), positive = eligible.filter(r => r.cents>0), groups = groupRecords(positive);
    let items = eligible, focused = null;
    if (focusPath[0]) {
      focused = groups.find(g => g.name===focusPath[0]);
      if (!focused) focusPath = [];
      else {
        // Include unvalued records in a focused theme/objective/institution list.
        const mode = get('fundingGroup').value;
        items = eligible.filter(r => (mode==='theme'?r.theme:mode==='objective'?r.objective:mode==='university'?r.institution:valueBand(r.cents))===focusPath[0]);
        if (mode==='theme' && focusPath[1]) items = items.filter(r => r.objective===focusPath[1]);
      }
    }
    const valued = items.filter(r => r.cents>0), total = sum(valued), missing = items.filter(r => r.cents===null).length;
    const summary = get('fundingSummary');summary.replaceChildren();
    for (const [value,label] of [[dollars(total),get('fundingBasis').value==='all'?'Reported values · mixed bases':basisLabels[get('fundingBasis').value]+' · CAD'],[valued.length,'Valued records in treemap'],[missing,'Records with no reported value'],[new Set(valued.map(r => r.objective)).size,'Primary objectives represented']]) {
      const metric = make('div');metric.append(make('strong',value),make('span',label));summary.append(metric);
    }
    get('fundingBasisNote').textContent = basisNotes[get('fundingBasis').value];
    const path = get('fundingPath');path.replaceChildren();
    const reset = make('button','All groups');reset.disabled = !focusPath.length;reset.onclick = () => {focusPath=[];renderResearch();};path.append(reset);
    focusPath.forEach(name => path.append(make('span','› '+name)));
    // A selector makes tiny groups available without a precise pointer target.
    const label = make('label','Focus group '), picker = make('select');picker.setAttribute('aria-label','Focus funding group');
    const all = make('option','All groups');all.value='';picker.append(all);
    groups.forEach(g => {const option = make('option',g.name+' · '+dollars(g.value));option.value=g.name;picker.append(option);});picker.value=focusPath[0]||'';
    picker.onchange = () => {focusPath=picker.value?[picker.value]:[];renderResearch();};label.append(picker);path.append(label);
    const map = get('fundingMap');map.replaceChildren();
    if (!valued.length) map.append(make('p','No positive funding values match these filters. Try another funding basis or scope; unvalued records remain in the project list.','funding-empty'));
    else {
      const width = Math.max(260,map.getBoundingClientRect().width || 900), height = window.innerWidth<=560?540:window.innerWidth<=1000?580:640;
      const svg = svgNode('svg',{viewBox:`0 0 ${width} ${height}`,role:'group','aria-label':'Research funding treemap. Area represents reported CAD; use project list for small tiles.'});
      clipId=0;
      const rect = {x:2,y:2,w:width-4,h:height-4};
      if (!focusPath.length) drawGroups(svg,groups,rect,0);
      else if (get('fundingGroup').value==='theme' && focusPath.length===1) drawGroups(svg,objectiveGroups(valued),rect,1);
      else drawProjects(svg,valued,rect);
      map.append(svg);
    }
    const legend=get('fundingLegend');legend.replaceChildren();
    themes.filter(t => valued.some(r => r.theme===t)).forEach(t => {const entry=make('span'), dot=make('i');dot.style.background=themeColor.get(t);entry.append(dot,document.createTextNode(t));legend.append(entry);});
    const zero = items.filter(r => r.cents===0).length;
    get('fundingStatus').textContent = `${items.length} records in view · ${missing} missing amounts · ${zero} zero amounts · ${scope.length-eligible.length} records outside selected funding basis. Colours identify themes. Click a group header to focus; use the project list for tiny tiles.`;
    renderTable(items);
    if (selectedId && items.some(r => r.id===selectedId)) projectDetails(items.find(r => r.id===selectedId));
    else {selectedId=null;get('fundingDetails').replaceChildren(make('div','PROJECT EVIDENCE','eyebrow'),make('h3','Select a project'),make('p','Hover or focus a tile to see its title and PI. Click, tap or choose from the project list for grant sources, objective-matching rationale and verification notes.','subtle'));}
  }
  for (const id of ['fundingRegion','fundingInstitutions','fundingGroup','fundingBasis','fundingOrder','fundingTheme']) get(id).onchange=()=>{focusPath=[];renderResearch();};
  get('fundingSearch').oninput=()=>{focusPath=[];renderResearch();};
  window.addEventListener('resize',()=>{if (!get('research').hidden) renderResearch();});
  window.addEventListener('keydown',event=>{if (event.key==='Escape') hideFundingTip();});
  window.renderResearch=renderResearch;
  window.hideFundingTip=hideFundingTip;
  // Pure helpers also support reproducible data/layout checks without a browser.
  window.researchFunding={scopeRecords,basisRecords,groupRecords,layout};
})();

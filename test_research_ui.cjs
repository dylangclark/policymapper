// Run with Node; no third-party packages. Exercises the actual embedded scripts.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2] || __dirname+'/index.html','utf8');
const payload=html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
const ctx=new Proxy({measureText:text=>({width:text.length*6})},{get:(target,key)=>key in target?target[key]:(()=>{})});
class Element {
  constructor(tag='div'){this.tagName=tag;this.children=[];this.style={};this.attrs={};this.value='';this.hidden=false;this.checked=false;this.textContent='';this.classList={add:()=>{}};}
  append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
  setAttribute(key,value){this.attrs[key]=value;}get options(){return this.children;}
  get parentElement(){return this;}getBoundingClientRect(){return {x:0,y:0,left:0,top:0,width:900,height:640};}
  getContext(){return ctx;}focus(){}setPointerCapture(){}
}
const els=new Map(),get=id=>{if(!els.has(id))els.set(id,new Element());return els.get(id);};
get('data').textContent=payload;
for(const [id,value] of Object.entries({outcomeOrder:'economic',sort:'count',fundingRegion:'canada',fundingInstitutions:'universities',fundingGroup:'theme',fundingBasis:'award',fundingOrder:'desc'}))get(id).value=value;
get('showPolicies').checked=true;get('includeConstraints').checked=true;
const win={devicePixelRatio:1,innerWidth:1400,innerHeight:1000,addEventListener:()=>{}};
const sandbox=vm.createContext({console,document:{getElementById:get,createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),createTextNode:t=>({textContent:t}),querySelector:get},window:win,innerWidth:1400,innerHeight:1000,requestAnimationFrame:f=>f()});
for(const script of html.matchAll(/<script>\s*([\s\S]*?)<\/script>/g))vm.runInContext(script[1],sandbox);
const ex=s=>vm.runInContext(s,sandbox),json=s=>JSON.parse(ex('JSON.stringify('+s+')'));
const countTiles=node=>(node.attrs?.class==='funding-tile'?1:0)+(node.children||[]).reduce((s,n)=>s+countTiles(n),0);
const text=node=>[node.textContent,...(node.children||[]).map(text)].join(' ');
if(!ex('Boolean(D.research)')) {
  assert(get('researchTab').hidden);assert.equal(ex('activeEdges.length'),903);
  console.log('Optional research data: tab hidden, existing network preserved');process.exit();
}
get('researchTab').onclick();
assert(get('counts').hidden && get('network').hidden && !get('research').hidden);
assert(get('networkFilters').hidden && get('metrics').hidden);
assert.equal(countTiles(get('fundingMap')),69);
assert(text(get('fundingSummary')).includes('$23,569,592'));
const expected={bc:{universities:[47,1024964633],all:[49,1047814633]},canada:{universities:[165,4224968299],all:[178,4654109799]},all:{universities:[167,4258968299],all:[186,4739809799]}};
for(const [region,types] of Object.entries(expected))for(const [type,[count,cents]] of Object.entries(types)) {
  get('fundingRegion').value=region;get('fundingInstitutions').value=type;get('fundingBasis').value='all';win.renderResearch();
  const rows=json('window.researchFunding.scopeRecords()');assert.equal(rows.length,count);assert.equal(rows.reduce((s,r)=>s+(r.cents||0),0),cents);
  assert.equal(countTiles(get('fundingMap')),count-rows.filter(r=>r.cents===null).length);
}
get('fundingRegion').value='all';get('fundingInstitutions').value='all';
for(const [basis,count,cents] of [['award',89,2868550700],['payment',89,1860359099],['supplement',4,5000000],['annual',1,1500000],['uncertain',2,4400000]]) {
  get('fundingBasis').value=basis;get('fundingBasis').onchange();
  const rows=json('window.researchFunding.basisRecords(window.researchFunding.scopeRecords())');
  assert.equal(rows.length,count+1);assert.equal(rows.reduce((s,r)=>s+(r.cents||0),0),cents);assert.equal(countTiles(get('fundingMap')),count);
}
get('fundingBasis').value='all';
for(const group of ['theme','objective','university','value'])for(const order of ['desc','asc','name']) {
  get('fundingGroup').value=group;get('fundingOrder').value=order;get('fundingGroup').onchange();
  assert.equal(countTiles(get('fundingMap')),185);
  const groups=json('window.researchFunding.groupRecords(D.research.records.filter(r=>r.cents>0))');assert.equal(groups.reduce((s,g)=>s+g.value,0),4739809799);
}
// Packing invariants: no overlaps, conserved area and value-proportional rectangles.
for(const [w,h] of [[900,640],[260,540],[1,1]]) {
  const cells=json(`window.researchFunding.layout(Array.from({length:100},(_,i)=>({value:i+1,name:String(i)})),0,0,${w},${h})`);
  assert.equal(cells.length,100);assert(Math.abs(cells.reduce((s,c)=>s+c.w*c.h,0)-w*h)<1e-6);
  for(const [i,a] of cells.entries()) {
    assert([a.x,a.y,a.w,a.h].every(Number.isFinite));assert(a.w>0 && a.h>0);
    assert(Math.abs(a.w*a.h/(w*h)-a.value/5050)<1e-8);
    assert(cells.slice(i+1).every(b=>Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)<1e-7 || Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)<1e-7));
  }
}
get('fundingSearch').value='Christopher Carlsten';get('fundingSearch').oninput();assert.equal(countTiles(get('fundingMap')),1);
const tile=(function find(n){return n.attrs?.class==='funding-tile'?n:(n.children||[]).map(find).find(Boolean);})(get('fundingMap'));
tile.onpointermove({clientX:100,clientY:100});assert(get('fundingTip').textContent.includes('Lungs on Fire'));assert(get('fundingTip').textContent.includes('Christopher Carlsten'));
tile.onkeydown({key:'Enter',preventDefault(){}});assert(text(get('fundingDetails')).includes('Match rationale'));assert(text(get('fundingDetails')).includes('Grant value source'));
get('fundingSearch').value='no matching project 123xyz';get('fundingSearch').oninput();assert.equal(countTiles(get('fundingMap')),0);assert(text(get('fundingMap')).includes('No positive funding'));
get('networkTab').onclick();assert(!get('network').hidden && get('research').hidden);assert(!get('networkFilters').hidden);assert.equal(ex('activeEdges.length'),903);assert.equal(ex('D.policy_stats.associations'),856);
get('outcomeOrder').value='combined';get('outcomeOrder').onchange();assert.equal(ex('activeNodes.length'),124);
console.log('Research UI: scopes, all bases/groupings/orders, totals, proportional packing, tooltips, evidence, empty state and network regression passed');

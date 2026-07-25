// ====== 手绘地图布局 静态渲染 + stub ======
let mapInitialized = false, mapSvg, mapG;
let vx = 0, vy = 0, vw = 1800, vh = 1500;

// 外围绕行弧线（绕过地图中间的线路）
const ARC_EDGES = [['capetown','swau'],['colombo','swau'],['jakarta','swau']];
function isArc(a,b){return ARC_EDGES.some(w=>(w[0]===a&&w[1]===b)||(w[0]===b&&w[1]===a));}

// Stub edges (搭船/搭飞机 - 只画短线标签)
let STUB_EDGES = [];
fetch('/static/js/stubs.json').then(r=>r.json()).then(d=>{STUB_EDGES=d;});

function isStub(a,b){return STUB_EDGES.some(s=>(s[0]===a&&s[1]===b)||(s[0]===b&&s[1]===a));}

function initMap(){
    mapSvg=document.getElementById('game-map');
    mapSvg.setAttribute('viewBox',`${vx} ${vy} ${vw} ${vh}`);
    mapSvg.innerHTML=''; mapSvg.style.cursor='grab';
    mapG=createSvgEl('g',{id:'map-main'}); mapSvg.appendChild(mapG);
    mapG.appendChild(createSvgEl('rect',{x:0,y:0,width:1800,height:1500,fill:'#f4f6f9'}));
    drawEdges(); drawCities(); attachEvents(); mapInitialized=true;
}

function drawEdges(){
    const g=createSvgEl('g',{id:'map-edges'}); mapG.appendChild(g);
    const drawn=new Set(), stubsPerCity={};
    gameState.cities.forEach(c=>{c.connections.forEach(cid=>{
        const k=[c.id,cid].sort().join('-'); if(drawn.has(k))return; drawn.add(k);
        const t=cityDataMap[cid]; if(!t)return;
        const dist=Math.hypot(t.x-c.x,t.y-c.y);
        if(isArc(c.id,cid)){
            // 外围绕弧线：控制点向外推到地图边缘
            const mx=(c.x+t.x)/2, my=(c.y+t.y)/2;
            const cx=mx+(mx-1100)*2.5, cy=my+(my-800)*2.5;
            g.appendChild(createSvgEl('path',{d:`M ${c.x} ${c.y} Q ${cx} ${cy} ${t.x} ${t.y}`,
                class:'map-edge arc','data-key':k,fill:'none',stroke:'#2B6CB0','stroke-width':2.5}));
        }else if(isStub(c.id,cid)){
            const o1=stubsPerCity[c.id]||0, o2=stubsPerCity[cid]||0;
            drawStub(g,k,c,t,o1); stubsPerCity[c.id]=o1+1;
            drawStub(g,k,t,c,o2); stubsPerCity[cid]=o2+1;
        }else{
            g.appendChild(createSvgEl('path',{d:`M ${c.x} ${c.y} L ${t.x} ${t.y}`,
                class:'map-edge','data-key':k,fill:'none',stroke:'#8899aa','stroke-width':1.5}));
        }
    });});
}
function drawStub(p,k,f,to,offset=0){
    const dx=to.x-f.x,dy=to.y-f.y,l=Math.hypot(dx,dy); if(!l)return;
    let dirX = dx>0 ? 1 : -1;
    if(f.x < 300 && to.x > 1500) dirX = -1;
    if(f.x > 1500 && to.x < 300) dirX = 1;
    const sx=f.x+dirX*65;
    const oy=f.y + offset*16;  // 每个stub垂直偏移16px避免重叠
    p.appendChild(createSvgEl('line',{x1:f.x+dirX*22,y1:oy,x2:sx,y2:oy,
        class:'map-edge stub','data-key':k,stroke:'#aab','stroke-width':1.5,'stroke-dasharray':'3 3'}));
    const lb=createSvgEl('text',{x:sx+dirX*4,y:oy-4,'font-size':'11px',fill:'#556','font-weight':'600','text-anchor':dirX>0?'start':'end'});
    lb.textContent='⇢ '+to.name; p.appendChild(lb);
}
function drawCities(){
    const g=createSvgEl('g',{id:'map-cities'}); mapG.appendChild(g);
    const RESOURCE_IDS = new Set(['riyadh','tehran','kabul','yekaterinburg','tashkent','novosibirsk','baikal']);
    gameState.cities.forEach(c=>{
        const r=getCityRadius(c);
        const cg=createSvgEl('g',{class:'city-group','data-id':c.id,transform:`translate(${c.x},${c.y})`});
        cg.appendChild(createSvgEl('circle',{cx:0,cy:0,r:r,class:'city-circle owner-'+c.owner}));
        if(RESOURCE_IDS.has(c.id)){
            cg.appendChild(createSvgEl('polygon',{points:'0,-12 5,-7 0,-2 -5,-7',fill:'#F5A623',stroke:'#fff','stroke-width':0.5}));
        }
        const at=createSvgEl('text',{x:0,y:1,class:'city-army',fill:'#fff','font-size':'9px','text-anchor':'middle','font-weight':'700'});
        at.textContent=getCityDisplayArmy(c.id);
        const nt=createSvgEl('text',{x:0,y:r+11,class:'city-label','font-size':'8px',fill:'#333','text-anchor':'middle'});
        nt.textContent=c.name;
        cg.appendChild(at); cg.appendChild(nt);
        cg.querySelector('circle').addEventListener('click',e=>{e.stopPropagation();onCityClick(c.id);});
        cg.querySelector('circle').addEventListener('mouseover',e=>{clearTimeout(_tt);showTooltip(c,e);});
        cg.querySelector('circle').addEventListener('mouseout',()=>hideTooltip());
        g.appendChild(cg);
    });
}
function attachEvents(){
    let d=false,lx,ly;
    mapSvg.addEventListener('mousedown',e=>{if(e.target===mapSvg||e.target.tagName==='rect'){d=true;lx=e.clientX;ly=e.clientY;mapSvg.style.cursor='grabbing';}});
    window.addEventListener('mousemove',e=>{if(!d)return;const r=mapSvg.getBoundingClientRect();vx-=(e.clientX-lx)*vw/r.width;vy-=(e.clientY-ly)*vh/r.height;lx=e.clientX;ly=e.clientY;mapSvg.setAttribute('viewBox',`${vx} ${vy} ${vw} ${vh}`);});
    window.addEventListener('mouseup',()=>{d=false;mapSvg.style.cursor='grab';});
    mapSvg.addEventListener('wheel',e=>{e.preventDefault();const r=mapSvg.getBoundingClientRect();const mx=(e.clientX-r.left)*vw/r.width+vx,my=(e.clientY-r.top)*vh/r.height+vy;const z=e.deltaY>0?1.15:1/1.15;vw=Math.max(360,Math.min(3600,vw*z));vh=Math.max(300,Math.min(3000,vh*z));vx=mx-(e.clientX-r.left)*vw/r.width;vy=my-(e.clientY-r.top)*vh/r.height;mapSvg.setAttribute('viewBox',`${vx} ${vy} ${vw} ${vh}`);});
}
function renderMap(){if(!mapInitialized){initMap();return;}document.querySelectorAll('#map-cities .city-group').forEach((g,i)=>{const c=gameState.cities[i];if(!c)return;g.querySelector('circle').setAttribute('class','city-circle owner-'+c.owner);g.querySelector('circle').setAttribute('r',getCityRadius(c));g.querySelector('text').textContent=getCityDisplayArmy(c.id);g.classList.toggle('selected',selectedCity===c.id);});highlightValidTargets();}
function getCityRadius(c){return 14+Math.min(Math.sqrt(getCityDisplayArmy(c.id))*.3,5);}
function highlightValidTargets(){document.querySelectorAll('#map-cities .city-group').forEach(g=>g.classList.remove('valid-target'));document.querySelectorAll('#map-edges path,#map-edges line').forEach(e=>e.classList.remove('highlight','inspected'));const aid=selectedCity||inspectedCity;if(!aid)return;const c=cityDataMap[aid];if(!c)return;const insp=inspectedCity===aid;c.connections.forEach(cid=>{document.querySelectorAll('#map-edges path,#map-edges line').forEach(e=>{if(e.getAttribute('data-key')===[aid,cid].sort().join('-'))e.classList.add(insp?'inspected':'highlight');});const g=document.querySelector(`#map-cities .city-group[data-id=\"${cid}\"]`);if(g)g.classList.add('valid-target');});}
let _tt=null;
function showTooltip(city,event){clearTimeout(_tt);const t=document.getElementById('city-tooltip');const oc={player_a:'#2B6CB0',player_b:'#C53030',npc:'#C07D1A'};const on={player_a:'蓝方',player_b:'红方',npc:'NPC武装'};const RES_IDS=new Set(['riyadh','tehran','kabul','yekaterinburg','tashkent','novosibirsk','baikal']);
const resTag=RES_IDS.has(city.id)?' <span style=\"color:#F5A623;font-size:10px\">[资源城]</span>':'';
const resBonus=RES_IDS.has(city.id)?` (+2资源)`:'';
t.innerHTML=`<b style=\"color:${oc[city.owner]||'#888'}\">${city.name}${resTag}</b><br>所属: ${on[city.owner]||'?'}<br>兵力: ${getCityDisplayArmy(city.id)}<br>连接: ${city.connection_count} 条<br>增兵/回合: +${city.connection_count}${resBonus}<br><span style=\"color:#C53030\">攻占需: ${Math.ceil(city.army*1.5)} 兵</span>`;const mr=document.querySelector('.map-container').getBoundingClientRect();t.style.left=Math.min(event.clientX-mr.left+15,mr.width-170)+'px';t.style.top=(event.clientY-mr.top-100)+'px';t.classList.remove('hidden');}
function hideTooltip(){clearTimeout(_tt);_tt=setTimeout(()=>document.getElementById('city-tooltip').classList.add('hidden'),150);}

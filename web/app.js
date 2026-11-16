/* Speider local site. All UI text goes through T (Norwegian and English). */
const T = {
  no: { find: 'Finn', player: 'Spiller', eras: 'Epoker', market: 'Marked', search: 'Søk etter spiller',
    findTitle: 'Sjanse for toppliga', findLead: 'Unge spillere utenfor de fem store ligaene, rangert etter sjansen for å spille der innen tre år. Modellen bygger på alder, karriere og nivå, og er testet på ekte utfall.',
    baseRate: 'Snittsjanse', baseSub: 'For alle under 24 utenfor topp fem', inList: 'Spillere i utvalget', inListSub: 'Under 24, minst 270 minutter', hit: 'Treff i øverste tidel', hitSub: 'I testen: én av fire nådde en toppliga',
    allRoles: 'Alle roller', maxAge: 'Maks alder', smallOnly: 'Bare svakere ligaer', name: 'Spiller', league: 'Liga', age: 'Alder', min: 'Minutter', chance: 'Sjanse toppliga', times: 'Mot snittet',
    playerTitle: 'Spillere', big: 'Søk blant 32 000 spillere', cGrow: 'Størst forventet verdivekst på tre år', cUnder: 'Speider verdsetter høyere enn markedet', cStep: 'Størst sjanse for toppliga', in3s: 'om tre år', vsMv: 'mot markedsverdi', yrs: 'år', until: 'Kontrakt til', season: 'Sesong', height: 'Høyde',
    p5: 'Sjanse for toppliga innen tre år', p5sub: 'Snittet er', quality: 'Tall per 90 minutter', qualitySub: 'Justert for spilletid. Søylen viser plassering blant spillere i samme rolle, liga og sesong.',
    better: 'Bedre enn', career: 'Karriere', matches: 'Kamper', goals: 'Mål', assists: 'Assist', rating: 'Rating', team: 'Lag',
    mv: 'Markedsverdi fra tredjepart', mvSub: 'Millioner euro. Dette er ikke Speiders anslag. Leverandørens tall hopper mye fra år til år og vises bare som bakgrunn.',
    tipStat: 'Målt: {raw} per 90\nJustert for spilletid: {adj}\nBedre enn {p} % av {n} spillere', tipTyp: 'Typisk for alderen', range: 'Spenn, 8 av 10 utfall', mvShort: 'Markedsverdi', sv: 'Speider-verdi', svSub: 'Sannsynlig spenn', mv3: 'Markedsverdi, tredjepart', in3: 'Om tre år', in3Sub: 'Dagens prisnivå. Spenn', vs: 'mot tredjepart', valNote: 'Speider-verdien er hva en overgang trolig ville kostet i dag, lært av faktiske overgangssummer. Testet på {n} overganger i 2025–26: typisk bom {a} % for Speider og {b} % for tredjepartsverdien. Den er altså ikke bedre ennå, og vises som et eget anslag.', path: 'Forventet verdi', pathSub: 'Millioner euro i dagens prisnivå. Grønn linje er spillerens egen bane ut fra alder, karriere, nivå og tall. Feltet dekker 8 av 10 utfall. Prikket linje er en typisk spiller på samme alder med samme verdi i dag.', play: 'Sjanse for fortsatt å spille', profile: 'Spillerprofil', strong: 'Styrker', weak: 'Svakheter', similar: 'Ligner mest i spillestil', none: 'Ingen tydelige', value: 'Speider-verdi',
    erasTitle: 'Epoker', erasLead: 'Mål uten straffer per 90 minutter, målt mot alle faste utespillere i samme liga og sesong. Fulle tropper tilbake til 2001/02 for seks ligaer.',
    pick: 'Søk etter spiller og velg sesong', perc: 'Bedre enn', npg: 'Mål uten straffer per 90', sd: 'Standardavvik over snittet', loading: 'Laster …', noHit: 'Ingen treff',
    marketTitle: 'Marked', marketLead: 'Prisnivået på overganger over tid, og hvor sterke ligaene er målt på spillere som bytter liga.',
    idx: 'Prisindeks', idxSub: 'Samme type spiller, samme selgende og kjøpende liga, samme alder. 2026 = 100. Stiplet linje er fremskrevet, med spennet 8 av 10 utfall faller i.',
    strength: 'Ligastyrke', strengthSub: 'Målt på spillere som bytter liga. Høyere tall betyr sterkere liga.', now: 'Nå', growth: 'Vekst per år', y2034: 'Anslag 2034' },
  en: { find: 'Find', player: 'Player', eras: 'Eras', market: 'Market', search: 'Search for a player',
    findTitle: 'Top-league chance', findLead: 'Young players outside the big five leagues, ranked by their chance of playing there within three years. The model uses age, career and level, and is tested on real outcomes.',
    baseRate: 'Average chance', baseSub: 'For everyone under 24 outside the big five', inList: 'Players in the sample', inListSub: 'Under 24, at least 270 minutes', hit: 'Hit rate in the top tenth', hitSub: 'In the test: one in four reached a top league',
    allRoles: 'All roles', maxAge: 'Max age', smallOnly: 'Weaker leagues only', name: 'Player', league: 'League', age: 'Age', min: 'Minutes', chance: 'Top-league chance', times: 'Against average',
    playerTitle: 'Players', big: 'Search 32,000 players', cGrow: 'Largest expected value growth in three years', cUnder: 'Speider values higher than the market', cStep: 'Best chance of a top league', in3s: 'in three years', vsMv: 'vs market value', yrs: 'yrs', until: 'Contract to', season: 'Season', height: 'Height',
    p5: 'Chance of a top league within three years', p5sub: 'The average is', quality: 'Numbers per 90 minutes', qualitySub: 'Adjusted for playing time. The bar shows rank among players in the same role, league and season.',
    better: 'Better than', career: 'Career', matches: 'Matches', goals: 'Goals', assists: 'Assists', rating: 'Rating', team: 'Team',
    mv: 'Third-party market value', mvSub: "Millions of euros. This is not Speider's estimate. The provider's numbers jump a lot from year to year and are shown as background only.",
    tipStat: 'Measured: {raw} per 90\nAdjusted for playing time: {adj}\nBetter than {p}% of {n} players', tipTyp: 'Typical for the age', range: 'Range, 8 in 10 outcomes', mvShort: 'Market value', sv: 'Speider value', svSub: 'Likely range', mv3: 'Market value, third party', in3: 'In three years', in3Sub: "Today's prices. Range", vs: 'vs third party', valNote: 'The Speider value is what a transfer would probably cost today, learned from actual fees. Tested on {n} transfers in 2025–26: typical miss {a}% for Speider and {b}% for the third-party value. So it is not better yet, and is shown as a separate estimate.', path: 'Expected value', pathSub: "Millions of euros in today's prices. The green line is the player's own path from age, career, level and numbers. The band covers 8 in 10 outcomes. The dotted line is a typical player of the same age with the same value today.", play: 'Chance of still playing', profile: 'Player profile', strong: 'Strengths', weak: 'Weaknesses', similar: 'Most similar in style', none: 'None that stand out', value: 'Speider value',
    erasTitle: 'Eras', erasLead: 'Non-penalty goals per 90 minutes, measured against every outfield regular in the same league and season. Full squads back to 2001/02 for six leagues.',
    pick: 'Search for a player and pick a season', perc: 'Better than', npg: 'Non-penalty goals per 90', sd: 'Standard deviations above the mean', loading: 'Loading …', noHit: 'No matches',
    marketTitle: 'Market', marketLead: 'The price level of transfers over time, and how strong the leagues are measured on players who change league.',
    idx: 'Price index', idxSub: 'Same type of player, same selling and buying league, same age. 2026 = 100. The dotted line is projected, with the range 8 in 10 outcomes fall in.',
    strength: 'League strength', strengthSub: 'Measured on players who change league. A higher number means a stronger league.', now: 'Now', growth: 'Growth per year', y2034: 'Estimate 2034' } };
const STAT = { rating: ['Rating', 'Rating'], goals_per_90: ['Mål', 'Goals'], expected_goals_per_90: ['xG', 'xG'], expected_assists_per_90: ['xA', 'xA'], total_scoring_att: ['Skudd', 'Shots'],
  ontarget_scoring_att: ['Skudd på mål', 'Shots on target'], won_contest: ['Dribler', 'Dribbles'], accurate_pass: ['Pasninger', 'Passes'],
  accurate_long_balls: ['Lange pasninger', 'Long passes'], total_tackle: ['Taklinger', 'Tackles'], interception: ['Brudd', 'Interceptions'], ball_recovery: ['Ballvinninger', 'Recoveries'],
  effective_clearance: ['Klareringer', 'Clearances'], poss_won_att_3rd: ['Ballvinning høyt', 'High ball wins'] };
const ROLE = { GK: ['Keeper', 'Goalkeeper'], CB: ['Midtstopper', 'Centre-back'], FB: ['Back', 'Full-back'], DM: ['Defensiv midtbane', 'Defensive midfielder'], CM: ['Sentral midtbane', 'Central midfielder'],
  AM: ['Offensiv midtbane', 'Attacking midfielder'], W: ['Kant', 'Winger'], ST: ['Spiss', 'Striker'] };
let lang = (() => { try { return localStorage.getItem('sp-lang') } catch (e) { return null } })() || 'no';
const t = k => T[lang][k] || k, li = () => (lang === 'no' ? 0 : 1), PS = () => (lang === 'no' ? ' %' : '%');
const nf = (v, d = 0) => v == null ? '–' : Number(v).toLocaleString(lang === 'no' ? 'nb-NO' : 'en-GB', { minimumFractionDigits: d, maximumFractionDigits: d });
const eur = v => v == null ? '–' : v >= 1e6 ? '€' + nf(v / 1e6, v < 1e7 ? 1 : 0) + (lang === 'no' ? ' mill.' : 'm') : '€' + nf(v / 1e3) + 'k';
const pc = v => v == null ? '–' : nf(v * 100, v < 0.1 ? 1 : 0) + PS();
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/ø/g, 'o').replace(/æ/g, 'ae').replace(/đ/g, 'd');
const P = window.SP.players, M = window.SP.market, view = document.getElementById('view');
const PN = P.map(p => norm(p[1]));
const load = src => new Promise((res, rej) => { const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej; document.head.appendChild(s) });
async function player(id) { const n = id % (M.shards || 256), k = 'shard' + n; if (!window.SP[k]) await load('data/shard/' + n + '.js'); return window.SP[k][id] }

function chrome() {
  document.documentElement.lang = lang === 'no' ? 'nb' : 'en';
  const cur = (location.hash.slice(1).split(/[\/-]/)[0]) || 'find';
  document.getElementById('tabs').innerHTML = ['find', 'player', 'eras', 'market'].map(k => `<a href="#${k}" ${cur === k ? 'aria-current="page"' : ''}>${t(k)}</a>`).join('');
  document.getElementById('q').placeholder = t('search'); document.getElementById('lang').textContent = lang === 'no' ? 'English' : 'Norsk';
}
function countUp() { document.querySelectorAll('[data-n]').forEach(el => { const end = +el.dataset.n, d = +el.dataset.d || 0, suf = el.dataset.s || '', t0 = performance.now();
  const step = now => { const k = Math.min(1, (now - t0) / 900), e = 1 - Math.pow(1 - k, 3); el.textContent = nf(end * e, d) + suf; if (k < 1) requestAnimationFrame(step) }; requestAnimationFrame(step) }) }
const tile = (label, n, d, suf, sub, g) => `<div class="tile rise"><span class="sub">${label}</span><b class="${g ? 'g' : ''}" data-n="${n}" data-d="${d}" data-s="${suf}">${nf(n, d)}${suf}</b><span class="sub">${sub}</span></div>`;

let F = { role: '', age: 23, small: false };
function find() {
  const base = M.top5_base_rate;
  let rows = P.filter(p => p[8] != null && !(p[9] >= 0.25) && p[2] <= F.age + 0.999 && (!F.role || p[4] === F.role) && (!F.small || (p[9] != null && p[9] < 0)));
  const total = rows.length; rows = rows.sort((a, b) => b[8] - a[8]).slice(0, 100);
  const G = 'grid-template-columns:minmax(200px,2.2fr) minmax(150px,1.5fr) .6fr .8fr 1fr 1fr';
  view.innerHTML = `<header class="rise"><h1>${t('findTitle')}</h1><p class="lead">${t('findLead')}</p></header>
  <div class="tiles">${tile(t('baseRate'), base * 100, 1, PS(), t('baseSub'))}${tile(t('inList'), total, 0, '', t('inListSub'), true)}${tile(t('hit'), 25, 0, PS(), t('hitSub'))}</div>
  <section class="rise"><div class="filters"><select id="frole" aria-label="${t('allRoles')}"><option value="">${t('allRoles')}</option>${Object.keys(ROLE).map(r => `<option value="${r}" ${F.role === r ? 'selected' : ''}>${ROLE[r][li()]}</option>`).join('')}</select>
  ${[19, 21, 23].map(a => `<button class="chip" data-age="${a}" aria-pressed="${F.age === a}">${t('maxAge')} ${a}</button>`).join('')}<button class="chip" id="fsmall" aria-pressed="${F.small}">${t('smallOnly')}</button></div>
  <div class="table"><div class="grid head" style="${G}"><span>${t('name')}</span><span>${t('league')}</span><span class="r">${t('age')}</span><span class="r">${t('value')}</span><span class="r">${t('chance')}</span><span class="r">${t('times')}</span></div>
  ${rows.map(p => `<a class="grid row" style="${G}" href="#player-${p[0]}"><span><strong>${esc(p[1])}</strong><br><span class="sub">${ROLE[p[4]][li()]} · ${esc(p[5] || '')}</span></span><span>${esc(p[6])}<br><span class="sub">${esc(p[3] || '')}</span></span><span class="r">${nf(p[2], 1)}</span><span class="r">${eur(p[10])}</span><span class="r"><strong>${pc(p[8])}</strong></span><span class="r"><span class="badge">×${nf(p[8] / base, 1)}</span></span></a>`).join('') || `<p class="empty">${t('noHit')}</p>`}</div></section>`;
  document.getElementById('frole').onchange = e => { F.role = e.target.value; find() };
  view.querySelectorAll('[data-age]').forEach(b => b.onclick = () => { F.age = +b.dataset.age; find() });
  document.getElementById('fsmall').onclick = () => { F.small = !F.small; find() }; countUp();
}
line.n = 0; line.reg = {};
const sp = P => { if (P.length < 3) return P.map((p, i) => (i ? 'L' : 'M') + p[0] + ' ' + p[1]).join(''); let d = 'M' + P[0][0] + ' ' + P[0][1];
  for (let i = 0; i < P.length - 1; i++) { const a = P[i - 1] || P[i], b = P[i], c = P[i + 1], e = P[i + 2] || c, k = 1 / 6;
    d += `C${b[0] + (c[0] - a[0]) * k} ${b[1] + (c[1] - a[1]) * k} ${c[0] - (e[0] - b[0]) * k} ${c[1] - (e[1] - b[1]) * k} ${c[0]} ${c[1]}` } return d };
/* Line chart with a readout above it: hovering moves a crosshair and markers, and the readout shows the numbers, so nothing ever covers the data. */
function line(pts, W, H, opt = {}) {
  const L = 52, R = 20, Tp = 16, B = 30, xs = pts.map(p => p[0]), ys = pts.flatMap(p => [p[1], p[2] ?? p[1], p[3] ?? p[1]]).concat((opt.extra || []).map(p => p[1]));
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = opt.y0 ?? 0, y1 = Math.max(...ys) * 1.08;
  const X = x => L + (W - L - R) * (x - x0) / Math.max(1, x1 - x0), Y = y => Tp + (H - Tp - B) * (1 - (y - y0) / (y1 - y0));
  const cid = 'c' + (++line.n), split = opt.split ?? pts.length, a = pts.slice(0, split), b = pts.slice(split - 1), proj = b.length > 1;
  let o = `<div class="readout" id="ro-${cid}"></div><svg data-ch="${cid}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.label || '')}" style="width:100%;height:auto;display:block;touch-action:pan-y">`;
  o += `<defs><linearGradient id="g${cid}" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="var(--signal)" stop-opacity=".26"/><stop offset="1" stop-color="var(--signal)" stop-opacity=".08"/></linearGradient><clipPath id="${cid}"><rect class="wipe" x="${L - 8}" y="0" width="${W - L - R + 16}" height="${H}"/></clipPath></defs>`;
  for (let k = 0; k <= 4; k++) { const v = y0 + (y1 - y0) * k / 4; o += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--faint)" stroke-opacity=".45"/><text x="${L - 8}" y="${Y(v) + 4}" text-anchor="end">${opt.fmt ? opt.fmt(v) : nf(v)}</text>` }
  pts.forEach((p, i) => { if (pts.length <= 14 || i % 2 === 0) o += `<text x="${X(p[0])}" y="${H - 8}" text-anchor="middle">${p[0]}</text>` });
  o += `<g clip-path="url(#${cid})">`;
  if (proj && b[1][2] != null) o += `<path d="${sp(b.map(p => [X(p[0]), Y(p[3] ?? p[1])])) + sp(b.slice().reverse().map(p => [X(p[0]), Y(p[2] ?? p[1])])).replace(/^M/, 'L')}Z" fill="url(#g${cid})"/>`;
  if (opt.extra) o += `<path d="${sp(opt.extra.map(p => [X(p[0]), Y(p[1])]))}" fill="none" stroke="var(--muted)" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 7"/>`;
  if (a.length > 1) o += `<path d="${sp(a.map(p => [X(p[0]), Y(p[1])]))}" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
  if (proj) o += `<path d="${sp(b.map(p => [X(p[0]), Y(p[1])]))}" fill="none" stroke="var(--signal)" stroke-width="3" stroke-linecap="round" ${opt.dash ? 'stroke-dasharray="2 8"' : ''}/>`;
  const e = a[a.length - 1]; o += `<circle cx="${X(e[0])}" cy="${Y(e[1])}" r="5" fill="var(--ink)"/></g>`;
  o += `<g class="ov"><line class="ovl" y1="${Tp}" y2="${H - B}" stroke="var(--muted)" stroke-width="1"/><rect class="ovr" x="-4" width="8" rx="4" fill="var(--signal)" opacity=".4"/><circle class="ov2" r="5" fill="var(--muted)" stroke="var(--card)" stroke-width="2.5"/><circle class="ov1" r="7" stroke="var(--card)" stroke-width="3"/></g></svg>`;
  line.reg[cid] = { pts, xs: pts.map(p => X(p[0])), Y, W, H, Tp, B, split, proj, extra: opt.extra, opt };
  return o;
}
function hydrate(svg) {
  const c = line.reg[svg.dataset.ch]; if (!c || svg._h) return; svg._h = 1;
  const ro = document.getElementById('ro-' + svg.dataset.ch), q = s => svg.querySelector(s), ov = q('.ov'), o = c.opt, f = o.val || o.fmt || (v => nf(v)), def = o.def ?? c.pts.length - 1;
  const isProj = i => c.proj && i >= c.split - 1 && (c.split === 1 || i > c.split - 1);
  const item = (sw, lab, val) => `<span class="ro-i"><span class="ro-l">${sw ? `<i style="background:${sw}"></i>` : ''}${lab}</span><b>${val}</b></span>`;
  const show = i => { const p = c.pts[i], xl = o.xl ? o.xl(p[0], i) : [p[0], '']; let h = item('', xl[1] || '&nbsp;', xl[0]) + item(isProj(i) ? 'var(--signal)' : 'var(--ink)', (o.names || [''])[0], f(p[1]));
    if (c.extra && c.extra[i]) h += item('var(--muted)', o.names[1], f(c.extra[i][1]));
    if (p[2] != null && p[2] !== p[3]) h += item('color-mix(in srgb,var(--signal) 40%,transparent)', t('range'), f(p[2]) + '–' + f(p[3]));
    ro.innerHTML = h };
  const move = ev => { const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) * c.W / r.width; let i = 0, bd = 1e9; c.xs.forEach((v, k) => { const d = Math.abs(v - x); if (d < bd) { bd = d; i = k } });
    const p = c.pts[i], px = c.xs[i]; ov.classList.add('on'); q('.ovl').style.transform = `translate(${px}px,0)`;
    const m1 = q('.ov1'); m1.style.transform = `translate(${px}px,${c.Y(p[1])}px)`; m1.setAttribute('fill', isProj(i) ? 'var(--signal)' : 'var(--ink)');
    const m2 = q('.ov2'), rr = q('.ovr'); m2.style.display = c.extra && c.extra[i] ? '' : 'none'; if (c.extra && c.extra[i]) m2.style.transform = `translate(${px}px,${c.Y(c.extra[i][1])}px)`;
    if (p[2] != null && p[2] !== p[3]) { rr.style.display = ''; rr.style.transform = `translate(${px}px,${c.Y(p[3])}px)`; rr.setAttribute('height', Math.max(0, c.Y(p[2]) - c.Y(p[3]))) } else rr.style.display = 'none';
    show(i) };
  svg.addEventListener('pointermove', move); svg.addEventListener('pointerdown', move);
  svg.addEventListener('pointerleave', () => { ov.classList.remove('on'); show(def) }); show(def);
}
async function showPlayer(id) {
  if (!id) {
    const ok = P.filter(p => p[10] && p[7] >= 600 && p[12] >= 1e6), top = (f, n = 24) => ok.filter(p => f(p) != null).sort((a, b) => f(b) - f(a)).slice(0, n);
    const car = (title, rows, big, sub) => `<section class="rise"><h2>${title}</h2><div class="car">${rows.map((p, i) => `<a class="pc" href="#player-${p[0]}" style="animation-delay:${i * 40}ms"><span class="sub">${ROLE[p[4]][li()]} · ${nf(p[2], 0)} ${t('yrs')}</span><strong>${esc(p[1])}</strong><span class="sub">${esc(p[5] || '')}</span><b>${big(p)}</b><span class="sub">${sub(p)}</span></a>`).join('')}</div></section>`;
    view.innerHTML = `<header class="rise" style="position:relative;z-index:5"><h1>${t('playerTitle')}</h1><div class="search bigs"><input id="pq" type="search" aria-label="${t('big')}" placeholder="${t('big')}" autocomplete="off"><div id="ph" class="hits" hidden></div></div></header>
    ${car(t('cGrow'), top(p => p[11]), p => '×' + nf(p[11], 1), p => eur(p[10]) + ' → ' + eur(p[10] * p[11]))}
    ${car(t('cUnder'), top(p => p[2] <= 25 ? p[10] / p[12] : null), p => '+' + nf((p[10] / p[12] - 1) * 100) + PS(), p => eur(p[10]) + ' ' + t('vsMv') + ' ' + eur(p[12]))}
    ${car(t('cStep'), top(p => p[9] >= 0.25 ? null : p[8]), p => pc(p[8]), p => esc(p[6]))}`;
    suggest(document.getElementById('pq'), document.getElementById('ph')); document.getElementById('pq').focus({ preventScroll: true }); return }
  view.innerHTML = `<p class="empty">${t('loading')}</p>`; const p = await player(+id);
  if (!p) { view.innerHTML = `<p class="empty">${t('noHit')}</p>`; return }
  const base = M.top5_base_rate, order = Object.keys(STAT), st = (p.stats || []).filter(s => STAT[s[0]]).sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]));
  const G = 'grid-template-columns:.8fr 1.6fr 1.6fr .6fr .6fr .6fr .6fr';
  const V = p.val, PT = p.path, vt = M.value_test, s3 = PT && V ? V[0] * PT[2][2] : null;
  const strong = st.filter(s => s[3] >= 75).sort((a, b) => b[3] - a[3]).slice(0, 4), weak = st.filter(s => s[3] <= 25).sort((a, b) => a[3] - b[3]).slice(0, 4);
  const chips = (xs, g) => xs.length ? xs.map(s => `<span class="badge" style="${g ? '' : 'background:var(--surface);color:var(--ink)'}">${STAT[s[0]][li()]} ${nf(Math.min(99, s[3]))}${PS()}</span>`).join(' ') : `<span class="sub">${t('none')}</span>`;
  const curve = V && PT ? [[2026, V[0] / 1e6, V[0] / 1e6, V[0] / 1e6]].concat(PT.map(r => [2026 + r[0], V[0] * r[2] / 1e6, V[0] * r[1] / 1e6, V[0] * r[3] / 1e6])) : null;
  const typ = V && p.typ ? [[2026, V[0] / 1e6]].concat(p.typ.map((g, i) => [2027 + i, V[0] * g / 1e6])) : null;
  view.innerHTML = `<header class="rise"><h1>${esc(p.name)}</h1><p class="lead">${ROLE[p.role][li()]} · ${nf(p.age, 1)} ${t('yrs')} · ${esc(p.team || '')} · ${esc(p.league)}${p.country ? ' · ' + esc(p.country) : ''}${p.contract ? ' · ' + t('until') + ' ' + p.contract.slice(0, 4) : ''}</p></header>
  ${V ? `<div class="tiles"><div class="tile rise"><span class="sub">${t('sv')}</span><b class="g">${eur(V[0])}</b><span class="sub">${t('svSub')} ${eur(V[1])}–${eur(V[2])}</span></div><div class="tile rise"><span class="sub">${t('mv3')}</span><b>${eur(V[3])}</b><span class="sub">Speider ${V[0] >= V[3] ? '+' : '−'}${nf(Math.abs(V[0] / V[3] - 1) * 100)}${PS()} ${t('vs')}</span></div>${s3 ? `<div class="tile rise"><span class="sub">${t('in3')}</span><b>${eur(s3)}</b><span class="sub">${t('in3Sub')} ${eur(V[0] * PT[2][1])}–${eur(V[0] * PT[2][3])}</span></div>` : ''}</div>` : ''}
  <div class="tiles">${p.p5 != null && !(p.ls >= 0.25) ? tile(t('p5'), p.p5 * 100, p.p5 < 0.1 ? 1 : 0, PS(), t('p5sub') + ' ' + pc(base), true) : ''}${tile(t('min'), p.minutes, 0, '', t('season') + ' ' + p.season)}${p.height ? tile(t('height'), p.height, 0, ' cm', '') : ''}</div>
  ${V && vt ? `<p class="note rise">${t('valNote').replace('{n}', nf(vt.n_test)).replace('{a}', nf(vt.speider_err * 100)).replace('{b}', nf(vt.third_party_err * 100))}</p>` : ''}
  ${curve ? `<section class="rise"><div><h2>${t('path')}</h2><p class="note">${t('pathSub')}</p></div><div class="card">${line(curve, 1040, 340, { split: 1, extra: typ, def: 3, fmt: v => nf(v, v < 10 ? 1 : 0), val: v => eur(v * 1e6), names: [esc(p.name.split(' ').slice(-1)[0]), t('tipTyp')], xl: x => [x, nf(p.age + x - 2026, 0) + ' ' + t('yrs')], label: t('path') })}<div class="grid" style="grid-template-columns:1.6fr repeat(5,1fr);padding:12px 16px 0;min-width:0;gap:8px"><span class="sub">${t('play')}</span>${PT.map(r => `<span class="r"><span class="sub">${2026 + r[0]}</span> <strong>${nf(r[4] * 100)}${PS()}</strong></span>`).join('')}</div></div></section>` : ''}
  ${st.length ? `<section class="rise"><h2>${t('profile')}</h2><div class="card" style="display:flex;flex-direction:column;gap:16px"><div><span class="sub">${t('strong')}</span><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">${chips(strong, true)}</div></div><div><span class="sub">${t('weak')}</span><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">${chips(weak, false)}</div></div>${p.sim && p.sim.length ? `<div><span class="sub">${t('similar')}</span><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">${p.sim.map(x => `<a class="chip" href="#player-${x[0]}">${esc(x[1])} <span class="sub">${esc(x[2] || '')} · ${nf(x[3], 0)}</span></a>`).join('')}</div></div>` : ''}</div></section>` : ''}
  ${st.length ? `<section class="rise"><div><h2>${t('quality')}</h2><p class="note">${t('qualitySub')}</p></div><div class="card">${st.map((s, i) => `<div class="bar" data-tip="${esc(t('tipStat').replace('{raw}', nf(s[2], 2)).replace('{adj}', nf(s[1], 2)).replace('{p}', nf(Math.min(99, s[3]))).replace('{n}', nf(s[4])))}"><span>${STAT[s[0]][li()]}</span><div class="track"><div class="fill ${s[3] >= 75 ? 'g' : ''}" style="width:${s[3]}%;animation-delay:${i * 45}ms"></div></div><span class="r"><strong>${nf(s[1], 2)}</strong> <span class="sub">${nf(Math.min(99, s[3]))}${PS()}</span></span></div>`).join('')}</div></section>` : ''}
  ${p.career ? `<section class="rise"><h2>${t('career')}</h2><div class="table"><div class="grid head" style="${G}"><span>${t('season')}</span><span>${t('league')}</span><span>${t('team')}</span><span class="r">${t('matches')}</span><span class="r">${t('goals')}</span><span class="r">${t('assists')}</span><span class="r">${t('rating')}</span></div>${p.career.map(c => `<div class="grid row" style="${G}"><span>${esc(c[0])}</span><span>${esc(c[1])}</span><span>${esc(c[2] || '')}</span><span class="r">${nf(c[3])}</span><span class="r">${nf(c[4])}</span><span class="r">${nf(c[5])}</span><span class="r">${c[6] ? nf(c[6], 2) : '–'}</span></div>`).join('')}</div></section>` : ''}
  ${p.mv && p.mv.length > 1 ? `<section class="rise"><div><h2>${t('mv')}</h2><p class="note">${t('mvSub')}</p></div><div class="card">${line(p.mv.map(m => [m[0], m[1] / 1e6]), 1040, 300, { fmt: v => nf(v, v < 10 ? 1 : 0), val: v => eur(v * 1e6), names: [t('mvShort')], xl: x => [x, nf(p.age + x - 2026, 0) + ' ' + t('yrs')], label: t('mv') })}</div></section>` : ''}`;
  countUp();
}
let E = { a: null, b: null };
async function eras() {
  if (!window.SP.eras) { view.innerHTML = `<p class="empty">${t('loading')}</p>`; await load('data/eras.js'); window.SP.erasN = window.SP.eras.map(r => norm(r[0])) }
  const D = window.SP.eras, N = window.SP.erasN;
  if (!E.a) { const i = D.findIndex(r => r[0] === 'Cristiano Ronaldo' && r[1] === 2008), j = D.findIndex(r => r[0] === 'Antonio Nusa' && r[1] === 2026); E.a = i >= 0 ? D[i] : D[0]; E.b = j >= 0 ? D[j] : D[1] }
  const side = (r, k) => `<div style="flex:1 1 300px;display:flex;flex-direction:column;gap:12px"><div class="search" style="max-width:none;margin:0;flex:none"><input id="e${k}" type="search" aria-label="${t('pick')}" placeholder="${t('pick')}" autocomplete="off"><div id="h${k}" class="hits" hidden></div></div><div><span class="sub">${esc(r[2])} ${r[1] - 1}/${String(r[1]).slice(2)} · ${esc(r[3])}</span><h2>${esc(r[0])}</h2></div></div>`;
  const rows = [[t('npg'), 8, 2, 1.5], [t('perc'), 10, 1, 100, PS(), 99.9], [t('sd'), 9, 2, 8], [t('goals'), 5, 0, 50], [t('assists'), 7, 0, 25], [t('min'), 4, 0, 3420]];
  view.innerHTML = `<header class="rise"><h1>${t('erasTitle')}</h1><p class="lead">${t('erasLead')}</p></header>
  <div class="rise" style="display:flex;flex-wrap:wrap;gap:24px;position:relative;z-index:5">${side(E.a, 'a')}${side(E.b, 'b')}</div>
  <section class="rise"><div class="card">${rows.map(([lab, i, d, mx, suf, cap]) => `<div class="duo"><span class="r"><strong>${nf(cap ? Math.min(cap, E.a[i]) : E.a[i], d)}${suf || ''}</strong></span><div class="track l"><div class="fill" style="width:${Math.max(2, Math.min(100, 100 * E.a[i] / mx))}%"></div></div><span style="text-align:center">${lab}</span><div class="track"><div class="fill g" style="width:${Math.max(2, Math.min(100, 100 * E.b[i] / mx))}%"></div></div><span><strong>${nf(cap ? Math.min(cap, E.b[i]) : E.b[i], d)}${suf || ''}</strong></span></div>`).join('')}</div></section>`;
  for (const k of ['a', 'b']) { const inp = document.getElementById('e' + k), box = document.getElementById('h' + k);
    inp.oninput = () => { const q = norm(inp.value.trim()); if (q.length < 3) { box.hidden = true; return } const out = [];
      for (let i = 0; i < N.length && out.length < 60; i++) if (N[i].includes(q)) out.push(i);
      out.sort((x, y) => D[y][1] - D[x][1]); box.hidden = false;
      box.innerHTML = out.map(i => `<a href="#eras" data-i="${i}"><span>${esc(D[i][0])} · ${D[i][1] - 1}/${String(D[i][1]).slice(2)}</span><small>${esc(D[i][2])} · ${esc(D[i][3])} · ${nf(D[i][5])} ${t('goals').toLowerCase()}</small></a>`).join('') || `<small style="padding:12px">${t('noHit')}</small>`;
      box.querySelectorAll('a').forEach(a => a.onclick = ev => { ev.preventDefault(); E[k] = D[+a.dataset.i]; eras() }) } }
}
function market() {
  const I = M.index, pr = M.projection, pts = I.map(r => [r[0], r[1]]).concat(pr.map(r => [r[0], r[1], r[2], r[3]])), g = Math.pow(I[I.length - 1][1] / I[0][1], 1 / (I.length - 1)) - 1, last = pr[pr.length - 1];
  const mx = Math.max(...M.leagues.map(l => l[2])), mn = Math.min(...M.leagues.map(l => l[2]));
  view.innerHTML = `<header class="rise"><h1>${t('marketTitle')}</h1><p class="lead">${t('marketLead')}</p></header>
  <div class="tiles">${tile(t('now'), 100, 0, '', '2026 = 100')}${tile(t('growth'), g * 100, 1, PS(), I[0][0] + '–' + I[I.length - 1][0])}${tile(t('y2034'), last[1], 0, '', last[2] + '–' + last[3], true)}</div>
  <section class="rise"><div><h2>${t('idx')}</h2><p class="note">${t('idxSub')}</p></div><div class="card">${line(pts, 1040, 340, { split: I.length, y0: 50, dash: true, names: [t('idx')], label: t('idx') })}</div></section>
  <section class="rise"><div><h2>${t('strength')}</h2><p class="note">${t('strengthSub')}</p></div><div class="card">${M.leagues.map((l, i) => `<div class="bar" data-tip="${esc(l[0] + ' (' + l[1] + ')\n' + t('strength') + ' ' + nf(l[2], 2))}"><span>${esc(l[0])} <span class="sub">${esc(l[1])}</span></span><div class="track"><div class="fill ${l[2] > 0.2 ? 'g' : ''}" style="width:${Math.max(2, 100 * (l[2] - mn) / (mx - mn))}%;animation-delay:${Math.min(i, 20) * 30}ms"></div></div><span class="r"><strong>${nf(l[2], 2)}</strong></span></div>`).join('')}</div></section>`;
  countUp();
}
function route() { chrome(); const [v, id] = location.hash.slice(1).split(/[\/-]/); window.scrollTo(0, 0);
  if (v === 'player') showPlayer(id); else if (v === 'eras') eras(); else if (v === 'market') market(); else find() }
const q = document.getElementById('q'), hits = document.getElementById('hits');
function suggest(q, hits) { q.oninput = () => { const s = norm(q.value.trim()); if (s.length < 2) { hits.hidden = true; return } let out = [];
  for (let i = 0; i < PN.length && out.length < 200; i++) if (PN[i].includes(s)) out.push(P[i]);
  out = out.sort((a, b) => (b[10] || 0) - (a[10] || 0)).slice(0, 12);
  hits.hidden = false; hits.innerHTML = out.map(p => `<a href="#player-${p[0]}"><span>${esc(p[1])}</span><small>${ROLE[p[4]][li()]} · ${esc(p[5] || '')} · ${esc(p[6])}</small></a>`).join('') || `<small style="padding:12px">${t('noHit')}</small>` };
  q.onkeydown = e => { if (e.key === 'Enter') { const a = hits.querySelector('a'); if (a) { location.hash = a.getAttribute('href'); hits.hidden = true; q.value = '' } } } }
suggest(q, hits);
document.addEventListener('click', e => { if (e.target.closest('.hits a')) { document.querySelectorAll('.hits').forEach(h => h.hidden = true); q.value = '' } else if (!e.target.closest('.search')) document.querySelectorAll('.hits').forEach(h => h.hidden = true) });
document.getElementById('lang').onclick = () => { lang = lang === 'no' ? 'en' : 'no'; try { localStorage.setItem('sp-lang', lang) } catch (e) { } route() };
const tipEl = document.body.appendChild(Object.assign(document.createElement('div'), { id: 'tip' }));
const showTip = e => { const el = e.target.closest && e.target.closest('[data-tip]'); if (!el) { tipEl.classList.remove('on'); return }
  tipEl.textContent = el.dataset.tip; tipEl.classList.add('on'); const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
  tipEl.style.left = Math.max(8, Math.min(innerWidth - w - 8, e.clientX + 14)) + 'px'; tipEl.style.top = (e.clientY - h - 14 < 8 ? e.clientY + 18 : e.clientY - h - 14) + 'px' };
document.addEventListener('pointermove', showTip); document.addEventListener('pointerdown', showTip); window.addEventListener('scroll', () => tipEl.classList.remove('on'), { passive: true });
const io = 'IntersectionObserver' in window ? new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target) } }), { threshold: 0.15 }) : null;
new MutationObserver(() => { view.querySelectorAll('svg[data-ch]').forEach(hydrate); view.querySelectorAll('.card:not(.in)').forEach(c => io ? io.observe(c) : c.classList.add('in')) }).observe(view, { childList: true, subtree: true });
window.addEventListener('hashchange', route); route();

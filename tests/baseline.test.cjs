const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../www/index.html'), 'utf8');
const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map(m => m[1]);
test('Inline JavaScript parses', () => {
  assert.ok(scripts.length > 0);
  scripts.forEach(s => new vm.Script(s));
});
// Temporary baseline harness: expose the existing calculation functions without changing production HTML.
// Replace with direct module imports when the calculation core is extracted.
const marker = 'function validPeriod(p)';
assert.ok(scripts[0].includes(marker), 'Update harness if calculation core moves');
const prefix = scripts[0].slice(0, scripts[0].indexOf(marker));
function core() {
  const ctx = vm.createContext({localStorage:{getItem:()=>null}, console});
  vm.runInContext(prefix + '\n globalThis.api={state,getCalendar,loadCalendar,compute,resolvePeriod,baseCalendars,iso}; })();', ctx);
  return ctx.api;
}
test('Calendar monthly working days match embedded reference for 2026/2027 and both schedules',()=>{
  const a=core();
  for(const y of [2026,2027]) for(const week of [5,6]) {
    assert.equal(a.getCalendar(y,week).monthly.join(','),a.baseCalendars[y]['expected'+week].join(','), `${y} ${week}`);
  }
});
test('July 2027 example: 14 paid days, 10 working days, +2327 RUB',()=>{
  const a=core(); a.loadCalendar();
  const r=a.compute([{start:'2027-07-05',end:'2027-07-18',type:'auto',inputMode:'dates'}],100000);
  assert.equal(r.error,null); assert.equal(r.paid,14); assert.equal(r.missed,10); assert.equal(Math.round(r.delta),2327);
});
test('June holiday excluded and duration mode extends by one day',()=>{
  const a=core(); a.loadCalendar();
  const p={start:'2027-06-07',end:'2027-06-20',type:'auto'};
  assert.equal(a.compute([{...p,inputMode:'dates'}]).paid,13);
  const r=a.compute([{...p,inputMode:'days',duration:14}]);
  assert.equal(r.paid,14); assert.equal(r.list[0].effectiveEnd,'2027-06-21');
});
test('Overlapping periods and cross-year duration are rejected',()=>{
  const a=core(); a.loadCalendar();
  const p={start:'2027-07-05',end:'2027-07-18',type:'auto',inputMode:'dates'};
  assert.ok(a.compute([p,p]).error);
  assert.ok(a.compute([{start:'2027-12-28',end:'2027-12-31',type:'auto',inputMode:'days',duration:14}]).error);
});
test('Salary mode changes interpretation, not formula',()=>{
  const a=core(); a.loadCalendar();
  const p=[{start:'2027-07-05',end:'2027-07-18',type:'auto',inputMode:'dates'}];
  const net=a.compute(p).delta; a.state.salaryMode='gross'; assert.equal(a.compute(p).delta,net);
});

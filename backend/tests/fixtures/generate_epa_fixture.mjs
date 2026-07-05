// Sinh fixture parity cho EPA — chạy TRỰC TIẾP code JS gốc trong legacy/fortune-hr/server.js
// (trích phần thuật toán thuần: LunarData → getCanChiFromBirthdate, không cần express/sqlite)
//
// Chạy: TZ=UTC node tests/fixtures/generate_epa_fixture.mjs
// Output: tests/fixtures/epa_parity_fortune_hr.json (commit vào repo để CI không cần node)
//
// ⚠️ BẮT BUỘC chạy với TZ=UTC: code JS gốc dùng new Date() theo múi giờ local —
// tzdata lịch sử của VN (đổi +7/+8/+9 giai đoạn 1906-1975) làm lệch 1 ngày ở vài mốc.
// Production Fortune HR chạy Docker TZ=UTC nên hành vi chuẩn = số học ngày thuần.

if (new Date().getTimezoneOffset() !== 0) {
  console.error('LOI: phai chay voi TZ=UTC (vd: TZ=UTC node generate_epa_fixture.mjs)');
  process.exit(1);
}

import { readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const serverJs = readFileSync(join(here, '../../../legacy/fortune-hr/server.js'), 'utf-8');

// Trích từ "const LunarData" đến ngay trước "// Get today's Can Chi"
const start = serverJs.indexOf('const LunarData');
const end = serverJs.indexOf("// Get today's Can Chi");
if (start < 0 || end < 0) throw new Error('Không tìm thấy phần thuật toán trong server.js');
const algoSource = serverJs.slice(start, end);

// eslint-disable-next-line no-new-func
const getCanChiFromBirthdate = new Function(
  algoSource + '\nreturn getCanChiFromBirthdate;'
)();

// PRNG seeded (mulberry32) để bộ ngày test tái lập được
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);

const cases = [];
// Case bắt buộc theo tài liệu + các mốc quanh Tết
const mandatory = [
  [1, 1, 1938],   // → Đinh Sửu (1937 âm), KHÔNG phải Mậu Dần
  [31, 1, 1938], [1, 2, 1938],
  [15, 2, 1985], [20, 2, 1985], [21, 2, 1985],
  [4, 2, 2000], [5, 2, 2000],
  [16, 2, 2026], [17, 2, 2026],
  [28, 1, 1960], [29, 1, 1960],
  [1, 1, 1900], [31, 1, 1900], [1, 2, 1900],
  [31, 12, 2099], [29, 2, 2000], [29, 2, 1996],
  [23, 1, 2012], [22, 1, 2012],
];
for (const [d, m, y] of mandatory) cases.push([d, m, y]);

// 280 ngày ngẫu nhiên 1900-2099 (seeded)
for (let i = 0; i < 280; i++) {
  const y = 1900 + Math.floor(rand() * 200);
  const m = 1 + Math.floor(rand() * 12);
  const maxDay = new Date(y, m, 0).getDate();
  const d = 1 + Math.floor(rand() * maxDay);
  cases.push([d, m, y]);
}

const fixture = cases.map(([day, month, year]) => ({
  input: { day, month, year },
  expected: getCanChiFromBirthdate(day, month, year),
}));

writeFileSync(
  join(here, 'epa_parity_fortune_hr.json'),
  JSON.stringify(fixture, null, 1),
  'utf-8'
);
console.log(`OK: ${fixture.length} cases -> epa_parity_fortune_hr.json`);
console.log('Case 1/1/1938:', JSON.stringify(fixture[0].expected.tuoiAm));

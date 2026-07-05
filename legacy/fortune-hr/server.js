const express = require('express');
const cors = require('cors');
const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const path = require('path');
const fs = require('fs');

require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'hpu-fortune-hr-secret-2025';

app.use(cors());
app.use(express.json());

// Database
const dbPath = process.env.DB_PATH || './data/fortune-hr.db';
const dbDir = path.dirname(dbPath);
if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });
const db = new Database(dbPath);
db.pragma('journal_mode = WAL');

// =====================================================
// LUNAR CALENDAR - Thuật toán chuẩn xác
// =====================================================
const LunarData = [
    0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,
    0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,
    0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,
    0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,
    0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,
    0x06ca0,0x0b550,0x15355,0x04da0,0x0a5d0,0x14573,0x052d0,0x0a9a8,0x0e950,0x06aa0,
    0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,
    0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b5a0,0x195a6,
    0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,
    0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x055c0,0x0ab60,0x096d5,0x092e0,
    0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,
    0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,
    0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,
    0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,
    0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,
    0x14b63,0x09370,0x049f8,0x04970,0x064b0,0x168a6,0x0ea50,0x06b20,0x1a6c4,0x0aae0,
    0x0a2e0,0x0d2e3,0x0c960,0x0d557,0x0d4a0,0x0da50,0x05d55,0x056a0,0x0a6d0,0x055d4,
    0x052d0,0x0a9b8,0x0a950,0x0b4a0,0x0b6a6,0x0ad50,0x055a0,0x0aba4,0x0a5b0,0x052b0,
    0x0b273,0x06930,0x07337,0x06aa0,0x0ad50,0x14b55,0x04b60,0x0a570,0x054e4,0x0d160,
    0x0e968,0x0d520,0x0daa0,0x16aa6,0x056d0,0x04ae0,0x0a9d4,0x0a2d0,0x0d150,0x0f252
];

function getLunarYearDays(y) {
    let sum = 348;
    for (let i = 0x8000; i > 0x8; i >>= 1) {
        sum += (LunarData[y - 1900] & i) ? 1 : 0;
    }
    return sum + getLeapDays(y);
}

function getLeapMonth(y) {
    return LunarData[y - 1900] & 0xf;
}

function getLeapDays(y) {
    if (getLeapMonth(y)) {
        return (LunarData[y - 1900] & 0x10000) ? 30 : 29;
    }
    return 0;
}

function getLunarMonthDays(y, m) {
    return (LunarData[y - 1900] & (0x10000 >> m)) ? 30 : 29;
}

// Convert solar date to lunar date
function getLunarDate(solarYear, solarMonth, solarDay) {
    if (solarYear < 1900 || solarYear > 2100) {
        return { lunarYear: solarYear, lunarMonth: solarMonth, lunarDay: solarDay };
    }
    
    // Base date: 1900-01-31 = Lunar 1900-01-01
    const baseDate = new Date(1900, 0, 31);
    const targetDate = new Date(solarYear, solarMonth - 1, solarDay);
    let offset = Math.floor((targetDate - baseDate) / 86400000);
    
    // Find lunar year
    let lunarYear = 1900;
    let daysInYear;
    while (lunarYear < 2100 && offset >= 0) {
        daysInYear = getLunarYearDays(lunarYear);
        if (offset < daysInYear) break;
        offset -= daysInYear;
        lunarYear++;
    }
    
    // Find lunar month
    let lunarMonth = 1;
    let leapMonth = getLeapMonth(lunarYear);
    let isLeapMonth = false;
    let daysInMonth;
    
    for (let i = 1; i <= 12; i++) {
        if (leapMonth > 0 && i === leapMonth + 1 && !isLeapMonth) {
            daysInMonth = getLeapDays(lunarYear);
            isLeapMonth = true;
            i--;
        } else {
            daysInMonth = getLunarMonthDays(lunarYear, i);
        }
        
        if (offset < daysInMonth) {
            lunarMonth = i;
            break;
        }
        offset -= daysInMonth;
    }
    
    let lunarDay = offset + 1;
    
    return { lunarYear, lunarMonth, lunarDay, isLeapMonth };
}

// Get Can Chi based on LUNAR year (CRITICAL FIX for people born before Tet!)
function getCanChiFromBirthdate(solarDay, solarMonth, solarYear) {
    const lunar = getLunarDate(solarYear, solarMonth, solarDay);
    
    // KEY: Use LUNAR YEAR for tuoi am
    // Example: 1/1/1938 dương → lunar năm Đinh Sửu (1937), NOT Mậu Dần (1938)
    const lunarYear = lunar.lunarYear;
    
    const THIEN_CAN = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý'];
    const DIA_CHI = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi'];
    const CON_GIAP = ['Chuột', 'Trâu', 'Hổ', 'Mèo', 'Rồng', 'Rắn', 'Ngựa', 'Dê', 'Khỉ', 'Gà', 'Chó', 'Lợn'];
    const EMOJI_GIAP = ['🐭', '🐮', '🐯', '🐱', '🐲', '🐍', '🐴', '🐐', '🐵', '🐔', '🐶', '🐷'];
    
    const NAP_AM = [
        'Hải Trung Kim', 'Hải Trung Kim', 'Lư Trung Hỏa', 'Lư Trung Hỏa',
        'Đại Lâm Mộc', 'Đại Lâm Mộc', 'Lộ Bàng Thổ', 'Lộ Bàng Thổ',
        'Kiếm Phong Kim', 'Kiếm Phong Kim', 'Sơn Đầu Hỏa', 'Sơn Đầu Hỏa',
        'Giản Hạ Thủy', 'Giản Hạ Thủy', 'Thành Đầu Thổ', 'Thành Đầu Thổ',
        'Bạch Lạp Kim', 'Bạch Lạp Kim', 'Dương Liễu Mộc', 'Dương Liễu Mộc',
        'Tuyền Trung Thủy', 'Tuyền Trung Thủy', 'Ốc Thượng Thổ', 'Ốc Thượng Thổ',
        'Tích Lịch Hỏa', 'Tích Lịch Hỏa', 'Tùng Bách Mộc', 'Tùng Bách Mộc',
        'Trường Lưu Thủy', 'Trường Lưu Thủy', 'Sa Trung Kim', 'Sa Trung Kim',
        'Sơn Hạ Hỏa', 'Sơn Hạ Hỏa', 'Bình Địa Mộc', 'Bình Địa Mộc',
        'Bích Thượng Thổ', 'Bích Thượng Thổ', 'Kim Bạch Kim', 'Kim Bạch Kim',
        'Phúc Đăng Hỏa', 'Phúc Đăng Hỏa', 'Thiên Hà Thủy', 'Thiên Hà Thủy',
        'Đại Trạch Thổ', 'Đại Trạch Thổ', 'Thoa Xuyến Kim', 'Thoa Xuyến Kim',
        'Tang Đố Mộc', 'Tang Đố Mộc', 'Đại Khê Thủy', 'Đại Khê Thủy',
        'Sa Trung Thổ', 'Sa Trung Thổ', 'Thiên Thượng Hỏa', 'Thiên Thượng Hỏa',
        'Thạch Lựu Mộc', 'Thạch Lựu Mộc', 'Đại Hải Thủy', 'Đại Hải Thủy'
    ];
    
    const MENH_MAP = {
        'Kim': ['Hải Trung Kim', 'Kiếm Phong Kim', 'Bạch Lạp Kim', 'Sa Trung Kim', 'Kim Bạch Kim', 'Thoa Xuyến Kim'],
        'Mộc': ['Đại Lâm Mộc', 'Dương Liễu Mộc', 'Tùng Bách Mộc', 'Bình Địa Mộc', 'Tang Đố Mộc', 'Thạch Lựu Mộc'],
        'Thủy': ['Giản Hạ Thủy', 'Tuyền Trung Thủy', 'Trường Lưu Thủy', 'Thiên Hà Thủy', 'Đại Khê Thủy', 'Đại Hải Thủy'],
        'Hỏa': ['Lư Trung Hỏa', 'Sơn Đầu Hỏa', 'Tích Lịch Hỏa', 'Sơn Hạ Hỏa', 'Phúc Đăng Hỏa', 'Thiên Thượng Hỏa'],
        'Thổ': ['Lộ Bàng Thổ', 'Thành Đầu Thổ', 'Ốc Thượng Thổ', 'Bích Thượng Thổ', 'Đại Trạch Thổ', 'Sa Trung Thổ']
    };
    
    // Calculate indices based on LUNAR year
    const canIdx = (lunarYear - 4) % 10;
    const chiIdx = (lunarYear - 4) % 12;
    const napAmIdx = (lunarYear - 4) % 60;
    
    const napAm = NAP_AM[napAmIdx];
    
    // Find Menh
    let menh = 'Thổ';
    for (const [element, napAmList] of Object.entries(MENH_MAP)) {
        if (napAmList.includes(napAm)) {
            menh = element;
            break;
        }
    }
    
    return {
        thienCan: THIEN_CAN[canIdx],
        diaChi: DIA_CHI[chiIdx],
        conGiap: CON_GIAP[chiIdx],
        emoji: EMOJI_GIAP[chiIdx],
        tuoiAm: THIEN_CAN[canIdx] + ' ' + DIA_CHI[chiIdx],
        napAm,
        menh,
        lunarYear,
        lunarMonth: lunar.lunarMonth,
        lunarDay: lunar.lunarDay
    };
}

// Get today's Can Chi for dashboard
function getTodayCanChi() {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    
    const lunar = getLunarDate(year, month, day);
    
    const THIEN_CAN = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý'];
    const DIA_CHI = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi'];
    
    // Can Chi năm (based on LUNAR year)
    const yearCan = THIEN_CAN[(lunar.lunarYear - 4) % 10];
    const yearChi = DIA_CHI[(lunar.lunarYear - 4) % 12];
    
    // Can Chi ngày (simple calculation)
    const baseDate = new Date(2000, 0, 7); // Ngày Giáp Tý
    const diff = Math.floor((today - baseDate) / 86400000);
    const dayCan = THIEN_CAN[((diff % 10) + 10) % 10];
    const dayChi = DIA_CHI[((diff % 12) + 12) % 12];
    
    return {
        solarDate: `${day}/${month}/${year}`,
        lunarDate: `${lunar.lunarDay}/${lunar.lunarMonth}/${lunar.lunarYear}`,
        lunarYear: lunar.lunarYear,
        lunarMonth: lunar.lunarMonth,
        lunarDay: lunar.lunarDay,
        yearCanChi: yearCan + ' ' + yearChi,
        dayCanChi: dayCan + ' ' + dayChi
    };
}

// =====================================================
// DATABASE INIT
// =====================================================
function initDatabase() {
    db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user',
            dept TEXT,
            position TEXT,
            can_see_all INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);
    
    db.exec(`
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            gender TEXT,
            day INTEGER,
            month INTEGER,
            year INTEGER,
            birth_time TEXT,
            dept TEXT,
            position TEXT,
            email TEXT,
            phone TEXT,
            relation TEXT,
            is_family INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);
    
    db.exec(`
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            parent_code TEXT,
            sort_order INTEGER DEFAULT 0
        )
    `);
    
    // Default admin users
    const existingAdmin = db.prepare('SELECT id FROM users WHERE email=?').get('trungth@hpu.edu.vn');
    if (!existingAdmin) {
        const hash = bcrypt.hashSync('123456', 10);
        db.prepare('INSERT INTO users(email,password,name,role,dept,position,can_see_all) VALUES(?,?,?,?,?,?,?)')
            .run('trungth@hpu.edu.vn', hash, 'Trần Hữu Trung', 'admin', 'Ban Giám hiệu', 'Phó Hiệu trưởng', 1);
        db.prepare('INSERT INTO users(email,password,name,role,dept,position,can_see_all) VALUES(?,?,?,?,?,?,?)')
            .run('nghith@hpu.edu.vn', hash, 'Trần Hữu Nghị', 'admin', 'Hội đồng Trường', 'Chủ tịch HĐT', 1);
    }
    
    console.log('✅ Database initialized');
}

// =====================================================
// AUTHENTICATION
// =====================================================
function auth(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ error: 'No token' });
    const token = authHeader.split(' ')[1];
    try {
        req.user = jwt.verify(token, JWT_SECRET);
        next();
    } catch (e) {
        res.status(401).json({ error: 'Invalid token' });
    }
}

// =====================================================
// API ROUTES
// =====================================================
app.post('/api/login', (req, res) => {
    const { email, password } = req.body;
    const user = db.prepare('SELECT * FROM users WHERE email=?').get(email);
    if (!user || !bcrypt.compareSync(password, user.password)) {
        return res.status(401).json({ error: 'Email hoặc mật khẩu không đúng' });
    }
    const token = jwt.sign({ id: user.id, email: user.email, name: user.name, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
    res.json({
        token,
        user: { id: user.id, email: user.email, name: user.name, role: user.role, dept: user.dept, position: user.position, canSeeAll: user.can_see_all }
    });
});

app.get('/api/me', auth, (req, res) => {
    const user = db.prepare('SELECT id,email,name,role,dept,position,can_see_all FROM users WHERE id=?').get(req.user.id);
    res.json(user);
});

// Employees (with deduplication check)
app.get('/api/employees', auth, (req, res) => {
    const employees = db.prepare('SELECT * FROM employees ORDER BY is_family DESC, dept, name').all();
    
    // Deduplicate by employee code
    const seen = new Set();
    const uniqueEmployees = employees.filter(e => {
        if (seen.has(e.code)) return false;
        seen.add(e.code);
        return true;
    });
    
    const result = uniqueEmployees.map(e => ({
        ...e,
        zodiac: getCanChiFromBirthdate(e.day, e.month, e.year)
    }));
    res.json(result);
});

app.get('/api/employees/:id', auth, (req, res) => {
    const emp = db.prepare('SELECT * FROM employees WHERE id=?').get(req.params.id);
    if (!emp) return res.status(404).json({ error: 'Không tìm thấy' });
    emp.zodiac = getCanChiFromBirthdate(emp.day, emp.month, emp.year);
    res.json(emp);
});

app.post('/api/employees', auth, (req, res) => {
    const { code, name, gender, day, month, year, birth_time, dept, position, email, phone, relation, is_family } = req.body;
    
    // Check duplicate code
    const existing = db.prepare('SELECT id FROM employees WHERE code=?').get(code);
    if (existing) {
        return res.status(400).json({ error: 'Mã nhân viên đã tồn tại!' });
    }
    
    try {
        const result = db.prepare('INSERT INTO employees(code,name,gender,day,month,year,birth_time,dept,position,email,phone,relation,is_family) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)')
            .run(code, name, gender, day, month, year, birth_time, dept, position, email, phone, relation, is_family ? 1 : 0);
        res.json({ id: result.lastInsertRowid, message: 'Đã thêm' });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.put('/api/employees/:id', auth, (req, res) => {
    const { name, gender, day, month, year, birth_time, dept, position, email, phone, relation, is_family } = req.body;
    db.prepare('UPDATE employees SET name=?,gender=?,day=?,month=?,year=?,birth_time=?,dept=?,position=?,email=?,phone=?,relation=?,is_family=? WHERE id=?')
        .run(name, gender, day, month, year, birth_time, dept, position, email, phone, relation, is_family ? 1 : 0, req.params.id);
    res.json({ message: 'Đã cập nhật' });
});

app.delete('/api/employees/:id', auth, (req, res) => {
    db.prepare('DELETE FROM employees WHERE id=?').run(req.params.id);
    res.json({ message: 'Đã xóa' });
});

// Remove duplicate employees
app.post('/api/employees/cleanup-duplicates', auth, (req, res) => {
    // Find and remove duplicates (keep first occurrence)
    const dupes = db.prepare(`
        SELECT code, COUNT(*) as cnt 
        FROM employees 
        GROUP BY code 
        HAVING cnt > 1
    `).all();
    
    let removed = 0;
    for (const d of dupes) {
        const rows = db.prepare('SELECT id FROM employees WHERE code=? ORDER BY id').all(d.code);
        for (let i = 1; i < rows.length; i++) {
            db.prepare('DELETE FROM employees WHERE id=?').run(rows[i].id);
            removed++;
        }
    }
    
    res.json({ message: `Đã xóa ${removed} bản ghi trùng lặp`, removed });
});

// List all employees (for admin review)
app.get('/api/employees/list-all', auth, (req, res) => {
    const all = db.prepare('SELECT id, code, name, dept, position, is_family FROM employees ORDER BY id').all();
    res.json({ total: all.length, employees: all });
});

// Delete employees by name (for cleanup fake data)
app.post('/api/employees/delete-by-names', auth, (req, res) => {
    const { names } = req.body; // Array of names to delete
    if (!names || !Array.isArray(names)) {
        return res.status(400).json({ error: 'Cần truyền mảng names' });
    }
    
    let deleted = 0;
    const deletedNames = [];
    
    for (const name of names) {
        const emp = db.prepare('SELECT id, name, code FROM employees WHERE name = ?').get(name);
        if (emp) {
            db.prepare('DELETE FROM employees WHERE id = ?').run(emp.id);
            deleted++;
            deletedNames.push({ id: emp.id, name: emp.name, code: emp.code });
        }
    }
    
    res.json({ message: `Đã xóa ${deleted} người`, deleted, deletedNames });
});

// Delete employee by code
app.delete('/api/employees/by-code/:code', auth, (req, res) => {
    const code = req.params.code;
    const emp = db.prepare('SELECT id, name FROM employees WHERE code = ?').get(code);
    if (!emp) {
        return res.status(404).json({ error: 'Không tìm thấy mã ' + code });
    }
    db.prepare('DELETE FROM employees WHERE code = ?').run(code);
    res.json({ message: `Đã xóa ${emp.name} (${code})` });
});

// Search employees
app.get('/api/employees/search/:keyword', auth, (req, res) => {
    const keyword = '%' + req.params.keyword + '%';
    const results = db.prepare('SELECT id, code, name, dept, position, is_family FROM employees WHERE name LIKE ? OR code LIKE ?').all(keyword, keyword);
    res.json(results);
});

// Departments
app.get('/api/departments', auth, (req, res) => {
    res.json(db.prepare('SELECT * FROM departments ORDER BY sort_order').all());
});

app.post('/api/departments', auth, (req, res) => {
    const { code, name, parent_code } = req.body;
    try {
        const result = db.prepare('INSERT INTO departments(code,name,parent_code) VALUES(?,?,?)').run(code, name, parent_code);
        res.json({ id: result.lastInsertRowid });
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.put('/api/departments/:id', auth, (req, res) => {
    const { name, parent_code, sort_order } = req.body;
    db.prepare('UPDATE departments SET name=?,parent_code=?,sort_order=? WHERE id=?').run(name, parent_code, sort_order, req.params.id);
    res.json({ message: 'Đã cập nhật' });
});

app.delete('/api/departments/:id', auth, (req, res) => {
    db.prepare('DELETE FROM departments WHERE id=?').run(req.params.id);
    res.json({ message: 'Đã xóa' });
});

// Stats
app.get('/api/stats', auth, (req, res) => {
    const totalEmployees = db.prepare('SELECT COUNT(*) as c FROM employees WHERE is_family=0').get().c;
    const totalFamily = db.prepare('SELECT COUNT(*) as c FROM employees WHERE is_family=1').get().c;
    const totalDepts = db.prepare('SELECT COUNT(DISTINCT dept) as c FROM employees').get().c;
    const currentMonth = new Date().getMonth() + 1;
    const birthdays = db.prepare('SELECT COUNT(*) as c FROM employees WHERE month=?').get(currentMonth).c;
    res.json({ totalEmployees, totalFamily, totalDepts, birthdays });
});

// Today's Can Chi
app.get('/api/today', auth, (req, res) => {
    res.json(getTodayCanChi());
});

// Zodiac calculation API
app.get('/api/zodiac/:day/:month/:year', auth, (req, res) => {
    const { day, month, year } = req.params;
    res.json(getCanChiFromBirthdate(parseInt(day), parseInt(month), parseInt(year)));
});

// Lunar date conversion API (for frontend to call)
app.get('/api/lunar/:day/:month/:year', auth, (req, res) => {
    const { day, month, year } = req.params;
    const lunar = getLunarDate(parseInt(year), parseInt(month), parseInt(day));
    res.json(lunar);
});

// Team suggestion
app.post('/api/team-suggest', auth, (req, res) => {
    const { size, deptFilter } = req.body;
    
    const TAM_HOP = [
        ['Thân', 'Tý', 'Thìn'],
        ['Tỵ', 'Dậu', 'Sửu'],
        ['Dần', 'Ngọ', 'Tuất'],
        ['Hợi', 'Mão', 'Mùi']
    ];
    
    const XUNG = [
        ['Tý', 'Ngọ'], ['Sửu', 'Mùi'], ['Dần', 'Thân'],
        ['Mão', 'Dậu'], ['Thìn', 'Tuất'], ['Tỵ', 'Hợi']
    ];
    
    let emps = db.prepare('SELECT * FROM employees WHERE is_family=0').all();
    if (deptFilter) emps = emps.filter(e => e.dept === deptFilter);
    if (emps.length < size) return res.json({ teams: [] });
    
    emps = emps.map(e => ({ ...e, zodiac: getCanChiFromBirthdate(e.day, e.month, e.year) }));
    
    function getScore(e1, e2) {
        let score = 50;
        TAM_HOP.forEach(g => {
            if (g.includes(e1.zodiac.diaChi) && g.includes(e2.zodiac.diaChi)) score += 25;
        });
        XUNG.forEach(p => {
            if (p.includes(e1.zodiac.diaChi) && p.includes(e2.zodiac.diaChi)) score -= 30;
        });
        return Math.min(100, Math.max(0, score));
    }
    
    const teams = [];
    for (let i = 0; i < 3; i++) {
        const shuffled = [...emps].sort(() => Math.random() - 0.5);
        const team = shuffled.slice(0, size);
        let total = 0, cnt = 0;
        for (let a = 0; a < team.length; a++) {
            for (let b = a + 1; b < team.length; b++) {
                total += getScore(team[a], team[b]);
                cnt++;
            }
        }
        teams.push({ members: team, score: Math.round(total / (cnt || 1)) });
    }
    teams.sort((a, b) => b.score - a.score);
    res.json({ teams });
});

// Compatibility check
app.get('/api/compatibility/:id1/:id2', auth, (req, res) => {
    const TAM_HOP = [
        ['Thân', 'Tý', 'Thìn'],
        ['Tỵ', 'Dậu', 'Sửu'],
        ['Dần', 'Ngọ', 'Tuất'],
        ['Hợi', 'Mão', 'Mùi']
    ];
    
    const XUNG = [
        ['Tý', 'Ngọ'], ['Sửu', 'Mùi'], ['Dần', 'Thân'],
        ['Mão', 'Dậu'], ['Thìn', 'Tuất'], ['Tỵ', 'Hợi']
    ];
    
    const e1 = db.prepare('SELECT * FROM employees WHERE id=?').get(req.params.id1);
    const e2 = db.prepare('SELECT * FROM employees WHERE id=?').get(req.params.id2);
    if (!e1 || !e2) return res.status(404).json({ error: 'Không tìm thấy' });
    
    const z1 = getCanChiFromBirthdate(e1.day, e1.month, e1.year);
    const z2 = getCanChiFromBirthdate(e2.day, e2.month, e2.year);
    
    let score = 50;
    const notes = [];
    
    TAM_HOP.forEach(g => {
        if (g.includes(z1.diaChi) && g.includes(z2.diaChi)) {
            score += 25;
            notes.push('Tam hợp: Rất tương hợp');
        }
    });
    
    XUNG.forEach(p => {
        if (p.includes(z1.diaChi) && p.includes(z2.diaChi)) {
            score -= 30;
            notes.push('Xung: Dễ mâu thuẫn');
        }
    });
    
    score = Math.min(100, Math.max(0, score));
    res.json({ person1: { ...e1, zodiac: z1 }, person2: { ...e2, zodiac: z2 }, score, notes });
});

// =====================================================
// START SERVER
// =====================================================
initDatabase();
app.listen(PORT, () => console.log('🚀 Fortune HR v6.1 running on port ' + PORT));

# 🔮 Fortune HR v6.2 - Trợ Lý Tử Vi Phong Thủy HPU

## 📋 Các bugs đã fix trong v6.2

| # | Bug | Sửa |
|---|-----|-----|
| 1 | **CSS hiện lỗi** trên Dashboard & Nhịp sinh học | ✅ Rebuild hoàn toàn HTML với CSS đúng format |
| 2 | **Dropdown lặp** người gia đình 2 lần | ✅ Thêm deduplication bằng `seen.has(e.code)` |
| 3 | **Dữ liệu sai** (Vũ Văn Hải, Nguyễn Văn Đạt...) | ⚠️ Cần cleanup DB - chạy cleanup API |
| 4 | **Thiếu dự báo tuần/tháng** | ✅ Thêm Dự báo tuần + tháng trong Xem tử vi |
| 5 | **Thiếu biểu đồ nhịp sinh học** | ✅ Thêm Chart.js biểu đồ 30 ngày |

## 🆕 Tính năng mới v6.2

- **Dự báo tuần này** - Hiển thị vận số, lời khuyên cho tuần
- **Dự báo tháng này** - Hiển thị vận số, lời khuyên cho tháng
- **Biểu đồ nhịp sinh học** - Chart 30 ngày với 3 đường (thể chất, cảm xúc, trí tuệ)
- **Filter nhân viên/gia đình** - Nút lọc nhanh
- **Dropdown không lặp** - Mỗi người chỉ hiện 1 lần

## 🚀 Deploy

```bash
# SSH vào server
ssh root@hpu-server

# Backup DB cũ
docker exec tuvi-backend cp /app/data/fortune-hr.db /app/data/fortune-hr.db.bak

# Upload và giải nén
cd /root/trungth
unzip -o fortune-hr-v6.2.zip
mv fortune-hr-v6.2 fortune-hr-v65

# Deploy
cd fortune-hr-v65/docker
docker compose down
docker compose up -d --build

# Cleanup dữ liệu sai (Vũ Văn Hải, etc)
TOKEN=$(curl -s -X POST http://localhost:3001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"trungth@hpu.edu.vn","password":"123456"}' | \
  grep -o '"token":"[^"]*"' | cut -d'"' -f4)

curl -X POST http://localhost:3001/api/employees/cleanup-duplicates \
  -H "Authorization: Bearer $TOKEN"
```

## 🧹 Cleanup dữ liệu sai

Nếu DB có những người không phải nhân viên (Vũ Văn Hải, Nguyễn Văn Đạt, Nguyễn Văn Thắng...), cần xóa thủ công:

```bash
# Vào container
docker exec -it tuvi-backend sh

# Xóa người không phải NV
sqlite3 /app/data/fortune-hr.db "DELETE FROM employees WHERE code LIKE 'HPU0%' AND name IN ('Vũ Văn Hải', 'Nguyễn Văn Đạt', 'Nguyễn Văn Thắng', 'Lê Văn Đạt', 'Lê Văn Tâm');"

# Hoặc reset toàn bộ DB
rm /app/data/fortune-hr.db
# Restart container để tạo DB mới
docker restart tuvi-backend
```

## 🧪 Test sau deploy

1. **Login:** https://tuvi.hpu.edu.vn
2. **Dashboard:** Không còn CSS code hiện
3. **Xem tử vi:** Có dự báo tuần + tháng
4. **Nhịp sinh học:** Có biểu đồ 30 ngày
5. **Dropdown:** Mỗi người chỉ hiện 1 lần

---
**Version:** 6.2  
**Date:** 16/3/2026

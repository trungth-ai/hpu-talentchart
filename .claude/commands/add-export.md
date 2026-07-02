# Export Excel — Tạo endpoint xuất Excel cho module
# File: .claude/commands/add-export.md
# Sử dụng: /add-export employees

Thêm tính năng xuất Excel cho module "$ARGUMENTS".

## Yêu cầu

1. **API endpoint**: GET /api/v1/$ARGUMENTS/export
   - Query params: filter giống endpoint list (department_id, status, search...)
   - Return: file .xlsx download

2. **Code pattern**:
```python
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO

@router.get("/export")
async def export_excel(
    # Same filters as list endpoint
    db: Session = Depends(get_db)
):
    # Query data (same logic as list, without pagination)
    items = query.all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Danh sách"
    
    # Header row styling
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1E3A5F", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Headers
    headers = ["STT", "Mã", "Tên", ...]  # Tiếng Việt
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    
    # Data rows
    for idx, item in enumerate(items, 1):
        row = idx + 1
        ws.cell(row=row, column=1, value=idx)
        ws.cell(row=row, column=2, value=item.code)
        # Money columns: format
        money_cell = ws.cell(row=row, column=N, value=item.salary)
        money_cell.number_format = '#,##0'
        money_cell.alignment = Alignment(horizontal='right')
    
    # Auto-fit column width
    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 4, 30)
    
    # Freeze header row
    ws.freeze_panes = "A2"
    
    # Return as download
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"DanhSach_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

3. **UI**: Thêm nút "Xuất Excel" trên trang danh sách
```html
<a href="/api/v1/$ARGUMENTS/export" 
   class="px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 
          rounded-lg hover:bg-gray-50 inline-flex items-center gap-1">
  📥 Xuất Excel
</a>
```

4. **Dependencies**: Thêm `openpyxl` vào requirements.txt nếu chưa có

Đảm bảo:
- Header tiếng Việt
- Money format #,##0 (Excel tự hiểu dấu phẩy)
- Auto-fit column width
- Freeze header row
- File name có timestamp

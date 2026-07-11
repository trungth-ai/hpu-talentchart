# Dữ liệu 12 cung hoàng đạo (chiêm tinh phương Tây) — tính cách đặc trưng theo ngày sinh.
# Nguồn nội dung: sách "12 Chòm Sao Và Đời Người" (Trung cung cấp) — màu sắc may mắn,
# sao bảo hộ, điểm mạnh (Sự thu hút), điểm yếu (Chỗ thiếu sót), tính cách (mục III).
# Nghề phù hợp: chắt lọc theo đặc trưng tính cách của từng cung.
#
# LƯU Ý nghiệp vụ: đây là thông tin tham khảo, KHÔNG dùng làm yếu tố quyết định tuyển dụng.

from datetime import date

# (start_month, start_day) — mốc BẮT ĐẦU cung; cung cuối (Ma Kết) vắt qua năm.
# name = tên phổ thông hiện nay; name_book = tên trong sách nguồn.
HOROSCOPE_SIGNS: list[dict] = [
    {
        "code": "ARIES",
        "name": "Bạch Dương",
        "name_book": "Bạch Dương",
        "emoji": "♈",
        "date_range": "21/3 – 19/4",
        "element": "Hỏa tượng",
        "ruling_planet": "Sao Hỏa",
        "lucky_colors": ["Đỏ sẫm", "Vàng"],
        "personality": (
            "Thẳng thắn, tư tưởng tiến bộ, yêu tự do và tràn đầy sức sống. Giỏi khởi đầu, "
            "hành động độc lập, có chí tiến thủ và khả năng ứng biến nhanh; nhưng nóng nảy, "
            "thiếu kiên nhẫn và dễ bỏ dở khi mất hứng thú."
        ),
        "strengths": ["Tự tin", "Nhiệt tình", "Dũng cảm, dám tiên phong", "Quyết đoán, hành động nhanh"],
        "weaknesses": ["Nóng vội, thiếu kiên nhẫn", "Bốc đồng, cẩu thả tiểu tiết", "Dễ đắc tội người khác", "Khó bền chí"],
        "careers": ["Lãnh đạo, quản lý dự án", "Kinh doanh, khởi nghiệp", "Thể thao, lực lượng vũ trang", "Công việc cần tiên phong đổi mới"],
    },
    {
        "code": "TAURUS",
        "name": "Kim Ngưu",
        "name_book": "Kim Ngưu",
        "emoji": "♉",
        "date_range": "20/4 – 20/5",
        "element": "Thổ tượng",
        "ruling_planet": "Sao Kim",
        "lucky_colors": ["Lam"],
        "personality": (
            "Vững vàng, kiên định, giỏi chăm sóc người khác nên tạo cảm giác an tâm, đáng tin. "
            "Hiền lành, vui vẻ, thực tế; nhưng dễ trở nên cứng nhắc, cố chấp và chậm thay đổi."
        ),
        "strengths": ["Kiên trì, bền bỉ", "Đáng tin cậy", "Thực tế, giỏi quản lý tài chính", "Điềm tĩnh, chu đáo"],
        "weaknesses": ["Cố chấp, cứng nhắc", "Chậm thích nghi cái mới", "Bảo thủ", "Hay trì hoãn quyết định"],
        "careers": ["Tài chính, kế toán", "Quản lý tài sản, ngân hàng", "Nông nghiệp, ẩm thực", "Nghệ thuật, thiết kế"],
    },
    {
        "code": "GEMINI",
        "name": "Song Tử",
        "name_book": "Song Tử",
        "emoji": "♊",
        "date_range": "21/5 – 21/6",
        "element": "Phong tượng",
        "ruling_planet": "Sao Thủy",
        "lucky_colors": ["Vàng", "Xanh nhạt", "Xanh lá cây"],
        "personality": (
            "Hiếu kỳ, linh hoạt, thái độ sống phong phú đa dạng, sức sống dồi dào và giao tiếp "
            "khéo léo. Thông minh, phản ứng nhanh; nhưng dễ nôn nóng, thiếu nhẫn nại và hay thay đổi."
        ),
        "strengths": ["Nhanh nhẹn, thông minh", "Giao tiếp giỏi", "Ham học hỏi, đa năng", "Thích ứng nhanh"],
        "weaknesses": ["Thiếu kiên nhẫn", "Hay thay đổi, khó nhất quán", "Dễ phân tán", "Nói nhanh hơn làm"],
        "careers": ["Truyền thông, báo chí, PR", "Bán hàng, đàm phán", "Giáo dục, đào tạo", "Công nghệ thông tin"],
    },
    {
        "code": "CANCER",
        "name": "Cự Giải",
        "name_book": "Cự Giải",
        "emoji": "♋",
        "date_range": "22/6 – 22/7",
        "element": "Thủy tượng",
        "ruling_planet": "Mặt Trăng",
        "lucky_colors": ["Trắng bạc", "Chàm", "Xanh"],
        "personality": (
            "Giàu tình cảm, thấu hiểu và biết thông cảm, gắn bó với gia đình. Lắng nghe và chăm "
            "sóc người khác tận tâm; nhưng dễ đa cảm, nhạy cảm quá mức và khó buông bỏ."
        ),
        "strengths": ["Thấu cảm, tận tâm", "Chăm sóc, bảo bọc", "Trung thành", "Trực giác tốt"],
        "weaknesses": ["Đa cảm, dễ tổn thương", "Hay giữ trong lòng", "Ngại thay đổi", "Dễ bị cảm xúc chi phối"],
        "careers": ["Nhân sự, công tác xã hội", "Y tế, chăm sóc", "Giáo dục mầm non", "Dịch vụ khách hàng, hậu cần"],
    },
    {
        "code": "LEO",
        "name": "Sư Tử",
        "name_book": "Sư Tử",
        "emoji": "♌",
        "date_range": "23/7 – 22/8",
        "element": "Hỏa tượng",
        "ruling_planet": "Mặt Trời",
        "lucky_colors": ["Cam", "Đỏ sẫm", "Tím"],
        "personality": (
            "Phong thái vương giả, ngay thẳng phóng khoáng, thích giao tiếp và rất có khả năng "
            "lãnh đạo, biết khơi gợi khí chất tập thể. Nhiệt tình, tự tin; nhưng dễ tự cao, "
            "võ đoán và thích nắm quyền."
        ),
        "strengths": ["Khả năng lãnh đạo", "Tự tin, hào phóng", "Nhiệt tình, cuốn hút", "Nêu gương, nỗ lực"],
        "weaknesses": ["Tự cao, tự cho mình đúng", "Thích quyền lực", "Khó bao dung", "Sĩ diện"],
        "careers": ["Quản lý cấp cao, điều hành", "Nghệ thuật biểu diễn, MC", "Đào tạo, truyền cảm hứng", "Kinh doanh, thương hiệu"],
    },
    {
        "code": "VIRGO",
        "name": "Xử Nữ",
        "name_book": "Xử Nữ",
        "emoji": "♍",
        "date_range": "23/8 – 22/9",
        "element": "Thổ tượng",
        "ruling_planet": "Sao Thủy",
        "lucky_colors": ["Xám", "Vàng"],
        "personality": (
            "Tỉ mỉ, cẩn thận, coi trọng sự chính xác và hoàn hảo. Phân tích tốt, có trách nhiệm, "
            "thực tế và chăm chỉ; nhưng dễ cầu toàn, hay lo lắng và khắt khe với bản thân lẫn người khác."
        ),
        "strengths": ["Tỉ mỉ, chính xác", "Phân tích, logic", "Trách nhiệm, chăm chỉ", "Thực tế, ngăn nắp"],
        "weaknesses": ["Cầu toàn quá mức", "Hay lo lắng, soi xét", "Khắt khe, khó tính", "Ngại rủi ro"],
        "careers": ["Kế toán, kiểm toán, kiểm soát chất lượng", "Phân tích dữ liệu, nghiên cứu", "Y dược", "Biên tập, hành chính"],
    },
    {
        "code": "LIBRA",
        "name": "Thiên Bình",
        "name_book": "Thiên Xứng",
        "emoji": "♎",
        "date_range": "23/9 – 23/10",
        "element": "Phong tượng",
        "ruling_planet": "Sao Kim",
        "lucky_colors": ["Xanh nhạt"],
        "personality": (
            "Nho nhã, công bằng, giữ thái độ trung dung và ưa hòa hợp. Hiểu biết, lý giải và tư "
            "duy logic tốt, giỏi xã giao, yêu cái đẹp; nhưng do dự, thiếu quyết đoán và hay né tránh xung đột."
        ),
        "strengths": ["Công bằng, khách quan", "Giao tiếp, ngoại giao khéo", "Thẩm mỹ tốt", "Ôn hòa, biết lắng nghe"],
        "weaknesses": ["Do dự, khó quyết đoán", "Ngại va chạm", "Hay ỷ lại", "Tránh né hiện thực"],
        "careers": ["Nhân sự, đối ngoại, ngoại giao", "Luật, hòa giải", "Thiết kế, nghệ thuật", "Tư vấn, dịch vụ khách hàng"],
    },
    {
        "code": "SCORPIO",
        "name": "Bọ Cạp",
        "name_book": "Bò Cạp",
        "emoji": "♏",
        "date_range": "24/10 – 21/11",
        "element": "Thủy tượng",
        "ruling_planet": "Sao Diêm Vương",
        "lucky_colors": ["Đỏ sẫm", "Đỏ"],
        "personality": (
            "Sâu sắc, mãnh liệt, ý chí mạnh và rất trọng lời hứa. Kiên định, quyết tâm cao, trực "
            "giác nhạy; nhưng dễ cực đoan trong cảm xúc, đa nghi và khó tha thứ khi bị phản bội."
        ),
        "strengths": ["Ý chí mạnh, quyết tâm", "Trung thành, giữ lời", "Sâu sắc, trực giác", "Bền bỉ theo mục tiêu"],
        "weaknesses": ["Đa nghi, hay ghen", "Cực đoan, cố chấp", "Khó tha thứ", "Kín đáo, khó gần"],
        "careers": ["Nghiên cứu, điều tra", "Tài chính, kiểm soát rủi ro", "Y khoa, tâm lý", "An ninh, pháp lý"],
    },
    {
        "code": "SAGITTARIUS",
        "name": "Nhân Mã",
        "name_book": "Xạ Thủ",
        "emoji": "♐",
        "date_range": "22/11 – 21/12",
        "element": "Hỏa tượng",
        "ruling_planet": "Sao Mộc",
        "lucky_colors": ["Tím"],
        "personality": (
            "Lạc quan, yêu tự do, thích khám phá và mở rộng tầm nhìn. Chân thành, rộng lượng, "
            "nhiệt huyết; nhưng thiếu kiên nhẫn với chi tiết, hay hứa quá và ngại ràng buộc."
        ),
        "strengths": ["Lạc quan, nhiệt huyết", "Thẳng thắn, chân thành", "Ham học, tầm nhìn rộng", "Thích nghi, phiêu lưu"],
        "weaknesses": ["Thiếu kiên nhẫn", "Hứa nhiều, ngại ràng buộc", "Bất cẩn chi tiết", "Nói thẳng dễ mất lòng"],
        "careers": ["Giáo dục, đào tạo, học thuật", "Du lịch, đối ngoại quốc tế", "Truyền thông, xuất bản", "Kinh doanh mở rộng thị trường"],
    },
    {
        "code": "CAPRICORN",
        "name": "Ma Kết",
        "name_book": "Ma Kiệt",
        "emoji": "♑",
        "date_range": "22/12 – 19/1",
        "element": "Thổ tượng",
        "ruling_planet": "Sao Thổ",
        "lucky_colors": ["Nâu đậm"],
        "personality": (
            "Điềm tĩnh, kỷ luật, thực tế và có tham vọng bền bỉ. Trách nhiệm cao, kiên nhẫn theo "
            "đuổi mục tiêu dài hạn; nhưng dễ lạnh lùng, quá đề phòng và khắt khe."
        ),
        "strengths": ["Kỷ luật, kiên nhẫn", "Trách nhiệm, đáng tin", "Thực tế, có kế hoạch", "Bền chí, tham vọng"],
        "weaknesses": ["Lạnh lùng, khó gần", "Quá đề phòng", "Bảo thủ, cứng nhắc", "Ôm đồm áp lực"],
        "careers": ["Quản lý, quản trị vận hành", "Tài chính, đầu tư dài hạn", "Kỹ thuật, xây dựng", "Hành chính, pháp chế"],
    },
    {
        "code": "AQUARIUS",
        "name": "Bảo Bình",
        "name_book": "Thủy Bình",
        "emoji": "♒",
        "date_range": "20/1 – 18/2",
        "element": "Phong tượng",
        "ruling_planet": "Sao Thiên Vương",
        "lucky_colors": ["Xanh"],
        "personality": (
            "Thuần khiết, độc lập, tư duy đổi mới và trọng lý tưởng nhân văn. Sáng tạo, khách quan, "
            "thành thật; nhưng đôi khi hành động chưa quyết liệt và hơi xa cách trong cảm xúc."
        ),
        "strengths": ["Sáng tạo, đổi mới", "Độc lập, khách quan", "Nhân văn, vì cộng đồng", "Thành thật, cởi mở"],
        "weaknesses": ["Hành động chưa dứt khoát", "Xa cách cảm xúc", "Bướng, khó đoán", "Lý tưởng hóa"],
        "careers": ["Công nghệ, nghiên cứu & phát triển", "Sáng tạo, đổi mới", "Hoạt động xã hội, phi lợi nhuận", "Khoa học dữ liệu"],
    },
    {
        "code": "PISCES",
        "name": "Song Ngư",
        "name_book": "Song Ngư",
        "emoji": "♓",
        "date_range": "19/2 – 20/3",
        "element": "Thủy tượng",
        "ruling_planet": "Sao Hải Vương",
        "lucky_colors": ["Bạc xám", "Tím"],
        "personality": (
            "Giàu cảm thụ, tinh tế, nhân hậu và mơ mộng. Đồng cảm sâu, sáng tạo, vị tha; nhưng "
            "dễ mềm lòng, thiếu thực tế và hay bị cảm xúc dẫn dắt."
        ),
        "strengths": ["Đồng cảm, nhân hậu", "Sáng tạo, giàu tưởng tượng", "Vị tha, dịu dàng", "Trực giác tốt"],
        "weaknesses": ["Mềm lòng, dễ mủi lòng", "Thiếu thực tế", "Hay né tránh", "Dễ bị chi phối cảm xúc"],
        "careers": ["Nghệ thuật, âm nhạc, sáng tác", "Chăm sóc, y tế, tâm lý", "Công tác xã hội, thiện nguyện", "Thiết kế, truyền thông sáng tạo"],
    },
]

# Mốc kết thúc mỗi cung (ngày cuối) — dùng để tra cung theo ngày sinh.
# (month, last_day_of_that_sign) — cung bắt đầu ngày kế tiếp.
_CUSP_END = [
    (1, 19, "CAPRICORN"),   # 1/1–19/1: Ma Kết (vắt từ năm trước)
    (2, 18, "AQUARIUS"),
    (3, 20, "PISCES"),
    (4, 19, "ARIES"),
    (5, 20, "TAURUS"),
    (6, 21, "GEMINI"),
    (7, 22, "CANCER"),
    (8, 22, "LEO"),
    (9, 22, "VIRGO"),
    (10, 23, "LIBRA"),
    (11, 21, "SCORPIO"),
    (12, 21, "SAGITTARIUS"),
    (12, 31, "CAPRICORN"),  # 22/12–31/12: Ma Kết
]

_BY_CODE = {s["code"]: s for s in HOROSCOPE_SIGNS}


def get_sign_by_date(birth: date) -> dict:
    """Trả về dict cung hoàng đạo theo ngày/tháng sinh (dương lịch)."""
    for month, last_day, code in _CUSP_END:
        if birth.month == month and birth.day <= last_day:
            return _BY_CODE[code]
    # Sau mốc cuối của tháng → thuộc cung bắt đầu trong tháng đó
    starts_in_month = {
        1: "AQUARIUS", 2: "PISCES", 3: "ARIES", 4: "TAURUS", 5: "GEMINI",
        6: "CANCER", 7: "LEO", 8: "VIRGO", 9: "LIBRA", 10: "SCORPIO",
        11: "SAGITTARIUS", 12: "CAPRICORN",
    }
    return _BY_CODE[starts_in_month[birth.month]]

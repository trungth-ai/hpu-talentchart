# Dữ liệu tính cách 12 CON GIÁP — chắt lọc từ tài liệu Trung cung cấp
# ("12 con giáp theo lịch vạn niên", phần "Tài năng và tính cách" của mỗi tuổi).
# Key = địa chi (khớp field `dia_chi` do app/services/epa/canchi.py trả về).
#
# LƯU Ý nghiệp vụ: thông tin tham khảo, KHÔNG dùng làm yếu tố quyết định tuyển dụng.

ZODIAC_ANIMALS: dict[str, dict] = {
    "Tý": {
        "dia_chi": "Tý",
        "animal": "Chuột",
        "personality": (
            "Thẳng thắn, thành thực, hòa đồng và có sức hấp dẫn tự nhiên; nỗ lực trong công "
            "việc, tiết kiệm, cảnh giác cao và giỏi tùy cơ ứng biến. Có năng lực lãnh đạo — tổ "
            "chức, trí nhớ tốt và tầm nhìn xa trong kinh doanh."
        ),
        "strengths": ["Thông minh, nhạy bén", "Cần kiệm, chịu khó", "Lãnh đạo & tổ chức tốt", "Tùy cơ ứng biến, cảnh giác", "Trực giác & trí nhớ tốt"],
        "weaknesses": ["Hay do dự trước cơ hội", "Tính toán, so đo việc nhỏ", "Thích phê bình người khác", "Cố chấp, dễ nổi cáu"],
        "careers": ["Kinh doanh, thương mại", "Quản lý, tổ chức", "Tài chính", "Viết lách, sáng tác"],
    },
    "Sửu": {
        "dia_chi": "Sửu",
        "animal": "Trâu",
        "personality": (
            "Kiên định, bền bỉ, cần cù và sống có nguyên tắc, tôn trọng truyền thống. Tư duy "
            "logic, thực tế, trung thành và đáng tin; có tài lãnh đạo bằng kỷ luật, làm việc đến "
            "cùng không bỏ dở."
        ),
        "strengths": ["Chăm chỉ, bền bỉ", "Kiên định, có nguyên tắc", "Trách nhiệm, đáng tin", "Thực tế, kỷ luật", "Lãnh đạo nghiêm túc, nêu gương"],
        "weaknesses": ["Cứng nhắc, cố chấp", "Bảo thủ, thiếu linh hoạt", "Khó gần, ít lãng mạn", "Đôi khi kiêu ngạo, võ đoán"],
        "careers": ["Quản lý, quản trị vận hành", "Công việc cần kỷ luật, bền bỉ", "Kỹ thuật, sản xuất", "Cải cách thể chế, hành chính"],
    },
    "Dần": {
        "dia_chi": "Dần",
        "animal": "Hổ",
        "personality": (
            "Mạnh mẽ, nhiệt tình, bạo dạn và giàu sức thu hút — thường là trung tâm chú ý. Lạc "
            "quan, hành động mau lẹ, thành thật khảng khái và có cá tính hài hước; làm việc dốc "
            "toàn lực."
        ),
        "strengths": ["Lãnh đạo cuốn hút", "Dũng cảm, dám tiên phong", "Nhiệt huyết, lạc quan", "Hành động dứt khoát", "Tận tâm hết mình"],
        "weaknesses": ["Bốc đồng, đôi khi lỗ mãng", "Đa nghi, khó tin người", "Quyết định vội vàng", "Dễ nổi giận, thiếu ổn định"],
        "careers": ["Lãnh đạo, chỉ huy", "Khởi nghiệp, tiên phong", "Công việc cần dũng khí & ảnh hưởng", "Kinh doanh, thể thao"],
    },
    "Mão": {
        "dia_chi": "Mão",
        "animal": "Mèo",
        "personality": (
            "Hiền hòa, nhân từ, nho nhã và yêu hòa bình; hàm súc, yêu nghệ thuật, khả năng phán "
            "đoán tốt. Khéo ngoại giao — đàm phán, thận trọng và giỏi động viên an ủi người khác."
        ),
        "strengths": ["Ngoại giao, đàm phán khéo", "Nho nhã, lịch thiệp", "Thận trọng, phán đoán tốt", "Đồng cảm, biết an ủi", "May mắn trong kinh doanh"],
        "weaknesses": ["Né tránh xung đột & trách nhiệm", "Đôi khi lạnh nhạt, vô tình", "Quá thận trọng, e dè", "Mẫn cảm, dễ u buồn"],
        "careers": ["Ngoại giao, đối ngoại", "Chính trị, hành chính công", "Kinh doanh, đàm phán", "Học giả, nghệ thuật"],
    },
    "Thìn": {
        "dia_chi": "Thìn",
        "animal": "Rồng",
        "personality": (
            "Khoan hồng độ lượng, khí phách mạnh mẽ, nhiệt huyết và tiềm lực lớn. Tự tin, lý "
            "tưởng cao, quyết đoán và dũng cảm đối diện sự thật; hướng ngoại, thích làm việc lớn."
        ),
        "strengths": ["Nhiệt huyết, mạnh mẽ", "Tự tin, khí phách", "Lãnh đạo, quyết đoán", "Rộng lượng, dũng cảm", "Thuyết phục & bán hàng giỏi"],
        "weaknesses": ["Võ đoán, tự cao", "Bốc đồng, dễ cuồng nhiệt", "Kiêu ngạo, ít nghe người khác", "Thiếu kiên nhẫn với tiểu tiết"],
        "careers": ["Lãnh đạo, điều hành", "Khởi xướng dự án lớn", "Kinh doanh, bán hàng", "Công việc đòi hỏi khí phách, tiên phong"],
    },
    "Tỵ": {
        "dia_chi": "Tỵ",
        "animal": "Rắn",
        "personality": (
            "Trí tuệ thiên bẩm, sâu sắc và có phần bí ẩn khó đoán; yêu văn hóa, nghệ thuật, thẩm "
            "mỹ. Quyết đoán theo chính kiến, cơ mưu cẩn thận, kiên cường bền bỉ, trách nhiệm cao "
            "với mục tiêu rõ ràng."
        ),
        "strengths": ["Trí tuệ sâu sắc", "Kiên cường, bền bỉ", "Cơ mưu, thận trọng", "Trực giác, mẫn cảm", "Trách nhiệm, mục tiêu rõ"],
        "weaknesses": ["Khó hòa đồng số đông", "Đa nghi, hay để bụng", "Cố chấp, ít nghe lời khuyên", "Giấu cảm xúc, đôi khi cực đoan"],
        "careers": ["Nghiên cứu, tư tưởng, triết học", "Chính trị", "Kỹ sư, chuyên môn sâu", "Nghệ thuật, sáng tạo"],
    },
    "Ngọ": {
        "dia_chi": "Ngọ",
        "animal": "Ngựa",
        "personality": (
            "Tính tình rộng mở, tư duy mẫn tiệp, khéo giao tiếp và độc lập tự tin. Hoạt bát, linh "
            "hoạt, quyết đoán tại chỗ và nhiệt tình; giỏi tìm giải pháp cho việc khó."
        ),
        "strengths": ["Nhanh nhẹn, linh hoạt", "Giao tiếp giỏi", "Độc lập, tự tin", "Quyết đoán, giải quyết việc khó", "Nhiệt tình, lạc quan"],
        "weaknesses": ["Nóng vội, thiếu nhẫn nại", "Cố chấp, hay thay đổi", "Dễ lạc đề, khó theo quy trình", "Đôi khi lấy mình làm trung tâm"],
        "careers": ["Công việc linh hoạt, nhiều kích thích", "Giao tiếp, đối ngoại", "Quản lý tài chính", "Xử lý tình huống khó, biểu diễn"],
    },
    "Mùi": {
        "dia_chi": "Mùi",
        "animal": "Dê",
        "personality": (
            "Ôn hòa nhất trong 12 con giáp — bác ái, nhân hậu, dễ đồng cảm và tao nhã. Rộng "
            "lượng, khảng khái, trân trọng tình cảm; có khiếu sáng tạo nghệ thuật và giỏi tạo bầu "
            "không khí hài hòa."
        ),
        "strengths": ["Nhân hậu, đồng cảm", "Ôn hòa, tạo hòa khí", "Sáng tạo, nghệ thuật", "Rộng lượng, khảng khái", "Bình tĩnh, dễ mến"],
        "weaknesses": ["Do dự, thiếu quyết đoán", "Dễ ỷ lại, có phần bạc nhược", "Đa sầu đa cảm, ưu uất", "Ngại va chạm"],
        "careers": ["Nghệ thuật, thiết kế, sáng tạo", "Công tác chăm sóc, đồng cảm", "Công việc trong môi trường có dẫn dắt/kỷ luật", "Dịch vụ, cộng đồng"],
    },
    "Thân": {
        "dia_chi": "Thân",
        "animal": "Khỉ",
        "personality": (
            "Thông minh, đa tài đa năng, khéo giao tiếp và tùy cơ ứng biến bậc nhất. Kiên định, "
            "quản lý tài chính tốt, ý thức cạnh tranh mạnh và rất tự tin thể hiện bản thân."
        ),
        "strengths": ["Thông minh, đa tài", "Ứng biến linh hoạt", "Giao tiếp, ngoại giao khéo", "Quản lý tài chính tốt", "Cạnh tranh, kiên định"],
        "weaknesses": ["Tự cao, ít tôn trọng người khác", "Hay tật đố, ganh đua", "Ham hư danh, trục lợi", "Mưu mẹo nên đôi khi khó được tin"],
        "careers": ["Diễn viên, hoạt động xã hội", "Ngoại giao, đối ngoại", "Tài chính, chứng khoán", "Giáo viên, kinh doanh, thể thao"],
    },
    "Dậu": {
        "dia_chi": "Dậu",
        "animal": "Gà",
        "personality": (
            "Thích hành hiệp trượng nghĩa, phong độ và có sức thu hút; tinh nhanh, tổ chức tốt, "
            "nghiêm túc chuyên cần. Thẳng thắn, quyết đoán, quản lý tài chính giỏi và có tài ăn "
            "nói, biểu diễn."
        ),
        "strengths": ["Tổ chức & quản lý tài chính giỏi", "Chuyên cần, nghiêm túc", "Thẳng thắn, quyết đoán", "Tài ăn nói, biểu diễn", "Sẵn lòng giúp người"],
        "weaknesses": ["Thích tranh luận, hay cãi", "Khoa trương, ham hư danh", "Cố chấp khi gặp bất lợi", "Bảo thủ, ít sáng tạo"],
        "careers": ["Biểu diễn, MC, truyền thông", "Kế toán, quản lý tài chính", "Công việc cần tổ chức tỉ mỉ", "Diễn thuyết, viết lách"],
    },
    "Tuất": {
        "dia_chi": "Tuất",
        "animal": "Chó",
        "personality": (
            "Chính trực, thành thực, giàu lòng chính nghĩa và hay bênh vực người yếu thế. Trung "
            "thành, trách nhiệm cao, đáng tin cậy, làm việc tận tâm không bỏ dở; nhìn đời bằng lý trí."
        ),
        "strengths": ["Trung thành, đáng tin", "Trách nhiệm, tận tâm", "Chính trực, công bằng", "Lý trí, thực tế", "Dũng cảm bảo vệ lẽ phải"],
        "weaknesses": ["Cố chấp, bảo thủ ý kiến", "Đa nghi, cảnh giác quá mức", "Thiếu linh hoạt ứng biến", "Kém nhẫn nại"],
        "careers": ["Quân đội, an ninh, pháp lý", "Giáo viên", "Thầy thuốc, chăm sóc", "Kỹ sư, quản lý vận hành"],
    },
    "Hợi": {
        "dia_chi": "Hợi",
        "animal": "Lợn",
        "personality": (
            "Trầm tĩnh, ổn định, cương nghị, lương thiện và thuần phác. Chân thành, tận tâm bền "
            "bỉ, khoan dung độ lượng, ôn hòa hòa thuận và trung thành với bạn bè."
        ),
        "strengths": ["Chân thành, đáng tin", "Tận tâm, bền bỉ", "Khoan dung, độ lượng", "Ôn hòa, giỏi hòa giải", "Nhân nghĩa, sẵn lòng giúp người"],
        "weaknesses": ["Quá cả tin, dễ bị lợi dụng", "Mềm lòng, quản lý tiền kém", "Khó nói lời từ chối", "Đôi khi né tránh, tầm nhìn ngắn"],
        "careers": ["Giáo viên, đào tạo", "Công tác xã hội, thiện nguyện", "Tổ chức sự kiện, cộng đồng", "Công việc cần tận tâm, bền bỉ"],
    },
}


def get_animal_by_dia_chi(dia_chi: str) -> dict | None:
    """Trả về dict tính cách con giáp theo địa chi (Tý, Sửu, ...)."""
    return ZODIAC_ANIMALS.get(dia_chi)

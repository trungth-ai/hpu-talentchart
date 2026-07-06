# ★ 12 Personality Archetype — nội dung biên soạn từ docs/DISC-Tieng-Viet.pdf
# (tài liệu DISCstyles 40 trang do Trung cung cấp 2026-07-05, xem ADR-005)
#
# ⚠️ Core IP của TalentChart — Trung review nội dung trước khi go-live.
# Mapping fusion DISC + Mệnh + Tam hợp: xem ADR-005 và app/services/epa/archetype.py.
# Ngôn ngữ hiển thị: Behavioural Layer (không nhắc mệnh/tử vi trong mô tả).

# Base mapping: DISC profile (primary hoặc primary/secondary) → archetype code
DISC_TO_ARCHETYPE = {
    "D": "CHALLENGER",
    "D/I": "CATALYST",
    "D/S": "EXECUTOR",
    "D/C": "STRATEGIST",
    "I": "CONNECTOR",
    "I/D": "VISIONARY",
    "I/S": "MENTOR",
    "I/C": "VISIONARY",
    "S": "HARMONIZER",
    "S/D": "BUILDER",
    "S/I": "MENTOR",
    "S/C": "GUARDIAN",
    "C": "ANALYST",
    "C/D": "STRATEGIST",
    "C/S": "CRAFTSMAN",
    "C/I": "CRAFTSMAN",
}

# Mệnh (ngũ hành) → archetype có cùng "chất" (ADR-005) — dùng nội bộ cho fusion,
# KHÔNG hiển thị ra Behavioural Layer
MENH_AFFINITY = {
    "Kim": ["STRATEGIST", "CRAFTSMAN"],
    "Mộc": ["BUILDER", "MENTOR"],
    "Thủy": ["CONNECTOR", "ANALYST"],
    "Hỏa": ["CATALYST", "CHALLENGER"],
    "Thổ": ["GUARDIAN", "HARMONIZER"],
}

# Nhóm tam hợp (theo địa chi) → archetype cùng khí chất nhóm
TAMHOP_AFFINITY = {
    # Thân - Tý - Thìn: nhóm trí tuệ, sáng tạo, nhìn xa
    "Thân": ["VISIONARY", "STRATEGIST", "ANALYST"],
    "Tý": ["VISIONARY", "STRATEGIST", "ANALYST"],
    "Thìn": ["VISIONARY", "STRATEGIST", "ANALYST"],
    # Dần - Ngọ - Tuất: nhóm hành động, độc lập, quyết liệt
    "Dần": ["CHALLENGER", "EXECUTOR", "CATALYST"],
    "Ngọ": ["CHALLENGER", "EXECUTOR", "CATALYST"],
    "Tuất": ["CHALLENGER", "EXECUTOR", "CATALYST"],
    # Tỵ - Dậu - Sửu: nhóm kiên định, chỉn chu, bền bỉ
    "Tỵ": ["CRAFTSMAN", "GUARDIAN", "BUILDER"],
    "Dậu": ["CRAFTSMAN", "GUARDIAN", "BUILDER"],
    "Sửu": ["CRAFTSMAN", "GUARDIAN", "BUILDER"],
    # Hợi - Mão - Mùi: nhóm nhân ái, hòa hợp, vun đắp
    "Hợi": ["MENTOR", "HARMONIZER", "CONNECTOR"],
    "Mão": ["MENTOR", "HARMONIZER", "CONNECTOR"],
    "Mùi": ["MENTOR", "HARMONIZER", "CONNECTOR"],
}

ARCHETYPES = {
    "CHALLENGER": {
        "code": "CHALLENGER",
        "name_en": "The Challenger",
        "name_vi": "Người Thách Thức",
        "disc_core": "D",
        "tagline": "Đối mặt thẳng với thách thức và biến áp lực thành kết quả",
        "description": (
            "Người Thách Thức quyết đoán, cạnh tranh và hướng thẳng tới kết quả. "
            "Họ tư duy nhanh, dám nghĩ dám làm, chủ động tạo ra cơ hội thay vì chờ đợi "
            "và sẵn sàng đối mặt trực diện với khó khăn. Động lực chính của họ là sự "
            "độc lập và quyền tự quyết; họ đánh giá bản thân qua tác động và thành tích "
            "đạt được. Trong tập thể, họ là người dấn thân đầu tiên khi có vấn đề gai góc "
            "và không ngại nói thẳng những điều người khác né tránh."
        ),
        "strengths": [
            "Giải quyết vấn đề nhanh, quyết đoán ngay cả khi thiếu thông tin",
            "Chịu áp lực tốt, càng thách thức càng có năng lượng",
            "Dám chịu trách nhiệm và giữ vai trò dẫn dắt khi tình huống hỗn loạn",
            "Đặt tiêu chuẩn cao cho bản thân và thúc đẩy tập thể tiến về phía trước",
        ],
        "watchouts": [
            "Có thể áp đặt, quan tâm mục tiêu hơn cảm xúc con người",
            "Thiếu kiên nhẫn với quy trình và với người làm việc chậm hơn mình",
            "Khi căng thẳng dễ trở nên độc đoán, hay chỉ trích",
            "Nỗi sợ cốt lõi: thất bại và bị mất quyền kiểm soát",
        ],
        "communication_dos": [
            "Đi thẳng vào vấn đề, cung cấp dữ kiện ngắn gọn",
            "Chỉ cho họ thấy cơ hội chiến thắng và kết quả cụ thể",
            "Thỏa thuận rõ mục tiêu và giới hạn, rồi để họ tự chọn cách làm",
        ],
        "communication_donts": [
            "Không vòng vo, không sa đà vào tiểu tiết",
            "Không tranh luận dựa trên cảm tính cá nhân — hãy dùng bằng chứng",
            "Không kiểm soát vi mô cách họ thực hiện công việc",
        ],
        "motivations": [
            "Thách thức cần chinh phục và thẩm quyền để hành động",
            "Sự đa dạng, thay đổi và cơ hội mới",
            "Được công nhận qua thành tích và kết quả đo đếm được",
        ],
        "stress_behavior": [
            "Trở nên thiếu kiên nhẫn, đòi hỏi và chỉ trích thái quá",
            "Ôm quyền quyết định, bỏ qua ý kiến người khác",
        ],
        "improvement_tips": [
            "Rèn sự cảm thông và kiên nhẫn — lắng nghe hết ý trước khi phản hồi",
            "Học cách trao quyền thật sự thay vì chỉ giao việc",
        ],
        "university_fit": (
            "Phù hợp vai trò trưởng đơn vị, quản lý dự án chuyển đổi, khởi xướng "
            "chương trình mới. Cần ghép cùng người chỉn chu về quy trình để cân bằng."
        ),
    },
    "CATALYST": {
        "code": "CATALYST",
        "name_en": "The Catalyst",
        "name_vi": "Người Xúc Tác",
        "disc_core": "D/I",
        "tagline": "Châm ngòi thay đổi và kéo mọi người cùng tăng tốc",
        "description": (
            "Người Xúc Tác kết hợp sự quyết đoán hướng kết quả với năng lượng truyền "
            "cảm hứng. Họ vừa quyết đoán vừa có tài thuyết phục, nắm bắt nhanh khái niệm "
            "mới, năng động và luôn tràn đầy năng lượng. Họ không chỉ muốn thắng — họ "
            "muốn cả đội cùng hào hứng lao về đích. Ở đâu trì trệ, họ xuất hiện để khuấy "
            "động; ý tưởng qua tay họ được đẩy thành hành động với tốc độ đáng nể."
        ),
        "strengths": [
            "Khởi động thay đổi nhanh và lôi kéo được người khác tham gia",
            "Thuyết phục giỏi, biến ý tưởng thành cam kết hành động",
            "Giữ nhịp độ nhanh mà vẫn duy trì không khí tích cực",
            "Xử lý nhiều việc cùng lúc với ý thức cao về thời hạn",
        ],
        "watchouts": [
            "Dễ hứa nhiều hơn khả năng thực hiện, cần người giữ nhịp thực tế",
            "Thiếu kiên nhẫn với giai đoạn triển khai chi tiết, lặp đi lặp lại",
            "Khi áp lực có thể vừa nóng nảy (D) vừa nói mà chưa suy nghĩ kỹ (I)",
            "Nỗi sợ cốt lõi: thất bại và mất hình ảnh trong mắt người khác",
        ],
        "communication_dos": [
            "Giữ nhịp nhanh, tập trung bức tranh tổng thể và cơ hội",
            "Công nhận công khai thành tích và sự tiến bộ của họ",
            "Chốt cuộc trao đổi bằng hành động cụ thể cho bước tiếp theo",
        ],
        "communication_donts": [
            "Không dập tắt ý tưởng ngay khi họ đang hào hứng — hãy hỏi để họ tự lượng hóa",
            "Không giao việc đơn điệu kéo dài mà không có tương tác",
            "Không để quyết định dang dở, thiếu người chịu trách nhiệm",
        ],
        "motivations": [
            "Dự án mới, thử thách mới với quyền chủ động",
            "Môi trường sôi nổi, nhiều tương tác và sự công nhận",
            "Tự do thể hiện ý tưởng và được tin tưởng giao trọng trách",
        ],
        "stress_behavior": [
            "Nôn nóng thúc ép, ra quyết định bốc đồng",
            "Chuyển việc liên tục, bỏ dở phần chi tiết",
        ],
        "improvement_tips": [
            "Cam kết ít hơn, hoàn thành trọn vẹn hơn — chốt tiêu chí xong trước khi nhận việc mới",
            "Kiểm soát cảm xúc khi bị phản biện; xem phản biện là dữ liệu, không phải công kích",
        ],
        "university_fit": (
            "Phù hợp truyền thông - tuyển sinh, phát động phong trào, khởi động đề án "
            "đổi mới. Nên có cộng sự thuộc nhóm chỉn chu để bảo đảm chất lượng triển khai."
        ),
    },
    "EXECUTOR": {
        "code": "EXECUTOR",
        "name_en": "The Executor",
        "name_vi": "Người Thực Thi",
        "disc_core": "D/S",
        "tagline": "Đã nhận việc là về đích — bền bỉ và không ồn ào",
        "description": (
            "Người Thực Thi hướng tới kết quả nhưng tiến về đích bằng sự bền bỉ và "
            "nhất quán thay vì bùng nổ. Họ kết hợp tính quyết đoán với sự kiên nhẫn "
            "đáng tin cậy: đặt mục tiêu rõ, giữ cam kết, và làm việc theo nhịp ổn định "
            "cho tới khi hoàn thành. Họ không cần sân khấu — thành quả cụ thể là tiếng "
            "nói của họ. Với tập thể, họ là người 'nói ít làm nhiều' mà ai cũng muốn có."
        ),
        "strengths": [
            "Hoàn thành cam kết đúng hạn với chất lượng ổn định",
            "Giữ được sự tập trung cao độ vào mục tiêu, không dễ phân tâm",
            "Bình tĩnh tháo gỡ vấn đề thay vì làm to chuyện",
            "Trung thành tuyệt đối với các cam kết đã đặt ra",
        ],
        "watchouts": [
            "Có thể ôm việc, ngại nhờ hỗ trợ cho đến khi quá tải",
            "Ít chia sẻ tiến độ khiến người khác khó phối hợp",
            "Khi căng thẳng trở nên lì lợm, khó lay chuyển",
            "Nỗi sợ cốt lõi: mất ổn định và thất bại trong cam kết",
        ],
        "communication_dos": [
            "Giao mục tiêu rõ ràng kèm quyền chủ động về cách làm",
            "Ghi nhận sự bền bỉ và kết quả thực chất của họ",
            "Báo trước sớm khi có thay đổi để họ kịp điều chỉnh kế hoạch",
        ],
        "communication_donts": [
            "Không thay đổi yêu cầu đột ngột vào phút chót nếu tránh được",
            "Không đánh giá họ qua mức độ 'thể hiện' trong cuộc họp",
            "Không giao việc mơ hồ, thiếu tiêu chí hoàn thành",
        ],
        "motivations": [
            "Mục tiêu cụ thể, đo được và thẩm quyền tương xứng",
            "Môi trường ổn định, ít nhiễu để tập trung làm việc",
            "Sự tin tưởng lâu dài từ lãnh đạo",
        ],
        "stress_behavior": [
            "Thu mình, tự gánh hết việc và im lặng chịu đựng",
            "Trở nên cứng nhắc với thay đổi",
        ],
        "improvement_tips": [
            "Chủ động báo cáo tiến độ và khó khăn sớm — nhờ hỗ trợ không phải là yếu kém",
            "Tập phản hồi thẳng khi bất đồng thay vì lẳng lặng làm theo ý mình",
        ],
        "university_fit": (
            "Phù hợp quản lý đào tạo, triển khai đề án dài hơi, vận hành cơ sở vật chất. "
            "Là 'xương sống' của các dự án cần độ tin cậy cao."
        ),
    },
    "STRATEGIST": {
        "code": "STRATEGIST",
        "name_en": "The Strategist",
        "name_vi": "Nhà Chiến Lược",
        "disc_core": "D/C",
        "tagline": "Nhìn thấu bàn cờ, quyết định bằng dữ liệu và đi trước một bước",
        "description": (
            "Nhà Chiến Lược kết hợp khát vọng kết quả với tư duy phân tích sắc bén. "
            "Họ quyết đoán nhưng chỉ hành động sau khi đã nhìn thấu vấn đề: thu thập "
            "dữ kiện, cân nhắc rủi ro, thiết kế lộ trình rồi mới ra tay — và khi đã ra "
            "tay thì dứt khoát. Họ đặt tiêu chuẩn cao cho cả tốc độ lẫn chất lượng, "
            "giỏi lập kế hoạch hành động từng bước để bảo đảm kết quả tích cực, và "
            "sẵn sàng nói thẳng khi phát hiện điểm không ổn."
        ),
        "strengths": [
            "Tư duy hệ thống: thấy cả bức tranh lớn lẫn điểm gãy chi tiết",
            "Ra quyết định dựa trên bằng chứng, ít bị cảm xúc chi phối",
            "Thiết kế lộ trình khả thi cho các mục tiêu phức tạp",
            "Tư duy phản biện mạnh, phát hiện sớm rủi ro người khác bỏ sót",
        ],
        "watchouts": [
            "Có thể lạnh lùng, thiếu chú tâm đến cảm xúc đội ngũ",
            "Cầu toàn kế hoạch, đôi khi chậm nhịp so với cơ hội",
            "Khi căng thẳng vừa độc đoán vừa chỉ trích gay gắt",
            "Nỗi sợ cốt lõi: sai lầm và bị vượt quyền kiểm soát",
        ],
        "communication_dos": [
            "Trình bày có cấu trúc, kèm dữ liệu và phân tích ưu nhược điểm",
            "Giải thích rõ 'tại sao' đằng sau mỗi yêu cầu",
            "Tôn trọng thời gian suy nghĩ của họ trước khi đòi hỏi cam kết",
        ],
        "communication_donts": [
            "Không thuyết phục bằng ý kiến số đông hay cảm tính",
            "Không đưa dữ liệu thiếu kiểm chứng — họ sẽ mất niềm tin lâu dài",
            "Không ép quyết định lớn khi chưa đủ thông tin",
        ],
        "motivations": [
            "Bài toán chiến lược khó và quyền thiết kế giải pháp",
            "Môi trường tôn trọng logic, dữ liệu và năng lực",
            "Được công nhận qua chất lượng quyết định, không qua hình thức",
        ],
        "stress_behavior": [
            "Phân tích quá mức, trì hoãn quyết định",
            "Chỉ trích sắc bén, thiếu đồng cảm",
        ],
        "improvement_tips": [
            "Chia sẻ lý do đằng sau quyết định để tránh bị xem là độc đoán",
            "Dành thời gian cho 'yếu tố con người' — kế hoạch hay đến đâu cũng cần người thực hiện",
        ],
        "university_fit": (
            "Phù hợp hoạch định chiến lược, đảm bảo chất lượng, thiết kế chương trình "
            "đào tạo, phân tích dữ liệu quản trị đại học."
        ),
    },
    "CONNECTOR": {
        "code": "CONNECTOR",
        "name_en": "The Connector",
        "name_vi": "Người Kết Nối",
        "disc_core": "I",
        "tagline": "Biến đám đông xa lạ thành một cộng đồng có năng lượng",
        "description": (
            "Người Kết Nối nhiệt tình, lạc quan và có sức hút tự nhiên. Họ suy nghĩ "
            "theo cảm xúc, tin vào con người, giỏi tạo không khí tích cực và truyền "
            "cảm hứng khiến người khác muốn tham gia. Mạng lưới quan hệ là tài sản "
            "lớn nhất của họ — họ chủ động kết nối người mới, nhớ tên, nhớ chuyện, "
            "và làm cho mọi cuộc gặp trở nên dễ chịu. Trong tổ chức, họ là chất keo "
            "gắn kết giữa các nhóm vốn ít làm việc với nhau."
        ),
        "strengths": [
            "Giao tiếp xuất sắc, tạo đồng thuận và truyền cảm hứng",
            "Xây dựng mạng lưới quan hệ rộng, mở cửa cho hợp tác mới",
            "Khích lệ người khác phát huy tiềm năng",
            "Lan tỏa sự lạc quan, nâng tinh thần tập thể trong giai đoạn khó",
        ],
        "watchouts": [
            "Dễ thiếu tập trung, nói nhiều hơn làm nếu không có cấu trúc",
            "Né tránh chi tiết và các cuộc trao đổi khó chịu",
            "Khi căng thẳng trở nên hời hợt, thậm chí châm biếm",
            "Nỗi sợ cốt lõi: bị từ chối, bị lạc lõng khỏi tập thể",
        ],
        "communication_dos": [
            "Tương tác trực tiếp, thân thiện, dành thời gian trò chuyện",
            "Khen ngợi chân thành và công khai khi họ làm tốt",
            "Giúp họ cấu trúc công việc: cùng lập checklist, chốt deadline",
        ],
        "communication_donts": [
            "Không giao tiếp lạnh lùng, chỉ email không gặp mặt",
            "Không phủ nhận ý tưởng trước đám đông — góp ý riêng",
            "Không bỏ mặc họ làm việc cô lập trong thời gian dài",
        ],
        "motivations": [
            "Môi trường thân thiện, nhiều hoạt động và sự kiện",
            "Sự tán thành, công nhận cá nhân thường xuyên",
            "Cơ hội làm việc trực tiếp với nhiều người",
        ],
        "stress_behavior": [
            "Nói vòng vo, hứa để làm hài lòng rồi quá tải",
            "Tìm sự chú ý thay vì giải quyết gốc vấn đề",
        ],
        "improvement_tips": [
            "Rèn thói quen ghi chép và theo dõi cam kết đến cùng",
            "Tập nói 'không' — mỗi lời hứa mới là một khoản nợ thời gian",
        ],
        "university_fit": (
            "Phù hợp tuyển sinh, quan hệ doanh nghiệp, công tác sinh viên, sự kiện - "
            "truyền thông. Tỏa sáng ở mọi vị trí cần 'bộ mặt' của nhà trường."
        ),
    },
    "VISIONARY": {
        "code": "VISIONARY",
        "name_en": "The Visionary",
        "name_vi": "Người Kiến Tạo Tầm Nhìn",
        "disc_core": "I/D",
        "tagline": "Vẽ ra bức tranh tương lai khiến người khác muốn đi cùng",
        "description": (
            "Người Kiến Tạo Tầm Nhìn có trí tưởng tượng mạnh và khả năng truyền đạt "
            "tầm nhìn hấp dẫn. Họ giỏi 'gieo hạt giống của một ý tưởng và làm nó phát "
            "triển thành giải pháp thành công', tạo ra hình ảnh trong tâm trí người nghe "
            "để làm sáng tỏ con đường dẫn tới mục tiêu. Họ suy nghĩ vừa nhanh vừa có "
            "chiều sâu về các ý tưởng mới, không ngại thử nghiệm táo bạo, và chính sự "
            "hào hứng của họ trở thành chất xúc tác cho thay đổi tích cực trong tổ chức."
        ),
        "strengths": [
            "Nhìn ra cơ hội và xu hướng trước người khác",
            "Truyền đạt tầm nhìn lôi cuốn, quy tụ người ủng hộ",
            "Tư duy sáng tạo gắn với khái niệm thực tế, khả thi",
            "Giúp người khác 'hình dung được' các bước đi đến thành công",
        ],
        "watchouts": [
            "Dễ đề cao ý tưởng của mình, lạc quan quá mức về tính khả thi",
            "Bỏ ngỏ phần thực thi chi tiết nếu không có cộng sự phù hợp",
            "Khi căng thẳng có thể phóng đại, thiếu thực tế với thời hạn",
            "Nỗi sợ cốt lõi: ý tưởng bị bác bỏ, hình ảnh bản thân xấu đi",
        ],
        "communication_dos": [
            "Lắng nghe trọn vẹn ý tưởng trước khi mổ xẻ tính khả thi",
            "Đặt câu hỏi giúp họ tự cụ thể hóa: nguồn lực, mốc thời gian, rủi ro",
            "Ủng hộ điểm sáng trong ý tưởng ngay cả khi chưa dùng được toàn bộ",
        ],
        "communication_donts": [
            "Không giết ý tưởng bằng 'trước giờ vẫn làm thế' ",
            "Không sa đà bắt bẻ tiểu tiết khi đang ở giai đoạn định hướng",
            "Không dùng ý kiến số đông làm lý do duy nhất để bác bỏ",
        ],
        "motivations": [
            "Không gian tự do sáng tạo và thử nghiệm",
            "Được trình bày trước người có quyền quyết định",
            "Dự án đổi mới có tầm ảnh hưởng rộng",
        ],
        "stress_behavior": [
            "Nhảy từ ý tưởng này sang ý tưởng khác, bỏ dở giữa chừng",
            "Phản ứng cảm xúc khi bị phản biện",
        ],
        "improvement_tips": [
            "Chọn MỘT ý tưởng trọng tâm mỗi quý và đi đến cùng",
            "Ghép đôi với người giỏi thực thi ngay từ khi phác thảo",
        ],
        "university_fit": (
            "Phù hợp phát triển chương trình mới, chuyển đổi số, đổi mới sáng tạo, "
            "xây dựng thương hiệu học thuật của trường."
        ),
    },
    "MENTOR": {
        "code": "MENTOR",
        "name_en": "The Mentor",
        "name_vi": "Người Dẫn Dắt",
        "disc_core": "I/S",
        "tagline": "Thành công của người khác là thước đo của chính mình",
        "description": (
            "Người Dẫn Dắt ấm áp, kiên nhẫn và thực lòng quan tâm đến sự phát triển "
            "của người khác. Họ kết hợp kỹ năng giao tiếp truyền cảm hứng với sự bền "
            "bỉ đáng tin cậy: biết lắng nghe, biết chờ đợi, và biết khích lệ đúng lúc "
            "để mỗi người tiến thêm một bước. Họ xây dựng lòng tin qua sự nhất quán "
            "giữa lời nói và hành động, thường được đồng nghiệp tìm đến để xin lời "
            "khuyên — cả trong công việc lẫn ngoài đời."
        ),
        "strengths": [
            "Phát hiện và nuôi dưỡng tiềm năng của từng người",
            "Kiên nhẫn hỗ trợ từng bước, không bỏ rơi người đang khó khăn",
            "Xây dựng lòng tin sâu và quan hệ lâu dài",
            "Truyền động lực nhẹ nhàng mà bền, không cần khẩu hiệu",
        ],
        "watchouts": [
            "Quá nhường nhịn, ngại va chạm nên khó nói thẳng điều tiêu cực",
            "Dễ ôm việc hộ người khác thay vì để họ tự trưởng thành",
            "Khi căng thẳng trở nên phục tùng, thiếu quyết đoán",
            "Nỗi sợ cốt lõi: xung đột và làm tổn thương người khác",
        ],
        "communication_dos": [
            "Trao đổi chân thành, quan tâm đến con người trước công việc",
            "Ghi nhận những đóng góp thầm lặng của họ",
            "Khuyến khích họ nói thật suy nghĩ, kể cả ý kiến trái chiều",
        ],
        "communication_donts": [
            "Không gây áp lực đối đầu công khai",
            "Không xem sự im lặng của họ là đồng thuận",
            "Không lợi dụng sự tận tình của họ để dồn việc",
        ],
        "motivations": [
            "Thấy người mình hướng dẫn tiến bộ và thành công",
            "Môi trường hợp tác chân thành, ít đấu đá",
            "Vai trò gắn với đào tạo, tư vấn, phát triển con người",
        ],
        "stress_behavior": [
            "Nhận thêm trách nhiệm quá sức để làm hài lòng mọi người",
            "Né tránh xung đột đến mức để vấn đề âm ỉ kéo dài",
        ],
        "improvement_tips": [
            "Học cách phản hồi thẳng thắn với thiện chí — nói thật là món quà",
            "Đặt ranh giới thời gian cho việc hỗ trợ người khác",
        ],
        "university_fit": (
            "Phù hợp cố vấn học tập, giảng viên chủ nhiệm, đào tạo nội bộ, "
            "phát triển đội ngũ kế cận. Là 'người thầy của người thầy'."
        ),
    },
    "HARMONIZER": {
        "code": "HARMONIZER",
        "name_en": "The Harmonizer",
        "name_vi": "Người Hòa Hợp",
        "disc_core": "S",
        "tagline": "Giữ cho tập thể êm nhịp ngay cả giữa sóng gió",
        "description": (
            "Người Hòa Hợp kiên nhẫn, chân thành và nhất quán. Họ lắng nghe thấu đáo, "
            "quan tâm để mọi người cảm thấy được hỗ trợ, an toàn và có giá trị; ưu "
            "tiên sự ổn định và hòa khí của tập thể. Họ làm việc theo nhịp độ từ tốn "
            "nhưng cực kỳ đáng tin cậy — đã hứa là làm. Khi nhóm có mâu thuẫn, họ là "
            "người tìm điểm chung và giải pháp dung hòa, giữ cho cỗ máy chung chạy "
            "trơn tru mà không cần ai để ý đến công sức của mình."
        ),
        "strengths": [
            "Lắng nghe kiên nhẫn và hòa giải mâu thuẫn khéo léo",
            "Ổn định tâm lý, là điểm tựa của nhóm trong giai đoạn xáo trộn",
            "Hỗ trợ đồng đội tận tình, đặt lợi ích nhóm lên trước",
            "Bền bỉ và nhất quán — chất lượng công việc ít dao động",
        ],
        "watchouts": [
            "Ngại thay đổi đột ngột, cần thời gian thích nghi",
            "Chậm ra quyết định, quá nhường nhịn trong tranh luận",
            "Khi căng thẳng trở nên thụ động, im lặng chấp nhận",
            "Nỗi sợ cốt lõi: thay đổi đột ngột, mất an toàn và ổn định",
        ],
        "communication_dos": [
            "Cư xử từ tốn, tạo không khí thoải mái trước khi bàn việc",
            "Cung cấp trình tự từng bước và hướng dẫn rõ ràng",
            "Cho họ sự đảm bảo cá nhân khi có thay đổi: lộ trình, lý do, hỗ trợ",
        ],
        "communication_donts": [
            "Không ép quyết định ngay trong cuộc họp căng thẳng",
            "Không thay đổi kế hoạch liên tục thiếu giải thích",
            "Không lớn tiếng — họ sẽ đóng cửa giao tiếp",
        ],
        "motivations": [
            "Môi trường ổn định, quan hệ chân thành và tin cậy lẫn nhau",
            "Được ghi nhận sự kiên trì và đóng góp thầm lặng",
            "Làm việc nhóm có tinh thần hợp tác thật sự",
        ],
        "stress_behavior": [
            "Phục tùng bên ngoài nhưng ấm ức bên trong",
            "Trì hoãn thay đổi bằng sự im lặng",
        ],
        "improvement_tips": [
            "Rèn sự quyết đoán khi bị áp lực — ý kiến của bạn có giá trị",
            "Chủ động nêu nhu cầu thay vì chờ người khác nhận ra",
        ],
        "university_fit": (
            "Rất phù hợp môi trường đại học: hành chính - tổng hợp, tư vấn sinh viên, "
            "thư viện, các vị trí cần sự tin cậy lâu dài. Trụ cột ổn định của đơn vị."
        ),
    },
    "BUILDER": {
        "code": "BUILDER",
        "name_en": "The Builder",
        "name_vi": "Người Xây Dựng",
        "disc_core": "S/D",
        "tagline": "Xây từng viên gạch chắc chắn cho công trình dài hạn",
        "description": (
            "Người Xây Dựng kết hợp sự bền bỉ ổn định với ý chí hướng đến kết quả. "
            "Họ thích áp dụng thay đổi từng bước chắc chắn, không vội vàng nhưng "
            "không bao giờ dừng lại. Khác với người chỉ giữ ổn định, họ chủ động "
            "kiến thiết: cải tiến quy trình, bồi đắp nền tảng, đưa tập thể đi lên "
            "bằng những bước tiến nhỏ mà tích lũy. Giá trị của họ thường chỉ lộ rõ "
            "sau một chặng đường — khi nhìn lại mới thấy mọi thứ đã vững hơn rất nhiều."
        ),
        "strengths": [
            "Kiên trì cải tiến liên tục, biến nhỏ thành lớn",
            "Cân bằng tốt giữa ổn định và tiến bộ",
            "Đáng tin cậy trong các dự án dài hơi nhiều giai đoạn",
            "Giữ cho nhóm gắn kết trong khi vẫn đi đúng tiến độ",
        ],
        "watchouts": [
            "Thận trọng quá mức trước cơ hội cần quyết định nhanh",
            "Khó buông những gì đã dày công xây khi cần đổi hướng",
            "Khi căng thẳng trở nên bảo thủ, bám chặt cách cũ",
            "Nỗi sợ cốt lõi: công sức tích lũy bị phá bỏ đột ngột",
        ],
        "communication_dos": [
            "Trình bày thay đổi như lộ trình từng bước có kiểm soát",
            "Ghi nhận nền tảng họ đã xây trước khi đề xuất cải tiến",
            "Cho họ vai trò rõ ràng trong kế hoạch dài hạn",
        ],
        "communication_donts": [
            "Không phủ nhận sạch trơn hệ thống hiện có",
            "Không đòi kết quả lớn tức thì",
            "Không thay đổi mục tiêu giữa chừng thiếu bàn bạc",
        ],
        "motivations": [
            "Dự án dài hạn có ý nghĩa tích lũy",
            "Quyền chủ động cải tiến trong phạm vi của mình",
            "Sự ổn định về định hướng từ lãnh đạo",
        ],
        "stress_behavior": [
            "Cố thủ với quy trình cũ dù bối cảnh đã đổi",
            "Làm chậm nhịp cả nhóm để giữ sự chắc chắn",
        ],
        "improvement_tips": [
            "Định kỳ tự hỏi: nếu xây lại từ đầu hôm nay, mình có làm giống hệt không?",
            "Tập chấp nhận phiên bản 'đủ tốt' để kịp nhịp cơ hội",
        ],
        "university_fit": (
            "Phù hợp xây dựng đơn vị mới, phát triển cơ sở dữ liệu - quy trình nội bộ, "
            "quản lý các đề án hạ tầng và văn hóa tổ chức."
        ),
    },
    "GUARDIAN": {
        "code": "GUARDIAN",
        "name_en": "The Guardian",
        "name_vi": "Người Gìn Giữ",
        "disc_core": "S/C",
        "tagline": "Chốt chặn tin cậy của chất lượng và chuẩn mực",
        "description": (
            "Người Gìn Giữ kết hợp sự kiên nhẫn ổn định với tính chuẩn mực cao. Họ "
            "cân bằng, đánh giá cao dữ liệu, khéo léo trong giao thiệp và luôn chú ý "
            "đến 'nguyên tắc'; không thích xáo trộn và nhập nhằng. Họ là người bảo vệ "
            "các giá trị, quy trình và tiêu chuẩn đã được kiểm chứng — không phải vì "
            "bảo thủ, mà vì hiểu cái giá của sự tùy tiện. Tổ chức nào cũng cần họ để "
            "những gì tốt đẹp không bị xói mòn theo thời gian."
        ),
        "strengths": [
            "Tuân thủ và duy trì tiêu chuẩn một cách tự nguyện, bền bỉ",
            "Phát hiện sai lệch quy trình từ sớm",
            "Đáng tin trong công việc đòi hỏi bảo mật và cẩn trọng",
            "Khéo léo giữ nguyên tắc mà không gây căng thẳng",
        ],
        "watchouts": [
            "Có thể cứng nhắc khi quy định không còn phù hợp thực tế",
            "Do dự trước cái mới cho đến khi có đủ bằng chứng",
            "Khi căng thẳng trở nên thu mình, ương ngạnh",
            "Nỗi sợ cốt lõi: sai sót, bị chỉ trích và mất chuẩn mực",
        ],
        "communication_dos": [
            "Giải thích thay đổi kèm cơ sở pháp lý/quy định rõ ràng",
            "Cho họ thời gian kiểm tra và xác nhận trước khi triển khai",
            "Ghi nhận vai trò 'người gác cổng' của họ một cách trân trọng",
        ],
        "communication_donts": [
            "Không yêu cầu 'linh hoạt' vượt quy định mà không có văn bản",
            "Không chê họ chậm khi họ đang làm đúng quy trình",
            "Không thay đổi tiêu chuẩn tùy tiện theo tình huống",
        ],
        "motivations": [
            "Hệ thống quy định rõ ràng, nhất quán",
            "Môi trường tôn trọng chất lượng hơn tốc độ",
            "Sự an toàn và ổn định lâu dài của tổ chức",
        ],
        "stress_behavior": [
            "Bám chặt câu chữ quy định, giảm linh hoạt",
            "Âm thầm bất mãn khi chuẩn mực bị bỏ qua",
        ],
        "improvement_tips": [
            "Phân biệt 'nguyên tắc cốt lõi' với 'thói quen cũ' — chỉ giữ cái đầu",
            "Chủ động đề xuất cập nhật quy định thay vì chỉ thực thi",
        ],
        "university_fit": (
            "Phù hợp thanh tra - pháp chế, khảo thí, đảm bảo chất lượng, "
            "quản lý hồ sơ văn bằng. Chốt chặn tin cậy của nhà trường."
        ),
    },
    "ANALYST": {
        "code": "ANALYST",
        "name_en": "The Analyst",
        "name_vi": "Nhà Phân Tích",
        "disc_core": "C",
        "tagline": "Để dữ liệu lên tiếng trước, kết luận đến sau",
        "description": (
            "Nhà Phân Tích chính xác, tỉ mỉ và có óc phân tích sâu. Họ dựa trên dữ "
            "liệu, dữ kiện và bằng chứng; tin tưởng vào giá trị của cấu trúc, tiêu "
            "chuẩn và trình tự. Họ hành động thận trọng — suy nghĩ, đặt câu hỏi và "
            "kiểm chứng trước khi quyết định — và chỉ hài lòng khi tìm ra câu trả lời "
            "'đúng' thay vì câu trả lời 'nhanh'. Trong thế giới nhiều ý kiến, họ là "
            "người kiên định hỏi: bằng chứng đâu?"
        ),
        "strengths": [
            "Phân tích logic chặt chẽ, kết luận có căn cứ",
            "Chất lượng công việc cao, ít sai sót",
            "Suy nghĩ độc lập, không bị cuốn theo đám đông",
            "Tìm ra nguyên nhân gốc rễ thay vì xử lý bề mặt",
        ],
        "watchouts": [
            "Phân tích quá nhiều dẫn đến chậm quyết định",
            "Quá cầu toàn, khó chấp nhận phương án 80%",
            "Khi căng thẳng trở nên thu mình, phòng thủ trước chỉ trích",
            "Nỗi sợ cốt lõi: mắc sai lầm và bị đánh giá thiếu chính xác",
        ],
        "communication_dos": [
            "Cung cấp dữ liệu dạng văn bản, có nguồn rõ ràng",
            "Giải thích 'tại sao' và 'như thế nào' một cách hợp lý",
            "Cho họ thời gian suy nghĩ và kiểm chứng trước khi chốt",
        ],
        "communication_donts": [
            "Không thúc ép quyết định khi dữ liệu chưa đủ",
            "Không phê bình công khai — góp ý riêng, có dẫn chứng",
            "Không dùng cảm xúc thay cho lập luận",
        ],
        "motivations": [
            "Bài toán chuyên môn sâu thỏa trí tò mò",
            "Tiêu chuẩn rõ ràng và môi trường tôn trọng logic",
            "Được công nhận về độ chính xác và chất lượng",
        ],
        "stress_behavior": [
            "Sa đà vào chi tiết, trì hoãn kết luận",
            "Phòng thủ, tìm bằng chứng để chứng minh mình đúng",
        ],
        "improvement_tips": [
            "Đặt hạn chót cho việc phân tích — quyết định đúng lúc cũng là chất lượng",
            "Bớt lo lắng về sai sót nhỏ; chia sẻ bản nháp sớm để nhận phản hồi",
        ],
        "university_fit": (
            "Lý tưởng cho nghiên cứu khoa học, phân tích dữ liệu, tài chính - kế toán, "
            "kiểm định chất lượng chương trình."
        ),
    },
    "CRAFTSMAN": {
        "code": "CRAFTSMAN",
        "name_en": "The Craftsman",
        "name_vi": "Người Tinh Xảo",
        "disc_core": "C/S",
        "tagline": "Hoàn hảo trong từng chi tiết, khiêm nhường trong cách thể hiện",
        "description": (
            "Người Tinh Xảo theo đuổi chất lượng bằng cả sự chính xác lẫn sự kiên "
            "nhẫn. Họ lập kế hoạch kỹ lưỡng và thận trọng để bảo đảm kết quả chất "
            "lượng, tập trung vào sự chính xác, cơ cấu, trình tự và sự tỉ mỉ — làm "
            "đúng việc và làm việc đúng cách. Khác với sự cầu toàn ồn ào, họ trau "
            "chuốt sản phẩm trong thầm lặng, cải tiến qua từng phiên bản, và tự hào "
            "về những chi tiết mà người thường không nhìn thấy."
        ),
        "strengths": [
            "Tay nghề chuyên môn sâu, sản phẩm đầu ra chỉn chu",
            "Nhất quán về chất lượng qua thời gian dài",
            "Kiên nhẫn hoàn thiện những việc người khác bỏ dở",
            "Kết hợp tiêu chuẩn cao với thái độ hợp tác ôn hòa",
        ],
        "watchouts": [
            "Khó ủy thác vì 'không ai làm kỹ bằng mình'",
            "Trau chuốt quá mức làm chậm tiến độ chung",
            "Khi căng thẳng cần nhịp chậm để xử lý, dễ bị dồn ép",
            "Nỗi sợ cốt lõi: sản phẩm kém chất lượng gắn với tên mình",
        ],
        "communication_dos": [
            "Tôn trọng quy trình làm việc và nhịp độ của họ",
            "Khen ngợi cụ thể vào chi tiết chất lượng họ đã làm",
            "Thống nhất tiêu chí 'hoàn thành' ngay từ đầu",
        ],
        "communication_donts": [
            "Không ép rút ngắn giai đoạn kiểm tra chất lượng",
            "Không so sánh họ với người làm nhanh nhưng ẩu",
            "Không thay đổi tiêu chí chất lượng giữa chừng",
        ],
        "motivations": [
            "Công việc chuyên môn sâu được đầu tư đúng mức",
            "Môi trường trân trọng chất lượng và tay nghề",
            "Thời gian đủ để làm ra sản phẩm đáng tự hào",
        ],
        "stress_behavior": [
            "Ôm việc tự làm hết để bảo đảm chất lượng",
            "Im lặng rút lui khi tiêu chuẩn bị hạ thấp",
        ],
        "improvement_tips": [
            "Dạy lại chuẩn của mình cho người khác — nhân bản chất lượng thay vì độc quyền",
            "Phân biệt việc cần 100% với việc chỉ cần 80% là đủ",
        ],
        "university_fit": (
            "Phù hợp biên soạn học liệu, phát triển phần mềm - hệ thống, "
            "thí nghiệm - thực hành, xuất bản học thuật."
        ),
    },
}

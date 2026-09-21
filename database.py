import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'school.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table (Admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')

    # Posts / Articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category_slug TEXT NOT NULL,
            thumbnail TEXT,
            summary TEXT,
            content TEXT NOT NULL,
            author TEXT DEFAULT 'Ban Biên Tập',
            is_featured INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_slug) REFERENCES categories (slug)
        )
    ''')

    # Documents (Văn bản chỉ đạo / Quyết định)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_code TEXT NOT NULL,
            title TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            signer TEXT DEFAULT 'UBND / Sở GD&ĐT Lào Cai',
            category TEXT DEFAULT 'Chỉ đạo điều hành',
            file_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Timetables (Thời khóa biểu)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            week_number INTEGER NOT NULL,
            apply_from TEXT NOT NULL,
            branch TEXT NOT NULL, -- 'Trường chính' hoặc 'Phân hiệu 2'
            content_html TEXT,
            file_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Student Grades / Results for Lookup (Tra cứu kết quả học tập & điểm thi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            birth_date TEXT,
            semester TEXT DEFAULT 'Học kỳ I - 2026-2027',
            math REAL,
            literature REAL,
            english REAL,
            physics REAL,
            chemistry REAL,
            history REAL,
            gpa REAL,
            rank TEXT,
            conduct TEXT DEFAULT 'Tốt'
        )
    ''')

    # Feedbacks / Góp ý
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'Chưa đọc',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Visitor Counter
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            val INTEGER NOT NULL
        )
    ''')

    # Site Settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            val TEXT NOT NULL
        )
    ''')

    conn.commit()

    # Seed Admin User with password Phuc2012@
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password_hash, display_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hash_password('Phuc2012@'), 'Quản trị viên (Phúc)', 'admin'))

    # Seed Categories
    categories_data = [
        ('tin-tuc', 'Tin tức', 'Tin tức hoạt động chung của trường THCS Ngô Văn Sở'),
        ('su-kien', 'Sự kiện', 'Các sự kiện, thông báo quan trọng của trường'),
        ('thoi-khoa-bieu', 'Thời khóa biểu', 'Lịch học chính khóa và bổ trợ theo từng tuần'),
        ('noi-dung-cong-khai', 'Nội dung công khai', 'Các văn bản, cam kết và điều kiện đảm bảo chất lượng giáo dục'),
        ('tu-van-hoc-duong', 'Tư vấn học đường', 'Các bài viết định hướng, tư vấn tâm lý và kỹ năng sống cho học sinh'),
        ('van-ban-truong', 'Văn bản trường', 'Quy định, cam kết và văn bản nội bộ trường THCS Ngô Văn Sở'),
        ('ke-hoach', 'Kế hoạch', 'Kế hoạch tuần, kế hoạch tháng năm học 2026-2027'),
        ('phong-truyen-thong', 'Phòng truyền thống', 'Lịch sử thành lập và thành tích xuất sắc của nhà trường')
    ]
    for slug, name, desc in categories_data:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (slug, name, description)
            VALUES (?, ?, ?)
        ''', (slug, name, desc))

    # Seed Stats
    initial_stats = [
        ('total_visits', 45892),
        ('visits_today', 342),
        ('visits_week', 2180),
        ('online_count', 14)
    ]
    for k, v in initial_stats:
        cursor.execute('INSERT OR IGNORE INTO stats (key, val) VALUES (?, ?)', (k, v))

    # Seed Settings
    settings_data = [
        ('school_name', 'TRƯỜNG THCS NGÔ VĂN SỞ'),
        ('school_short_name', 'THCSCHAODAU'),
        ('school_slogan', 'Trường học hạnh phúc - Học sinh tài năng'),
        ('location', 'Phường Lào Cai, thành phố Lào Cai, tỉnh Lào Cai'),
        ('address', '428 Nguyễn Huệ, phường Lào Cai, tỉnh Lào Cai'),
        ('phone', '0919803266'),
        ('email', 'thcsngovanso@elc.vn'),
        ('principal', 'Bà Phùng Thị Dung - Hiệu trưởng'),
        ('founded_year', '1990'),
        ('youtube_video', 'https://www.youtube.com/embed/5QeuPIu3y3Q'),
        ('announcement_marquee', 'Chào mừng bạn đến với cổng thông tin điện tử Trường THCS Ngô Văn Sở - Thành phố Lào Cai!'),
        ('banner_url', 'https://storage-edu.vnpt.vn/edu-lci/8428/DUY/banner moi.gif'),
        ('banner_link', '/'),
        ('promo_banner_url', 'https://storage-vnportal.vnpt.vn/bcn-khdn/3405/banner/hcm_khoangtrang.png'),
        ('promo_banner_link', '/post/ra-mat-khong-gian-van-hoa-ho-chi-minh'),
        ('promo_banner_title', 'Không gian văn hóa Hồ Chí Minh - THCS Ngô Văn Sở'),
        ('promo_banner_active', '1'),
        ('sidebar_banner_1_url', 'https://storage-vnportal.vnpt.vn/bcn-khdn/3405/banner/cds.png'),
        ('sidebar_banner_1_link', 'https://laocai.gov.vn/'),
        ('sidebar_banner_1_title', 'Chương trình Chuyển đổi số Giáo dục'),
        ('sidebar_banner_1_active', '1'),
        ('sidebar_banner_2_url', 'https://storage-vnportal.vnpt.vn/bcn-khdn/3405/banner/khaosat.png'),
        ('sidebar_banner_2_link', '/search-student'),
        ('sidebar_banner_2_title', 'Tra cứu Kết quả học tập & Đánh giá rèn luyện'),
        ('sidebar_banner_2_active', '1'),
        ('sidebar_banner_3_url', ''),
        ('sidebar_banner_3_link', ''),
        ('sidebar_banner_3_title', 'Liên kết Hoạt động Giáo dục'),
        ('sidebar_banner_3_active', '0'),
        ('logo_url', 'https://storage-vnportal.vnpt.vn/edu-lci/8428/DUY/logo-2024.png'),
        ('facebook_url', ''),
        ('zalo_url', ''),
        ('footer_note', '')
    ]
    for k, v in settings_data:
        cursor.execute('INSERT OR IGNORE INTO settings (key, val) VALUES (?, ?)', (k, v))

    # Seed Real Articles from thcsngovanso.phuonglaocai.edu.vn
    cursor.execute('SELECT COUNT(*) FROM posts')
    if cursor.fetchone()[0] == 0:
        real_posts = [
            (
                "Ra mắt không gian văn hoá Hồ Chí Minh",
                "ra-mat-khong-gian-van-hoa-ho-chi-minh",
                "tin-tuc",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/Picture1-205853.jpg",
                "Trường THCS Ngô Văn Sở long trọng tổ chức lễ ra mắt Không gian văn hóa Hồ Chí Minh nhằm lan tỏa giá trị tư tưởng, đạo đức, phong cách của Bác đến toàn thể cán bộ, giáo viên và học sinh.",
                """<p>Nhằm thiết thực học tập và làm theo tư tưởng, đạo đức, phong cách Hồ Chí Minh, sáng nay Trường THCS Ngô Văn Sở đã tổ chức lễ ra mắt Không gian văn hoá Hồ Chí Minh tại khuôn viên nhà trường.</p>
                <p>Không gian văn hóa Hồ Chí Minh được trang bị phong phú các tư liệu quý, sách báo, tranh ảnh ghi lại cuộc đời và sự nghiệp vẻ vang của Chủ tịch Hồ Chí Minh, đặc biệt là những kỷ niệm và lời dặn dò của Bác khi về thăm Lào Cai.</p>
                <p>Phát biểu tại buổi lễ, Hiệu trưởng nhà trường - cô Phùng Thị Dung khẳng định: Không gian văn hóa Hồ Chí Minh sẽ là nơi sinh hoạt truyền thống, bồi dưỡng lý tưởng cách mạng, lòng tự hào dân tộc cho các thế hệ học sinh nhà trường, đồng thời khích lệ các em không ngừng nỗ lực rèn đức luyện tài.</p>""",
                "Ban Biên Tập", 1, 1420
            ),
            (
                "Học và làm theo Bác từ những việc làm cụ thể",
                "hoc-va-lam-theo-bac-tu-nhung-viec-lam-cu-the",
                "tin-tuc",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/Picture1-205853.jpg",
                "Hướng tới kỷ niệm 68 năm ngày Bác Hồ lên thăm Lào Cai (23/9/1958 – 23/9/2026), sáng ngày 14/9/2026 Trường THCS Ngô Văn Sở đã phát động đợt thi đua đặc biệt.",
                """<p>Hướng tới kỷ niệm 68 năm ngày Bác Hồ lên thăm Lào Cai (23/9/1958 – 23/9/2026), sáng ngày 14/9/2026, toàn thể thầy cô giáo và học sinh trường THCS Ngô Văn Sở đã tham gia buổi sinh hoạt chuyên đề 'Học và làm theo Bác từ những việc làm cụ thể'.</p>
                <p>Các phong trào thi đua dạy tốt - học tốt, xây dựng trường lớp sáng - xanh - sạch - đẹp, nuôi heo đất giúp bạn vượt khó, và phong trào đọc sách 15 phút mỗi ngày đã nhận được sự hưởng ứng nhiệt liệt từ 100% các chi đội.</p>""",
                "Phùng Thị Dung", 1, 985
            ),
            (
                "Thời khoá biểu chính khoá tuần 4 thực hiện từ 21 tháng 9 năm 2026 (Trường chính)",
                "thoi-khoa-bieu-chinh-khoa-tuan-4-thuc-hien-tu-21-thang-9-nam-2026-truong-chinh",
                "thoi-khoa-bieu",
                "https://storage-edu.vnpt.vn/edu-lci/8428/DUY/images.jpg",
                "Nhà trường thông báo thời khóa biểu chính khóa tuần 4 năm học 2026-2027 áp dụng cho các khối 6, 7, 8, 9 tại cơ sở Trường chính bắt đầu từ ngày 21/09/2026.",
                """<p>Ban Giám hiệu Trường THCS Ngô Văn Sở thông báo Thời khoá biểu chính khoá tuần 4, thực hiện từ ngày 21/09/2026 cho học sinh các lớp khối 6, khối 7, khối 8 và khối 9 tại Trường chính.</p>
                <p>Yêu cầu các tổ chuyên môn, giáo viên bộ môn và giáo viên chủ nhiệm nghiêm túc thực hiện đúng phân phối chương trình và nề nếp dạy học.</p>
                <div class="table-responsive">
                <table class="table table-bordered text-center">
                    <thead class="table-primary">
                        <tr><th>Thứ / Buổi</th><th>Khối 6</th><th>Khối 7</th><th>Khối 8</th><th>Khối 9</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Thứ 2 (Sáng)</td><td>Chào cờ / Toán / Văn / Anh</td><td>Chào cờ / Văn / Toán / KHTN</td><td>Chào cờ / Anh / Lịch sử / Toán</td><td>Chào cờ / KHTN / Văn / Toán</td></tr>
                        <tr><td>Thứ 3 (Sáng)</td><td>KHTN / KHTN / GDCD / Tin</td><td>Toán / Toán / Mỹ thuật / Anh</td><td>Văn / Văn / KHTN / KHTN</td><td>Toán / KHTN / Anh / Sử-Địa</td></tr>
                        <tr><td>Thứ 4 (Sáng)</td><td>Văn / Toán / Thể dục / Sử</td><td>KHTN / Văn / Tin / Thể dục</td><td>Toán / Anh / Công nghệ / GDCD</td><td>Văn / Văn / Toán / Tin</td></tr>
                        <tr><td>Thứ 5 (Sáng)</td><td>Anh / Anh / Công nghệ / Nhạc</td><td>GDCD / Thể dục / Toán / Văn</td><td>KHTN / KHTN / Thể dục / Văn</td><td>Lịch sử / Toán / KHTN / KHTN</td></tr>
                        <tr><td>Thứ 6 (Sáng)</td><td>Toán / Văn / KHTN / HĐTN</td><td>Văn / Toán / KHTN / HĐTN</td><td>Toán / Văn / Anh / HĐTN</td><td>Anh / Toán / Văn / HĐTN</td></tr>
                        <tr><td>Thứ 7 (Sáng)</td><td>Sinh hoạt lớp / Ôn tập</td><td>Sinh hoạt lớp / Ôn tập</td><td>Sinh hoạt lớp / Ôn tập</td><td>Sinh hoạt lớp / Ôn tập</td></tr>
                    </tbody>
                </table>
                </div>""",
                "Chuyên Môn", 1, 2340
            ),
            (
                "Thời khoá biểu chính khoá tuần 3 thực hiện từ 14 tháng 9 năm 2026 (Phân hiệu 2)",
                "thoi-khoa-bieu-chinh-khoa-tuan-3-phan-hieu-2",
                "thoi-khoa-bieu",
                "https://storage-edu.vnpt.vn/edu-lci/8428/DUY/images.jpg",
                "Thông báo thời khóa biểu chính khóa áp dụng tại Phân hiệu 2 từ ngày 14/09/2026.",
                """<p>Thời khóa biểu chính khóa tuần 3 dành cho các lớp học tại Phân hiệu 2, áp dụng từ thứ Hai ngày 14/09/2026. Đề nghị các thầy cô giáo và học sinh theo dõi và thực hiện nghiêm túc.</p>""",
                "Chuyên Môn", 0, 712
            ),
            (
                "Bản cam kết của giáo viên với nhà trường về thực hiện các quy định về dạy thêm, học thêm",
                "ban-cam-ket-day-them-hoc-them",
                "noi-dung-cong-khai",
                "https://storage-edu.vnpt.vn/edu-lci/8428/DUY/qlvb-online.png",
                "Thực hiện theo Thông tư và chỉ đạo của Sở GD&ĐT Lào Cai, 100% giáo viên trường THCS Ngô Văn Sở ký cam kết chấp hành nghiêm túc quy định dạy thêm, học thêm.",
                """<p>Nhằm nâng cao chất lượng giáo dục toàn diện và thực hiện nghiêm các quy định của Bộ GD&ĐT, Sở GD&ĐT tỉnh Lào Cai, Trường THCS Ngô Văn Sở đã tổ chức cho 100% cán bộ, giáo viên ký bản cam kết về việc thực hiện đúng các quy định về dạy thêm, học thêm trong và ngoài nhà trường.</p>
                <p>Nội dung bản cam kết nhấn mạnh: Không dạy thêm có thu tiền đối với học sinh chính khóa khi chưa được cấp phép; không ép buộc học sinh học thêm dưới bất kỳ hình thức nào; tập trung dạy tốt trong giờ học chính khóa.</p>""",
                "Thanh tra nhà trường", 1, 1680
            ),
            (
                "Tổ chức thành công Chuyên đề “giáo dục hòa nhập trong dạy học môn Tiếng Anh lớp 6”",
                "to-chuc-thanh-cong-chuyen-de-giao-duc-hoa-nhap-mon-tieng-anh-6",
                "tin-tuc",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/Picture1-378053.png",
                "Tổ Ngoại ngữ - Nghệ thuật trường THCS Ngô Văn Sở tổ chức thành công chuyên đề cấp cụm trường với nhiều phương pháp đổi mới sáng tạo và hiệu quả cao.",
                """<p>Vừa qua, Tổ Ngoại ngữ - Nghệ thuật trường THCS Ngô Văn Sở đã tổ chức thành công buổi sinh hoạt chuyên đề cấp cụm với chủ đề “Giáo dục hòa nhập trong dạy học môn Tiếng Anh lớp 6 theo Chương trình GDPT 2018”.</p>
                <p>Tiết dạy thể nghiệm do cô giáo Đỗ Thị Mai Lan thực hiện với sự tham gia hào hứng của các em học sinh lớp 6A1. Tiết học kết hợp hài hòa giữa công nghệ thông tin, trò chơi tương tác và các phương pháp phát triển kỹ năng nghe - nói tự nhiên cho học sinh.</p>""",
                "Tổ Ngoại ngữ", 0, 830
            ),
            (
                "Sinh hoạt dưới cờ – khí thế mới, quyết tâm mới",
                "sinh-hoat-duoi-co-khi-the-moi-quyet-tam-moi",
                "su-kien",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/PA1211.png",
                "Buổi chào cờ đầu tuần của trường THCS Ngô Văn Sở diễn ra trang nghiêm, tạo động lực phấn đấu thi đua học tập rèn luyện tốt trong toàn thể học sinh.",
                """<p>Sáng thứ Hai, toàn thể thầy cô giáo và hơn 800 học sinh trường THCS Ngô Văn Sở đã tề tựu đông đủ dự Lễ Chào cờ đầu tuần. Tại buổi lễ, Liên đội đã đánh giá nề nếp thi đua tuần qua và triển khai kế hoạch hoạt động tuần mới với khí thế quyết tâm đạt nhiều hoa điểm 10 dâng tặng thầy cô.</p>""",
                "Tổng phụ trách Đội", 0, 654
            ),
            (
                "Trường THCS Ngô Văn Sở tổ chức lễ Khai giảng năm học 2026 – 2027",
                "truong-thcs-ngo-van-so-to-chuc-le-khai-giang-nam-hoc-2026-2027",
                "su-kien",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/Picture1-205853.jpg",
                "Hòa chung không khí tưng bừng của ngày hội 'Toàn dân đưa trẻ đến trường', thầy và trò trường THCS Ngô Văn Sở long trọng tổ chức Lễ Khai giảng năm học mới.",
                """<p>Sáng ngày 5/9/2026, trong không khí hân hoan rực rỡ cờ hoa, Trường THCS Ngô Văn Sở đã long trọng tổ chức Lễ Khai giảng năm học 2026 - 2027. Đến dự buổi lễ có các đồng chí lãnh đạo UBND phường Lào Cai, đại diện Hội Cha mẹ học sinh cùng toàn thể cán bộ, giáo viên và học sinh nhà trường.</p>
                <p>Hồi trống khai trường vang lên rộn rã báo hiệu một năm học mới với nhiều thành công mới, thắng lợi mới của ngôi trường mang tên người anh hùng Ngô Văn Sở.</p>""",
                "Ban Biên Tập", 1, 3120
            ),
            (
                "Các giải pháp và kinh nghiệm trong hoạt động tư vấn và khai thác hiệu quả công tác tư vấn học đường",
                "cac-giai-phap-va-kinh-nghiem-tu-van-hoc-duong",
                "tu-van-hoc-duong",
                "https://storage-edu.vnpt.vn/edu-lci/8428/DUY/cm.png",
                "Bài viết chia sẻ các kinh nghiệm quý báu của tổ tư vấn tâm lý học đường trường THCS Ngô Văn Sở trong việc hỗ trợ các em học sinh vượt qua áp lực tâm lý.",
                """<p>Tổ Tư vấn tâm lý học đường trường THCS Ngô Văn Sở luôn là điểm tựa tin cậy cho các em học sinh. Hằng tuần, các thầy cô phụ trách phòng tư vấn luôn lắng nghe, chia sẻ và tháo gỡ những băn khoăn về tâm sinh lý lứa tuổi, quan hệ bạn bè, phương pháp học tập hiệu quả cũng như giải tỏa áp lực thi cử.</p>
                <p>Phụ huynh và các em học sinh có thể gửi câu hỏi hoặc liên hệ trực tiếp phòng Tư vấn học đường tại tầng 2 nhà hiệu bộ để được hỗ trợ tận tình.</p>""",
                "Tổ Tư vấn tâm lý", 0, 1150
            ),
            (
                "GẶP MẶT TRI ÂN THẦY CÔ NHÂN 43 NĂM NGÀY NHÀ GIÁO VIỆT NAM (20/11/1982 – 20/11/2025)",
                "gap-mat-tri-an-thay-co-ngay-nha-giao-viet-nam",
                "su-kien",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/PA1211.png",
                "Ngày 14/11, UBND phường Lào Cai và nhà trường đã tổ chức buổi Gặp mặt chào mừng 43 năm Ngày Nhà giáo Việt Nam trong không khí ấm áp tri ân.",
                """<p>Nhân kỷ niệm 43 năm ngày Nhà giáo Việt Nam 20/11, nhà trường đã tổ chức buổi lễ gặp mặt tri ân đầy xúc động với các thế hệ nhà giáo lão thành cùng toàn thể thầy cô giáo đang công tác tại trường.</p>""",
                "Công đoàn trường", 0, 890
            ),
            (
                "Thông báo trả bằng tốt nghiệp THCS năm học 2023-2024 và các năm học trở về trước",
                "thong-bao-tra-bang-tot-nghiep-thcs",
                "su-kien",
                "https://storage-edu.vnpt.vn/edu-lci/8428/DUY/qlvb-online.png",
                "Bộ phận Văn thư trường THCS Ngô Văn Sở thông báo lịch trả bằng tốt nghiệp THCS cho học sinh các khóa đã tốt nghiệp.",
                """<p>Trường THCS Ngô Văn Sở thông báo kế hoạch trả bằng tốt nghiệp THCS cho cựu học sinh:</p>
                <p>- Thời gian: Các ngày làm việc từ thứ 2 đến thứ 6 hàng tuần.</p>
                <p>- Địa điểm: Văn phòng văn thư nhà trường, tầng 1 nhà hiệu bộ.</p>
                <p>- Thủ tục: Xuất trình Căn cước công dân hoặc giấy tờ tùy thân hợp lệ khi nhận bằng.</p>""",
                "Bộ phận Văn thư", 0, 1450
            )
        ]

        for p in real_posts:
            cursor.execute('''
                INSERT INTO posts (title, slug, category_slug, thumbnail, summary, content, author, is_featured, views)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)

    # Seed Real Documents from target site
    cursor.execute('SELECT COUNT(*) FROM documents')
    if cursor.fetchone()[0] == 0:
        docs = [
            (
                "1631/QĐ-SGD&ĐT",
                "QĐ - V/v ban hành Bộ Quy tắc văn hóa giao thông cho giáo viên, học sinh tỉnh Lào Cai",
                "18/10/2024",
                "Sở GD&ĐT Lào Cai",
                "Văn bản chỉ đạo các cấp",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/QDVBKH/bo-quy-tac-van-hoa-giao-thong-cho-gv-hs-tinh-lc.pdf"
            ),
            (
                "CT/09-UBNDT",
                "CT - Về nhiệm vụ chủ yếu trong dịp Tết Nguyên đán Ất Tỵ năm 2025",
                "20/12/2024",
                "UBND tỉnh Lào Cai",
                "Chỉ thị điều hành",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/QDVBKH/chi_thi_so_09_ubnd_tinh_241230042105989980_20241231050348614.pdf"
            ),
            (
                "CT/04-UBND",
                "CT - Về nhiệm vụ chủ yếu phát triển kinh tế xã hội và giáo dục trên địa bàn",
                "31/12/2024",
                "UBND thành phố Lào Cai",
                "Chỉ thị điều hành",
                "https://storage-edu.vnpt.vn/edu-lci/8428/2024/QDVBKH/chi_thi_ve_nhiem_vu_chu_yeu_tr20241231051929070_signed.pdf"
            ),
            (
                "45/KH-THCSNVS",
                "Kế hoạch thực hiện nhiệm vụ năm học 2026-2027 trường THCS Ngô Văn Sở",
                "08/09/2026",
                "Hiệu trưởng Phùng Thị Dung",
                "Văn bản trường",
                "#"
            ),
            (
                "12/QĐ-THCSNVS",
                "Quyết định thành lập Tổ tư vấn tâm lý học đường năm học 2026-2027",
                "10/09/2026",
                "Trường THCS Ngô Văn Sở",
                "Văn bản trường",
                "#"
            )
        ]
        for d in docs:
            cursor.execute('''
                INSERT INTO documents (doc_code, title, issue_date, signer, category, file_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', d)

    # Seed Sample Students for lookup
    cursor.execute('SELECT COUNT(*) FROM students')
    if cursor.fetchone()[0] == 0:
        sample_students = [
            ("HS202601", "Nguyễn Văn An", "9A1", "12/03/2012", "Học kỳ I - 2026-2027", 9.2, 8.5, 9.0, 8.8, 9.0, 8.5, 8.9, "Xuất sắc", "Tốt"),
            ("HS202602", "Trần Thị Mai", "9A1", "05/08/2012", "Học kỳ I - 2026-2027", 8.8, 9.0, 9.5, 8.5, 8.0, 9.0, 8.8, "Giỏi", "Tốt"),
            ("HS202603", "Lê Hoàng Phúc", "8A2", "20/11/2013", "Học kỳ I - 2026-2027", 9.5, 8.8, 9.2, 9.0, 9.5, 9.0, 9.2, "Xuất sắc", "Tốt"),
            ("HS202604", "Hoàng Thu Thảo", "7A3", "14/02/2014", "Học kỳ I - 2026-2027", 8.0, 8.5, 8.0, 8.2, 8.0, 8.5, 8.2, "Khá", "Tốt"),
            ("HS202605", "Đặng Minh Quân", "6A1", "09/06/2015", "Học kỳ I - 2026-2027", 9.0, 9.0, 9.5, 8.8, 8.5, 9.2, 9.0, "Giỏi", "Tốt")
        ]
        for s in sample_students:
            cursor.execute('''
                INSERT INTO students (student_code, full_name, class_name, birth_date, semester, math, literature, english, physics, chemistry, history, gpa, rank, conduct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', s)

    # Seed Sample Feedbacks
    cursor.execute('SELECT COUNT(*) FROM feedbacks')
    if cursor.fetchone()[0] == 0:
        sample_fbs = [
            ("Nguyễn Thị Lan (Phụ huynh lớp 8A2)", "lan.nguyen@gmail.com", "0988123456", "Ý kiến về hoạt động ngoại khóa", "Kính gửi Ban giám hiệu, gia đình rất ủng hộ các hoạt động trải nghiệm kỹ năng sống vừa qua của nhà trường. Kính chúc các thầy cô luôn mạnh khỏe!", "Đã đọc"),
            ("Trần Văn Đức (Phụ huynh lớp 6A1)", "duc.tran@gmail.com", "0977654321", "Đóng góp về căn tin nhà trường", "Đề nghị nhà trường giám sát chặt chẽ vệ sinh an toàn thực phẩm tại khu vực căn tin phục vụ học sinh.", "Chưa đọc")
        ]
        for fb in sample_fbs:
            cursor.execute('''
                INSERT INTO feedbacks (sender_name, email, phone, title, content, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', fb)

    conn.commit()
    conn.close()
    print("Database initialized and populated successfully.")

if __name__ == '__main__':
    init_db()

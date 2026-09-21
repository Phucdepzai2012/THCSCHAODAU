from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import os
import re
import unicodedata
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from database import get_db, hash_password, init_db

import socket
import subprocess
import threading

app = Flask(__name__)
app.secret_key = 'thcs-ngo-van-so-secret-key-2026'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max upload

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def get_public_url():
    url_file = os.path.join(os.path.dirname(__file__), 'public_url.txt')
    if os.path.exists(url_file):
        try:
            with open(url_file, 'r', encoding='utf-8') as f:
                url = f.read().strip()
                if url.startswith('http'):
                    return url
        except Exception:
            pass
    return None

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để truy cập trang quản trị.', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to provide common data (stats, settings, categories, links) to all templates
@app.context_processor
def inject_common():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, val FROM settings')
    settings = {row['key']: row['val'] for row in cursor.fetchall()}

    cursor.execute('SELECT key, val FROM stats')
    stats = {row['key']: row['val'] for row in cursor.fetchall()}

    cursor.execute('SELECT slug, name FROM categories')
    categories = cursor.fetchall()
    conn.close()

    local_ip = get_local_ip()
    public_url = get_public_url()

    return dict(
        settings=settings,
        stats=stats,
        categories=categories,
        now=datetime.now(),
        local_ip=local_ip,
        local_share_url=f"http://{local_ip}:5000",
        public_share_url=public_url
    )

# ================= PUBLIC ROUTES =================

@app.route('/')
@app.route('/index')
@app.route('/index.html')
@app.route('/index.php')
@app.route('/home')
@app.route('/trang-chu')
def index():
    conn = get_db()
    cursor = conn.cursor()

    # Update visit counters
    cursor.execute("UPDATE stats SET val = val + 1 WHERE key = 'total_visits'")
    cursor.execute("UPDATE stats SET val = val + 1 WHERE key = 'visits_today'")
    conn.commit()

    # Featured slider posts
    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at, category_slug
        FROM posts
        WHERE is_featured = 1
        ORDER BY published_at DESC LIMIT 6
    ''')
    featured_posts = cursor.fetchall()

    # Recent news (Tin tức)
    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at
        FROM posts
        WHERE category_slug = 'tin-tuc'
        ORDER BY published_at DESC LIMIT 5
    ''')
    news_posts = cursor.fetchall()

    # Public notices (Nội dung công khai)
    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at
        FROM posts
        WHERE category_slug = 'noi-dung-cong-khai'
        ORDER BY published_at DESC LIMIT 5
    ''')
    public_posts = cursor.fetchall()

    # Timetables (Thời khóa biểu)
    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at
        FROM posts
        WHERE category_slug = 'thoi-khoa-bieu'
        ORDER BY published_at DESC LIMIT 5
    ''')
    timetable_posts = cursor.fetchall()

    # School counseling (Tư vấn học đường)
    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at
        FROM posts
        WHERE category_slug = 'tu-van-hoc-duong'
        ORDER BY published_at DESC LIMIT 5
    ''')
    counseling_posts = cursor.fetchall()

    # Events & Notices (Sự kiện)
    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at
        FROM posts
        WHERE category_slug = 'su-kien'
        ORDER BY published_at DESC LIMIT 5
    ''')
    event_posts = cursor.fetchall()

    # Right sidebar: New Documents
    cursor.execute('''
        SELECT id, doc_code, title, issue_date, signer, file_url
        FROM documents
        ORDER BY issue_date DESC, id DESC LIMIT 5
    ''')
    documents = cursor.fetchall()

    conn.close()
    return render_template('index.html',
                           featured_posts=featured_posts,
                           news_posts=news_posts,
                           public_posts=public_posts,
                           timetable_posts=timetable_posts,
                           counseling_posts=counseling_posts,
                           event_posts=event_posts,
                           documents=documents)

@app.route('/bai-viet/<slug_or_id>')
@app.route('/post/<slug_or_id>')
@app.route('/tin-tuc/<slug_or_id>')
@app.route('/article/<slug_or_id>')
@app.route('/news/<slug_or_id>')
def post_detail(slug_or_id):
    conn = get_db()
    cursor = conn.cursor()

    if slug_or_id.isdigit():
        cursor.execute('SELECT * FROM posts WHERE id = ?', (int(slug_or_id),))
    else:
        cursor.execute('SELECT * FROM posts WHERE slug = ?', (slug_or_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        flash('Bài viết không tồn tại hoặc đã được gỡ bỏ.', 'danger')
        return redirect(url_for('index'))

    # Increase view count
    cursor.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post['id'],))
    conn.commit()

    # Get related posts
    cursor.execute('''
        SELECT id, title, slug, thumbnail, published_at
        FROM posts
        WHERE category_slug = ? AND id != ?
        ORDER BY published_at DESC LIMIT 5
    ''', (post['category_slug'], post['id']))
    related_posts = cursor.fetchall()

    # Get category name
    cursor.execute('SELECT name FROM categories WHERE slug = ?', (post['category_slug'],))
    cat_row = cursor.fetchone()
    category_name = cat_row['name'] if cat_row else 'Tin tức'

    conn.close()
    return render_template('post_detail.html', post=post, related_posts=related_posts, category_name=category_name)

@app.route('/danh-muc/<slug>')
@app.route('/category/<slug>')
@app.route('/chuyen-muc/<slug>')
def category_view(slug):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT name, description FROM categories WHERE slug = ?', (slug,))
    cat = cursor.fetchone()
    if not cat:
        conn.close()
        flash('Chuyên mục không tồn tại.', 'warning')
        return redirect(url_for('index'))

    cursor.execute('''
        SELECT id, title, slug, thumbnail, summary, published_at, views
        FROM posts
        WHERE category_slug = ?
        ORDER BY published_at DESC
    ''', (slug,))
    posts = cursor.fetchall()

    conn.close()
    return render_template('category.html', category=cat, slug=slug, posts=posts)

@app.route('/van-ban')
@app.route('/documents')
@app.route('/vanban')
def documents_view():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents ORDER BY issue_date DESC, id DESC')
    docs = cursor.fetchall()
    conn.close()
    return render_template('documents.html', documents=docs)

@app.route('/thoi-khoa-bieu')
def timetable_view():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM posts
        WHERE category_slug = 'thoi-khoa-bieu'
        ORDER BY published_at DESC
    ''')
    posts = cursor.fetchall()
    conn.close()
    return render_template('category.html',
                           category={'name': 'Thời khóa biểu', 'description': 'Thời khóa biểu các khối trường chính và phân hiệu 2'},
                           slug='thoi-khoa-bieu',
                           posts=posts)

@app.route('/tra-cuu', methods=['GET', 'POST'])
@app.route('/search-student', methods=['GET', 'POST'])
@app.route('/diem', methods=['GET', 'POST'])
def search_student():
    student_result = None
    query = request.args.get('q', '').strip()
    if request.method == 'POST':
        query = request.form.get('student_query', '').strip()

    if query:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM students
            WHERE student_code LIKE ? OR full_name LIKE ?
            LIMIT 1
        ''', (f'%{query}%', f'%{query}%'))
        student_result = cursor.fetchone()
        conn.close()

    return render_template('search_student.html', query=query, student=student_result)

@app.route('/gop-y', methods=['GET', 'POST'])
def feedback_view():
    if request.method == 'POST':
        name = request.form.get('sender_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not name or not title or not content:
            flash('Vui lòng điền đầy đủ các thông tin bắt buộc (*).', 'danger')
        else:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedbacks (sender_name, email, phone, title, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, phone, title, content))
            conn.commit()
            conn.close()
            flash('Cảm ơn bạn! Ý kiến đóng góp của bạn đã được gửi thành công đến Ban Giám hiệu nhà trường.', 'success')
            return redirect(url_for('feedback_view'))

    return render_template('feedback.html')

@app.route('/tim-kiem')
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, slug, thumbnail, summary, published_at, category_slug
            FROM posts
            WHERE title LIKE ? OR summary LIKE ? OR content LIKE ?
            ORDER BY published_at DESC LIMIT 20
        ''', (f'%{q}%', f'%{q}%', f'%{q}%'))
        results = cursor.fetchall()
        conn.close()
    return render_template('search.html', query=q, results=results)

@app.route('/so-do-trang')
def sitemap():
    return render_template('sitemap.html')

# Static institutional pages
@app.route('/ban-giam-hieu')
def bgh_view():
    return render_template('institutional.html',
                           page_title='Ban Giám Hiệu',
                           page_type='bgh')

@app.route('/cac-doan-the')
def doanthe_view():
    return render_template('institutional.html',
                           page_title='Các Đoàn Thể',
                           page_type='doanthe')

@app.route('/noi-quy-quy-dinh')
def noiquy_view():
    return render_template('institutional.html',
                           page_title='Nội quy - Quy định nhà trường',
                           page_type='noiquy')

@app.route('/phong-truyen-thong')
def truyen_thong_view():
    return render_template('institutional.html',
                           page_title='Phòng Truyền Thống Nhà Trường',
                           page_type='phong-truyen-thong')

@app.route('/tai-nguyen-day-hoc')
def tai_nguyen_view():
    return render_template('institutional.html',
                           page_title='Tài nguyên Dạy & Học',
                           page_type='tai-nguyen')

# ================= ADMIN ROUTES =================

@app.route('/admin/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
@app.route('/dang-nhap', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user['password_hash'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            session['role'] = user['role']
            flash(f'Đăng nhập thành công! Xin chào {user["display_name"]}.', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('admin_dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác! Vui lòng thử lại.', 'danger')

    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Bạn đã đăng xuất khỏi hệ thống quản trị.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM posts')
    total_posts = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM documents')
    total_docs = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM feedbacks')
    total_feedbacks = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]

    cursor.execute('''
        SELECT id, title, slug, category_slug, published_at, views, is_featured
        FROM posts
        ORDER BY published_at DESC LIMIT 6
    ''')
    recent_posts = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM feedbacks
        ORDER BY created_at DESC LIMIT 5
    ''')
    recent_feedbacks = cursor.fetchall()

    conn.close()
    return render_template('admin/dashboard.html',
                           total_posts=total_posts,
                           total_docs=total_docs,
                           total_feedbacks=total_feedbacks,
                           total_students=total_students,
                           recent_posts=recent_posts,
                           recent_feedbacks=recent_feedbacks)

# Post Management
@app.route('/admin/posts')
@login_required
def admin_posts():
    cat_filter = request.args.get('category', '')
    q = request.args.get('q', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    sql = '''
        SELECT p.*, c.name as category_name
        FROM posts p
        LEFT JOIN categories c ON p.category_slug = c.slug
        WHERE 1=1
    '''
    params = []
    if cat_filter:
        sql += ' AND p.category_slug = ?'
        params.append(cat_filter)
    if q:
        sql += ' AND (p.title LIKE ? OR p.summary LIKE ?)'
        params.extend([f'%{q}%', f'%{q}%'])

    sql += ' ORDER BY p.published_at DESC'
    cursor.execute(sql, params)
    posts = cursor.fetchall()

    cursor.execute('SELECT slug, name FROM categories')
    cats = cursor.fetchall()
    conn.close()

    return render_template('admin/posts.html', posts=posts, categories=cats, current_cat=cat_filter, query=q)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def admin_post_new():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_slug = request.form.get('category_slug', 'tin-tuc')
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        thumbnail = request.form.get('thumbnail_url', '').strip()
        author = request.form.get('author', session.get('display_name', 'Ban Biên Tập')).strip()
        is_featured = 1 if request.form.get('is_featured') else 0

        # Handle file upload if provided
        if 'thumbnail_file' in request.files:
            file = request.files['thumbnail_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_name = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                thumbnail = f"/static/uploads/{unique_name}"

        if not thumbnail:
            thumbnail = "https://storage-edu.vnpt.vn/edu-lci/8428/2024/AnhNhaTruong/Picture1-205853.jpg"

        slug_base = slugify(title)
        slug = slug_base
        counter = 1
        while True:
            cursor.execute('SELECT id FROM posts WHERE slug = ?', (slug,))
            if not cursor.fetchone():
                break
            slug = f"{slug_base}-{counter}"
            counter += 1

        cursor.execute('''
            INSERT INTO posts (title, slug, category_slug, thumbnail, summary, content, author, is_featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, slug, category_slug, thumbnail, summary, content, author, is_featured))
        conn.commit()
        conn.close()

        flash('Đã đăng bài viết mới thành công!', 'success')
        return redirect(url_for('admin_posts'))

    cursor.execute('SELECT slug, name FROM categories')
    cats = cursor.fetchall()
    conn.close()
    return render_template('admin/post_form.html', post=None, categories=cats, action_title='Thêm Bài Viết Mới')

@app.route('/admin/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def admin_post_edit(post_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    if not post:
        conn.close()
        flash('Không tìm thấy bài viết.', 'danger')
        return redirect(url_for('admin_posts'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_slug = request.form.get('category_slug', 'tin-tuc')
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        thumbnail = request.form.get('thumbnail_url', '').strip()
        author = request.form.get('author', 'Ban Biên Tập').strip()
        is_featured = 1 if request.form.get('is_featured') else 0

        # Upload
        if 'thumbnail_file' in request.files:
            file = request.files['thumbnail_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_name = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                thumbnail = f"/static/uploads/{unique_name}"

        if not thumbnail:
            thumbnail = post['thumbnail']

        cursor.execute('''
            UPDATE posts
            SET title = ?, category_slug = ?, thumbnail = ?, summary = ?, content = ?, author = ?, is_featured = ?
            WHERE id = ?
        ''', (title, category_slug, thumbnail, summary, content, author, is_featured, post_id))
        conn.commit()
        conn.close()

        flash('Cập nhật bài viết thành công!', 'success')
        return redirect(url_for('admin_posts'))

    cursor.execute('SELECT slug, name FROM categories')
    cats = cursor.fetchall()
    conn.close()
    return render_template('admin/post_form.html', post=post, categories=cats, action_title='Chỉnh Sửa Bài Viết')

@app.route('/admin/posts/delete/<int:post_id>', methods=['POST'])
@login_required
def admin_post_delete(post_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Đã xóa bài viết thành công!', 'success')
    return redirect(url_for('admin_posts'))

# Document Management
@app.route('/admin/documents', methods=['GET', 'POST'])
@login_required
def admin_documents():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        doc_code = request.form.get('doc_code', '').strip()
        title = request.form.get('title', '').strip()
        issue_date = request.form.get('issue_date', datetime.now().strftime('%d/%m/%Y')).strip()
        signer = request.form.get('signer', 'Sở GD&ĐT / UBND').strip()
        category = request.form.get('category', 'Văn bản chỉ đạo').strip()
        file_url = request.form.get('file_url', '#').strip()

        if 'file_upload' in request.files:
            file = request.files['file_upload']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_name = f"doc_{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                file_url = f"/static/uploads/{unique_name}"

        cursor.execute('''
            INSERT INTO documents (doc_code, title, issue_date, signer, category, file_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (doc_code, title, issue_date, signer, category, file_url))
        conn.commit()
        flash('Thêm văn bản mới thành công!', 'success')
        return redirect(url_for('admin_documents'))

    cursor.execute('SELECT * FROM documents ORDER BY id DESC')
    docs = cursor.fetchall()
    conn.close()
    return render_template('admin/documents.html', documents=docs)

@app.route('/admin/documents/delete/<int:doc_id>', methods=['POST'])
@login_required
def admin_document_delete(doc_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()
    flash('Đã xóa văn bản thành công!', 'success')
    return redirect(url_for('admin_documents'))

# Feedback Management
@app.route('/admin/feedback')
@login_required
def admin_feedback():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM feedbacks ORDER BY created_at DESC')
    feedbacks = cursor.fetchall()
    conn.close()
    return render_template('admin/feedback_list.html', feedbacks=feedbacks)

@app.route('/admin/feedback/toggle/<int:fb_id>', methods=['POST'])
@login_required
def admin_feedback_toggle(fb_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE feedbacks
        SET status = CASE WHEN status = 'Đã đọc' THEN 'Chưa đọc' ELSE 'Đã đọc' END
        WHERE id = ?
    ''', (fb_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_feedback'))

# Student Grade Management
@app.route('/admin/students', methods=['GET', 'POST'])
@login_required
def admin_students():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        student_code = request.form.get('student_code', '').strip().upper()
        full_name = request.form.get('full_name', '').strip()
        class_name = request.form.get('class_name', '').strip()
        birth_date = request.form.get('birth_date', '').strip()
        math = float(request.form.get('math', 0) or 0)
        literature = float(request.form.get('literature', 0) or 0)
        english = float(request.form.get('english', 0) or 0)
        physics = float(request.form.get('physics', 0) or 0)
        chemistry = float(request.form.get('chemistry', 0) or 0)
        history = float(request.form.get('history', 0) or 0)

        gpa = round((math*2 + literature*2 + english*2 + physics + chemistry + history) / 9.0, 1)
        rank = 'Xuất sắc' if gpa >= 9.0 else ('Giỏi' if gpa >= 8.0 else ('Khá' if gpa >= 6.5 else 'Trung bình'))

        cursor.execute('''
            INSERT OR REPLACE INTO students
            (student_code, full_name, class_name, birth_date, math, literature, english, physics, chemistry, history, gpa, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_code, full_name, class_name, birth_date, math, literature, english, physics, chemistry, history, gpa, rank))
        conn.commit()
        flash('Đã lưu dữ liệu học sinh thành công!', 'success')
        return redirect(url_for('admin_students'))

    cursor.execute('SELECT * FROM students ORDER BY class_name, full_name')
    students = cursor.fetchall()
    conn.close()
    return render_template('admin/students.html', students=students)

# Settings Management
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action', 'general')

        if action == 'general':
            text_fields = [
                'school_name', 'school_short_name', 'school_slogan',
                'address', 'phone', 'email', 'principal',
                'founded_year', 'youtube_video', 'announcement_marquee',
                'facebook_url', 'zalo_url', 'footer_note'
            ]
            for key in text_fields:
                if key in request.form:
                    cursor.execute('INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)',
                                   (key, request.form[key].strip()))
            conn.commit()
            flash('✅ Cập nhật thông tin trường thành công!', 'success')

        elif action in ['banner', 'promo_banner', 'sidebar_banner_1', 'sidebar_banner_2', 'sidebar_banner_3']:
            prefix = action
            url_key = f"{prefix}_url" if prefix != 'banner' else 'banner_url'
            link_key = f"{prefix}_link" if prefix != 'banner' else 'banner_link'
            title_key = f"{prefix}_title"
            active_key = f"{prefix}_active"
            file_key = f"{prefix}_file"

            img_url = request.form.get(url_key, '').strip()
            if file_key in request.files:
                f = request.files[file_key]
                if f and f.filename:
                    fname = f"{prefix}_{int(datetime.now().timestamp())}_{secure_filename(f.filename)}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    img_url = f"/static/uploads/{fname}"

            if img_url:
                cursor.execute('INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)', (url_key, img_url))
            if link_key in request.form:
                cursor.execute('INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)', (link_key, request.form.get(link_key, '').strip()))
            if title_key in request.form:
                cursor.execute('INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)', (title_key, request.form.get(title_key, '').strip()))
            
            # Active status
            active_val = '1' if request.form.get(active_key) == '1' else '0'
            cursor.execute('INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)', (active_key, active_val))
            conn.commit()

            banner_labels = {
                'banner': 'Banner chính đầu trang',
                'promo_banner': 'Banner tuyên truyền giữa trang',
                'sidebar_banner_1': 'Banner cột phải vị trí 1',
                'sidebar_banner_2': 'Banner cột phải vị trí 2',
                'sidebar_banner_3': 'Banner cột phải vị trí 3'
            }
            flash(f'✅ Cập nhật {banner_labels.get(prefix, "Banner")} thành công!', 'success')

        elif action == 'logo':
            # Handle logo upload or URL
            logo_url = request.form.get('logo_url', '').strip()
            if 'logo_file' in request.files:
                f = request.files['logo_file']
                if f and f.filename:
                    fname = f"logo_{int(datetime.now().timestamp())}_{secure_filename(f.filename)}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    logo_url = f"/static/uploads/{fname}"
            if logo_url:
                cursor.execute('INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)',
                               ('logo_url', logo_url))
                conn.commit()
                flash('✅ Cập nhật Logo thành công!', 'success')
            else:
                flash('⚠️ Vui lòng chọn file hoặc nhập URL logo.', 'warning')

        elif action == 'password':
            old_pw = request.form.get('old_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
            user = cursor.fetchone()

            if not user or user['password_hash'] != hash_password(old_pw):
                flash('❌ Mật khẩu hiện tại không đúng!', 'danger')
            elif new_pw != confirm_pw:
                flash('❌ Xác nhận mật khẩu mới không khớp!', 'danger')
            elif len(new_pw) < 6:
                flash('❌ Mật khẩu mới phải có ít nhất 6 ký tự!', 'danger')
            else:
                cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                               (hash_password(new_pw), session['user_id']))
                conn.commit()
                flash('✅ Đổi mật khẩu thành công! Vui lòng đăng nhập lại.', 'success')

        conn.close()
        return redirect(url_for('admin_settings'))

    cursor.execute('SELECT key, val FROM settings')
    settings = {row['key']: row['val'] for row in cursor.fetchall()}
    conn.close()
    return render_template('admin/settings.html', settings=settings)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('404.html'), 500

if __name__ == '__main__':
    init_db()
    print("Starting THCS Ngo Van So Portal Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)


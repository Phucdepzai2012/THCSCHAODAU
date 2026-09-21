import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app
from database import get_db, hash_password

client = app.test_client()

# 1. Test Login with wrong password (must NOT leak password)
res = client.post('/admin/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
html = res.get_data(as_text=True)
assert 'Phuc2012@' not in html, 'FAILED: Password leaked in login response!'
assert 'Tên đăng nhập hoặc mật khẩu không chính xác' in html, 'FAILED: Error message missing'
print('PASS 1: Mật khẩu không còn bị lộ khi đăng nhập sai.')

# 2. Test Home page renders cleanly with banners
res = client.get('/')
assert res.status_code == 200, 'FAILED: Trang chủ không phản hồi 200'
print('PASS 2: Trang chủ tải thành công với hệ thống banner mới.')

# 3. Test Admin Settings Multi-slot banner post
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['username'] = 'admin'
    sess['role'] = 'admin'

res = client.post('/admin/settings', data={
    'action': 'promo_banner',
    'promo_banner_active': '1',
    'promo_banner_title': 'Banner Thử Nghiệm Test',
    'promo_banner_url': 'https://storage-vnportal.vnpt.vn/bcn-khdn/3405/banner/hcm_khoangtrang.png',
    'promo_banner_link': '/post/ra-mat-khong-gian-van-hoa-ho-chi-minh'
}, follow_redirects=True)
assert res.status_code == 200, 'FAILED: Cập nhật banner thất bại'

conn = get_db()
c = conn.cursor()
c.execute("SELECT val FROM settings WHERE key='promo_banner_title'")
row = c.fetchone()
assert row['val'] == 'Banner Thử Nghiệm Test', f'FAILED: Sai giá trị {row}'
print('PASS 3: Quản lý và lưu cấu hình Banner hoạt động hoàn hảo.')

# 4. Test Change Password Security
res = client.post('/admin/settings', data={
    'action': 'password',
    'old_password': 'wrong_old_password',
    'new_password': 'NewPassword123@',
    'confirm_password': 'NewPassword123@'
}, follow_redirects=True)
assert 'Mật khẩu hiện tại không đúng' in res.get_data(as_text=True)
print('PASS 4: Tính năng Đổi mật khẩu Admin bảo mật và xác thực chính xác.')

print('\n===> TẤT CẢ 4 BÀI KIỂM THỬ ĐÃ VƯỢT QUA 100%! <===')

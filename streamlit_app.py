from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, json, uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'labuan-bajo-land-secret-2024'

@app.template_filter('fromjson')
def fromjson_filter(s):
    try:
        return json.loads(s) if s else []
    except Exception:
        return []

UPLOAD_FOLDER = 'static/uploads'
BACKGROUND_FOLDER = 'static/backgrounds'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BACKGROUND_FOLDER'] = BACKGROUND_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('land.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS lands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        location TEXT NOT NULL,
        area REAL NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        certificate TEXT DEFAULT 'SHM',
        land_type TEXT DEFAULT 'Tanah Pribadi',
        status TEXT DEFAULT 'Dijual',
        lat REAL,
        lng REAL,
        map_url TEXT,
        images TEXT DEFAULT '[]',
        contact_wa TEXT,
        posted_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (posted_by) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Default settings
    defaults = [
        ('background_color', '#0a1628'),
        ('background_image', ''),
        ('site_title', 'Tanah Labuan Bajo'),
        ('site_subtitle', 'Properti Premium di Surga Indonesia'),
        ('wa_number', '6281234567890'),
        ('hero_text', 'Temukan Tanah Impian Anda di Labuan Bajo'),
    ]
    for key, value in defaults:
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

    # Default superadmin
    c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
              ('superadmin', generate_password_hash('admin123'), 'superadmin'))
    # Default admin
    c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
              ('admin', generate_password_hash('admin456'), 'admin'))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = get_db()
    row = conn.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else ''

def get_all_settings():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'superadmin':
            flash('Akses ditolak. Hanya superadmin yang bisa mengakses fitur ini.', 'error')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated

# ─── PUBLIC ROUTES ───────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    lands = conn.execute('SELECT * FROM lands WHERE status="Dijual" ORDER BY created_at DESC').fetchall()
    conn.close()
    settings = get_all_settings()
    return render_template('index.html', lands=lands, settings=settings)

@app.route('/tanah/<int:land_id>')
def land_detail(land_id):
    conn = get_db()
    land = conn.execute('SELECT * FROM lands WHERE id=?', (land_id,)).fetchone()
    conn.close()
    if not land:
        return redirect(url_for('index'))
    settings = get_all_settings()
    images = json.loads(land['images']) if land['images'] else []
    wa_number = land['contact_wa'] or settings.get('wa_number', '')
    return render_template('detail.html', land=land, images=images, settings=settings, wa_number=wa_number)

# ─── AUTH ROUTES ─────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('admin_dashboard'))
        flash('Username atau password salah!', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

# ─── ADMIN ROUTES ─────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db()
    lands = conn.execute('SELECT * FROM lands ORDER BY created_at DESC').fetchall()
    total = conn.execute('SELECT COUNT(*) as c FROM lands').fetchone()['c']
    dijual = conn.execute('SELECT COUNT(*) as c FROM lands WHERE status="Dijual"').fetchone()['c']
    terjual = conn.execute('SELECT COUNT(*) as c FROM lands WHERE status="Terjual"').fetchone()['c']
    conn.close()
    settings = get_all_settings()
    return render_template('admin/dashboard.html', lands=lands, total=total,
                           dijual=dijual, terjual=terjual, settings=settings)

@app.route('/admin/tanah/tambah', methods=['GET', 'POST'])
@login_required
def add_land():
    settings = get_all_settings()
    if request.method == 'POST':
        images = []
        if 'images' in request.files:
            for f in request.files.getlist('images'):
                if f and allowed_file(f.filename):
                    ext = f.filename.rsplit('.', 1)[1].lower()
                    fname = f"{uuid.uuid4().hex}.{ext}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    images.append(fname)

        lat = request.form.get('lat') or None
        lng = request.form.get('lng') or None

        conn = get_db()
        conn.execute('''INSERT INTO lands 
            (title, location, area, price, description, certificate, land_type, status, lat, lng, images, contact_wa, posted_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (request.form['title'], request.form['location'],
             float(request.form['area']), float(request.form['price'].replace('.', '').replace(',', '')),
             request.form['description'], request.form['certificate'],
             request.form['land_type'], request.form['status'],
             lat, lng, json.dumps(images),
             request.form.get('contact_wa') or settings.get('wa_number'),
             session['user_id']))
        conn.commit()
        conn.close()
        flash('Tanah berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_land.html', settings=settings)

@app.route('/admin/tanah/edit/<int:land_id>', methods=['GET', 'POST'])
@login_required
def edit_land(land_id):
    conn = get_db()
    land = conn.execute('SELECT * FROM lands WHERE id=?', (land_id,)).fetchone()
    conn.close()
    settings = get_all_settings()
    if not land:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        images = json.loads(land['images']) if land['images'] else []
        if 'images' in request.files:
            for f in request.files.getlist('images'):
                if f and f.filename and allowed_file(f.filename):
                    ext = f.filename.rsplit('.', 1)[1].lower()
                    fname = f"{uuid.uuid4().hex}.{ext}"
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    images.append(fname)

        lat = request.form.get('lat') or None
        lng = request.form.get('lng') or None

        conn = get_db()
        conn.execute('''UPDATE lands SET title=?, location=?, area=?, price=?, description=?,
            certificate=?, land_type=?, status=?, lat=?, lng=?, images=?, contact_wa=?
            WHERE id=?''',
            (request.form['title'], request.form['location'],
             float(request.form['area']), float(request.form['price'].replace('.', '').replace(',', '')),
             request.form['description'], request.form['certificate'],
             request.form['land_type'], request.form['status'],
             lat, lng, json.dumps(images),
             request.form.get('contact_wa') or settings.get('wa_number'),
             land_id))
        conn.commit()
        conn.close()
        flash('Data tanah berhasil diperbarui!', 'success')
        return redirect(url_for('admin_dashboard'))

    images = json.loads(land['images']) if land['images'] else []
    return render_template('admin/edit_land.html', land=land, images=images, settings=settings)

@app.route('/admin/tanah/hapus/<int:land_id>', methods=['POST'])
@login_required
def delete_land(land_id):
    conn = get_db()
    conn.execute('DELETE FROM lands WHERE id=?', (land_id,))
    conn.commit()
    conn.close()
    flash('Data tanah berhasil dihapus!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/tanah/hapus-gambar', methods=['POST'])
@login_required
def delete_image():
    data = request.json
    land_id = data.get('land_id')
    filename = data.get('filename')
    conn = get_db()
    land = conn.execute('SELECT images FROM lands WHERE id=?', (land_id,)).fetchone()
    if land:
        imgs = json.loads(land['images'])
        if filename in imgs:
            imgs.remove(filename)
            conn.execute('UPDATE lands SET images=? WHERE id=?', (json.dumps(imgs), land_id))
            conn.commit()
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except:
                pass
    conn.close()
    return jsonify({'success': True})

# ─── SETTINGS ROUTES ──────────────────────────────────────────────

@app.route('/admin/pengaturan', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = get_all_settings()
    if request.method == 'POST':
        conn = get_db()
        fields = ['site_title', 'site_subtitle', 'hero_text', 'wa_number', 'background_color']
        for field in fields:
            if field in request.form:
                conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                             (field, request.form[field]))
        # Background image upload
        if 'background_image' in request.files:
            f = request.files['background_image']
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                fname = f"bg_{uuid.uuid4().hex}.{ext}"
                f.save(os.path.join(app.config['BACKGROUND_FOLDER'], fname))
                conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                             ('background_image', fname))
        # Clear background image
        if request.form.get('clear_bg') == '1':
            conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                         ('background_image', ''))
        conn.commit()
        conn.close()
        flash('Pengaturan berhasil disimpan!', 'success')
        return redirect(url_for('admin_settings'))
    return render_template('admin/settings.html', settings=settings)

# ─── USER MANAGEMENT (SUPERADMIN ONLY) ───────────────────────────

@app.route('/admin/pengguna')
@login_required
@superadmin_required
def manage_users():
    conn = get_db()
    users = conn.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    settings = get_all_settings()
    return render_template('admin/users.html', users=users, settings=settings)

@app.route('/admin/pengguna/tambah', methods=['POST'])
@login_required
@superadmin_required
def add_user():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password, role) VALUES (?,?,?)',
                     (username, generate_password_hash(password), role))
        conn.commit()
        flash(f'Admin "{username}" berhasil ditambahkan!', 'success')
    except sqlite3.IntegrityError:
        flash('Username sudah digunakan!', 'error')
    conn.close()
    return redirect(url_for('manage_users'))

@app.route('/admin/pengguna/hapus/<int:user_id>', methods=['POST'])
@login_required
@superadmin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('Anda tidak bisa menghapus akun sendiri!', 'error')
        return redirect(url_for('manage_users'))
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('Pengguna berhasil dihapus!', 'success')
    return redirect(url_for('manage_users'))

if __name__ == '__main__':
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(BACKGROUND_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)

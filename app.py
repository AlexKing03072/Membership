import sqlite3
from flask import Flask, jsonify, request, render_template, redirect, url_for


# 設定 Flask 應用程式
app = Flask(__name__)

# 設定常數
DB_NAME = 'membership.db'


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as db:
        db.execute(
            '''CREATE TABLE IF NOT EXISTS members (
                iid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT,
                birthdate TEXT
            )'''
        )
        # 插入初始資料，使用 INSERT OR IGNORE 避免重複插入
        db.execute(
            '''INSERT OR IGNORE INTO members (username, email, password, phone, birthdate)
            VALUES (?, ?, ?, ?, ?)''',
            ('admin', 'admin@example.com', 'admin123', '0912345678', '1990-01-01'),
        )
        db.commit()


# 初始化資料庫
init_db()


@app.template_filter('add_stars')
def add_stars_filter(s: str) -> str:
    return f"★{s}★"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        birth = request.form.get('birthdate')

        if not username or not email or not password:
            return render_template('error.html', message='請輸入用戶名、電子郵件和密碼')

        with connect_db() as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM members WHERE username = ?', (username,))
            if cursor.fetchone():
                return render_template('error.html', message='用戶名已存在')

            cursor.execute(
                '''INSERT INTO members (username, email, password, phone, birthdate)
                VALUES (?, ?, ?, ?, ?)''',
                (username, email, password, phone, birth),
            )
            db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return render_template('error.html', message='請輸入電子郵件和密碼')

        with connect_db() as db:
            cursor = db.cursor()
            cursor.execute('SELECT iid, username, password FROM members WHERE email = ?', (email,))
            user = cursor.fetchone()

        if not user or user['password'] != password:
            return render_template('error.html', message='電子郵件或密碼錯誤')
        # 登入成功，重定向到歡迎頁面
        return render_template('welcome.html', username=user['username'], iid=user['iid'])

    return render_template('login.html')


@app.route('/welcome/<int:iid>')
def welcome(iid: int):
    with connect_db() as db:
        cursor = db.cursor()
        cursor.execute('SELECT username FROM members WHERE iid = ?', (iid,))
        row = cursor.fetchone()
        if not row:
            return render_template('error.html', message='找不到使用者')
        username = row['username']
    return render_template('welcome.html', username=username, iid=iid)


@app.route('/edit_profile/<int:iid>', methods=['GET', 'POST'])
def edit_profile(iid: int):
    with connect_db() as db:
        cursor = db.cursor()
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            birth = request.form.get('birthdate')

            if not email or not password:
                return render_template('error.html', message='請輸入電子郵件和密碼')

            cursor.execute('SELECT * FROM members WHERE email = ? AND iid != ?', (email, iid))
            if cursor.fetchone():
                return render_template('error.html', message='電子郵件已被使用')

            cursor.execute(
                '''UPDATE members SET email=?, password=?, phone=?, birthdate=? WHERE iid=?''',
                (email, password, phone, birth, iid),
            )
            db.commit()
            return redirect(url_for('welcome', iid=iid))

        cursor.execute('SELECT * FROM members WHERE iid = ?', (iid,))
        user = cursor.fetchone()
    return render_template('edit_profile.html', user=user)


@app.route('/delete/<int:iid>')
def delete(iid: int):
    with connect_db() as db:
        cursor = db.cursor()
        cursor.execute('DELETE FROM members WHERE iid = ?', (iid,))
        db.commit()
    return redirect(url_for('index'))

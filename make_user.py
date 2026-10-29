# POS Manager 로그인 계정을 만들거나 비밀번호를 다시 정하는 파일
# 사용법: app.py가 있는 폴더에 이 파일을 넣고, 명령 프롬프트에서  python make_user.py
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash

DB_NAME = "pospro_data.db"  # app.py가 쓰는 DB 파일 이름과 같아야 함

username = input("아이디: ").strip()
password = getpass("비밀번호 (입력해도 화면에 안 보임): ")

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
# DB가 처음이면 표부터 만든다 (app.py의 init_db와 같은 구조)
c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS merchants (
    id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, biz_no TEXT, owner_name TEXT,
    phone TEXT, biz_address TEXT, full_data TEXT)""")
# 같은 아이디가 있으면 비밀번호만 바꾸고, 없으면 새로 만든다
c.execute("""INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')
    ON CONFLICT(username) DO UPDATE SET password = excluded.password""",
    (username, generate_password_hash(password)))
conn.commit()
conn.close()
print(f"완료: '{username}' 계정으로 로그인할 수 있습니다.")

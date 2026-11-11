# 파이썬에 기본으로 들어 있는 SQLite 도구를 꺼내 옵니다. (따로 설치할 필요 없어요)
import sqlite3
# 파일 위치를 다루는 도구예요. 어느 폴더에서 서버를 켜도 같은 DB 파일을 쓰게 하려고요.
from pathlib import Path

# DB 전체가 이 파일 하나예요. app.py 옆에 reviews.db 로 생겨요.
DB_PATH = Path(__file__).parent / "reviews.db"


# DB 파일과 연결(전화 연결 같은 것)을 하나 열어 돌려주는 함수예요.
def connect():
    # 파일이 없으면 새로 만들고, 있으면 그 파일에 연결해요.
    con = sqlite3.connect(DB_PATH)
    # 꺼낸 줄을 r["nickname"]처럼 칸 이름으로 읽을 수 있게 해요.
    con.row_factory = sqlite3.Row
    return con


# 표(엑셀 시트 같은 것)가 없으면 만드는 함수예요. 앱이 켜질 때 한 번 불러요.
def init_db():
    # with: 일이 끝나면 저장(commit)을 자동으로 해 줘요.
    with connect() as con:
        # IF NOT EXISTS: 이미 표가 있으면 건드리지 않아요. (저장된 후기가 지워지지 않게)
        con.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id         INTEGER PRIMARY KEY,                -- 후기 번호 (자동으로 1, 2, 3…)
                class_id   INTEGER NOT NULL,                   -- 어느 클래스의 후기인지
                nickname   TEXT    NOT NULL,                   -- 닉네임
                star       INTEGER NOT NULL,                   -- 별점 1~5
                content    TEXT    NOT NULL,                   -- 후기 내용
                created_at TEXT    DEFAULT (datetime('now', 'localtime'))  -- 저장 시각 (자동)
            )
        """)
    # with는 저장만 해 주고 연결은 닫지 않아서, 다 쓴 연결을 직접 닫아요.
    con.close()


# 후기 하나를 표에 넣는 함수예요.
def add_review(class_id, nickname, star, content):
    with connect() as con:
        # 사용자 값은 문장에 이어 붙이지 않고 ? 자리에 따로 넘겨요. 그래야 값이 명령이 되지 않아요.
        con.execute(
            "INSERT INTO reviews (class_id, nickname, star, content) VALUES (?, ?, ?, ?)",
            (class_id, nickname, star, content),
        )
    con.close()


# 그 클래스의 후기를 최신순(번호가 큰 것부터)으로 꺼내는 함수예요.
def get_reviews(class_id):
    with connect() as con:
        # 클래스 번호도 ? 자리에 넣어요.
        rows = con.execute(
            "SELECT nickname, star, content, created_at FROM reviews WHERE class_id = ? ORDER BY id DESC",
            (class_id,),
        ).fetchall()
    con.close()
    # 템플릿에서 r.nickname 처럼 쓸 수 있게 사전(dict) 목록으로 바꿔 돌려줘요.
    return [dict(r) for r in rows]

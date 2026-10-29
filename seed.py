# 데모 데이터 넣기
# 가상의 가맹점 5곳과 데모 계정(demo / demo1234)을 만든다.
# 사용법: app.py가 있는 폴더에서  python seed.py
# 이미 가맹점이 있으면 가맹점은 다시 넣지 않는다(중복 방지).
import sqlite3
import json
from werkzeug.security import generate_password_hash

DB_NAME = "pospro_data.db"


def eq(eq_id, type_, model, van="", cond="신품", qty="1", memo=""):
    """장비 한 대의 정보를 앱이 쓰는 형식으로 만든다."""
    return {"eq_id": eq_id, "type": type_, "type_other": "", "van": van, "model": model,
            "model_other": "", "qty": qty, "cond": cond, "memo": memo}


def history(date, worker, category, content="", status="완료", actions=None, auto_content=""):
    """작업 이력 한 건을 앱이 쓰는 형식으로 만든다."""
    return {"status": status, "mode": "장비" if actions else "일반", "date": date, "worker": worker,
            "category": category, "category_other": "", "content": content,
            "auto_content": auto_content, "img_urls": [], "actions": actions or []}


def merchant(store_name, biz_no, owner_name, owner_phone, biz_address, **extra):
    """가맹점 한 곳의 기본 틀. 필요한 항목만 extra로 덮어쓴다."""
    data = {
        "store_name": store_name, "biz_no": biz_no, "owner_name": owner_name,
        "owner_phone": owner_phone, "store_phone": "", "biz_address": biz_address,
        "biz_address_detail": "", "biz_address_memo": "", "merchant_memo": "",
        "biz_type": "개인", "tax_type": "일반", "paper_type": "유상",
        "franchise": "", "franchise_other": "", "program_other": "",
        "program_fee_type": "해당없음", "program_fee_amount": "",
        "rental_fee_type": "월 대여료", "rental_fee_amount": "35,000",
        "van_list": ["FD"], "program_list": ["유니온"], "extra_contacts": [],
        "additional_addresses": [], "equipments": [],
        "contracts": [{"memo": "", "amount": "", "start": "2025-03-02", "term": "36"}],
        "histories": [],
    }
    data.update(extra)
    return data


# 모든 상호·사업자번호·연락처는 가상이며, 실제 프랜차이즈와 연결하지 않았다. 주소는 길안내 테스트를 위해 공공건물·업무지구 주소를 썼다.
MERCHANTS = [
    merchant("[데모] 한입치킨 동대문점", "000-00-00001", "김데모", "010-1111-1111",
             "서울 동대문구 왕산로 214", biz_address_detail="1층",
             extra_contacts=[{"role": "실무자", "phone": "010-2000-0001"}],
             equipments=[eq("eq_demo_1a", "포스", "아임유"), eq("eq_demo_1b", "카드단말기", "3103(4200)", van="FD")],
             histories=[
                 history("2026-03-15", "오혜성", "설치", actions=[
                     {"actType": "설치", "newEq": eq("eq_demo_1a", "포스", "아임유"), "oldEq": None},
                     {"actType": "설치", "newEq": eq("eq_demo_1b", "카드단말기", "3103(4200)", van="FD"), "oldEq": None}],
                     auto_content="➕ [설치] 포스 (아임유) - 신품\n➕ [설치] 카드단말기 (3103(4200)) - 신품"),
                 history("", "오혜성", "방문AS", content="영수증 출력 안 됨. 전화 안내 후에도 동일", status="예정"),
             ]),
    merchant("[데모] 소담카페", "000-00-00002", "이데모", "010-2000-0002",
             "서울 마포구 양화로 160", store_phone="02-123-4567",
             program_list=["포스피드"],
             # 010-1111-1111은 1번 가맹점 대표자이면서 이 가맹점의 실무자 → 전화 수신 시 두 곳이 함께 뜬다
             extra_contacts=[{"role": "실무자", "phone": "010-1111-1111"}],
             equipments=[eq("eq_demo_2a", "키오스크", "하나시스"), eq("eq_demo_2b", "카드단말기", "7503", van="코밴")],
             van_list=["코밴"],
             histories=[history("2026-04-02", "직원1", "신규 가맹", content="신규 카드가맹, 키오스크 1대")]),
    merchant("[데모] 푸른분식", "000-00-00003", "박데모", "010-2000-0003",
             "서울 종로구 세종대로 175", rental_fee_type="무상", rental_fee_amount="", paper_type="무상",
             additional_addresses=[{"type": "실제 주소", "type_other": "", "main": "서울 종로구 종로 1",
                                    "detail": "지하 1층", "memo": "사업자 주소와 실제 매장 위치가 다름"}],
             equipments=[eq("eq_demo_3a", "포스", "아펙사", cond="중고")],
             histories=[history("", "", "원격AS", content="네트워크 오류 반복 문의", status="예정")]),
    merchant("[데모] 바다횟집 판교점", "000-00-00004", "최데모", "010-2000-0004",
             "경기 성남시 분당구 판교역로 166", biz_type="법인",
             van_list=["FD", "금결"],
             equipments=[eq("eq_demo_4a", "포스", "아임유"), eq("eq_demo_4b", "카드단말기", "3103(4200)", van="FD"),
                         eq("eq_demo_4c", "프린터", "", qty="2")],
             histories=[history("2026-04-08", "오혜성", "방문AS", content="터치 불량. 액정 세척 후 재부팅으로 해결")]),
    merchant("[데모] 한강국밥", "000-00-00005", "정데모", "010-2000-0005",
             "서울 송파구 올림픽로 300", program_list=["유니온"],
             equipments=[eq("eq_demo_5a", "포스", "아임유"), eq("eq_demo_5b", "카드단말기", "1902", van="FD")],
             histories=[history("", "오혜성", "교체", content="카드단말기 노후, 교체 예정", status="예정")]),
]

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
# 표 만들기 (app.py의 init_db와 같은 구조)
c.execute("""CREATE TABLE IF NOT EXISTS merchants (
    id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, biz_no TEXT, owner_name TEXT,
    phone TEXT, biz_address TEXT, full_data TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)""")

# 데모 계정 (이미 있으면 그대로 둔다)
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
          ("demo", generate_password_hash("demo1234"), "admin"))

# 가맹점 (비어 있을 때만 넣는다)
count = c.execute("SELECT COUNT(*) FROM merchants").fetchone()[0]
if count == 0:
    for m in MERCHANTS:
        c.execute("INSERT INTO merchants (store_name, biz_no, owner_name, phone, biz_address, full_data) VALUES (?, ?, ?, ?, ?, '')",
                  (m["store_name"], m["biz_no"], m["owner_name"], m["owner_phone"], m["biz_address"]))
        m["id"] = str(c.lastrowid)  # 앱은 full_data 안에도 id가 있어야 수정·저장이 된다
        c.execute("UPDATE merchants SET full_data = ? WHERE id = ?", (json.dumps(m, ensure_ascii=False), c.lastrowid))
    print(f"가맹점 {len(MERCHANTS)}곳을 넣었습니다.")
else:
    print(f"이미 가맹점이 {count}곳 있어서 가맹점은 넣지 않았습니다.")

conn.commit()
conn.close()
print("데모 계정: demo / demo1234")

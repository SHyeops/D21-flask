# Flask 도구 상자에서 Flask(웹 서버 틀), render_template(HTML 파일에 값을 채워 보내는 도구),
# request(손님 주문서 — 주소 뒤 ?category= 같은 값을 읽는 도구),
# abort(주문을 멈추고 상태 코드를 돌려주는 도구), jsonify(파이썬 값을 JSON 포장으로 바꾸는 도구)를 꺼내 옵니다.
# flash(한 번만 보일 안내), redirect(다른 주소로 다시 가게 하기), url_for(함수 이름으로 주소 만들기)도 꺼내 옵니다.
# session(이 브라우저 손님을 기억하는 잠긴 메모장)도 꺼내 옵니다.
# os(컴퓨터의 환경 변수를 읽는 도구)와, .env 파일을 환경 변수로 읽어 들이는 도구를 꺼내 옵니다.
import os
from dotenv import load_dotenv
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
# 데이터 담당 파일(data.py)에서 필요한 함수들을 가져옵니다.
from data import load_classes, categories, filter_and_sort
# 후기 저장 담당 파일(db.py)에서 표 만들기 · 넣기 · 꺼내기 함수를 가져옵니다.
from db import init_db, add_review, get_reviews

# .env 파일이 있으면 그 안의 값을 환경 변수로 올려요. (Render처럼 .env 가 없으면 아무 일도 안 해요)
load_dotenv()

# 우리 식당(웹 서버)을 하나 엽니다. __name__은 "이 파일이 기준"이라는 뜻이에요.
app = Flask(__name__)
# JSON에서 한글이 \uXXXX 같은 암호로 바뀌지 않고 그대로 보이게 합니다.
app.json.ensure_ascii = False
# flash · 세션(찜 목록)을 잠그는 열쇠예요. 코드에 적지 않고 환경 변수(.env 또는 Render 설정)에서 읽어요.
app.secret_key = os.environ.get("SECRET_KEY")
# 열쇠가 없으면 아무나 세션을 위조할 수 있어서, 서버를 켜지 않고 바로 알려 줘요.
if not app.secret_key:
    raise RuntimeError("SECRET_KEY 가 없어요. .env 파일(내 컴퓨터) 또는 Render 환경 변수에 넣어 주세요.")

# 서버가 켜질 때 CSV를 한 번 읽어 둡니다. (주문마다 다시 읽지 않아도 돼요)
CLASSES = load_classes()

# 서버가 켜질 때 후기 표가 있는지 확인하고, 없으면 만듭니다. (reviews.db 파일 — 서버를 꺼도 남아요)
init_db()


# 손님이 주소 "/"(첫 화면)로 주문하면 바로 아래 함수가 담당합니다. (라우트)
@app.route("/")
# 첫 화면 주문을 처리하는 함수(주방 담당자)입니다.
def home():
    # 전체 개수와 카테고리 목록을 홈 화면에 채워 보냅니다. (응답)
    return render_template("home.html", total=len(CLASSES), cats=categories(CLASSES))


# 손님이 주소 "/about"으로 주문하면 바로 아래 함수가 담당합니다.
@app.route("/about")
# 서비스 소개 주문을 처리하는 함수입니다.
def about():
    # templates/about.html 화면을 보냅니다.
    return render_template("about.html")


# <name> 자리에 손님이 쓴 글자가 무엇이든 받아서 name이라는 이름으로 넘겨줍니다.
@app.route("/hello/<name>")
# 받은 이름(name)으로 인사 화면을 만드는 함수입니다.
def hello(name):
    # hello.html의 {{ name }} 구멍에 받은 이름을 채워 보냅니다. 템플릿이 위험한 글자를 알아서 막아 줘요.
    return render_template("hello.html", name=name)


# 손님이 주소 "/classes"로 주문하면 바로 아래 함수가 담당합니다.
@app.route("/classes")
# 클래스 목록을 보여 주는 함수입니다.
def class_list():
    # 주소 뒤 ?category= 값을 읽습니다. 없으면 빈 글자("")가 돼요.
    category = request.args.get("category", "")
    # 주소 뒤 ?sort= 값을 읽습니다. (price 또는 rating)
    sort = request.args.get("sort", "")
    # 조건에 맞게 거르고 정렬한 목록을 만듭니다.
    items = filter_and_sort(CLASSES, category, sort)
    # 목록 화면에 결과와, 고르는 상자에 필요한 값들을 채워 보냅니다.
    return render_template(
        "classes.html",
        items=items,
        cats=categories(CLASSES),
        category=category,
        sort=sort,
    )


# <int:class_id>는 "숫자만 받아요"라는 뜻. /class/abc 처럼 글자가 오면 Flask가 알아서 404를 줘요.
# methods: 보기(GET, 엽서)와 후기 남기기(POST, 봉투)를 같은 주소에서 받아요.
@app.route("/class/<int:class_id>", methods=["GET", "POST"])
# 클래스 하나의 상세 화면을 보여 주는 함수입니다.
def class_detail(class_id):
    # 목록에서 번호가 같은 클래스를 찾습니다. 없으면 None이 돼요.
    c = next((c for c in CLASSES if c["id"] == class_id), None)
    # 못 찾았으면 화면만이 아니라 진짜 상태 코드 404로 멈춥니다.
    if c is None:
        abort(404)
    # 봉투(POST)로 왔다면 = 손님이 '저장' 버튼을 눌렀다면
    if request.method == "POST":
        # 봉투 안의 값 3개를 꺼내 DB 표에 한 줄로 넣어요. (검증은 4번 단계에서)
        add_review(
            class_id,                                  # 어느 클래스의 후기인지
            request.form.get("nickname", ""),          # 닉네임 칸
            request.form.get("star", ""),              # 별점 칸
            request.form.get("content", ""),           # 후기 내용 칸
        )
        # 다음 화면에 딱 한 번만 보일 안내를 맡겨 둬요.
        flash("후기가 저장됐어요")
        # PRG: 저장(POST) 뒤엔 화면을 바로 그리지 않고 같은 주소로 다시 오게(302) 해요.
        # 그러면 마지막 요청이 '보기(GET)'가 되어, F5를 눌러도 저장이 반복되지 않아요.
        # (검증 실패 때는 4번 단계에서 redirect 없이 입력값을 남긴 채 400으로 보여 줄 거예요)
        return redirect(url_for("class_detail", class_id=class_id))
    # DB에서 이 클래스의 후기를 최신순으로 꺼내요.
    reviews = get_reviews(class_id)
    # 이 클래스가 내 찜 목록(세션)에 들어 있는지 확인해요. 버튼 글자를 ♡/♥ 중 무엇으로 할지 정하려고요.
    wished = class_id in session.get("wish", [])
    # 상세 화면에 클래스와 후기 목록, 찜 여부를 채워 보냅니다.
    return render_template("class.html", c=c, reviews=reviews, wished=wished)


# 찜하기/찜 취소 — 값을 바꾸는 일이라 봉투(POST)로만 받아요.
@app.route("/class/<int:class_id>/wish", methods=["POST"])
def toggle_wish(class_id):
    # 없는 클래스 번호로 찜하려 하면 404로 멈춰요. (F12로 번호를 바꿔 보내는 경우 대비)
    if not any(c["id"] == class_id for c in CLASSES):
        abort(404)
    # 세션 메모장에서 찜 목록을 꺼내요. 처음이면 빈 목록이에요.
    wish = session.get("wish", [])
    # 이미 찜했으면 빼고(취소), 아니면 넣어요(찜하기).
    if class_id in wish:
        wish.remove(class_id)
        flash("찜을 취소했어요")
    else:
        wish.append(class_id)
        flash("찜 목록에 담았어요")
    # 바꾼 목록을 다시 세션에 넣어야 브라우저 쿠키에 새로 저장돼요.
    session["wish"] = wish
    # PRG: 다시 상세 화면을 보기(GET)로 보여 줘요.
    return redirect(url_for("class_detail", class_id=class_id))


# 내 찜 목록 화면
@app.route("/wishlist")
def wishlist():
    # 세션의 번호들로 클래스를 찾아요. 찜한 순서대로 보여 줘요.
    ids = session.get("wish", [])
    items = [c for i in ids for c in CLASSES if c["id"] == i]
    return render_template("wishlist.html", items=items)


# ---------- 여기부터 프로그램용 JSON 창구(API) ----------

# 손님이 /api/classes 로 주문하면 전체 목록을 JSON으로 포장해 보냅니다.
@app.route("/api/classes")
def api_classes():
    # 주소 뒤 ?category= 값을 읽습니다. 없으면 전체예요.
    category = request.args.get("category", "")
    # 목록 화면과 같은 함수로 거릅니다. (화면과 API 숫자가 어긋나지 않게)
    items = filter_and_sort(CLASSES, category)
    # 개수와 목록을 함께 JSON으로 보냅니다. 파이썬의 None은 JSON에서 null이 돼요.
    return jsonify({"count": len(items), "items": items})


# 손님이 /api/classes/번호 로 주문하면 그 클래스 하나를 JSON으로 보냅니다.
@app.route("/api/classes/<int:class_id>")
def api_class(class_id):
    # 번호가 같은 클래스를 찾습니다. 없으면 None이에요.
    c = next((c for c in CLASSES if c["id"] == class_id), None)
    # 못 찾으면 JSON 에러 메시지와 함께 진짜 상태 코드 404를 보냅니다.
    if c is None:
        return jsonify({"error": f"{class_id}번 클래스가 없어요"}), 404
    # 찾았으면 그 클래스를 JSON으로 보냅니다.
    return jsonify(c)


# 손님이 /api/stats 로 주문하면 요약 숫자를 JSON으로 보냅니다.
@app.route("/api/stats")
def api_stats():
    # 가격이 있는 것만 모읍니다. (빈칸을 0으로 치면 평균이 낮아져서 빼요)
    prices = [c["price"] for c in CLASSES if c["price"] is not None]
    # 평점이 있는 것만 모읍니다.
    ratings = [c["rating"] for c in CLASSES if c["rating"] is not None]
    # 요약 숫자들을 JSON으로 보냅니다.
    return jsonify({
        "total": len(CLASSES),                                  # 전체 개수
        "avg_price": round(sum(prices) / len(prices)),          # 평균 판매가 (빈칸 빼고, 원 단위 반올림)
        "price_inquiry": len(CLASSES) - len(prices),            # 가격 문의 수 (= 가격 빈칸)
        "avg_rating": round(sum(ratings) / len(ratings), 2),    # 평균 평점 (빈칸 빼고, 소수 둘째 자리)
        "no_review": len(CLASSES) - len(ratings),               # 리뷰 없음 수 (= 평점 빈칸)
        "by_category": dict(categories(CLASSES)),               # 카테고리별 개수
    })


# 어느 주소에서든 404가 나면 이 함수가 대신 응답합니다.
@app.errorhandler(404)
def not_found(error):
    # API 주소(/api/...)였다면 프로그램이 읽을 수 있게 JSON으로 알려 줍니다.
    if request.path.startswith("/api/"):
        return jsonify({"error": "찾는 데이터가 없어요"}), 404
    # 화면 뒤에 붙은 404가 상태 코드예요. 이걸 빼면 상태 코드가 200이 되어 버려요.
    return render_template("404.html"), 404


# 코드에서 예상 못 한 에러가 나면(500) 이 함수가 대신 응답합니다. (debug가 꺼진 배포 환경에서 보여요)
@app.errorhandler(500)
def server_error(error):
    # API 주소였다면 JSON으로 알려 줍니다.
    if request.path.startswith("/api/"):
        return jsonify({"error": "서버에서 문제가 생겼어요. 잠시 뒤 다시 시도해 주세요"}), 500
    # 손님에게는 에러 내용 대신 친절한 화면을, 상태 코드는 진짜 500으로 보내요.
    return render_template("500.html"), 500


# 이 파일을 직접 실행했을 때만 아래 줄이 작동합니다.
if __name__ == "__main__":
    # debug는 환경 변수 FLASK_DEBUG=1 일 때만 켜져요. 내 컴퓨터의 .env 에만 넣고 Render에는 넣지 않아요.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

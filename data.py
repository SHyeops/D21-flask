# 표 모양 데이터를 다루는 도구 판다스를 가져옵니다.
import pandas as pd
# 이 파일이 있는 폴더 위치를 알아내는 도구를 가져옵니다.
from pathlib import Path

# CSV 파일 위치: 이 파일 옆 data 폴더 안의 classes.csv
CSV_PATH = Path(__file__).parent / "data" / "classes.csv"


# 빈칸(NaN)이면 None(값 없음)으로, 아니면 원래 숫자로 바꿔 주는 작은 도우미입니다.
def _value_or_none(x):
    # pd.isna는 "빈칸이야?"를 물어보는 함수예요. 빈칸이면 0이 아니라 None을 돌려줍니다.
    return None if pd.isna(x) else x


# CSV를 읽어서 클래스 하나하나를 사전(dict)으로 담은 목록을 돌려줍니다.
def load_classes():
    # CSV를 읽습니다. utf-8-sig는 파일 맨 앞의 보이지 않는 표시(BOM)를 지워 줘요.
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    # 결과를 담을 빈 목록을 만듭니다.
    classes = []
    # 표의 한 줄(클래스 하나)씩 차례로 꺼냅니다.
    for _, row in df.iterrows():
        # 정가와 할인가를 꺼냅니다. 빈칸이면 None이 됩니다.
        list_price = _value_or_none(row["정가"])
        sale = _value_or_none(row["할인가"])
        # 판매가 = 할인가가 있으면 할인가, 없으면 정가 (둘 다 없으면 None = 가격 문의)
        price = sale if sale is not None else list_price
        # 화면에서 쓰기 편한 이름으로 한 클래스를 정리해 목록에 넣습니다.
        classes.append({
            "id": int(row["id"]),
            "category": row["카테고리"],
            "region": row["지역"],
            "name": row["클래스명"],
            "list_price": list_price,          # 정가 (취소선용)
            "price": price,                    # 판매가 (실제로 내는 돈)
            "on_sale": sale is not None,       # 할인 중이면 True
            "rating": _value_or_none(row["평점"]),
            "reviews": int(row["리뷰수"]),
        })
    # 다 모은 목록을 돌려줍니다.
    return classes


# 카테고리 이름을 클래스가 많은 순서대로 돌려줍니다. (홈 버튼 · 고르는 상자용)
def categories(classes):
    # 카테고리별 개수를 셉니다.
    counts = {}
    for c in classes:
        counts[c["category"]] = counts.get(c["category"], 0) + 1
    # 개수가 많은 순으로 (이름, 개수) 짝을 정렬해 돌려줍니다.
    return sorted(counts.items(), key=lambda kv: -kv[1])


# 카테고리로 거르고, 원하는 순서로 정렬한 목록을 돌려줍니다.
def filter_and_sort(classes, category=None, sort=None):
    # 카테고리를 골랐으면 그 카테고리만 남깁니다.
    if category:
        classes = [c for c in classes if c["category"] == category]
    # 싼 순: 가격이 없는 클래스(가격 문의)는 (1, 0)이 되어 맨 뒤로 갑니다.
    if sort == "price":
        classes = sorted(classes, key=lambda c: (c["price"] is None, c["price"] or 0))
    # 평점 높은 순: 평점이 없는 클래스(리뷰 없음)는 맨 뒤로 갑니다.
    elif sort == "rating":
        classes = sorted(classes, key=lambda c: (c["rating"] is None, -(c["rating"] or 0)))
    # 리뷰 많은 순: 리뷰 수가 큰 클래스가 앞으로 옵니다.
    elif sort == "review":
        classes = sorted(classes, key=lambda c: -c["reviews"])
    # 정리된 목록을 돌려줍니다.
    return classes

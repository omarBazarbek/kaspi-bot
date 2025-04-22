import requests

def get_kaspi_reviews(product_id: str):
    url = f"https://kaspi.kz/yml/review-view/api/v1/reviews/product/{product_id}?baseProductCode&orderCode&filter=COMMENT&sort=POPULARITY&limit=9&withAgg=true"

    headers = {
        "Accept": "application/json, text/*",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15",
        "Referer": f"https://kaspi.kz/shop/p/art-111-{product_id}/?c=750000000",
        "X-KS-City": "750000000",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", {})
            rating_data = summary.get("statistic", [])
            rating_summary = {d['rate']: d['count'] for d in rating_data}
            total_reviews = sum(rating_summary.values())
            comment_count = data.get("groupSummary", [{}])[0].get("total", 0)

            print(f"📊 Рейтинг по звёздам: {rating_summary}")
            print(f"⭐ Всего оценок: {total_reviews}")
            print(f"💬 Текстовых отзывов: {comment_count}")
        else:
            print(f"❌ Ошибка {response.status_code}: не удалось получить отзывы")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")

# Пример вызова:
get_kaspi_reviews("102298404")

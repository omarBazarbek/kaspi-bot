import re
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from estimator import estimate_sales  



def extract_product_id(url):
    match = re.search(r'/p/[^/]+-(\d+)', url)
    return match.group(1) if match else None

def parse_kaspi_product(url):
    product_id = extract_product_id(url)
    if not product_id:
        print("❌ Не удалось извлечь product_id из URL")
        return None

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    try:
        wait = WebDriverWait(driver, 10)

        title = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item__heading"))).text.strip()
        price_text = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item__price-once"))).text.strip()
        price = int(re.sub(r"[^\d]", "", price_text))


        rating_summary = {}
        comment_count = 0
        total_reviews = 0

        try:
            api_url = f"https://kaspi.kz/yml/review-view/api/v1/reviews/product/{product_id}?baseProductCode&orderCode&filter=COMMENT&sort=POPULARITY&limit=9&withAgg=true"
            headers = {
                "Accept": "application/json, text/*",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15",
                "Referer": url,
                "X-KS-City": "750000000",
            }

            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                rating_data = summary.get("statistic", [])
                rating_summary = {d['rate']: d['count'] for d in rating_data}
                total_reviews = sum(rating_summary.values())


                comment_count = next((item['total'] for item in data.get("groupSummary", []) if item['id'] == 'COMMENT'), 0)
            else:
                print(f"❌ Ошибка {response.status_code}: не удалось получить отзывы")
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")


        try:
            reviews_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@data-tab='reviews']")))
            driver.execute_script("arguments[0].click();", reviews_tab)
            time.sleep(2)
        except:
            pass

        for _ in range(20):
            try:
                more_btn = driver.find_element(By.CLASS_NAME, "reviews__more")
                if more_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(2)
                else:
                    break
            except:
                break

        date_elements = driver.find_elements(By.CLASS_NAME, "reviews__date")
        review_dates = []
        for el in date_elements:
            try:
                date_str = el.text.strip()
                review_date = datetime.strptime(date_str, "%d.%m.%Y")
                review_dates.append(review_date)
            except:
                continue

        now = datetime.now()
        reviews_today = sum(1 for d in review_dates if d.date() == now.date())
        reviews_week = sum(1 for d in review_dates if now - timedelta(days=7) <= d <= now)
        reviews_month = sum(1 for d in review_dates if now - timedelta(days=30) <= d <= now)

       

        print(f"📦 Название товара: {title}")
        print(f"🔢 ID товара: {product_id}")
        print(f"💰 Цена: {price} ₸")
        print(f"⭐ Всего оценок: {total_reviews}")
        print(f"💬 Текстовых отзывов: {comment_count}")
        print("📊 Рейтинг по звёздам:")
        for rate in sorted(rating_summary.keys(), reverse=True):
            print(f"  {rate}★ — {rating_summary[rate]} шт.")

        print("\n📅 Отзывы по датам:")
        print(f"  Сегодня: {reviews_today}")
        print(f"  За неделю: {reviews_week}")
        print(f"  За месяц: {reviews_month}")

     

        sales_analysis = estimate_sales({
            "all_reviews": total_reviews,
            "text_reviews": comment_count,
            "price": price,
            "text_reviews_today": reviews_today,
            "text_reviews_week": reviews_week,
            "text_reviews_month": reviews_month,
            "review_dates": review_dates
        })
      
        if sales_analysis:
            print("\n📦 Результат анализа продаж:")
            print(f"  ~ Продажи всего: {sales_analysis['sales_estimate']} шт.")
            print(f"  ~ Выручка за все время: {sales_analysis['revenue_estimate']} ₸")

            print(f"\n📈 Примерные продажи:")
            print(f"  • В день: {sales_analysis['avg_sales_today']} шт. ({sales_analysis['daily_range'][0]}–{sales_analysis['daily_range'][1]} шт.)")
            print(f"  • За неделю: {sales_analysis['avg_sales_week']} шт. ({sales_analysis['weekly_range'][0]}–{sales_analysis['weekly_range'][1]} шт.)")
            print(f"  • За месяц: {sales_analysis['avg_sales_month']} шт. ({sales_analysis['monthly_range'][0]}–{sales_analysis['monthly_range'][1]} шт.)")

            print(f"\n💰 Выручка за месяц: {sales_analysis['avg_sales_month'] * price} ₸")
            print(f"\n📌 Статус активности: {sales_analysis['status']}")
            print(f"🕒 Последний отзыв: {sales_analysis['last_review_date']}")
            print(f"{sales_analysis['confidence']}")


        return {
            "product_id": product_id,
            "title": title,
            "price": price,
            "ratings": rating_summary,
            "text_reviews": comment_count,
            "review_dates": review_dates,
            "reviews_today": reviews_today,
            "reviews_week": reviews_week,
            "reviews_month": reviews_month,
            "sales_analysis": sales_analysis  
        }


    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")
        return None
    finally:
        driver.quit()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re

def debug_price_extraction():
    """بررسی دقیق استخراج قیمت از یک آگهی نمونه"""
    
    # تنظیمات Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # رفتن به صفحه اصلی دیوار
        driver.get('https://divar.ir/s/tehran/car')
        time.sleep(3)
        
        # پیدا کردن اولین آگهی
        ad_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/v/"]')
        if ad_links:
            first_ad_url = ad_links[0].get_attribute('href')
            print(f"رفتن به آگهی: {first_ad_url}")
            
            # رفتن به صفحه آگهی
            driver.get(first_ad_url)
            time.sleep(5)
            
            print("\n=== بررسی محتوای صفحه ===")
            
            # 1. بررسی کل متن صفحه
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            print(f"طول کل متن صفحه: {len(page_text)} کاراکتر")
            
            # جستجو برای کلمات مرتبط با قیمت
            price_keywords = ['قیمت', 'میلیون', 'هزار', 'تومان']
            for keyword in price_keywords:
                if keyword in page_text:
                    print(f"✅ کلمه '{keyword}' در صفحه یافت شد")
                    # نمایش متن اطراف کلمه
                    index = page_text.find(keyword)
                    start = max(0, index - 50)
                    end = min(len(page_text), index + 50)
                    context = page_text[start:end].replace('\n', ' ')
                    print(f"   متن اطراف: ...{context}...")
                else:
                    print(f"❌ کلمه '{keyword}' در صفحه یافت نشد")
            
            # 2. جستجو با الگوهای regex
            print("\n=== جستجو با الگوهای regex ===")
            price_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*میلیون',
                r'(\d{1,3}(?:,\d{3})*)\s*هزار',
                r'(\d{6,})\s*تومان',
                r'قیمت[:\s]*(\d+)',
                r'(\d{1,3}(?:,\d{3})*)',  # هر عدد با کاما
            ]
            
            for i, pattern in enumerate(price_patterns):
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    print(f"الگو {i+1}: {len(matches)} مورد یافت شد")
                    print(f"   نمونه‌ها: {matches[:5]}")
                else:
                    print(f"الگو {i+1}: هیچ موردی یافت نشد")
            
            # 3. بررسی HTML source
            print("\n=== بررسی HTML source ===")
            page_source = driver.page_source
            print(f"طول HTML source: {len(page_source)} کاراکتر")
            
            # جستجو در HTML
            html_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*(?:میلیون|هزار|تومان)', page_source, re.IGNORECASE)
            if html_matches:
                print(f"در HTML {len(html_matches)} مورد یافت شد: {html_matches[:5]}")
            else:
                print("در HTML هیچ قیمتی یافت نشد")
            
            # 4. ذخیره HTML برای بررسی دستی
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("\n💾 HTML صفحه در debug_page_source.html ذخیره شد")
            
        else:
            print("هیچ آگهی‌ای یافت نشد")
            
    except Exception as e:
        print(f"خطا: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_price_extraction()
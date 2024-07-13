import requests
from bs4 import BeautifulSoup
import pandas as pd
"""
이 스크립트는 루마 사이트의 프로모션 페이지를 크롤링하여 데이터를 수집합니다.
수집된 데이터는 CSV 파일로 저장됩니다.
"""

BASE_URL = "http://llumar.co.kr/sub_bbs/bbs_list.php?curr_page={}&bcode=11&list_count=1&sch_option=&sch_str="

promotion_data = []

page_number = 1
while True:
    url = BASE_URL.format(page_number)
    response = requests.get(url)
    response.encoding = 'euc-kr'
    soup = BeautifulSoup(response.text, 'html.parser')


    rows = soup.select('table > tbody > tr')
    valid_data_found = False

    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 4:
            promo_no = cols[0].text.strip()
            title_tag = cols[1].find('a')
            title_text = title_tag.text.strip()
            title_link = title_tag['href']
            date = cols[2].text.strip()
            views = cols[3].text.strip()

            full_url = f"http://www.llumar.co.kr/sub_bbs/{title_link}"
            detail_response = requests.get(full_url)
            detail_response.encoding = 'euc-kr'
            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
            content_div = detail_soup.find('div', class_='bbs_view')
            if content_div:
                content = ' '.join(content_div.stripped_strings)
            else:
                content = None  # 본문 내용이 없으면 None 할당

            promotion_data.append([promo_no, title_text, date, views, content])
            valid_data_found = True

    if not valid_data_found:
        break

    next_page_number = page_number + 1
    next_page_link = soup.find('a', href=lambda href: href and f'curr_page={next_page_number}' in href)
    if not next_page_link:
        break

    page_number += 1


promotion_df = pd.DataFrame(promotion_data, columns=['No', '제목', '작성일', '조회', '본문'])
promotion_df.to_csv("~/CRAWLER_LLUMAR/result_promotion_scraping_results.csv", index=False, encoding='utf-8-sig')
print("Data saved to promotion_scraping_results.csv")
print(promotion_df.head())

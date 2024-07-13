import requests
from bs4 import BeautifulSoup
import pandas as pd
"""
이 스크립트는 루마 사이트의 FAQ 페이지를 크롤링하여 데이터를 수집합니다.
수집된 데이터는 CSV 파일로 저장됩니다.
"""

BASE_URL = "http://llumar.co.kr/sub_support/faq.php?curr_page={}&list_count=20&sch_str=&sch_cate="

faq_data = []

page_number = 1
while True:
    url = BASE_URL.format(page_number)
    response = requests.get(url)
    
    if response.status_code == 200:  # 페이지가 존재하는 경우
        response.encoding = 'euc-kr'  # 한글 깨짐 방지
        soup = BeautifulSoup(response.text, 'html.parser')

        rows = soup.select('tr')

        valid_data_found = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 4:
                faq_no = cols[0].text.strip()
                importance = cols[1].text.strip()
                question_field = cols[2].text.strip()
                question_tag = cols[3].find('a')
                question_text = question_tag.text.strip()
                question_link = question_tag['href']
                
                full_url = f"http://llumar.co.kr/sub_support/{question_link}"
                detail_response = requests.get(full_url)
                detail_response.encoding = 'euc-kr'
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                content_div = detail_soup.find('div', class_='tx-content-container')
                if content_div:
                    content = ' '.join(content_div.stripped_strings)
                else:
                    content = None
                    
                faq_data.append([faq_no, importance, question_field, question_text, content])
                valid_data_found = True

        if not valid_data_found:
            break

        next_page_number = page_number + 1
        next_page_link = soup.find('a', href=lambda href: href and f'curr_page={next_page_number}' in href)
        if not next_page_link:
            break

        page_number += 1


faq_df = pd.DataFrame(faq_data, columns=['No', '중요도', '질문분야', '질문', '본문'])
faq_df.to_csv("~/CRAWLER_LLUMAR/result_faq_scraping_results.csv", index=False, encoding='utf-8-sig')
print("Data saved to faq_scraping_results.csv")
print(faq_df)

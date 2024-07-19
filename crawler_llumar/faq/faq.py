import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

BASE_URL = "http://llumar.co.kr/sub_support/faq.php?curr_page={}&list_count=20&sch_str=&sch_cate="
state_file = "faq/faq_state.txt"
output_file = "result_faq_scraping_results.csv"

# 상태 파일에서 현재 페이지 번호를 읽어들임
try:
    with open(state_file, 'r') as file:
        page_number = int(file.read().strip())
except FileNotFoundError:
    page_number = 1

# 이미 존재하는 데이터 읽기
try:
    existing_data = pd.read_csv(output_file)
    faq_data = existing_data.values.tolist()
except FileNotFoundError:
    faq_data = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

try:
    while True:
        url = BASE_URL.format(page_number)
        print(f"Requesting URL: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print(f"Status Code: {response.status_code}")
            response.encoding = 'euc-kr'
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

                    # 공지사항(NOTICE) 제외
                    if page_number > 1 and "NOTICE" in faq_no.upper():
                        print(f"Skipping NOTICE on page {page_number}: {faq_no}")
                        continue
                    
                    full_url = f"http://llumar.co.kr/sub_support/{question_link}"
                    print(f"Requesting detail URL: {full_url}")
                    detail_response = requests.get(full_url, headers=headers)
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
                print("No valid data found, exiting.")
                break

            next_page_number = page_number + 1
            next_page_link = soup.find('a', href=lambda href: href and f'curr_page={next_page_number}' in href)
            if not next_page_link:
                print("No next page link found, exiting.")
                break

            page_number += 1

            # 현재 페이지 번호를 상태 파일에 저장
            with open(state_file, 'w') as file:
                file.write(str(page_number))

            # 중간 저장
            faq_df = pd.DataFrame(faq_data, columns=['No', '중요도', '질문분야', '질문', '본문'])
            faq_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Data saved to {output_file}")

        else:
            print(f"Error: Received status code {response.status_code}")
            break

except KeyboardInterrupt:
    print("Crawling paused. Current progress saved.")
    sys.exit(0)

finally:
    # 최종 저장
    faq_df = pd.DataFrame(faq_data, columns=['No', '중요도', '질문분야', '질문', '본문'])
    faq_df.to_csv(output_file, index=False, encoding='utf-8-sig')
   
    # 크롤링이 완료된 후 상태 파일 삭제
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"State file {state_file} has been removed.")
    else:
        print(f"State file {state_file} does not exist.")

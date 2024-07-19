import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys

BASE_URL = "http://www.llumar.co.kr/sub_bbs/bbs_list.php?curr_page={}&bcode=9&list_count=20&sch_option=&sch_str="
state_file = "whatsnew/whatsnew_state.txt"
output_file = "~/CRAWLER_LLUMAR/result_whatsnew_scraping_results.csv"

# 상태 파일에서 현재 페이지 번호를 읽어들임
try:
    with open(state_file, 'r') as file:
        page_number = int(file.read().strip())
except FileNotFoundError:
    page_number = 1

# 이미 존재하는 데이터 읽기
try:
    existing_data = pd.read_csv(output_file)
    whatsnew_data = existing_data.values.tolist()
except FileNotFoundError:
    whatsnew_data = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

try:
    while True:
        url = BASE_URL.format(page_number)
        print(f"Requesting URL: {url}")
        response = requests.get(url, headers=headers)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')

        rows = soup.select('table > tbody > tr')
        valid_data_found = False

        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 4:
                news_no = cols[0].text.strip()
                title_tag = cols[1].find('a')
                title_text = title_tag.text.strip()
                title_link = title_tag['href']
                date = cols[2].text.strip()
                views = cols[3].text.strip()

                if page_number > 1 and "NOTICE" in news_no.upper():
                    print(f"Skipping NOTICE on page {page_number}: {news_no}")
                    continue
     

                full_url = f"http://www.llumar.co.kr/sub_bbs/{title_link}"
                print(f"Requesting detail URL: {full_url}")
                detail_response = requests.get(full_url, headers=headers)
                detail_response.encoding = 'euc-kr'
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                content_div = detail_soup.find('div', class_='bbs_view')
                if content_div:
                    content = ' '.join(content_div.stripped_strings)
                    content = content.replace('\n', ' ').replace('\r', ' ')
                else:
                    content = None

                whatsnew_data.append([news_no, title_text, date, views, content])
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
        whatsnew_df = pd.DataFrame(whatsnew_data, columns=['No', '제목', '작성일', '조회', '본문'])
        whatsnew_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Data saved to {output_file}")

except KeyboardInterrupt:
    print("Crawling paused. Current progress saved.")
    sys.exit(0)

finally:
    # 최종 저장
    whatsnew_df = pd.DataFrame(whatsnew_data, columns=['No', '제목', '작성일', '조회', '본문'])
    whatsnew_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # 크롤링이 완료된 후 상태 파일 삭제
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"State file {state_file} has been removed.")
    else:
        print(f"State file {state_file} does not exist.")
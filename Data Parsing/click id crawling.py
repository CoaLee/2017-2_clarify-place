from bs4 import BeautifulSoup
import urllib.request
import sys
import urllib.parse
sys.stdout.buffer.write(chr(9986).encode('utf8'))


INPUT_FILE_NAME = '검색어 리스트.txt'
OUTPUT_FILE_NAME = '각 검색어별(1만 개) 30개의 업체 id(업체로 검색하기 결과).txt'
# 긁어 올 URL : query = '명동칼국수'


def get_text(query, url):
    source_code_from_url = urllib.request.urlopen(url)
    soup = BeautifulSoup(source_code_from_url, 'lxml', from_encoding='utf-8')
    text = query + '\n'
    for item in soup.find_all('a', {"class": "info_area _info_area"}):
        text = text + (str(item['href']))[23:-9] + ' '
    return text


def main():
    open_input_file = open(INPUT_FILE_NAME, 'r', encoding='utf-8')
    open_output_file = open(OUTPUT_FILE_NAME, 'w')
    while True:
        query = open_input_file.readline()
        if len(query) is 0:
            break

        # query = urllib.parse.quote_plus(query)
        url = 'https://m.store.naver.com/restaurants/listMap?level=top&query=' + query + '&queryRank=2'
        result_text = get_text(query, url)
        open_output_file.write(result_text)
        open_output_file.close()


if __name__ == '__main__':
    main()


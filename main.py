from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
import time
import re
import pandas as pd

driver = webdriver.Chrome(executable_path='chromedriver')


def preprocessing(text):  # 필요없는 특수기호 제거 위해 추가
    pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'  # 한글 자음, 모음 제거
    text = re.sub(pattern=pattern, repl='', string=text)
    pattern = '<[^>]*>'  # HTML 태그 제거
    text = re.sub(pattern=pattern, repl='', string=text)
    pattern = '[^\w\s]'  # 특수기호제거
    text = re.sub(pattern=pattern, repl='', string=text)
    return text


def menu():  # 메뉴 크롤링
    success = pd.read_csv('대구광역시_아동급식카드가맹점정보_20221125.csv', names=['가맹점ID', '가맹점명', '주소', '음식점분류', '위도', '경도'],
                          encoding='cp949')
    cat = success['가맹점명']
    store_list = cat.values.tolist()
    cat2 = success['주소']
    address_list = cat2.values.tolist()
    cat3 = success['음식점분류']
    category_num = cat3.values.tolist()

    df = pd.DataFrame(success)
    df = df.drop([0])
    # total = []

    # 공공데이터 주소와 상호명을 하나씩 읽어와서 검색
    for i in range(len(store_list) - 1):
        # info_set = []
        menu = []
        num = 0
        search_find = True
        if category_num[i + 1] != "23":  # 23은 편의점이라서 편의점이 아닌 가게의 메뉴만 검색해서 크롤링
            driver.get("https://map.naver.com/v5/search/" + address_list[i + 1])  # 검색창에 가게 주소 입력
            time.sleep(3)
            driver.implicitly_wait(30)
            print(i + 1)
            re_store = (store_list[i + 1]).replace(" ", "")  # 검색할 가맹점 이름에서 띄어쓰기 제거
            re_store = preprocessing(str(re_store))  # 특수기호들 제거
            parse_store = preprocessing(str(store_list[i + 1]).split()[0])
            search = ""  # 네이버지도에서 최종적으로 찾아 볼 가맹점 상호명 저장

            try:  # 이 주소의 장소 더보기 버튼 있는 경우
                button = driver.find_element(By.CLASS_NAME, 'link_more')  # 이 주소의 장소 더보기 버튼 선택
                driver.implicitly_wait(40)
                button.send_keys(Keys.ENTER)  # 버튼 클릭
                driver.implicitly_wait(40)
                temp = driver.find_element(By.CLASS_NAME, 'place_area')
                driver.implicitly_wait(40)

                # 현재 페이지의 상호명들을 map_store 에 저장하여 찾고자 하는 공공데이터 상호명과 비교
                while search_find:

                    map_store = temp.find_elements(By.CLASS_NAME, 'search_title')  # 주소검색했을때 나오는 가게를 리스트로 저장
                    driver.implicitly_wait(40)

                    for j in range(len(map_store)):
                        print(map_store[j].text, store_list[i + 1])  # 네이버 상호명, 공공데이터 상호명
                        # 공백제거한 상호명끼리 비교해서 같은 이름인 경우
                        if preprocessing(map_store[j].text.replace(" ", "")) == re_store:
                            print('상호명같음1')
                            search = map_store[j].text
                            search_find = False
                            break
                        # 공공데이터 상호명이 네이버 지도 상호명 안에 포함되는 경우
                        elif re_store in preprocessing(map_store[j].text.replace(" ", "")):
                            print('상호명포함1-1')
                            search = map_store[j].text
                            search_find = False
                            break
                        # 네이버 지도 상호명이 공공데이터 상호명 안에 포함되는 경우
                        elif preprocessing(map_store[j].text.replace(" ", "")) in re_store:
                            print('상호명포함1-2')
                            search = map_store[j].text
                            search_find = False
                            break

                    for k in range(len(map_store)):
                        if search == "" and parse_store in preprocessing(map_store[k].text.replace(" ", "")):
                            print('띄어쓰기 기준으로 자른 공공데이터 상호명이 네이버지도 상호명에 포함1')
                            search = map_store[k].text
                            search_find = False
                            break
                    for l in range(len(map_store)):
                        if search == "" and str(preprocessing(map_store[l].text)).split()[0] in re_store:
                            print('띄어쓰기 기준으로 자른 상호명이 공공데이터 상호명에 포함1')
                            search = map_store[l].text
                            search_find = False
                            break

                    # 현재 페이지에서 찾고자 하는 상호명이 없는 경우
                    if search_find and search == "":
                        try:  # 현재 페이지에서 같은 가게 못찾았고 다음 페이지 버튼이 있을 경우 다음 페이지로 넘어감
                            # print("현재 페이지에 없어서 다음 페이지 클릭")

                            # 다음 페이지 넘어가는 버튼이 비활성화 상태이면 찾고자 하는 가게가 없는 것이므로 search에 - 저장
                            html = driver.page_source
                            soup = BeautifulSoup(html, 'html.parser')
                            btn = soup.select('.pagination_area> .btn_next')
                            check = str(btn).split()
                            if check[3] == 'disabled=\"\"' and search_find and search == "":
                                # print("disabled yes")
                                search = "-"
                                search_find = False
                                break

                            next_btn = driver.find_element_by_css_selector("button.btn_next")
                            driver.implicitly_wait(40)
                            next_btn.click()
                            time.sleep(3)

                        except:  # 현재 페이지에서 같은 가게 못찾았고 다음 페이지 버튼도 없는 경우 -> 공공데이터 상호명 넘겨주고 while 문 나가게함
                            # print("현재 페이지에 없고 다음페이지도 없음")
                            search = "-"
                            search_find = False

            except:  # 이 주소의 장소 더보기 버튼 없이 가게 리스트가 바로 나오는 경우 -> 크롤링 태그가 달라서 따로 처리
                while search_find:
                    driver.switch_to.default_content()  # frame 초기화
                    driver.switch_to.frame('searchIframe')  # frame 변경
                    map_store = driver.find_elements(By.CSS_SELECTOR, '.YwYLL')

                    for j in range(len(map_store)):
                        print(map_store[j].text, re_store)
                        # 공백제거한 상호명끼리 비교해서 같은 이름인 경우
                        if preprocessing(map_store[j].text.replace(" ", "")) == re_store:
                            print('상호명같음2')
                            search = map_store[j].text
                            num = j + 1
                            search_find = False
                            break
                        # 공공데이터 상호명이 네이버 지도 상호명 안에 포함되는 경우
                        elif re_store in preprocessing(map_store[j].text.replace(" ", "")):
                            print('상호명포함2-1')
                            search = map_store[j].text
                            num = j + 1
                            search_find = False
                            break
                        # 네이버 지도 상호명이 공공데이터 상호명 안에 포함되는 경우
                        elif preprocessing(map_store[j].text.replace(" ", "")) in re_store:
                            print('상호명포함2-2')
                            search = map_store[j].text
                            num = j + 1
                            search_find = False
                            break

                    for k in range(len(map_store)):
                        if search == "" and parse_store in preprocessing(map_store[k].text.replace(" ", "")):
                            print('띄어쓰기 기준으로 자른 공공데이터 상호명이 네이버지도 상호명에 포함2')
                            search = map_store[k].text
                            num = k + 1
                            search_find = False
                            break

                    for l in range(len(map_store)):
                        if search == "" and str(preprocessing(map_store[l].text)).split()[0] in re_store:
                            print('띄어쓰기 기준으로 자른 상호명이 공공데이터 상호명에 포함2')
                            search = map_store[l].text
                            num = l + 1
                            search_find = False
                            break

                    # 현재 페이지에서 찾고자 하는 상호명이 없는 경우
                    if search_find and search == "":
                        try:  # 현재 페이지에서 같은 가게 못찾았고 다음 페이지 버튼이 있을 경우 다음 페이지로 넘어감
                            # print("현재 페이지에 없어서 다음 페이지 클릭")
                            next_btn = driver.find_elements(By.CSS_SELECTOR, '.zRM9F> a')
                            driver.implicitly_wait(40)

                            # 마지막 페이지인지 확인
                            html = driver.page_source
                            soup = BeautifulSoup(html, 'html.parser')
                            btn = soup.select('.XUrfU> .zRM9F')
                            ck = str(btn).split('<a')

                            # 마지막 페이지이면 search에 - 저장
                            if 'class=\"eUTV2 Y89AQ\"' in ck[-1]:
                                search = "-"
                                search_find = False
                                break
                            if map_store[-1]:  # 마지막 가게일 경우 다음버튼 클릭
                                next_btn[-1].click()
                                time.sleep(2)
                            else:
                                print('페이지 인식 못함')
                                search = "-"
                                search_find = False
                                break

                        except:  # 현재 페이지에서 같은 가게 못찾았고 다음 페이지 버튼도 없는 경우 -> 공공데이터 상호명 넘겨주고 while 문 나가게함
                            # print("현재 페이지에 없고 다음페이지도 없음")
                            search = "-"
                            search_find = False
        else:
            search = "-"

        print('search', search)
        if search != "-":  # 상호명 비교했을때 검색결과가 있는 경우
            try:  # 이 주소의 장소 더보기에서 search를 저장했을때
                if "\'" in search:
                    search = search.split("\'")[0]
                    store = temp.find_element(By.XPATH, f".//*[contains(text(), '{search}')]")
                    driver.implicitly_wait(40)
                else:
                    store = temp.find_element(By.XPATH, f".//*[contains(text(), '{search}')]")
                    driver.implicitly_wait(40)

                store = store.find_element(By.XPATH, "../../..")
                driver.implicitly_wait(40)

                ActionChains(driver).click(store).perform()  # 해당 항목 마우스 클릭

            except:  # 이 주소의 장소 더보기가 없는 가게 리스트에서 search를 저장했을때
                store = driver.find_element(By.CSS_SELECTOR, f"li:nth-child({num}) > div.qbGlu > div > "
                                                             f"a:nth-child(1) > div > div > .YwYLL")
                ActionChains(driver).click(store).perform()

            # iframe으로 이동
            driver.switch_to.default_content()  # frame이 이상하게 넘어가는 경우 방지를 위해 원래 frame으로 변경한 후에 이동
            driver.switch_to.frame('entryIframe')  # 메뉴정보가 entryIframe에 있기 때문에 frame 변경함
            driver.implicitly_wait(3)

            try:
                store_name = driver.find_element(By.CLASS_NAME, 'Fc1rA')  # 네이버 지도 상호명
                store_address = driver.find_element(By.CLASS_NAME, 'LDgIH')  # 네이버 지도 주소
                store_category = driver.find_element(By.CLASS_NAME, 'DJJvD')  # 네이버 지도 가게의 카테고리

                # info_set.append(store_name.text)
                # info_set.append(store_address.text)
                # info_set.append(store_category.text)
                df.loc[i + 1, '네이버지도_상호명'] = store_name.text
                df.loc[i + 1, '네이버지도_주소'] = store_address.text
                df.loc[i + 1, '네이버지도_카테고리'] = store_category.text

                start = driver.find_elements(By.CLASS_NAME, 'Ozh8q')  # 배달의 민족에서 제공하는 메뉴가 랜더링 되어 있는 경우
                driver.implicitly_wait(20)
                for k in start:
                    menu_name = k.find_element(By.CLASS_NAME, 'MENyI')
                    price = k.find_element(By.CLASS_NAME, 'gl2cc')
                    menu.append(f"{menu_name.text} {price.text}")
                if len(start) == 0:  # 가게에서 직접 제공하는 메뉴가 랜더링 되어 있는 경우
                    start = driver.find_elements(By.CLASS_NAME, 'gHmZ_')
                    driver.implicitly_wait(20)
                    for e in start:
                        menu_name = e.find_element(By.TAG_NAME, 'a')
                        price = e.find_element(By.CLASS_NAME, 'awlpp')
                        menu.append(f"{menu_name.text} {price.text}")
                if len(start) == 0:  # 메뉴가 없는 경우
                    print('메뉴X')

            except:
                store_name = 'X'
                store_address = 'X'
                store_category = 'X'
                # info_set.append(store_name)
                # info_set.append(store_address)
                # info_set.append(store_category)
                df.loc[i + 1, '네이버지도_상호명'] = store_name
                df.loc[i + 1, '네이버지도_주소'] = store_address
                df.loc[i + 1, '네이버지도_카테고리'] = store_category

        else:  # 상호명 비교시 검색결과가 없는 경우
            store_name = 'X'
            store_address = 'X'
            store_category = 'X'
            # info_set.append(store_name)
            # info_set.append(store_address)
            # info_set.append(store_category)
            df.loc[i + 1, '네이버지도_상호명'] = store_name
            df.loc[i + 1, '네이버지도_주소'] = store_address
            df.loc[i + 1, '네이버지도_카테고리'] = store_category

        # info_set.append(menu)
        # total.append(info_set)
        df.loc[i + 1, '네이버지도_메뉴'] = str(menu)

        df.to_csv("대구광역시_아동급식가맹점_데이터크롤링.csv")
    # print(total)
    # nv_name = []
    # nv_address = []
    # # nv_category = []
    # nv_menu = []
    #
    # for i in range(len(total)):
    #     nv_name.append(total[i][0])
    #     nv_address.append(total[i][1])
    #     # nv_category.append(total[i][2])
    #     nv_menu.append(total[i][2])
    #
    # df['네이버지도_가게이름'] = nv_name
    # df['네이버지도_주소'] = nv_address
    # # df['네이버지도_카테고리'] = nv_category
    # df['네이버_음식메뉴'] = nv_menu
    # df.to_csv("ex.csv")
    driver.quit()


if __name__ == "__main__":
    menu()
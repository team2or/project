#corpus_insert() 필요 라이브러리
import pymysql #python 이용 데이터베이스 연동
import json #json 파일 load
import pandas as pd #json -> DataFrame 변경
import re #데이터 전처리 이용

#ner_insert() 필요 라이브러리
import requests
import sys

# function description
# 수집 말뭉치(JSON) 데이터베이스 저장 함수
# 작성자: 이재은
# file_route: 파일경로 입력
def corpus_insert(file_route):
    try:
        #데이터베이스 연동
        #192.168.30.1 192.168.0.124
        conn = pymysql.connect(host='192.168.0.124', port=3306, user='LEEJAEEUN', password='1234!@#$', db='kakao_bank', charset='utf8')
        cursor = conn.cursor()
        try:
            #json 파일 불러오기
            with open(file_route, 'r') as f:
                f = json.load(f)
            #json -> 데이터프레임으로 변경
            df = pd.DataFrame(f)
        except FileNotFoundError:
            print("파일경로를 찾을 수 없습니다.")
        except ValueError:
            print("str타입으로 경로를 입력해주세요.")
        except:
            print("정보를 제대로 입력해주세요.")
        else:
            #데이터 전처리
            no = 1 #고유번호 생성에 필요한 게시글 넘버링
            for i in range(1, len(df['text'])):
            # for i in range(30, 50):
                user_id = df['id'][i] #인스타그램 게시자
                date = df['date'][i].replace('T', ' ') #게시날짜

                #게시내용/ 영어,숫자,한글 제외 제거
                text = str(re.compile(r'[^A-Za-z0-9가-힣]').sub(' ', df['text'][i][0]))
                #공백 여러개 1개로 변경
                text = re.sub(' +', ' ', text)

                #해시태그
                hashtags = []
                hashtags.clear()
                for j in df['hashtag'][i]:
                    #영어,숫자,한글 제외 제거
                    tag = re.compile(r'[^A-Za-z0-9가-힣]').sub('', j)
                    #공백 여러개 1개로 변경
                    tag = re.sub(' +', '', tag)
                    if len(tag) > 1:
                        hashtags.append(tag)
                df['hashtag'][i] = hashtags
                #리스트 -> 문자열로 변경
                #mysql은 리스트 저장을 지원하지 않아 문자열로 변환
                hashtag = ' '.join(df['hashtag'][i])
                #해시태그 정보 없으면 0으로 값 입력
                if hashtag == '':
                    hashtag = 0

                #좋아요수
                try:
                    #숫자만 추출
                    likes = int(re.compile(r'[^0-9]').sub('', df['like'][i]))
                except:
                    #정보 없을시 0으로 값 입력
                    likes = 0

                #입력되는 데이터 예시 출력
                print(f"'{no}', '{user_id}', '{date}', '{text}','{hashtag}','{likes}'")
                
                #게시내용 길이가 1글자 이하이거나 비어있을 시 저장하지 않음.
                if len(text) < 1 or text == ' ' or hashtag == ' ':
                    pass
                else:
                    #데이터베이스에 전처리한 데이터 삽입
                    #데이터베이트 필드명
                    #id: 출구별 게시글 수 넘버링 / user_id: 인스타그램 게시아이디 / dates: 게시날짜 / texts: 게시내용
                    #hashtag: 게시내용 중 #붙여진 단어 / likes: 게시글 좋아요 or 조회수 수
                    cursor.execute(f"INSERT INTO corpus (id, user_id, dates, texts, hashtag, likes) VALUES ('4-{str(no).zfill(5)}', '{user_id}', '{date}', '{text}','{hashtag}','{likes}')")
                    no += 1

            #데이터베이스에 commit하기
            conn.commit()
    except:
        # db 연동 error 처리
        print('db 연동 error')
        conn.rollback() # db 반영 취소
    finally:
        # closing database connection.
        cursor.close()
        conn.close()
        print("connection is closed")

# 수집 말뭉치(JSON) 데이터베이스 저장함수 호출
# file_route: 파일경로 입력
corpus_insert("C:/Users/user/혜화역3번출구.json")


# 버터블럭 ner 개체명 추출 결과 데이터베이스 저장 함수
# 작성자: 이재은
def ner_insert():
    try:
        #데이터베이스 연동
        conn = pymysql.connect(host='192.168.0.124', port=3306, user='team2', password='1234', db='test', charset='utf8')
        cursor = conn.cursor()
        
        # 수집 말뭉치 데이터 corpus테이블에서 불러오기
        cursor.execute("SELECT id, user_id, hashtag FROM corpus")
        # 불러온 데이터 fetchall()로 모두 rows 변수에 저장하기
        rows = cursor.fetchall()
        # for문(반복문)을 통해 hashtag를 ner에 적용시켜 개체명 추출하기
        for i in rows:
            # 데이터 ner 입력 포맷으로 변경(JSON)
            texts = {"texts" : [f"{i[2]}"]}
            # ner에 데이터 post하기
            response = requests.post("http://192.168.0.124:1111/ner", json=texts)
            # 결과 json형태로 변수에 저장
            response_text = json.loads(response.text)
            print(response_text[0])
            #결과가 있을 경우 불용어 처리하기
            if len(response_text[0]) > 0:
                #해시태그 불용어 단어리스트
                stopWord = ["대학", "성신", "성균", "혜화", "종로", "동대문", "성대", "배우", "도시락", "카톡", "동숭동",\
                            "아이돌", "방통대", "그램", "서울", "배달", "이화동", "포항", "오빠", "작가", "마스터", "편집자", "아이패드"]
                #게시글별 모든 해시태그 for문으로 불용어 찾기
                for j in range(len(response_text[0])):
                    stopW = [word not in response_text[0][j][1] for word in stopWord]
                    #불용어 단어리스트에 해당 할 경우 결과저장 안함.
                    if False in stopW:
                        stop = False
                    #불용어 단어리스트에 해당하지 않을 경우. 아래 if문에서 정제.
                    else:
                        stop = True
                    # 개체명 태그 중 ["시간","날짜","수량","인물"]이 아닌 해시태그 데이터베이스에 insert
                    if response_text[0][j][2] not in ["시간", "날짜", "수량", "인물"] and stop and\
                            len(response_text[0][j][1]) > 1:
                        cursor.execute(f"INSERT INTO ner_hashtag (id, user_id, words, word_tag) VALUES ('{i[0]}', '{i[1]}','{response_text[0][j][1]}','{response_text[0][j][2]}')")
                        #입력되는 데이터 예시 출력
                        print(f"('{i[0]}', '{i[1]}', '{response_text[0][j][1]}', '{response_text[0][j][2]}')")
            else:
                pass

        #데이터베이스에 commit하기
        conn.commit()
    except:
        # db 연동 error 처리
        print('db 연동 error')
        conn.rollback() # db 반영 취소
    finally:
        # closing database connection.
        cursor.close()
        conn.close()
        print("connection is closed")
# ner 개체명 추출 결과 데이터베이스 저장함수 호출
ner_insert()

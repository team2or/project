from flask import Flask, render_template, request
import requests
import pymysql
from flask_socketio import SocketIO, send
import json
import random
import ast
import codecs
from urllib.parse import unquote
import os
import mtc_model



#데이터베이스 접근
db= pymysql.connect(host='192.168.30.1',
                    user='LEEJAEEUN',
                    passwd='1234!@#$',
                    db='team2db',
                    charset='utf8'
                    )
cursor= db.cursor()
# sql='''select * from corpus limit 10'''
# cursor.execute(sql)
# result=cursor.fetchall()

#데이터베이스 접근 학원
# db= pymysql.connect(host='192.168.0.124',
#                     user='team2',
#                     passwd='1234',
#                     db='team2DB',
#                     charset='utf8'
#                     )
# cursor= db.cursor()



app = Flask(__name__)
app.secret_key = "mysecret"
socket_io = SocketIO(app)


#html과 소켓 연결
@socket_io.on("message")
def reply(message):
    message = ast.literal_eval(codecs.unicode_escape_decode(unquote(message).replace('%','\\'))[0].replace('\n','\\n'))
    to_client = dict()

    if type(message) is dict :

        #ner모델 적용
        if message['type'] == 'ner' :
            input_text = message["text"][0]
            input_json = {'texts':[input_text]}
            results = requests.post('http://192.168.0.124:1111/ner', json=input_json)
            results = ast.literal_eval(results.text)
            output_text = '\n'
            for result in results :
                for (pos, word, tag) in result :
                    output_text += word+' ('+tag+')\n'
                output_text += '\n'

            if not result :
                output_text = '결과없음\n'

            send(output_text)
        
        #mrc모델 적용
        elif message['type'] == 'mrc' :
            message["context"][0] = message["context"][0][:100000]
            context = message["context"][0]
            question = message["question"][0]

            results = requests.post('http://192.168.0.124:2222/mrc', json=message)
            output_json = ast.literal_eval(results.text)[0]
            score = (output_json['score']/10) * 100
            if score > 100 : score = 100
            output_json['score'] = f"{score:2.2f}"

            send(output_json)

        #분류모델 적용
        elif message['type'] == 'mtc' :
            input_text = message["text"][0]
            if input_text == '''
 ''':
                result = {'score':'0\n0\n0\n0\n0\n0\n0', 'result':'결과없음<br>'}
            else:
                model = mtc_model.Predict()
                result = model.predict_(input_text)

            send(result)
        

@app.route('/ner')
def ner():
    #데이터베이스에서 예시 text 1개 불러오기
    sql='''select texts from corpus order by rand() limit 1'''
    cursor.execute(sql)
    result=cursor.fetchall()
    #text길이가 20이상일 때만 적용
    while len(result[0][0])<=20:
        cursor.execute(sql)
        result=cursor.fetchall()

    #1번출구 ner 개체명 추출한 단어 빈도수 통계 불러오기
    sql1='''SELECT words, count(words) FROM ner_hashtag WHERE id LIKE "1-%" GROUP BY words ORDER BY count(words) DESC LIMIT 7;'''
    cursor.execute(sql1)
    chart_list1=cursor.fetchall()
    text1 = []
    num1 = []
    for i in chart_list1:
        text1.append(i[0])
        num1.append(i[1])

    #2번출구 ner 개체명 추출한 단어 빈도수 통계 불러오기
    sql2='''SELECT words, count(words) FROM ner_hashtag WHERE id LIKE "2-%" GROUP BY words ORDER BY count(words) DESC LIMIT 7;'''
    cursor.execute(sql2)
    chart_list2=cursor.fetchall()
    text2 = []
    num2 = []
    for i in chart_list2:
        text2.append(i[0])
        num2.append(i[1])

    #3번출구 ner 개체명 추출한 단어 빈도수 통계 불러오기
    sql3='''SELECT words, count(words) FROM ner_hashtag WHERE id LIKE "3-%" GROUP BY words ORDER BY count(words) DESC LIMIT 7;'''
    cursor.execute(sql3)
    chart_list3=cursor.fetchall()
    text3 = []
    num3 = []
    for i in chart_list3:
        text3.append(i[0])
        num3.append(i[1])

    #4번출구 ner 개체명 추출한 단어 빈도수 통계 불러오기
    sql4='''SELECT words, count(words) FROM ner_hashtag WHERE id LIKE "4-%" GROUP BY words ORDER BY count(words) DESC LIMIT 7;'''
    cursor.execute(sql4)
    chart_list4=cursor.fetchall()
    text4 = []
    num4 = []
    for i in chart_list4:
        text4.append(i[0])
        num4.append(i[1])

    return render_template('ner.html', host_url=request.host_url,
    response_text=result[0][0] ,text1=text1, num1=num1, text2=text2, num2=num2, text3=text3, num3=num3, text4=text4, num4=num4)




@app.route('/mrc')
def mrc():
    #데이터베이스에서 예시 text 1개 불러오기
    sql='''select texts from corpus order by rand() limit 1'''
    cursor.execute(sql)
    result=cursor.fetchall()
    #text길이가 20이상일 때만 적용
    while len(result[0][0])<=20:
        cursor.execute(sql)
        result=cursor.fetchall()

    return render_template('mrc.html', host_url=request.host_url,
    response_text=result[0][0])

@app.route('/mtc')
def mtc():
    #데이터베이스에서 예시 text 1개 불러오기
    sql='''select texts from corpus order by rand() limit 1'''
    cursor.execute(sql)
    result=cursor.fetchall()
    #text길이가 20이상일 때만 적용
    while len(result[0][0])<=20:
        cursor.execute(sql)
        result=cursor.fetchall()
    
    return render_template('mtc.html', host_url=request.host_url,
    response_text=result[0][0])

@app.route('/')
def home():
    return render_template('home.html')    

if __name__ == '__main__':
    socket_io.run(app, debug=True)



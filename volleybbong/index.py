import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)  # MongoDB는 27017 포트로 돌아간다.
db = client.dbvolleyball  # dbvolleyball라는 이름으로 데이터베이스를 생성한다.

"""
< requests >
- 브라우저에서 엔터를 치는 효과. URL에 요청하기
- 첫 응답만 받으며 추가 요청이 없다.
- 단순한 요청에 최적화 되어있다.

< BeautifulSoup >
- HTML 파싱을 편리하게 사용할 수 있게 해준다.
- HTML을 검색하기 용이한 상태로 만든다.

< Pymongo >
- 파이썬 MongoDB의 라이브러리이다.
- 파이썬에 MongoDB를 돌아가게 해주는 패키지이다.
"""

'''
사용자의 요청받기 : Ajax통신
'''

# ########## 타겟 URL을 읽어 HTML을 받아온다.
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

# 변수에 "파싱 용이해진 html"이 담긴 상태 -> 코딩을 통해 필요한 부분을 추출할 수 있다.
# ########## 배구연맹 GAME > V-리그 > '일정 및 결과' 페이지
gameSchedulePage = requests.get(
    'https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp',
    headers=headers)
schedulePage = BeautifulSoup(gameSchedulePage.text, 'html.parser')

# ########## 1) 배구연맹의 모든 경기년도/월
gameMonth = schedulePage.select(".w120 > option")
monthArr = []  # 모든 경기년도/월 정보를 담은 배열
for month in gameMonth:
    value = month.get('value')
    monthArr.append(value)

# ################## HTML을 주는 부분
@app.route('/')
def home():
    return render_template('hello.html')
app.run()  # Debug mode: off

@app.route('/month', methods=['GET'])
def month_get():
    return jsonify(monthArr)

# 경기년도에 해당하는 경기번호 데이터 가져오기 (여자배구)
@app.route('/number', methods=['POST'])
def number_post():
    # 파라미터를 가져온다. request body 요청 - form data 형식
    month_receive = request.form['month']  # 경기년도/월 요청정보

    NumberArr = list(db.dbvolleyselect.find({'gameMonth': month_receive}, {'_id': 0}))
    selectNumberArr = []
    for number in NumberArr:
        selectNumberArr.append(int(number['gameNumber']))
    selectNumberArr = list(set(selectNumberArr))  # 중복제거

    if len(selectNumberArr) == 0:
        return jsonify({'result': 'fail', 'msg': '경기결과가 분석되지 않았습니다.'})

    return jsonify({'result': 'success', 'msg': selectNumberArr})

# 경기번호에 해당하는 경기팀 불러오기
@app.route('/team', methods=['POST'])
def team_post():
    month_receive = request.form['month']  # 경기년도/월 요청정보
    number_receive = request.form['number']  # 경기번호 요청정보

    teamResult = list(db.dbvolleyselect.find({'gameMonth': month_receive, 'gameNumber': number_receive}, {'_id': 0}))
    selectTeamArr = []
    for team in teamResult:
        selectTeamArr.append(team['gameTeam'])
    selectTeamArr = list(set(selectTeamArr))

    return jsonify({'result': 'success', 'msg': selectTeamArr})

# 경기팀에 해당하는 선수 불러오기
@app.route('/player', methods=['POST'])
def player_post():
    month_receive = request.form['month']  # 경기년도/월 요청정보
    number_receive = request.form['number']  # 경기번호 요청정보
    team_receive = request.form['team']  # 경기팀 요청정보

    playerResult = list(db.dbvolleyselect.find({'gameMonth': month_receive, 'gameNumber': number_receive, 'gameTeam': team_receive}, {'_id': 0}))
    selectPlayerArr = []
    for player in playerResult:
        selectPlayerArr.append(player['gamePlayer'])
    selectPlayerArr = list(set(selectPlayerArr))

    return jsonify(selectPlayerArr)

@app.route('/volley', methods=['POST'])
def volley_post():

    # ##### 사용자에게 입력받을 최종정보
    gameMonth = request.form['gameMonth']  # 경기년도/월 요청정보
    gameNum = request.form['gameNum']  # 경기번호 요청정보
    gameTeam = request.form['gameTeam']  # 경기팀 요청정보
    gamePlayer = request.form['gamePlayer']  # 배구선수 요청정보

    information = db.dbvolleyresult.find_one({'gameDate': gameMonth, 'gameNum': gameNum, 'ourTeam': gameTeam, 'gamePlayer': gamePlayer}, {'_id': 0})

    return jsonify(information)

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
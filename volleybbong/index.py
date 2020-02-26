import requests
from bs4 import BeautifulSoup

from datetime import datetime

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

# ################## HTML을 주는 부분
@app.route('/')
def home():
    return render_template('hello.html')

# ################## 타겟 URL을 읽어 HTML을 받아온다.
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

# 배구연맹 GAME > V-리그 > 일정 및 결과 페이지
gameSchedulePage = requests.get('https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp', headers=headers)
# 변수에 "파싱 용이해진 html"이 담긴 상태 -> 코딩을 통해 필요한 부분을 추출할 수 있다.
schedulePage = BeautifulSoup(gameSchedulePage.text, 'html.parser')

# 경기년도/월 셀렉트박스 데이터 가져오기
gameMonth = schedulePage.select(".w120 > option")

MonthArr = []  # 경기년도/월 정보를 담은 배열
for month in gameMonth:
    value = month.get('value')
    MonthArr.append(value)

@app.route('/month', methods=['GET'])
def month_get():
    return jsonify(MonthArr)

# 경기년도에 해당하는 경기번호 데이터 가져오기 (여자배구)
@app.route('/number', methods=['POST'])
def number_post():
    # 파라미터를 가져온다. request body 요청 - form data 형식
    month_receive = request.form['month']  # 경기년도/월 요청정보
    # nowDate = datetime.today().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS 형태의 시간 출력
    nowMonth = datetime.today().month  # 현재 월 가져오기

    # 오늘날짜를 앞서간 경기일자 선택 막기
    if int(month_receive[-1:]) > int(nowMonth):
        return jsonify({'result': 'fail', 'msg': '이번달과 이전의 경기일자를 선택해주세요.'})

    # 경기년도/월에 해당하는 경기정보 페이지
    gameMonthPage = requests.get('https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp?season=016&team=&yymm='+month_receive, headers=headers)
    monthPage = BeautifulSoup(gameMonthPage.text, 'html.parser')

    gameNumber = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(2)")  # 해당하는 모든 경기번호
    gameGender = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(3)")  # 해당하는 모든 경기의 성별

    # 여자배구만 가져오기
    numCount = len(gameNumber)
    NumberArr = []  # 경기번호를 담은 배열
    for i in range(0, numCount):
        if gameGender[i].text == '여자':
            value = gameNumber[i].text.strip()
            NumberArr.append(value)

    return jsonify({'result': 'success', 'msg': NumberArr})

# 경기번호에 해당하는 경기팀 불러오기
@app.route('/team', methods=['POST'])
def team_post():
    month_receive = request.form['month']  # 경기년도/월 요청정보
    number_receive = request.form['number']  # 경기번호 요청정보

    # 경기년도/월에 해당하는 경기정보 페이지
    gameMonthPage = requests.get('https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp?season=016&team=&yymm='+month_receive, headers=headers)
    monthPage = BeautifulSoup(gameMonthPage.text, 'html.parser')

    gameRowNum = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(2)")  # 경기번호
    NumberArr = []  # 경기번호를 담은 배열
    for number in gameRowNum:
        value = number.text.strip()
        if value == '':
            continue
        NumberArr.append(value)
    gameNumCnt = len(NumberArr)

    gameRowRound = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(9)")  # 경기 라운드

    # 경기번호에 해당하는 경기라운드 데이터 가져오기
    gameRound = ''  # 경기 라운드
    for game in range(0, gameNumCnt):
        if NumberArr[game] == number_receive:
            gameRound = (gameRowRound[game].text)[4:5]
    print("round : " + gameRound)

    # 해당경기의 상세결과 페이지
    gameDetailPage = requests.get('https://www.kovo.co.kr/game/v-league/11141_game-summary.asp?season=016&g_part=201&r_round='+gameRound+'&g_num='+number_receive+'&', headers=headers)
    detailPage = BeautifulSoup(gameDetailPage.text, 'html.parser')

    # 해당경기의 경기 팀 크롤링
    teamOne = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first span.team')  # 경기 팀 1
    teamTwo = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child span.team')  # 경기 팀 2

    teamResult = []  # 경기팀을 담을 배열
    teamResult.append(teamOne.text)
    teamResult.append(teamTwo.text)

    return jsonify(teamResult)

# 경기팀에 해당하는 선수 불러오기
@app.route('/player', methods=['POST'])
def player_post():
    month_receive = request.form['month']  # 경기년도/월 요청정보
    number_receive = request.form['number']  # 경기번호 요청정보
    team_receive = request.form['team']  # 경기팀 요청정보

    # 경기년도/월에 해당하는 경기정보 페이지
    gameMonthPage = requests.get('https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp?season=016&team=&yymm='+month_receive, headers=headers)
    monthPage = BeautifulSoup(gameMonthPage.text, 'html.parser')

    gameRowNum = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(2)")  # 경기번호
    NumberArr = []  # 경기번호를 담은 배열
    for number in gameRowNum:
        value = number.text.strip()
        if value == '':
            continue
        NumberArr.append(value)
    gameNumCnt = len(NumberArr)

    gameRowRound = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(9)")  # 경기 라운드

    # 경기번호에 해당하는 경기라운드 데이터 가져오기
    gameRound = ''  # 경기 라운드
    for game in range(0, gameNumCnt):
        if NumberArr[game] == number_receive:
            gameRound = (gameRowRound[game].text)[4:5]
    print("round : " + gameRound)

    # 해당경기의 상세결과 페이지
    gameDetailPage = requests.get('https://www.kovo.co.kr/game/v-league/11141_game-summary.asp?season=016&g_part=201&r_round='+gameRound+'&g_num='+number_receive+'&', headers=headers)
    detailPage = BeautifulSoup(gameDetailPage.text, 'html.parser')

    # 해당경기의 경기 팀 크롤링
    teamOne = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first span.team')  # 경기 팀 1
    teamTwo = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child span.team')  # 경기 팀 2
    print("teamOne : " + teamOne.text)
    print("teamTwo : " + teamTwo.text)

    # 해당경기의 문자중계 페이지
    gameCastPage = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round='+gameRound+'&g_num='+number_receive, headers=headers)
    castPage = BeautifulSoup(gameCastPage.text, 'html.parser')

    position1 = ''
    position2 = ''
    position3 = ''
    position4 = ''
    position5 = ''
    position6 = ''

    if team_receive == teamOne.text:
        position1 = castPage.select_one('#tab1 > .position > .left01 > li:last-child')
        position2 = castPage.select_one('#tab1 > .position > .left02 > li:last-child')
        position3 = castPage.select_one('#tab1 > .position > .left02 > li:nth-child(2)')
        position4 = castPage.select_one('#tab1 > .position > .left02 > li:first-child')
        position5 = castPage.select_one('#tab1 > .position > .left01 > li:first-child')
        position6 = castPage.select_one('#tab1 > .position > .left01 > li:nth-child(2)')
    elif team_receive == teamTwo.text:
        position1 = castPage.select_one('#tab1 > .position > .right02 > li:first-child')
        position2 = castPage.select_one('#tab1 > .position > .right01 > li:first-child')
        position3 = castPage.select_one('#tab1 > .position > .right01 > li:nth-child(2)')
        position4 = castPage.select_one('#tab1 > .position > .right01 > li:last-child')
        position5 = castPage.select_one('#tab1 > .position > .right02 > li:last-child')
        position6 = castPage.select_one('#tab1 > .position > .right02 > li:nth-child(2)')

    playerResult = []  # 경기팀에 해당하는 선수를 담을 배열
    playerResult.append(position1.text)
    playerResult.append(position2.text)
    playerResult.append(position3.text)
    playerResult.append(position4.text)
    playerResult.append(position5.text)
    playerResult.append(position6.text)
    print('position1 : ' + position1.text)

    return jsonify(playerResult)

# ################## API 역할을 하는 부분
@app.route('/volley', methods=['POST'])
def volley_post():

    # ##### 사용자에게 입력받을 정보
    gameMonth = request.form['gameMonth']  # 경기년도/월 요청정보
    gameNum = request.form['gameNum']  # 경기번호 요청정보
    gameTeam = request.form['gameTeam']  # 경기팀 요청정보
    gamePlayer = request.form['gamePlayer']  # 배구선수 요청정보
    
    # ##### URL정보에 필요한 라운드 정보 가져오기
    # 경기년도/월에 해당하는 경기정보 페이지
    gameMonthPage = requests.get('https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp?season=016&team=&yymm='+gameMonth, headers=headers)
    monthPage = BeautifulSoup(gameMonthPage.text, 'html.parser')

    gameRowNum = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(2)")  # 해당 년도의 모든 경기번호
    NumberArr = []  # 경기번호를 담은 배열
    for number in gameRowNum:
        value = number.text.strip()
        if value == '':
            continue
        NumberArr.append(value)
    gameNumCnt = len(NumberArr)

    gameRowRound = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(9)")  # 해당 년도의 모든 경기 라운드

    # 경기번호에 해당하는 경기라운드 데이터 가져오기
    gameRound = ''  # 경기 라운드
    for game in range(0, gameNumCnt):
        if NumberArr[game] == gameNum:
            gameRound = (gameRowRound[game].text)[4:5]
    print("round : " + gameRound)

    # ##### 1. 한국 배구연맹 경기에 대한 상세결과 페이지 - 경기일자 / 우리팀 / 상대팀 / 최종 경기결과 크롤링
    gameDetailPage = requests.get('https://www.kovo.co.kr/game/v-league/11141_game-summary.asp?season=016&g_part=201&r_round='+gameRound+'&g_num='+gameNum+'&',headers=headers)
    detailPage = BeautifulSoup(gameDetailPage.text, 'html.parser')
    # ##### 2. 상세결과 페이지의 문자중계 페이지 - 포지션별 선수 세팅을 위한 초기 포지션 크롤링 / 총 SET 개수 구하기
    gameCastPage = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round='+gameRound+'&g_num='+gameNum,headers=headers)
    castPage = BeautifulSoup(gameCastPage.text, 'html.parser')

    # 경기일자 / 상대팀 / 최종 경기결과 데이터 가져오기
    gameDate = detailPage.select_one('.lst_recentgame > thead > tr > th')  # 경기일자

    teamOne = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first span.team')  # 경기 팀 1
    teamOneResult = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first p.result')  # 팀 경기결과
    teamOneSetScore = detailPage.select_one('.lst_recentgame > tbody > tr > td:nth-child(2) .num')  # 팀 최종 점수

    teamTwo = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child span.team')  # 경기 팀 2
    teamTwoResult = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child p.result')  # 팀 경기결과
    teamTwoSetScore = detailPage.select_one('.lst_recentgame > tbody > tr > td:nth-child(4) .num')  # 팀 최종 점수

    # ##### 사용자의 요청정보에 해당하는 팀 찾기
    ourTeam = ''
    opposeTeam = ''
    position1 = ''
    position2 = ''
    position3 = ''
    position4 = ''
    position5 = ''
    position6 = ''
    ourTeamResult = ''

    if gameTeam == teamOne.text:
        ourTeam = teamOne.text
        opposeTeam = teamTwo.text
        position1 = castPage.select_one('#tab1 > .position > .left01 > li:last-child')
        position2 = castPage.select_one('#tab1 > .position > .left02 > li:last-child')
        position3 = castPage.select_one('#tab1 > .position > .left02 > li:nth-child(2)')
        position4 = castPage.select_one('#tab1 > .position > .left02 > li:first-child')
        position5 = castPage.select_one('#tab1 > .position > .left01 > li:first-child')
        position6 = castPage.select_one('#tab1 > .position > .left01 > li:nth-child(2)')
        # 리베로 선수
        libero = (castPage.select_one('#tab1 > .position > .li01 > li:first-child').text)[4:7]

        ourTeamResult = teamOneResult.text

    elif gameTeam == teamTwo.text:
        ourTeam = teamTwo.text
        opposeTeam = teamOne.text
        position1 = castPage.select_one('#tab1 > .position > .right02 > li:first-child')
        position2 = castPage.select_one('#tab1 > .position > .right01 > li:first-child')
        position3 = castPage.select_one('#tab1 > .position > .right01 > li:nth-child(2)')
        position4 = castPage.select_one('#tab1 > .position > .right01 > li:last-child')
        position5 = castPage.select_one('#tab1 > .position > .right02 > li:last-child')
        position6 = castPage.select_one('#tab1 > .position > .right02 > li:nth-child(2)')
        # 리베로 선수
        libero = (castPage.select_one('#tab1 > .position > .li02 > li:first-child').text)[4:7]

        ourTeamResult = teamTwoResult.text

    print('우리팀 : ' + ourTeam)
    print('우리팀 결과 : ' + ourTeamResult)
    print('상대팀 : ' + opposeTeam)
    print('1번 포지션 : ' + position1.text)
    print('2번 포지션 : ' + position2.text)
    print('3번 포지션 : ' + position3.text)
    print('4번 포지션 : ' + position4.text)
    print('5번 포지션 : ' + position5.text)
    print('6번 포지션 : ' + position6.text)
    print('리베로 선수 : ' + libero)

    # ##### 문자중계 페이지에서 총 랠리 개수 구하기 * 최종적으로 T(득점)과 F(실점) 데이터와 포지션 로테이션에 필요 *
    sets = castPage.select('.wrp_tab_set > ul > li')
    setCount = len(sets)  # 세트의 개수
    print('세트의 개수 : ' + str(setCount))

    # ##### 각 세트의 스코어 크롤링 -> 랠리의 총 개수 찾기
    setArr = []  # 세트 배열
    AlltfArr = []  # 최종 T/F 배열
    for set in range(1, setCount+1):

        # ##### 3. 각 세트 페이지
        gameSetPage = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round='+gameRound+'&g_num='+gameNum+'&r_set='+str(set),headers=headers)
        setPage = BeautifulSoup(gameSetPage.text, 'html.parser')

        scores = ''  # 해당팀의 모든 점수태그 가져오기
        # 해당하는 팀에 따라 크롤링해야 하는 위치가 달라진다.
        if teamOne.text == ourTeam:
            scores = setPage.select('#onair_lst > ul > li > span.score_left')
        elif teamTwo.text == ourTeam:
            scores = setPage.select('#onair_lst > ul > li > span.score_right')

        # 모든 점수 태그를 숫자만 뽑아 배열에 담는다.
        scoreArr = []  # 해당팀의 세트별 점수 배열
        for score in scores:
            if score.text.strip():
                scoreArr.append(score.text.strip())

        # ##### 해당팀의 T/F 구하기
        tfArr = []  # 해당팀의 세트별 T/F 배열
        for i in range(0, len(scoreArr)):
            if i > 0:
                if(scoreArr[i-1] < scoreArr[i]):
                    tfArr.append('T')
                    setArr.append(set)
                else:
                    tfArr.append('F')
                    setArr.append(set)
        AlltfArr += tfArr  # 세트별 T/F 모두 합한다. - 한 경기의 T/F

    print("득실 배열 수 : " + str(len(AlltfArr)))
    print("세트 배열 수 : " + str(len(setArr)))

    # ##### 세트별 선수 포지션 설정하기
    doc = {
        'gameDate': gameDate.text,  # 경기일자
        'gameNumber': gameNum,  # 경기번호 요청정보
        'ourTeam': ourTeam,  # 우리팀
        'opposeTeam': opposeTeam,  # 상대팀
        'ourTeamResult': ourTeamResult,  # 경기결과
        'set': setArr[0],  # 세트
        'position1': position1.text,  # 1번 포지션
        'position2': position2.text,  # 2번 포지션
        'position3': position3.text,  # 3번 포지션
        'position4': position4.text,  # 4번 포지션
        'position5': position5.text,  # 5번 포지션
        'position6': position6.text,   # 6번 포지션
        'libero': libero,  # 리베로 선수
        'profit': AlltfArr[0]  # 득점 실점 정보 - T:득점 / F:실점
    }

    # ##### 센터 선수와 리베로 선수 크롤링
    centers = ''  # 해당팀의 모든 센터태그 가져오기

    # 사용자가 요청한 팀의 센터선수 찾기
    if teamOne.text == ourTeam:
        centers = detailPage.select('.wrp_recordtable:first-child > .wrp_lst > .lst_board > tbody > tr > td')
    elif teamTwo.text == ourTeam:
        centers = detailPage.select('.wrp_recordtable:last-child > .wrp_lst > .lst_board > tbody > tr > td')

    centerArr = []  # 해당팀의 센터선수 배열
    for center in centers:
        centerArr.append(center.text.strip())

    # '[C]':센터 - 라는 텍스트가 포함된 태그찾기
    searchCenter = '[C]'
    center_list = list()
    for word in centerArr:
        if searchCenter in word:
            center_list.append(word[:3])
    print('센터 선수 : ' + str(center_list))

    # ######### MongoDB에 기초 데이터 저장하기
    # MongoDB 'dbvolleyball'라는 collection에 초기정보 insert
    # 기본구조는 Dictionary의 형태

    for i in range(1, len(AlltfArr)+1):
        if '_id' in doc:
            del doc['_id']

        doc['set'] = setArr[i - 1]
        doc['profit'] = AlltfArr[i - 1]

        db.dbvolleyball.insert_one(doc)

        # 예외사항 2) 센터와 리베로 선수교체
        if doc['position6'] == center_list[0]:
            doc['position6'] = doc['libero']
        elif doc['position5'] == center_list[0]:
            doc['position5'] = doc['libero']
        elif doc['position4'] == doc['libero']:
            doc['position4'] = center_list[0]

        # 예외사항 1) T/F 정보를 이용하여 로테이션 여부 판단
        if i < len(AlltfArr):
            if AlltfArr[i-2] == 'F' and AlltfArr[i-1] == 'T':
                # position : 중복을 피하기 위한 더미 변수
                doc['position'] = doc['position1']
                doc['position1'] = doc['position2']
                doc['position2'] = doc['position3']
                doc['position3'] = doc['position4']
                doc['position4'] = doc['position5']
                doc['position5'] = doc['position6']
                doc['position6'] = doc['position']

        #db.dbvolleyball.remove({});  # collection의 모든 데이터 삭제

    # ################## 데이터베이스에서 데이터 가져오기 - 해당하는 선수의 각 포지션의 득점과 실점
    # 포지션 1번 득점과 실점
    pt1T_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position1': gamePlayer, 'profit': 'T'}))
    print('포지션1에서 T의 개수 : ' + str(len(pt1T_list)))
    pt1F_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position1': gamePlayer, 'profit': 'F'}))
    print('포지션1에서 F의 개수 : ' + str(len(pt1F_list)))
    pt1Margin = len(pt1T_list) - len(pt1F_list)
    print('마진 : ' + str(pt1Margin))

    # 포지션 2번 득점과 실점
    pt2T_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position2': gamePlayer, 'profit': 'T'}))
    print('포지션2에서 T의 개수 : ' + str(len(pt2T_list)))
    pt2F_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position2': gamePlayer, 'profit': 'F'}))
    print('포지션2에서 F의 개수 : ' + str(len(pt2F_list)))
    pt2Margin = len(pt2T_list) - len(pt2F_list)
    print('마진 : ' + str(pt2Margin))

    # 포지션 3번 득점과 실점
    pt3T_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position3': gamePlayer, 'profit': 'T'}))
    print('포지션3에서 T의 개수 : ' + str(len(pt3T_list)))
    pt3F_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position3': gamePlayer, 'profit': 'F'}))
    print('포지션3에서 F의 개수 : ' + str(len(pt3F_list)))
    pt3Margin = len(pt3T_list) - len(pt3F_list)
    print('마진 : ' + str(pt3Margin))

    # 포지션 4번 득점과 실점
    pt4T_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position4': gamePlayer, 'profit': 'T'}))
    print('포지션4에서 T의 개수 : ' + str(len(pt4T_list)))
    pt4F_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position4': gamePlayer, 'profit': 'F'}))
    print('포지션4에서 F의 개수 : ' + str(len(pt4F_list)))
    pt4Margin = len(pt4T_list) - len(pt4F_list)
    print('마진 : ' + str(pt4Margin))

    # 포지션 5번 득점과 실점
    pt5T_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position5': gamePlayer, 'profit': 'T'}))
    print('포지션5에서 T의 개수 : ' + str(len(pt5T_list)))
    pt5F_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position5': gamePlayer, 'profit': 'F'}))
    print('포지션5에서 F의 개수 : ' + str(len(pt5F_list)))
    pt5Margin = len(pt5T_list) - len(pt5F_list)
    print('마진 : ' + str(pt5Margin))

    # 포지션 6번 득점과 실점
    pt6T_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position6': gamePlayer, 'profit': 'T'}))
    print('포지션6에서 T의 개수 : ' + str(len(pt6T_list)))
    pt6F_list = list(db.dbvolleyball.find({'gameNumber': gameNum, 'position6': gamePlayer, 'profit': 'F'}))
    print('포지션6에서 F의 개수 : ' + str(len(pt6F_list)))
    pt6Margin = len(pt6T_list) - len(pt6F_list)
    print('마진 : ' + str(pt6Margin))

    return jsonify({
                    'pt1T_list': len(pt1T_list),  # 1번 포지션에서의 T의 개수
                    'pt1F_list': len(pt1F_list),  # 1번 포지션에서의 F의 개수
                    'pt1Margin': pt1Margin,  # 1번 포지션에서의 마진
                    'pt2T_list': len(pt2T_list),
                    'pt2F_list': len(pt2F_list),
                    'pt2Margin': pt2Margin,
                    'pt3T_list': len(pt3T_list),
                    'pt3F_list': len(pt3F_list),
                    'pt3Margin': pt3Margin,
                    'pt4T_list': len(pt4T_list),
                    'pt4F_list': len(pt4F_list),
                    'pt4Margin': pt4Margin,
                    'pt5T_list': len(pt5T_list),
                    'pt5F_list': len(pt5F_list),
                    'pt5Margin': pt5Margin,
                    'pt6T_list': len(pt6T_list),
                    'pt6F_list': len(pt6F_list),
                    'pt6Margin': pt6Margin
                    })


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
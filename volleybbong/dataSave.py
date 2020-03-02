import requests
from bs4 import BeautifulSoup

from flask import Flask
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)  # MongoDB는 27017 포트로 돌아간다.
db = client.dbvolleyball  # dbvolleyball라는 이름으로 데이터베이스를 생성한다.

# collection의 모든 데이터 삭제
db.dbvolleyball.remove({})
db.dbvolleyresult.remove({})
db.dbvolleyselect.remove({})

'''
배치 프로그램 : 배구연맹 사이트의 모든 데이터 저장하기 [크롤링]
'''

################################################## 사용자의 모든 선택을 dbvolleyselect에 저장

# ########## 타겟 URL을 읽어 HTML을 받아온다.
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

# 변수에 "파싱 용이해진 html"이 담긴 상태 -> 코딩을 통해 필요한 부분을 추출할 수 있다.
# ########## 배구연맹 GAME > V-리그 > '일정 및 결과' 페이지
gameSchedulePage = requests.get(
    'https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp',
    headers=headers)
schedulePage = BeautifulSoup(gameSchedulePage.text, 'html.parser')

# ########## 1) 배구연맹의 모든 경기년도/월 크롤링
gameMonth = schedulePage.select(".w120 > option")
monthArr = []  # 모든 경기년도/월 정보를 담은 배열
for month in gameMonth:
    value = month.get('value')
    monthArr.append(value)

# ########## 2) 해당 경기년월의 모든 경기번호 크롤링(여자배구)
monthArrLen = len(monthArr)

# 각 경기년월에 해당하는 경기번호를 모두 가져와야 한다.
for year in range(0, monthArrLen):

    # ########## 배구연맹 해당하는 년도/월 페이지
    gameMonthPage = requests.get(
        'https://www.kovo.co.kr/game/v-league/11110_schedule_list.asp?season=016&team=&yymm=' + monthArr[year],
        headers=headers)
    monthPage = BeautifulSoup(gameMonthPage.text, 'html.parser')

    # ##### 테이블의 구조가 규칙적이지 않아 공백을 제거한 배열을 맞춰준다.
    gameRowNumber = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(2)")  # 해당하는 모든 경기번호 (공백 포함)
    gameRowGender = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(3)")  # 해당하는 모든 경기의 성별 (공백 포함)
    # 경기 라운드 (경기가 없다면 라운드의 td태그가 존재하지 않아 정보가 있는 td태그만 담는다.)
    roundNotNull = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(9)")

    numberNotNull = []  # 모든 경기번호를 담은 배열 (공백 제거)
    for number in gameRowNumber:
        value = number.text.strip()
        if value == '':
            continue
        numberNotNull.append(value)

    genderNotNull = []  # 모든 경기의 성별을 담은 배열 (공백 제거)
    for gender in gameRowGender:
        value = gender.text.strip()
        if value == '경기가 없습니다.':
            continue
        genderNotNull.append(value)

    numberCnt = len(numberNotNull)
    genderCnt = len(genderNotNull)

    # ##### 비고란의 티켓예매 여부에 따라 데이터 저장 제한하기
    # 경기 비고칸 (경기가 없다면 비고칸의 td태그가 존재하지 않아 정보가 있는 td태그만 담는다.)
    gameRowTicket = monthPage.select(".lst_schedule > tbody > tr > td:nth-child(10)")
    ticketNotNull = []  # 모든 비고란을 담은 배열
    for ticket in gameRowTicket:
        ticketNotNull.append(ticket.text.strip())

    # 여자배구만 가져오기
    numberArr = []  # 경기번호를 담은 배열
    roundArr = []  # 경기라운드를 담은 배열
    ticketArr = []  # 비고란을 담은 배열
    for number in range(0, numberCnt):
        if genderNotNull[number] == '여자':
            # 여자배구 경기번호를 담은 배열
            value = numberNotNull[number]
            numberArr.append(value)
            # 여자배구 경기라운드를 담은 배열
            roundVal = (roundNotNull[number].text)[4:5]
            roundArr.append(roundVal)
            # 여자배구 비고란을 담은 배열
            ticketVal = ticketNotNull[number]
            ticketArr.append(ticketVal)

    # ########## 3) 해당 경기번호의 모든 경기팀
    numberArrLen = len(numberArr)

    # 경기번호에 해당하는 경기라운드 데이터 가져오기
    for i in range(0, numberArrLen):

        # 아직 경기의 상세결과가 나오지 않아 정보를 저장할 수 없다.
        if ((ticketArr[i])[-4:]) == "티켓예매":
            break

        # ########## 배구연맹 상세결과 페이지
        gameDetailPage = requests.get(
            'https://www.kovo.co.kr/game/v-league/11141_game-summary.asp?season=016&g_part=201&r_round=' + roundArr[i] + '&g_num=' + numberArr[i] + '&',
            headers=headers)
        detailPage = BeautifulSoup(gameDetailPage.text, 'html.parser')

        # 경기일자 / 상대팀 / 최종 경기결과 데이터 가져오기
        gameDate = detailPage.select_one('.lst_recentgame > thead > tr > th')  # 경기일자

        teamOne = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first span.team')  # 경기 팀 1
        teamOneResult = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first p.result')  # 팀 경기결과
        teamOneSetScore = detailPage.select_one('.lst_recentgame > tbody > tr > td:nth-child(2) .num')  # 팀 최종 점수

        teamTwo = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child span.team')  # 경기 팀 2
        teamTwoResult = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child p.result')  # 팀 경기결과
        teamTwoSetScore = detailPage.select_one('.lst_recentgame > tbody > tr > td:nth-child(4) .num')  # 팀 최종 점수

        teamArr = []  # 경기팀을 담을 배열
        teamArr.append(teamOne.text)
        teamArr.append(teamTwo.text)

        # ########## 4) 해당 경기팀의 모든 선수
        teamArrLen = len(teamArr)
        for team in range(0, teamArrLen):

            # 해당경기의 문자중계 페이지
            gameCastPage = requests.get(
                'https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round=' + roundArr[i] + '&g_num=' + numberArr[i],
                headers=headers)
            castPage = BeautifulSoup(gameCastPage.text, 'html.parser')

            ourTeam = ''
            opposeTeam = ''
            ourTeamResult = ''
            position1 = ''
            position2 = ''
            position3 = ''
            position4 = ''
            position5 = ''
            position6 = ''

            if teamArr[team] == teamOne.text:
                ourTeam = teamOne.text
                opposeTeam = teamTwo.text
                # 리베로 선수
                libero = (castPage.select_one('#tab1 > .position > .li01 > li:first-child').text)[4:7]
                position1 = castPage.select_one('#tab1 > .position > .left01 > li:last-child')
                position2 = castPage.select_one('#tab1 > .position > .left02 > li:last-child')
                position3 = castPage.select_one('#tab1 > .position > .left02 > li:nth-child(2)')
                position4 = castPage.select_one('#tab1 > .position > .left02 > li:first-child')
                position5 = castPage.select_one('#tab1 > .position > .left01 > li:first-child')
                position6 = castPage.select_one('#tab1 > .position > .left01 > li:nth-child(2)')
                ourTeamResult = teamOneResult.text
            elif teamArr[team] == teamTwo.text:
                ourTeam = teamTwo.text
                opposeTeam = teamOne.text
                # 리베로 선수
                libero = (castPage.select_one('#tab1 > .position > .li02 > li:first-child').text)[4:7]
                position1 = castPage.select_one('#tab1 > .position > .right02 > li:first-child')
                position2 = castPage.select_one('#tab1 > .position > .right01 > li:first-child')
                position3 = castPage.select_one('#tab1 > .position > .right01 > li:nth-child(2)')
                position4 = castPage.select_one('#tab1 > .position > .right01 > li:last-child')
                position5 = castPage.select_one('#tab1 > .position > .right02 > li:last-child')
                position6 = castPage.select_one('#tab1 > .position > .right02 > li:nth-child(2)')
                ourTeamResult = teamTwoResult.text

            playArr = []  # 경기팀에 해당하는 모든 선수를 담을 배열
            playArr.append(position1.text)
            playArr.append(position2.text)
            playArr.append(position3.text)
            playArr.append(position4.text)
            playArr.append(position5.text)
            playArr.append(position6.text)

            for player in playArr:
                print('경기년월 : ' + monthArr[year])
                print('경기번호 : ' + numberArr[i])
                print('경기라운드 : ' + roundArr[i])
                print('경기팀 : ' + teamArr[team])
                print('팀 선수 : ' + player)
                print('#####################################')

                selectDoc = {
                    'gameMonth': monthArr[year],  # 경기년월
                    'gameNumber': numberArr[i],  # 경기번호
                    'gameTeam': teamArr[team],  # 경기팀
                    'gamePlayer': player  # 배구선수
                }

                db.dbvolleyselect.insert_one(selectDoc)

################################################## 선택별 모든 로테이션 변화를 dbvolleyball에 저장

                gameMonth = monthArr[year]  # 경기년도/월 요청정보
                gameNum = numberArr[i]  # 경기번호 요청정보
                gameRound = roundArr[i]  # 경기라운드 요청정보
                gameTeam = teamArr[team]  # 경기팀 요청정보
                gamePlayer = player  # 배구선수 요청정보

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

                # ########## 문자중계 페이지에서 총 랠리 개수 구하기 * 최종적으로 T(득점)과 F(실점) 데이터와 포지션 로테이션에 필요 *
                sets = castPage.select('.wrp_tab_set > ul > li')
                setCount = len(sets)  # 세트의 개수
                print('세트의 개수 : ' + str(setCount))

                # ##### 각 세트의 스코어 크롤링 -> 랠리의 총 개수 찾기
                setArr = []  # 세트 배열
                finalTFarr = []  # 최종 T/F 배열
                for set in range(1, setCount + 1):

                    # ##### 3. 각 세트 페이지
                    gameSetPage = requests.get(
                        'https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round=' + gameRound + '&g_num=' + gameNum + '&r_set=' + str(set),
                        headers=headers)
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
                    for tf in range(0, len(scoreArr)):
                        if tf > 0:
                            if (scoreArr[tf - 1] < scoreArr[tf]):
                                tfArr.append('T')
                                setArr.append(set)
                            else:
                                tfArr.append('F')
                                setArr.append(set)
                    finalTFarr += tfArr  # 세트별 T/F 모두 합한다. - 한 경기의 T/F

                print("득실 배열 수 : " + str(len(finalTFarr)))
                print("세트 배열 수 : " + str(len(setArr)))

                # ##### 세트별 선수 포지션 설정하기
                doc = {
                    'gameDate': gameMonth,  # 경기일자
                    'gameNumber': gameNum,  # 경기번호 요청정보
                    'ourTeam': ourTeam,  # 우리팀
                    'opposeTeam': opposeTeam,  # 상대팀
                    'ourTeamResult': ourTeamResult,  # 경기결과
                    'myPlayer': gamePlayer,  # 내가 선택한 배구선수
                    'set': setArr[0],  # 세트
                    'position1': position1.text,  # 1번 포지션
                    'position2': position2.text,  # 2번 포지션
                    'position3': position3.text,  # 3번 포지션
                    'position4': position4.text,  # 4번 포지션
                    'position5': position5.text,  # 5번 포지션
                    'position6': position6.text,  # 6번 포지션
                    'libero': libero,  # 리베로 선수
                    'profit': finalTFarr[0]  # 득점 실점 정보 - T:득점 / F:실점
                }

                # ##### 센터 선수와 리베로 선수 크롤링
                centers = ''  # 해당팀의 모든 센터태그 가져오기

                # 사용자가 요청한 팀의 센터선수 찾기
                if teamOne.text == ourTeam:
                    centers = detailPage.select(
                        '.wrp_recordtable:first-child > .wrp_lst > .lst_board > tbody > tr > td')
                elif teamTwo.text == ourTeam:
                    centers = detailPage.select(
                        '.wrp_recordtable:last-child > .wrp_lst > .lst_board > tbody > tr > td')

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

                # ########## MongoDB에 기초 데이터 저장하기 : 'dbvolleyball' collection에 초기정보 저장 (Dictionary)

                db.dbvolleyball.remove({})  # 데이터를 초기화 해준다. (최종데이터를 구할 때 중복 예방)

                for alltf in range(1, len(finalTFarr) + 1):
                    if '_id' in doc:
                        del doc['_id']

                    doc['set'] = setArr[alltf - 1]
                    doc['profit'] = finalTFarr[alltf - 1]

                    db.dbvolleyball.insert_one(doc)

                    # ##### 예외사항 2) 센터와 리베로 선수교체
                    if doc['position6'] == center_list[0]:
                        doc['position6'] = doc['libero']
                    elif doc['position5'] == center_list[0]:
                        doc['position5'] = doc['libero']
                    elif doc['position4'] == doc['libero']:
                        doc['position4'] = center_list[0]

                    # ##### 예외사항 1) T/F 정보를 이용하여 로테이션 여부 판단
                    if alltf < len(finalTFarr):
                        if finalTFarr[alltf - 2] == 'F' and finalTFarr[alltf - 1] == 'T':
                            # position : 중복을 피하기 위한 더미 변수
                            doc['position'] = doc['position1']
                            doc['position1'] = doc['position2']
                            doc['position2'] = doc['position3']
                            doc['position3'] = doc['position4']
                            doc['position4'] = doc['position5']
                            doc['position5'] = doc['position6']
                            doc['position6'] = doc['position']

################################################## 해당 선수의 포지션별 득점과 실점을 dbvolleyresult에 저장

                resultDoc = {}
                for result in range(1, 7):
                    T_count = len(list(db.dbvolleyball.find({'gameNumber': gameNum, 'position' + str(result): gamePlayer, 'profit': 'T'})))
                    F_count = len(list(db.dbvolleyball.find({'gameNumber': gameNum, 'position' + str(result): gamePlayer, 'profit': 'F'})))
                    margin = T_count - F_count

                    resultDoc['position' + str(result) + 'T'] = T_count
                    resultDoc['position' + str(result) + 'F'] = F_count
                    resultDoc['position' + str(result) + 'M'] = margin

                # 해당 선수의 총 마진
                All_tcount = len(list(db.dbvolleyball.find({'gameNumber': gameNum, 'myPlayer': gamePlayer, 'profit': 'T'})))
                All_fcount = len(list(db.dbvolleyball.find({'gameNumber': gameNum, 'myPlayer': gamePlayer, 'profit': 'F'})))
                All_margin = All_tcount - All_fcount
                resultDoc['allT'] = All_tcount
                resultDoc['allF'] = All_fcount
                resultDoc['allM'] = All_margin
                resultDoc['ourTeam'] = ourTeam
                resultDoc['ourTeamResult'] = ourTeamResult
                resultDoc['gameDate'] = monthArr[year]
                resultDoc['gameNum'] = gameNum
                resultDoc['gamePlayer'] = gamePlayer

                db.dbvolleyresult.insert_one(resultDoc)
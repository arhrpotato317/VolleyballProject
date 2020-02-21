import requests
from bs4 import BeautifulSoup

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

# ######### 사용자에게 입력받을 정보
gameNum = '147'  # 경기순번
gameTeam = '현대캐피탈'  # 사용자가 원하는 배구팀
gameGender = '5'  # 배구팀 성별 4 = 여자 / 5 = 남자

# ######### 타겟 URL을 읽어 HTML을 받아온다.
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

# ######### 변수에 "파싱 용이해진 html"이 담긴 상태 -> 코딩을 통해 필요한 부분을 추출할 수 있다.
# 1. 한국 배구연맹 경기에 대한 상세결과 페이지 - 경기일자 / 우리팀 / 상대팀 / 최종 경기결과 크롤링
gameDetailPage = requests.get('https://www.kovo.co.kr/game/v-league/11141_game-summary.asp?season=016&g_part=201&r_round='+gameGender+'&g_num='+gameNum+'&',headers=headers)
detailPage = BeautifulSoup(gameDetailPage.text, 'html.parser')
# 2. 상세결과 페이지의 문자중계 페이지 - 포지션별 선수 세팅을 위한 초기 포지션 크롤링 / 총 SET 개수 구하기
gameCastPage = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round='+gameGender+'&g_num='+gameNum,headers=headers)
castPage = BeautifulSoup(gameCastPage.text, 'html.parser')

# 경기일자 / 상대팀 / 최종 경기결과 데이터 가져오기
gameDate = detailPage.select_one('.lst_recentgame > thead > tr > th')  # 경기일자

teamOne = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first span.team')  # 경기 팀 1
teamOneResult = detailPage.select_one('.lst_recentgame > tbody > tr > td.team.first p.result')  # 팀 경기결과
teamOneSetScore = detailPage.select_one('.lst_recentgame > tbody > tr > td:nth-child(2) .num')  # 팀 최종 점수

teamTwo = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child span.team')  # 경기 팀 2
teamTwoResult = detailPage.select_one('.lst_recentgame > tbody > tr > td.team:last-child p.result')  # 팀 경기결과
teamTwoSetScore = detailPage.select_one('.lst_recentgame > tbody > tr > td:nth-child(4) .num')  # 팀 최종 점수

# ######### 사용자의 입력에 해당하는 팀 찾기
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

    ourTeamResult = teamTwoResult.text

print(teamOne)
print(teamTwo)
print('우리팀 : ' + ourTeam)
print('우리팀 결과 : ' + ourTeamResult)
print('상대팀 : ' + opposeTeam)
print('1번 포지션 : ' + position1.text)
print('2번 포지션 : ' + position2.text)
print('3번 포지션 : ' + position3.text)
print('4번 포지션 : ' + position4.text)
print('5번 포지션 : ' + position5.text)
print('6번 포지션 : ' + position6.text)

# ######### 문자중계 페이지에서 총 SET 개수 구하기 * 최종적으로 T(득점)과 F(실점) 데이터를 위한 로직 *
sets = castPage.select('.wrp_tab_set > ul > li')
setCount = len(sets)  # 세트의 개수
print('세트의 개수 : ' + str(setCount))

# ######### 각 세트의 스코어 크롤링 -> 랠리의 총 개수 찾기
AlltfArr = []  # 최종 T/F 배열
for set in range(1, setCount+1):

    # 3. 각 세트 페이지
    gameSetPage = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round='+gameGender+'&g_num='+gameNum+'&r_set='+str(set),headers=headers)
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

    # ######### 해당팀의 T/F 구하기
    tfArr = []  # 해당팀의 세트별 T/F 배열
    for i in range(0, len(scoreArr)):
        if i > 0:
            if(scoreArr[i-1] < scoreArr[i]):
                tfArr.append('T')
            else:
                tfArr.append('F')
    AlltfArr += tfArr  # 세트별 T/F 모두 합한다.

print('득실 배열 : ' + str(AlltfArr))

# ######### 세트별 선수 포지션 설정하기
doc = {
    'gameDate': gameDate.text,  # 경기일자
    'ourTeam': ourTeam,  # 우리팀
    'opposeTeam': opposeTeam,  # 상대팀
    'ourTeamResult': ourTeamResult,  # 경기결과
    'position1': position1.text,  # 1번 포지션
    'position2': position2.text,  # 2번 포지션
    'position3': position3.text,  # 3번 포지션
    'position4': position4.text,  # 4번 포지션
    'position5': position5.text,  # 5번 포지션
    'position6': position6.text,   # 6번 포지션
    'profit': AlltfArr[0]  # 득점 실점 정보 - T:득점 / F:실점
}

# ######### 센터 선수와 리베로 선수 크롤링
centers = ''  # 해당팀의 모든 센터태그 가져오기

# 사용자 입력정보에 따른 팀의 센터선수 찾기
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

# '[Li]':리베로 - 라는 텍스트가 포함된 태그찾기
searchLi = '[Li]'
li_list = list()
for word in centerArr:
    if searchLi in word:
        li_list.append(word[:3])
print('리베로 선수 : ' + str(li_list))

# ######### MongoDB에 기초 데이터 저장하기
# MongoDB 'dbvolleyball'라는 collection에 초기정보 insert
# 기본구조는 Dictionary의 형태

for i in range(1, len(AlltfArr)+1):
    if '_id' in doc:
        del doc['_id']

    doc['profit'] = AlltfArr[i-1]
    # 예외사항 2) 센터와 리베로 선수교체
    if doc['position6'] == center_list[0]:
        doc['position6'] = li_list[0]
    elif doc['position5'] == center_list[0]:
        doc['position5'] = li_list[0]
    elif doc['position4'] == li_list[0]:
        doc['position4'] = center_list[0]

    db.dbvolleyball.insert_one(doc)

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










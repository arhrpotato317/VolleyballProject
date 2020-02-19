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

gameNum = '150'  # 경기순번 : 사용자에게 입력받을 변수
gameTeam = '현대건설'  # 사용자에게 입력받을 배구팀
gameGender = '4';  # 사용자에게 입력받을 배구팀 성별 4 = 여자 / 5 = 남자

# 타겟 URL을 읽어 HTML을 받아온다.
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
data = requests.get('https://www.kovo.co.kr/game/v-league/11141_game-summary.asp?season=016&g_part=201&r_round='+gameGender+'&g_num='+gameNum+'&',headers=headers)
# 포지션별 선수 세팅
position = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round=5&g_num='+gameNum,headers=headers)

# soup이라는 변수에 "파싱 용이해진 html"이 담긴 상태 -> 코딩을 통해 필요한 부분을 추출할 수 있다.
soup = BeautifulSoup(data.text, 'html.parser')
souppt = BeautifulSoup(position.text, 'html.parser')

# 경기일자 / 상대팀 / 최종 경기결과 데이터 가져오기
# 경기일자
gameDate = soup.select_one('.lst_recentgame > thead > tr > th')
# 경기 팀
teamOne = soup.select_one('.lst_recentgame > tbody > tr > td.team.first span.team')
teamOneResult = soup.select_one('.lst_recentgame > tbody > tr > td.team.first p.result')
teamOneSetScore = soup.select_one('.lst_recentgame > tbody > tr > td:nth-child(2) .num')

teamTwo = soup.select_one('.lst_recentgame > tbody > tr > td.team:last-child span.team')
teamTwoResult = soup.select_one('.lst_recentgame > tbody > tr > td.team:last-child p.result')
teamTwoSetScore = soup.select_one('.lst_recentgame > tbody > tr > td:nth-child(4) .num')

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
    position1 = souppt.select_one('#tab1 > .position > .left01 > li:last-child')
    position2 = souppt.select_one('#tab1 > .position > .left02 > li:last-child')
    position3 = souppt.select_one('#tab1 > .position > .left02 > li:nth-child(2)')
    position4 = souppt.select_one('#tab1 > .position > .left02 > li:first-child')
    position5 = souppt.select_one('#tab1 > .position > .left01 > li:first-child')
    position6 = souppt.select_one('#tab1 > .position > .left01 > li:nth-child(2)')

    ourTeamResult = teamOneResult.text

elif gameTeam == teamTwo.text:
    ourTeam = teamTwo.text
    opposeTeam = teamOne.text
    position1 = souppt.select_one('#tab1 > .position > .right02 > li:first-child')
    position2 = souppt.select_one('#tab1 > .position > .right01 > li:first-child')
    position3 = souppt.select_one('#tab1 > .position > .right01 > li:nth-child(2)')
    position4 = souppt.select_one('#tab1 > .position > .right01 > li:last-child')
    position5 = souppt.select_one('#tab1 > .position > .right02 > li:last-child')
    position6 = souppt.select_one('#tab1 > .position > .right02 > li:nth-child(2)')

    ourTeamResult = teamTwoResult.text

print(teamOne)
print(teamTwo)
print(ourTeam)
print(opposeTeam)
print(position1.text)
print(position2.text)
print(position3.text)
print(position4.text)
print(position5.text)
print(position6.text)

# MongoDB 'dbvolleyball'라는 collection에 초기정보 insert
# 기본구조는 Dictionary의 형태
'''
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
    'position6': position6.text   # 6번 포지션
}
'''
# db.dbvolleyball.insert_one(doc)
# 가장 처음 문자중계에서 set개수 구하기
gameSetCount = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round=5&g_num='+gameNum,headers=headers)
soupsc = BeautifulSoup(gameSetCount.text, 'html.parser')
setCount = soupsc.select('.wrp_tab_set > ul > li')
count = len(setCount)  # 세트의 개수

# 세트의 개수만큼 반복문을 실행하여 서브개수 구하기 -> 서브의 개수로 랠리의 개수 판단 (총 랠리 개수 구하기)
serveCnt = 0  # 서브최종개수
AlltfArr = []  # 최종 T/F 배열
for set in range(1, count+1):
    gameSet = requests.get('https://www.kovo.co.kr/media/popup_result.asp?season=016&g_part=201&r_round=5&g_num='+gameNum+'&r_set='+str(set),headers=headers)
    soupst = BeautifulSoup(gameSet.text, 'html.parser')

    serves = soupst.select('#onair_lst > ul > li > span')
    #print(serves)

    serveArr = []  # 세트별 문자중계 텍스트 담기

    for serve in serves:
        serveArr.append(serve.text.strip())
    #print(serveArr)
    
    # '서브'라는 텍스트가 포함된 태그들의 개수 구하기
    search = '서브'
    match_list = list()
    for word in serveArr:
        if search in word:
            match_list.append(word)

    count = len(match_list)
    serveCnt += count

    # ourTeam의 T/F 구하기
    scores = ''
    if teamOne.text == ourTeam:
        print('teamOne')
        scores = soupst.select('#onair_lst > ul > li > span.score_left')
    elif teamTwo.text == ourTeam:
        print('teamTwo')
        scores = soupst.select('#onair_lst > ul > li > span.score_right')

    print(scores)
    scoreArr = []

    for score in scores:
        if score.text.strip():
            scoreArr.append(score.text.strip())
    print(scoreArr)
    tfArr = []
    for i in range(0, len(scoreArr)):
        if i > 0:
            if(scoreArr[i-1]<scoreArr[i]):
                print('T')
                tfArr.append('T')
            else:
                print('F')
                tfArr.append('F')
    print(tfArr)
    AlltfArr += tfArr

    print(AlltfArr)

print(serveCnt)
print(len(AlltfArr))

# 세트별 선수 포지션 설정하기 (테스트)
# for ption in range(1, serveCnt + 1):
doc = {
    'gameDate': gameDate.text,  # 경기일자
    'ourTeam': ourTeam,  # 우리팀
    'opposeTeam': opposeTeam,  # 상대팀
    'ourTeamResult': ourTeamResult,  # 경기결과
    'tandf': AlltfArr[0],
    'position1': position1.text,  # 1번 포지션
    'position2': position2.text,  # 2번 포지션
    'position3': position3.text,  # 3번 포지션
    'position4': position4.text,  # 4번 포지션
    'position5': position5.text,  # 5번 포지션
    'position6': position6.text   # 6번 포지션
}

# MongoDB에 기초 데이터 저장하기
for i in range(1, len(AlltfArr) + 1):
    #print(doc)
    if '_id' in doc:
        del doc['_id']

    doc['tandf'] = AlltfArr[i-1]
    db.dbvolleyball.insert_one(doc)



    # position : 중복을 피하기 위한 더미 변수
    doc['position'] = doc['position1']
    doc['position1'] = doc['position2']
    doc['position2'] = doc['position3']
    doc['position3'] = doc['position4']
    doc['position4'] = doc['position5']
    doc['position5'] = doc['position6']
    doc['position6'] = doc['position']

#db.dbvolleyball.remove({});  # collection의 모든 데이터 삭제

# 예외사항 처리하기




    













# list 실습
############
a = [1, 2, 3, 4, 5]

#슬라이싱
a[1:3] # [2, 3]
a[::-1] # [5, 4, 3, 2, 1]
a[::2] # [1, 3, 5]

#정렬
a.sort() #오름차순 정렬
sorted(a, reverse=True) #내림차순 정렬

#2D 행렬
matrix = [[1, 2], [3, 4], [5, 6]]
cols = [row[1] for row in matrix] # [2, 4, 6]

#################
#dict,set,counter
#################
from collections import Counter, defaultdict

#counter : 빈도 집계
c = Counter(['서울', '부산', '서울', '대구','서울'])
c.most_common(1) # [('서울', 3)]


#defaultdict : 기본값이 있는 dict
group = defaultdict(list)
for row in rows:
    group[row['region']].append(row['sales'])

#set 연산
a = {'서울', '부산', '대구'}
b = {'서울', '인천'}
a & b # #교집합
a - b #차집합  {'부산', '대구'}

###############
#컴프리헨션 전체 패턴
################
#리스트
evens = [x for x in data if x % 2 == 0]
scaled = [x * 1.1 for x in prices]

#dict
word_len = {w: len(w) for w in words}
inv_map = {v: k for k, v in mapping.items()}

#set
regions = {row['region'] for row in rows}

#2D 행렬
flat = [x for row in matrix for x in row]

#조건부 값 변환
labels = ['정상' if x > 0 else '오류' for x in codes]


###########
generator
###########
#리스트 컴프리헨션과 유사하지만, 메모리를 절약

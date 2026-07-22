#실습1 자료구조 집계, 컴프리헨션, 제너레이터

##data
sales = [
    {"region": "서울", "category": "전자", "amount": 1500, "month": "2024-01"},
    {"region": "부산", "category": "의류", "amount": 800, "month": "2024-01"},
    {"region": "서울", "category": "의류", "amount": 1200, "month": "2024-02"},
    {"region": "대구", "category": "전자", "amount": 950, "month": "2024-01"},
    {"region": "서울", "category": "전자", "amount": 2100, "month": "2024-02"},
    {"region": "부산", "category": "전자", "amount": 650, "month": "2024-02"},
    {"region": "대구", "category": "의류", "amount": 1100, "month": "2024-02"},
    {"region": "인천", "category": "전자", "amount": 1350, "month": "2024-01"},
    {"region": "광주", "category": "의류", "amount": 720, "month": "2024-01"},
    {"region": "대전", "category": "전자", "amount": 1100, "month": "2024-03"},
    {"region": "울산", "category": "의류", "amount": 890, "month": "2024-02"},
    {"region": "세종", "category": "전자", "amount": 1400, "month": "2024-03"},
    {"region": "서울", "category": "식품", "amount": 450, "month": "2024-01"},
    {"region": "부산", "category": "식품", "amount": 380, "month": "2024-03"},
    {"region": "인천", "category": "의류", "amount": 950, "month": "2024-02"},
    {"region": "대구", "category": "식품", "amount": 510, "month": "2024-04"},
    {"region": "광주", "category": "전자", "amount": 1250, "month": "2024-02"},
    {"region": "대전", "category": "식품", "amount": 420, "month": "2024-01"},
    {"region": "울산", "category": "전자", "amount": 1750, "month": "2024-03"},
    {"region": "세종", "category": "의류", "amount": 680, "month": "2024-01"},
    {"region": "서울", "category": "전자", "amount": 1850, "month": "2024-03"},
    {"region": "부산", "category": "의류", "amount": 1050, "month": "2024-04"},
    {"region": "인천", "category": "식품", "amount": 620, "month": "2024-03"},
    {"region": "대구", "category": "전자", "amount": 1420, "month": "2024-03"},
    {"region": "광주", "category": "식품", "amount": 310, "month": "2024-04"},
    {"region": "대전", "category": "의류", "amount": 870, "month": "2024-02"},
    {"region": "울산", "category": "식품", "amount": 490, "month": "2024-01"},
    {"region": "세종", "category": "식품", "amount": 530, "month": "2024-02"},
    {"region": "서울", "category": "의류", "amount": 1600, "month": "2024-04"},
    {"region": "부산", "category": "전자", "amount": 920, "month": "2024-02"},
    {"region": "인천", "category": "전자", "amount": 2200, "month": "2024-04"},
    {"region": "대구", "category": "의류", "amount": 780, "month": "2024-01"},
    {"region": "광주", "category": "전자", "amount": 1050, "month": "2024-03"},
    {"region": "대전", "category": "의류", "amount": 1150, "month": "2024-04"},
    {"region": "울산", "category": "전자", "amount": 1300, "month": "2024-04"},
    {"region": "세종", "category": "전자", "amount": 1650, "month": "2024-04"},
    {"region": "서울", "category": "식품", "amount": 720, "month": "2024-02"},
    {"region": "부산", "category": "식품", "amount": 540, "month": "2024-04"},
    {"region": "인천", "category": "의류", "amount": 1300, "month": "2024-01"},
    {"region": "대구", "category": "전자", "amount": 1150, "month": "2024-04"},
    {"region": "광주", "category": "의류", "amount": 910, "month": "2024-03"},
    {"region": "대전", "category": "식품", "amount": 390, "month": "2024-02"},
    {"region": "울산", "category": "의류", "amount": 620, "month": "2024-03"},
    {"region": "세종", "category": "의류", "amount": 840, "month": "2024-03"},
    {"region": "서울", "category": "전자", "amount": 2500, "month": "2024-04"},
    {"region": "부산", "category": "전자", "amount": 1100, "month": "2024-01"},
    {"region": "인천", "category": "식품", "amount": 480, "month": "2024-04"},
    {"region": "대구", "category": "식품", "amount": 630, "month": "2024-02"},
    {"region": "광주", "category": "식품", "amount": 420, "month": "2024-01"},
    {"region": "대전", "category": "전자", "amount": 1480, "month": "2024-01"},
    {"region": "울산", "category": "식품", "amount": 510, "month": "2024-04"},
    {"region": "세종", "category": "식품", "amount": 600, "month": "2024-04"},
    {"region": "서울", "category": "의류", "amount": 1420, "month": "2024-03"},
    {"region": "부산", "category": "의류", "amount": 930, "month": "2024-03"},
    {"region": "인천", "category": "전자", "amount": 1600, "month": "2024-02"},
    {"region": "대구", "category": "의류", "amount": 1250, "month": "2024-03"},
    {"region": "광주", "category": "전자", "amount": 1380, "month": "2024-04"},
    {"region": "대전", "category": "의류", "amount": 790, "month": "2024-03"},
    {"region": "울산", "category": "전자", "amount": 1520, "month": "2024-02"},
    {"region": "세종", "category": "전자", "amount": 1200, "month": "2024-01"},
    {"region": "서울", "category": "식품", "amount": 580, "month": "2024-04"},
    {"region": "부산", "category": "전자", "amount": 1250, "month": "2024-04"},
    {"region": "인천", "category": "의류", "amount": 1100, "month": "2024-04"},
    {"region": "대구", "category": "전자", "amount": 1050, "month": "2024-02"},
    {"region": "광주", "category": "의류", "amount": 850, "month": "2024-02"},
    {"region": "대전", "category": "전자", "amount": 980, "month": "2024-04"},
    {"region": "울산", "category": "의류", "amount": 740, "month": "2024-01"},
    {"region": "세종", "category": "의류", "amount": 920, "month": "2024-04"},
    {"region": "서울", "category": "의류", "amount": 1350, "month": "2024-01"},
    {"region": "부산", "category": "식품", "amount": 410, "month": "2024-02"},
    {"region": "인천", "category": "전자", "amount": 1750, "month": "2024-03"},
    {"region": "대구", "category": "의류", "amount": 990, "month": "2024-04"},
    {"region": "광주", "category": "식품", "amount": 500, "month": "2024-02"},
    {"region": "대전", "category": "식품", "amount": 460, "month": "2024-04"},
    {"region": "울산", "category": "전자", "amount": 1100, "month": "2024-01"},
    {"region": "세종", "category": "식품", "amount": 370, "month": "2024-02"},
    {"region": "서울", "category": "전자", "amount": 2200, "month": "2024-01"},
    {"region": "부산", "category": "의류", "amount": 1150, "month": "2024-02"},
    {"region": "인천", "category": "식품", "amount": 530, "month": "2024-01"},
    {"region": "대구", "category": "전자", "amount": 1300, "month": "2024-03"},
    {"region": "광주", "category": "의류", "amount": 690, "month": "2024-04"},
    {"region": "대전", "category": "전자", "amount": 1250, "month": "2024-02"},
    {"region": "울산", "category": "의류", "amount": 820, "month": "2024-04"},
    {"region": "세종", "category": "전자", "amount": 1500, "month": "2024-02"},
    {"region": "서울", "category": "식품", "amount": 640, "month": "2024-03"},
    {"region": "부산", "category": "전자", "amount": 880, "month": "2024-03"},
    {"region": "인천", "category": "의류", "amount": 1200, "month": "2024-03"},
    {"region": "대구", "category": "식품", "amount": 480, "month": "2024-03"},
    {"region": "광주", "category": "전자", "amount": 1150, "month": "2024-01"},
    {"region": "대전", "category": "의류", "amount": 930, "month": "2024-01"},
    {"region": "울산", "category": "식품", "amount": 360, "month": "2024-02"},
    {"region": "세종", "category": "의류", "amount": 710, "month": "2024-02"},
    {"region": "서울", "category": "전자", "amount": 1950, "month": "2024-02"},
    {"region": "부산", "category": "의류", "amount": 870, "month": "2024-04"},
    {"region": "인천", "category": "전자", "amount": 1450, "month": "2024-02"},
    {"region": "대구", "category": "의류", "amount": 1050, "month": "2024-01"},
    {"region": "광주", "category": "식품", "amount": 390, "month": "2024-03"},
    {"region": "대전", "category": "전자", "amount": 1320, "month": "2024-03"},
    {"region": "울산", "category": "전자", "amount": 1600, "month": "2024-04"},
    {"region": "세종", "category": "식품", "amount": 420, "month": "2024-01"}
]


#======================
#1.리스트/딕셔너리 컴프리헨션
#======================

# amount가 1000 이상인 데이터만 필터링 
amount_1000 = [sale for sale in sales if sale['amount'] >= 1000] 

# 지역별 총 매출 dict를 컴프리헨션으로
region_list = {sale['region'] for sale in amount_1000} # 필터링 후 지역 set

# 지역별 합계
region_total = {
    region: sum(sale['amount'] for sale in amount_1000 if sale['region'] == region) for region in region_list
    }

# region_sales = {region: sum(sale['amount'] for sale in sales if sale['region'] == region) for region in set(sale['region'] for sale in sales)}
# print("지역별 합계 :", region_total)
# print("지역 목록 : ", region_list)



#======================
#2.counter, defaultdict
#======================
#import
from collections import Counter, defaultdict

#counter로 지역별 거래 건수
c = Counter(sale['region'] for sale in sales)
# print("지역별 거래 건수 : ",c)

#defaultdict로 카테고리별 amout 리스트
group = defaultdict(list)
for sale in sales:
    group[sale['category']].append(sale['amount'])
# print("카테고리별 매출 : ", group)




#======================
#3. 제너레이터 메모리 비교
#======================
# amount > 1000인 행만 yield하는 제너레이터
def filter_amount(sales):
    for sale in sales:
        if sale['amount'] > 1000:
            yield sale


#리스트 vs 제너레이터 메모리 비교
import sys
list_sales = [sale for sale in sales if sale['amount'] > 1000]
gen_sales = filter_amount(sales)
# print("list_sales 메모리:", sys.getsizeof(list_sales), "bytes") ##472bytes
# print("gen_sales 메모리:", sys.getsizeof(gen_sales), "bytes") ##208bytes


#==========================
#3. 종합 - 월별 카테고리 매출 집계
#==========================
#sales 데이터를 월별, 카테고리별로 그룹핑해 총매출 dict 완성
group = defaultdict(list)
for sale in sales:
    key = (sale['month'], sale['category'])
    group[key].append(sale['amount'])

# 월별, 카테고리별 총매출 계산
monthly_category_total = {key: sum(amounts) for key, amounts in group.items()}
top3 = sorted(monthly_category_total.items(), key=lambda x: x[1], reverse=True)[:3]

print("월별, 카테고리별 총매출 : ", monthly_category_total)
print("상위 3개 : ", top3)
# 실습 02 : 파일 I/O, 예외 처리, Pydantic 검증 파이프라인

작성일: 2026-07-20

Sales 데이터(`Python_Practice2_Data.json`)를 활용한 검증 파이프라인 실습.

## 내용

1. 예외 처리 + 파일 읽기 (`safe_load_csv`)
2. Pydantic v2 스키마 정의 (`SalesRecord`)
3. 검증 파이프라인 — raw 데이터를 valid / errors로 분리
4. 결과 파일 저장(CSV/JSON) + 재로딩 확인

## 실행

```bash
python "광주_1반_김하연.py"
```

mock 데이터(정상 4건 + 위반 3건)로 체크포인트를 검증한 뒤, 동일 파이프라인을 실제 데이터에도 적용한다.

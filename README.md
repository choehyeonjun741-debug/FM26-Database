# FM26-Database

FM26 스타일 축구 게임 데이터베이스 프로젝트.

## 구조

- `data/raw/` — 원본 데이터. 원칙적으로 수정하지 않음.
- `data/processed/` — 게임에서 사용할 정제 데이터.
- `data/releases/` — 버전별 배포 파일.
- `src/convert/` — CSV/원본 데이터를 JSON으로 변환.
- `src/validation/` — 선수·계약·이적·임대 데이터 검증.
- `src/database/` — 게임 데이터 로더 및 공통 DB 처리.
- `config/` — 스키마와 게임 설정.
- `docs/` — 데이터 구조 및 규칙 문서.

## 선수/계약 관계

선수의 현재 소속팀과 계약 보유팀을 분리한다.
임대 선수는 `players.current_club_id`와 `players.contract_club_id`를 통해 현재 팀과 원소속 계약팀을 구분한다.

실제 계약기간, 주급, 임대료, 선택/의무 완전이적 조건은 확인된 데이터만 입력하며 추정값을 넣지 않는다.

# FIN DINING Bull & Bear — 승인 템플릿 실행 규칙

이 파일은 상위 `bull-bear-market-automation/automation-prompt.md`와 함께 적용한다. 충돌하면 상위 프롬프트의 데이터·산출물 규칙을 우선하고, 이 파일의 시각 규칙을 승인 템플릿 규격으로 적용한다.

## 1. 날짜별 방향 선택

- 상위 프롬프트의 `MARKET PLATE RULE v1.0`으로 먼저 `bull` 또는 `bear`를 결정하고 `output/YYYY-MM-DD/<bull|bear>/` 하나만 만든다.
- 선택된 폴더에는 PNG 7장과 `caption.md`, `reels-script.md`, `story-copy.md`만 최종 보관한다.
- `bull`은 강세 테마 5개와 황소만, `bear`는 약세 테마 5개와 곰만 사용한다.
- KOSPI·KOSDAQ 등락률과 시장폭, 판정 단계, 기준 시각, 선택 방향을 `caption.md`에 기록한다.

## 2. 순위와 코스

테마 등락률 기준 1~5위를 아래 코스에 고정한다.

1. MAIN = 1위
2. SIGNATURE = 2위
3. STARTER = 3위
4. AMUSE BOUCHE = 4위
5. DESSERT = 5위

표지의 시각 순서는 `AMUSE BOUCHE → STARTER → SIGNATURE → MAIN → DESSERT`, 상세 카드와 파일 순서는 `MAIN → SIGNATURE → STARTER → AMUSE BOUCHE → DESSERT`다. 마지막 `TODAY'S MENU`는 같은 테마를 1~5위로 표시한다.

## 3. 승인 디자인

- `template/share.html`과 `content/sample-content.json`을 기준으로 당일 패키지별 `content.json`을 만든다.
- `meta.package`는 `bull`/`bear`, `meta.direction`은 `up`/`down`으로 넣고 각 코스에 대응 순위 `rank` 1~5를 넣는다.
- 표지 각 코스는 `코스명` / `테마명 · 등락률`의 2단 가운데 정렬이다.
- 상세 카드의 메타와 말풍선에 `강세/약세 N위`를 표시한다.
- 말풍선은 `방향·순위·테마` / `대표 종목·등락률` / `영향 요인`의 정확히 3줄이다.
- 승인된 흰 접시와 하단 `FIN DINING` 음각, 축소된 은색 포크·나이프, 크레용 질감 캐릭터를 유지한다.
- 상승 빨강 `#E23B35`, 하락 파랑 `#3569D4`, 웜 아이보리 배경 `#FBF8F2` 규칙을 지킨다.

## 4. 카드와 파일명

1. `01-cover.png`
2. `02-main.png`
3. `03-signature.png`
4. `04-starter.png`
5. `05-amuse-bouche.png`
6. `06-dessert.png`
7. `07-todays-menu.png`

모든 PNG는 1080×1350이며 카드 전체를 생성형 AI로 다시 그리지 않는다.

## 5. 검수

- PASS 1: 방향 판정값과 선택 결과, 선택 패키지의 사실, 기준시각, 순위, 영향 요인, 최근 5·20거래일 해설을 확인한다.
- PASS 2: 순위-코스 대응, 표지/상세 순서, 3줄 말풍선, 텍스트 오버플로, 1080×1350을 확인한다.
- PASS 3: 모바일 가독성, 식기·텍스트 위계, 캐릭터 간격과 색상 의미를 실제 PNG로 확인한다.

선택된 패키지가 세 PASS를 모두 통과하기 전에는 완료로 보고하지 않는다.

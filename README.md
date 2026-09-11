# FIN DINING by Finsight

금융·시장 정보를 인스타그램 캐러셀로 제작하는 콘텐츠 자동화 프로젝트입니다.

## 구성

- `fin-dining-instagram-automation-prompt-final.md`: 콘텐츠 제작 단일 기준
- `templates/render_adaptive_course.py`: v4.1 적응형 렌더러
- `templates/render_sector_course.py`: 주도 섹터 코스 렌더러 (메뉴판·접시·메뉴 보드)
- `scripts/fetch_sector_course.py`: FinSight 업종 랭킹 API → 주도 섹터 코스 원고
- `scripts/cutout_assets.py`: 원본 일러스트 → 투명 PNG 컷아웃
- `assets/`: 원본 일러스트, `templates/assets/`: 컷아웃한 셰프·식기 PNG
- `templates/templates-manifest.json`: 요일별 브랜드·레이아웃 매니페스트
- `templates/<day_key>/layout.json`: 요일별 색상·폰트·히어로 설정
- `templates/assets/`: 글자 없는 히어로 이미지
- `design-review/`: 디자인 검수 및 개선 기록

`outputs/`는 매번 다시 생성할 수 있으므로 Git에서 제외합니다. 게시용 PNG와 ZIP은 필요할 때 GitHub Release 또는 공유 드라이브에 올립니다.

## 환경

- Python 3.10 이상
- Pillow 10 이상
- 현재 폰트 설정은 macOS의 New York 및 Apple SD Gothic Neo 경로를 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 일일 코스 렌더링

먼저 `course-content.json`을 준비한 뒤 다음 명령을 실행합니다.

```bash
python3 templates/render_adaptive_course.py \
  outputs/YYYY-MM-DD_<day_key>/course-content.json \
  outputs/YYYY-MM-DD_<day_key>/
```

렌더러는 다음 파일을 생성합니다.

- 1080×1350 RGB 카드 PNG 5~7장
- `layout-plan.json`
- `layout-audit.json`
- 전체 미리보기
- 390px 모바일 미리보기

## 주도 섹터 코스 (FinSight 자동 수집)

FinSight(`trading-signal-frontend`)의 업종 랭킹 API에서 그날의 주도 섹터와 대장주를 받아
`course-content.json`을 만들고, `templates/render_sector_course.py`로 카드를 그립니다.

카드 구성은 커버(메뉴판) 1장 + 코스 순서대로 업종별 상승 종목 5장 + 오늘의 메뉴(업종 등락 랭킹) 1장,
총 7장입니다. 코스 자리는 요리의 무게 순서(AMUSE BOUCHE → MAIN → DESSERT)로 두고 등락 1위를 MAIN에
앉힙니다.

**이 코스는 오른 것만 다룹니다.** 내린 종목과 업종은 하락 테마를 따로 다루는 게시물의 몫이라 여기서는
싣지 않습니다. 그래서 해설하는 셰프는 늘 황소(BULL)입니다. 오른 업종이 5개에 못 미치면 스크립트가
중단합니다.

렌더러는 v4.1 적응형 렌더러(`render_adaptive_course.py`)와 별개입니다. 그쪽은 어두운 셸 위에
아키타입을 골라 얹는 편집형이고, 이쪽은 밝은 종이 위 파인다이닝 상차림이라 배경부터 카드 구성까지
공유하는 것이 없습니다. 요일 브랜드 색(`templates/<day>/layout.json`)만 함께 씁니다.

FinSight는 로그인 게이트 뒤에 있고, 구성종목 응답에 붙는 시가총액 보강은 종목이 많은 업종에서
BFF 10초 타임아웃을 넘겨 mock으로 떨어집니다. 코스에는 시가총액을 쓰지 않으므로 로컬 수집용
서버는 두 가지를 끄고 띄웁니다.

```bash
cd ../trading-signal-frontend
GOOGLE_OAUTH_CLIENT_ID= GOOGLE_OAUTH_CLIENT_SECRET= \
TOSS_CLIENT_ID= TOSS_CLIENT_SECRET= npm run dev
```

그다음 원고를 만들고 렌더합니다.

```bash
python3 scripts/fetch_sector_course.py outputs/YYYY-MM-DD_<day_key>/course-content.json
python3 templates/render_sector_course.py \
  outputs/YYYY-MM-DD_<day_key>/course-content.json \
  outputs/YYYY-MM-DD_<day_key>/
```

`--day-key`를 생략하면 게시일의 요일 템플릿을 씁니다. 배포본에서 받을 때는
`--base`와 세션 쿠키를 넘깁니다.

```bash
FINSIGHT_COOKIE="app_auth=<토큰>" python3 scripts/fetch_sector_course.py \
  outputs/.../course-content.json --base https://<배포 주소>
```

응답이 실데이터(`X-Data-Source: kis`)가 아니면 스크립트가 재시도하고, 그래도 mock이면
중단합니다. mock 숫자는 진짜와 구별되지 않아 게시물에 실리면 안 되기 때문입니다.
레이아웃만 확인할 때는 `--allow-mock`을 씁니다.

### 날짜는 게시일이 아니라 거래일입니다

카드와 원고에 적히는 날짜는 `/api/market/sectors` 응답의 `tradingDate`입니다. 주말이나 휴장일에
돌리면 응답 시각은 오늘이지만 숫자는 직전 영업일 종가라, 그 차이를 무시하면 "9월 6일에 올랐다" 같은
틀린 문장이 나갑니다. 업종 랭킹 TR에는 영업일 필드가 없어 FinSight 쪽
`lib/api/kis/tradingDate.ts`가 일자별 시세로 따로 조회합니다. 거래일이 없으면 스크립트가 중단합니다.

### 생성되는 파일

수집 스크립트가 `course-content.json`과 함께 게시용 원고를 만듭니다. 카드와 같은 데이터에서 나오므로
숫자가 어긋날 일이 없습니다.

| 파일 | 쓰는 곳 |
|---|---|
| `course-content.json` | 렌더러 입력. 이것만 있으면 카드를 몇 번이든 똑같이 다시 그립니다 |
| `instagram-caption.txt` | 게시물 본문. 그대로 복사해 붙입니다 |
| `reels-script.md` | 릴스 대본 22초. 화면 문구와 내레이션을 나눠 적습니다 |
| `story-poll.md` | 스토리 A/B 투표 문항 |

릴스와 스토리는 **텍스트 대본만** 만듭니다. 둘 다 9:16(1080×1920)이라 4:5 카드를 그대로 못 쓰고,
영상은 별도 편집이 필요합니다. 매번 올리는 것이 아니라면 대본으로 충분합니다. 9:16 이미지가 필요해지면
그때 렌더러에 추가하는 편이 낫습니다.

렌더러는 카드 PNG 7장과 전체 미리보기를 만듭니다.

### 캐릭터와 식기 에셋

원본 일러스트는 `assets/`에 두고, 배경을 지운 컷아웃을 `templates/assets/`에 둡니다.
컷아웃은 `scripts/cutout_assets.py`가 만듭니다.

```bash
python3 scripts/cutout_assets.py
```

| 원본 | 떼어내는 것 |
|---|---|
| `assets/fin-dining-chefs.png` | `chef-bear.png` · `chef-bull.png` |
| `assets/fin-dining-cutlery.png` | `cutlery-fork.png` · `cutlery-knife.png` |


| 파일 | 쓰임 |
|---|---|
| `chef-bull.png` | 상승을 해설하는 셰프. 이 코스에서는 늘 이쪽입니다 |
| `chef-bear.png` | 하락 담당. 커버에 함께 서고, 하락 테마 게시물에서 말합니다 |
| `cutlery-fork.png` · `cutlery-knife.png` | v1 일러스트 식기(이전 결과 재현용) |
| `fine-dining-silver-setting-v2.png` | v2 은식기·실버 차저·백자 플레이트 상차림 |

v2 커버는 다섯 업종을 같은 크기의 목록으로 놓지 않는다. 전채 2열, 시그니처 전환부, 확대된 MAIN
카르투슈, 디저트 순으로 실제 테이스팅 메뉴의 위계를 만들며 보조 코스 상승률은 은회색으로 낮춘다.

컷아웃은 테두리에서 flood fill로 배경을 지운 뒤 가장 큰 덩어리만 남기는 방식입니다. 캐릭터가 진한
윤곽선으로 닫혀 있어 채우기가 안쪽으로 들어가지 못하고, 떨어져 있는 장식(반짝이·하트)은 덩어리
선별에서 걸러집니다. 손에 든 도구와 발밑 그림자는 대상에 붙어 있어 함께 남습니다. 새 아트로 교체할
때는 스크립트의 `SOURCES`에서 잘라낼 영역만 고치면 됩니다.

## 협업 규칙

1. `main`에는 검수 완료 상태만 반영합니다.
2. 작업별 브랜치를 만든 뒤 Pull Request로 합칩니다.
3. 전체 카드와 글자를 생성형 AI로 한 번에 만들지 않습니다.
4. 텍스트·숫자·차트·출처는 렌더러로 합성합니다.
5. PASS 1 사실·원고, PASS 2 기술, PASS 3 시각 검수를 모두 통과해야 완료입니다.
6. API 키와 계정 정보는 커밋하지 않습니다.

자세한 제작 규칙은 `AGENTS.md`와 최종 자동화 프롬프트를 확인하세요.

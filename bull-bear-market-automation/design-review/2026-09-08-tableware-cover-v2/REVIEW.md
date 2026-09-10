# Bull & Bear 디자인 검수본 · 2026-09-08

이 폴더는 `bull-bear-market-automation` 원본을 수정하지 않고 만든 독립 검수본이다. 템플릿, 샘플 콘텐츠, 기존 캐릭터 4종과 자동화 지침을 함께 복사해 상대 경로만으로 확인할 수 있게 구성했다.

## 2026-09-09 사용자 피드백 반영

- 표지의 다섯 코스를 `코스명 · 업종명 · 등락률` 한 행 구조로 통일했다.
- 메뉴 묶음의 시작 위치를 아래로 내려 표지의 세로 중앙에 가깝게 조정했다.
- 2~7번 카드 말풍선을 항상 정확히 3줄로 고정했다: `업종 방향 요약` / `대표 종목과 등락률` / `상승·하락 영향 요인`.
- 각 코스와 랭킹 데이터에 `reason` 필드를 추가했으며, 확인되지 않은 인과를 단정하지 않도록 `기대`, `우려` 표현을 사용했다.
- 표지 코스 목록을 `코스명`과 `산업명·등락률`의 2단 중앙 정렬로 다시 구성하고 항목 사이에 가는 구분선을 추가했다.
- 하단 요약은 시장 방향 문장 뒤에서 강제 줄바꿈해 `9월 7일 코스입니다.`를 별도 중앙 행으로 표시했다.

## 적용 내용

- 기존 황소·곰 캐릭터 PNG는 픽셀 단위로 변경하지 않았다.
- CSS 원형 접시와 선형 SVG 포크·나이프를 제거했다.
- 캐릭터와 같은 검은 크레용 외곽선 및 회색 색연필 결을 가진 식기 세팅 PNG를 새로 적용했다.
- 식기 중앙은 종목명·현재가·등락률이 선명하게 읽히도록 흰색으로 정리했다.
- 표지는 2열 테이스팅 메뉴 구성으로 단순화하고 `MAIN`만 글자 크기와 얇은 구분선으로 강조했다.
- 표지 중앙 안내문은 테두리 말풍선 대신 작은 회색 설명과 한 줄 구분선만 사용했다.
- 최종 렌더는 기존 확정 게시물의 2026-09-07 종가·업종·종목 데이터를 사용했다. 게시글, 릴스, 스토리 원고도 검수본 `content/`에 함께 복사했다.

## 3회 디자인 검수

### PASS 1 · 캐릭터와 식기 질감

- 발견: 첫 생성본의 투명 배경이 체크무늬 픽셀로 렌더링되어 카드 배경과 충돌했다.
- 개선: 식기 형태와 크레용 질감은 유지하고 배경만 실제 알파 투명 PNG로 재추출했다.

### PASS 2 · 내용 가독성과 구성

- 발견: 새 접시의 안쪽 검은 링이 종목명과 등락률을 통과해 숫자 비교를 방해했다.
- 개선: 접시 중앙에 흰색 언더페인트를 두고 종목 열 너비를 38cqw로 조정해 모든 2~5개 종목 샘플을 링 안에 안정적으로 배치했다.

### PASS 3 · 표지 절제와 위계

- 발견: 코스를 동일한 한 줄 행으로 반복하면 메뉴판보다 목록표에 가까워지고, 장식이 많아질수록 `MAIN`의 중심성이 약해졌다.
- 개선: AMUSE BOUCHE와 STARTER를 2열로 묶고 SIGNATURE·MAIN·DESSERT를 중앙 축에 배치했다. MAIN은 크기만 키우고 장식은 얇은 상하선으로 제한했으며, 하단 안내 상자의 외곽선과 꼬리를 제거했다.

## 최종 에셋 생성 프롬프트

기본 생성에는 내장 이미지 생성 모드를 사용했다.

```text
Use case: stylized-concept
Asset type: transparent editorial illustration asset for the Bull & Bear Market Instagram card template
Primary request: Create one empty fine-dining place setting that matches the exact hand-drawn visual texture of the two reference chef characters, without including or altering any character.
Input images: the existing Bull and Bear chef PNGs are style references only for black crayon outline, slightly imperfect handmade contours, white fill, and restrained colored-pencil texture.
Scene/backdrop: genuinely transparent background, no table, no placemat, no shadow rectangle
Subject: a single large round white porcelain dinner plate viewed directly from above, a refined silver fork vertically on the left, and a refined silver dinner knife vertically on the right
Style/medium: simple children's editorial illustration, softly uneven black wax-crayon outlines and sparse gray colored-pencil hatching, matching the reference characters; elegant but friendly, not photorealistic
Composition/framing: square canvas; plate centered; fork and knife parallel and evenly spaced; ample transparent padding; the center of the plate stays visually quiet for dynamic market text
Color palette: white porcelain, graphite black outline, cool neutral silver-gray only; no red or blue
Text: none
Constraints: no characters, food, logo, letters, numbers, extra utensils, gold, 3D rendering, or glossy chrome reflections
```

배경 재추출에서는 식기와 선을 그대로 유지하고 체크무늬 배경만 실제 투명 알파로 바꾸도록 지정했다.

## 확인 파일

- 최종 템플릿: `template/share.html`
- 최종 식기 에셋: `assets/bull-bear-place-setting-v2.png`
- 7장 렌더 검수본: `preview/01-cover.png`부터 `preview/07-card.png`
- 9월 7일 원고: `content/caption.md`, `content/reels-script.md`, `content/story-copy.md`

# FIN DINING project instructions

이 폴더의 기본 브랜드와 콘텐츠 자동화 기준은 `FIN DINING by Finsight`다.

사용자가 `오늘 코스 만들어줘`, `오늘의 코스 만들어줘`, `오늘 FIN DINING 만들어줘`, `오늘 게시물 만들어줘` 또는 같은 의미로 요청하면 다음을 수행한다.

1. `fin-dining-instagram-automation-prompt-final.md`를 처음부터 끝까지 읽는다.
2. `templates/templates-manifest.json`과 당일 `layout.json`을 읽어 브랜드 토큰을 불러온다.
3. 해당 최종 프롬프트에 따라 최신 정보 조사, 팩트체크, 정보량에 맞는 실제 카드 PNG 5~7장, 게시글, 릴스, 스토리 원고를 생성하고 출처를 확인한다.
4. 전체 카드를 생성형 AI로 다시 그리지 않는다. `templates/render_adaptive_course.py`를 사용해 승인된 컴포지션 패밀리 안에서 레이아웃을 선택하고 텍스트·데이터·도형을 코드로 합성한다. `templates/render_daily_course.py`는 v3 재현용으로만 사용한다. 주도 섹터 코스(FinSight 업종 랭킹 기반)는 `templates/render_sector_course.py`를 쓴다 — 밝은 파인다이닝 상차림이라 v4.1과 시각 체계를 공유하지 않는다.
5. PASS 1 사실·원고, PASS 2 템플릿·기술, PASS 3 시각·폰트 검수를 모두 통과할 때까지 완료로 보고하지 않는다.

최종 검수를 통과한 뒤 당일 결과 폴더에는 게시물 사진과 원고만 남긴다. 필요한 출처는 원고에 포함하며, 조사 자료·HTML·JSON·검수 기록·미리보기·이전 버전 등 중간 산출물은 삭제한다. ZIP 등 압축파일은 만들지 않는다. 이 최종 정리 규칙은 개별 제작 프롬프트의 산출물 목록보다 우선한다. 공용 템플릿·캐릭터·자동화 소스는 보존한다.

주 6코스는 월요일부터 토요일까지이며 일요일은 사용자의 별도 지시가 없으면 게시물을 만들지 않는다.

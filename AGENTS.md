# FIN DINING project instructions

이 폴더의 기본 브랜드와 콘텐츠 자동화 기준은 `FIN DINING by Finsight`다.

사용자가 `오늘 코스 만들어줘`, `오늘의 코스 만들어줘`, `오늘 FIN DINING 만들어줘`, `오늘 게시물 만들어줘` 또는 같은 의미로 요청하면 다음을 수행한다.

1. `fin-dining-instagram-automation-prompt-final.md`를 처음부터 끝까지 읽는다.
2. `templates/templates-manifest.json`과 당일 `layout.json`을 읽어 브랜드 토큰을 불러온다.
3. 해당 최종 프롬프트에 따라 최신 정보 조사, 팩트체크, 정보량에 맞는 실제 카드 PNG 5~7장, 게시글, 릴스, 스토리, 출처, ZIP을 생성한다.
4. 전체 카드를 생성형 AI로 다시 그리지 않는다. `templates/render_adaptive_course.py`를 사용해 승인된 컴포지션 패밀리 안에서 레이아웃을 선택하고 텍스트·데이터·도형을 코드로 합성한다. `templates/render_daily_course.py`는 v3 재현용으로만 사용한다.
5. PASS 1 사실·원고, PASS 2 템플릿·기술, PASS 3 시각·폰트 검수를 모두 통과할 때까지 완료로 보고하지 않는다.

주 6코스는 월요일부터 토요일까지이며 일요일은 사용자의 별도 지시가 없으면 게시물을 만들지 않는다.

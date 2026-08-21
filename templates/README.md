# FIN DINING by Finsight — 월–토 마스터 템플릿

한 주는 6개 코스로 구성되며, 각 코스는 7장 인스타그램 캐러셀이다. 프로필 그리드에서는 3개씩 두 줄로 한 주 세트가 완성된다.

| 폴더 | 코스 | 주제 |
|---|---|---|
| `mon-policy` | COURSE 01 | 정책 |
| `tue-global` | COURSE 02 | 글로벌 |
| `wed-market` | COURSE 03 | 국내시장 |
| `thu-industry` | COURSE 04 | 산업 |
| `fri-weekly` | COURSE 05 | 주간결산 |
| `sat-preview` | COURSE 06 | 다음 주 프리뷰 |

각 요일 폴더에는 다음 파일이 있다.

- `01_cover_master.png`~`07_cta_master.png`: 매주 재사용하는 고정 마스터
- `layout.json`: 슬롯·색상·폰트·해시 명세
- `<day_key>-preview.png`: 샘플 문구를 넣은 7장 미리보기

공통 파일:

- `templates-manifest.json`: 6개 템플릿의 단일 기준
- `render_master_templates.py`: 마스터를 새 버전으로 다시 만드는 원본 렌더러
- `render_daily_course.py`: 구조화 원고를 고정 마스터에 합성하는 일일 렌더러
- `verify_templates.py`: 3회 재렌더링·해시·크기·폰트 검수
- `all-weekday-master-preview.png`: 월–토 표지 3×2 그리드

일상적인 게시물 제작에서는 마스터 렌더러를 실행하지 않는다. `render_daily_course.py`에 `course-content.json`을 전달해 날짜·원고·데이터만 합성한다.

현재 마스터 버전은 `v3`다. 다크 배경용 `accent`와 밝은 카드용 `accentInk`를 분리해 작은 글자도 WCAG AA 4.5:1 이상의 대비를 확보한다. 배경에는 결정론적 미세 질감을 넣고 카드 라운드와 그림자는 절제해 금융 에디토리얼 인상을 유지한다.

폰트는 New York과 Apple SD Gothic Neo를 사용한다. 영문 디스플레이는 28px, 한글 본문은 30px, 면책·출처는 24px 미만으로 줄이지 않으며, 넘치는 문구는 축약 후 다시 렌더링한다.

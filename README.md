# FIN DINING by Finsight

금융·시장 정보를 인스타그램 캐러셀로 제작하는 콘텐츠 자동화 프로젝트입니다.

## 구성

- `fin-dining-instagram-automation-prompt-final.md`: 콘텐츠 제작 단일 기준
- `templates/render_adaptive_course.py`: v4.1 적응형 렌더러
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

## 협업 규칙

1. `main`에는 검수 완료 상태만 반영합니다.
2. 작업별 브랜치를 만든 뒤 Pull Request로 합칩니다.
3. 전체 카드와 글자를 생성형 AI로 한 번에 만들지 않습니다.
4. 텍스트·숫자·차트·출처는 렌더러로 합성합니다.
5. PASS 1 사실·원고, PASS 2 기술, PASS 3 시각 검수를 모두 통과해야 완료입니다.
6. API 키와 계정 정보는 커밋하지 않습니다.

자세한 제작 규칙은 `AGENTS.md`와 최종 자동화 프롬프트를 확인하세요.

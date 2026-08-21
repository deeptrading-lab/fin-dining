# FIN DINING 템플릿 디자인 검수 — v2 → v3

- 검수일: 2026-08-21 KST
- 범위: 월~토 6개 요일 × 7장, 마스터 42장, 오늘 실제 카드 7장
- 판정: 브랜드 방향 유지, 접근성·타이포 위계·카드 디테일 개선

## 트렌드 판정

현재의 다크 에디토리얼, 절제된 세리프, 촉각적인 3D 오브젝트는 2026년의 clean layout·serif·simple branding·tactile texture 흐름과 맞아 전면 교체하지 않았다. 금융 콘텐츠 특성상 과도한 스크랩북·핸드메이드 효과는 신뢰도를 낮출 수 있어 적용하지 않았다.

- Canva 2026 Design Trends: https://www.canva.com/newsroom/news/design-trends-2026/
- Adobe 2026 Creative Trends: https://business.adobe.com/uk/resources/creative-trends-report.html
- W3C WCAG 2.2 Contrast Minimum: https://www.w3.org/TR/WCAG22/#contrast-minimum

## 개선 내용

1. 색상
   - 배경 `#11100F` → `#131210`, 종이 `#FFFBF4` → `#F8F3EA`로 조정해 순흑·순백 대비의 피로를 완화했다.
   - 다크 배경용 `accent`와 밝은 카드용 `accentInk`를 분리했다.
   - 6개 요일 모두 포인트 텍스트 대비를 4.88~9.00:1 범위로 확보했다.
2. 타이포그래피
   - 본문을 실제 Apple SD Gothic Neo Regular로 변경했다.
   - 본문 30→32px, 작은 본문 28→30px, 면책 22→24px, 제목 52→56px, 표지 62→66px로 상향했다.
   - New York 최소 크기를 26→28px로 올렸다.
3. 카드와 표면
   - 카드 라운드 28→18px, 그림자 오프셋 12→8px, 불투명도 95→58로 줄였다.
   - 밝은 카드의 윤곽선을 2→1px로 줄여 SaaS UI보다 편집 지면에 가까운 인상으로 바꿨다.
   - 다크 배경에 결정론적 미세 그레인을 추가해 과도하게 매끈한 AI 이미지 느낌을 줄였다.
4. 운영 안정성
   - 템플릿 ID와 manifest를 v3로 갱신했다.
   - 일일 렌더러와 최종 자동화 프롬프트의 폰트·색상 규칙을 함께 갱신했다.

## 3회 검수

### ROUND 1 · 디자인 시스템 — PASS

- 6개 요일의 `accent / background`, `accentInk / paper` 대비를 계산했다.
- 최저 대비는 수요일 밝은 카드의 4.88:1로 WCAG AA 4.5:1을 통과한다.
- 디스플레이 28px, 본문 30px, 면책 24px 최소값이 모든 layout에 동일하게 선언됐다.

### ROUND 2 · 실제 카드 — PASS

- 오늘 원고를 v3 금요일 마스터에 다시 합성했다.
- 7장 모두 1080×1350 RGB이며 제목·본문·차트·CTA·출처의 잘림이 없다.
- 카드 6의 기회·리스크 한 줄 정렬과 카드 7의 출처·CTA 대비를 개별 확인했다.

### ROUND 3 · 모바일 축소 — PASS

- 390px 피드 폭으로 7장을 축소해 제목 위계, 본문 행간, 숫자·차트 레이블을 확인했다.
- 표지 후크와 카드 제목은 즉시 식별되고, 본문과 면책은 경계를 넘지 않는다.
- 42개 마스터는 3회 재렌더링에서 동일한 SHA-256을 유지했다.

세 라운드 모두 PASS. v3를 새 운영 기본값으로 사용한다.

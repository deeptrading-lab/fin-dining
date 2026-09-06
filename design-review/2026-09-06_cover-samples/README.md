# 주도 섹터 코스 시각 개편 · 2026-09-06

v4.1(어두운 셸 + 편집형 아키타입)에서 밝은 파인다이닝 상차림으로 바꾼 과정의 기록이다.
`build*.py` 는 결정 과정에서 쓴 HTML 시안 생성기이고, `plate_proto.py` 는 Pillow 이식 시제품이다.
확정 결과는 `templates/render_sector_course.py` 에 들어갔다.

시안 PNG·HTML 은 커밋하지 않는다. 스크립트를 돌리면 다시 나온다(레포 규칙: 재생성 가능한 산출물은
Git에서 제외).

```bash
python3 design-review/2026-09-06_cover-samples/build9.py       # 확정 시안 3종 HTML
python3 design-review/2026-09-06_cover-samples/plate_proto.py   # 접시 카드 Pillow 시제품
```

두 스크립트 모두 `outputs/<날짜>_<day_key>/course-content.json` 을 읽어 그날 실데이터로 시안을 만든다.
`outputs/` 는 Git에서 제외되므로, 먼저 `scripts/fetch_sector_course.py` 로 원고를 받아 두어야 한다.

HTML 시안은 Chrome 헤드리스로 찍었다.

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --hide-scrollbars --force-device-scale-factor=1 --window-size=1080,1350 \
  --screenshot=out.png "file://$PWD/final-cover.html"
```

## 무엇을 왜 골랐나

| 결정 | 고른 것 | 이유 |
|---|---|---|
| 커버 형식 | 정통 메뉴판(A1) | 참조한 파인다이닝 메뉴판에 가장 가깝다. 코스 리스트·접시 커버·미니멀 타이틀은 탈락 |
| 코스 자리 | 크레센도 배치 | 코스명은 요리의 무게 순서인데 업종은 등락 순위라 위계가 어긋났다. 인쇄 순서는 그대로 두고 MAIN에 1위를 앉혀 4위→3위→2위→1위→5위로 읽히게 했다 |
| FISH 자리 | SIGNATURE | FISH는 재료를 지시해 업종명 위에 얹으면 엉뚱한 뜻이 붙는다. SECOND COURSE는 설명문처럼 튀고, INTERMEZZO는 원래 가벼운 요리라 2위가 앉기엔 무게가 거꾸로다 |
| 종이 | `#FDFAF4` | 한 단계 더 밝히면 종이 질감이 빠지면서 테두리가 상대적으로 진해 보인다 |
| 접시 | 물결 타원 + 금색 문양 띠 | 테두리 한 겹짜리 타원은 그냥 도형으로 보였다. 그릇이 그릇으로 읽히는 이유는 가장자리 금선과 림을 도는 반복 문양이다. 정원보다 타원이 다섯 줄에 폭을 더 준다 |
| 식기 | 컷아웃 사용 | 선으로 직접 그리니 캐릭터 일러스트와 화풍이 어긋났다 |
| 랭킹 10행 | 접시 대신 보드 | 원 안에 열 줄을 넣으면 줄마다 쓸 수 있는 폭이 달라져 글자 크기를 맞출 수 없다 |
| 등락 색 | 요일 accent와 분리 | 등락은 뜻이 고정된 값이라 요일마다 색이 달라지면 의미가 흐려진다. 요일 색은 MAIN 라벨과 태그라인에만 남겼다 |

## 이식하며 걸린 것

- **New York 폰트에 한글 글리프가 없다.** 브라우저는 폴백하지만 Pillow는 빈 네모를 그린다.
  한글이 섞이는 자리는 전부 Apple SD Gothic Neo로 그린다.
- **하이픈이 안 찍힌다.** New York에서 `-` 의 폭은 잡히는데 글리프가 그려지지 않는다(재현 확인).
  자간 넓은 대문자라 빼도 읽혀 `AMUSE BOUCHE` 로 뒀다.
- **숫자 폭이 제각각이다.** Apple SD Gothic Neo의 `1` 이 좁아 우측 정렬만으로는 값이 세로로 늘어설 때
  끝이 어긋난다. OpenType `tnum` 은 이 Pillow 빌드에 libraqm이 없어 못 쓴다. 0~9 최대 폭을 슬롯으로
  삼는 `draw_tabular` 로 처리했다.
- **말풍선 꼬리 이음매.** 몸통과 꼬리를 따로 그리면 테두리가 맞닿는 자리에 선이 남는다. 한 마스크에
  함께 칠하고 안쪽을 깎아낸 차이만 테두리로 쓴다.
- **하단이 밀려났다.** 세로 흐름에 얹으면 위 내용이 길어질 때 바닥글이 프레임 밖으로 나간다.
  카드가 1080×1350 고정이므로 `SLOTS` 의 절대 좌표에 박았다.

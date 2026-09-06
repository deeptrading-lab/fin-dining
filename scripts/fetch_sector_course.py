#!/usr/bin/env python3
"""FinSight 업종 랭킹 API → FIN DINING 주도 섹터 코스 원고.

`지금 뜨는 산업`(`/api/market/sectors`)과 상위 업종의 구성종목
(`/api/market/sectors/<code>/constituents`)을 읽어 7장짜리 코스를 만든다.

  01 cover  메뉴판 — 코스 다섯 자리에 1~5위 업종
  02~06 dish 코스 순서대로 업종별 대장주 5종목
  07 board  오늘의 메뉴 — 업종 등락 랭킹 상위 10

렌더는 `templates/render_sector_course.py` 가 맡는다.

    python3 scripts/fetch_sector_course.py outputs/2026-09-06_sat-preview/course-content.json
    python3 templates/render_sector_course.py <위 파일> outputs/2026-09-06_sat-preview/

FinSight 는 로그인 게이트 뒤에 있고, 구성종목의 시가총액 보강은 종목이 많은 업종에서 BFF 10초
타임아웃을 넘겨 mock 으로 떨어진다. 코스는 시가총액을 쓰지 않으므로 로컬 수집용 서버는 둘 다 끄고 띄운다.

    cd ../trading-signal-frontend
    GOOGLE_OAUTH_CLIENT_ID= GOOGLE_OAUTH_CLIENT_SECRET= \\
    TOSS_CLIENT_ID= TOSS_CLIENT_SECRET= npm run dev

배포본에서 받을 때는 `--base` 와 세션 쿠키(`FINSIGHT_COOKIE`)를 넘긴다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

# 요일별 브랜드 템플릿 (templates-manifest.json `week`). 일요일은 코스를 만들지 않는다.
DAY_KEYS = ["mon-policy", "tue-global", "wed-market", "thu-industry", "fri-weekly", "sat-preview"]

BOARD_COUNT = 10       # 마지막 보드에 싣는 업종 수.
DETAIL_SECTORS = 5     # 접시 카드를 만들 상위 업종 수.
STOCKS_PER_SECTOR = 5

RETRIES = 3
# 구성종목 호출은 KIS 등락률 순위 + 시가총액 배치라 무겁다. 연달아 부르면 상류 레이트리밋에 걸려
# BFF 10초 타임아웃 → mock 으로 떨어진다. 하루 한 번 도는 스크립트이므로 속도보다 실데이터가 우선이다.
RETRY_WAIT_SECONDS = 20.0
PACING_SECONDS = 12.0

# 코스는 요리의 무게 순서 그대로, 자리에 앉는 업종만 등락 순위로 정한다. 인쇄 순서를 따라 읽으면
# 4위 → 3위 → 2위 → 1위(MAIN)로 올라갔다가 5위로 가볍게 닫힌다.
COURSE_PLAN = [("AMUSE BOUCHE", 3), ("STARTER", 2), ("SIGNATURE", 1), ("MAIN", 0), ("DESSERT", 4)]

WEEKDAYS = "월화수목금토일"


def request_once(base: str, path: str, timeout: float) -> tuple[dict, str]:
    request = urllib.request.Request(base.rstrip("/") + path)
    cookie = os.environ.get("FINSIGHT_COOKIE")
    if cookie:
        request.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), response.headers.get("X-Data-Source", "?")
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise SystemExit(
                f"{path} 401 — FinSight 로그인 게이트에 막혔습니다. FINSIGHT_COOKIE 를 설정하세요."
            ) from error
        raise SystemExit(f"{path} {error.code} {error.reason}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"{path} 연결 실패 — {error.reason}. dev 서버가 떠 있는지 확인하세요.") from error


def fetch(base: str, path: str, timeout: float, allow_mock: bool = False) -> dict:
    """실데이터(`X-Data-Source: kis`)만 통과시킨다.

    BFF 는 KIS 타임아웃·레이트리밋을 never-throw 로 흡수해 **mock 을 200 으로** 돌려준다. 그 숫자는
    진짜와 구별되지 않으므로 게시물에 실리면 안 된다. 연속 호출이 초당 한도에 걸린 것뿐인 경우가 많아,
    실패하면 간격을 두고 다시 부르고 그래도 mock 이면 중단한다.
    """
    for attempt in range(RETRIES):
        body, source = request_once(base, path, timeout)
        if source == "kis" or allow_mock:
            return body
        if attempt + 1 < RETRIES:
            print(f"{path} → {source}, {RETRY_WAIT_SECONDS:g}초 후 재시도", file=sys.stderr)
            time.sleep(RETRY_WAIT_SECONDS)
    raise SystemExit(
        f"{path} 가 실데이터를 주지 않았습니다 (X-Data-Source: {source}). "
        "장중이 아니거나 KIS 한도에 걸렸을 수 있습니다. 검수용이면 --allow-mock 을 쓰세요."
    )


def signed(value: float) -> str:
    return f"{value:+.2f}%"


def dish_dialogue(sector: dict, stocks: list[dict]) -> list:
    """접시 카드의 대사를 데이터에서 만든다.

    이 코스는 오른 것만 다룬다. 내린 종목은 하락 테마를 따로 다루는 게시물의 몫이라 여기서는 언급하지
    않는다. 그래서 말하는 셰프는 늘 황소다(곰은 하락 게시물에서 나온다).

    조사는 쓰지 않는다. 종목명 뒤 조사는 받침에 따라 갈리는데("케이씨텍이" / "키다리스튜디오가")
    영문·숫자로 끝나는 이름(NHN·DKME·TYM)은 규칙 자체가 애매하다. 이름을 쉼표 앞에 두면 조사가 사라진다.
    """
    lead = stocks[0]
    return [
        (sector["name"], "name"), (" 종목 ", "body"), (f"{sector['total']}개", "body"),
        (" 가운데 ", "body"), (f"{sector['up']}개", "up"), ("가 올랐어요. 가장 크게 오른 건 ", "body"),
        (lead["name"], "name"), (", ", "body"), (signed(lead["changePct"]), "up"), ("입니다.", "body"),
    ]


def write_copy(payload: dict, out_dir: Path) -> list[Path]:
    """게시에 필요한 원고를 카드와 같은 데이터에서 만들어 저장한다.

    카드는 숫자를 보여 주고 캡션은 그 숫자를 문장으로 푼다. 둘이 같은 `course-content.json` 에서
    나오므로 어긋날 일이 없다. 릴스·스토리는 텍스트 대본만 만든다 — 영상과 스토리 이미지는 9:16 이라
    카드(4:5)를 그대로 못 쓰고, 매번 올리는 것이 아니라면 대본만으로 충분하다.
    """
    cover = payload["cards"][0]
    dishes = [c for c in payload["cards"] if c["kind"] == "dish"]
    board = payload["cards"][-1]
    trade = date.fromisoformat(payload["trading_date"])
    day_label = f"{trade.month}월 {trade.day}일 {WEEKDAYS[trade.weekday()]}요일"
    lead = cover["courses"][[c["main"] for c in cover["courses"]].index(True)]
    basis = f"{trade.year}년 {trade.month}월 {trade.day}일 장 마감 기준 (한국투자증권)"

    lines = [
        f"{day_label}, 오른 업종 다섯을 코스로 담았습니다.",
        "",
        f"메인은 {lead['name']}, {lead['pct']}입니다.",
        "",
    ]
    # 숫자 뒤 조사는 읽는 소리의 받침에 따라 갈린다(10 = "십" 이라 "10은"). 단위 "개"를 붙이면
    # 받침이 없어 조사가 하나로 고정되므로, 규칙을 구현하는 대신 어형으로 피한다.
    pct_by_sector = {c["name"]: c["pct"] for c in cover["courses"]}
    for dish in dishes:
        top = dish["rows"][0]
        lines.append(f"· {dish['course']}  {dish['sector']} {pct_by_sector[dish['sector']]}")
        lines.append(f"  {dish['breadth']} · 가장 크게 오른 건 {top['name']} {top['pct']}")
    lines += [
        "",
        f"오른 업종 상위 {len(board['rows'])}개는 마지막 장에 담았습니다. "
        "저장해 두고 다음 코스와 비교해 보세요.",
        "",
        "정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 않습니다.",
        "",
        "자료 기준일",
        f"· KOSPI 업종 등락·종목 시세: {basis}",
    ]
    caption = "\n".join(lines) + "\n"

    second = cover["courses"][[c["label"] for c in cover["courses"]].index("SIGNATURE")]
    top_dish = next(d for d in dishes if d["course"] == "MAIN")
    reels = f"""# FIN DINING 릴스 · {payload['date']} 주도 섹터

총 길이 22초. 화면 문구와 내레이션을 분리한다. 영상 편집은 별도로 한다.

## 0~4초 · 후크

- 화면: `{day_label} 주도 섹터`
- 내레이션: {day_label}, 가장 크게 오른 업종은 {lead['name']}입니다.

## 4~9초 · 메인

- 화면: `{lead['name']} {lead['pct']}`
- 내레이션: {top_dish['breadth']}. 가장 크게 오른 건 {top_dish['rows'][0]['name']}, {top_dish['rows'][0]['pct']}입니다.

## 9~15초 · 나머지 코스

- 화면: `{' · '.join(c['name'] + ' ' + c['pct'] for c in cover['courses'] if not c['main'])}`
- 내레이션: 뒤이어 {second['name']}가 {second['pct']}로 따라붙었습니다.

## 15~19초 · 전체

- 화면: `오른 업종 {len(board['rows'])}개`
- 내레이션: 오른 업종 상위 {len(board['rows'])}개를 순서대로 정리했습니다.

## 19~22초 · CTA

- 화면: `내일 코스도 같은 시간`
- 내레이션: 저장해 두고 다음 코스와 비교해 보세요.
"""

    options = [c for c in cover["courses"] if c["label"] in ("MAIN", "SIGNATURE")]
    story = f"""# FIN DINING 스토리 투표 · {payload['date']}

질문: {day_label} 코스 중 더 관심 가는 섹터는?

- 선택지 A: `{options[1]['name']}` ({len(options[1]['name'])}자)
- 선택지 B: `{options[0]['name']}` ({len(options[0]['name'])}자)

두 선택지 모두 12자 이내여야 한다(인스타 투표 스티커 제한). 투표는 1개만 게시한다.
스토리 하단에 기준일을 함께 적는다 — {basis}
"""

    written = []
    for name, body in (("instagram-caption.txt", caption),
                       ("reels-script.md", reels),
                       ("story-poll.md", story)):
        path = out_dir / name
        path.write_text(body, encoding="utf-8")
        written.append(path)
    return written


def build(base: str, day: date, day_key: str, timeout: float, allow_mock: bool) -> dict:
    ranking = fetch(base, "/api/market/sectors", timeout, allow_mock)
    sectors = ranking.get("sectors", [])
    if len(sectors) < DETAIL_SECTORS:
        raise SystemExit(f"업종이 {len(sectors)}개뿐이라 코스를 만들 수 없습니다 (최소 {DETAIL_SECTORS}개).")

    # 게시일이 아니라 **거래일**을 쓴다. 주말·휴장일에 돌리면 응답 시각은 오늘이지만 숫자는 직전
    # 영업일 종가다. 그 차이를 무시하면 "9월 6일에 올랐다" 같은 틀린 문장이 나간다.
    if ranking.get("tradingDate"):
        trade_day = date.fromisoformat(ranking["tradingDate"])
    elif allow_mock:
        # mock 은 어느 영업일의 값도 아니라 거래일이 null 이다. 레이아웃 확인용이므로 게시일로 대신하되,
        # 이 결과가 게시물로 나가면 안 된다는 점을 눈에 띄게 남긴다.
        print("경고: 거래일이 없어 게시일을 대신 씁니다 (--allow-mock). 게시물에 쓰지 마세요.",
              file=sys.stderr)
        trade_day = day
    else:
        raise SystemExit("응답에 거래일(tradingDate)이 없습니다. 날짜 없이 게시물을 만들지 않습니다.")
    day_label = f"{trade_day.month}월 {trade_day.day}일 {WEEKDAYS[trade_day.weekday()]}요일"
    foot_left = f"{trade_day.year} · {trade_day.month:02d} · {trade_day.day:02d} 종가 기준"

    risen_sectors = [s for s in sectors if s["changePct"] > 0]
    if len(risen_sectors) < DETAIL_SECTORS:
        raise SystemExit(
            f"오른 업종이 {len(risen_sectors)}개뿐입니다 (코스에 {DETAIL_SECTORS}개 필요). "
            "하락 우위 장은 별도 게시물로 다뤄야 합니다."
        )
    top = risen_sectors[:DETAIL_SECTORS]
    lead = top[0]

    cover = {
        "kind": "cover",
        "tagline": "오늘의 산업 코스",
        "courses": [
            {"label": label, "name": top[i]["name"], "pct": signed(top[i]["changePct"]),
             "main": label == "MAIN"}
            for label, i in COURSE_PLAN
        ],
        "dialogue": [
            (f"{day_label} 주도 섹터 다섯 코스, 지금 나갑니다. 메인은 ", "body"),
            (lead["name"], "name"), (", ", "body"), (signed(lead["changePct"]), "up"), ("입니다.", "body"),
        ],
        "footer_left": foot_left,
        "footer_right": "KOSPI 업종 등락",
    }

    dishes = []
    for label, index in COURSE_PLAN:
        sector = top[index]
        time.sleep(PACING_SECONDS)
        payload = fetch(base, f"/api/market/sectors/{sector['code']}/constituents", timeout, allow_mock)
        # 오른 종목만 싣는다. 보합(0.00%)도 상승이 아니므로 뺀다.
        risen = [s for s in payload.get("constituents", []) if s["changePct"] > 0]
        stocks = risen[:STOCKS_PER_SECTOR]
        # 접시 표는 두 줄부터 성립한다. 오른 종목이 모자란 업종은 카드를 만들지 않는다.
        if len(stocks) < 2:
            print(f"경고: {sector['name']} 상승 종목 {len(stocks)}개 — 카드를 건너뜁니다", file=sys.stderr)
            continue
        dialogue = dish_dialogue(sector, stocks)
        dishes.append({
            "kind": "dish",
            "course": label,
            "sector": sector["name"],
            "breadth": f"{sector['total']}개 중 {sector['up']}개 상승" if sector["total"] else "",
            "rows": [
                {"name": s["name"], "price": f"{s['price']:,}", "pct": signed(s["changePct"])}
                for s in stocks
            ],
            "chef": "BULL",
            "dialogue": dialogue,
            "footer_left": foot_left,
            "footer_right": f"오른 종목 {len(stocks)}개",
        })

    # 보드도 오른 업종만 싣는다. 상승분이 BOARD_COUNT 에 못 미치면 있는 만큼만 나간다.
    board_rows = [s for s in sectors if s["changePct"] > 0][:BOARD_COUNT]
    if not board_rows:
        raise SystemExit("오른 업종이 없습니다. 상승 코스를 만들 수 없습니다.")
    board = {
        "kind": "board",
        "title": "지금 뜨는 산업",
        "breadth": f"오른 업종 상위 {len(board_rows)}",
        "rows": [{"name": s["name"], "pct": signed(s["changePct"])} for s in board_rows],
        "chef": "BULL",
        "dialogue": [
            ("오늘 오른 업종 ", "body"), (f"{len(board_rows)}개", "up"),
            ("를 순서대로 담았어요. 1위는 ", "body"), (lead["name"], "name"), (", ", "body"),
            (signed(lead["changePct"]), "up"), ("입니다.", "body"),
        ],
        "footer_left": foot_left,
        "footer_right": "출처 한국투자증권",
    }

    return {
        "date": day.isoformat(),
        "trading_date": trade_day.isoformat(),
        "day_key": day_key,
        "topic": f"{lead['name']} 주도 섹터",
        "cards": [cover, *dishes, board],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="FinSight 업종 랭킹 → FIN DINING 주도 섹터 코스")
    parser.add_argument("out", type=Path, help="생성할 course-content.json 경로")
    parser.add_argument("--base", default=os.environ.get("FINSIGHT_BASE", "http://localhost:3000"))
    parser.add_argument("--date", default=date.today().isoformat(), help="게시일 YYYY-MM-DD (기본 오늘)")
    parser.add_argument("--day-key", choices=DAY_KEYS, help="브랜드 템플릿 (기본 --date 의 요일)")
    parser.add_argument("--timeout", type=float, default=90.0, help="요청 타임아웃 초 (기본 90)")
    parser.add_argument("--allow-mock", action="store_true",
                        help="레이아웃 검수 전용 — mock 응답도 받는다. 게시물에는 쓰지 말 것")
    args = parser.parse_args()

    day = date.fromisoformat(args.date)
    if args.day_key:
        day_key = args.day_key
    elif day.weekday() >= len(DAY_KEYS):
        raise SystemExit("일요일은 코스를 만들지 않습니다. --day-key 로 템플릿을 직접 지정하세요.")
    else:
        day_key = DAY_KEYS[day.weekday()]

    payload = build(args.base, day, day_key, args.timeout, args.allow_mock)
    if args.allow_mock:
        print("주의: --allow-mock — 숫자가 실데이터가 아닐 수 있습니다", file=sys.stderr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    copies = write_copy(payload, args.out.parent)
    print(f"{args.out} · {len(payload['cards'])}장 · {day_key} · 거래일 {payload['trading_date']}")
    for path in copies:
        print(f"  {path.name}")


if __name__ == "__main__":
    main()

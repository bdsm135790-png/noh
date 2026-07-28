"""실시간 지역 기상정보: 지명/좌표로 현재 날씨를 불러온다.

소방·군집 드론 운용에서 바람·기온·습도는 화재 확산과 비행 안전을 좌우한다.
이 모듈은 무료·무인증(API key 불필요) Open-Meteo 서비스를 사용해
- 지명 → 좌표(geocoding)
- 좌표 → 현재 기상(current weather)
를 조회하고, 소방 관점의 화재기상 위험도까지 산출한다.

외부 의존성 없이 표준 라이브러리(urllib)만 사용한다. 네트워크 장애 시에는
예외를 던지므로 호출 측에서 try/except 로 방어하거나 캐시를 사용한다.

좌표계·단위
-----------
- 기온: 섭씨(°C), 습도: 상대습도(%), 강수: mm.
- 풍속: m/s, 풍향: 바람이 불어오는 방향(기상학 관례, 0=북, 90=동).

사용 예
-------
>>> from weather import get_weather
>>> w = get_weather("서울")          # 지명으로 조회
>>> print(w.summary())
>>> w2 = get_weather(lat=37.57, lon=126.98)  # 좌표로 조회
"""

import json
import math
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_TIMEOUT = 10.0  # 초

# WMO weather interpretation code → 한글 설명(주요 코드).
_WMO_CODE = {
    0: "맑음",
    1: "대체로 맑음", 2: "부분적으로 흐림", 3: "흐림",
    45: "안개", 48: "상고대 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비",
    66: "약한 어는 비", 67: "강한 어는 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈", 77: "싸락눈",
    80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    85: "약한 눈 소나기", 86: "강한 눈 소나기",
    95: "뇌우", 96: "약한 우박 뇌우", 99: "강한 우박 뇌우",
}


@dataclass
class WeatherInfo:
    """한 지점의 현재 기상 관측값."""

    name: str                 # 지역 이름(geocoding 결과 또는 좌표 문자열)
    latitude: float
    longitude: float
    temperature: float        # °C
    humidity: float           # %
    wind_speed: float         # m/s
    wind_direction: float     # deg (바람이 불어오는 방향)
    precipitation: float      # mm
    weather_code: int         # WMO code
    observed_at: str          # ISO8601 관측 시각
    raw: dict = field(default_factory=dict, repr=False)  # 원본 응답

    @property
    def description(self):
        """WMO 코드의 한글 날씨 설명."""
        return _WMO_CODE.get(self.weather_code, f"알 수 없음({self.weather_code})")

    @property
    def wind_cardinal(self):
        """풍향을 8방위 한글로 변환(N/NE/E...를 북/북동/동...)."""
        dirs = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"]
        idx = int((self.wind_direction % 360) / 45.0 + 0.5) % 8
        return dirs[idx]

    def fire_weather_risk(self):
        """화재기상 위험도를 (등급, 점수 0~100)로 산출한다.

        고온·저습·강풍은 화재 확산을 가속한다. 강수가 있으면 위험을 낮춘다.
        간이 지표로, 정식 FWI(Fire Weather Index)를 대체하지 않는다.
        """
        # 각 요소를 0~1로 정규화.
        temp_f = _clamp((self.temperature - 15.0) / 25.0, 0.0, 1.0)   # 15→40°C
        dry_f = _clamp((60.0 - self.humidity) / 60.0, 0.0, 1.0)       # 습도 낮을수록↑
        wind_f = _clamp(self.wind_speed / 15.0, 0.0, 1.0)            # 0→15 m/s
        rain_f = _clamp(self.precipitation / 5.0, 0.0, 1.0)          # 강수 완화

        score = 100.0 * (0.35 * temp_f + 0.30 * dry_f + 0.35 * wind_f)
        score *= (1.0 - 0.7 * rain_f)  # 비가 오면 최대 70% 경감
        score = _clamp(score, 0.0, 100.0)

        if score >= 75:
            level = "위험"
        elif score >= 50:
            level = "경계"
        elif score >= 25:
            level = "주의"
        else:
            level = "안전"
        return level, round(score, 1)

    def summary(self):
        """사람이 읽기 좋은 한 줄 요약."""
        level, score = self.fire_weather_risk()
        return (
            f"[{self.name}] {self.description} · 기온 {self.temperature:.1f}°C · "
            f"습도 {self.humidity:.0f}% · 바람 {self.wind_cardinal} {self.wind_speed:.1f} m/s · "
            f"강수 {self.precipitation:.1f} mm · 화재위험 {level}({score}) · "
            f"관측 {self.observed_at}"
        )


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _http_get_json(url, params, timeout=DEFAULT_TIMEOUT):
    """URL + 쿼리 파라미터로 GET 요청 후 JSON을 파싱해 반환한다."""
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(full_url, headers={"User-Agent": "noh-drone/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode(place, count=1, timeout=DEFAULT_TIMEOUT):
    """지명을 위도/경도로 변환한다.

    Parameters
    ----------
    place : str
        지역 이름(예: "서울", "부산", "Seoul").
    count : int
        받아올 후보 개수.

    Returns
    -------
    dict
        {"name", "latitude", "longitude", "country", ...}

    Raises
    ------
    ValueError
        검색 결과가 없을 때.
    """
    data = _http_get_json(
        GEOCODE_URL,
        {"name": place, "count": count, "language": "ko", "format": "json"},
        timeout=timeout,
    )
    results = data.get("results")
    if not results:
        raise ValueError(f"지명을 찾을 수 없습니다: {place!r}")
    return results[0]


def get_weather(place=None, lat=None, lon=None, timeout=DEFAULT_TIMEOUT):
    """실시간 현재 기상정보를 조회한다.

    지명(``place``) 또는 좌표(``lat``, ``lon``) 중 하나로 조회한다. 지명을 주면
    먼저 geocoding 으로 좌표를 구한 뒤 현재 기상을 가져온다.

    Parameters
    ----------
    place : str, optional
        지역 이름. ``lat``/``lon`` 미지정 시 필수.
    lat, lon : float, optional
        위도/경도. ``place`` 대신 사용.
    timeout : float
        HTTP 타임아웃(초).

    Returns
    -------
    WeatherInfo

    Raises
    ------
    ValueError
        인자가 부족하거나 지명 검색이 실패했을 때.
    urllib.error.URLError
        네트워크/서버 오류.
    """
    if lat is None or lon is None:
        if not place:
            raise ValueError("place 또는 (lat, lon) 중 하나는 반드시 지정해야 합니다.")
        geo = geocode(place, timeout=timeout)
        lat, lon = geo["latitude"], geo["longitude"]
        name = geo.get("name", place)
    else:
        name = place or f"({lat:.4f}, {lon:.4f})"

    data = _http_get_json(
        FORECAST_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ]),
            "wind_speed_unit": "ms",
            "timezone": "auto",
        },
        timeout=timeout,
    )

    cur = data.get("current")
    if not cur:
        raise ValueError(f"기상 데이터를 받지 못했습니다: {name!r}")

    return WeatherInfo(
        name=name,
        latitude=float(data.get("latitude", lat)),
        longitude=float(data.get("longitude", lon)),
        temperature=float(cur.get("temperature_2m", math.nan)),
        humidity=float(cur.get("relative_humidity_2m", math.nan)),
        wind_speed=float(cur.get("wind_speed_10m", math.nan)),
        wind_direction=float(cur.get("wind_direction_10m", math.nan)),
        precipitation=float(cur.get("precipitation", 0.0)),
        weather_code=int(cur.get("weather_code", -1)),
        observed_at=str(cur.get("time", "")),
        raw=data,
    )


if __name__ == "__main__":  # 간단 CLI: python3 weather.py [지명]
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "서울"
    try:
        info = get_weather(query)
        print(info.summary())
    except Exception as exc:  # noqa: BLE001 - CLI에서는 사용자에게 메시지만 보여준다
        print(f"기상정보 조회 실패: {exc}")
        sys.exit(1)

"""weather 모듈 동작 검증 테스트(네트워크 없이 실행).

실제 HTTP 호출은 하지 않고, ``weather._http_get_json`` 을 가짜 응답으로
대체(monkeypatch)해 파싱·위험도 로직만 검증한다.
"""

import weather
from weather import WeatherInfo, get_weather, geocode


def _sample(**over):
    base = dict(
        name="테스트시", latitude=37.0, longitude=127.0,
        temperature=20.0, humidity=50.0, wind_speed=3.0,
        wind_direction=90.0, precipitation=0.0, weather_code=0,
        observed_at="2026-07-28T12:00",
    )
    base.update(over)
    return WeatherInfo(**base)


def test_description_and_wind_cardinal():
    w = _sample(weather_code=61, wind_direction=90.0)
    assert w.description == "약한 비"
    assert w.wind_cardinal == "동"
    # 경계값: 350도는 북(0)으로 반올림.
    assert _sample(wind_direction=350.0).wind_cardinal == "북"


def test_unknown_weather_code():
    assert "알 수 없음" in _sample(weather_code=1234).description


def test_fire_risk_high_when_hot_dry_windy():
    hot = _sample(temperature=40.0, humidity=10.0, wind_speed=15.0)
    level, score = hot.fire_weather_risk()
    assert level == "위험"
    assert score >= 75


def test_fire_risk_low_when_cool_wet_calm():
    mild = _sample(temperature=12.0, humidity=90.0, wind_speed=0.5)
    level, score = mild.fire_weather_risk()
    assert level == "안전"
    assert score < 25


def test_rain_reduces_risk():
    dry = _sample(temperature=38.0, humidity=15.0, wind_speed=12.0, precipitation=0.0)
    wet = _sample(temperature=38.0, humidity=15.0, wind_speed=12.0, precipitation=5.0)
    assert wet.fire_weather_risk()[1] < dry.fire_weather_risk()[1]


def test_summary_contains_key_fields():
    s = _sample(name="서울").summary()
    assert "서울" in s
    assert "화재위험" in s


def test_get_weather_by_coords(monkeypatch):
    """좌표로 조회 시 geocoding 없이 forecast 응답을 파싱한다."""
    def fake_get(url, params, timeout=weather.DEFAULT_TIMEOUT):
        assert url == weather.FORECAST_URL
        return {
            "latitude": 37.5, "longitude": 127.0,
            "current": {
                "time": "2026-07-28T12:00",
                "temperature_2m": 31.2,
                "relative_humidity_2m": 28.0,
                "precipitation": 0.0,
                "weather_code": 1,
                "wind_speed_10m": 6.5,
                "wind_direction_10m": 225.0,
            },
        }

    monkeypatch.setattr(weather, "_http_get_json", fake_get)
    w = get_weather(lat=37.5, lon=127.0)
    assert w.temperature == 31.2
    assert w.wind_cardinal == "남서"
    assert w.description == "대체로 맑음"


def test_get_weather_by_place_uses_geocode(monkeypatch):
    """지명으로 조회 시 geocode → forecast 순으로 호출한다."""
    calls = []

    def fake_get(url, params, timeout=weather.DEFAULT_TIMEOUT):
        calls.append(url)
        if url == weather.GEOCODE_URL:
            return {"results": [{"name": "부산", "latitude": 35.1, "longitude": 129.0}]}
        return {
            "latitude": 35.1, "longitude": 129.0,
            "current": {
                "time": "2026-07-28T12:00", "temperature_2m": 25.0,
                "relative_humidity_2m": 60.0, "precipitation": 1.0,
                "weather_code": 3, "wind_speed_10m": 2.0, "wind_direction_10m": 0.0,
            },
        }

    monkeypatch.setattr(weather, "_http_get_json", fake_get)
    w = get_weather("부산")
    assert calls == [weather.GEOCODE_URL, weather.FORECAST_URL]
    assert w.name == "부산"
    assert w.description == "흐림"


def test_missing_args_raises():
    try:
        get_weather()
    except ValueError:
        pass
    else:  # pragma: no cover
        assert False, "인자 미지정 시 ValueError 를 던져야 한다"


def test_geocode_no_result_raises(monkeypatch):
    monkeypatch.setattr(weather, "_http_get_json", lambda *a, **k: {"results": []})
    try:
        geocode("없는지명xyz")
    except ValueError:
        pass
    else:  # pragma: no cover
        assert False, "결과 없음 시 ValueError 를 던져야 한다"


if __name__ == "__main__":
    # pytest 없이도 실행 가능하도록 최소 러너 제공.
    import types

    class _MP:
        def __init__(self):
            self._undo = []

        def setattr(self, obj, name, val):
            self._undo.append((obj, name, getattr(obj, name)))
            setattr(obj, name, val)

        def undo(self):
            for obj, name, val in reversed(self._undo):
                setattr(obj, name, val)
            self._undo.clear()

    passed = 0
    for fname, fn in sorted(globals().items()):
        if fname.startswith("test_") and isinstance(fn, types.FunctionType):
            mp = _MP()
            try:
                if "monkeypatch" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                    fn(mp)
                else:
                    fn()
                print(f"  ok  {fname}")
                passed += 1
            finally:
                mp.undo()
    print(f"\n{passed} passed")

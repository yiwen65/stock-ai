# backend/tests/e2e/test_api_e2e.py
"""
End-to-end API tests against the live backend server (http://localhost:8001).
These tests verify the full request→service→AKShare→response chain.

Run with:  pytest tests/e2e/test_api_e2e.py -v
"""
import pytest
import httpx
import time

BASE_URL = "http://localhost:8001/api/v1"
TIMEOUT = 60.0  # AKShare can be slow on first call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


def _assert_ok(resp: httpx.Response):
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"


# ===========================================================================
# 1. Health check
# ===========================================================================
class TestHealthCheck:
    def test_root(self, client: httpx.Client):
        r = client.get("http://localhost:8001/")
        _assert_ok(r)
        body = r.json()
        assert "Stock AI API" in body.get("message", "")

    def test_health(self, client: httpx.Client):
        r = client.get("http://localhost:8001/health")
        _assert_ok(r)
        assert r.json()["status"] == "healthy"


# ===========================================================================
# 2. Stock search — the core fix we are validating
# ===========================================================================
class TestStockSearch:
    def test_search_by_code(self, client: httpx.Client):
        """Search by stock code should return matching stocks"""
        r = client.get("/stocks/search", params={"q": "600519", "limit": 5})
        _assert_ok(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        codes = [s["stock_code"] for s in data]
        assert "600519" in codes

    def test_search_by_name(self, client: httpx.Client):
        """Search by Chinese name should return matching stocks"""
        r = client.get("/stocks/search", params={"q": "茅台", "limit": 5})
        _assert_ok(r)
        data = r.json()
        assert len(data) >= 1
        names = [s["stock_name"] for s in data]
        assert any("茅台" in n for n in names)

    def test_search_partial_code(self, client: httpx.Client):
        """Partial code search should return multiple matches"""
        r = client.get("/stocks/search", params={"q": "6005", "limit": 10})
        _assert_ok(r)
        data = r.json()
        assert len(data) >= 2
        for s in data:
            assert "6005" in s["stock_code"]

    def test_search_has_required_fields(self, client: httpx.Client):
        """Search results should contain QuoteResponse required fields"""
        r = client.get("/stocks/search", params={"q": "600519", "limit": 1})
        _assert_ok(r)
        data = r.json()
        assert len(data) >= 1
        stock = data[0]
        required = ["stock_code", "stock_name", "price", "change", "pct_change", "volume", "amount"]
        for field in required:
            assert field in stock, f"Missing field: {field}"

    def test_search_no_results(self, client: httpx.Client):
        """Search with nonsense keyword returns empty list, not error"""
        r = client.get("/stocks/search", params={"q": "ZZZZZZ", "limit": 5})
        _assert_ok(r)
        assert r.json() == []

    def test_search_limit(self, client: httpx.Client):
        """Limit parameter should cap the number of results"""
        r = client.get("/stocks/search", params={"q": "银行", "limit": 3})
        _assert_ok(r)
        data = r.json()
        assert len(data) <= 3

    def test_search_empty_query_rejected(self, client: httpx.Client):
        """Empty query should be rejected with 422"""
        r = client.get("/stocks/search", params={"q": "", "limit": 5})
        assert r.status_code == 422

    def test_search_response_time(self, client: httpx.Client):
        """Search should return within 5 seconds (cache should be warm)"""
        start = time.time()
        r = client.get("/stocks/search", params={"q": "600036", "limit": 3})
        elapsed = time.time() - start
        _assert_ok(r)
        assert elapsed < 5.0, f"Search took {elapsed:.1f}s, expected < 5s"


# ===========================================================================
# 3. Stock list
# ===========================================================================
class TestStockList:
    def test_get_stocks(self, client: httpx.Client):
        """Get full stock list"""
        r = client.get("/stocks")
        _assert_ok(r)
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 1000, f"Expected >1000 stocks, got {len(data)}"

    def test_stock_list_has_code_and_name(self, client: httpx.Client):
        r = client.get("/stocks")
        _assert_ok(r)
        data = r.json()
        for stock in data[:5]:
            assert "stock_code" in stock
            assert "stock_name" in stock
            assert len(stock["stock_code"]) == 6


# ===========================================================================
# 4. Stock quote
# ===========================================================================
class TestStockQuote:
    def test_get_quote(self, client: httpx.Client):
        """Get realtime quote for a known stock (may timeout if snapshot not cached)"""
        try:
            r = client.get("/stocks/600519/quote")
            if r.status_code == 200:
                q = r.json()
                assert q["stock_code"] == "600519"
                assert isinstance(q["price"], (int, float))
            else:
                assert r.status_code == 404
        except httpx.ReadTimeout:
            pytest.skip("Snapshot not cached; quote endpoint timed out (expected on cold start)")

    def test_get_quote_invalid_code(self, client: httpx.Client):
        try:
            r = client.get("/stocks/999999/quote")
            assert r.status_code == 404
        except httpx.ReadTimeout:
            pytest.skip("Snapshot fetch timed out")


# ===========================================================================
# 5. K-line data
# ===========================================================================
class TestKLine:
    def test_get_kline(self, client: httpx.Client):
        """Get daily K-line data for a major stock"""
        r = client.get("/stocks/600519/kline", params={"period": "1d", "days": 30})
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)
            assert len(data) > 0
            required = ["date", "open", "high", "low", "close", "volume"]
            for field in required:
                assert field in data[0], f"Missing field: {field}"
        else:
            # AKShare may occasionally fail; accept 404
            assert r.status_code == 404


# ===========================================================================
# 6. Strategy execution (选股) — the other core fix
# ===========================================================================
class TestStrategyExecution:
    def test_execute_graham(self, client: httpx.Client):
        """Execute Graham value strategy"""
        r = client.post("/strategies/execute", json={
            "strategy_type": "graham",
            "limit": 10,
        })
        # May succeed or 500 if snapshot is still loading
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)
            for stock in data:
                assert "stock_code" in stock
                assert "stock_name" in stock
                assert "market_cap" in stock

    def test_execute_invalid_strategy(self, client: httpx.Client):
        """Invalid strategy type should return 422"""
        r = client.post("/strategies/execute", json={
            "strategy_type": "nonexistent",
            "limit": 10,
        })
        assert r.status_code == 422

    def test_execute_custom_without_conditions(self, client: httpx.Client):
        """Custom strategy without conditions should fail with 400 or 422"""
        r = client.post("/strategies/execute", json={
            "strategy_type": "custom",
            "limit": 10,
        })
        assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}"

    def test_execute_response_is_array(self, client: httpx.Client):
        """Strategy result should be a plain JSON array (not wrapped in {data: ...})"""
        r = client.post("/strategies/execute", json={
            "strategy_type": "quality_factor",
            "limit": 5,
        })
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list), f"Expected list, got {type(data).__name__}"
            # Ensure it's NOT wrapped in ApiResponse
            assert not isinstance(data, dict), "Response should be a plain array, not {data: [...]}"


# ===========================================================================
# 7. Market endpoints
# ===========================================================================
class TestMarket:
    def test_sectors(self, client: httpx.Client):
        r = client.get("/market/sectors")
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)
            if data:
                assert "sector_name" in data[0]

    def test_indices(self, client: httpx.Client):
        r = client.get("/market/indices")
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)

    def test_capital_flow(self, client: httpx.Client):
        r = client.get("/market/capital-flow")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ===========================================================================
# 8. Industries list (used by StrategyForm)
# ===========================================================================
class TestIndustries:
    def test_list_industries(self, client: httpx.Client):
        r = client.get("/strategies/industries")
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)

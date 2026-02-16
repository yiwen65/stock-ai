
import akshare as ak
import time

def test_code_name():
    print("Testing stock_info_a_code_name...")
    start = time.time()
    try:
        df = ak.stock_info_a_code_name()
        print(f"CodeName success: {len(df)} rows in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"CodeName failed: {e}")

def test_spot():
    print("Testing stock_zh_a_spot_em...")
    start = time.time()
    try:
        # Requesting a small subset or just checking connection speed
        df = ak.stock_zh_a_spot_em()
        print(f"Spot success: {len(df)} rows in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Spot failed: {e}")

if __name__ == "__main__":
    test_code_name()
    test_spot()

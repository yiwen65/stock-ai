
import akshare as ak
import time

def test_sh():
    print("Testing SH...")
    start = time.time()
    try:
        df = ak.stock_info_sh_name_code()
        print(f"SH success: {len(df)} rows in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"SH failed: {e}")

def test_sz():
    print("Testing SZ...")
    start = time.time()
    try:
        df = ak.stock_info_sz_name_code()
        print(f"SZ success: {len(df)} rows in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"SZ failed: {e}")

if __name__ == "__main__":
    test_sh()
    test_sz()

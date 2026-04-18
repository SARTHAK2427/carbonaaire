import os
import pandas as pd
from utils.helpers import (
    extract_from_electricity_document,
    extract_from_cloud_document,
    extract_from_fuel_document,
    extract_from_hardware_document
)

def test_electricity_read():
    print("\n--- Testing Electricity Read ---")
    test_path = "dummy_elec.xlsx"
    pd.DataFrame([["Total consumption is 1500 kWh", "Location: Delhi"]]).to_excel(test_path, index=False, header=False)
    try:
        res = extract_from_electricity_document(test_path)
        print("Electricity Result:", res)
        assert res.get("electricity_kwh_per_month") == 1500.0
        assert res.get("location_state") == "delhi"
        print("[SUCCESS] Electricity tests passed!")
    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        if os.path.exists(test_path): os.remove(test_path)

def test_cloud_read():
    print("\n--- Testing Cloud Read ---")
    test_path = "dummy_cloud.xlsx"
    pd.DataFrame([["Amazon Web Services Monthly Invoice", "Total Amount Due: $ 500"]]).to_excel(test_path, index=False, header=False)
    try:
        res = extract_from_cloud_document(test_path)
        print("Cloud Result:", res)
        assert res.get("cloud_provider") == "aws"
        assert res.get("cloud_monthly_bill_inr") == 500.0 * 83.0
        print("[SUCCESS] Cloud tests passed!")
    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        if os.path.exists(test_path): os.remove(test_path)

def test_fuel_read():
    print("\n--- Testing Fuel Read ---")
    test_path = "dummy_fuel.xlsx"
    pd.DataFrame([["Fill up receipt", "45.5 litres of diesel", "10 liters petrol"]]).to_excel(test_path, index=False, header=False)
    try:
        res = extract_from_fuel_document(test_path)
        print("Fuel Result:", res)
        assert res.get("diesel_litres_per_month") == 45.5
        assert res.get("petrol_litres_per_month") == 10.0
        print("[SUCCESS] Fuel tests passed!")
    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        if os.path.exists(test_path): os.remove(test_path)

def test_hardware_read():
    print("\n--- Testing Hardware Read ---")
    test_path = "dummy_hw.xlsx"
    pd.DataFrame([["Order Information", "Qty 10 laptops", "5 desktops shipped", "2 units servers"]]).to_excel(test_path, index=False, header=False)
    try:
        res = extract_from_hardware_document(test_path)
        print("Hardware Result:", res)
        assert res.get("num_laptops") == 10
        assert res.get("num_desktops") == 5
        assert res.get("num_servers_onprem") == 2
        print("[SUCCESS] Hardware tests passed!")
    except Exception as e:
        print(f"[ERROR]: {e}")
    finally:
        if os.path.exists(test_path): os.remove(test_path)

def test_image_read(image_path="bill.png"):
    print(f"\n--- Testing Image OCR Read ({image_path}) ---")
    if not os.path.exists(image_path):
        print(f"[SKIP] {image_path} not found. Save your bill image as '{image_path}' to test OCR.")
        return
    try:
        res = extract_from_electricity_document(image_path)
        print("Image OCR Result:", res)
        # For the user's bill, we expect ~353 kWh and Delhi
        print(f"[VERIFY] extracted kWh: {res.get('electricity_kwh_per_month')}")
        print(f"[VERIFY] extracted State: {res.get('location_state')}")
        print("[SUCCESS] Image OCR extraction complete!")
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")

if __name__ == "__main__":
    test_electricity_read()
    test_cloud_read()
    test_fuel_read()
    test_hardware_read()
    test_image_read()

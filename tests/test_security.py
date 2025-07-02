import requests
import os
import json

BASE_URL = "http://localhost:8000"
ADMIN_CREDS = {"username": "admin", "password": "admin123"}

def run_tests():
    # 1. Проверка базового эндпоинта
    print("1. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json() == {"status": "API is working"}
    print("✅ Root endpoint works")

    # 2. Тест аутентификации
    print("\n2. Testing authentication...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data=ADMIN_CREDS,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"❌ Auth failed: {response.status_code} {response.text}")
        return
    
    token = response.json()["access_token"]
    print(f"✅ Auth success. Token: {token[:15]}...")

    # 3. Тест защищенного эндпоинта
    print("\n3. Testing secure endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/secure-data", headers=headers)
    assert response.status_code == 200
    assert "secret" in response.json()["data"]
    print("✅ Secure endpoint works")

    # 4. Тест админского эндпоинта
    print("\n4. Testing admin endpoint...")
    response = requests.post(
        f"{BASE_URL}/admin/update-model",
        headers=headers
    )
    assert response.status_code == 200
    assert "Модель обновлена" in response.json()["message"]
    print("✅ Admin endpoint works")

    # 5. Тест предсказания
    print("\n5. Testing prediction endpoint...")
    try:
        # Подготовка тестовых данных (реальные параметры модели)
        test_features = [
            10, 3, 1, 0.0, 2021, 60, 2, 1, 1, 3, 2, 1, 1, 50, 7, 12, 5, 77, 
            77317, 2, 1, 0, 6, 48.60, 2.89, 17, 2, 1
            ]
        
        response = requests.post(
            f"{BASE_URL}/predict",
            json={"features": test_features}
        )
        
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}") 
        
        if response.status_code == 200:
            print(f"✅ Prediction success. Result: {response.json()}")
        else:
            print(f"❌ Prediction failed. Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Prediction test error: {str(e)}")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
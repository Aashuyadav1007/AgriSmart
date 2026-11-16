import io
from pathlib import Path
from fastapi.testclient import TestClient
from app import app, load_all_models

load_all_models()
client = TestClient(app)

print("=" * 60)
print("STARTING COMPREHENSIVE STAGE 1-3 TEST SUITE")
print("=" * 60)

# Test 1: Health & Root
r_health = client.get('/health')
assert r_health.status_code == 200
h = r_health.json()
print('[TEST 1] /health check:', h)
assert h['rf_model_loaded'] is True
assert h['tf_model_loaded'] is True
assert h['disease_model_loaded'] is True
assert h['metrics_available'] is True

# Test 2: Dual Yield Prediction
payload = {
    'Region': 'North',
    'Soil_Type': 'Loam',
    'Crop': 'Wheat',
    'Rainfall_mm': 650.0,
    'Temperature_Celsius': 23.5,
    'Weather_Condition': 'Sunny',
    'Fertilizer_Used': True,
    'Irrigation_Used': True,
    'Days_to_Harvest': 120
}
r_yield = client.post('/api/yield/predict', json=payload)
assert r_yield.status_code == 200
y = r_yield.json()
print('[TEST 2] /api/yield/predict:')
print('  RF:', y['predictions']['random_forest'])
print('  TF:', y['predictions']['tensorflow_dnn'])
print('  Consensus:', y['predictions']['ensemble_consensus'])
assert y['predictions']['ensemble_consensus']['model_agreement_percentage'] > 90

# Test 3: Legacy contract preservation
r_legacy = client.post('/predict', json=payload)
assert r_legacy.status_code == 200
print('[TEST 3] Preserved legacy /predict:', r_legacy.json())

# Test 4: Disease Classes Endpoint
r_classes = client.get('/api/disease/classes')
assert r_classes.status_code == 200
c = r_classes.json()
print('[TEST 4] /api/disease/classes total:', c['total_classes'])
assert c['total_classes'] == 8

# Test 5: Disease Detection with Real PlantVillage Leaf Image
sample_leaf = list(Path('data/plantvillage_dataset/Potato___Early_blight').glob('*.JPG'))[0]
print(f'[TEST 5] Testing real leaf image: {sample_leaf.name}')
with open(sample_leaf, 'rb') as f:
    r_detect = client.post(
        '/api/disease/detect',
        files={'file': (sample_leaf.name, f.read(), 'image/jpeg')}
    )
assert r_detect.status_code == 200, f'Detect failed: {r_detect.text}'
d = r_detect.json()
print('  Predicted Class:', d['prediction']['class_name'])
print('  Condition:', d['prediction']['condition'])
print(f"  Confidence: {d['prediction']['confidence_percentage']}%")
print('  Organic remedies:', d['pathology_and_remedies']['organic_controls'][:2])
print('  Chemical treatment:', d['pathology_and_remedies']['chemical_treatment'][:2])
assert d['prediction']['confidence_score'] > 0

# Test 6: Input Validation & Error Handling (Invalid file)
fake_bytes = b'not an image content'
r_bad = client.post(
    '/api/disease/detect',
    files={'file': ('bad.txt', fake_bytes, 'text/plain')}
)
assert r_bad.status_code == 400
print('[TEST 6] Bad image rejection passed:', r_bad.json()['detail'])

print('\n' + '=' * 60)
print('ALL STAGES 1, 2, AND 3 TESTS PASSED SUCCESSFULLY (100%)!')
print('=' * 60)

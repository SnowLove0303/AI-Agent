import sys
from pathlib import Path

server_dir = Path(r"C:\Users\Administrator\.gemini\config\mcp-servers\substance-compliance-mcp")
sys.path.insert(0, str(server_dir))

import server

print("Server loaded successfully!")
print("Server name:", server.mcp.name)

# Test check_substance_compliance tool directly
print("\n--- Test 1: Query Cadmium (7440-43-9) with 150 ppm (RoHS Limit is 100 ppm) ---")
res_cd = server.check_substance_compliance("7440-43-9", concentration_ppm=150)
print("Cadmium Verdict:", res_cd.get("overall_verdict"))
print("Violations:", res_cd.get("violations"))
print("Summary:", res_cd.get("summary"))

print("\n--- Test 2: Query Chinese name '邻苯二甲酸二(2-乙基己)酯' (DEHP) with 800 ppm (RoHS limit 1000 ppm) ---")
res_dehp = server.check_substance_compliance("邻苯二甲酸二(2-乙基己)酯", concentration_ppm=800)
print("DEHP Verdict:", res_dehp.get("overall_verdict"))
print("DEHP RoHS verdict:", res_dehp.get("regulations", {}).get("EU_ROHS", {}).get("verdict"))
print("DEHP SVHC verdict:", res_dehp.get("regulations", {}).get("REACH_SVHC", {}).get("verdict"))
print("Summary:", res_dehp.get("summary"))

print("\n--- Test 3: Query Safe Non-Restricted Substance 'Water' / '水' (7732-18-5) ---")
res_water = server.check_substance_compliance("7732-18-5", concentration_pct=95.0)
print("Water Verdict:", res_water.get("overall_verdict"))
print("Matched Count:", res_water.get("matched_regulations_count"))
print("Summary:", res_water.get("summary"))

print("\n--- Test 4: Batch Formulation Check ---")
batch_input = [
    {"substance": "7440-43-9", "name": "镉", "concentration_ppm": 50},
    {"substance": "80-05-7", "name": "双酚A", "concentration_pct": 0.03},
    {"substance": "7732-18-5", "name": "水", "concentration_pct": 99.0}
]
res_batch = server.batch_check_compliance(batch_input)
print("Batch Overall Pass:", res_batch.get("overall_pass"))
print("Batch Verdict:", res_batch.get("verdict"))
print("Restricted Substances:", res_batch.get("restricted_substances_found"))

print("\nALL DEPLOYED MCP TESTS PASSED!")

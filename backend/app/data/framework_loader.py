import json
import os
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

def load_competency_framework() -> Dict[str, Any]:
    file_path = os.path.join(DATA_DIR, "competency_framework.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_role_benchmarks() -> List[Dict[str, Any]]:
    file_path = os.path.join(DATA_DIR, "role_benchmarks.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("role_benchmarks", [])

def get_benchmarks_for_role(designation: str) -> Optional[Dict[str, Any]]:
    all_roles = load_role_benchmarks()
    # Direct match or case-insensitive match
    for role in all_roles:
        if role["designation"].lower() == designation.lower():
            return role
    # Fallback to JSO
    return all_roles[0] if all_roles else None

def get_competency_by_code(code: str) -> Optional[Dict[str, Any]]:
    framework = load_competency_framework()
    for comp in framework.get("competencies", []):
        if comp["code"] == code:
            return comp
    return None

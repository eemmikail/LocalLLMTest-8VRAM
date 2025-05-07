import asyncio
import sys
import json
import httpx
import datetime
import random
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

# ────────────────────────────────────────────────────────────
#  1) MODELLERİ VE ŞEMALARI TANIMLAYALIM
# ────────────────────────────────────────────────────────────
class UserInfo(BaseModel):
    name: str
    age: int
    is_active: bool = True
    hobbies: Optional[List[str]] = None

class WeatherParams(BaseModel):
    city: str
    units: str = "metric"

class CalculatorParams(BaseModel):
    a: float
    b: float
    operation: str

class TravelRecommendation(BaseModel):
    destination: str
    budget: float
    duration_days: int
    activities: List[str]
    best_season: str

# ────────────────────────────────────────────────────────────
#  2) TEST SONUÇ SINIFI
# ────────────────────────────────────────────────────────────
class TestResult:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.basic_test = False
        self.tools_test = False
        self.schema_test = False
        self.combined_test = False
        self.errors = []

    def add_error(self, test_name: str, error_msg: str):
        self.errors.append(f"{test_name}: {error_msg}")

# ────────────────────────────────────────────────────────────
#  3) ANA TESTER SINIFI
# ────────────────────────────────────────────────────────────
class OllamaConnectionTest:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "mistral:7b"):
        self.ollama_url = ollama_url
        self.model = model

    # --------------------------------------------------------
    # Yardımcı (simüle) araç fonksiyonları
    # --------------------------------------------------------
    def get_weather(self, city: str, units: str = "metric") -> Dict[str, Any]:
        print(f"  → Executing tool: get_weather({city}, {units})")
        temp = random.randint(-10, 35)
        conditions = random.choice(["Sunny", "Cloudy", "Rainy", "Snowy", "Windy"])
        unit = "°C" if units == "metric" else "°F"
        return {
            "city": city,
            "temperature": temp,
            "unit": unit,
            "conditions": conditions,
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
        }

    def calculator(self, a: float, b: float, operation: str) -> Dict[str, Any]:
        print(f"  → Executing tool: calculator({a}, {b}, '{operation}')")
        result, error = None, None
        try:
            if operation == "+": result = a + b
            elif operation == "-": result = a - b
            elif operation == "*": result = a * b
            elif operation == "/":
                if b == 0: raise ValueError("Division by zero")
                result = a / b
            else: error = f"Unsupported operation: {operation}"
        except Exception as e:
            error = str(e)
        return {"a": a, "b": b, "operation": operation, "result": result, "error": error}

    def search_flights(self, from_city: str, to_city: str, date: str = None) -> Dict[str, Any]:
        print(f"  → Executing tool: search_flights({from_city}, {to_city}, {date})")
        if not date:
            date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        flights = []
        for _ in range(random.randint(1, 3)):
            dep = random.randint(6, 20)
            dur = random.randint(1, 8)
            flights.append({
                "flight_number": f"{random.choice(['BA','LH','TK'])}{random.randint(100,999)}",
                "from": from_city,
                "to": to_city,
                "date": date,
                "departure_time": f"{dep:02d}:{random.randint(0,59):02d}",
                "arrival_time": f"{(dep+dur)%24:02d}:{random.randint(0,59):02d}",
                "duration": f"{dur}h",
                "price": round(random.uniform(150, 800), 2),
                "currency": "USD",
            })
        return {"from": from_city, "to": to_city, "date": date, "flights": flights}

    def check_visa_requirements(self, country: str, citizenship: str) -> Dict[str, Any]:
        print(f"  → Executing tool: check_visa_requirements({country}, {citizenship})")
        visa_db = {
            "France": {"US": "Visa‑free 90d", "TR": "Visa required"},
            "Italy": {"US": "Visa‑free 90d", "TR": "Visa required"},
            "Germany": {"US": "Visa‑free 90d", "TR": "Visa required"},
        }
        requirement = visa_db.get(country, {}).get(citizenship, "Unknown, check embassy.")
        return {"country": country, "citizenship": citizenship, "requirement": requirement}

    # Araç çağrısını çalıştır
    async def execute_tool(self, tool_call: Dict[str, Any]) -> str:
        name = tool_call["function"]["name"]
        raw_args = tool_call["function"].get("arguments", {})

        print(f"  → Processing tool call: {name}")
        # ←←←  BU KISIM GÜNCELLENDİ
        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON arguments"})
        elif isinstance(raw_args, dict):
            args = raw_args
        else:
            return json.dumps({"error": "Unsupported arguments format"})

        # Gerçek fonksiyonu çağır
        if name == "get_weather":
            result = self.get_weather(**args)
        elif name == "calculator":
            result = self.calculator(**args)
        elif name == "search_flights":
            result = self.search_flights(**args)
        elif name == "check_visa_requirements":
            result = self.check_visa_requirements(**args)
        else:
            result = {"error": f"Unknown tool {name}"}

        return json.dumps(result)

    # --------------------------------------------------------
    # TEMEL BAĞLANTI TESTİ
    # --------------------------------------------------------
    async def test_basic_connection(self):
        print(f"\n[1/4] 🚀 Testing basic connection for {self.model}...")
        url = f"{self.ollama_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Hello, world!"}],
            "stream": False
        }
        try:
            print("  → Sending basic prompt: 'Hello, world!'")
            async with httpx.AsyncClient(timeout=240) as client:
                r = await client.post(url, json=payload); r.raise_for_status()
            print("  ✅ Basic connection test passed")
            return True, None
        except Exception as e:
            print(f"  ❌ Basic connection test failed: {e}")
            return False, str(e)

    # --------------------------------------------------------
    # SADECE ARAÇ TESTİ
    # --------------------------------------------------------
    async def test_with_tool_calls(self):
        print(f"\n[2/4] 🔧 Testing tool calls for {self.model}...")
        url = f"{self.ollama_url}/api/chat"
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather.",
                    "parameters": WeatherParams.model_json_schema()
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Do math.",
                    "parameters": CalculatorParams.model_json_schema()
                }
            }
        ]
        messages = [
            {"role": "system", "content": "Use tools when helpful."},
            {"role": "user", "content": "Weather in Istanbul and 15*7 please."}
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "options": {"temperature": 0.2},
            "stream": False
        }
        try:
            print("  → Sending prompt with tools: 'Weather in Istanbul and 15*7 please.'")
            async with httpx.AsyncClient(timeout=240) as client:
                r = await client.post(url, json=payload); r.raise_for_status()
                data = r.json()
            
            has_tool_calls = bool(data["message"].get("tool_calls"))
            if has_tool_calls:
                print(f"  ✅ Tool calls test passed: model successfully used tools")
            else:
                print(f"  ❌ Tool calls test failed: model did not use any tools")
            return has_tool_calls, None
        except Exception as e:
            print(f"  ❌ Tool calls test failed with error: {e}")
            return False, str(e)

    # --------------------------------------------------------
    # SADECE ŞEMA TESTİ
    # --------------------------------------------------------
    async def test_with_schema(self):
        print(f"\n[3/4] 📋 Testing schema validation for {self.model}...")
        url = f"{self.ollama_url}/api/chat"
        schema = UserInfo.model_json_schema()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return JSON matching schema."},
                {"role": "user", "content": "Create a profile for Alex, 28, hiking."}
            ],
            "format": schema,
            "stream": False,
            "options": {"temperature": 0.2}
        }
        try:
            print("  → Sending prompt with schema: 'Create a profile for Alex, 28, hiking.'")
            async with httpx.AsyncClient(timeout=240) as client:
                r = await client.post(url, json=payload); r.raise_for_status()
                content = r.json()["message"]["content"]
            json_result = json.loads(content)  # parse test
            print(f"  ✅ Schema test passed: received valid JSON: {json_result}")
            return True, None
        except Exception as e:
            print(f"  ❌ Schema test failed: {e}")
            return False, str(e)

    # --------------------------------------------------------
    # YENİ: ARAÇ + ŞEMA (İKİ AŞAMALI)
    # --------------------------------------------------------
    async def test_with_tools_and_schema(self):
        print(f"\n[4/4] 🔄 Testing combined tools and schema for {self.model}...")
        url = f"{self.ollama_url}/api/chat"
        schema = TravelRecommendation.model_json_schema()

        # Araç tanımları
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_flights",
                    "description": "Find flights.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_city": {"type": "string"},
                            "to_city": {"type": "string"},
                            "date": {"type": "string"}
                        },
                        "required": ["from_city", "to_city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_visa_requirements",
                    "description": "Visa rules.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "country": {"type": "string"},
                            "citizenship": {"type": "string"}
                        },
                        "required": ["country", "citizenship"]
                    }
                }
            }
        ]

        system_prompt = (
            "You are a travel assistant. "
            "First, use tools to gather data. "
            "Do NOT give the final answer yet."
        )
        user_prompt = (
            "I have 2000 USD and 7 days. I love history and food. "
            "Recommend somewhere in Europe and check visa for a US citizen."
        )

        # ---------- AŞAMA 1: SADECE ARAÇLAR ----------
        print("  → PHASE 1: Tool gathering phase")
        print("  → Sending travel prompt with tools")
        phase1_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "tools": tools,
            "tool_choice": "auto",
            "options": {"temperature": 0.2},
            "stream": False
        }

        async with httpx.AsyncClient(timeout=240) as client:
            r1 = await client.post(url, json=phase1_payload); r1.raise_for_status()
            data1 = r1.json()

        tool_calls = data1["message"].get("tool_calls", [])
        if not tool_calls:
            print("  ❌ Phase 1 failed: Model did not call any tools")
            return False, "Model called no tools."
        else:
            print(f"  ✅ Phase 1 complete: Model called {len(tool_calls)} tools")

        # Araçları çalıştır ve mesaj listesine ekle
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            data1["message"]  # modelın tool çağrısı içeren cevabı
        ]
        for idx, call in enumerate(tool_calls):
            result_str = await self.execute_tool(call)
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", f"call_{idx}"),
                "name": call["function"]["name"],
                "content": result_str
            })

        # ---------- AŞAMA 2: SADECE ŞEMA ----------
        print("  → PHASE 2: Schema formatting phase")
        print("  → Sending tool results for final formatting with schema")
        phase2_payload = {
            "model": self.model,
            "messages": messages + [
                {"role": "system", "content": "Now synthesise everything and output JSON only."}
            ],
            "format": schema,
            "options": {"temperature": 0.2},
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=240) as client:
                r2 = await client.post(url, json=phase2_payload); r2.raise_for_status()
                final_content = r2.json()["message"]["content"]
            json_result = json.loads(final_content)  # parse & validate
            print(f"  ✅ Phase 2 complete: Received valid JSON: {json_result}")
            return True, None
        except Exception as e:
            print(f"  ❌ Phase 2 failed: {e}")
            return False, str(e)

# ────────────────────────────────────────────────────────────
#  4) TÜM TESTLERİ ÇALIŞTIR
# ────────────────────────────────────────────────────────────
async def run_all_tests_for_model(model_name: str, url: str) -> TestResult:
    print(f"\n{'='*50}")
    print(f"📊 RUNNING ALL TESTS FOR MODEL: {model_name}")
    print(f"{'='*50}")
    
    result = TestResult(model_name)
    tester = OllamaConnectionTest(url, model_name)

    result.basic_test, err = await tester.test_basic_connection()
    if err: result.add_error("Basic", err)

    result.tools_test, err = await tester.test_with_tool_calls()
    if err: result.add_error("Tools", err)

    result.schema_test, err = await tester.test_with_schema()
    if err: result.add_error("Schema", err)

    result.combined_test, err = await tester.test_with_tools_and_schema()
    if err: result.add_error("Combined", err)

    print(f"\n{'='*50}")
    print(f"📝 TEST RESULTS FOR {model_name}:")
    print(f"- Basic Connection: {'✅' if result.basic_test else '❌'}")
    print(f"- Tool Calls: {'✅' if result.tools_test else '❌'}")
    print(f"- Schema: {'✅' if result.schema_test else '❌'}")
    print(f"- Combined: {'✅' if result.combined_test else '❌'}")
    print(f"{'='*50}")

    return result

async def main():
    print("\n🔍 OLLAMA MODEL CAPABILITY TESTER")
    print("-------------------------------")
    
    ollama_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11434"
    print(f"Using Ollama server: {ollama_url}")
    
    models = [
        "mistral:7b",   
        "phi4-mini:3.8b-fp16",        
        "llama3.2:latest",       
        "qwen3:14b",
        "qwen3:8b"
    ]
    if len(sys.argv) > 2:
        models = [sys.argv[2]]
        print(f"Testing single model: {models[0]}")
    else:
        print(f"Testing {len(models)} models: {', '.join(models)}")

    all_results = []
    for m in models:
        res = await run_all_tests_for_model(m, ollama_url)
        all_results.append(res)

    print("\n🏁 === SUMMARY ===")
    print(f"{'Model':<18} | Basic | Tools | Schema | Combo")
    print(f"{'-'*18}-|-------|-------|--------|-------")
    for r in all_results:
        print(f"{r.model_name:<18} | "
              f"{'✅' if r.basic_test else '❌'}     | "
              f"{'✅' if r.tools_test else '❌'}    | "
              f"{'✅' if r.schema_test else '❌'}    | "
              f"{'✅' if r.combined_test else '❌'}")

    for r in all_results:
        if r.errors:
            print(f"\n❌ Errors for {r.model_name}:")
            for e in r.errors:
                print(" -", e)

if __name__ == "__main__":
    asyncio.run(main())

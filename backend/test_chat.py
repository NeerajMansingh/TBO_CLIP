import sys
sys.path.append('.')
from gemini_utils import generate_chat_response
session = {
    "conversation_history": [{"role": "user", "content": "hello"}],
    "itinerary_stops": [{"destination": "Goa", "price_per_person": 1000}],
    "budget": 50000
}
try:
    print(generate_chat_response(session))
except Exception as e:
    print("FATAL ERROR", e)

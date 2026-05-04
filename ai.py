import requests
import config

class HoloAI:
    """Handles conversation with Ollama LLM"""
    
    def __init__(self):
        self.conversation_history = []
        self.system_prompt = """You are HOLO, a female hologram librarian. 
Be friendly, warm, and helpful. Keep responses SHORT (1-2 sentences).
If you didn't understand what the user said, ask them to repeat it nicely.
Never use markdown, asterisks, or special characters."""
        
        # Test connection
        try:
            test = requests.post(
                config.OLLAMA_URL,
                json={"model": config.OLLAMA_MODEL, "prompt": "Hi", "stream": False, "options": {"max_tokens": 5}},
                timeout=10
            )
            if test.status_code == 200:
                print("✅ Ollama connected!")
            else:
                print(f"⚠️ Ollama status: {test.status_code}")
        except Exception as e:
            print(f"⚠️ Ollama not reachable: {e}")
    
    def get_response(self, user_input):
        """Get AI response for user input"""
        print(f"\n📝 User: {user_input}")
        
        prompt = f"{self.system_prompt}\n"
        for msg in self.conversation_history[-6:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        prompt += f"User: {user_input}\nHOLO:"
        
        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "max_tokens": 100, "stop": ["\nUser:", "\n\n"]}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                ai_response = ai_response.replace('*', '').replace('#', '').strip()
                print(f"🤖 HOLO: {ai_response}")
                
                self.conversation_history.append({"role": "User", "content": user_input})
                self.conversation_history.append({"role": "HOLO", "content": ai_response})
                
                return ai_response if ai_response else "I'm not sure what to say about that."
            else:
                return "I'm having trouble thinking right now."
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return "I can't reach my brain right now. Can you try again?"

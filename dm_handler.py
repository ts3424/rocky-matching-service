import discord
import aiohttp
import csv
import os


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

PRIMING_FILE = 'initial_priming.txt'

class DMHandler:
    def __init__(self, bot):
        self.bot = bot
        self.user_sessions = {}
        self.priming_text = self.load_priming()


    def load_priming(self):
        try:
            with open(PRIMING_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print("❌ priming file not found")
            return "priming goes here"

    async def query_ollama(self, prompt: str) -> str:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "No response from Ollama.")
                else:
                    return f"Ollama API Error: {resp.status}"

    
    async def start_dm_conversation(self, user: discord.User):
        # Initialize user session with priming text
        self.user_sessions[user.id] = {
            "context": self.priming_text,
            "history": []
        }
        dm = await user.create_dm()

        # Don't send priming text to user, just greet
        await dm.send("Hi, I'm Rocky! I embody the 'everyone's friend' role in the SundAI community 🧸✨ " \
        "Let's have a quick chat and I'll connect you to some cool people you might hit it off with! \n\n" \
        "--> Tell me more about your background <-- \n" \
            "- Where are you from?\n" \
            "- What's your educational/professional background? \n"
            "- Who are you hoping to connect with? ")

    async def handle_dm_message(self, message: discord.Message):
        user_id = message.author.id
        user = message.author

        # Ensure session is initialized
        if user_id not in self.user_sessions:
            await message.channel.send("Please click 'Introduce me' in the group channel to start.")
            return

        session = self.user_sessions[user_id]

        # Fallback fix: if somehow session lacks keys
        session.setdefault("context", self.priming_text)
        session.setdefault("history", [])
        session.setdefault("question_count", 0)

        user_input = message.content.strip()

        # Build prompt
        full_prompt = session["context"] + "\n"
        for line in session["history"]:
            full_prompt += line + "\n"
        full_prompt += f"User: {user_input}\nRocky:"

        try:
            llm_response = await self.query_ollama(full_prompt)
        except Exception as e:
            llm_response = f"⚠️ Error contacting Ollama: {e}"

        # Save history
        session["history"].append(f"User: {user_input}")
        session["history"].append(f"Rocky: {llm_response}")
        session["question_count"] += 1

        if session["question_count"] >= 5:
            await message.channel.send("This is it! thank you for your responses! I'll reach out once I have matches for you")

            # Collect data
            full_name = str(user)
            discord_id = str(user.id)
            user_responses = [line[6:].strip() for line in session["history"] if line.startswith("User:")]
            concatenated_text = " ".join(user_responses)

            # Save to CSV
            file_exists = os.path.isfile('matches.csv')
            with open('matches.csv', mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists:
                    writer.writerow(["Full Name", "Discord ID", "Responses"])
                writer.writerow([full_name, discord_id, concatenated_text])

            # End session
            del self.user_sessions[user_id]
            
        else:
            await message.channel.send(llm_response)
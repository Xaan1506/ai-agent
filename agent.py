import os
import asyncio
from dotenv import load_dotenv
from openclaw import OpenClaw
from huggingface_hub import InferenceClient
from playwright.async_api import async_playwright
import json
import re
import httpx

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
llm_client = InferenceClient(token=HF_API_KEY)

# ─── DETERMINISTIC KNOWLEDGE BASE ───────────────────────────────────────
# No LLM needed for these - pure Python logic

GREETING_WORDS = {"hi", "hello", "hey", "hola", "namaste", "yo", "sup", "hii", "hiii", "hiiii"}

TALK_PATTERNS = [
    "what can you do", "who are you", "help me", "how do you work",
    "what are you", "tell me about yourself", "what is this",
    "how are you", "good morning", "good evening", "good night",
    "thank you", "thanks", "bye", "goodbye", "see you",
    "what do you do", "can you help", "assist me"
]

# CEO/Founder database for disambiguation and direct Wikipedia lookup
CEO_DATABASE = {
    # ── Indian CEOs & Founders ──
    "aman gupta": {"full_name": "Aman Gupta", "company": "boAt Lifestyle", "role": "Co-founder & CMO", "wiki": "Aman_Gupta_(businessman)", "company_info": {"industry": "Consumer Electronics / Audio", "founded": "2016", "valuation": "~$1.5 Billion", "employees": "~5,000+", "hq": "New Delhi, India"}},
    "mukesh ambani": {"full_name": "Mukesh Ambani", "company": "Reliance Industries", "role": "Chairman & MD", "wiki": "Mukesh_Ambani", "company_info": {"industry": "Conglomerate (Oil, Telecom, Retail)", "founded": "1966", "valuation": "~$250 Billion market cap", "employees": "~360,000+", "hq": "Mumbai, India"}},
    "ratan tata": {"full_name": "Ratan Tata", "company": "Tata Group", "role": "Chairman Emeritus", "wiki": "Ratan_Tata", "company_info": {"industry": "Conglomerate (Steel, IT, Auto, Hotels)", "founded": "1868", "valuation": "~$400 Billion (group combined)", "employees": "~935,000+", "hq": "Mumbai, India"}},
    "gautam adani": {"full_name": "Gautam Adani", "company": "Adani Group", "role": "Chairman", "wiki": "Gautam_Adani", "company_info": {"industry": "Infrastructure, Energy, Ports", "founded": "1988", "valuation": "~$200 Billion (group combined)", "employees": "~50,000+", "hq": "Ahmedabad, India"}},
    "azim premji": {"full_name": "Azim Premji", "company": "Wipro", "role": "Founder Chairman", "wiki": "Azim_Premji", "company_info": {"industry": "IT Services & Consulting", "founded": "1945", "valuation": "~$30 Billion market cap", "employees": "~250,000+", "hq": "Bangalore, India"}},
    "narayana murthy": {"full_name": "N. R. Narayana Murthy", "company": "Infosys", "role": "Co-founder", "wiki": "N._R._Narayana_Murthy", "company_info": {"industry": "IT Services & Consulting", "founded": "1981", "valuation": "~$90 Billion market cap", "employees": "~340,000+", "hq": "Bangalore, India"}},
    "shiv nadar": {"full_name": "Shiv Nadar", "company": "HCL Technologies", "role": "Founder & Chairman", "wiki": "Shiv_Nadar", "company_info": {"industry": "IT Services", "founded": "1976", "valuation": "~$45 Billion market cap", "employees": "~225,000+", "hq": "Noida, India"}},
    "byju raveendran": {"full_name": "Byju Raveendran", "company": "BYJU'S", "role": "Founder & CEO", "wiki": "Byju_Raveendran", "company_info": {"industry": "EdTech", "founded": "2011", "valuation": "~$22 Billion (peak)", "employees": "~10,000+", "hq": "Bangalore, India"}},
    "ritesh agarwal": {"full_name": "Ritesh Agarwal", "company": "OYO Rooms", "role": "Founder & CEO", "wiki": "Ritesh_Agarwal", "company_info": {"industry": "Hospitality / Travel Tech", "founded": "2013", "valuation": "~$9 Billion", "employees": "~10,000+", "hq": "Gurugram, India"}},
    "falguni nayar": {"full_name": "Falguni Nayar", "company": "Nykaa", "role": "Founder & CEO", "wiki": "Falguni_Nayar", "company_info": {"industry": "Beauty & Fashion E-commerce", "founded": "2012", "valuation": "~$7 Billion market cap", "employees": "~3,500+", "hq": "Mumbai, India"}},
    "kunal shah": {"full_name": "Kunal Shah", "company": "CRED", "role": "Founder & CEO", "wiki": "Kunal_Shah_(entrepreneur)", "company_info": {"industry": "Fintech", "founded": "2018", "valuation": "~$6.4 Billion", "employees": "~1,000+", "hq": "Bangalore, India"}},
    "deepinder goyal": {"full_name": "Deepinder Goyal", "company": "Zomato", "role": "Founder & CEO", "wiki": "Deepinder_Goyal", "company_info": {"industry": "Food Delivery / FoodTech", "founded": "2008", "valuation": "~$15 Billion market cap", "employees": "~5,000+", "hq": "Gurugram, India"}},
    "bhavish aggarwal": {"full_name": "Bhavish Aggarwal", "company": "Ola Cabs", "role": "Co-founder & CEO", "wiki": "Bhavish_Aggarwal", "company_info": {"industry": "Ride-hailing / EV", "founded": "2010", "valuation": "~$7 Billion", "employees": "~8,000+", "hq": "Bangalore, India"}},
    "vijay shekhar sharma": {"full_name": "Vijay Shekhar Sharma", "company": "Paytm", "role": "Founder & CEO", "wiki": "Vijay_Shekhar_Sharma", "company_info": {"industry": "Fintech / Digital Payments", "founded": "2010", "valuation": "~$5 Billion market cap", "employees": "~9,000+", "hq": "Noida, India"}},
    "nithin kamath": {"full_name": "Nithin Kamath", "company": "Zerodha", "role": "Founder & CEO", "wiki": "Nithin_Kamath", "company_info": {"industry": "Fintech / Stock Brokerage", "founded": "2010", "valuation": "Profitable & Private", "employees": "~1,200+", "hq": "Bangalore, India"}},
    "ashneer grover": {"full_name": "Ashneer Grover", "company": "BharatPe", "role": "Co-founder", "wiki": "Ashneer_Grover", "company_info": {"industry": "Fintech / Payments", "founded": "2018", "valuation": "~$2.8 Billion", "employees": "~1,500+", "hq": "New Delhi, India"}},
    "peyush bansal": {"full_name": "Peyush Bansal", "company": "Lenskart", "role": "Founder & CEO", "wiki": "Peyush_Bansal"},
    "nita ambani": {"full_name": "Nita Ambani", "company": "Reliance Foundation", "role": "Chairperson", "wiki": "Nita_Ambani", "company_info": {"industry": "Philanthropy / Sports / Education", "founded": "2010", "valuation": "Part of Reliance Industries", "employees": "N/A", "hq": "Mumbai, India"}},
    "anand mahindra": {"full_name": "Anand Mahindra", "company": "Mahindra Group", "role": "Chairman", "wiki": "Anand_Mahindra", "company_info": {"industry": "Auto, IT, Real Estate", "founded": "1945", "valuation": "~$20 Billion market cap", "employees": "~260,000+", "hq": "Mumbai, India"}},
    "kumar mangalam birla": {"full_name": "Kumar Mangalam Birla", "company": "Aditya Birla Group", "role": "Chairman", "wiki": "Kumar_Mangalam_Birla", "company_info": {"industry": "Conglomerate (Cement, Telecom, Finance)", "founded": "1857", "valuation": "~$60 Billion (group)", "employees": "~140,000+", "hq": "Mumbai, India"}},
    "nandan nilekani": {"full_name": "Nandan Nilekani", "company": "Infosys / Aadhaar", "role": "Co-founder & Chairman", "wiki": "Nandan_Nilekani", "company_info": {"industry": "IT Services", "founded": "1981", "valuation": "~$90 Billion market cap", "employees": "~340,000+", "hq": "Bangalore, India"}},

    # ── International CEOs & Founders ──
    "elon musk": {"full_name": "Elon Musk", "company": "Tesla / SpaceX / X", "role": "CEO", "wiki": "Elon_Musk", "company_info": {"industry": "EV, Space, Social Media", "founded": "2003 (Tesla)", "valuation": "~$800B (Tesla market cap)", "employees": "~140,000+ (Tesla)", "hq": "Austin, Texas, USA"}},
    "jensen huang": {"full_name": "Jensen Huang", "company": "NVIDIA", "role": "Founder & CEO", "wiki": "Jensen_Huang", "company_info": {"industry": "Semiconductors / AI Computing", "founded": "1993", "valuation": "~$3 Trillion market cap", "employees": "~30,000+", "hq": "Santa Clara, California, USA"}},
    "tim cook": {"full_name": "Tim Cook", "company": "Apple", "role": "CEO", "wiki": "Tim_Cook", "company_info": {"industry": "Consumer Electronics / Software", "founded": "1976", "valuation": "~$3.4 Trillion market cap", "employees": "~160,000+", "hq": "Cupertino, California, USA"}},
    "satya nadella": {"full_name": "Satya Nadella", "company": "Microsoft", "role": "Chairman & CEO", "wiki": "Satya_Nadella", "company_info": {"industry": "Software / Cloud / AI", "founded": "1975", "valuation": "~$3 Trillion market cap", "employees": "~220,000+", "hq": "Redmond, Washington, USA"}},
    "sundar pichai": {"full_name": "Sundar Pichai", "company": "Alphabet / Google", "role": "CEO", "wiki": "Sundar_Pichai", "company_info": {"industry": "Internet / AI / Advertising", "founded": "1998 (Google)", "valuation": "~$2 Trillion market cap", "employees": "~180,000+", "hq": "Mountain View, California, USA"}},
    "mark zuckerberg": {"full_name": "Mark Zuckerberg", "company": "Meta (Facebook)", "role": "Founder & CEO", "wiki": "Mark_Zuckerberg", "company_info": {"industry": "Social Media / VR / AI", "founded": "2004", "valuation": "~$1.5 Trillion market cap", "employees": "~67,000+", "hq": "Menlo Park, California, USA"}},
    "jeff bezos": {"full_name": "Jeff Bezos", "company": "Amazon", "role": "Founder & Executive Chairman", "wiki": "Jeff_Bezos", "company_info": {"industry": "E-commerce / Cloud (AWS)", "founded": "1994", "valuation": "~$2 Trillion market cap", "employees": "~1,500,000+", "hq": "Seattle, Washington, USA"}},
    "bill gates": {"full_name": "Bill Gates", "company": "Microsoft / Gates Foundation", "role": "Co-founder", "wiki": "Bill_Gates", "company_info": {"industry": "Software / Philanthropy", "founded": "1975 (Microsoft)", "valuation": "~$3 Trillion (Microsoft)", "employees": "~220,000+ (Microsoft)", "hq": "Redmond, Washington, USA"}},
    "sam altman": {"full_name": "Sam Altman", "company": "OpenAI", "role": "CEO", "wiki": "Sam_Altman", "company_info": {"industry": "Artificial Intelligence", "founded": "2015", "valuation": "~$157 Billion", "employees": "~3,000+", "hq": "San Francisco, California, USA"}},
    "andy jassy": {"full_name": "Andy Jassy", "company": "Amazon", "role": "CEO", "wiki": "Andy_Jassy", "company_info": {"industry": "E-commerce / Cloud", "founded": "1994", "valuation": "~$2 Trillion market cap", "employees": "~1,500,000+", "hq": "Seattle, Washington, USA"}},
    "lisa su": {"full_name": "Lisa Su", "company": "AMD", "role": "CEO", "wiki": "Lisa_Su", "company_info": {"industry": "Semiconductors", "founded": "1969", "valuation": "~$200 Billion market cap", "employees": "~26,000+", "hq": "Santa Clara, California, USA"}},
    "warren buffett": {"full_name": "Warren Buffett", "company": "Berkshire Hathaway", "role": "Chairman & CEO", "wiki": "Warren_Buffett", "company_info": {"industry": "Conglomerate / Investments", "founded": "1839", "valuation": "~$1 Trillion market cap", "employees": "~400,000+", "hq": "Omaha, Nebraska, USA"}},
    "larry page": {"full_name": "Larry Page", "company": "Alphabet / Google", "role": "Co-founder", "wiki": "Larry_Page", "company_info": {"industry": "Internet / AI", "founded": "1998", "valuation": "~$2 Trillion market cap", "employees": "~180,000+", "hq": "Mountain View, California, USA"}},
    "sergey brin": {"full_name": "Sergey Brin", "company": "Alphabet / Google", "role": "Co-founder", "wiki": "Sergey_Brin", "company_info": {"industry": "Internet / AI", "founded": "1998", "valuation": "~$2 Trillion market cap", "employees": "~180,000+", "hq": "Mountain View, California, USA"}},
    "jack dorsey": {"full_name": "Jack Dorsey", "company": "Block (Square) / Twitter", "role": "Co-founder", "wiki": "Jack_Dorsey", "company_info": {"industry": "Fintech / Social Media", "founded": "2009 (Square)", "valuation": "~$30 Billion (Block)", "employees": "~12,000+", "hq": "San Francisco, California, USA"}},
    "steve jobs": {"full_name": "Steve Jobs", "company": "Apple", "role": "Co-founder (Late)", "wiki": "Steve_Jobs", "company_info": {"industry": "Consumer Electronics", "founded": "1976", "valuation": "~$3.4 Trillion market cap", "employees": "~160,000+", "hq": "Cupertino, California, USA"}},
    "larry ellison": {"full_name": "Larry Ellison", "company": "Oracle", "role": "Co-founder & CTO", "wiki": "Larry_Ellison", "company_info": {"industry": "Enterprise Software / Cloud", "founded": "1977", "valuation": "~$400 Billion market cap", "employees": "~160,000+", "hq": "Austin, Texas, USA"}},
    "reed hastings": {"full_name": "Reed Hastings", "company": "Netflix", "role": "Co-founder & Executive Chairman", "wiki": "Reed_Hastings", "company_info": {"industry": "Streaming / Entertainment", "founded": "1997", "valuation": "~$300 Billion market cap", "employees": "~13,000+", "hq": "Los Gatos, California, USA"}},
    "brian chesky": {"full_name": "Brian Chesky", "company": "Airbnb", "role": "Co-founder & CEO", "wiki": "Brian_Chesky", "company_info": {"industry": "Travel / Hospitality", "founded": "2008", "valuation": "~$80 Billion market cap", "employees": "~6,900+", "hq": "San Francisco, California, USA"}},
    "daniel ek": {"full_name": "Daniel Ek", "company": "Spotify", "role": "Co-founder & CEO", "wiki": "Daniel_Ek", "company_info": {"industry": "Music Streaming", "founded": "2006", "valuation": "~$80 Billion market cap", "employees": "~9,000+", "hq": "Stockholm, Sweden"}},
    "pat gelsinger": {"full_name": "Pat Gelsinger", "company": "Intel", "role": "Former CEO", "wiki": "Pat_Gelsinger", "company_info": {"industry": "Semiconductors", "founded": "1968", "valuation": "~$100 Billion market cap", "employees": "~120,000+", "hq": "Santa Clara, California, USA"}},
    "dara khosrowshahi": {"full_name": "Dara Khosrowshahi", "company": "Uber", "role": "CEO", "wiki": "Dara_Khosrowshahi", "company_info": {"industry": "Ride-hailing / Delivery", "founded": "2009", "valuation": "~$160 Billion market cap", "employees": "~32,000+", "hq": "San Francisco, California, USA"}},
}


def identify_intent(user_input):
    """Pure Python intent detection - NO LLM needed."""
    clean = user_input.lower().strip().rstrip("?!.,")
    
    # Check greetings
    if clean in GREETING_WORDS:
        return "GREETING"
    
    # Check talk patterns
    for pattern in TALK_PATTERNS:
        if pattern in clean:
            return "TALK"
    
    # Everything else is a research request
    return "RESEARCH"


def extract_target_name(user_input):
    """Pure Python name extraction - NO LLM needed."""
    clean = user_input.strip()
    
    # Remove common prefixes
    prefixes = [
        "tell me about", "who is", "research", "search for", "look up",
        "find info on", "find information on", "give me info on",
        "i want to know about", "can you research", "please research",
        "search", "find", "about", "look into",
    ]
    lower = clean.lower()
    for prefix in sorted(prefixes, key=len, reverse=True):
        if lower.startswith(prefix):
            clean = clean[len(prefix):].strip()
            lower = clean.lower()
            break
    
    # Remove trailing punctuation
    clean = clean.rstrip("?!.,")
    
    return clean.strip()


def find_in_database(name):
    """Find a CEO/founder in our database using fuzzy matching."""
    lower_name = name.lower().strip()
    
    # Direct match
    if lower_name in CEO_DATABASE:
        return CEO_DATABASE[lower_name]
    
    # Partial match
    for key, value in CEO_DATABASE.items():
        if key in lower_name or lower_name in key:
            return value
    
    # Company match (e.g., "CEO of Apple" -> Tim Cook)
    for key, value in CEO_DATABASE.items():
        if value["company"].lower() in lower_name:
            return value
    
    return None


class AutonomousResearchAgent:
    def __init__(self, user_input, status_callback=None):
        self.user_input = user_input.strip()
        self.status_callback = status_callback
        self.memory = []

    async def log_status(self, message):
        print(f"DEBUG: {message}")
        if self.status_callback:
            if asyncio.iscoroutinefunction(self.status_callback):
                await self.status_callback(message)
            else:
                self.status_callback(message)

    async def chat(self, prompt):
        """Call LLM - ONLY used for content analysis and report generation."""
        try:
            res = llm_client.chat_completion(
                model="meta-llama/Llama-3.2-1B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.2
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            await self.log_status(f"⚠️ LLM Error: {e}")
            return ""

    async def browse(self, url):
        await self.log_status(f"🌐 Browsing: {url}")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    await page.set_extra_http_headers({
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    })
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)
                    text = await page.inner_text("body")
                    await browser.close()
                    return text[:15000]
                except Exception as e:
                    await self.log_status(f"⚠️ Browser error: {e}")
                    await browser.close()
        except Exception as e:
            await self.log_status(f"⚠️ Playwright unavailable, using HTTP fallback: {e}")

        # Fallback for restricted deploy environments where Chromium cannot launch.
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                res = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                    },
                )
                html = res.text
                text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return text[:15000]
        except Exception as e:
            await self.log_status(f"⚠️ HTTP fallback failed: {e}")
            return ""

    def build_company_section(self, db_entry):
        """Build a rich company info section from database."""
        ci = db_entry.get("company_info", {})
        if not ci:
            return ""
        return f"""## 🏢 Company — {db_entry['company']}
| Detail | Info |
|--------|------|
| **Industry** | {ci.get('industry', 'N/A')} |
| **Founded** | {ci.get('founded', 'N/A')} |
| **Valuation / Market Cap** | {ci.get('valuation', 'N/A')} |
| **Employees** | {ci.get('employees', 'N/A')} |
| **Headquarters** | {ci.get('hq', 'N/A')} |
"""

    async def run(self):
        # ── STEP 1: Intent Detection (Pure Python) ──
        intent = identify_intent(self.user_input)
        await self.log_status(f"🎯 Intent: {intent}")

        if intent == "GREETING":
            return "👋 Hello! I'm your **OpenClaw Research Agent**. I can research any CEO, founder, or company — from **international giants** like Elon Musk and Tim Cook to **Indian leaders** like Mukesh Ambani and Aman Gupta. Just type a name and I'll find everything about them!"

        if intent == "TALK":
            return await self.handle_talk()

        # ── STEP 2: Name Extraction (Pure Python) ──
        target_name = extract_target_name(self.user_input)
        if not target_name:
            return "I couldn't understand who you want me to research. Please type a name like **Jensen Huang** or **Aman Gupta**."

        await self.log_status(f"🔍 Researching: {target_name}")

        # ── STEP 3: Database Lookup ──
        db_entry = find_in_database(target_name)
        if db_entry:
            target_name = db_entry["full_name"]
            await self.log_status(f"✅ Found in database: {db_entry['full_name']}")
        else:
            await self.log_status(f"🔎 Global Search: looking for information on {target_name}...")
        
        # ── STEP 4: Browse Wikipedia ──
        wiki_slug = db_entry["wiki"] if db_entry else target_name.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/wiki/{wiki_slug}"
        wiki_text = await self.browse(wiki_url)

        company_section = self.build_company_section(db_entry) if db_entry else ""
        wiki_report = ""

        if wiki_text and len(wiki_text) > 500:
            await self.log_status(f"🧠 Analyzing Wikipedia data...")
            extract_prompt = f"""Extract a detailed business profile for {target_name} from this text.
If the text is about another person or irrelevant, say "NOT_FOUND".
Otherwise, extract: Role, Company, Net Worth, Industry, Key Achievements, Education, Early Life.
Also include company details: number of employees, founding year, valuation, headquarters.

Formatting: Use professional Markdown. If information is missing, try to infer it or leave it as "Researching...".

Content:
{wiki_text[:8000]}
"""
            wiki_report = await self.chat(extract_prompt)
            
            # Check if extraction was successful or sparse
            is_sparse = "Not available" in wiki_report or "None mentioned" in wiki_report or "Researching..." in wiki_report or "NOT_FOUND" in wiki_report
            
            if wiki_report and "NOT_FOUND" not in wiki_report and not is_sparse:
                if company_section:
                    wiki_report += "\n\n" + company_section
                await self.log_status("✅ Fast lookup complete!")
                return wiki_report
            else:
                await self.log_status("🕵️ Wikipedia was sparse. Deep searching the web for more details...")

        # ── STEP 5: Deep Google Search (Targeted) ──
        search_queries = [
            f"{target_name} CEO founder company role net worth news",
            f"{target_name} company employees valuation headquarters"
        ]
        
        all_search_data = ""
        for query in search_queries:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            await self.log_status(f"🔎 Searching: {query}...")
            stext = await self.browse(search_url)
            if stext:
                all_search_data += stext[:4000] + "\n\n"

        if all_search_data:
            await self.log_status(f"🧠 Synthesizing all findings...")
            synthesis_prompt = f"""You are a top business research analyst.
Target: {target_name}
Wikipedia Snippet: {wiki_report[:1000]}
Web Search Data: {all_search_data[:10000]}

Create the absolute best business profile report. Be specific about their CURRENT role and company.
If it's Namita Thapar, she is the Executive Director of Emcure Pharmaceuticals.
If it's a global CEO, find their latest company metrics.

Markdown Sections:
# {target_name}
## 💼 Role & Company
## 💰 Net Worth / Financials
## 🏢 Company Overview (Use a Markdown Table with Details like Employees, Founded, Valuation, HQ)
## 🏭 Industry
## 🏆 Key Achievements
## 📚 Background & Education
"""
            final_report = await self.chat(synthesis_prompt)
            if final_report and len(final_report) > 200:
                if company_section:
                    final_report += "\n\n" + company_section
                await self.log_status("✅ In-depth research complete!")
                return final_report

        # ── STEP 6: Last resort ──
        if db_entry:
            await self.log_status("📊 Fallback: Database report generated.")
            return f"""# {db_entry['full_name']}
## 💼 Role & Company
**{db_entry['role']}** at **{db_entry['company']}**
{company_section}
> ℹ️ Live web data was limited. Above info is from our primary records."""

        if wiki_report:
            return wiki_report

        return f"I couldn't find a detailed business profile for '{target_name}'. Please try a more specific query."

    async def handle_talk(self):
        """Handle general conversation using the LLM."""
        talk_prompt = f"""You are a friendly AI Research Assistant called OpenClaw Agent.
The user said: "{self.user_input}"

Respond naturally and helpfully. Mention that you can research any CEO or founder worldwide.
Keep your response friendly, concise, and helpful. Use markdown formatting."""
        response = await self.chat(talk_prompt)
        if response:
            return response
        return "I'm your **OpenClaw Research Agent**! Just type a name and I'll research them for you!"


if __name__ == "__main__":
    agent = AutonomousResearchAgent("Aman Gupta")
    asyncio.run(agent.run())
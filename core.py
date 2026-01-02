import re
import json
import random
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from faker import Faker

faker = Faker()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

@dataclass
class FormDetails:
    url: str
    form_action_url: str
    questions: Dict[str, Dict[str, Any]]
    hidden_fields: Dict[str, str]

class FormParser:
    """Handles fetching and parsing of Google Forms."""
    
    def __init__(self, url: str):
        self.url = url
        
    def _clean_url(self, url: str) -> str:
        """Cleans the URL to ensure it's in the correct format for fetching."""
        clean_url = url.split("/viewform")[0].split("/edit")[0]
        if clean_url.endswith("/"):
            clean_url = clean_url[:-1]
        return clean_url

    async def fetch_details(self) -> Optional[FormDetails]:
        """Fetches the form HTML and extracts questions/tokens asynchronously."""
        clean_url = self._clean_url(self.url)
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                    elif response.status == 429:
                        print(f"[Alert] IP Blocked (429). You are temporarily timed out. Please wait a few hours (up to 24h) before running again.")
                        return None
                    else:
                        print(f"Error: Server returned status {response.status}")
                        return None
            except Exception as e:
                print(f"Error fetching form: {e}")
                return None

        # Extract FB_PUBLIC_LOAD_DATA_
        match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);\s*<', html_content, re.DOTALL)
        if not match:
             match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);', html_content, re.DOTALL)
        
        if not match:
            print("Error: Could not find form data in page source (REGEX failed).")
            return None

        try:
            data = json.loads(match.group(1))
            questions_raw = data[1][1]
            
            parsed_questions = {}
            if questions_raw:
                for q_item in questions_raw:
                    if not q_item or len(q_item) < 5:
                        continue
                    
                    q_text = q_item[1]
                    q_type_id = q_item[3]
                    q_details = q_item[4]
                    
                    if not q_details:
                        continue

                    for detail in q_details:
                        entry_id = detail[0]
                        options_raw = detail[1]
                        options = []
                        
                        if options_raw:
                            for opt in options_raw:
                                if opt and len(opt) > 0 and opt[0]:
                                    options.append(opt[0])
                        
                        # Determine Type
                        # Mapping based on common Google Form type IDs
                        type_map = {
                            0: "Short Answer",
                            1: "Paragraph",
                            2: "Multiple Choice",
                            3: "Dropdown",
                            4: "Checkboxes",
                            5: "Linear Scale",
                            7: "Multiple Choice Grid",
                            9: "Date",
                            10: "Time"
                        }
                        q_type = type_map.get(q_type_id, "Open Ended")
                        
                        # Fallback heuristic if type is unknown but options exist (likely some choice type)
                        if q_type == "Open Ended" and options:
                             q_type = "Multiple Choice"
                        
                        parsed_questions[f"entry.{entry_id}"] = {
                            "text": q_text,
                            "type": q_type,
                            "options": options,
                            "required": True 
                        }

            # Extract Hidden Fields using Regex (lighter than BS4) or simple string find
            # For robustness, we can use a simple regex for input type=hidden
            hidden_fields = {}
            # Minimal regex to find hidden inputs. 
            # Note: BS4 is robust but blocking, we could start a thread or just use regex.
            # Google forms hidden fields are usually clearly formatted.
            # Let's use a regex for simplicity and speed in this async context, 
            # or we could import BS4 inside and use it (it's fast enough for one file).
            # We'll stick to regex to reduce dependency on bs4 in core if possible, 
            # but main used it. Let's use re for consistency with valid patterns.
            
            # Simple attribute extractor
            input_matches = re.findall(r'<input\s+type="hidden"\s+name="([^"]+)"\s+value="([^"]+)"', html_content)
            for name, value in input_matches:
                 if name not in ["entry"]:
                     hidden_fields[name] = value
            
            form_action_url = clean_url.replace("/u/0/", "/") + "/formResponse"
            
            return FormDetails(
                url=self.url,
                form_action_url=form_action_url,
                questions=parsed_questions,
                hidden_fields=hidden_fields
            )

        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return None

class AsyncFormSpammer:
    """Manages the async spamming process with high reliability."""
    
    def __init__(self, form_details: FormDetails):
        self.details = form_details
        self.stats = {"success": 0, "failed": 0, "retries": 0, "errors": {}}
        self.user_agents = USER_AGENTS

    def generate_response(self, custom_text: str = None, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generates a response based on questions and custom configuration.
        
        Handles splitting Date/Time into proper component fields for Google Forms.
        """
        response = {}
        for q_id, q_data in self.details.questions.items():
            answer = ""
            q_type = q_data["type"]
            
            # 1. Custom Config Priority
            if custom_config and q_id in custom_config:
                answer = custom_config[q_id]
            else:
                # 2. Random Generation
                if q_type in ["Multiple Choice", "Dropdown", "Linear Scale", "Multiple Choice Grid"]:
                    if q_data["options"]:
                        answer = random.choice(q_data["options"])
                elif q_type == "Checkboxes":
                    if q_data["options"]:
                        k = random.randint(1, len(q_data["options"]))
                        answer = random.sample(q_data["options"], k)
                elif q_type == "Date":
                    answer = str(faker.date_between(start_date='-1y', end_date='today'))
                elif q_type == "Time":
                    answer = faker.time(pattern="%H:%M")
                elif q_type in ["Short Answer", "Paragraph", "Open Ended"]:
                    if custom_text:
                        answer = custom_text
                    else:
                        q_text_lower = q_data["text"].lower()
                        if "email" in q_text_lower:
                            answer = faker.email()
                        elif "name" in q_text_lower:
                            answer = faker.name()
                        elif "phone" in q_text_lower or "number" in q_text_lower:
                            answer = faker.phone_number()
                        elif "age" in q_text_lower:
                            answer = str(random.randint(18, 99))
                        elif "time" in q_text_lower:
                            answer = faker.time(pattern="%H:%M")
                        elif "date" in q_text_lower:
                            answer = str(faker.date_between(start_date='-30y', end_date='today'))
                        else:
                            answer = faker.sentence() if q_type == "Short Answer" else faker.paragraph()
            
            # 3. Payload Formatting (Splitting Date/Time)
            if q_type == "Date" and answer:
                # Expect YYYY-MM-DD
                try:
                    y, m, d = answer.split('-')
                    response[f"{q_id}_year"] = y
                    response[f"{q_id}_month"] = m
                    response[f"{q_id}_day"] = d
                except:
                    # Fallback if format is wrong (e.g. from custom input error), send as is?
                    # Or just fail? Let's send as is to be safe, but it will likely 400.
                    response[q_id] = answer
            elif q_type == "Time" and answer:
                # Expect HH:MM
                try:
                    h, m = answer.split(':')
                    response[f"{q_id}_hour"] = h
                    response[f"{q_id}_minute"] = m
                except:
                    response[q_id] = answer
            else:
                response[q_id] = answer
                
        return response

    async def _send_request(self, session: aiohttp.ClientSession, data: Dict[str, Any], retry_count: int = 20):
        """Sends a single POST request with retries and exponential backoff."""
        payload = {**self.details.hidden_fields, **data}
        url = self.details.form_action_url
        
        # User-Agent rotation
        headers = {
            "User-Agent": random.choice(self.user_agents)
        }

        for attempt in range(retry_count + 1):
            try:
                # Add random jitter to avoid exact burst patterns
                await asyncio.sleep(random.uniform(0.05, 0.2))
                
                async with session.post(url, data=payload, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        self.stats["success"] += 1
                        return True, None
                    elif resp.status in [408, 429, 500, 502, 503]:
                        # Rate limit or Server Error - Retry
                        if attempt < retry_count:
                            self.stats["retries"] += 1
                            # Cap backoff at 60 seconds to avoid waiting too long, but wait long enough for 429 reset
                            backoff = min(2 ** attempt, 60)
                            wait_time = backoff + random.uniform(0, 2)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            self.stats["failed"] += 1
                            return False, f"Status {resp.status} (Max Retries)"
                    else:
                        # Other errors (400, 401, 403, 404) - Do not retry usually
                        if attempt < retry_count and resp.status != 404:
                             # Maybe retry 403? Google forms 403 might be sticky.
                             pass
                        
                        self.stats["failed"] += 1
                        return False, f"Status {resp.status}"
                        
            except Exception as e:
                if attempt < retry_count:
                    self.stats["retries"] += 1
                    await asyncio.sleep(1 + attempt)
                    continue
                self.stats["failed"] += 1
                return False, str(e)
                
        return False, "Unknown Error"

    async def run(self, count: int, workers: int, custom_text: str = None, custom_config: Dict[str, Any] = None, progress_callback=None):
        """Runs the spammer with N requests using M concurrent workers."""
        
        queue = asyncio.Queue()
        for _ in range(count):
            queue.put_nowait(True)
            
        async def worker():
            # Create a localized session per worker, or per batch?
            # Creating one session per worker is best for keep-alive.
            # However, for rotation, we might want to clear cookies occasionally?
            # Basic aiohttp session handles cookies automatically. 
            # If Google tracks by cookie, we might want new session per request or clear cookie jar.
            # Let's try ONE session per worker for performance first.
            async with aiohttp.ClientSession() as session:
                while not queue.empty():
                    _ = await queue.get()
                    data = self.generate_response(custom_text, custom_config)
                    success, err = await self._send_request(session, data)
                    
                    if not success and err:
                        err_str = str(err)
                        self.stats["errors"][err_str] = self.stats["errors"].get(err_str, 0) + 1
                    
                    if progress_callback:
                        progress_callback(success)
                    
                    queue.task_done()

        tasks = [asyncio.create_task(worker()) for _ in range(workers)]
        await queue.join()
        
        for t in tasks:
            t.cancel()

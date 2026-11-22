import re
import html
import json
import random
import asyncio
import aiohttp
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
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

# aiohttp deprecated bare-number timeouts; one ClientTimeout for all sessions.
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

GOOGLE_FORM_HOSTS = ("docs.google.com", "forms.gle")

def is_google_form_url(url: str) -> bool:
    """True only for http(s) URLs whose host is a Google Forms domain."""
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return False
    host = (parsed.netloc or "").lower().split("@")[-1]
    host = host[:-1] if host.endswith(".") else host
    return parsed.scheme in ("http", "https") and host in GOOGLE_FORM_HOSTS

# A 200 can be a confirmation page or the form again (closed or rejected), so classify the body.
CONFIRMATION_MARKERS = (
    "freebirdFormviewerViewResponseConfirmationMessage",
    "freebirdFormviewerViewResponseConfirmation",
    "your response has been recorded",
    "your responses have been recorded",
    "thank you for your response",
)
CLOSED_MARKERS = (
    "freebirdFormviewerViewNoLongerAcceptingResponses",
    "no longer accepting responses",
    "not accepting responses",
)
FORM_VIEW_MARKERS = (
    "FB_PUBLIC_LOAD_DATA_",
    "freebirdFormviewerViewFormContent",
    "freebirdFormviewerViewItemsItemErrorMessage",
)


def classify_submission(body: str) -> str:
    """Classify a formResponse body: recorded, closed, rejected, or unknown."""
    if not body:
        return "unknown"
    lowered = body.lower()
    if any(marker.lower() in lowered for marker in CONFIRMATION_MARKERS):
        return "recorded"
    if any(marker.lower() in lowered for marker in CLOSED_MARKERS):
        return "closed"
    if any(marker.lower() in lowered for marker in FORM_VIEW_MARKERS):
        return "rejected"
    return "unknown"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunReport:
    """Append-only JSONL log; appending lets several batches share one file."""

    def __init__(self, path: str, meta: Dict[str, Any]):
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8", buffering=1)
        self._write({"type": "run_start", "at": _utc_now(), **meta})

    def _write(self, payload: Dict[str, Any]) -> None:
        self._fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def record(self, n: int, answers: Dict[str, Any], ok: bool,
               verdict: Optional[str], error: Optional[str]) -> None:
        self._write({
            "type": "response",
            "n": n,
            "at": _utc_now(),
            "ok": bool(ok),
            "verified": verdict,
            "error": error,
            "answers": answers,
        })

    def close(self, stats: Dict[str, Any], status: str) -> None:
        self._write({
            "type": "run_end",
            "at": _utc_now(),
            "status": status,
            "success": stats["success"],
            "failed": stats["failed"],
            "unverified": stats["unverified"],
            "retries": stats["retries"],
        })
        self._fh.close()


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
        """Fetches the form HTML and extracts questions/tokens asynchronously.

        Raises ValueError for non-Google-Forms URLs; returns None on fetch/parse failure.
        """
        if not is_google_form_url(self.url):
            raise ValueError(f"Not a Google Forms URL: {self.url}")
        clean_url = self._clean_url(self.url)
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            try:
                async with session.get(self.url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                    else:
                        raise RuntimeError(f"Failed to fetch form (HTTP {response.status})")
            except aiohttp.ClientError as e:
                raise RuntimeError(f"Failed to connect to form: {e}") from e

        match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\])\s*;\s*<', html_content, re.DOTALL)
        if not match:
             match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\])\s*;', html_content, re.DOTALL)
        
        if not match:
            raise RuntimeError("Form data not found in page (not a public form, or the page changed).")

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
                        required = bool(len(detail) > 2 and detail[2])
                        options = []
                        # Grid rows: detail[3] is the row label, not the grid title.
                        row_label = detail[3] if len(detail) > 3 and isinstance(detail[3], str) and detail[3].strip() else None
                        
                        if options_raw:
                            for opt in options_raw:
                                if opt and len(opt) > 0 and opt[0]:
                                    options.append(opt[0])
                        
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
                        
                        # Unknown type with options is likely a choice type.
                        if q_type == "Open Ended" and options:
                             q_type = "Multiple Choice"
                        
                        parsed_questions[f"entry.{entry_id}"] = {
                            "text": f"{q_text} — {row_label}" if row_label else q_text,
                            "type": q_type,
                            "options": options,
                            "required": required
                        }

            # Hidden inputs carry fvv/partialResponse/pageHistory/fbzx, required for the POST
            hidden_fields = {}
            for tag in re.findall(r"<input\b[^>]*>", html_content):
                attrs = dict(re.findall(r"""([\w-]+)\s*=\s*["']([^"']*)["']""", tag))
                name = attrs.get("name")
                if attrs.get("type") == "hidden" and name and name != "entry":
                    hidden_fields[name] = html.unescape(attrs.get("value", ""))

            # Google credits only the page named by the last pageHistory entry, so list every index.
            # Each type-8 item is a page break.
            page_count = 1 + sum(1 for q_item in (questions_raw or [])
                                 if len(q_item) > 3 and q_item[3] == 8)
            if page_count > 1:
                hidden_fields["pageHistory"] = ",".join(str(i) for i in range(page_count))
            
            form_action_url = clean_url.replace("/u/0/", "/") + "/formResponse"
            action_match = re.search(r'<form[^>]+action="([^"]+)"', html_content)
            if action_match:
                form_action_url = urljoin(self.url, html.unescape(action_match.group(1)))
            
            return FormDetails(
                url=self.url,
                form_action_url=form_action_url,
                questions=parsed_questions,
                hidden_fields=hidden_fields
            )

        except (ValueError, IndexError, KeyError, TypeError) as e:
            # Malformed FB_PUBLIC_LOAD_DATA_ shape: surface it, don't print-and-None.
            raise RuntimeError(f"Form data unreadable: {e}") from e

class SubmissionEngine:
    """Generates and submits responses with configurable concurrency and retries."""
    
    def __init__(self, form_details: FormDetails):
        self.details = form_details
        self.stats = {"success": 0, "failed": 0, "retries": 0, "unverified": 0, "errors": {}}
        self.user_agents = USER_AGENTS
        # Per-question answer counts for successful submissions.
        self.distributions: Dict[str, Dict[str, int]] = {}

    def _count_answers(self, answers: Dict[str, Any]) -> None:
        for q_id, value in answers.items():
            key = " | ".join(value) if isinstance(value, (list, tuple)) else str(value)
            seen = self.distributions.setdefault(q_id, {})
            seen[key] = seen.get(key, 0) + 1

    def generate_response(self, custom_text: str = None, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generates a response based on questions and custom configuration.
        
        Handles splitting Date/Time into proper component fields for Google Forms.
        """
        response = {}
        for q_id, q_data in self.details.questions.items():
            answer = ""
            q_type = q_data["type"]

            if custom_config and q_id in custom_config:
                answer = custom_config[q_id]
            else:
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

            # Split Date/Time into the component fields Google expects.
            if q_type == "Date" and answer:
                parts = str(answer).split("-")
                if len(parts) == 3:
                    response[f"{q_id}_year"], response[f"{q_id}_month"], response[f"{q_id}_day"] = parts
                else:
                    response[q_id] = answer
            elif q_type == "Time" and answer:
                parts = str(answer).split(":")
                if len(parts) >= 2:
                    response[f"{q_id}_hour"], response[f"{q_id}_minute"] = parts[0], parts[1]
                else:
                    response[q_id] = answer
            else:
                response[q_id] = answer

        return response

    async def _send_request(self, session: aiohttp.ClientSession, data: Dict[str, Any], retry_count: int = 5):
        """Sends a single POST request with retries and exponential backoff."""
        payload = [(k, v) for k, v in self.details.hidden_fields.items()]
        for k, v in data.items():
            if isinstance(v, (list, tuple)):
                payload.extend((k, item) for item in v)
            elif v not in (None, ""):
                payload.append((k, v))
        url = self.details.form_action_url
        
        headers = {
            "User-Agent": random.choice(self.user_agents)
        }

        for attempt in range(retry_count + 1):
            try:
                # Add random jitter to avoid exact burst patterns
                await asyncio.sleep(random.uniform(0.05, 0.2))
                
                async with session.post(url, data=payload, headers=headers) as resp:
                    if resp.status == 200:
                        try:
                            body = await resp.text()
                        except Exception:
                            body = ""
                        verdict = classify_submission(body)
                        if verdict == "closed":
                            self.stats["failed"] += 1
                            return False, "Form is no longer accepting responses", verdict
                        if verdict == "rejected":
                            self.stats["failed"] += 1
                            return False, "Answer rejected (not recorded)", verdict
                        self.stats["success"] += 1
                        if verdict == "unknown":
                            # 200 with an unrecognised page counts as success but is not proven.
                            self.stats["unverified"] += 1
                        return True, None, verdict
                    elif resp.status in [408, 429, 500, 502, 503]:
                        if attempt < retry_count:
                            self.stats["retries"] += 1
                            # Cap backoff at 8s so one rate-limited request cannot pin a worker for the run.
                            backoff = min(2 ** attempt, 8)
                            wait_time = backoff + random.uniform(0, 2)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            self.stats["failed"] += 1
                            return False, f"Status {resp.status} (Max Retries)", None
                    else:
                        # 400/401/403/404 etc: not transient, retrying cannot fix them.
                        self.stats["failed"] += 1
                        return False, f"Status {resp.status}", None
                        
            except Exception as e:
                if attempt < retry_count:
                    self.stats["retries"] += 1
                    await asyncio.sleep(1 + attempt)
                    continue
                self.stats["failed"] += 1
                return False, str(e), None

        return False, "Unknown Error", None

    async def run(self, count: int, workers: int, custom_text: str = None,
                  custom_config: Dict[str, Any] = None, progress_callback=None,
                  report_path: str = None):
        """Submits count responses using workers concurrent tasks."""

        queue = asyncio.Queue()
        for _ in range(count):
            queue.put_nowait(True)

        report = None
        if report_path:
            report = RunReport(report_path, {
                "url": self.details.url,
                "count": count,
                "workers": workers,
            })
        sent = 0

        async def worker():
            nonlocal sent
            # One session per worker: keep-alive across its submissions.
            async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
                while True:
                    _ = await queue.get()
                    data = {}
                    verdict = None
                    try:
                        data = self.generate_response(custom_text, custom_config)
                        success, err, verdict = await self._send_request(session, data)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:  # noqa: BLE001 - fail one response, not the whole run
                        success, err = False, f"generate: {exc}"
                        self.stats["failed"] += 1
                    sent += 1
                    if success:
                        self._count_answers(data)
                    if report:
                        report.record(sent, data, success, verdict, err)
                    if not success and err:
                        self.stats["errors"][str(err)] = self.stats["errors"].get(str(err), 0) + 1
                    if progress_callback:
                        progress_callback(success)
                    queue.task_done()

        tasks = [asyncio.create_task(worker()) for _ in range(workers)]
        status = "cancelled"
        try:
            await queue.join()
            status = "done"
        finally:
            # Cancel workers too; cancelling queue.join() alone strands them mid-POST.
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if report:
                report.close(self.stats, status)

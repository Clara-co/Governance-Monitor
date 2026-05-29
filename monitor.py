import anthropic
import smtplib
import json
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_RECIPIENTS = os.environ["EMAIL_RECIPIENTS"]

FORTUNE_500_WATCH = [
    "Microsoft", "Walmart", "Amazon", "Apple", "Alphabet", "Google",
    "Meta", "JPMorgan", "Goldman Sachs", "Bank of America", "Citigroup",
    "Wells Fargo", "UnitedHealth", "CVS", "Exxon", "Chevron",
    "Berkshire", "AT&T", "Verizon", "Ford", "General Motors",
    "Boeing", "Lockheed", "IBM", "Oracle", "Salesforce",
    "Intel", "Nvidia", "Cisco", "Qualcomm", "Tesla", "Disney",
    "Comcast", "Netflix", "Pfizer", "Merck", "JPMorgan Chase",
    "UPS", "FedEx", "Home Depot", "Costco", "Target",
]

SYSTEM_PROMPT = (
    "You are the AI Governance News Monitor for the UNC Hussman "
    "Fortune 500 AI Governance Audit research project at the Hussman School of "
    "Journalism and Media, University of North Carolina at Chapel Hill. "
    "Your task: search the web for AI governance news from the past 7 days and "
    "return a structured briefing. "
    "SEARCH PRIORITY: 1) SEC filings on EDGAR 2) Company press releases and IR pages "
    "3) Reuters, Bloomberg, WSJ, Financial Times, AP, HBR, KPMG, Deloitte, PwC "
    "4) CIO Dive, MIT Technology Review, The Verge. Skip aggregators and SEO blogs. "
    "COVER: Fortune 500 AI announcements, policies, named AI executives, "
    "governance incidents, lawsuits, regulatory actions, new AI frameworks, board changes. "
    "FLAG items involving: Microsoft, Walmart, Amazon, Apple, Alphabet, Meta, "
    "JPMorgan, Goldman Sachs, IBM, Oracle, Salesforce, Intel, Nvidia, Tesla, Disney, Comcast. "
    "RETURN a single JSON object only, no markdown, no preamble: "
    '{"weekOf":"Month DD YYYY",'
    '"headlineIncidents":[{"headline":"...","company":"...","date":"...","summary":"One sentence no em dashes.","url":"verified url or empty","urlVerified":true}],'
    '"newPoliciesFrameworks":[{"headline":"...","company":"...","date":"...","summary":"...","url":"...","urlVerified":true}],'
    '"regulatoryLegal":[{"headline":"...","company":"...","date":"...","summary":"...","url":"...","urlVerified":true}],'
    '"worthWatching":[{"headline":"...","company":"...","date":"...","summary":"...","url":"...","urlVerified":true}]} '
    "RULES: 3 to 5 items per section. No em dashes. One plain sentence per summary. "
    "Only include stories confirmed via web search."
)


def run_briefing():
    today = datetime.today()
    week_ago = today - timedelta(days=7)
    date_str = today.strftime("%B %d, %Y")
    range_str = week_ago.strftime("%B %d") + " to " + date_str

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": "Run the weekly AI governance briefing for " + range_str + ". Search all priority sources and return the JSON briefing."
        }]
    )

    text_block = next((b for b in response.content if b.type == "text"), None)
    if not text_block:
        raise ValueError("No text response from Claude.")

    clean = text_block.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


def is_fortune_500(text):
    return any(co.lower() in text.lower() for co in FORTUNE_500_WATCH)


def build_plain_text(data):
    date_str = data.get("weekOf", datetime.today().strftime("%B %d, %Y"))
    lines = [
        "AI GOVERNANCE MONITOR - WEEKLY BRIEFING",
        "Week of " + date_str,
        "Prepared for: UNC Hussman Fortune 500 AI Governance Audit Project",
        "Hussman School of Journalism and Media, UNC Chapel Hill",
        "",
    ]
    sections = [
        ("HEADLINE INCIDENTS", data.get("headlineIncidents", [])),
        ("NEW POLICIES AND FRAMEWORKS", data.get("newPoliciesFrameworks", [])),
        ("REGULATORY AND LEGAL", data.get("regulatoryLegal", [])),
        ("WORTH WATCHING", data.get("worthWatching", [])),
    ]
    for label, items in sections:
        if not items:
            continue
        lines.append("--- " + label + " ---")
        for i, item in enumerate(items, 1):
            f500 = " [Fortune 500]" if is_fortune_500(json.dumps(item)) else ""
            url = item.get("url", "")
            verified = item.get("urlVerified", True)
            lines.append(str(i) + ". " + item.get("headline", "") + f500)
            meta = " | ".join(filter(None, [item.get("company"), item.get("date")]))
            if meta:
                lines.append("   " + meta)
            lines.append("   " + item.get("summary", ""))
            if url:
                lines.append("   " + (url if verified else "URL unverified - search for this story"))
            lines.append("")
        lines.append("")
    lines += [
        "---",
        "Generated by the UNC Hussman AI Governance News Monitor.",
        "This briefing is produced automatically each Monday morning.",
        "Hussman School of Journalism and Media, UNC Chapel Hill.",
    ]
    return "\n".join(lines)


def build_html(data):
    date_str = data.get("weekOf", datetime.today().strftime("%B %d, %Y"))
    tag_colors = {
        "HEADLINE INCIDENTS": ("#FEE2E2", "#991B1B"),
        "NEW POLICIES AND FRAMEWORKS": ("#DBEAFE", "#1E40AF"),
        "REGULATORY AND LEGAL": ("#FEF3C7", "#92400E"),
        "WORTH WATCHING": ("#D1FAE5", "#065F46"),
    }
    sections = [
        ("HEADLINE INCIDENTS", data.get("headlineIncidents", [])),
        ("NEW POLICIES AND FRAMEWORKS", data.get("newPoliciesFrameworks", [])),
        ("REGULATORY AND LEGAL", data.get("regulatoryLegal", [])),
        ("WORTH WATCHING", data.get("worthWatching", [])),
    ]
    sections_html = ""
    for label, items in sections:
        if not items:
            continue
        bg, fg = tag_colors.get(label, ("#F3F4F6", "#111827"))
        sections_html += '<div style="margin-bottom:24px;">'
        sections_html += '<div style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:11px;font-weight:600;text-transform:uppercase;padding:4px 10px;border-radius:4px;margin-bottom:12px;">' + label + '</div>'
        for item in items:
            f500 = is_fortune_500(json.dumps(item))
            url = item.get("url", "")
            verified = item.get("urlVerified", True)
            meta = " | ".join(filter(None, [item.get("company"), item.get("date")]))
            badge = '<span style="background:#FEF3C7;color:#92400E;font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px;margin-right:6px;">Fortune 500</span>' if f500 else ""
            meta_html = '<div style="font-size:12px;color:#6B7280;margin-bottom:4px;">' + meta + '</div>' if meta else ""
            url_html = '<a href="' + url + '" style="font-size:12px;color:#2563EB;word-break:break-all;">' + (url if verified else "URL unverified") + '</a>' if url else ""
            sections_html += '<div style="border:1px solid #E5E7EB;border-radius:8px;padding:14px 16px;margin-bottom:10px;background:#FFFFFF;">'
            sections_html += '<div style="margin-bottom:4px;">' + badge + '<span style="font-size:14px;font-weight:600;color:#111827;">' + item.get("headline", "") + '</span></div>'
            sections_html += meta_html
            sections_html += '<div style="font-size:13px;color:#374151;line-height:1.6;">' + item.get("summary", "") + '</div>'
            sections_html += url_html
            sections_html += '</div>'
        sections_html += '</div>'

    html = '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
    html += '<body style="margin:0;padding:0;background:#F9FAFB;font-family:Arial,sans-serif;">'
    html += '<div style="max-width:640px;margin:32px auto;background:#FFFFFF;border-radius:12px;border:1px solid #E5E7EB;overflow:hidden;">'
    html += '<div style="background:#1B3A6B;padding:24px 28px;">'
    html += '<div style="font-size:20px;font-weight:700;color:#FFFFFF;margin-bottom:4px;">AI Governance Monitor</div>'
    html += '<div style="font-size:13px;color:#93C5FD;">Weekly Briefing - Week of ' + date_str + '</div>'
    html += '<div style="font-size:12px;color:#60A5FA;margin-top:2px;">UNC Hussman Fortune 500 AI Governance Audit Project</div>'
    html += '</div>'
    html += '<div style="padding:24px 28px;">' + sections_html + '</div>'
    html += '<div style="background:#F3F4F6;padding:16px 28px;border-top:1px solid #E5E7EB;font-size:12px;color:#9CA3AF;">'
    html += 'Generated by the UNC Hussman AI Governance News Monitor. Hussman School of Journalism and Media, UNC Chapel Hill.'
    html += '</div></div></body></html>'
    return html


def send_email(data):
    date_str = data.get("weekOf", datetime.today().strftime("%B %d, %Y"))
    subject = "AI Governance Monitor - Weekly Briefing - " + date_str
    recipients = [r.strip() for r in EMAIL_RECIPIENTS.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(build_plain_text(data), "plain"))
    msg.attach(MIMEText(build_html(data), "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipients, msg.as_string())

    print("Briefing sent to: " + ", ".join(recipients))


if __name__ == "__main__":
    print("Running AI Governance briefing...")
    briefing = run_briefing()
    print("Briefing generated: " + str(briefing.get("weekOf")))
    send_email(briefing)
    print("Done.")

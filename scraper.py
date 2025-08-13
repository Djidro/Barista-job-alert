import os
import requests
from bs4 import BeautifulSoup
import time
import json
import base64
from datetime import datetime
import pytz

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GH_TOKEN = os.getenv('GH_TOKEN')
GITHUB_USERNAME = "YOUR_GITHUB_USERNAME"  # Change this!

JOB_SITES = {
    'Jooble': 'https://jooble.org/SearchResult?ukw=barista&r={country}',
    'NaukriGulf': 'https://www.naukrigulf.com/barista-jobs-in-{country}',
    'Jora': 'https://jooble.org/SearchResult?ukw=barista&r={country}'
}
COUNTRIES = ['Oman', 'Saudi-Arabia', 'Qatar', 'Kuwait', 'Dubai']
KEYWORDS = ['barista', 'coffee', 'café', 'cafe']

def load_seen_jobs():
    try:
        url = f"https://{GITHUB_USERNAME}.github.io/barista-job-alerts/seen_jobs.json"
        response = requests.get(url)
        return response.json()
    except:
        return {}

def save_seen_jobs(jobs):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/barista-job-alerts/contents/seen_jobs.json"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": "Update seen jobs",
        "content": base64.b64encode(json.dumps(jobs).encode()).decode(),
        "branch": "gh-pages"
    }
    response = requests.put(url, headers=headers, json=data)
    return response.status_code == 200

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_jobs = []
    
    for country in COUNTRIES:
        for site, url_template in JOB_SITES.items():
            try:
                url = url_template.format(country=country)
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Example scraping logic (adjust selectors as needed)
                jobs = soup.select('.job-listing')  # Update this selector
                for job in jobs:
                    title = job.select_one('.title').text.strip()
                    link = job.find('a')['href']
                    job_id = f"{site}_{country}_{hash(link)}"
                    
                    if job_id not in seen_jobs and any(kw.lower() in title.lower() for kw in KEYWORDS):
                        new_jobs.append({
                            'title': title,
                            'link': link,
                            'country': country,
                            'source': site,
                            'id': job_id
                        })
                        seen_jobs[job_id] = True
            except Exception as e:
                print(f"Error scraping {site} for {country}: {e}")
    
    if new_jobs:
        save_seen_jobs(seen_jobs)
        for job in new_jobs:
            message = f"<b>New Barista Job in {job['country']}</b>\n{job['title']}\n<a href='{job['link']}'>Apply Here</a>"
            send_telegram_message(message)

if __name__ == "__main__":
    print(f"Starting job scrape at {datetime.now(pytz.utc)}")
    scrape_jobs()

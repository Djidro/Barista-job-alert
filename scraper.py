import requests
from bs4 import BeautifulSoup
import time
import schedule
import pytz
from datetime import datetime
import os
import json

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'your_bot_token')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'your_chat_id')
JOB_SITES = {
    'Jooble': 'https://jooble.org/SearchResult?ukw=barista&r={country}',
    'NaukriGulf': 'https://www.naukrigulf.com/barista-jobs-in-{country}',
    'Jora': 'https://jooble.org/SearchResult?ukw=barista&r={country}'
}
COUNTRIES = ['Oman', 'Saudi-Arabia', 'Qatar', 'Kuwait', 'Dubai']
KEYWORDS = ['barista', 'coffee', 'café', 'cafe']
CHECK_INTERVAL = 60  # minutes

# Storage for seen jobs
seen_jobs_file = 'seen_jobs.json'

def load_seen_jobs():
    try:
        with open(seen_jobs_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_seen_jobs(seen_jobs):
    with open(seen_jobs_file, 'w') as f:
        json.dump(seen_jobs, f)

seen_jobs = load_seen_jobs()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

def scrape_jooble(country):
    jobs = []
    url = JOB_SITES['Jooble'].format(country=country)
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for job in soup.select('.vacancy_wrapper'):
            title = job.select_one('.position').text.strip()
            company = job.select_one('.company').text.strip() if job.select_one('.company') else "N/A"
            location = job.select_one('.location').text.strip() if job.select_one('.location') else country
            link = job.select_one('a')['href']
            
            if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                job_id = f"jooble_{country}_{hash(link)}"
                if job_id not in seen_jobs:
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': link,
                        'source': 'Jooble',
                        'id': job_id
                    })
                    seen_jobs[job_id] = True
    except Exception as e:
        print(f"Error scraping Jooble for {country}: {e}")
    return jobs

def scrape_naukrigulf(country):
    jobs = []
    url = JOB_SITES['NaukriGulf'].format(country=country.lower().replace(' ', '-'))
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for job in soup.select('.srp-tuple-wrapper'):
            title = job.select_one('.srp-tuple-title').text.strip()
            company = job.select_one('.comp-name').text.strip() if job.select_one('.comp-name') else "N/A"
            location = job.select_one('.loc').text.strip() if job.select_one('.loc') else country
            link = job.select_one('a')['href']
            
            if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                job_id = f"naukrigulf_{country}_{hash(link)}"
                if job_id not in seen_jobs:
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': link,
                        'source': 'NaukriGulf',
                        'id': job_id
                    })
                    seen_jobs[job_id] = True
    except Exception as e:
        print(f"Error scraping NaukriGulf for {country}: {e}")
    return jobs

def scrape_jora(country):
    jobs = []
    url = JOB_SITES['Jora'].format(country=country)
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for job in soup.select('.job-item'):
            title = job.select_one('.job-title').text.strip()
            company = job.select_one('.company').text.strip() if job.select_one('.company') else "N/A"
            location = job.select_one('.location').text.strip() if job.select_one('.location') else country
            link = job.select_one('a')['href']
            
            if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                job_id = f"jora_{country}_{hash(link)}"
                if job_id not in seen_jobs:
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': link,
                        'source': 'Jora',
                        'id': job_id
                    })
                    seen_jobs[job_id] = True
    except Exception as e:
        print(f"Error scraping Jora for {country}: {e}")
    return jobs

def check_jobs():
    print(f"Checking for new jobs at {datetime.now(pytz.utc)}")
    all_jobs = []
    
    for country in COUNTRIES:
        all_jobs.extend(scrape_jooble(country))
        all_jobs.extend(scrape_naukrigulf(country))
        all_jobs.extend(scrape_jora(country))
    
    for job in all_jobs:
        message = (
            f"<b>New Barista Job in {job['location']}</b>\n"
            f"<b>Title:</b> {job['title']}\n"
            f"<b>Company:</b> {job['company']}\n"
            f"<b>Source:</b> {job['source']}\n"
            f"<a href='{job['link']}'>Apply Here</a>"
        )
        send_telegram_message(message)
    
    save_seen_jobs(seen_jobs)
    print(f"Found {len(all_jobs)} new jobs")

def main():
    # Initial check
    check_jobs()
    
    # Schedule hourly checks
    schedule.every(CHECK_INTERVAL).minutes.do(check_jobs)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()

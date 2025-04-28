import os
import json
import requests
from bs4 import BeautifulSoup
from kafka import KafkaProducer

def scrape(keyword):
    url = f"https://patentscope.wipo.int/search/en/search.jsf?query={keyword}"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for entry in soup.select(".resultItem"):  # adjust selector as needed
        title_el = entry.select_one(".resultItemTitle")
        pub_el = entry.select_one(".publicationNumber")
        if title_el and pub_el:
            results.append({
                "keyword": keyword,
                "title": title_el.get_text(strip=True),
                "publication_number": pub_el.get_text(strip=True)
            })
    return results

if __name__ == "__main__":
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    keyword = os.getenv("SCRAPER_KEYWORD", "default")
    producer = KafkaProducer(
        bootstrap_servers=[kafka_servers],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    records = scrape(keyword)
    for rec in records:
        producer.send("patent_raw", rec)
    producer.flush()
    print(f"Sent {len(records)} records for keyword '{keyword}'")
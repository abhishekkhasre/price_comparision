from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import re
import logging

# Load environment variables and set up logging
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Supported domains per country
ECOMMERCE_DOMAINS = {
    "IN": ["flipkart.com", "amazon.in", "croma.com", "reliancedigital.in", "vijaysales.com", "tatacliq.com"],
    "US": ["amazon.com", "walmart.com", "bestbuy.com", "target.com", "ebay.com", "bhphotovideo.com"],
    "UK": ["amazon.co.uk", "argos.co.uk", "currys.co.uk", "ebay.co.uk", "johnlewis.com", "ao.com"],
    "CA": ["amazon.ca", "walmart.ca", "bestbuy.ca", "newegg.ca", "staples.ca", "canadacomputers.com"],
    "AU": ["amazon.com.au", "jbhifi.com.au", "harveynorman.com.au", "ebay.com.au", "officeworks.com.au", "thegoodguys.com.au"]
}

def clean_price(price_str):
    """Clean a price string and return it as a float."""
    try:
        cleaned = re.sub(r"[^\d.]", "", price_str)
        return float(cleaned)
    except Exception as e:
        logging.error(f"Failed to clean price '{price_str}': {e}")
        return 0.0

def get_price_results_from_serpapi(country: str, query: str):
    """Get product prices using SerpAPI for the given country and query."""
    country = country.upper()
    domains = ECOMMERCE_DOMAINS.get(country, [])
    
    if not domains:
        raise ValueError(f"Unsupported country: {country}")

    results = []
    symbol_map = {"₹": "INR", "$": "USD", "£": "GBP"}

    for domain in domains:
        params = {
            "engine": "google",
            "q": f"{query} site:{domain}",
            "api_key": os.getenv("SERPAPI_KEY"),
            "num": 10,
            "hl": "en",
            "gl": country.lower(),
        }

        try:
            search = GoogleSearch(params)
            response = search.get_dict()
            organic_results = response.get("organic_results", [])

            for item in organic_results:
                title = item.get("title")
                link = item.get("link")
                snippet = item.get("snippet", "")

                price_match = re.search(r"(₹|£|\$)\s?[\d,]+(?:\.\d+)?", snippet)
                if not (title and link and price_match):
                    continue

                symbol = price_match.group(1)
                price = clean_price(price_match.group())
                if price <= 0:
                    continue

                results.append({
                    "productName": title,
                    "price": price,
                    "currency": symbol_map.get(symbol, "USD"),
                    "link": link
                })

        except Exception as e:
            logging.error(f"[SERPAPI ERROR] Domain: {domain} - {e}")

    # Sort by price (lowest first)
    results.sort(key=lambda x: x["price"])

    return results

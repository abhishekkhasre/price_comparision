# 🌐 Price Comparison API

This project is a Flask-based web service that allows you to fetch product prices across major e-commerce retailers using **Selenium** and **SerpAPI**.

It supports multiple countries (US, UK, India, etc.) and retrieves price data using two methods:
- Direct scraping with **Selenium**
- Search API integration via **Google SerpAPI**

---

## 🚀 Features

- 🛒 Price scraping from top retailers like Amazon, Walmart, Target, Apple, Flipkart, Croma, and more
- 🌍 Country-based filtering (US, UK, India, CA, AU)
- 🔍 Dual-mode search:
  - `/selenium/search` – Real-time scraping
  - `/api/search` – Fast search using Google’s SerpAPI
- 🧠 Automatic retries on failure
- 📉 Results sorted by lowest price
- 🧪 Built-in error handling and logging

---

## 🏗️ Technologies Used

- Python 3.10+
- Flask
- Selenium + Chrome WebDriver
- BeautifulSoup4
- SerpAPI (`google-search-results`)
- dotenv for environment config

---

## 📸 Postman Screenshot:
![image](https://github.com/user-attachments/assets/144c5312-314f-4010-b54e-cbf827c060b4)


<sup>🔗 If the image doesn't load, [click here to view it on Google Drive](https://drive.google.com/file/d/1YXSmeNZwERmqBq_5Ti_j1UiCg8yw6-Hm/view?usp=drivesdk)</sup>

---

## 📦 Installation

```bash
git clone https://github.com/abhishekkhasre/price_comparision.git
cd pprice_comparision
pip install -r requirements.txt



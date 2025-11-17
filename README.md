# 🕸️ Advanced Web Scraping & Metadata Extraction System  
### **Internship Project – Knimbus Technology Private Limited**

---

## 📌 Overview
This project is an **advanced Python-based web scraping and metadata extraction system** developed during my internship at **Knimbus Technology Pvt. Ltd.**

The tool automatically crawls **multiple publisher websites (500+)**, extracts rich metadata, and generates:

- ✔️ A **PDF report** (professional format)  
- ✔️ A **JSON file** with all raw extracted data  
- ✔️ A **log file** to track success/errors  

This system is built for **scalability, speed, and automation**, making it ideal for large metadata extraction tasks.

---

## 🚀 Features

### 🔍 Comprehensive Metadata Extraction
The crawler extracts the following information from each website:

- Title  
- Meta Description  
- Meta Keywords  
- Author  
- Publish Date  
- Canonical URL  
- Language Tag  
- Open Graph (OG) Metadata  
- Twitter Card Metadata  
- Schema.org Structured Data (JSON-LD)  
- Headings: H1–H6  
- Links (internal + external)  
- Images (src, alt, title)  
- HTTP Status Code  
- Content Type  

---

### ⚙️ Multi-Threaded Crawling (High Performance)
Powered by `ThreadPoolExecutor`:
- Faster crawling through concurrency  
- Auto rate-limiting  
- Robust error handling  

---

### 📄 Automatic PDF Report Generation
The PDF includes:
- Summary table of all websites  
- Per-website detailed metadata  
- Errors (if any)  
- Clean formatted layout using **ReportLab**



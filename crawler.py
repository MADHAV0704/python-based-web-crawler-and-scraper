import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

class WebCrawler:
    """Advanced web crawler for extracting metadata from publisher websites"""
    
    def __init__(self, max_workers=10, timeout=30, delay=1):
        self.max_workers = max_workers
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def extract_metadata(self, url):
        """Extract comprehensive metadata from a webpage"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            metadata = {
                'url': url,
                'title': self._get_title(soup),
                'description': self._get_description(soup),
                'keywords': self._get_keywords(soup),
                'author': self._get_author(soup),
                'publish_date': self._get_publish_date(soup),
                'og_data': self._get_open_graph(soup),
                'twitter_data': self._get_twitter_card(soup),
                'canonical_url': self._get_canonical(soup),
                'language': self._get_language(soup),
                'headings': self._get_headings(soup),
                'links': self._get_links(soup, url),
                'images': self._get_images(soup, url),
                'schema_org': self._get_schema_org(soup),
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type', ''),
                'scraped_at': datetime.now().isoformat()
            }
            
            logging.info(f"Successfully scraped: {url}")
            return metadata
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
    
    def _get_title(self, soup):
        """Extract page title"""
        title = soup.find('title')
        if title:
            return title.get_text().strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '').strip()
        
        return 'No title found'
    
    def _get_description(self, soup):
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '').strip()
        
        return 'No description found'
    
    def _get_keywords(self, soup):
        """Extract meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            return meta_keywords.get('content', '').strip()
        return ''
    
    def _get_author(self, soup):
        """Extract author information"""
        author = soup.find('meta', attrs={'name': 'author'})
        if author:
            return author.get('content', '').strip()
        
        article_author = soup.find('meta', property='article:author')
        if article_author:
            return article_author.get('content', '').strip()
        
        return ''
    
    def _get_publish_date(self, soup):
        """Extract publication date"""
        date_patterns = [
            {'property': 'article:published_time'},
            {'name': 'pubdate'},
            {'name': 'publishdate'},
            {'itemprop': 'datePublished'}
        ]
        
        for pattern in date_patterns:
            date_tag = soup.find('meta', attrs=pattern)
            if date_tag:
                return date_tag.get('content', '').strip()
        
        return ''
    
    def _get_open_graph(self, soup):
        """Extract Open Graph metadata"""
        og_data = {}
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        
        for tag in og_tags:
            prop = tag.get('property', '')
            content = tag.get('content', '')
            if prop and content:
                og_data[prop] = content
        
        return og_data
    
    def _get_twitter_card(self, soup):
        """Extract Twitter Card metadata"""
        twitter_data = {}
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        
        for tag in twitter_tags:
            name = tag.get('name', '')
            content = tag.get('content', '')
            if name and content:
                twitter_data[name] = content
        
        return twitter_data
    
    def _get_canonical(self, soup):
        """Extract canonical URL"""
        canonical = soup.find('link', rel='canonical')
        if canonical:
            return canonical.get('href', '')
        return ''
    
    def _get_language(self, soup):
        """Extract page language"""
        html_tag = soup.find('html')
        if html_tag:
            return html_tag.get('lang', '')
        return ''
    
    def _get_headings(self, soup):
        """Extract all headings (H1-H6)"""
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [h.get_text().strip() for h in h_tags if h.get_text().strip()]
        return headings
    
    def _get_links(self, soup, base_url):
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            absolute_url = urljoin(base_url, href)
            links.append({
                'text': link.get_text().strip(),
                'url': absolute_url
            })
        return links[:50]  # Limit to first 50 links
    
    def _get_images(self, soup, base_url):
        """Extract all images"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        return images[:20]  # Limit to first 20 images
    
    def _get_schema_org(self, soup):
        """Extract Schema.org structured data"""
        schema_data = []
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                schema_data.append(data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return schema_data
    
    def crawl_multiple(self, urls):
        """Crawl multiple URLs concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.extract_metadata, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    time.sleep(self.delay)  # Rate limiting
                except Exception as e:
                    logging.error(f"Error processing {url}: {str(e)}")
                    results.append({
                        'url': url,
                        'error': str(e),
                        'scraped_at': datetime.now().isoformat()
                    })
        
        return results


class PDFReportGenerator:
    """Generate comprehensive PDF reports from scraped data"""
    
    def __init__(self, filename='crawler_report.pdf'):
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=letter)
        self.styles = getSampleStyleSheet()
        self.story = []
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14
        )
    
    def generate_report(self, scraped_data):
        """Generate PDF report from scraped data"""
        
        # Title page
        self.story.append(Paragraph("Web Crawler Report", self.title_style))
        self.story.append(Spacer(1, 0.3*inch))
        self.story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        self.story.append(Paragraph(f"Total Sites Scraped: {len(scraped_data)}", self.normal_style))
        self.story.append(PageBreak())
        
        # Summary table
        self._add_summary_table(scraped_data)
        self.story.append(PageBreak())
        
        # Detailed data for each site
        for idx, data in enumerate(scraped_data, 1):
            self._add_site_details(data, idx)
            if idx < len(scraped_data):
                self.story.append(PageBreak())
        
        # Build PDF
        self.doc.build(self.story)
        logging.info(f"PDF report generated: {self.filename}")
    
    def _add_summary_table(self, scraped_data):
        """Add summary table to report"""
        self.story.append(Paragraph("Summary Overview", self.heading_style))
        self.story.append(Spacer(1, 0.2*inch))
        
        table_data = [['#', 'URL', 'Title', 'Status']]
        
        for idx, data in enumerate(scraped_data, 1):
            url = data.get('url', 'N/A')
            title = data.get('title', 'N/A')[:50]  # Truncate long titles
            status = 'Success' if 'error' not in data else 'Failed'
            
            table_data.append([str(idx), url[:40], title, status])
        
        table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 2.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.story.append(table)
    
    def _add_site_details(self, data, index):
        """Add detailed information for a single site"""
        url = data.get('url', 'N/A')
        
        self.story.append(Paragraph(f"Site #{index}: {url}", self.title_style))
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'error' in data:
            self.story.append(Paragraph(f"<b>Error:</b> {data['error']}", self.normal_style))
            return
        
        # Basic metadata
        self.story.append(Paragraph("<b>Basic Metadata</b>", self.heading_style))
        basic_data = [
            ('Title', data.get('title', 'N/A')),
            ('Description', data.get('description', 'N/A')[:200]),
            ('Author', data.get('author', 'N/A')),
            ('Publish Date', data.get('publish_date', 'N/A')),
            ('Language', data.get('language', 'N/A')),
            ('Canonical URL', data.get('canonical_url', 'N/A')),
            ('Status Code', str(data.get('status_code', 'N/A'))),
        ]
        
        for label, value in basic_data:
            self.story.append(Paragraph(f"<b>{label}:</b> {value}", self.normal_style))
            self.story.append(Spacer(1, 0.1*inch))
        
        # Headings
        if data.get('headings'):
            self.story.append(Paragraph("<b>Headings</b>", self.heading_style))
            for level, headings in data['headings'].items():
                if headings:
                    self.story.append(Paragraph(f"<b>{level.upper()}:</b> {', '.join(headings[:3])}", self.normal_style))
        
        self.story.append(Spacer(1, 0.1*inch))
        
        # Links count
        links_count = len(data.get('links', []))
        images_count = len(data.get('images', []))
        self.story.append(Paragraph(f"<b>Links Found:</b> {links_count}", self.normal_style))
        self.story.append(Paragraph(f"<b>Images Found:</b> {images_count}", self.normal_style))


def main():
    """Main execution function"""
    
    # Example usage with multiple publisher URLs
    urls = [
        'https://www.example.com',
        'https://www.python.org',
        'https://www.github.com',
        # Add up to 500+ URLs here
    ]
    
    print("=" * 60)
    print("Advanced Web Crawler with PDF Report Generation")
    print("=" * 60)
    
    # Get URL from user or use default list
    user_input = input("\nEnter website URL (or press Enter to use example list): ").strip()
    
    if user_input:
        urls = [user_input]
    
    print(f"\nStarting crawl of {len(urls)} URL(s)...")
    
    # Initialize crawler
    crawler = WebCrawler(max_workers=10, timeout=30, delay=1)
    
    # Crawl URLs
    results = crawler.crawl_multiple(urls)
    
    print(f"\nCrawling complete! Scraped {len(results)} sites.")
    
    # Generate PDF report
    print("\nGenerating PDF report...")
    pdf_generator = PDFReportGenerator('crawler_report.pdf')
    pdf_generator.generate_report(results)
    
    print("\n" + "=" * 60)
    print("Report generated successfully: crawler_report.pdf")
    print("=" * 60)
    
    # Also save as JSON for further processing
    with open('crawler_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("Raw data saved to: crawler_data.json")


if __name__ == "__main__":
    main()
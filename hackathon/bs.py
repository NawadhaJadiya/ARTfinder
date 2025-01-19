import requests
from bs import BeautifulSoup
import json
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime

def get_product_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        def extract_with_patterns(patterns, validation_func=None):
            
            """Generic function to extract data using patterns"""
            for pattern in patterns:
                # Check meta tags first
                if pattern.startswith('meta'):
                    element = soup.select_one(pattern)
                    if element and element.get('content'):
                        content = element.get('content')
                        if not validation_func or validation_func(content):
                            return content
                
                # Then check regular elements
                elements = soup.select(pattern)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and (not validation_func or validation_func(text)):
                        return text
            return None

        def find_price():
            patterns = [
                'meta[property="product:price:amount"]',
                '[class*=price]', '[class*=Price]', '[id*=price]',
                'span:contains("₹")', 'span:contains("$")', 'span:contains("€")',
                '.price', '.product-price', '.sale-price'
            ]
            def is_valid_price(text):
                return bool(re.search(r'[\d.,]+', text) and re.search(r'[$₹€]', text))
            return extract_with_patterns(patterns, is_valid_price) or 'Price not found'

        def find_title():
            patterns = [
                'meta[property="og:title"]',
                'meta[name="title"]',
                '[class*=title]', '[class*=name]',
                'h1', '.product-title', '#product-title'
            ]
            def is_valid_title(text):
                return len(text.split()) >= 2 and '<' not in text
            return extract_with_patterns(patterns, is_valid_title) or 'Title not found'

        def find_images():
            image_patterns = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                '[class*=product] img', '[class*=gallery] img',
                '.product-image img', '.main-image img'
            ]
            images = []
            
            # Check meta tags
            for pattern in image_patterns[:2]:
                element = soup.select_one(pattern)
                if element and element.get('content'):
                    images.append(element.get('content'))
            
            # Check img tags
            for pattern in image_patterns[2:]:
                for img in soup.select(pattern):
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src and src not in images:
                        images.append(src)
            
            # Convert relative URLs to absolute
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            images = [urljoin(base_url, img) if not img.startswith(('http://', 'https://')) else img
                     for img in images]
            
            return images

        def find_description():
            patterns = [
                'meta[name="description"]',
                'meta[property="og:description"]',
                '[class*=description]', '[class*=details]',
                '#description', '.product-description'
            ]
            def is_valid_description(text):
                return len(text.split()) >= 10
            return extract_with_patterns(patterns, is_valid_description) or 'Description not found'

        def find_brand():
            patterns = [
                'meta[property="product:brand"]',
                '[class*=brand]', '[class*=manufacturer]',
                '.brand', '#brand'
            ]
            def is_valid_brand(text):
                return len(text.split()) <= 3
            return extract_with_patterns(patterns, is_valid_brand) or 'Brand not found'

        def find_specifications():
            spec_patterns = [
                '[class*=specification] li', '[class*=specs] li',
                '.product-specs li', '.technical-details li',
                'table[class*=specification] tr'
            ]
            specs = {}
            for pattern in spec_patterns:
                elements = soup.select(pattern)
                for element in elements:
                    text = element.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        specs[key.strip()] = value.strip()
            return specs

        # Extract all data
        product_data = {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': find_title(),
            'brand': find_brand(),
            'price': find_price(),
            'description': find_description(),
            'specifications': find_specifications(),
            'images': find_images(),
            'extracted_at': datetime.now().isoformat()
        }
        
        # Print extracted data
        print("\n=== Product Data ===")
        for key, value in product_data.items():
            if key not in ['images', 'specifications']:
                print(f"{key.title()}: {value}")
        
        print("\nImages:")
        for img in product_data['images']:
            print(f"• {img}")
            
        print("\nSpecifications:")
        for key, value in product_data['specifications'].items():
            print(f"• {key}: {value}")
            
        # Save to JSON
        with open('product_data.json', 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
            
        return product_data

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if _name_ == "_main_":
    # Example usage
    url = input("Enter product URL: ")
    get_product_data(url)
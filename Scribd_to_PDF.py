# Version 1.0
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
import threading
import time
import requests
import re
import img2pdf
from PIL import Image
import io

default_name = "document.pdf"

def main():
    # Box style
    print()
    print("\033[1;94m  ┌─────────────────────────────────────────────┐")
    print("\033[1;94m  │ \033[1;95m🚀 Welcome to Scribd Scraper by ILFforever\033[1;94m  │")
    print("\033[1;94m  └─────────────────────────────────────────────┘\033[0m")
    print("\033[90m ⚠️  This program is meant for educational use only ⚠️\033[0m")    
    print()
    input_url = input("Input Scribd url : ")
    if not validate_scribd_url(input_url):
        print("Enter a Valid Scribd url")
        sys.exit()
    
    jsonp = fetch_jsonp(input_url)
    images = fetch_image_urls_optimized(extract_url(jsonp))
    max_width = input("Input Max Width (default 1200) : ").strip()
    quality = input("Input Quality (default 85%) : ").strip()
    file_name = input(f"Input pdf-name (default {default_name}) : ").strip()

    print()

    max_width = int(max_width) if max_width else 1200
    quality = int(quality) if quality else 85
    if not file_name:
        file_name = default_name
    elif not file_name.lower().endswith('.pdf'):
        file_name += '.pdf'

    #create_pdf_from_urls(images, file_name, max_width, quality)
    create_pdf_from_urls_threaded(images, file_name, max_width, quality)

def fetch_jsonp(input_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    response = requests.get(input_url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        print(f"Invalid response code : {response.status_code}")
        sys.exit()
        
    # Find content after the script tag
    start_marker = "docManager.addPage"
    end_marker = " if (window.docManagerIEAdded != true) {"

    # In addition find name
    start_name_marker = "</script><title>"
    end_name_marker = "</title>"
    
    content = response.text
    
    # Find the position of the script tag
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    start_name_pos = content.find(start_name_marker)
    end_name_pos = content.find(end_name_marker)

    if start_name_pos != -1 and end_name_pos != -1:
        full = content[start_name_pos + len(start_name_marker) : end_name_pos]
        global default_name
        default_name = full.split('|')[0].strip()
        default_name += ".pdf"
        
    if start_pos != -1 and end_pos != -1:
        # Get everything after the script tag
        return content[start_pos:end_pos]
        
    else:
        print("Content tag not found on page")
        
def validate_scribd_url(url):
   """Validate that URL is a Scribd document URL"""
   pattern = r'^https://www\.scribd\.com/document/\d+/'
   return bool(re.match(pattern, url))

#Extract URLs from Json result
def extract_url(jsonp_content):
        pattern = r'docManager\.addPage\(\{[^}]*pageNum:\s*(\d+)[^}]*contentUrl:\s*["\']([^"\']+)["\'][^}]*\}\);'
        
        matches = re.findall(pattern, jsonp_content)
        
        # Convert to list of tuples with page number as int
        page_url_tuples = [[int(page_num), url] for page_num, url in matches]
        
        # Sort by page number
        page_url_tuples.sort(key=lambda x: x[0])
        
        return page_url_tuples

# Optimized version using multi-threading
def fetch_image_urls_optimized(page_url_tuples, max_workers=10):
    """
    Ultra-optimized version using session reuse
    """
    total_pages = len(page_url_tuples)
    print(f"⚡ Fetching {total_pages} pages ...")
    
    start_time = time.time()
    completed = 0
    found_img = 0
    notfound_img = []
    results = {}
    
    progress_lock = threading.Lock()
    
    def fetch_with_session(items_chunk):
        """Process a chunk of items with a reused session"""
        with requests.Session() as session:
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            chunk_results = []
            for page_num, content_url in items_chunk:
                try:
                    response = session.get(content_url, timeout=15)
                    response.raise_for_status()
                    
                    # Extract image URL
                    orig_pattern = r'orig=\\"([^"]+)\\"'
                    orig_match = re.search(orig_pattern, response.text)
                    
                    if orig_match:
                        image_url = orig_match.group(1)
                        image_url = image_url.replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'")
                        chunk_results.append((page_num, content_url, image_url, True))
                    else:
                        fallback_pattern = r'orig=\\\\"([^"]+)\\\\"'
                        fallback_match = re.search(fallback_pattern, response.text)
                        if fallback_match:
                            image_url = fallback_match.group(1)
                            chunk_results.append((page_num, content_url, image_url, True))
                        else:
                            chunk_results.append((page_num, content_url, "No image URL found", False))
                            
                except Exception as e:
                    chunk_results.append((page_num, content_url, f"Error: {e}", False))
                
                # Update progress
                nonlocal completed
                with progress_lock:
                    completed += 1
                    progress = (completed / total_pages) * 100
                    bar_length = 50
                    filled_length = int(bar_length * completed // total_pages)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    print(f'\r⚡ Progress: |{bar}| {progress:.1f}% ({completed}/{total_pages}) - {rate:.1f} req/s', end='', flush=True)
            
            return chunk_results
    
    # Split work into chunks for session reuse
    chunk_size = max(1, total_pages // max_workers)
    chunks = [page_url_tuples[i:i + chunk_size] for i in range(0, total_pages, chunk_size)]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_with_session, chunk) for chunk in chunks]
        
        for future in as_completed(futures):
            chunk_results = future.result()
            for page_num, content_url, image_url, success in chunk_results:
                results[page_num] = [page_num, content_url, image_url]
                if success:
                    found_img += 1
                else:
                    notfound_img.append(page_num)
    
    print()
    results_list = [results[page_num] for page_num in sorted(results.keys())]
    
    print("=" * 30)
    print(f"✅ Found {found_img} images from {total_pages} pages")
    
    if notfound_img:
        print(f"❌ Missing {len(notfound_img)} images: {notfound_img[:10]}{'...' if len(notfound_img) > 10 else ''}")
    
    return results_list

def process_single_image(item, headers, max_width, quality):
    """
    Process a single image - download and convert to JPEG bytes
    """
    page_num, content_url, image_url = item
    
    try:
        # Download image to memory
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Process image in memory
        image_bytes = io.BytesIO(response.content)
        
        with Image.open(image_bytes) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if needed
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to memory buffer as JPEG
            output_buffer = io.BytesIO()
            img.save(output_buffer, 'JPEG', quality=quality, optimize=True)
            output_buffer.seek(0)
            
            return (page_num, output_buffer.getvalue(), True)
            
    except Exception as e:
        return (page_num, str(e), False)

def create_pdf_from_urls_threaded(image_data, output_pdf='document.pdf', max_width=1200, quality=85, max_workers=8):
    """
    Create PDF directly from image URLs using multithreading
    """
    valid_images = [item for item in image_data if len(item) == 3 and item[2].startswith('http')]
    
    if not valid_images:
        print("No valid image URLs found.")
        return
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    }
    
    total_images = len(valid_images)
    print(f"Creating PDF from {total_images} images using {max_workers} threads...")
    
    start_time = time.time()
    completed = 0
    successful = 0
    failed = 0
    results = {} 

    progress_lock = threading.Lock()
    
    def update_progress():
        nonlocal completed
        with progress_lock:
            completed += 1
            progress = (completed / total_images) * 100
            bar_length = 50
            filled_length = int(bar_length * completed // total_images)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            eta = (total_images - completed) / rate if rate > 0 else 0
            print(f'\r ⏳ Progress: |{bar}| {progress:.1f}% ({completed}/{total_images}) - {rate:.1f} img/s - ETA: {eta:.0f}s', end='', flush=True)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(process_single_image, item, headers, max_width, quality): item 
            for item in valid_images
        }
        
        # Process completed futures
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            page_num = item[0]
            
            try:
                page_num_result, data, success = future.result()
                if success:
                    results[page_num] = data
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
            
            update_progress()
    
    print()  
    
    if not results:
        print("No images were successfully processed.")
        return
    
    print(f"\n📝 Creating PDF from {len(results)} processed images...")
    
    # Sort results by page number to maintain correct order
    processed_images = [results[page_num] for page_num in sorted(results.keys())]
    
    try:
        # Create PDF using img2pdf
        with open(output_pdf, "wb") as pdf_file:
            pdf_bytes = img2pdf.convert(processed_images)
            pdf_file.write(pdf_bytes)
        
        pdf_size = os.path.getsize(output_pdf)
        total_time = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ PDF created successfully!")
        print(f"📁 Output file: {os.path.abspath(output_pdf)}")
        print(f"📊 File size: {pdf_size / (1024*1024):.1f} MB")
        print(f"📄 Pages: {len(processed_images)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"🚀 Average speed: {successful/total_time:.1f} images/second")
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")


if __name__ == "__main__":

    main()

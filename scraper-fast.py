from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import datetime
import re
import concurrent.futures

# Add time tracking functionality
class TaskTimer:
    def __init__(self):
        self.start_time = time.time()
        self.section_times = {}
        self.last_checkpoint = self.start_time
    
    def checkpoint(self, section_name):
        now = time.time()
        elapsed = now - self.last_checkpoint
        total = now - self.start_time
        self.section_times[section_name] = elapsed
        self.last_checkpoint = now
        print(f"✅ {section_name}: {elapsed:.2f} seconds (Total: {total:.2f}s)")
        return elapsed
    
    def summary(self):
        total_time = time.time() - self.start_time
        print("\n⏱️ PERFORMANCE SUMMARY:")
        print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print("Section breakdown:")
        for section, duration in self.section_times.items():
            percentage = (duration / total_time) * 100
            print(f"  • {section}: {duration:.2f}s ({percentage:.1f}%)")

# Initialize timer
timer = TaskTimer()
print("Starting Facebook comment scraper...")

print("Setting up Chrome options...")
chrome_options = Options()
chrome_options.add_argument("--headless")  # Headless mode for speed
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
chrome_options.add_argument("--window-size=1280,720")  # Smaller window reduces resource usage
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

print("Installing ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
timer.checkpoint("Browser initialization")

# Block unnecessary resources (CSS, images, fonts, etc.) using CDP
driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*.css", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.woff", "*.ttf", "*.ico"]})
driver.execute_cdp_cmd("Network.enable", {})

# Maximum comments to collect
MAX_COMMENTS = 1000

# Create CSV filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"facebook_comments_{timestamp}.csv"

print("Starting browser and loading the post...")
fb_post_url = "https://web.facebook.com/photo/?fbid=992188076425376&set=a.588916660085855"
driver.get(fb_post_url)
wait = WebDriverWait(driver, 10)  # 10-second timeout
timer.checkpoint("Page load")

try:
    # Try to close any login popups if present
    try:
        close_buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@aria-label='Close']")))
        for button in close_buttons:
            if button.is_displayed():
                driver.execute_script("arguments[0].click();", button)
                print("Closed a popup")
                time.sleep(0.2)  # Shorter wait time
    except Exception as e:
        print("No popups to close:", str(e))
    timer.checkpoint("Handle popups")
    
    # Consolidated XPath for "View more" buttons
    view_more_xpath = ("//span[contains(text(),'View') and (contains(text(),'more comments') or contains(text(),'more'))] | "
                       "//div[@role='button']//span[contains(text(),'View')]")
    
    def click_view_more_buttons():
        buttons = driver.find_elements(By.XPATH, view_more_xpath)
        count = 0
        for btn in buttons:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                count += 1
                time.sleep(0.2)  # Reduced wait after each click
        return count

    initial_clicks = click_view_more_buttons()
    print(f"Initially clicked {initial_clicks} 'View more' buttons")
    timer.checkpoint("Initial view more clicks")
    
    # Define multiple comment detection patterns
    comment_patterns = [
        "//div[contains(@aria-label, 'Comment')]",
        "//div[@data-testid='comment']",
        "//div[contains(@class, 'x1y1aw1k')]",
        "//div[@role='article']",
        "//div[contains(@class, 'x16tdsg8')]"
    ]
    
    # Function to count comments using the patterns (will return count from first successful pattern)
    def count_comments():
        for pattern in comment_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    return len(elements)
            except Exception:
                continue
        return 0
    
    # Optimized scrolling routine with fewer pauses
    scroll_count = 0
    max_scrolls = 200
    last_count = 0
    no_change_count = 0
    
    scroll_start_time = time.time()
    print("Starting to scroll and load comments...")
    
    while scroll_count < max_scrolls and no_change_count < 4:
        scroll_count += 1
        print(f"Scrolling iteration {scroll_count}/{max_scrolls}")
        
        # Scroll: every 3rd iteration scroll to the bottom, otherwise page down
        if scroll_count % 3 == 0:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        
        time.sleep(0.8)  # Shortened wait time for new content
        if scroll_count % 2 == 0:
            click_view_more_buttons()
        
        current_count = count_comments()
        print(f"Found {current_count} comments so far")
        if current_count > last_count:
            last_count = current_count
            no_change_count = 0
        else:
            no_change_count += 1
            
        if current_count >= MAX_COMMENTS:
            print(f"Target of {MAX_COMMENTS} comments reached.")
            break
    
    # Record scrolling time
    scroll_time = time.time() - scroll_start_time
    print(f"Scrolling completed in {scroll_time:.2f} seconds")
    timer.checkpoint("Comments scrolling")
    
    print("Extracting comments...")
    comments_text = []
    
    def process_comment(raw_text):
        if not raw_text.strip():
            return None
        lines = raw_text.split('\n')
        if len(lines) <= 1:
            return None
        
        # Badge indicators that may be present in the text
        badge_indicators = ["top fan", "valued commenter", "admin", "moderator", "new member", "founder"]
        first_line_badge = lines and any(badge in lines[0].lower() for badge in badge_indicators)
        lines_to_skip = 2 if first_line_badge else 1
        lines_to_skip = min(lines_to_skip, len(lines) - 1)
        content_lines = lines[lines_to_skip:]
        
        filtered_lines = []
        for line in content_lines:
            # Skip timestamps like "1d", "19h", etc.
            if re.match(r'^\d+[dhmswy]$', line.strip()):
                continue
            # Skip simple number lines (reaction counts)
            if re.match(r'^\d+$', line.strip()):
                continue
            if any(badge in line.lower() for badge in badge_indicators):
                continue
            filtered_lines.append(line)
        
        comment_text = "\n".join(filtered_lines)
        comment_text = re.sub(r'\s+\d+[dhmswy](\s+\d+)?$', '', comment_text)
        comment_text = re.sub(r'\b\d{1,2}[ymwdhs]\b', '', comment_text)
        return comment_text.strip() if comment_text.strip() else None
    
    # Try different comment patterns until comments are found
    extraction_start = time.time()
    for pattern in comment_patterns:
        try:
            comment_elements = driver.find_elements(By.XPATH, pattern)
            if comment_elements:
                print(f"Extracting {len(comment_elements)} comments using pattern: {pattern}")
                raw_texts = [elem.text.strip() for elem in comment_elements]
                
                processing_start = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    processed_comments = list(executor.map(process_comment, raw_texts))
                processing_time = time.time() - processing_start
                print(f"Comment processing took {processing_time:.2f} seconds")
                
                comments_text.extend([c for c in processed_comments if c])
                break  # Stop if we've found comments using one pattern
        except Exception as e:
            print(f"Error with pattern {pattern}: {str(e)}")
    
    extraction_time = time.time() - extraction_start
    print(f"Comment extraction took {extraction_time:.2f} seconds")
    timer.checkpoint("Comments extraction")
    
    # Limit results to MAX_COMMENTS
    if len(comments_text) > MAX_COMMENTS:
        comments_text = comments_text[:MAX_COMMENTS]
    
    # Write the comments to a CSV file efficiently
    print(f"Writing {len(comments_text)} comments to {csv_filename}")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Comment Number", "Comment Text"])
        for i, text in enumerate(comments_text, 1):
            writer.writerow([i, text])
    timer.checkpoint("CSV writing")
    
    print(f"Successfully saved {len(comments_text)} comments to {csv_filename}")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("Closing browser...")
    driver.quit()
    timer.checkpoint("Browser cleanup")
    
    # Print final timing summary
    timer.summary()
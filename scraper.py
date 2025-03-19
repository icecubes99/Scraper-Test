from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import datetime
import re
import concurrent.futures

print("Setting up Chrome options...")
chrome_options = Options()
# Performance-oriented options
chrome_options.add_argument("--headless")  # Run in headless mode for speed
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images for speed
chrome_options.add_argument("--window-size=1280,720")  # Smaller window for less resource usage
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

# Maximum comments to collect
MAX_COMMENTS = 100

print("Installing ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Create CSV filename
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"facebook_comments_{timestamp}.csv"

print("Starting browser...")
fb_post_url = "https://www.facebook.com/photo/?fbid=1049393963882034&set=a.459043889583714"
driver.get(fb_post_url)

# Use WebDriverWait instead of sleep
print("Waiting for page to load...")
wait = WebDriverWait(driver, 10)  # 10-second timeout

try:
    # Try to close any login popups
    try:
        # Wait for popup to appear with a short timeout
        close_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@aria-label='Close']")),
            message="Looking for close buttons"
        )
        
        if close_buttons:
            for button in close_buttons:
                if button.is_displayed():
                    button.click()
                    print("Closed a popup")
                    time.sleep(0.5)  # Reduced wait time
    except Exception:
        print("No popups found or couldn't close them")
    
    # Click view more comments buttons if present
    view_more_patterns = [
        "//span[contains(text(), 'View more comments')]",
        "//span[contains(text(), 'View') and contains(text(), 'more')]",
        "//div[@role='button']//span[contains(text(), 'View')]"
    ]
    
    # Use a single function to click all "View more" buttons
    def click_view_more_buttons():
        buttons_clicked = 0
        for pattern in view_more_patterns:
            try:
                buttons = driver.find_elements(By.XPATH, pattern)
                for button in buttons:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        buttons_clicked += 1
                        time.sleep(0.5)  # Reduced wait time
            except:
                pass
        return buttons_clicked
    
    # Initial click on view more buttons
    buttons_clicked = click_view_more_buttons()
    print(f"Initially clicked {buttons_clicked} 'View more' buttons")
    
    # Define comment patterns for detection
    comment_patterns = [
        "//div[contains(@aria-label, 'Comment')]",
        "//div[@data-testid='comment']",
        "//div[contains(@class, 'x1y1aw1k')]",
        "//div[@role='article']",
        "//div[contains(@class, 'x16tdsg8')]"
    ]
    
    # Function to count visible comments - more efficient
    def count_comments():
        for pattern in comment_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    return len(elements)
            except:
                continue
        return 0
    
    # Optimized scrolling - fewer pauses, more targeted
    print("Scrolling to load comments...")
    scroll_count = 0
    max_scrolls = 15  # Keep this as is, but with faster scroll cycles
    last_count = 0
    consecutive_no_change = 0
    
    # More efficient scrolling
    while scroll_count < max_scrolls and consecutive_no_change < 3:
        scroll_count += 1
        print(f"Fast scroll {scroll_count}/{max_scrolls}")
        
        # Scroll more efficiently
        if scroll_count % 3 == 0:
            # Scroll to bottom every third time
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            # Regular scroll
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        
        # Shorter wait time - just enough for content to load
        time.sleep(1)
        
        # Periodically click "View more" buttons
        if scroll_count % 2 == 0:
            click_view_more_buttons()
        
        # Count comments after scrolling
        current_count = count_comments()
        print(f"Found {current_count} comments so far")
        
        # Check if we've found new comments
        if current_count > last_count:
            last_count = current_count
            consecutive_no_change = 0
        else:
            consecutive_no_change += 1
            
        # Break if we have enough comments
        if current_count >= MAX_COMMENTS:
            print(f"Reached target of {MAX_COMMENTS} comments")
            break
    
    # Collect all the comments we found - Do this faster
    print("Extracting comments...")
    comments_text = []
    
    def process_comment(raw_text):
        if not raw_text.strip():
            return None
            
        # Split by newlines and process
        lines = raw_text.split('\n')
        if len(lines) <= 1:
            return None
        
        # Define badge indicators to check for
        badge_indicators = ["top fan", "valued commenter", "admin", "moderator", "new member", "founder"]
        
        # First, determine if we have a badge-name-comment structure
        # We need to check if the first line is a badge indicator
        first_line_is_badge = len(lines) > 0 and any(badge in lines[0].lower() for badge in badge_indicators)
        
        # Determine how many lines to skip
        if first_line_is_badge:
            lines_to_skip = 2  # Skip both badge and name
        else:
            lines_to_skip = 1  # Skip just the name
        
        # Make sure we don't try to skip more lines than we have
        lines_to_skip = min(lines_to_skip, len(lines) - 1)
        
        # Remove the first lines (badge and/or name)
        content_lines = lines[lines_to_skip:]
        
        # Process each line to remove timestamps and reactions
        filtered_lines = []
        for line in content_lines:
            # Skip lines that are just timestamps (like "1d", "19h", etc.)
            if re.match(r'^\d+[dhmswy]$', line.strip()):
                continue
            
            # Skip lines that are just numbers (likely reaction counts)
            if re.match(r'^\d+$', line.strip()):
                continue
            
            # Skip any additional badge indicators that might appear elsewhere
            if any(badge in line.lower() for badge in badge_indicators):
                continue
            
            filtered_lines.append(line)
        
        # Join the filtered lines back together
        comment_text = '\n'.join(filtered_lines)
        
        # Remove timestamps at the end of lines - more comprehensive regex
        comment_text = re.sub(r'\s+\d+[dhmswy](\s+\d+)?$', '', comment_text)
        comment_text = re.sub(r'\b\d{1,2}[ymwdhs]\b', '', comment_text)  # Remove "9y", "32w" anywhere in text
        
        # Only return non-empty comments
        if comment_text.strip():
            return comment_text
        return None
    
    # Try different patterns to find comments - find the right one faster
    for pattern in comment_patterns:
        try:
            comment_elements = driver.find_elements(By.XPATH, pattern)
            if comment_elements:
                print(f"Found {len(comment_elements)} comments using pattern: {pattern}")
                
                # Extract all raw texts first (faster than processing one at a time)
                raw_texts = [element.text.strip() for element in comment_elements]
                
                # Process comments in parallel for speed
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    processed_comments = list(executor.map(process_comment, raw_texts))
                
                # Filter out None values and add to comments_text
                comments_text.extend([c for c in processed_comments if c])
                
                # If we found comments, no need to try other patterns
                break
        except Exception as e:
            print(f"Error with pattern {pattern}: {str(e)}")
    
    # Limit to MAX_COMMENTS
    if len(comments_text) > MAX_COMMENTS:
        comments_text = comments_text[:MAX_COMMENTS]
    
    # Write to CSV file - do this efficiently
    print(f"Writing {len(comments_text)} comments to {csv_filename}")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Comment Number", "Comment Text"])  # Header
        
        # Write all rows at once without printing each one
        for i, text in enumerate(comments_text, 1):
            writer.writerow([i, text])
            
        print(f"Successfully saved {len(comments_text)} comments to {csv_filename}")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("Closing browser...")
    driver.quit()
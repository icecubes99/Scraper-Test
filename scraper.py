from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import datetime
import random
import re

print("Setting up Chrome options...")
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Comment this out to see the browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")
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
fb_post_url = "https://web.facebook.com/photo/?fbid=1154447183384015&set=a.362804292548312"
driver.get(fb_post_url)

print("Waiting for page to load...")
time.sleep(5)

try:
    # Try to close any login popups
    try:
        close_buttons = driver.find_elements(By.XPATH, "//div[@aria-label='Close']")
        if close_buttons:
            for button in close_buttons:
                if button.is_displayed():
                    button.click()
                    print("Closed a popup")
                    time.sleep(1)
    except:
        print("No popups found or couldn't close them")
    
    # Click view more comments buttons if present
    view_more_patterns = [
        "//span[contains(text(), 'View more comments')]",
        "//span[contains(text(), 'View') and contains(text(), 'more')]",
        "//div[@role='button']//span[contains(text(), 'View')]"
    ]
    
    for pattern in view_more_patterns:
        try:
            buttons = driver.find_elements(By.XPATH, pattern)
            for button in buttons:
                if button.is_displayed():
                    print(f"Clicking: {button.text}")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
        except:
            pass
    
    # Scroll to load more comments
    print("Scrolling to load comments...")
    scroll_count = 0
    max_scrolls = 15
    
    # Define comment patterns for detection
    comment_patterns = [
        "//div[contains(@aria-label, 'Comment')]",
        "//div[@data-testid='comment']",
        "//div[contains(@class, 'x1y1aw1k')]",
        "//div[@role='article']",
        "//div[contains(@class, 'x16tdsg8')]"
    ]
    
    # Function to count visible comments
    def count_comments():
        for pattern in comment_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    return len(elements)
            except:
                continue
        return 0
    
    # Scroll until we have enough comments or reach max scrolls
    last_count = 0
    consecutive_no_change = 0
    last_scroll_with_new_comments = 0
    
    while scroll_count < max_scrolls and consecutive_no_change < 3:
        scroll_count += 1
        print(f"Scroll {scroll_count}/{max_scrolls}")
        
        # Scroll down
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2 + random.random())
        
        # Try clicking "View more" buttons again after scrolling
        for pattern in view_more_patterns:
            try:
                buttons = driver.find_elements(By.XPATH, pattern)
                for button in buttons:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
            except:
                pass
        
        # Count comments after scrolling
        current_count = count_comments()
        print(f"Found {current_count} comments so far")
        
        # Check if we've found new comments
        if current_count > last_count:
            last_count = current_count
            consecutive_no_change = 0
            last_scroll_with_new_comments = scroll_count
        else:
            consecutive_no_change += 1
            
        # Break if we have enough comments
        if current_count >= MAX_COMMENTS:
            print(f"Reached target of {MAX_COMMENTS} comments")
            break
    
    # Collect all the comments we found
    print("Extracting comments...")
    comments_text = []
    
    # Try different patterns to find comments
    for pattern in comment_patterns:
        try:
            comment_elements = driver.find_elements(By.XPATH, pattern)
            if comment_elements:
                print(f"Found {len(comment_elements)} comments using pattern: {pattern}")
                
                for element in comment_elements:
                    # Get the raw text
                    raw_text = element.text.strip()
                    
                    # Split by newlines and process
                    lines = raw_text.split('\n')
                    if len(lines) > 1:
                        # Remove the first line (usually the name)
                        content_lines = lines[1:]
                        
                        # Process each line to remove timestamps and reactions
                        filtered_lines = []
                        for line in content_lines:
                            # Skip lines that are just timestamps (like "1d", "19h", etc.)
                            if re.match(r'^\d+[dhmswy]$', line.strip()):
                                continue
                            
                            # Skip lines that are just numbers (likely reaction counts)
                            if re.match(r'^\d+$', line.strip()):
                                continue
                            
                            filtered_lines.append(line)
                        
                        # Join the filtered lines back together
                        comment_text = '\n'.join(filtered_lines)
                        
                        # Remove timestamps at the end of lines
                        comment_text = re.sub(r'\s+\d+[dhmswy](\s+\d+)?$', '', comment_text)
                        
                        # Only add non-empty comments
                        if comment_text.strip():
                            comments_text.append(comment_text)
                
                # If we found comments, no need to try other patterns
                break
        except Exception as e:
            print(f"Error with pattern {pattern}: {str(e)}")
    
    # Limit to MAX_COMMENTS
    if len(comments_text) > MAX_COMMENTS:
        comments_text = comments_text[:MAX_COMMENTS]
    
    # Write to CSV file
    print(f"Writing {len(comments_text)} comments to {csv_filename}")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Comment Number", "Comment Text"])  # Header
        
        for i, text in enumerate(comments_text, 1):
            writer.writerow([i, text])
            print(f"Comment {i}: {text[:50]}..." if len(text) > 50 else text)
    
    print(f"Successfully saved {len(comments_text)} comments to {csv_filename}")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("Closing browser...")
    driver.quit()
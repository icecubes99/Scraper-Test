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
import os
import random

print("Setting up Chrome options...")
# Set up Selenium with headless mode
chrome_options = Options()
# Comment this out to see the browser in action (can help with debugging)
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
chrome_options.add_argument("--window-size=1920,1080")  # Larger window to see more content

# Set the maximum number of comments to collect
MAX_COMMENTS = 100

print("Installing ChromeDriver...")
# Use webdriver_manager to automatically install ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Create filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"facebook_comments_{timestamp}.csv"

print("Starting browser...")
# Replace this with a public Facebook post URL
fb_post_url = "https://www.facebook.com/photo/?fbid=894303803956454&set=a.632843580102479"  

# Open the Facebook post
driver.get(fb_post_url)

print("Waiting for page to load...")
time.sleep(5)  # Wait for initial content to load

try:
    # Look for login popup and close it if present
    try:
        close_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Close' or contains(@class, 'x92rtbv')]"))
        )
        close_button.click()
        print("Closed login popup")
    except:
        print("No login popup found or couldn't close it")
    
    # Look for and click on "View more comments" buttons or similar
    more_comments_buttons = [
        "//span[contains(text(), 'View more comments')]",
        "//span[contains(text(), 'View') and contains(text(), 'more')]",
        "//div[contains(@role, 'button')]//*[contains(text(), 'View')]",
        "//div[@role='button']//span[contains(text(), 'previous comments')]"
    ]
    
    print("Looking for 'View more comments' buttons...")
    view_more_clicked = False
    for selector in more_comments_buttons:
        try:
            buttons = driver.find_elements(By.XPATH, selector)
            if buttons:
                for button in buttons:
                    try:
                        if button.is_displayed():
                            print(f"Clicking '{button.text}' button")
                            driver.execute_script("arguments[0].click();", button)
                            view_more_clicked = True
                            time.sleep(3)
                    except:
                        continue
        except Exception as e:
            print(f"Error finding more comments button: {str(e)}")
    
    if view_more_clicked:
        print("Clicked on 'View more comments' buttons")
    else:
        print("No 'View more comments' buttons found or clickable")
    
    print("Scrolling to load comments...")
    # Scroll more times to load more comments - increased for more comments
    comment_count = 0
    last_count = 0
    scroll_attempts = 0
    max_scroll_attempts = 15  # Increased from 5 to 15
    
    # Helper function to count comments
    def count_current_comments():
        for pattern in comment_patterns:
            try:
                current_comments = driver.find_elements(By.XPATH, pattern)
                if current_comments:
                    return len(current_comments), pattern
            except:
                continue
        return 0, ""
    
    # Define comment patterns here for the function to use
    comment_patterns = [
        "//div[contains(@aria-label, 'Comment')]",
        "//div[@data-testid='comment']",
        "//div[contains(@class, 'x1y1aw1k xn6708d')]",
        "//div[contains(@class, 'x1n2onr6')]//div[contains(@class, 'x16tdsg8')]",
        "//ul[contains(@class, 'x1n2onr6')]//li",
        "//div[@role='article']"
    ]
    
    # Scroll until we have enough comments or stop making progress
    while comment_count < MAX_COMMENTS and scroll_attempts < max_scroll_attempts:
        scroll_attempts += 1
        print(f"Scroll {scroll_attempts}/{max_scroll_attempts}...")
        
        # Mix up scrolling approaches
        if scroll_attempts % 3 == 0:
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            # Use keys for more natural scrolling
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.END)
        
        # Random short pause to seem more human-like
        time.sleep(2 + random.random() * 2)
        
        # Check for "View more comments" buttons again
        for selector in more_comments_buttons:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                if buttons:
                    for button in buttons:
                        try:
                            if button.is_displayed():
                                print(f"Clicking '{button.text}' button")
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(2)
                        except:
                            continue
            except:
                pass
        
        # Count comments after scrolling
        comment_count, _ = count_current_comments()
        
        print(f"Found {comment_count} comments so far")
        
        # If we're not finding more comments after 3 attempts, break
        if comment_count == last_count:
            if scroll_attempts - last_scroll_with_new_comments >= 3:
                print("No new comments found after 3 scroll attempts, stopping")
                break
        else:
            last_count = comment_count
            last_scroll_with_new_comments = scroll_attempts
    
    print(f"Done scrolling. Looking for comments...")
    
    # Find comments using the patterns
    comments = []
    used_pattern = ""
    for pattern in comment_patterns:
        try:
            comments = driver.find_elements(By.XPATH, pattern)
            if comments:
                print(f"Found {len(comments)} comments using pattern: {pattern}")
                used_pattern = pattern
                break
        except Exception as e:
            print(f"Error with pattern {pattern}: {str(e)}")
    
    if not comments:
        print("No comments found using any patterns")
        
        # Take screenshot for debugging
        driver.save_screenshot("facebook_debug.png")
        print("Saved screenshot as facebook_debug.png")
        
        # Print page source for debugging (truncated)
        source = driver.page_source
        print(f"Page source preview (first 500 chars): {source[:500]}...")
    else:
        # Limit to MAX_COMMENTS if we found more
        if len(comments) > MAX_COMMENTS:
            print(f"Limiting to {MAX_COMMENTS} comments")
            comments = comments[:MAX_COMMENTS]
        
        print(f"Writing {len(comments)} comments to {csv_filename}...")
        
        # Open CSV file for writing
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Create CSV writer
            csv_writer = csv.writer(csvfile)
            
            # Write header row
            csv_writer.writerow(['Comment Number', 'Commenter Name', 'Comment Text', 'Timestamp'])
            
            # Process and write each comment
            for index, comment in enumerate(comments):
                try:
                    # Extract complete text
                    comment_text = comment.text.strip()
                    
                    # Try to extract commenter name (typically first line or element with specific class)
                    commenter_name = ""
                    timestamp = ""
                    
                    # Split the text by lines to separate name and comment
                    lines = comment_text.split("\n")
                    if lines:
                        # First line typically contains the name
                        commenter_name = lines[0]
                        
                        # Look for timestamp patterns in the text
                        for line in lines:
                            if any(time_unit in line.lower() for time_unit in ["min", "hr", "hrs", "d", "w", "sec"]):
                                timestamp = line
                                # Remove timestamp from comment text if possible
                                if line in comment_text:
                                    comment_text = comment_text.replace(line, "").strip()
                        
                        # Remove commenter name from comment text
                        if commenter_name in comment_text:
                            comment_text = comment_text.replace(commenter_name, "", 1).strip()
                    
                    # Write to CSV
                    csv_writer.writerow([index + 1, commenter_name, comment_text, timestamp])
                    print(f"Comment {index+1}: {commenter_name} - {comment_text[:40]}..." if len(comment_text) > 40 else comment_text)
                except Exception as e:
                    print(f"Error processing comment {index+1}: {str(e)}")
        
        print(f"Successfully saved {len(comments)} comments to {csv_filename}")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("Closing browser...")
    # Close browser
    driver.quit()
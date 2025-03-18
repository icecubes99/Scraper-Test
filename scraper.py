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

print("Setting up Chrome options...")
# Set up Selenium with headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

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
    
    print("Scrolling to load comments...")
    # Scroll more times to load more comments
    for i in range(5):  # Increased from 3 to 5
        print(f"Scroll {i+1}...")
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(3)
    
    print("Looking for comments...")
    # Try different XPaths to find comments
    comment_patterns = [
        "//div[contains(@aria-label, 'Comment')]",
        "//div[@data-testid='comment']",
        "//div[contains(@class, 'x1y1aw1k xn6708d')]",
        "//div[contains(@class, 'x1n2onr6')]//div[contains(@class, 'x16tdsg8')]",
        "//ul[contains(@class, 'x1n2onr6')]//li"
    ]
    
    comments = []
    used_pattern = ""
    for pattern in comment_patterns:
        comments = driver.find_elements(By.XPATH, pattern)
        if comments:
            print(f"Found {len(comments)} comments using pattern: {pattern}")
            used_pattern = pattern
            break
    
    if not comments:
        print("No comments found using any patterns")
        
        # Take screenshot for debugging
        driver.save_screenshot("facebook_debug.png")
        print("Saved screenshot as facebook_debug.png")
        
        # Print page source for debugging (truncated)
        source = driver.page_source
        print(f"Page source preview (first 500 chars): {source[:500]}...")
    else:
        print(f"Writing {len(comments)} comments to {csv_filename}...")
        
        # Open CSV file for writing
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Create CSV writer
            csv_writer = csv.writer(csvfile)
            
            # Write header row
            csv_writer.writerow(['Comment Number', 'Comment Text', 'Timestamp'])
            
            # Process and write each comment
            for index, comment in enumerate(comments):
                try:
                    # Extract comment text
                    comment_text = comment.text
                    
                    # Try to get timestamp if available
                    timestamp = ""
                    try:
                        # This is a generic approach - might need adjustment based on actual Facebook structure
                        time_elements = comment.find_elements(By.XPATH, ".//a[contains(@class, 'x1i10hfl')]")
                        for elem in time_elements:
                            if "min" in elem.text or "hr" in elem.text or "d" in elem.text:
                                timestamp = elem.text
                                break
                    except:
                        pass
                    
                    # Write to CSV
                    csv_writer.writerow([index + 1, comment_text, timestamp])
                    print(f"Comment {index+1}: {comment_text[:50]}..." if len(comment_text) > 50 else comment_text)
                except Exception as e:
                    print(f"Error processing comment {index+1}: {str(e)}")
        
        print(f"Successfully saved comments to {csv_filename}")
        
        # Attempting to extract more metadata
        print("Attempting to extract commenter names...")
        
        # Try to get commenter names specifically
        try:
            if used_pattern:
                # Adjust XPath to find the commenter names based on the working pattern
                commenter_patterns = [
                    f"{used_pattern}//a[contains(@class, 'x1i10hfl')]",
                    f"{used_pattern}//span[contains(@class, 'x3nfvp2')]"
                ]
                
                for c_pattern in commenter_patterns:
                    names = driver.find_elements(By.XPATH, c_pattern)
                    if names:
                        print(f"Found {len(names)} potential commenter names")
                        break
        except Exception as e:
            print(f"Error extracting commenter names: {str(e)}")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("Closing browser...")
    # Close browser
    driver.quit()
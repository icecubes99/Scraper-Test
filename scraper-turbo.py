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
import os
import json

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
print("Starting Facebook comment scraper with TURBO mode...")

print("Setting up Chrome options...")
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")
chrome_options.add_argument("--disable-javascript-harmony-shipping")
chrome_options.add_argument("--disable-hang-monitor")
chrome_options.add_argument("--disable-ipc-flooding-protection")
chrome_options.add_argument("--window-size=1280,720")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

# Add performance-focused Chrome preferences
chrome_prefs = {
    "profile.default_content_setting_values": {
        "images": 2,
        "plugins": 2,
        "popups": 2,
        "geolocation": 2,
        "notifications": 2,
        "auto_select_certificate": 2,
        "fullscreen": 2,
        "mouselock": 2,
        "mixed_script": 2,
        "media_stream": 2,
        "media_stream_mic": 2,
        "media_stream_camera": 2,
        "protocol_handlers": 2,
        "ppapi_broker": 2,
        "automatic_downloads": 2,
        "midi_sysex": 2,
        "push_messaging": 2,
        "ssl_cert_decisions": 2,
        "metro_switch_to_desktop": 2,
        "protected_media_identifier": 2,
        "app_banner": 2,
        "site_engagement": 2,
        "durable_storage": 2
    },
    "disk-cache-size": 33554432
}
chrome_options.add_experimental_option("prefs", chrome_prefs)

print("Installing ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
timer.checkpoint("Browser initialization")

# Block unnecessary resources using CDP
driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [
    "*.css", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.woff", "*.ttf", "*.ico",
    "*facebook.com/rsrc.php*", "*facebook.com/ajax*", "*facebook.com/api*"
]})
driver.execute_cdp_cmd("Network.enable", {})

# Maximum comments to collect
MAX_COMMENTS = 5000

# Create CSV filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"facebook_comments_{timestamp}.csv"

print("Starting browser and loading the post...")
fb_post_url = "https://web.facebook.com/photo/?fbid=992188076425376&set=a.588916660085855"
driver.get(fb_post_url)
wait = WebDriverWait(driver, 10)
timer.checkpoint("Page load")

try:
    # Try to close any login popups if present
    try:
        close_buttons = driver.find_elements(By.XPATH, "//div[@aria-label='Close']")
        for button in close_buttons:
            if button.is_displayed():
                driver.execute_script("arguments[0].click();", button)
        time.sleep(0.2)
    except Exception as e:
        pass
    timer.checkpoint("Handle popups")
    
    # Turbo scroll: JavaScript function to click "View more" buttons and scroll aggressively
    turbo_scroll_js = """
    return (async function() {
        const scrollDelay = ms => new Promise(resolve => setTimeout(resolve, ms));
        let lastCommentCount = 0;
        let noChangeCount = 0;
        const results = {clicks: 0, scrolls: 0, commentCount: 0};
        
        // Click all "view more" buttons using XPath selectors
        function clickAllButtons() {
            const buttonXPaths = [
                "//span[contains(text(), 'View')]", 
                "//span[contains(text(), 'more comments')]", 
                "//span[contains(text(), 'previous comments')]", 
                "//span[contains(text(), 'reply')]", 
                "//div[@role='button']//span[contains(text(), 'View')]", 
                "//a[@role='button' and starts-with(@href, '#')]"
            ];
            let clickCount = 0;
            buttonXPaths.forEach(xpath => {
                try {
                    const buttons = document.evaluate(
                        xpath,
                        document,
                        null,
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                        null
                    );
                    for (let i = 0; i < buttons.snapshotLength; i++) {
                        const btn = buttons.snapshotItem(i);
                        if (btn && btn.offsetParent !== null) {
                            btn.click();
                            clickCount++;
                        }
                    }
                } catch (e) {
                    // Skip errors for this selector
                }
            });
            return clickCount;
        }
        
        // Count comments using various selectors
        function countComments() {
            const commentSelectors = [
                "div[aria-label*='Comment']",
                "div[data-testid='comment']",
                "div.x1y1aw1k",
                "div[role='article']",
                "div.x16tdsg8"
            ];
            let maxComments = 0;
            commentSelectors.forEach(selector => {
                try {
                    const elems = document.querySelectorAll(selector);
                    if (elems.length > maxComments) {
                        maxComments = elems.length;
                    }
                } catch (e) {}
            });
            return maxComments;
        }
        
        // Main loop: click buttons and scroll
        for (let i = 0; i < 40; i++) {
            results.clicks += clickAllButtons();
            if (i % 3 === 0) {
                window.scrollTo(0, document.body.scrollHeight);
            } else {
                window.scrollBy(0, 800);
            }
            results.scrolls++;
            await scrollDelay(600);  // Slightly longer delay for content to load
            const currentCount = countComments();
            if (currentCount > lastCommentCount) {
                lastCommentCount = currentCount;
                noChangeCount = 0;
            } else {
                noChangeCount++;
            }
            if (noChangeCount >= 4) {
                break;
            }
        }
        results.commentCount = countComments();
        return results;
    })();
    """
    
    print("Starting turbo scrolling...")
    scroll_start_time = time.time()
    turbo_results = driver.execute_script(turbo_scroll_js)
    print(f"Turbo scrolling results: {turbo_results}")
    print(f"Clicked {turbo_results['clicks']} buttons, performed {turbo_results['scrolls']} scrolls")
    print(f"Found {turbo_results['commentCount']} comments")
    scroll_time = time.time() - scroll_start_time
    print(f"Turbo scrolling completed in {scroll_time:.2f} seconds")
    timer.checkpoint("Turbo scrolling")
    
    # Extra wait to ensure all comments are loaded
    time.sleep(1)
    
    # Extract comments using a refined JS function
    comments_extraction_js = """
    function getAllComments() {
        const commentSelectors = [
            "div[aria-label*='Comment']", 
            "div[data-testid='comment']",
            "div.x1y1aw1k", 
            "div[role='article']",
            "div.x16tdsg8",
            "ul[role='list'] li",
            "div.x78zum5"
        ];
        let bestElements = [];
        let bestSelector = "";
        commentSelectors.forEach(selector => {
            try {
                const elems = document.querySelectorAll(selector);
                if (elems.length > bestElements.length) {
                    bestElements = Array.from(elems);
                    bestSelector = selector;
                }
            } catch(e) {}
        });
        if (bestElements.length === 0) {
            try {
                const xpath = "//div[contains(@class, 'comment') or contains(@class, 'x1y1aw1k')]";
                const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                let xpathElements = [];
                for (let i = 0; i < result.snapshotLength; i++) {
                    xpathElements.push(result.snapshotItem(i));
                }
                if (xpathElements.length > bestElements.length) {
                    bestElements = xpathElements;
                    bestSelector = "xpath-fallback";
                }
            } catch(e) {}
        }
        console.log("Using selector: " + bestSelector + " with " + bestElements.length + " elements");
        // Use innerText so that only visible text is returned
        return bestElements.map(el => {
            try {
                return el.innerText || "";
            } catch(e) {
                return "";
            }
        }).filter(text => text.trim().length > 0);
    }
    return getAllComments();
    """
    
    print("Extracting comments...")
    extraction_start = time.time()
    raw_texts = driver.execute_script(comments_extraction_js)
    print(f"Extracted {len(raw_texts)} raw comments via JavaScript")
    if raw_texts and len(raw_texts) > 0:
        print("Debug - First raw comment text:")
        print(repr(raw_texts[0])[:200] + "...")
    
    # Process each raw comment using a refined function
    def process_comment(raw_text):
        if not raw_text or not raw_text.strip():
            return None
        lines = raw_text.split('\n')
        if len(lines) == 0:
            return None
        # Remove a potential username line if it's very short
        if len(lines) > 1 and len(lines[0]) < 40:
            lines = lines[1:]
        badge_indicators = ["top fan", "valued commenter", "admin", "moderator", "new member", "founder"]
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\d+[dhmswy]$', line):
                continue
            if re.match(r'^\d+$', line):
                continue
            if any(badge in line.lower() for badge in badge_indicators):
                continue
            if line.lower() in ['reply', 'like', 'share', 'edit', 'delete']:
                continue
            filtered_lines.append(line)
        comment_text = " ".join(filtered_lines)
        comment_text = re.sub(r'\s+\d+[dhmswy](\s+\d+)?$', '', comment_text)
        comment_text = re.sub(r'\b\d{1,2}[ymwdhs]\b', '', comment_text)
        comment_text = re.sub(r'\s+', ' ', comment_text).strip()
        return comment_text if comment_text and len(comment_text) > 5 else None
    
    # Process comments in parallel
    processing_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        processed_comments = list(executor.map(process_comment, raw_texts))
    processed_comments = [c for c in processed_comments if c]
    processing_time = time.time() - processing_start
    print(f"Comment processing took {processing_time:.2f} seconds")
    extraction_time = time.time() - extraction_start
    print(f"Comment extraction took {extraction_time:.2f} seconds")
    print(f"Extracted {len(processed_comments)} valid comments")
    timer.checkpoint("Comments extraction")
    
    # Limit comments if necessary
    if MAX_COMMENTS and len(processed_comments) > MAX_COMMENTS:
        print(f"Limiting output to {MAX_COMMENTS} comments (out of {len(processed_comments)} found)")
        processed_comments = processed_comments[:MAX_COMMENTS]
    
    print(f"Writing {len(processed_comments)} comments to {csv_filename}")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Comment Number", "Comment Text"])
        chunk_size = 500
        comment_chunks = [processed_comments[i:i + chunk_size] for i in range(0, len(processed_comments), chunk_size)]
        comment_number = 1
        for chunk in comment_chunks:
            rows = [(comment_number + i, text) for i, text in enumerate(chunk)]
            writer.writerows(rows)
            comment_number += len(chunk)
    timer.checkpoint("CSV writing")
    
    print(f"Successfully saved {len(processed_comments)} comments to {csv_filename}")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    print("Closing browser...")
    driver.quit()
    timer.checkpoint("Browser cleanup")
    timer.summary()

# Facebook Comment Scraper

A high-performance toolkit for extracting comments from Facebook posts using Selenium and JavaScript automation.

## 📋 Overview

This project provides multiple scripts for scraping comments from Facebook posts, each optimized for different scenarios:

- **scraper.py** - Standard version with balanced performance and reliability.
- **scraper-fast.py** - Performance-optimized version with timing metrics.
- **scraper-turbo.py** - Maximum-speed version using JavaScript injection.
- **scraper-replies.py** - Specialized version for capturing comment threads.

## 🚀 Features

- **Speed-optimized collection**: Get comments 5-10x faster than manual browsing.
- **Performance metrics**: Built-in timer to measure execution speed of each phase.
- **JavaScript automation**: Uses browser's native JavaScript for faster DOM traversal.
- **Parallel processing**: Multi-threaded comment extraction and processing.
- **Resource optimization**: Blocks unnecessary resources for faster page loads.
- **Robust error handling**: Deals with Facebook's dynamic layout changes.
- **CSV export**: Automatically saves comments with timestamps.

## 🛠️ Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/icecubes99/Scraper-Test.git
   cd Scraper-Test
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Make sure you have the Chrome browser installed.

## 📊 Usage

### Standard Scraper

Best for general-purpose comment extraction with good reliability.

### Fast Scraper (with performance metrics)

Optimized for speed with built-in performance tracking.

### Turbo Scraper (JavaScript-accelerated)

Uses JavaScript injection for maximum speed when extracting large numbers of comments.

### Replies Scraper

Specialized for extracting both comments and their replies.

## ⚙️ Configuration

Modify these variables in each script to customize behavior:

- **Post URL**: Update the `fb_post_url` variable with the target Facebook post URL.
- **Maximum Comments**: Adjust the `MAX_COMMENTS` variable to set the limit for comment extraction.

## 🧩 How It Works

1. **Initialization**: Sets up a Chrome browser with optimized settings.
2. **Navigation**: Opens the target Facebook post.
3. **Interaction**: Clicks "View more comments" buttons and scrolls to load content.
4. **Extraction**: Collects comments using various selector patterns.
5. **Processing**: Cleans and processes raw comment text.
6. **Export**: Saves processed comments to a timestamped CSV file.

## ⏱️ Performance Comparison

| Script Version | Comments Per Minute | Memory Usage | CPU Usage |
| -------------- | ------------------- | ------------ | --------- |
| Standard       | ~100-200            | Medium       | Medium    |
| Fast           | ~300-500            | Low          | Medium    |
| Turbo          | ~500-1000+          | Low          | High      |
| Replies        | ~50-100             | Medium       | Low       |

## 📈 Output Example

The scrapers generate CSV files with this format:

| Comment Number | Comment Text                               |
| -------------- | ------------------------------------------ |
| 1              | This is a sample comment.                  |
| 2              | Another example comment with more details. |

## 🔧 Troubleshooting

### Common Issues

- **No comments found**:

  - Try running without headless mode (remove the `--headless` option).
  - Check if the post URL is correct and publicly accessible.
  - Facebook may have changed their HTML structure; update the selectors.

- **Slow performance**:

  - Adjust the scroll delay values in the script.
  - Ensure your internet connection is stable.
  - Try using `scraper-turbo.py` for better performance.

- **Script crashes**:

  - Update ChromeDriver and Selenium to the latest versions.
  - Check for changes in Facebook's HTML structure.
  - Look for specific error messages in the output.

- **Empty comments**:
  - Check the comment processing function filters.
  - Make sure the post has public comments.

### Selector Maintenance

Facebook frequently changes its DOM structure. If the scraper stops working, you may need to update these patterns:

- Use browser developer tools to inspect the current structure and update accordingly.

## 📝 Requirements

See `requirements.txt` for a complete list of dependencies.

### Core Requirements:

- Python 3.8+
- Selenium 4.10.0+
- Chrome browser
- `webdriver-manager` 3.9.0+

## 🧪 Advanced Usage

### Batch Processing

To scrape multiple posts, create a file with URLs and use a loop to process each URL.

### Headful Mode

To see the browser in action (helpful for debugging), remove the `--headless` option in the Chrome options.

### Custom Output Format

To export to formats other than CSV, modify the export logic in the script.

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with Facebook's Terms of Service. The developers are not responsible for any misuse or violations of Facebook's policies. Web scraping may violate Facebook's Terms of Service. Use at your own risk.

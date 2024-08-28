# Web Crawler Script

## Overview

This Python-based web crawler is designed to recursively navigate through web pages, capturing images, HTML content, and table data from a user-provided domain. It allows users to specify the depth of crawling and filter the types of files to be extracted. The script logs all activities, including visited URLs, the crawling process, and timestamps, into a CSV file for easy tracking and analysis.

This script is suitable for basic web scraping tasks and data collection from websites.

## Features

- **Recursive Crawling:** Navigate through the domain and its subdomains up to a specified depth.
- **Image Capture:** Extract images from web pages, with options to filter by file extension.
- **Full HTML Capture:** Save the full HTML content of visited pages.
- **Table Data Extraction:** Capture table data from web pages.
- **JavaScript Handling:** Basic handling of JavaScript to ensure better capture of dynamic content.
- **Logging:** Detailed logs of the crawling process, including visited URLs and captured data.
- **File Renaming:** Rename downloaded files according to a customizable pattern.
- **CSV Logging:** Logs the URL paths and timestamps of captured images into a CSV file.
- **User-Friendly Interface:** Simple input widgets for configuration (currently being improved).
- **User Agents and Delays:** The script includes random User-Agent header rotation to mimic different browsers and platforms. It also implements delays between requests to avoid overloading the server and to simulate "natural browsing behavior". 

## Prerequisites

Before running the script, ensure you have the following dependencies installed:

### Python Packages

- **requests**: For making HTTP requests to web pages.
- **beautifulsoup4**: For parsing HTML content.
- **selenium**: For interacting with web pages, especially those with JavaScript.
- **pandas**: For handling and logging data in CSV format.
- **streamlit**: (Optional) For creating a simple GUI to interact with the script.
- **tqdm**: For displaying progress bars during crawling.
- **lxml**: For fast HTML and XML parsing.

To install the required Python packages, run the following command:

```bash
pip install requests beautifulsoup4 selenium pandas streamlit tqdm lxml
```

## System Requirements

 - Google Chrome: The script relies on the Chrome browser for rendering JavaScript-heavy content.

### Automatic ChromeDriver Installation

The script automatically downloads and installs the correct version of ChromeDriver based on your installed version of Google Chrome. Ensure you have an active internet connection when running the script for the first time.

## Getting Started

### Initial Setup
1. Clone the Repository
 - Clone this repository to your local machine:

```bash
git clone https://github.com/Jnich145/SeleniumCrawl.git
cd SeleniumCrawl
```
2. Install Dependencies
 - If you haven't installed the required Python packages above, you may also do so by running the following command:

```bash
pip install -r requirements.txt
```

## Running the Script
Here’s a step-by-step guide to using the script for the first time:

### Example: Crawling https://books.toscrape.com/
1. Open Terminal
Navigate to the directory where the script is located.

2. Run the Script
Execute the script using Python:

```bash
python web_crawler.py
```

3. Automatic ChromeDriver Installation
The script will automatically download and install the correct version of ChromeDriver if it is not already installed. Ensure you have an active internet connection for this step.

4. Input Parameters
The script will prompt you to enter the following parameters:

 - Starting URL: Provide the URL from which to start crawling.
Example: https://books.toscrape.com/
 - Crawl Depth: Enter the maximum depth for recursive crawling.
Example: 2 (This will crawl the main page and one level of links beyond it).
 - File Types to Capture: Specify which types of files to capture (e.g., images, HTML).
Example: images or html
 - File Extensions: If capturing images, specify the extensions to filter by (e.g., jpg, png).
 - Output Directory: Provide the path to the directory where captured files will be stored.
Example: ./output

5. Review Logs
As the script runs, it will log its progress in the terminal. You can monitor which URLs are being visited and what data is being captured.

6. View Captured Data
Once the crawl is complete, navigate to the specified output directory to review the captured images, HTML files, and log CSV.

7. Analyze Logs
The log CSV file will contain detailed information about the crawling process, including timestamps and URLs. You can analyze this file to gain insights into the data collection process.

## Customization
 - Adjusting Crawl Depth: You can modify the depth of crawling to either broaden or narrow the scope of data collection.
 - JavaScript Handling: The script currently has basic handling for JavaScript. A more robust solution is being developed for better interaction with dynamic content.
 - User Interface: A simple GUI is in development to make the script more user-friendly. 

## Troubleshooting
 - ChromeDriver Issues: If ChromeDriver installation fails, ensure your internet connection is active and try running the script again. The script should automatically detect the correct version of ChromeDriver based on your installed Chrome browser. If the problem persists, manually install ChromeDriver and add it to your system’s PATH.
## Future Enhancements
 - Advanced JavaScript Handling: Improving JavaScript support for better interaction with dynamic web content.
 - Enhanced GUI: Developing a more robust and user-friendly graphical interface.
 - Error Handling: Implementing more comprehensive error handling and logging mechanisms.

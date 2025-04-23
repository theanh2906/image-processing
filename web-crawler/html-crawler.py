import datetime
import logging
from tkinter import filedialog
from typing import List, Optional

import customtkinter as ctk  # Add customtkinter import
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HTMLCrawler:
    def __init__(self, timeout: int = 10, user_agent: str = None):
        """
        Initialize the HTML crawler
        
        Args:
            timeout (int): Request timeout in seconds
            user_agent (str): Custom user agent string
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_html_from_url(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL
        
        Args:
            url (str): URL to fetch
            
        Returns:
            Optional[str]: HTML content or None if failed
        """
        try:
            logger.info(f"Fetching HTML from URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None

    def get_html_from_file(self, file_path: str) -> Optional[str]:
        """
        Read HTML content from a local file
        
        Args:
            file_path (str): Path to the HTML file
            
        Returns:
            Optional[str]: HTML content or None if failed
        """
        try:
            logger.info(f"Reading HTML from file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None

    def extract_text_by_selector(self, html: str, selector: str) -> List[str]:
        """
        Extract text from HTML using CSS selector
        
        Args:
            html (str): HTML content
            selector (str): CSS selector
            
        Returns:
            List[str]: List of extracted text strings
        """
        try:
            logger.info(f"Extracting text using selector: {selector} (e.g., '.panel-header > a')")
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(selector) if selector else soup.select(
                '*')  # BeautifulSoup already supports jQuery-like selectors

            if not elements:
                logger.warning(f"No elements found with selector: {selector}")
                return []

            return [element.get_text(strip=True) for element in elements]
        except Exception as e:
            logger.error(f"Error extracting text with selector {selector}: {str(e)}")
            return []

    def save_to_file(self, content: List[str], output_file: str) -> bool:
        """
        Save extracted content to a file
        
        Args:
            content (List[str]): Content to save
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Saving content to file: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as file:
                for item in content:
                    file.write(f"{item}\n")
            return True
        except IOError as e:
            logger.error(f"Error saving to file {output_file}: {str(e)}")
            return False

    def crawl(self, source: str, selector: str, is_url: bool = True, output_file: Optional[str] = None) -> List[str]:
        """
        Main crawling function
        
        Args:
            source (str): URL or file path
            selector (str): CSS selector
            is_url (bool): True if source is URL, False if local file
            output_file (Optional[str]): Path to save results
            
        Returns:
            List[str]: Extracted text
        """
        # Get HTML content
        html = self.get_html_from_url(source) if is_url else self.get_html_from_file(source)
        if not html:
            return []

        # Extract text using selector  
        results = self.extract_text_by_selector(html, selector)

        # Save to file if specified
        if output_file and results:
            self.save_to_file(results, output_file)

        return results


class HTMLCrawlerGUI:
    def __init__(self):
        # Set up customtkinter appearance
        ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Create the main window with customtkinter
        self.window = ctk.CTk()
        self.window.title("HTML Crawler")
        self.window.geometry("1024x768")
        
        # Create crawler instance
        self.crawler = HTMLCrawler()

        # Create main frame
        self.main_frame = ctk.CTkFrame(self.window, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create input fields
        self.create_input_fields()

        # Create buttons
        self.create_buttons()

        # Create result area
        self.create_result_area()

        self.window.mainloop()

    def create_input_fields(self):
        # Input frame
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # Title for input section
        ctk.CTkLabel(input_frame, text="Input Parameters", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 10))

        # Create two columns
        left_column = ctk.CTkFrame(input_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_column = ctk.CTkFrame(input_frame)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Left Column - URL and File inputs
        # URL input
        ctk.CTkLabel(left_column, text="URL:").pack(anchor="w", padx=10, pady=(10, 0))
        self.url_entry = ctk.CTkEntry(left_column, height=30, placeholder_text="Enter URL to crawl")
        self.url_entry.pack(fill="x", padx=10, pady=(0, 10))

        # File input with browse button
        ctk.CTkLabel(left_column, text="HTML File:").pack(anchor="w", padx=10, pady=(5, 0))
        file_frame = ctk.CTkFrame(left_column)
        file_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.file_entry = ctk.CTkEntry(file_frame, height=30, placeholder_text="Select local HTML file")
        self.file_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            file_frame, 
            text="Browse", 
            command=self.browse_file, 
            width=100, 
            height=30,
            fg_color="#3a7ebf"
        ).pack(side="right", padx=5)

        # Right Column - Other inputs
        # Selector input
        ctk.CTkLabel(right_column, text="CSS Selector:").pack(anchor="w", padx=10, pady=(10, 0))
        self.selector_entry = ctk.CTkEntry(right_column, height=30, placeholder_text="e.g., .article h2, div.content p")
        self.selector_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Output file input
        ctk.CTkLabel(right_column, text="Output File:").pack(anchor="w", padx=10, pady=(5, 0))
        self.output_entry = ctk.CTkEntry(right_column, height=30, placeholder_text="Path to save results (optional)")
        self.output_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Timeout input
        ctk.CTkLabel(right_column, text="Timeout (sec):").pack(anchor="w", padx=10, pady=(5, 0))
        self.timeout_entry = ctk.CTkEntry(right_column, height=30)
        self.timeout_entry.insert(0, "10")
        self.timeout_entry.pack(fill="x", padx=10, pady=(0, 10))

    def create_buttons(self):
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(pady=15)

        # Create buttons with customtkinter styling
        ctk.CTkButton(
            button_frame, 
            text="Crawl", 
            command=self.crawl, 
            width=150, 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2d7d46",
            hover_color="#266f3c"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Export Results", 
            command=self.export_results, 
            width=150, 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame, 
            text="Clear", 
            command=self.clear_all, 
            width=150, 
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#d1335b",
            hover_color="#b32a4e"
        ).pack(side="left", padx=10)

    def create_result_area(self):
        # Results section label
        ctk.CTkLabel(
            self.main_frame, 
            text="Results", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), anchor="w", padx=10)
        
        # Results container
        result_frame = ctk.CTkFrame(self.main_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Replace ScrolledText with CTkTextbox
        self.result_area = ctk.CTkTextbox(
            result_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        self.result_area.pack(fill="both", expand=True, padx=10, pady=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select HTML File",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)

    def clear_all(self):
        self.url_entry.delete(0, "end")
        self.file_entry.delete(0, "end")
        self.selector_entry.delete(0, "end")
        self.output_entry.delete(0, "end")
        self.result_area.delete("0.0", "end")
        self.timeout_entry.delete(0, "end")
        self.timeout_entry.insert(0, "10")

    def crawl(self):
        # Clear previous results
        self.result_area.delete("0.0", "end")

        url = self.url_entry.get()
        file = self.file_entry.get()
        selector = self.selector_entry.get()
        output = self.output_entry.get()

        try:
            timeout = int(self.timeout_entry.get())
        except ValueError:
            self.result_area.insert("end", "Error: Timeout must be a number\n")
            return

        # Validate inputs
        if not selector:
            self.result_area.insert("end", "Error: CSS selector is required\n")
            return

        if not url and not file:
            self.result_area.insert("end", "Error: Either URL or file path must be specified\n")
            return

        if url and file:
            self.result_area.insert("end", "Error: Only one of URL or file should be specified\n")
            return

        # Set crawler timeout
        self.crawler.timeout = timeout

        # Perform crawl
        is_url = bool(url)
        source = url if is_url else file
        results = self.crawler.crawl(source, selector, is_url, output)

        # Display results
        if results:
            for result in results:
                self.result_area.insert("end", f"{result}\n")
        else:
            self.result_area.insert("end", "No results found\n")

    def export_results(self):
        results = self.result_area.get("0.0", "end").splitlines()
        if not results or not results[0]:
            return

        output_file = self.output_entry.get()
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{timestamp}-output.txt"

        if self.crawler.save_to_file(results, output_file):
            self.result_area.insert("end", f"\nResults exported to {output_file}\n")
        else:
            self.result_area.insert("end", f"\nError exporting results\n")


def main():
    HTMLCrawlerGUI()


if __name__ == "__main__":
    main()


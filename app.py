import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urlparse
import validators

# Set page configuration
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕷️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("🕷️ AI Web Scraper")
st.markdown("Extract data from any website with ease!")

# URL input taking full width
url = st.text_input("Enter Website URL:", placeholder="https://example.com")

# Description box below URL, taking full width
user_description = st.text_area(
    "Describe what to extract:",
    placeholder="Example: 'product prices', 'article titles', 'email addresses'",
    height=100  # Specify height for better visibility
)

# Sidebar configuration
st.sidebar.header("Scraping Configuration")

# Scraping options
scraping_option = st.sidebar.selectbox(
    "Select what to scrape:",
    ["Text Content", "Links", "Images", "Custom Elements", "Smart Extract"]
)

# Custom element input if selected
if scraping_option == "Custom Elements":
    custom_tag = st.sidebar.text_input("Enter HTML tag or class:", placeholder="div.class-name or #id")

def is_valid_url(url):
    return validators.url(url)

# Modified scrape_website function to include smart extraction
def scrape_website(url, option, custom_tag=None, description=None):
    try:
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Setup headers with error handling
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)  # Add timeout
            response.raise_for_status()  # Raise error for bad status codes
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. The website took too long to respond.")
        except requests.exceptions.SSLError:
            raise Exception("SSL Certificate verification failed. The website might not be secure.")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to the website. Please check your internet connection.")
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 403:
                raise Exception("Access forbidden. The website might be blocking web scrapers.")
            elif response.status_code == 404:
                raise Exception("Page not found. Please check if the URL is correct.")
            else:
                raise Exception(f"HTTP error occurred: {http_err}")
        
        # Parse HTML with error handling
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as parse_err:
            raise Exception(f"Failed to parse HTML content: {parse_err}")
        
        # Smart Extract error handling
        if option == "Smart Extract":
            if not description:
                raise ValueError("Description is required for Smart Extract")
            
            extracted_data = []
            desc_lower = description.lower()
            
            try:
                # Price extraction with validation
                if 'price' in desc_lower or '$' in desc_lower:
                    price_patterns = soup.find_all(
                        ['span', 'div', 'p'], 
                        text=lambda text: text and ('$' in text or '€' in text or '£' in text)
                    )
                    if not price_patterns:
                        st.warning("No price information found on the page")
                    extracted_data.extend([{'Type': 'Price', 'Content': p.text.strip()} for p in price_patterns])
                
                # Email extraction with validation
                if 'email' in desc_lower:
                    email_patterns = soup.find_all(['a'], href=lambda href: href and 'mailto:' in href)
                    if not email_patterns:
                        st.warning("No email addresses found on the page")
                    extracted_data.extend([{'Type': 'Email', 'Content': e['href'].replace('mailto:', '')} for e in email_patterns])
                
                # Return results with validation
                if not extracted_data:
                    st.warning("No matching data found for your description")
                return pd.DataFrame(extracted_data)
                
            except Exception as extract_err:
                raise Exception(f"Error during smart extraction: {extract_err}")
        
        # Custom Elements error handling
        elif option == "Custom Elements":
            if not custom_tag:
                raise ValueError("Custom tag is required for Custom Elements option")
            try:
                elements = []
                for element in soup.select(custom_tag):
                    elements.append({
                        'Content': element.text.strip(),
                        'HTML': str(element)
                    })
                if not elements:
                    st.warning(f"No elements found matching selector: {custom_tag}")
                return pd.DataFrame(elements)
            except Exception as selector_err:
                raise Exception(f"Invalid CSS selector: {selector_err}")
        
        # ... (rest of the scraping options)
            
    except Exception as e:
        st.error(f"🚨 Error: {str(e)}")
        # Log error for debugging (you can add proper logging here)
        print(f"Debug - Error details: {type(e).__name__}: {str(e)}")
        return None

# Enhanced error handling in the main execution
if st.button("Start Scraping"):
    try:
        # Input validation
        if not url:
            st.warning("⚠️ Please enter a URL")
            st.stop()
        elif not is_valid_url(url):
            st.error("❌ Invalid URL format. Please enter a valid URL (e.g., https://example.com)")
            st.stop()
        
        with st.spinner("🔄 Scraping in progress..."):
            # Progress bar with error handling
            try:
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
            except Exception as progress_err:
                st.warning("Progress bar error, but scraping continues...")
            
            # Validation for specific options
            if scraping_option == "Custom Elements" and not custom_tag:
                st.warning("⚠️ Please enter a custom element selector")
                st.stop()
            elif scraping_option == "Smart Extract" and not user_description:
                st.warning("⚠️ Please describe what you want to extract")
                st.stop()
            
            # Execute scraping with error handling
            results = scrape_website(
                url, 
                scraping_option, 
                custom_tag if scraping_option == "Custom Elements" else None,
                user_description if scraping_option == "Smart Extract" else None
            )
            
            # Handle results
            if results is not None and not results.empty:
                st.success("✅ Scraping completed successfully!")
                
                # Display and download results with error handling
                try:
                    st.subheader("Scraped Data")
                    st.dataframe(results)
                    
                    csv = results.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="scraped_data.csv",
                        mime="text/csv"
                    )
                except Exception as display_err:
                    st.error(f"Error displaying results: {display_err}")
            else:
                st.warning("⚠️ No data found for the given criteria")
                
    except Exception as main_err:
        st.error(f"🚨 An unexpected error occurred: {str(main_err)}")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Created by Nageswar kumar chodisetti | © 2024</div>", unsafe_allow_html=True)
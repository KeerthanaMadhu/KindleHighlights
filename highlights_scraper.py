import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

# Save cookies after manual login (Run this once)
def save_cookies():
    driver = webdriver.Chrome()
    driver.get("https://read.amazon.com/notebook")
    input("Log in manually, then press Enter...")
    time.sleep(10)
    pickle.dump(driver.get_cookies(), open("amazon_cookies2.pkl", "wb"))
    driver.quit()

# Load session with cookies
def load_session():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # Maximize the browser window for better visibility
    driver = webdriver.Chrome(options=options)
    driver.get("https://read.amazon.com/notebook")
    
    # Load cookies into the session
    cookies = pickle.load(open("amazon_cookies2.pkl", "rb"))
    current_domain = driver.current_url.split("//")[-1].split("/")[0]
    
    for cookie in cookies:
        if 'domain' in cookie:
            cookie['domain'] = current_domain  # Match the domain dynamically
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Could not add cookie: {e}")
    
    driver.refresh()  # Refresh the page to apply cookies
    return driver

# Helper function to wait for elements
def wait_and_find_element(driver, by, value, timeout=30):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except TimeoutException as e:
        print(f"Timeout while waiting for element: {value}")
        raise e

# Main function to extract highlights
def extract_all_highlights():
    driver = load_session()
    all_highlights = {}

    try:
        # Wait for the book list to load
        print("[INFO] Waiting for the book list to load...")
        book_list = wait_and_find_element(driver, By.ID, "kp-notebook-library")
        
        # Find all book elements
        books = book_list.find_elements(By.CLASS_NAME, "kp-notebook-library-each-book")
        total_books = len(books)
        print(books)
        print(f"[INFO] Found {total_books} books. Starting extraction...")

        for index in range(total_books):
            try:
                print(f"[INFO] Processing book {index + 1} of {total_books}")
                
                # Re-locate books after each interaction (to avoid stale element issues)
                books = book_list.find_elements(By.CLASS_NAME, "kp-notebook-library-each-book")
                book = books[index]
                
                # Scroll the book into view and click it
                driver.execute_script("arguments[0].scrollIntoView(true);", book)
                time.sleep(2)  # Allow time for scrolling to complete
                ActionChains(driver).move_to_element(book).click().perform()
                time.sleep(5)  # Wait for highlights to load
                
                # Debugging point: Check if the page has loaded correctly
                print("[DEBUG] Checking if book details page is loaded...")
                
                # Extract book title (check if title element exists)
                try:
                    book_title_element = wait_and_find_element(driver, By.XPATH, "//h3[contains(@class, 'kp-notebook-metadata')]")
                    book_title = book_title_element.text.strip()
                    book_title = book_title.replace("&amp;#39;", "'")
                    print(f"[INFO] Book title: {book_title}")
                except TimeoutException:
                    print("[ERROR] Could not find the book title. Skipping this book.")
                    continue
                
                # Extract highlights (check if highlight elements exist)
                try:
                    highlights_elements = driver.find_elements(By.CLASS_NAME, "kp-notebook-highlight")
                    book_highlights = [highlight.text.strip() for highlight in highlights_elements]
                    print(book_highlights)
                    print(f"[INFO] Extracted {len(book_highlights)} highlights from '{book_title}'")
                except Exception as e:
                    print(f"[ERROR] Could not extract highlights: {e}")
                    continue
                
                all_highlights[book_title] = book_highlights
                
            except StaleElementReferenceException as e:
                print(f"[ERROR] Stale element reference encountered while processing book {index + 1}: {e}")
                continue
            
            except Exception as e:
                print(f"[ERROR] Unexpected error while processing book {index + 1}: {e}")
                continue
        
        # Print all highlights after processing all books
        print("\n[INFO] Extraction complete. Printing all highlights...\n")
        for book_title, highlights in all_highlights.items():
            print(f"Highlights from '{book_title}':\n" + "=" * 30)
            for i, highlight in enumerate(highlights, start=1):
                print(f"{i}. {highlight}\n")
    
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
    
    finally:
        driver.quit()

# Usage
# Uncomment this line if you need to save cookies again
# save_cookies()

# Extract highlights from all books
extract_all_highlights()

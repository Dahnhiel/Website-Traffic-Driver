import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import random
import logging
from concurrent.futures import ThreadPoolExecutor
            
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='traffic_generator.log'
)

class TrafficGenerator:
    def __init__(self, target_url):
        self.target_url = target_url
        self.referrers = [
            "https://www.google.com/search?q=related+to+your+site",
            "https://www.facebook.com/",
            "https://twitter.com/",
            "https://www.linkedin.com/",
            "https://www.reddit.com/",
            "https://www.instagram.com/",
            "https://www.pinterest.com/",
            None  # Direct traffic
        ]
        self.ua = UserAgent()
        self.stop_event = threading.Event()  # Event to signal stop

    def get_random_user_agent(self):
        return self.ua.random

    def simulate_session(self):
        if self.stop_event.is_set():  # Check if stop event is set
            return False

        options = Options()
        options.headless = True  # Run in headless mode
        options.add_argument("--disable-blink-features=AutomationControlled")
        user_agent = self.get_random_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        
        driver = webdriver.Chrome(options=options)
        try:
            referrer = random.choice(self.referrers)
            if referrer:
                driver.execute_script(f"window.open('{referrer}', '_self');")
                time.sleep(random.uniform(2, 5))
                driver.get(self.target_url)
            else:
                driver.get(self.target_url)
            
            time.sleep(random.uniform(3, 7))  # Let the page load
            
            # Simulate scrolling
            for _ in range(random.randint(1, 3)):
                scroll_distance = random.randint(200, 1000)
                driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(random.uniform(1, 3))
            
            logging.info(f"Visited: {self.target_url} | UA: {user_agent[:30]}...")
            return True
        except Exception as e:
            logging.error(f"Session error: {str(e)}")
            return False
        finally:
            driver.quit()

    def generate_traffic(self, num_sessions=100, max_concurrent=5):
        logging.info(f"Starting traffic generation: {num_sessions} sessions to {self.target_url}")
        successful = 0
        failed = 0
        
        # Using ThreadPoolExecutor to run simulate_session concurrently
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            results = list(executor.map(lambda _: self.simulate_session(), range(num_sessions)))

        # Count the successful and failed sessions
        successful = results.count(True)
        failed = results.count(False)

        logging.info(f"Traffic generation complete. Successful: {successful}, Failed: {failed}")
        return successful, failed

    def stop(self):
        self.stop_event.set()  # Trigger the stop event


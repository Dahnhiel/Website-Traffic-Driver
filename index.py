import threading
import time
import random
import logging
import json
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
import psutil
import hashlib
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traffic_generator.log'),
        logging.StreamHandler()
    ]
)

class StealthTrafficGenerator:
    def __init__(self, target_url, callback=None):
        self.target_url = target_url
        self.callback = callback  # Callback for GUI updates
        self.session_id = hashlib.md5(f"{target_url}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Enhanced referrers with more realistic sources
        self.referrers = [
            "https://www.google.com/search?q={}".format(self._generate_search_query()),
            "https://www.bing.com/search?q={}".format(self._generate_search_query()),
            "https://duckduckgo.com/?q={}".format(self._generate_search_query()),
            "https://www.facebook.com/",
            "https://twitter.com/",
            "https://www.linkedin.com/feed/",
            "https://www.reddit.com/r/popular/",
            "https://www.instagram.com/",
            "https://www.pinterest.com/",
            "https://news.ycombinator.com/",
            "https://medium.com/",
            "https://www.youtube.com/",
            None  # Direct traffic
        ]
        
        # Realistic viewport sizes
        self.viewport_sizes = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
            (1280, 720), (1600, 900), (1024, 768), (1280, 1024),
            (375, 667), (414, 896), (360, 640)  # Mobile sizes
        ]
        
        # Browser profiles for stealth
        self.browser_profiles = [
            {"name": "Windows_Chrome", "os": "Windows NT 10.0; Win64; x64", "webgl": "NVIDIA Corporation"},
            {"name": "Mac_Chrome", "os": "Macintosh; Intel Mac OS X 10_15_7", "webgl": "Intel Inc."},
            {"name": "Linux_Chrome", "os": "X11; Linux x86_64", "webgl": "Mesa DRI Intel(R)"},
            {"name": "Windows_Edge", "os": "Windows NT 10.0; Win64; x64", "webgl": "ANGLE"}
        ]
        
        self.ua = UserAgent()
        self.stop_event = threading.Event()
        self.stats = {
            'total_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'total_page_views': 0,
            'total_time_spent': 0,
            'avg_session_duration': 0,
            'start_time': None,
            'end_time': None,
            'sessions_per_minute': 0,
            'bounce_rate': 0,
            'unique_pages_visited': set(),
            'countries_simulated': set(),
            'browsers_used': set(),
            'errors': []
        }
        
        # Country codes for IP geolocation simulation
        self.countries = ['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP', 'BR', 'IN', 'ES', 'IT', 'NL', 'SE', 'NO']
        
    def _generate_search_query(self):
        """Generate realistic search queries related to the target site"""
        domain = self.target_url.split('//')[1].split('/')[0]
        queries = [
            f"site:{domain}",
            f"{domain.split('.')[0]} review",
            f"{domain.split('.')[0]} features",
            f"visit {domain}",
            f"{domain.split('.')[0]} comparison",
            f"best {domain.split('.')[0]}",
            f"{domain.split('.')[0]} tutorial"
        ]
        return random.choice(queries)
    
    def _get_stealth_chrome_options(self):
        """Enhanced Chrome options for maximum stealth"""
        options = Options()
        profile = random.choice(self.browser_profiles)
        viewport = random.choice(self.viewport_sizes)
        
        # Basic stealth options
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Advanced stealth options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")
        
        # Randomize window size
        options.add_argument(f"--window-size={viewport[0]},{viewport[1]}")
        
        # Randomize user agent
        user_agent = self.ua.random
        options.add_argument(f"--user-agent={user_agent}")
        
        # Memory and performance optimization
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        # Additional fingerprint obfuscation
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        return options, profile, user_agent, viewport
    
    def _setup_driver_stealth(self, driver, profile):
        """Apply additional stealth measures to the driver"""
        # Override webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override automation indicators
        driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override languages
        languages = ['en-US', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh']
        selected_langs = random.sample(languages, random.randint(1, 3))
        driver.execute_script(f"""
            Object.defineProperty(navigator, 'languages', {{
                get: () => {selected_langs}
            }});
        """)
        
        # Set realistic timezone
        timezones = ['America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney']
        driver.execute_script(f"""
            const timezone = '{random.choice(timezones)}';
            Date.prototype.getTimezoneOffset = function() {{
                return -new Date().getTimezoneOffset();
            }};
        """)
    
    def _simulate_human_behavior(self, driver):
        """Simulate realistic human browsing behavior"""
        actions = ActionChains(driver)
        
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            x = random.randint(0, 1000)
            y = random.randint(0, 800)
            actions.move_by_offset(x, y)
            time.sleep(random.uniform(0.1, 0.5))
        
        # Random scrolling patterns
        scroll_patterns = [
            # Slow scroll down
            lambda: [driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});") 
                    for _ in range(random.randint(3, 8))],
            # Quick scroll to bottom then back up
            lambda: [driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"),
                    time.sleep(random.uniform(1, 3)),
                    driver.execute_script("window.scrollTo(0, 0);")],
            # Random section scrolling
            lambda: [driver.execute_script(f"window.scrollTo(0, {random.randint(200, 1500)});")
                    for _ in range(random.randint(2, 5))]
        ]
        
        pattern = random.choice(scroll_patterns)
        pattern()
        
        # Simulate reading time
        time.sleep(random.uniform(5, 15))
        
        # Try to interact with page elements
        try:
            elements = driver.find_elements(By.TAG_NAME, "a")[:5]
            if elements:
                element = random.choice(elements)
                actions.move_to_element(element).perform()
                time.sleep(random.uniform(0.5, 2))
        except:
            pass
    
    def _get_session_metrics(self, start_time, success, pages_visited=1):
        """Calculate session metrics"""
        duration = time.time() - start_time
        return {
            'duration': duration,
            'success': success,
            'pages_visited': pages_visited,
            'timestamp': datetime.now().isoformat()
        }
    
    def simulate_session(self, session_num):
        """Enhanced session simulation with stealth features"""
        if self.stop_event.is_set():
            return False, {}
        
        start_time = time.time()
        session_metrics = {'pages_visited': 0, 'duration': 0, 'success': False}
        
        try:
            # Update callback with session start
            if self.callback:
                self.callback('session_start', {
                    'session_num': session_num,
                    'total_sessions': self.stats['total_sessions']
                })
            
            options, profile, user_agent, viewport = self._get_stealth_chrome_options()
            
            # Add random delay to avoid detection
            time.sleep(random.uniform(1, 5))
            
            driver = webdriver.Chrome(options=options)
            self._setup_driver_stealth(driver, profile)
            
            # Set viewport
            driver.set_window_size(viewport[0], viewport[1])
            
            # Simulate referrer traffic
            referrer = random.choice(self.referrers)
            if referrer and not self.stop_event.is_set():
                try:
                    driver.get(referrer)
                    time.sleep(random.uniform(1, 3))
                    # Simulate search or social media interaction
                    self._simulate_human_behavior(driver)
                except:
                    pass
            
            # Visit target URL
            if not self.stop_event.is_set():
                driver.get(self.target_url)
                session_metrics['pages_visited'] += 1
                
                # Wait for page load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Simulate human browsing behavior
                self._simulate_human_behavior(driver)
                
                # Randomly visit additional pages
                if random.random() < 0.3:  # 30% chance to visit more pages
                    try:
                        links = driver.find_elements(By.TAG_NAME, "a")
                        internal_links = [link for link in links 
                                        if link.get_attribute("href") and 
                                        self.target_url.split("//")[1].split("/")[0] in link.get_attribute("href")]
                        
                        if internal_links:
                            for _ in range(random.randint(1, 3)):
                                if self.stop_event.is_set():
                                    break
                                link = random.choice(internal_links)
                                try:
                                    link.click()
                                    session_metrics['pages_visited'] += 1
                                    time.sleep(random.uniform(3, 8))
                                    self._simulate_human_behavior(driver)
                                except:
                                    break
                    except:
                        pass
                
                session_metrics['success'] = True
                session_metrics['duration'] = time.time() - start_time
                
                # Update stats
                self.stats['browsers_used'].add(user_agent.split('/')[0])
                self.stats['countries_simulated'].add(random.choice(self.countries))
                self.stats['unique_pages_visited'].add(self.target_url)
                
                logging.info(f"Session {session_num}: Success | UA: {user_agent[:50]}... | "
                           f"Pages: {session_metrics['pages_visited']} | Duration: {session_metrics['duration']:.2f}s")
                
                return True, session_metrics
                
        except Exception as e:
            error_msg = f"Session {session_num} error: {str(e)}"
            logging.error(error_msg)
            self.stats['errors'].append(error_msg)
            session_metrics['duration'] = time.time() - start_time
            return False, session_metrics
        
        finally:
            try:
                driver.quit()
            except:
                pass
            
            # Update callback with session completion
            if self.callback:
                self.callback('session_complete', {
                    'session_num': session_num,
                    'success': session_metrics['success'],
                    'duration': session_metrics['duration'],
                    'pages_visited': session_metrics['pages_visited']
                })
    
    def generate_traffic(self, num_sessions=100, max_concurrent=5):
        """Generate traffic with enhanced tracking and reporting"""
        logging.info(f"Starting enhanced traffic generation: {num_sessions} sessions to {self.target_url}")
        
        self.stats['total_sessions'] = num_sessions
        self.stats['start_time'] = datetime.now()
        
        successful = 0
        failed = 0
        total_duration = 0
        total_pages = 0
        
        def process_session(session_num):
            success, metrics = self.simulate_session(session_num)
            return success, metrics
        
        # Update callback with start
        if self.callback:
            self.callback('generation_start', {'total_sessions': num_sessions})
        
        # Use ThreadPoolExecutor for concurrent sessions
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [executor.submit(process_session, i+1) for i in range(num_sessions)]
            
            for future in futures:
                if self.stop_event.is_set():
                    break
                
                try:
                    success, metrics = future.result(timeout=120)  # 2 minute timeout per session
                    
                    if success:
                        successful += 1
                        self.stats['successful_sessions'] += 1
                    else:
                        failed += 1
                        self.stats['failed_sessions'] += 1
                    
                    total_duration += metrics.get('duration', 0)
                    total_pages += metrics.get('pages_visited', 0)
                    
                    # Update live stats
                    if self.callback:
                        self.callback('stats_update', {
                            'successful': successful,
                            'failed': failed,
                            'completed': successful + failed,
                            'total': num_sessions,
                            'avg_duration': total_duration / (successful + failed) if (successful + failed) > 0 else 0
                        })
                
                except Exception as e:
                    failed += 1
                    self.stats['failed_sessions'] += 1
                    logging.error(f"Session execution error: {str(e)}")
        
        # Final statistics
        self.stats['end_time'] = datetime.now()
        self.stats['total_page_views'] = total_pages
        self.stats['total_time_spent'] = total_duration
        self.stats['avg_session_duration'] = total_duration / num_sessions if num_sessions > 0 else 0
        
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        self.stats['sessions_per_minute'] = (successful + failed) / (duration / 60) if duration > 0 else 0
        self.stats['bounce_rate'] = (failed / num_sessions * 100) if num_sessions > 0 else 0
        
        logging.info(f"Traffic generation complete. Successful: {successful}, Failed: {failed}")
        
        # Update callback with completion
        if self.callback:
            self.callback('generation_complete', self.get_report())
        
        return successful, failed
    
    def get_report(self):
        """Generate comprehensive traffic report"""
        return {
            'session_id': self.session_id,
            'target_url': self.target_url,
            'stats': dict(self.stats),
            'summary': {
                'success_rate': f"{(self.stats['successful_sessions'] / self.stats['total_sessions'] * 100):.1f}%" if self.stats['total_sessions'] > 0 else "0%",
                'total_runtime': str(self.stats['end_time'] - self.stats['start_time']) if self.stats['start_time'] and self.stats['end_time'] else "N/A",
                'avg_pages_per_session': f"{self.stats['total_page_views'] / self.stats['total_sessions']:.1f}" if self.stats['total_sessions'] > 0 else "0",
                'performance_score': self._calculate_performance_score()
            }
        }
    
    def _calculate_performance_score(self):
        """Calculate overall performance score"""
        if self.stats['total_sessions'] == 0:
            return 0
        
        success_rate = self.stats['successful_sessions'] / self.stats['total_sessions']
        speed_score = min(self.stats['sessions_per_minute'] / 10, 1)  # Normalize to 10 sessions/min
        diversity_score = len(self.stats['browsers_used']) / 5  # Normalize to 5 different browsers
        
        return int((success_rate * 0.5 + speed_score * 0.3 + diversity_score * 0.2) * 100)
    
    def stop(self):
        """Stop traffic generation"""
        self.stop_event.set()
        logging.info("Stop signal sent to traffic generator")
    
    def get_system_info(self):
        """Get system performance information"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'active_threads': threading.active_count()
        }

# Alias for backward compatibility
TrafficGenerator = StealthTrafficGenerator
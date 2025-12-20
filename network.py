import requests
from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
import time
import random

def login_to_odi(username, password) -> Optional[requests.Session]:
    """
    Attempts to log in to getodi.com with the given username and password.
    Returns a requests.Session object if successful, otherwise None.
    Uses stealth techniques to avoid detection.
    """
    login_url = "https://getodi.com/sign-in/"
    session = requests.Session()
    
    # Setup realistic browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    })
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        # First, visit the login page (like a real browser)
        response = session.get(login_url, timeout=10)
        if response.status_code != 200:
            print("Login failed: Could not access login page.")
            return None
        
        # Random delay to mimic human behavior
        time.sleep(random.uniform(0.5, 1.5))
        
        # Login
        response = session.post(login_url, data=login_data, timeout=10)
        if response.status_code == 200:
            # Check if login was actually successful (e.g., not on login page anymore)
            if 'wrong_credentials' in response.url or "sign-in" in response.url:
                print("Login failed in network.py. Incorrect credentials or still on login page.")
                return None
            print("Login successful in network.py.")
            return session
        else:
            print(f"Login failed in network.py. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during login in network.py: {e}")
        return None

def create_session_from_cookies(cookies: dict) -> Optional[requests.Session]:
    """
    Create a requests.Session from saved cookies.
    Returns a session object if cookies are valid, otherwise None.
    """
    if not cookies:
        return None
    
    session = requests.Session()
    
    # Set cookies in the session
    # Use requests.cookies.create_cookie for proper cookie handling
    for name, value in cookies.items():
        # Create cookie with proper domain
        cookie = requests.cookies.create_cookie(
            name=name,
            value=value,
            domain='.getodi.com'  # Use dot prefix for subdomain matching
        )
        session.cookies.set_cookie(cookie)
    
    # Test if session is still valid by making a request
    try:
        test_url = "https://getodi.com/student/?city=35"
        response = session.get(test_url, timeout=10)
        
        # Check if we're redirected to login page (session expired)
        if 'sign-in' in response.url or 'login' in response.url.lower():
            print("Session cookies expired: redirected to login page")
            return None
        
        # Check if response contains login page indicators
        if 'sign-in' in response.text.lower() or ('username' in response.text.lower() and 'password' in response.text.lower()):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            login_form = soup.find('form', {'action': lambda x: x and 'sign-in' in x.lower()})
            if login_form:
                print("Session cookies expired: response contains login form")
                return None
        
        print("Session restored from cookies successfully")
        return session
    except requests.exceptions.RequestException as e:
        print(f"Error testing session from cookies: {e}")
        return None

def get_session_cookies(session: requests.Session) -> dict:
    """
    Extract cookies from a session as a dictionary.
    """
    cookies_dict = {}
    for cookie in session.cookies:
        cookies_dict[cookie.name] = cookie.value
    return cookies_dict

def check_meals(session: requests.Session, target_texts: List[str], city_id: str = "35") -> Optional[List[Dict[str, Any]]]:
    """
    Uses the session to check the meals page and search for target texts.
    New logic: A restaurant is considered available if the "Askıdan al" button is active
    (not disabled and has onclick that opens a modal). If button is disabled or has
    onclick="return false;", it's not available.
    Uses stealth techniques to avoid detection.
    Returns a list of found meals or None if there is an error.
    """
    meals_url = f"https://getodi.com/student/?city={city_id}"
    try:
        # Add referer header to make it look like navigation from student page
        headers = {
            'Referer': 'https://getodi.com/student/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        # Random delay to mimic human behavior (1-2 seconds)
        time.sleep(random.uniform(1.0, 2.0))
        
        response = session.get(meals_url, headers=headers, timeout=10)
        
        # Check if session is expired (redirected to login page)
        if 'sign-in' in response.url or 'login' in response.url.lower():
            print(f"Session expired: redirected to login page. URL: {response.url}")
            return None
        
        # Check if response contains login page indicators
        if response.ok:
            # Check if the response is actually the login page (session expired)
            if 'sign-in' in response.text.lower() or 'username' in response.text.lower() and 'password' in response.text.lower():
                # Check if we're looking at a login form
                soup_temp = BeautifulSoup(response.text, 'html.parser')
                login_form = soup_temp.find('form', {'action': lambda x: x and 'sign-in' in x.lower()})
                if login_form:
                    print("Session expired: response contains login form")
                    return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            meals_data: List[Dict[str, Any]] = []
            found_meals: Set[str] = set()

            menu_boxes = soup.select('div.menu-box')
            for menu_box in menu_boxes:
                if not isinstance(menu_box, Tag):
                    continue

                restaurant_name_tag = menu_box.select_one('div.menu-restaurant')
                menu_title_tag = menu_box.select_one('div.menu-title')
                menu_details_tag = menu_box.select_one('div.menu-details')

                restaurant_name_text = restaurant_name_tag.get_text(strip=True) if restaurant_name_tag else ""
                menu_title_text = menu_title_tag.get_text(strip=True) if menu_title_tag else ""
                menu_details_text = menu_details_tag.get_text(strip=True) if menu_details_tag else ""

                searchable_text_content = f"{restaurant_name_text} {menu_title_text} {menu_details_text}".lower()

                for target_text in target_texts:
                    if target_text.lower() in searchable_text_content and target_text not in found_meals:
                        # Find the "Askıdan al" button in this menu box
                        askidan_al_button = None
                        menu_buttons = menu_box.select('div.menu-btn-take')
                        for button in menu_buttons:
                            if isinstance(button, Tag):
                                button_text = button.get_text(strip=True).lower()
                                if 'askıdan al' in button_text:
                                    askidan_al_button = button
                                    break
                        
                        if not askidan_al_button:
                            # Button not found, skip this menu box
                            continue
                        
                        # Check if button is disabled
                        is_available = False
                        class_attr_raw = askidan_al_button.get('class')
                        if class_attr_raw is None:
                            class_attr = []
                        elif isinstance(class_attr_raw, str):
                            class_attr = [class_attr_raw]
                        elif isinstance(class_attr_raw, list):
                            class_attr = class_attr_raw
                        else:
                            class_attr = []
                        
                        has_disabled_class = 'disabled' in class_attr
                        
                        # Check onclick attribute
                        onclick_attr = askidan_al_button.get('onclick', '')
                        onclick_str = str(onclick_attr).lower()
                        has_return_false = 'return false' in onclick_str and 'modal' not in onclick_str
                        
                        # Button is available if:
                        # 1. It doesn't have "disabled" class
                        # 2. onclick doesn't contain "return false" (or contains modal which means it's active)
                        if not has_disabled_class and not has_return_false:
                            # Additional check: if onclick contains modal, it's definitely active
                            if 'modal' in onclick_str and 'reserve' in onclick_str:
                                is_available = True
                            elif 'return false' not in onclick_str:
                                # If no return false and no disabled class, consider it available
                                is_available = True
                        
                        if is_available:
                            actual_restaurant_name_display = menu_title_text or restaurant_name_text or target_text
                            actual_meal_name = restaurant_name_text or "No meal name available."
                            actual_location = menu_details_text or "No location available."

                            meal_info = {
                                'restaurant_name': actual_restaurant_name_display,
                                'meal_name': actual_meal_name,
                                'location': actual_location,
                                'available_count': 1,  # Button is active, so at least 1 meal available
                                'available': True,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            meals_data.append(meal_info)
                            found_meals.add(target_text)
                            break
            
            return meals_data
        else:
            print(f"Failed to access the meals page in network.py. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking meals in network.py: {e}")
        return None 
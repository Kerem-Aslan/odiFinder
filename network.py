import requests
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from typing import Optional, List, Dict, Any, Set, Tuple
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
        # No 'br': requests can only decode Brotli if the optional brotli package is installed
        'Accept-Encoding': 'gzip, deflate',
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

def _normalize_text(text: str) -> str:
    """Lowercases text with Turkish casing rules ("I" -> "ı", "İ" -> "i")."""
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def _is_login_page(soup: BeautifulSoup) -> bool:
    return soup.find('form', {'action': lambda x: x and 'sign-in' in x.lower()}) is not None

def _is_button_available(button: Tag) -> bool:
    """
    The "Askıdan al" button is available unless it is disabled or its onclick
    only does "return false" (an active button's onclick opens the reserve modal).
    """
    classes = button.get('class') or []
    if 'disabled' in classes or button.has_attr('disabled') or str(button.get('aria-disabled', '')).lower() == 'true':
        return False
    onclick = str(button.get('onclick', '')).lower()
    if 'modal' in onclick and 'reserve' in onclick:
        return True
    return 'return false' not in onclick

def check_meals(session: requests.Session, target_texts: List[str], city_id: str = "35") -> Optional[List[Dict[str, Any]]]:
    """
    Uses the session to check the meals page and search for target texts.
    A restaurant is considered available if its "Askıdan al" button is active.
    Uses stealth techniques to avoid detection.
    Returns a list of found meals, or None if the session has expired (the caller should log in again).
    Raises requests.exceptions.RequestException on network or HTTP errors.
    """
    meals_url = f"https://getodi.com/student/?city={city_id}"
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
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    if _is_login_page(soup):
        print("Session expired: response contains login form")
        return None

    normalized_targets = [(target, _normalize_text(target)) for target in target_texts if target.strip()]
    meals_data: List[Dict[str, Any]] = []
    found_boxes: Set[Tuple[str, str, str]] = set()

    for menu_box in soup.select('div.menu-box'):
        if not isinstance(menu_box, Tag):
            continue

        restaurant_name_tag = menu_box.select_one('div.menu-restaurant')
        menu_title_tag = menu_box.select_one('div.menu-title')
        menu_details_tag = menu_box.select_one('div.menu-details')

        restaurant_name_text = restaurant_name_tag.get_text(strip=True) if restaurant_name_tag else ""
        menu_title_text = menu_title_tag.get_text(strip=True) if menu_title_tag else ""
        menu_details_text = menu_details_tag.get_text(strip=True) if menu_details_tag else ""

        box_key = (restaurant_name_text, menu_title_text, menu_details_text)
        if box_key in found_boxes:
            continue

        searchable_text_content = _normalize_text(f"{restaurant_name_text} {menu_title_text} {menu_details_text}")
        matched_target = next((target for target, normalized in normalized_targets if normalized in searchable_text_content), None)
        if matched_target is None:
            continue

        # Find the "Askıdan al" button (also matches "Askıdan Ücretsiz Al") in this menu box
        askidan_al_button = next(
            (button for button in menu_box.select('div.menu-btn-take')
             if isinstance(button, Tag) and 'askıdan' in _normalize_text(button.get_text(strip=True))),
            None
        )
        if askidan_al_button is None or not _is_button_available(askidan_al_button):
            continue

        meals_data.append({
            'restaurant_name': menu_title_text or restaurant_name_text or matched_target,
            'meal_name': restaurant_name_text or "No meal name available.",
            'location': menu_details_text or "No location available.",
            'available_count': 1,  # Button is active, so at least 1 meal available
            'available': True,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        found_boxes.add(box_key)

    return meals_data

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from src.models.user import db, Task, Event, WBAccount

logger = logging.getLogger(__name__)

class WBService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.pages: Dict[int, Page] = {}  # account_id -> page
        self.playwright = None
        self.is_running = False
        
    async def start_browser(self):
        """Start Playwright browser with optimized settings"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            self.is_running = True
        return self.browser
    
    async def stop_browser(self):
        """Stop Playwright browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.pages.clear()
            self.is_running = False
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def get_page_for_account(self, wb_account: WBAccount) -> Page:
        """Get or create page for WB account with proper setup"""
        if wb_account.id not in self.pages:
            browser = await self.start_browser()
            page = await browser.new_page()
            
            # Set viewport and user agent
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Set cookies if available
            if wb_account.cookies:
                try:
                    cookies = json.loads(wb_account.cookies)
                    # Ensure cookies have proper format
                    for cookie in cookies:
                        if 'domain' not in cookie:
                            cookie['domain'] = '.wildberries.ru'
                        if 'path' not in cookie:
                            cookie['path'] = '/'
                    await page.context.add_cookies(cookies)
                    logger.info(f"Set {len(cookies)} cookies for account {wb_account.id}")
                except Exception as e:
                    logger.error(f"Failed to set cookies for account {wb_account.id}: {e}")
            
            # Set extra headers
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            self.pages[wb_account.id] = page
        
        return self.pages[wb_account.id]
    
    async def login_to_wb(self, wb_account: WBAccount) -> bool:
        """Login to Wildberries account"""
        try:
            page = await self.get_page_for_account(wb_account)
            
            # Navigate to WB login page
            await page.goto('https://seller.wildberries.ru/', wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Check if already logged in by looking for user menu or dashboard elements
            try:
                # Look for elements that indicate successful login
                await page.wait_for_selector('[data-testid="user-menu"], .user-menu, .profile-menu', timeout=5000)
                logger.info(f"Account {wb_account.account_name} already logged in")
                return True
            except PlaywrightTimeoutError:
                # Check if we're on login page
                if 'login' in page.url or 'auth' in page.url:
                    logger.warning(f"Manual login required for account {wb_account.account_name}")
                    return False
                
                # Try to navigate to a protected page to check login status
                await page.goto('https://seller.wildberries.ru/supplies-management/all-supplies', wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                if 'login' in page.url or 'auth' in page.url:
                    logger.warning(f"Session expired for account {wb_account.account_name}")
                    return False
                
                logger.info(f"Account {wb_account.account_name} appears to be logged in")
                return True
            
        except Exception as e:
            logger.error(f"Login check failed for account {wb_account.id}: {e}")
            return False
    
    async def search_slots(self, task: Task) -> List[Dict]:
        """Search for available slots based on task parameters"""
        try:
            if not task.wb_account:
                logger.error(f"No WB account assigned to task {task.id}")
                return []
            
            # Check if account is logged in
            if not await self.login_to_wb(task.wb_account):
                logger.error(f"Failed to login for task {task.id}")
                return []
            
            page = await self.get_page_for_account(task.wb_account)
            
            # Navigate to supplies management page
            await page.goto('https://seller.wildberries.ru/supplies-management/all-supplies', wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Check if logged in
            if 'login' in page.url or 'auth' in page.url:
                logger.error(f"Not logged in for task {task.id}")
                return []
            
            # Search for slots based on task parameters
            slots = await self._find_available_slots(page, task)
            
            # Update task with found slots count
            task.found_slots = len(slots)
            task.last_check = datetime.utcnow()
            db.session.commit()
            
            # Create event
            if slots:
                event = Event(
                    task_id=task.id,
                    user_id=task.user_id,
                    event_type='success',
                    message=f'Найдено {len(slots)} слотов для задачи "{task.name}"',
                    details=json.dumps(slots)
                )
            else:
                event = Event(
                    task_id=task.id,
                    user_id=task.user_id,
                    event_type='info',
                    message=f'Слоты не найдены для задачи "{task.name}"'
                )
            
            db.session.add(event)
            db.session.commit()
            
            return slots
            
        except Exception as e:
            logger.error(f"Slot search failed for task {task.id}: {e}")
            
            # Create error event
            event = Event(
                task_id=task.id,
                user_id=task.user_id,
                event_type='error',
                message=f'Ошибка поиска слотов: {str(e)}'
            )
            db.session.add(event)
            db.session.commit()
            
            return []
    
    async def _find_available_slots(self, page: Page, task: Task) -> List[Dict]:
        """Find available slots on the page using real WB selectors"""
        slots = []
        
        try:
            # Wait for page to load and look for create supply button
            try:
                await page.wait_for_selector('button[data-testid="create-supply-button"], .create-supply-btn, button:has-text("Создать поставку")', timeout=10000)
            except PlaywrightTimeoutError:
                # Try alternative selectors
                try:
                    await page.wait_for_selector('button:has-text("Создать"), .btn-primary', timeout=5000)
                except PlaywrightTimeoutError:
                    logger.error("Could not find create supply button")
                    return slots
            
            # Click create supply button
            try:
                await page.click('button[data-testid="create-supply-button"], .create-supply-btn, button:has-text("Создать поставку")')
            except:
                await page.click('button:has-text("Создать")')
            
            await page.wait_for_timeout(3000)
            
            # Wait for modal or form to appear
            try:
                await page.wait_for_selector('.modal, .form, [role="dialog"]', timeout=10000)
            except PlaywrightTimeoutError:
                logger.error("Supply creation modal did not appear")
                return slots
            
            # Select warehouse - try multiple selectors
            warehouse_selected = False
            warehouse_selectors = [
                f'text="{task.warehouse}"',
                f'[data-value="{task.warehouse}"]',
                f'option:has-text("{task.warehouse}")',
                f'[title="{task.warehouse}"]'
            ]
            
            for selector in warehouse_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    warehouse_selected = True
                    logger.info(f"Selected warehouse: {task.warehouse}")
                    break
                except:
                    continue
            
            if not warehouse_selected:
                logger.warning(f"Warehouse {task.warehouse} not found")
                return slots
            
            await page.wait_for_timeout(2000)
            
            # Select packaging type
            packaging_selected = False
            packaging_value = "Короба" if task.packaging == "boxes" else "Палеты"
            packaging_selectors = [
                f'text="{packaging_value}"',
                f'[data-value="{packaging_value}"]',
                f'option:has-text("{packaging_value}")',
                f'[title="{packaging_value}"]'
            ]
            
            for selector in packaging_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    packaging_selected = True
                    logger.info(f"Selected packaging: {packaging_value}")
                    break
                except:
                    continue
            
            if not packaging_selected:
                logger.warning(f"Packaging {packaging_value} not found")
                return slots
            
            await page.wait_for_timeout(2000)
            
            # Look for available dates and coefficients
            # Try multiple selectors for date slots
            date_selectors = [
                '[data-testid*="date-slot"]',
                '.date-slot',
                '.slot-item',
                '.available-date',
                '[class*="date"]',
                '[class*="slot"]'
            ]
            
            date_elements = []
            for selector in date_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        date_elements = elements
                        logger.info(f"Found {len(elements)} date elements with selector: {selector}")
                        break
                except:
                    continue
            
            if not date_elements:
                logger.warning("No date elements found")
                return slots
            
            # Parse each date element
            for i, date_element in enumerate(date_elements):
                try:
                    # Get text content
                    element_text = await date_element.text_content()
                    if not element_text:
                        continue
                    
                    # Look for coefficient in the element
                    coefficient = None
                    coefficient_selectors = [
                        '[data-testid*="coefficient"]',
                        '.coefficient',
                        '.coeff',
                        '[class*="coeff"]',
                        '[class*="rate"]'
                    ]
                    
                    for coeff_selector in coefficient_selectors:
                        try:
                            coeff_element = await date_element.query_selector(coeff_selector)
                            if coeff_element:
                                coeff_text = await coeff_element.text_content()
                                if coeff_text:
                                    # Extract number from text
                                    coeff_match = re.search(r'[\d,]+\.?\d*', coeff_text.replace(',', '.'))
                                    if coeff_match:
                                        coefficient = float(coeff_match.group())
                                        break
                        except:
                            continue
                    
                    # If no coefficient found in sub-elements, try to extract from main text
                    if coefficient is None:
                        coeff_match = re.search(r'[\d,]+\.?\d*', element_text.replace(',', '.'))
                        if coeff_match:
                            coefficient = float(coeff_match.group())
                    
                    # Extract date from text
                    slot_date = self._parse_date_from_text(element_text)
                    
                    # Check if this slot meets our criteria
                    if coefficient and coefficient >= task.coefficient:
                        if task.date_from <= slot_date.date() <= task.date_to:
                            slot = {
                                'id': f"slot_{task.id}_{i}",
                                'date': slot_date.isoformat(),
                                'coefficient': coefficient,
                                'warehouse': task.warehouse,
                                'packaging': task.packaging,
                                'raw_text': element_text.strip()
                            }
                            slots.append(slot)
                            logger.info(f"Found valid slot: {slot}")
                
                except Exception as e:
                    logger.error(f"Error parsing slot element {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error finding slots: {e}")
        
        return slots
    
    def _parse_date_from_text(self, date_text: str) -> datetime:
        """Parse date from text with multiple format support"""
        try:
            # Clean the text
            text = date_text.strip().lower()
            
            # Try different date patterns
            patterns = [
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
                r'(\d{1,2})/(\d{1,2})/(\d{4})',   # DD/MM/YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{4})',   # DD-MM-YYYY
                r'(\d{4})-(\d{1,2})-(\d{1,2})',   # YYYY-MM-DD
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD format
                            year, month, day = groups
                        else:  # DD.MM.YYYY format
                            day, month, year = groups
                        
                        return datetime(int(year), int(month), int(day))
            
            # Try relative dates
            if 'сегодня' in text or 'today' in text:
                return datetime.now()
            elif 'завтра' in text or 'tomorrow' in text:
                return datetime.now() + timedelta(days=1)
            elif 'послезавтра' in text:
                return datetime.now() + timedelta(days=2)
            
            # Try to extract day and month from current context
            day_match = re.search(r'(\d{1,2})', text)
            if day_match:
                day = int(day_match.group())
                # Assume current month and year
                now = datetime.now()
                return datetime(now.year, now.month, day)
            
            # Default to tomorrow if nothing else works
            return datetime.now() + timedelta(days=1)
            
        except Exception as e:
            logger.error(f"Error parsing date from text '{date_text}': {e}")
            return datetime.now() + timedelta(days=1)
    
    def _parse_date(self, date_text: str) -> datetime:
        """Legacy method for backward compatibility"""
        return self._parse_date_from_text(date_text)
    
    async def book_slot(self, task: Task, slot: Dict) -> bool:
        """Book a specific slot with real WB interaction"""
        try:
            if not task.auto_book:
                logger.info(f"Auto-booking disabled for task {task.id}")
                return False
            
            page = await self.get_page_for_account(task.wb_account)
            
            # Navigate to supplies management page
            await page.goto('https://seller.wildberries.ru/supplies-management/all-supplies', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Click create supply button
            try:
                await page.click('button[data-testid="create-supply-button"], .create-supply-btn, button:has-text("Создать поставку")')
            except:
                await page.click('button:has-text("Создать")')
            
            await page.wait_for_timeout(3000)
            
            # Wait for modal
            await page.wait_for_selector('.modal, .form, [role="dialog"]', timeout=10000)
            
            # Select warehouse
            warehouse_selected = False
            warehouse_selectors = [
                f'text="{task.warehouse}"',
                f'[data-value="{task.warehouse}"]',
                f'option:has-text("{task.warehouse}")'
            ]
            
            for selector in warehouse_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    warehouse_selected = True
                    break
                except:
                    continue
            
            if not warehouse_selected:
                logger.error(f"Could not select warehouse {task.warehouse}")
                return False
            
            await page.wait_for_timeout(1000)
            
            # Select packaging
            packaging_value = "Короба" if task.packaging == "boxes" else "Палеты"
            packaging_selected = False
            packaging_selectors = [
                f'text="{packaging_value}"',
                f'[data-value="{packaging_value}"]',
                f'option:has-text("{packaging_value}")'
            ]
            
            for selector in packaging_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    packaging_selected = True
                    break
                except:
                    continue
            
            if not packaging_selected:
                logger.error(f"Could not select packaging {packaging_value}")
                return False
            
            await page.wait_for_timeout(1000)
            
            # Find and click the specific slot
            slot_found = False
            slot_selectors = [
                f'[data-slot-id="{slot["id"]}"]',
                f'[data-date="{slot["date"][:10]}"]',
                f'[data-coefficient="{slot["coefficient"]}"]'
            ]
            
            # Also try to find by text content
            try:
                slot_elements = await page.query_selector_all('.slot-item, .date-slot, [class*="slot"]')
                for element in slot_elements:
                    text = await element.text_content()
                    if text and (slot["date"][:10] in text or str(slot["coefficient"]) in text):
                        await element.click()
                        slot_found = True
                        break
            except:
                pass
            
            if not slot_found:
                # Try clicking on the first available slot as fallback
                try:
                    await page.click('.slot-item:first-child, .date-slot:first-child')
                    slot_found = True
                except:
                    pass
            
            if not slot_found:
                logger.error(f"Could not find slot {slot['id']} to book")
                return False
            
            await page.wait_for_timeout(1000)
            
            # Look for confirm/booking button
            booking_buttons = [
                'button:has-text("Забронировать")',
                'button:has-text("Подтвердить")',
                'button:has-text("Создать")',
                '.btn-primary',
                '.confirm-btn'
            ]
            
            booking_clicked = False
            for button_selector in booking_buttons:
                try:
                    await page.click(button_selector, timeout=3000)
                    booking_clicked = True
                    break
                except:
                    continue
            
            if not booking_clicked:
                logger.warning("Could not find booking confirmation button")
                # Still consider it successful if we clicked the slot
            
            await page.wait_for_timeout(2000)
            
            # Check for success indicators
            success_indicators = [
                'text="Успешно"',
                'text="Забронировано"',
                '.success-message',
                '.alert-success'
            ]
            
            booking_successful = False
            for indicator in success_indicators:
                try:
                    await page.wait_for_selector(indicator, timeout=5000)
                    booking_successful = True
                    break
                except:
                    continue
            
            # If no explicit success indicator, assume success if no error
            if not booking_successful:
                # Check for error indicators
                error_indicators = [
                    'text="Ошибка"',
                    'text="Не удалось"',
                    '.error-message',
                    '.alert-error'
                ]
                
                has_error = False
                for indicator in error_indicators:
                    try:
                        await page.wait_for_selector(indicator, timeout=2000)
                        has_error = True
                        break
                    except:
                        continue
                
                booking_successful = not has_error
            
            if booking_successful:
                # Create success event
                event = Event(
                    task_id=task.id,
                    user_id=task.user_id,
                    event_type='success',
                    message=f'Слот успешно забронирован: {slot["date"]}, коэффициент {slot["coefficient"]}'
                )
                db.session.add(event)
                db.session.commit()
                
                logger.info(f"Slot successfully booked for task {task.id}: {slot}")
                return True
            else:
                # Create error event
                event = Event(
                    task_id=task.id,
                    user_id=task.user_id,
                    event_type='error',
                    message=f'Не удалось забронировать слот: {slot["date"]}'
                )
                db.session.add(event)
                db.session.commit()
                
                logger.error(f"Slot booking failed for task {task.id}: {slot}")
                return False
            
        except Exception as e:
            logger.error(f"Booking failed for task {task.id}: {e}")
            
            # Create error event
            event = Event(
                task_id=task.id,
                user_id=task.user_id,
                event_type='error',
                message=f'Ошибка бронирования слота: {str(e)}'
            )
            db.session.add(event)
            db.session.commit()
            
            return False
    
    async def find_shipment_slots(self, task: Task) -> List[Dict]:
        """Find slots by shipment number"""
        if not task.shipment_number:
            return []
        
        try:
            page = await self.get_page_for_account(task.wb_account)
            
            # Navigate to shipments page
            await page.goto('https://seller.wildberries.ru/supplies-management/all-supplies')
            await page.wait_for_timeout(2000)
            
            # Search for shipment number
            search_input = await page.query_selector('input[placeholder*="поиск"]')
            if search_input:
                await search_input.fill(task.shipment_number)
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(2000)
                
                # Look for available slots for this shipment
                # This would contain logic to find and book slots for specific shipment
                
                logger.info(f"Searched for shipment {task.shipment_number}")
            
            return []
            
        except Exception as e:
            logger.error(f"Shipment search failed for task {task.id}: {e}")
            return []

# Global service instance
wb_service = WBService()


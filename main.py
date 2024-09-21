import asyncio
from playwright.async_api import async_playwright
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchedulingService:
    def __init__(self, url):
        self.url = url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.closed = True
        self.state = {}  # Caching system for appointment types and dates

    async def initialize_browser(self, headless=True):
        """Start Playwright and open the browser."""
        logger.info("Initializing the browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.closed = False
        logger.info("Browser initialized.")

    async def close_browser(self):
        """Close the browser and Playwright."""
        logger.info("Closing the browser...")
        if not self.closed:
            await self.page.close()
            await self.context.close()
            await self.browser.close()
            await self.playwright.stop()
            self.closed = True
            logger.info("Browser closed.")

    async def navigate_to_scheduling_page(self):
        """Navigate to the scheduling page and wait for it to load."""
        logger.info(f"Navigating to {self.url}...")
        try:
            await self.page.goto(self.url)
            await self.page.wait_for_load_state('networkidle')
            logger.info("Page loaded successfully.")
        except Exception as e:
            logger.error(f"Error navigating to the page: {str(e)}")
            await self.page.screenshot(path="error_screenshot.png")
            raise

    async def select_appointment_type_direct_click(self, appointment_type):
        """Select the appointment type by clicking the corresponding button/link."""
        logger.info(f"Selecting appointment type: {appointment_type}")
        try:
            if appointment_type == "New appointment":
                await self.page.click('text="New appointment"')
            elif appointment_type == "Emergency appointment":
                await self.page.click('text="Emergency appointment"')
            elif appointment_type == "Invisalign consultation":
                await self.page.click('text="Invisalign consultation"')
            else:
                raise ValueError(f"Unknown appointment type: {appointment_type}")
            logger.info(f"{appointment_type} selected.")
        except Exception as e:
            logger.error(f"Error selecting appointment type: {str(e)}")
            await self.page.screenshot(path="error_screenshot.png")
            raise

    async def set_date_preference(self, date_preference):
        """Set date preference on the calendar if required."""
        if date_preference:
            logger.info(f"Selecting date: {date_preference}")
            try:
                # Assuming there's a date picker we need to interact with
                await self.page.click(f'text="{date_preference}"')  # Adjust as per actual calendar implementation
                logger.info(f"Date {date_preference} selected.")
            except Exception as e:
                logger.error(f"Error selecting date: {str(e)}")
                await self.page.screenshot(path="error_screenshot.png")
                raise

    async def get_available_slots(self):
        """Scrape available appointment slots."""
        logger.info("Checking available appointment slots...")
        try:
            await self.page.wait_for_selector('.time-slot', timeout=10000)  # Adjust the selector as per actual site
            slots = await self.page.query_selector_all('.time-slot')  # Example selector for slot elements

            available_slots = []
            for slot in slots[:5]:  # Limit to the first 5 slots
                time_text = await slot.inner_text()  # Extract time information
                date_text = await self.page.locator('.selected-date').inner_text()  # Adjust as per actual date element
                available_slots.append({'date': date_text, 'time': time_text})

            logger.info(f"Available slots found: {available_slots}")
            return available_slots
        except Exception as e:
            logger.error(f"Error checking available slots: {str(e)}")
            await self.page.screenshot(path="error_screenshot.png")
            raise

    async def check_available_appointments(self, appointment_type, date_preference=None):
        """Check available appointments for a specific type and optional date."""
        cache_key = (appointment_type, date_preference)
        if cache_key in self.state:
            logger.info(f"Using cached data for {appointment_type} on {date_preference}")
            return self.state[cache_key]

        await self.navigate_to_scheduling_page()
        await self.select_appointment_type_direct_click(appointment_type)
        if date_preference:
            await self.set_date_preference(date_preference)

        available_slots = await self.get_available_slots()
        self.state[cache_key] = available_slots  # Cache the result
        return available_slots

# Example usage
async def main():
    url = "https://care.425dental.com/schedule-appointments/?_gl=11eu87tj_gcl_auMTY4NjUyNjY2NC4xNzI2MjUyODIw_gaNzc0MzUzODQ3LjE3MjYyNTI4MjA._ga_P7N65JEY18*MTcyNjg2NDgzMi41LjEuMTcyNjg2NDkwMi4wLjAuMA.."
    service = SchedulingService(url)

    try:
        await service.initialize_browser(headless=True)  # Set headless=False for debugging
        appointment_type = "New appointment"
        date_preference = None  # Optionally pass a date preference
        available_slots = await service.check_available_appointments(appointment_type, date_preference)
        logger.info(f"Available slots: {available_slots}")
    finally:
        await service.close_browser()

if __name__ == "__main__":
    asyncio.run(main())

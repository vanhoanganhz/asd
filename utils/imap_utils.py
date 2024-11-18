import re
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from bs4 import BeautifulSoup
from loguru import logger
from imap_tools import MailBox, AND


async def check_if_email_valid(imap_server: str, email: str, password: str) -> bool:
    """Checks if the email credentials are valid by attempting to log in."""
    logger.info(f"Account: {email} | Checking if email is valid...")
    try:
        async with MailBox(imap_server).login(email, password):
            return True
    except Exception as error:
        logger.error(f"Account: {email} | Email is invalid (IMAP): {error}")
        return False


async def check_email_for_code(imap_server: str, email: str, password: str, max_attempts: int = 8, delay_seconds: int = 5) -> Optional[str]:
    """Checks email for a code within a specified number of attempts and delay between attempts."""
    logger.info(f"Account: {email} | Checking email for code...")

    code_pattern = re.compile(r'<div class="pDiv">\s*([A-Z0-9])\s*</div>')

    async def search_in_mailbox() -> Optional[str]:
        async with MailBox(imap_server).login(email, password) as mailbox:
            current_time = datetime.now()
            minutes_ago = current_time - timedelta(minutes=1)
            messages = mailbox.fetch(AND(from_="noreply@gradient.network", date_gte=minutes_ago.date()))

            for msg in messages:
                body = msg.text or msg.html
                if body and (match := code_pattern.search(body)):
                    soup = BeautifulSoup(body, "html.parser")
                    code_divs = soup.find_all("div", class_="pDiv")
                    code = "".join(div.text.strip() for div in code_divs if div.text.strip())
                    if len(code) == 6:
                        return code
        return None

    for attempt in range(max_attempts):
        link = await asyncio.to_thread(search_in_mailbox)
        if link:
            logger.success(f"Account: {email} | Code found: {link}")
            return link

        logger.info(f"Account: {email} | Code not found. Waiting {delay_seconds} seconds before next attempt...")
        await asyncio.sleep(delay_seconds)

    logger.warning(f"Account: {email} | Code not found after {max_attempts} attempts, searching in spam folder...")
    return await search_for_code_in_spam_sync(imap_server, email, password, "Spam Folder")


async def search_for_code_sync(mailbox: MailBox, code_pattern: str) -> Optional[str]:
    """Searches the mailbox for a code using a specified pattern."""
    current_time = datetime.now()
    minutes_ago = current_time - timedelta(minutes=1)
    messages = mailbox.fetch(AND(from_="noreply@gradient.network", date_gte=minutes_ago.date()))

    for msg in messages:
        body = msg.text or msg.html
        if body and (match := re.search(code_pattern, body)):
            soup = BeautifulSoup(body, "html.parser")
            code_divs = soup.find_all("div", class_="pDiv")
            code = "".join(div.text.strip() for div in code_divs if div.text.strip())
            if len(code) == 6:
                return code
    return None


async def search_for_code_in_spam_sync(mailbox: MailBox, link_pattern: str, spam_folder: str) -> Optional[str]:
    """Searches for a code in a specified spam folder."""
    if mailbox.folder.exists(spam_folder):
        mailbox.folder.set(spam_folder)
        return await search_for_code_sync(mailbox, link_pattern)
    return None

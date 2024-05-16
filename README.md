# Nitro-Bruteforcer

It bruteforces a certain Nitro subscription in discord with appropriate credentials.


# Features

1. **Generate Mastercard Details**:
   - Creates random 16-digit Mastercard numbers using luhn algorithm.
   - Includes 3-digit CVV codes.
   - Provides expiry dates in MM/YY format.

2. **Save Card Details**:
   - Stores generated card details (card number, CVV, expiry date) in a `cards.txt` file.

3. **Validate Cards**:
   - Reads card details from `cards.txt`.
   - Tests each card by attempting to redeem Discord Nitro using an API endpoint.

4. **Error Handling**:
   - Manages invalid responses and errors during card validation.
   - Offers feedback on the success or failure of each test.

5. **Customization**:
   - Adjustable to generate a different number of cards.
   - Configurable for different API endpoints and authorization tokens.

6. **Educational Purpose**:
   - Designed for learning about generating and handling sensitive data.
   - Demonstrates file operations and API requests in Python.

This program aims to provide a hands-on learning experience while demonstrating essential programming concepts.

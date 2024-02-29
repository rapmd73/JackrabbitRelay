def update_wallet(wallets, action, asset, amount, price, fee_rate=0.0073):
    """
    Update the wallets based on the action (buy or sell) for a specific asset at a given price, and track fees separately.

    Args:
        wallets (dict): Dictionary containing the wallets for each asset pair.
        action (str): Action to perform ('buy' or 'sell').
        asset (str): Name of the asset pair.
        amount (float): Amount of the asset to buy (positive) or sell (negative).
        price (float): Price of the asset.
        fee_rate (float, optional): Fee rate for the transaction (default is 0.3%).

    Returns:
        None: The wallets dictionary and fee balance are updated in-place.
    """
    # Split the asset pair into base and quote currencies
    base_asset, quote_asset = asset.split('/')

    if action == 'buy':
        # Calculate the total cost for buying the asset including fees
        total_cost = abs(amount) * price * (1 + fee_rate)
        # Check if the wallet has enough balance for the purchase including fees
        if quote_asset in wallets and wallets[quote_asset] >= total_cost:
            # Deduct the total cost including fees from the quote currency balance
            wallets[quote_asset] -= total_cost
            # Add the appropriate amount of the base currency to the base currency wallet
            if base_asset in wallets:
                wallets[base_asset] += abs(amount)
            else:
                wallets[base_asset] = abs(amount)  # Initialize the base currency wallet if not present
            # Update fee balance
            fee = round(abs(amount) * price * fee_rate,8)
            if 'fees' in wallets:
                wallets['fees'] += fee
            else:
                wallets['fees'] = fee  # Initialize fee balance if not present
        else:
            print("Warning: Insufficient balance to execute the buy order.")
    elif action == 'sell':
        # Check if the base currency is present in the base currency wallet and the amount to sell is available
        if base_asset in wallets and wallets[base_asset] >= abs(amount):
            # Calculate the total proceeds from selling the asset after deducting fees
            total_proceeds = abs(amount) * price * (1 - fee_rate)
            # Add the total proceeds minus fees to the quote currency balance
            if quote_asset in wallets:
                wallets[quote_asset] += total_proceeds
            else:
                wallets[quote_asset] = total_proceeds  # Initialize quote currency balance if not present
            # Subtract the appropriate amount of the base currency from the base currency wallet
            wallets[base_asset] -= abs(amount)
            # Update fee balance
            fee = round(abs(amount) * price * fee_rate,8)
            if 'fees' in wallets:
                wallets['fees'] += fee
            else:
                wallets['fees'] = fee  # Initialize fee balance if not present
        else:
            print("Warning: Insufficient balance of the base currency to execute the sell order.")
    else:
        print("Invalid action. Please specify 'buy' or 'sell'.")

# Example usage:
wallets = {'USDT': 1000, 'TRX': 0}  # Initial wallets with 1000 USDT and 0 TRX
actions = ['buy', 'sell', 'buy', 'sell']
amounts = [50, -30, -20, 10]  # Long position, short position, short position, long position
asset = 'TRX/USDT'  # Asset pair (TRX/USDT)
price = 0.5  # Price of TRX
for action, amount in zip(actions, amounts):
    update_wallet(wallets, action, asset, amount, price)
    print(wallets)  # Output the updated wallets and fee balance


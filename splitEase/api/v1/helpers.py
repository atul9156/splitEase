from collections import defaultdict

from splitEase.models import Membership, Transaction, User


def simplify_balance(amount: int, users: list, shares: list, type: str, is_payee: bool) -> list:
    sign = -1 if is_payee else 1
    if type == "amount":
        total = amount
    elif type == "share":
        total = sum(shares)
    else:
        total = 100
    return [(user, sign * (amount * share) / total) for user, share in zip(users, shares)]


def calculate_balances(group):
    transactions = Transaction.objects.filter(group=group, is_deleted=False)

    # Create a defaultdict to store balances for each user
    balances_list = []

    for transaction in transactions:
        paid_by = transaction.paid_by
        shared_by = transaction.shared_by
        balances_list.extend(
            simplify_balance(
                amount=transaction.amount,
                users=paid_by.get("users", []),
                shares=paid_by.get("share", []),
                type=paid_by.get("type", "amount"),
                is_payee=True,
            )
        )
        balances_list.extend(
            simplify_balance(
                amount=transaction.amount,
                users=shared_by.get("users", []),
                shares=shared_by.get("share", []),
                type=shared_by.get("type", "amount"),
                is_payee=False,
            )
        )

    balances = defaultdict(int)
    for user, amount in balances_list:
        balances[user] += amount
    return balances


def group_balance(group):
    balances = calculate_balances(group)
    final_balances = [{"user": email, "balance": balance} for email, balance in balances.items()]

    return final_balances


def calculate_optimal_settlement(group):
    balances = calculate_balances(group)
    # Separate and sort users by those who are owed money (negative balances) and those who owe money (positive balances)
    owed = sorted([(user, abs(bal)) for user, bal in balances.items() if bal < 0], key=lambda x: x[1], reverse=True)
    owes = sorted([(user, bal) for user, bal in balances.items() if bal > 0], key=lambda x: x[1], reverse=True)

    transactions = []

    while owed and owes:
        owed_user, amount_owed = owed.pop(0)  # User who is owed the most
        owes_user, amount_owes = owes.pop(0)  # User who owes the most

        transaction_amount = min(amount_owed, amount_owes)
        transactions.append({"payer": owes_user, "payee": owed_user, "amount": transaction_amount})

        # Update balances
        new_amount_owed = amount_owed - transaction_amount
        new_amount_owes = amount_owes - transaction_amount

        # If the owed user is still owed money, add them back with the updated balance
        if new_amount_owed > 0:
            owed.insert(0, (owed_user, new_amount_owed))

        # If the owes user still owes money, add them back with the updated balance
        if new_amount_owes > 0:
            owes.insert(0, (owes_user, new_amount_owes))

    return transactions


def create_memberships(emails: set, group):
    for email in emails:
        user, _ = User.objects.get_or_create(email=email)
        membership, _ = Membership.objects.get_or_create(user=user, group=group)
        if membership.is_deleted:
            membership.is_deleted = False
            membership.save()

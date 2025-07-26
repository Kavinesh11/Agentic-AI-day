def calculate_budget(income, expenses):
    """
    Calculate the remaining budget after expenses.

    Parameters:
    income (float): Total income for the period.
    expenses (list of float): List of expenses for the period.

    Returns:
    float: Remaining budget after expenses.
    """
    total_expenses = sum(expenses)
    return income - total_expenses

def categorize_expenses(expenses):
    """
    Categorize expenses into different types.

    Parameters:
    expenses (list of dict): List of expenses where each expense is a dict with 'amount' and 'category'.

    Returns:
    dict: A dictionary with categories as keys and total amounts as values.
    """
    categorized = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        if category in categorized:
            categorized[category] += amount
        else:
            categorized[category] = amount
    return categorized

def suggest_budget(income, expenses):
    """
    Suggest a budget based on income and past expenses.

    Parameters:
    income (float): Total income for the period.
    expenses (list of float): List of past expenses for the period.

    Returns:
    dict: Suggested budget allocations.
    """
    remaining_budget = calculate_budget(income, expenses)
    suggested_allocation = {
        'savings': remaining_budget * 0.20,
        'essentials': remaining_budget * 0.50,
        'discretionary': remaining_budget * 0.30
    }
    return suggested_allocation
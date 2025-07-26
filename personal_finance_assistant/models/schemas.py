from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: int
    name: str
    email: str

class Transaction(BaseModel):
    id: int
    user_id: int
    amount: float
    date: str
    description: Optional[str] = None

class Budget(BaseModel):
    user_id: int
    total_amount: float
    spent_amount: float
    remaining_amount: float

class FinancialData(BaseModel):
    user: User
    transactions: List[Transaction]
    budget: Budget
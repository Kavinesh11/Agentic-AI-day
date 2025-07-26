"""
Google Wallet API integration tools for retrieving Generic Passes
"""
import json
import logging
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models.schemas import WalletPass, FinancialContext
from config.settings import settings

logger = logging.getLogger(__name__)


class WalletAPIClient:
    """Google Wallet API client for managing Generic Passes"""

    def __init__(self):
        self.credentials = None
        self.service = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Wallet API client with service account credentials"""
        try:
            if settings.wallet_service_account_file:
                self.credentials = Credentials.from_service_account_file(
                    settings.wallet_service_account_file,
                    scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
                )
            else:
                logger.warning(
                    "No service account file configured for Wallet API")
                return

            self.service = build('walletobjects', 'v1',
                                 credentials=self.credentials)
            logger.info("Wallet API client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Wallet API client: {e}")
            raise

    async def get_generic_passes(self, issuer_id: str, user_context: Optional[str] = None) -> List[WalletPass]:
        """
        Retrieve Generic Passes for a user from Google Wallet API
        
        Args:
            issuer_id: The Wallet API issuer ID
            user_context: Optional user context for filtering passes
            
        Returns:
            List of WalletPass objects
        """
        if not self.service:
            logger.warning("Wallet API service not initialized")
            return []

        try:
            # List generic objects (passes) for the issuer
            request = self.service.genericobject().list(issuerId=issuer_id)
            response = request.execute()

            passes = []
            if 'resources' in response:
                for resource in response['resources']:
                    wallet_pass = self._parse_generic_pass(resource)
                    if wallet_pass:
                        passes.append(wallet_pass)

            logger.info(f"Retrieved {len(passes)} wallet passes")
            return passes

        except HttpError as e:
            logger.error(f"HTTP error retrieving wallet passes: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving wallet passes: {e}")
            return []

    def _parse_generic_pass(self, pass_data: Dict[str, Any]) -> Optional[WalletPass]:
        """
        Parse raw Google Wallet pass data into WalletPass model
        
        Args:
            pass_data: Raw pass data from Google Wallet API
            
        Returns:
            WalletPass object or None if parsing fails
        """
        try:
            # Extract financial information from Generic Pass fields
            financial_data = self._extract_financial_info(pass_data)

            wallet_pass = WalletPass(
                pass_id=pass_data.get('id', ''),
                pass_type='generic',
                issuer_name=pass_data.get('issuerName', 'Unknown'),
                pass_data=financial_data,
                creation_date=self._parse_date(pass_data.get(
                    'validTimeInterval', {}).get('start')),
                expiration_date=self._parse_date(
                    pass_data.get('validTimeInterval', {}).get('end')),
                status=pass_data.get('state', 'ACTIVE').lower()
            )

            return wallet_pass

        except Exception as e:
            logger.error(f"Error parsing wallet pass: {e}")
            return None

    def _extract_financial_info(self, pass_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract financial information from Generic Pass fields
        
        Args:
            pass_data: Raw pass data from Google Wallet API
            
        Returns:
            Dictionary containing financial information
        """
        financial_info = {}

        # Parse header fields for financial data
        if 'header' in pass_data:
            header = pass_data['header']
            if 'firstValue' in header:
                financial_info['primary_amount'] = self._parse_amount(
                    header['firstValue'])
            if 'secondValue' in header:
                financial_info['secondary_amount'] = self._parse_amount(
                    header['secondValue'])

        # Parse text modules for additional financial context
        if 'textModulesData' in pass_data:
            for module in pass_data['textModulesData']:
                header = module.get('header', '').lower()
                body = module.get('body', '')

                if 'income' in header:
                    financial_info['monthly_income'] = self._extract_numeric_value(
                        body)
                elif 'expense' in header or 'spending' in header:
                    financial_info['monthly_expenses'] = self._extract_numeric_value(
                        body)
                elif 'subscription' in header:
                    financial_info['subscriptions'] = self._parse_subscription_data(
                        body)
                elif 'budget' in header:
                    financial_info['budget_info'] = self._parse_budget_data(
                        body)

        return financial_info

    def _parse_amount(self, amount_data: Dict[str, Any]) -> Optional[float]:
        """Parse amount from Google Wallet amount structure"""
        try:
            if isinstance(amount_data, dict) and 'currencyCode' in amount_data:
                return float(amount_data.get('units', 0))
            elif isinstance(amount_data, str):
                return self._extract_numeric_value(amount_data)
            return None
        except (ValueError, TypeError):
            return None

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text string"""
        import re
        try:
            # Remove currency symbols and extract numbers
            numbers = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
            if numbers:
                return float(numbers[0])
            return None
        except (ValueError, IndexError):
            return None

    def _parse_subscription_data(self, subscription_text: str) -> List[Dict[str, Any]]:
        """Parse subscription information from text"""
        # Simple implementation - in production, this would be more sophisticated
        subscriptions = []
        lines = subscription_text.split('\n')

        for line in lines:
            if '$' in line or 'monthly' in line.lower():
                amount = self._extract_numeric_value(line)
                if amount:
                    subscriptions.append({
                        'name': line.split('-')[0].strip() if '-' in line else 'Unknown Service',
                        'monthly_cost': amount,
                        'category': 'subscription'
                    })

        return subscriptions

    def _parse_budget_data(self, budget_text: str) -> Dict[str, float]:
        """Parse budget information from text"""
        budget_info = {}
        lines = budget_text.split('\n')

        for line in lines:
            if ':' in line:
                category, amount_text = line.split(':', 1)
                amount = self._extract_numeric_value(amount_text)
                if amount:
                    budget_info[category.strip().lower()] = amount

        return budget_info

    def _parse_date(self, date_string: Optional[str]):
        """Parse date string to datetime object"""
        if not date_string:
            return None

        try:
            from datetime import datetime
            # Handle ISO format dates from Google Wallet API
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

# Tool function for ADK integration


async def get_wallet_passes(issuer_id: str, user_context: Optional[str] = None) -> Dict[str, Any]:
    """
    ADK tool function to retrieve wallet passes
    
    Args:
        issuer_id: Google Wallet issuer ID
        user_context: Optional user context for filtering
        
    Returns:
        Dictionary containing wallet passes and financial context
    """
    client = WalletAPIClient()
    passes = await client.get_generic_passes(issuer_id, user_context)

    # Extract financial context from passes
    financial_context = FinancialContext()

    for wallet_pass in passes:
        pass_data = wallet_pass.pass_data

        # Aggregate financial information
        if 'monthly_income' in pass_data and pass_data['monthly_income']:
            financial_context.monthly_income = pass_data['monthly_income']

        if 'monthly_expenses' in pass_data and pass_data['monthly_expenses']:
            financial_context.current_expenses = pass_data['monthly_expenses']

        if 'subscriptions' in pass_data:
            financial_context.subscriptions.extend(pass_data['subscriptions'])

        if 'budget_info' in pass_data:
            financial_context.budget_categories.update(
                pass_data['budget_info'])

        # Add pass to context
        financial_context.wallet_passes.append(wallet_pass.dict())

    return {
        'passes': [pass_obj.dict() for pass_obj in passes],
        'financial_context': financial_context.dict(),
        'total_passes': len(passes)
    }

"""PaySetu: the universe's only payment app, modelled on Indian UPI apps.

Schema: app_schemas.md section 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from are.simulation.tool_utils import OperationType, app_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import type_check

from .common import (
    COD,
    BharatApp,
    BharatProtocol,
    dump_records,
    format_datetime,
    load_records,
    matches,
    page,
    parse_date,
    parse_datetime,
    to_dict,
)

UPI_DAILY_LIMIT = 100_000
REQUEST_VALIDITY = timedelta(days=7)
SOURCE_TYPES = ("bank_account", "credit_card")
CATEGORIES = ("food", "shopping", "travel", "health", "bills", "transfer", "refund", "other")


@dataclass
class PaymentSource:
    source_id: str
    type: str
    label: str
    masked_number: str
    upi_id: str | None = None
    balance: int = 0
    available_limit: int = 0
    is_default: bool = False


@dataclass
class Payee:
    payee_id: str
    name: str
    upi_id: str
    phone: str = ""


@dataclass
class Transaction:
    txn_id: str
    timestamp: str
    direction: str
    amount: int
    counterparty_name: str
    source_id: str
    category: str
    status: str = "success"
    counterparty_upi_id: str | None = None
    reference_app: str | None = None
    reference_id: str | None = None
    refund_of: str | None = None
    note: str = ""


@dataclass
class PaymentRequest:
    request_id: str
    direction: str
    counterparty_name: str
    counterparty_upi_id: str
    amount: int
    note: str
    created_at: str
    expires_at: str
    status: str = "pending"


class PaySetuApp(BharatApp):
    """
    PaySetu is a UPI payments app. It holds the user's linked bank accounts and credit cards,
    saved payees, the full transaction history, and money requests sent or received.

    Every other app that takes money charges PaySetu, so every order and booking has a matching
    transaction here. Refunds always go back to the source that paid.

    Notes:
        - Amounts are whole rupees.
        - Times are local (IST) in the format YYYY-MM-DD HH:MM:SS.
        - A payment source is named by its source_id, e.g. "PS-SRC-HDFC01". Use list_payment_sources
          to see sources, balances and which one is the default.
        - Money can be sent to people only from bank accounts, not from credit cards.
        - UPI transfers to people are limited to 100000 rupees per day in total.
    """

    def __init__(self, name: str | None = "PaySetu") -> None:
        super().__init__(name)
        self.sources: dict[str, PaymentSource] = {}
        self.payees: dict[str, Payee] = {}
        self.transactions: dict[str, Transaction] = {}
        self.requests: dict[str, PaymentRequest] = {}

    def get_implemented_protocols(self) -> list[Any]:
        return [BharatProtocol.PAYMENT]

    # State -----------------------------------------------------------------
    def get_state(self) -> dict[str, Any]:
        return {
            **self.base_state(),
            "sources": dump_records(self.sources),
            "payees": dump_records(self.payees),
            "transactions": dump_records(self.transactions),
            "requests": dump_records(self.requests),
        }

    def load_state(self, state_dict: dict[str, Any]) -> None:
        self.load_base_state(state_dict)
        self.sources = load_records(PaymentSource, state_dict.get("sources", {}))
        self.payees = load_records(Payee, state_dict.get("payees", {}))
        self.transactions = load_records(Transaction, state_dict.get("transactions", {}))
        self.requests = load_records(PaymentRequest, state_dict.get("requests", {}))
        defaults = [source for source in self.sources.values() if source.is_default]
        if self.sources and len(defaults) != 1:
            raise ValueError("PaySetu state must have exactly one default payment source")

    # Internal helpers --------------------------------------------------------
    def default_source(self) -> PaymentSource:
        for source in self.sources.values():
            if source.is_default:
                return source
        raise ValueError("No default payment source is set")

    def _source(self, source_id: str) -> PaymentSource:
        if source_id == COD:
            raise ValueError("Cash on delivery is not a PaySetu payment source")
        if source_id not in self.sources:
            raise ValueError(f"Payment source {source_id} does not exist")
        return self.sources[source_id]

    def _debit(self, source: PaymentSource, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be a positive number of rupees")
        if source.type == "bank_account":
            if source.balance < amount:
                raise ValueError(f"Insufficient balance in {source.label}: balance {source.balance}, needed {amount}")
            source.balance -= amount
        else:
            if source.available_limit < amount:
                raise ValueError(
                    f"Insufficient credit limit on {source.label}: available {source.available_limit}, needed {amount}"
                )
            source.available_limit -= amount

    def _credit(self, source: PaymentSource, amount: int) -> None:
        if source.type == "bank_account":
            source.balance += amount
        else:
            source.available_limit += amount

    def _peer_transfers_today(self) -> int:
        today = self.today()
        return sum(
            txn.amount
            for txn in self.transactions.values()
            if txn.direction == "debit"
            and txn.category == "transfer"
            and txn.status == "success"
            and parse_datetime(txn.timestamp).date() == today
        )

    def _check_peer_transfer(self, source: PaymentSource, amount: int) -> None:
        if source.type != "bank_account":
            raise ValueError("Money can be sent to people only from a bank account, not a credit card")
        if amount > UPI_DAILY_LIMIT or self._peer_transfers_today() + amount > UPI_DAILY_LIMIT:
            raise ValueError(f"UPI transfer limit of {UPI_DAILY_LIMIT} rupees per day would be exceeded")

    def _record(self, **fields: Any) -> Transaction:
        txn = Transaction(txn_id=self.next_id("PS-TXN", 5), timestamp=self.now_str(), **fields)
        self.transactions[txn.txn_id] = txn
        return txn

    def _expire_due_requests(self) -> None:
        now = self.now()
        for request in self.requests.values():
            if request.status == "pending" and parse_datetime(request.expires_at) <= now:
                request.status = "expired"

    # Called by other apps (not agent tools) --------------------------------------------
    def charge(
        self,
        amount: int,
        payment: str,
        merchant: str,
        category: str,
        reference_app: str,
        reference_id: str,
    ) -> str:
        source = self._source(payment)
        self._debit(source, amount)
        return self._record(
            direction="debit",
            amount=amount,
            counterparty_name=merchant,
            source_id=source.source_id,
            category=category,
            reference_app=reference_app,
            reference_id=reference_id,
        ).txn_id

    def refund(self, txn_id: str, amount: int) -> str:
        if txn_id not in self.transactions:
            raise ValueError(f"Transaction {txn_id} does not exist")
        original = self.transactions[txn_id]
        already = sum(t.amount for t in self.transactions.values() if t.refund_of == txn_id)
        if amount > original.amount - already:
            raise ValueError(f"Refund of {amount} exceeds the refundable amount of transaction {txn_id}")
        source = self._source(original.source_id)
        self._credit(source, amount)
        return self._record(
            direction="credit",
            amount=amount,
            counterparty_name=original.counterparty_name,
            source_id=source.source_id,
            category="refund",
            reference_app=original.reference_app,
            reference_id=original.reference_id,
            refund_of=txn_id,
        ).txn_id

    def credit_default_account(self, amount: int, counterparty_name: str, reference_app: str, reference_id: str) -> str:
        source = self.default_source()
        if source.type != "bank_account":
            raise ValueError("The default payment source must be a bank account to receive refunds")
        self._credit(source, amount)
        return self._record(
            direction="credit",
            amount=amount,
            counterparty_name=counterparty_name,
            source_id=source.source_id,
            category="refund",
            reference_app=reference_app,
            reference_id=reference_id,
        ).txn_id

    # Read tools --------------------------------------------------------------
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_payment_sources(self) -> list[dict[str, Any]]:
        """
        List the user's linked bank accounts and credit cards, with balance (bank accounts),
        available limit (credit cards) and which source is the default.
        :returns: list of payment sources
        """
        return [to_dict(source) for source in self.sources.values()]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_transactions(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        category: str | None = None,
        direction: str | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        List transactions, newest first, optionally filtered.
        :param start_date: only transactions on or after this date, format YYYY-MM-DD
        :param end_date: only transactions on or before this date, format YYYY-MM-DD
        :param category: one of food, shopping, travel, health, bills, transfer, refund, other
        :param direction: "debit" (money out) or "credit" (money in)
        :param query: text matched against the counterparty name, UPI ID and note
        :param offset: index of the first transaction to return
        :param limit: maximum number of transactions to return
        :returns: a page of transactions with the total count
        """
        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None
        selected = []
        for txn in self.transactions.values():
            day = parse_datetime(txn.timestamp).date()
            if start and day < start or end and day > end:
                continue
            if category and txn.category != category:
                continue
            if direction and txn.direction != direction:
                continue
            if not matches(query, txn.counterparty_name, txn.counterparty_upi_id, txn.note):
                continue
            selected.append(txn)
        selected.sort(key=lambda txn: (txn.timestamp, txn.txn_id), reverse=True)
        return page([to_dict(txn) for txn in selected], offset, limit)

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_transaction(self, txn_id: str) -> dict[str, Any]:
        """
        Get one transaction.
        :param txn_id: the transaction ID
        :returns: the transaction
        """
        if txn_id not in self.transactions:
            raise ValueError(f"Transaction {txn_id} does not exist")
        return to_dict(self.transactions[txn_id])

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_payees(self, query: str | None = None) -> list[dict[str, Any]]:
        """
        List saved payees (people the user pays).
        :param query: optional text matched against name, UPI ID and phone
        :returns: list of payees
        """
        return [
            to_dict(payee) for payee in self.payees.values() if matches(query, payee.name, payee.upi_id, payee.phone)
        ]

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def list_payment_requests(self, status: str | None = None, direction: str | None = None) -> list[dict[str, Any]]:
        """
        List money requests, newest first.
        :param status: one of pending, paid, declined, expired
        :param direction: "incoming" (someone asks the user for money) or "outgoing" (the user asked someone)
        :returns: list of money requests
        """
        self._expire_due_requests()
        selected = [
            request
            for request in self.requests.values()
            if (status is None or request.status == status) and (direction is None or request.direction == direction)
        ]
        selected.sort(key=lambda request: request.created_at, reverse=True)
        return [to_dict(request) for request in selected]

    # Write tools -----------------------------------------------------------------
    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def send_money(self, upi_id: str, amount: int, payment: str, note: str = "") -> str:
        """
        Send money to a person by UPI ID.
        :param upi_id: the recipient's UPI ID, e.g. "rohit.malhotra@paysetu"
        :param amount: amount in whole rupees
        :param payment: source_id of the bank account to pay from (credit cards cannot be used)
        :param note: optional note shown to the recipient
        :returns: the transaction ID
        """
        source = self._source(payment)
        self._check_peer_transfer(source, amount)
        payee = next((p for p in self.payees.values() if p.upi_id == upi_id), None)
        self._debit(source, amount)
        return self._record(
            direction="debit",
            amount=amount,
            counterparty_name=payee.name if payee else upi_id,
            counterparty_upi_id=upi_id,
            source_id=source.source_id,
            category="transfer",
            note=note,
        ).txn_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def request_money(self, upi_id: str, amount: int, note: str = "") -> str:
        """
        Ask a person to pay the user. The request expires after 7 days.
        :param upi_id: UPI ID of the person being asked
        :param amount: amount in whole rupees
        :param note: optional note explaining the request
        :returns: the request ID
        """
        if amount <= 0:
            raise ValueError("Amount must be a positive number of rupees")
        payee = next((p for p in self.payees.values() if p.upi_id == upi_id), None)
        now = self.now()
        request = PaymentRequest(
            request_id=self.next_id("PS-REQ"),
            direction="outgoing",
            counterparty_name=payee.name if payee else upi_id,
            counterparty_upi_id=upi_id,
            amount=amount,
            note=note,
            created_at=format_datetime(now),
            expires_at=format_datetime(now + REQUEST_VALIDITY),
        )
        self.requests[request.request_id] = request
        return request.request_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def pay_request(self, request_id: str, payment: str) -> str:
        """
        Pay an incoming money request.
        :param request_id: the request ID
        :param payment: source_id of the bank account to pay from (credit cards cannot be used)
        :returns: the transaction ID
        """
        self._expire_due_requests()
        request = self._pending_incoming(request_id)
        source = self._source(payment)
        self._check_peer_transfer(source, request.amount)
        self._debit(source, request.amount)
        request.status = "paid"
        return self._record(
            direction="debit",
            amount=request.amount,
            counterparty_name=request.counterparty_name,
            counterparty_upi_id=request.counterparty_upi_id,
            source_id=source.source_id,
            category="transfer",
            reference_app=self.name,
            reference_id=request.request_id,
            note=request.note,
        ).txn_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def decline_request(self, request_id: str) -> str:
        """
        Decline an incoming money request.
        :param request_id: the request ID
        :returns: the request ID
        """
        self._expire_due_requests()
        self._pending_incoming(request_id).status = "declined"
        return request_id

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_payee(self, name: str, upi_id: str, phone: str = "") -> str:
        """
        Save a new payee.
        :param name: the payee's name
        :param upi_id: the payee's UPI ID
        :param phone: optional phone number
        :returns: the payee ID
        """
        if any(p.upi_id == upi_id for p in self.payees.values()):
            raise ValueError(f"A payee with UPI ID {upi_id} already exists")
        payee = Payee(payee_id=self.next_id("PS-PAYEE"), name=name, upi_id=upi_id, phone=phone)
        self.payees[payee.payee_id] = payee
        return payee.payee_id

    def _pending_incoming(self, request_id: str) -> PaymentRequest:
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} does not exist")
        request = self.requests[request_id]
        if request.direction != "incoming":
            raise ValueError(f"Request {request_id} was sent by the user and cannot be paid or declined")
        if request.status != "pending":
            raise ValueError(f"Request {request_id} is {request.status}")
        return request

    # Environment events -------------------------------------------------------
    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def receive_money(self, from_name: str, from_upi_id: str, amount: int, note: str = "") -> str:
        """
        A person sends money to the user's default bank account.
        :param from_name: sender's name
        :param from_upi_id: sender's UPI ID
        :param amount: amount in whole rupees
        :param note: note from the sender
        :returns: the transaction ID
        """
        source = self.default_source()
        self._credit(source, amount)
        for request in self.requests.values():
            if (
                request.direction == "outgoing"
                and request.status == "pending"
                and request.counterparty_upi_id == from_upi_id
                and request.amount == amount
            ):
                request.status = "paid"
                break
        return self._record(
            direction="credit",
            amount=amount,
            counterparty_name=from_name,
            counterparty_upi_id=from_upi_id,
            source_id=source.source_id,
            category="transfer",
            note=note,
        ).txn_id

    @type_check
    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def receive_payment_request(self, from_name: str, from_upi_id: str, amount: int, note: str = "") -> str:
        """
        A person asks the user for money.
        :param from_name: requester's name
        :param from_upi_id: requester's UPI ID
        :param amount: amount in whole rupees
        :param note: note from the requester
        :returns: the request ID
        """
        now = self.now()
        request = PaymentRequest(
            request_id=self.next_id("PS-REQ"),
            direction="incoming",
            counterparty_name=from_name,
            counterparty_upi_id=from_upi_id,
            amount=amount,
            note=note,
            created_at=format_datetime(now),
            expires_at=format_datetime(now + REQUEST_VALIDITY),
        )
        self.requests[request.request_id] = request
        return request.request_id

    @env_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def expire_requests(self) -> list[str]:
        """
        Mark pending requests whose expiry time has passed as expired.
        :returns: IDs of requests that expired
        """
        pending = {r.request_id for r in self.requests.values() if r.status == "pending"}
        self._expire_due_requests()
        return sorted(r for r in pending if self.requests[r].status == "expired")

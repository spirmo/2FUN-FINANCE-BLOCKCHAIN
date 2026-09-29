# 2FUN Financial + Blockchain Core
# Domain Ownership & Boundary Contract
## Architecture Contract — 2FUN-FIN-ARCH-004

**Status:** FOUNDATION — ARCHITECTURAL CONTRACT
**Version:** 1.0
**Scope:** Financial + Blockchain Core
**Repository:** 2FUN-FINANCE-BLOCKCHAIN

---

## 1. Purpose

This contract defines the ownership, responsibility, state boundaries,
and communication boundaries of the major domains of the
2FUN Financial + Blockchain Core.

The purpose is to prevent:

- duplicated authoritative ledgers
- parallel value calculation engines
- hidden cross-domain dependencies
- uncontrolled state mutation
- circular ownership
- direct domain-to-domain coupling

The architecture is modular and contract-driven.

---

## 2. Core Principle

Each responsibility has one authoritative owner.

A domain may consume another domain's published contract, event,
request, or service interface, but must not silently take ownership
of another domain's authoritative state.

No domain may create a parallel authoritative implementation of
another domain's core responsibility.

---

## 3. Value Domain / UVI

### Ownership

UVI owns the universal lifecycle of internal value.

### Responsibilities

- Value Types
- Value Calculation
- Value Validation
- Value Rules
- Value Conversion
- Value Transactions
- Value Ledger
- Value Balance Calculation
- Value State
- Value History
- Conversion Records
- Financial Value Events

### Authoritative State

UVI Value State and UVI Value Ledger.

### Operations

- Calculate
- Validate
- Convert
- Record
- Balance
- Value State Transition

### Boundary

UVI does not own:

- Fiat Accounting
- Banking Accounts
- Blockchain State
- Network Consensus
- Smart Contract State
- Regulatory Policy

---

## 4. Accounting Domain

### Ownership

Accounting owns the authoritative accounting representation of
financial activity.

### Responsibilities

- General Ledger
- Subledgers
- Double-Entry Accounting
- Chart of Accounts
- Journal Entries
- Debits
- Credits
- Accounts Receivable
- Accounts Payable
- Accounting Periods
- Financial Statements
- Accounting Reconciliation

### Authoritative State

Accounting Ledger and Accounting Records.

### Boundary

Accounting does not replace:

- UVI Value Ledger
- Financial Account State
- Blockchain State

A financial operation may produce accounting effects, but accounting
does not become the owner of the originating operational state.

---

## 5. Fiat Domain

### Ownership

Fiat Domain owns fiat-specific monetary representations and
fiat lifecycle rules within the system.

### Responsibilities

- Fiat Currency Definitions
- Fiat Balances
- Fiat Funding State
- Fiat Deposits
- Fiat Withdrawals
- Fiat Payment Rails
- Fiat Settlement Interfaces
- Fiat Currency Conversion Interfaces

### Supported Examples

- EUR
- USD
- GBP
- Other supported fiat currencies

### Boundary

Fiat Domain does not become the owner of:

- UVI Value Calculation
- Accounting Ledger
- Blockchain Consensus
- Blockchain State

---

## 6. Financial Services Domain

### Ownership

Financial Services owns financial products and operational
financial services.

### Responsibilities

- Financial Accounts
- Deposits
- Withdrawals
- Transfers
- Credit
- Loans
- Borrowing
- Financial Products
- Customer Financial Operations

### Boundary

Financial Services requests value operations and settlement,
but does not directly mutate another domain's authoritative state.

---

## 7. Payments Domain

### Ownership

Payments owns payment orchestration and payment lifecycle.

### Responsibilities

- Payment Requests
- Payment Authorization
- Payment Routing
- Payment Processing
- Payment Status
- Payment Reversal
- Payment Completion

### Boundary

Payments does not directly own:

- UVI Ledger
- Accounting Ledger
- Blockchain State

Payments coordinates those domains through defined contracts.

---

## 8. Exchange Domain

### Ownership

Exchange owns exchange-market operations.

### Responsibilities

- Trading Requests
- Orders
- Matching
- Market State
- Trading Fees
- Trade Execution
- Exchange Settlement Requests

### Boundary

Exchange does not independently calculate authoritative value
conversion rules belonging to UVI.

Exchange uses approved conversion, pricing, and settlement
interfaces.

---

## 9. Treasury Domain

### Ownership

Treasury owns institutional liquidity and treasury operations.

### Responsibilities

- Treasury Accounts
- Reserves
- Liquidity Allocation
- Funding
- Treasury Transfers
- Reserve Management
- Treasury Risk Controls

### Boundary

Treasury cannot directly bypass accounting, value, payment,
or settlement contracts.

---

## 10. Lending / Credit Domain

### Ownership

Lending and Credit owns credit lifecycle and lending operations.

### Responsibilities

- Loan Origination
- Credit Accounts
- Credit Limits
- Collateral References
- Interest Calculation
- Repayment Schedules
- Loan State
- Default State
- Lending Settlement Requests

### Boundary

Credit state is owned by the Lending/Credit domain.

Accounting effects are recorded by Accounting.

Value effects are recorded by UVI where applicable.

Settlement is handled by Settlement.

---

## 11. Liquidity Domain

### Ownership

Liquidity owns liquidity-pool and liquidity-management operations.

### Responsibilities

- Liquidity Pools
- Liquidity Positions
- Liquidity Allocation
- Liquidity Provision
- Liquidity Withdrawal
- Pool Accounting References
- Liquidity Settlement Requests

### Boundary

Liquidity does not create a parallel value engine or authoritative
Blockchain State.

---

## 12. Settlement Domain

### Ownership

Settlement owns the lifecycle of settling an approved financial
operation.

### Responsibilities

- Settlement Decision
- Settlement Request
- Internal Settlement
- External Settlement
- Settlement Status
- Confirmation
- Reconciliation Reference
- Settlement Record

### Settlement Types

1. Internal Settlement
2. Fiat Settlement
3. On-chain Settlement
4. Cross-system Settlement

### Boundary

Settlement does not independently redefine:

- Value
- Accounting
- Blockchain State

Settlement coordinates those domains.

---

## 13. Blockchain Domain

### Ownership

Blockchain owns decentralized network and on-chain state.

### Responsibilities

- Blockchain Core
- Blocks
- On-chain Transactions
- Blockchain State
- Transaction Execution
- Network
- Peer-to-Peer Communication
- Consensus
- Validators
- Finality
- Wallet Infrastructure
- Key Management Interfaces
- Smart Contracts
- Bridges
- On-chain Settlement

### Authoritative State

Blockchain State.

### Boundary

Blockchain does not own:

- UVI Value Calculation
- Fiat Accounting
- General Ledger
- Financial Account State
- Banking Product State

Blockchain validates and records operations according to
blockchain rules after receiving an authorized request.

---

## 14. DeFi Domain

### Ownership

DeFi owns decentralized financial protocols and their operational
interfaces.

### Responsibilities

- DEX
- Liquidity Protocols
- Staking Protocols
- Lending Protocols
- Borrowing Protocols
- Yield Mechanisms
- DeFi Smart Contract Interfaces

### Boundary

DeFi protocol state that exists on-chain is ultimately represented
by Blockchain State.

DeFi must not create a parallel authoritative blockchain state.

---

## 15. Compliance / Regulatory Domain

### Ownership

Compliance owns regulatory and policy enforcement workflows.

### Responsibilities

- KYC Interfaces
- AML Controls
- Transaction Monitoring
- Risk Rules
- Sanctions Screening Interfaces
- Compliance Decisions
- Regulatory Records
- Audit Requirements

### Boundary

Compliance may authorize, reject, restrict, or flag operations
according to applicable rules.

Compliance does not become the owner of:

- UVI Ledger
- Accounting Ledger
- Blockchain State
- Financial Account State

---

## 16. Ledger Separation

The following are distinct authoritative states:

### UVI Ledger

Authoritative for internal value changes.

### Accounting Ledger

Authoritative for accounting representation.

### Financial Account State

Authoritative for financial service account state.

### Blockchain State

Authoritative for on-chain state.

These states may reference one another through immutable identifiers,
but must not silently overwrite one another.

---

## 17. Settlement Boundary

The standard settlement flow is:

Financial Operation
        |
        v
Validation
        |
        v
UVI / Financial Processing
        |
        v
Settlement Decision
        |
        +----------------------+
        |                      |
        v                      v
Internal Settlement       On-chain Settlement
        |                      |
        |                      v
        |               Blockchain Gateway
        |                      |
        |                      v
        |                  Blockchain
        |                      |
        |                      v
        |                  Confirmation
        |                      |
        +----------+-----------+
                   |
                   v
           Settlement Record
                   |
                   v
             Reconciliation

---

## 18. Blockchain Gateway

The Blockchain Gateway is the controlled boundary between
Financial Operations / Settlement and Blockchain infrastructure.

The Gateway may:

- submit authorized transactions
- query transaction status
- request confirmation
- return transaction identifiers
- return blockchain confirmation data

The Gateway must not:

- calculate UVI value
- own accounting records
- redefine financial products
- silently mutate financial balances

---

## 19. Accounting Boundary

Financial operations may generate accounting effects.

The standard relationship is:

Financial Operation
        |
        +------> Operational State
        |
        +------> Accounting Event
                       |
                       v
                Accounting Ledger

Accounting does not replace the originating operational state.

---

## 20. Event and Contract Principle

Cross-domain communication must use explicit:

- Requests
- Responses
- Events
- Service Contracts
- Interfaces

Hidden direct dependencies between domain internals are prohibited.

A domain may depend on another domain's public contract,
but not on undocumented internal implementation details.

---

## 21. State Mutation Principle

A domain may directly mutate only state for which it is the
authoritative owner.

External domains must request state changes through the owning
domain's contract.

This rule applies to:

- Value
- Accounting
- Fiat
- Financial Accounts
- Payments
- Exchange
- Treasury
- Credit
- Liquidity
- Settlement
- Blockchain
- DeFi
- Compliance

---

## 22. 2FUNC Boundary

2FUNC is an ecosystem financial asset.

Its internal value lifecycle may pass through:

POINT
  |
  v
SHIR
  |
  v
ΣSHIR
  |
  v
2FUNC

The internal lifecycle is handled through UVI and Financial Core
contracts.

The on-chain representation of 2FUNC is owned by the Blockchain
Domain.

The internal and on-chain representations must remain traceable
through explicit transaction and settlement references.

---

## 23. Preview vs Execution

A preview operation:

- calculates
- validates eligibility
- returns a projection

A preview operation must NOT:

- mutate a ledger
- mutate a balance
- create a financial transaction
- create a blockchain transaction
- change blockchain state

An explicit execution request is required for actual mutation.

---

## 24. No Parallel Authority

The following are prohibited:

- second UVI calculation engine
- second authoritative Value Ledger
- second authoritative Accounting Ledger
- second authoritative Blockchain State
- hidden balance database that contradicts the owning ledger
- duplicated conversion rules outside the authoritative conversion layer

Adapters and caches may exist, but they are not authoritative.

---

## 25. Non-Destructive Architecture

Existing implementations must not be destructively deleted during
migration.

Migration follows:

Archive
  ->
Integrate
  ->
Validate
  ->
Switch Runtime Ownership
  ->
Cleanup Only When Explicitly Approved

Historical implementations remain recoverable.

---

## 26. Architectural Relationship

The resulting architecture is:

2FUN-OS
    |
    v
Financial + Blockchain Interfaces
    |
    v
2FUN Financial + Blockchain Core
    |
    +--> Value / UVI
    |
    +--> Accounting
    |
    +--> Fiat
    |
    +--> Financial Services
    |
    +--> Payments
    |
    +--> Exchange
    |
    +--> Treasury
    |
    +--> Lending / Credit
    |
    +--> Liquidity
    |
    +--> Settlement
    |
    +--> Blockchain
    |
    +--> DeFi
    |
    +--> Compliance / Regulatory

---

## 27. Architectural Rule

No implementation may be added to the Financial + Blockchain Core
unless its domain ownership and boundary are identifiable under
this contract or under a versioned extension of this contract.

---

## 28. Versioning

This contract is versioned architecture.

Changes to:

- domain ownership
- authoritative state
- ledger ownership
- settlement boundaries
- UVI responsibility
- blockchain responsibility

require a new contract version or an explicit architecture amendment.

---

## 29. Status

`2FUN-FIN-ARCH-004`

FOUNDATION — ARCHITECTURAL CONTRACT

This contract establishes domain ownership before implementation.

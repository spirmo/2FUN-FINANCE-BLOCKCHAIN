# 2FUN / توفان
# Unified Financial & Blockchain Architecture
## 2FUN Financial Core — Architecture Snapshot v1.0

**Status:** ARCHITECTURE LOCKED  
**Version:** 1.0  
**Architecture ID:** 2FUN-FIN-ARCH-005  
**Scope:** Financial Core + UVI + Finance + Blockchain  
**Principle:** One Architecture — One Authority per State

---

# 1. PURPOSE

این سند، سند مادر معماری شاخه مالی و بلاکچین 2FUN است.

هدف، ایجاد یک معماری یکپارچه، ماژولار و قابل توسعه برای تمام عملیات مالی متمرکز و غیرمتمرکز شامل:

- Value
- Calculation
- Conversion
- Accounting
- Accounts
- Payments
- Deposits
- Withdrawals
- Transfers
- Clearing
- Settlement
- Treasury
- Exchange
- Lending
- Borrowing
- Liquidity
- Staking
- CeFi
- DeFi
- Wallet
- Blockchain
- Smart Contracts
- On-chain Settlement

است.

این معماری باید از ایجاد موتورهای موازی برای محاسبه یا ثبت یک نوع ارزش جلوگیری کند.

---

# 2. ARCHITECTURAL PRINCIPLE

اصل مرکزی:

> ONE FINANCIAL ARCHITECTURE — ONE AUTHORITATIVE OWNER FOR EACH STATE

هر State (وضعیت) فقط یک مالک معتبر دارد.

هیچ ماژولی نباید مالکیت پنهان یا موازی یک State را ایجاد کند.

---

# 3. GLOBAL ARCHITECTURE

```text
2FUN-OS
   │
   ▼
Financial Interfaces / Events / Requests
   │
   ▼
2FUN Financial Core
   │
   ├── Universal Value Infrastructure (UVI)
   │
   ├── Accounting
   │
   ├── Financial Accounts
   │
   ├── Payments
   │
   ├── Exchange
   │
   ├── Treasury
   │
   ├── Lending / Credit
   │
   ├── Liquidity
   │
   ├── Settlement
   │
   ├── CeFi
   │
   └── DeFi
   │
   ▼
Settlement Layer
   │
   ├── Internal Settlement
   │
   └── Blockchain Settlement
           │
           ▼
      Blockchain Infrastructure
4. UNIVERSAL VALUE INFRASTRUCTURE — UVI
UVI زیرساخت مرکزی ارزش در Financial Core است.
UVI مسئول:
Value Types
Value Validation
Value Calculation
Value Rules
Value Conversion
Value Transactions
Value Ledger
Balance Calculation
Value State
Value History
Conversion Records
Financial Value Events
است.
UVI نباید با Accounting یا Blockchain یک State مشترک را به‌صورت موازی مالک شود.
5. VALUE LIFECYCLE
چرخه اصلی ارزش:
Value Creation
      ↓
Validation
      ↓
Calculation
      ↓
Conversion
      ↓
Ledger
      ↓
Balance
      ↓
Transaction
      ↓
Financial Operation
      ↓
Settlement
      ↓
Internal / On-chain
6. 2FUN VALUE HIERARCHY
ساختار فعلی ارزش:
POINT
  ↓
SHIR
  ↓
ΣSHIR
  ↓
2FUNC
نسبت‌های قفل‌شده:
1000 POINT = 1 SHIR

10 SHIR = 1 ΣSHIR

2 ΣSHIR = 1 2FUNC

20000 POINT = 1 2FUNC
این نسبت‌ها بخشی از معماری Value Layer هستند.
7. 2FUNC BOUNDARY
2FUNC دارایی نهایی اکوسیستم در این سلسله‌مراتب است.
UVI مسئول چرخه داخلی ارزش 2FUNC است.
Blockchain مسئول:
On-chain Ownership
On-chain Transactions
Network State
Verification
Consensus
Smart Contract State
است.
بنابراین:
UVI
Internal 2FUNC Lifecycle
        │
        ▼
Financial Operation
        │
        ▼
Settlement Decision
        │
        ▼
Blockchain Gateway
        │
        ▼
Blockchain
On-chain 2FUNC State
Blockchain موتور محاسبه ارزش داخلی 2FUNC نیست.
8. CONVERSION ARCHITECTURE
تمام Conversionها باید از Conversion Layer عبور کنند.
هر Conversion باید حداقل شامل:
Source Value
Destination Value
Rate
Rule ID
Rule Version
Effective Date
Limits
Fees
Eligibility
Context
باشد.
Conversion نباید بدون ثبت قابل ردیابی انجام شود.
9. PREVIEW VS EXECUTION
دو حالت کاملاً جدا هستند.
Preview
Preview فقط:
Calculation
Validation
Simulation
است.
Preview نباید:
Ledger را تغییر دهد
Balance را تغییر دهد
Transaction ایجاد کند
Blockchain Transaction ایجاد کند
State را Mutation کند
Explicit Execution
پس از درخواست صریح کاربر:
Validation
   ↓
Conversion
   ↓
Source Ledger Entry
   ↓
Destination Ledger Entry
   ↓
Balance Recalculation
   ↓
Conversion Reference
هیچ Conversion واقعی نباید صرفاً به‌دلیل نمایش Preview اجرا شود.
10. ACCOUNTING DOMAIN
Accounting مالک Accounting State است.
وظایف:
Journal
Debit
Credit
Accounting Entries
Accounting Balances
Financial Reporting
Reconciliation
Accounting نباید جایگزین UVI Value Ledger شود.
11. FINANCIAL ACCOUNT DOMAIN
Financial Accounts مسئول:
Account
Available Balance
Pending Balance
Locked Balance
Reserved Balance
Frozen Balance
Account Limits
Account Status
هستند.
Account State با UVI Ledger یکی نیست.
12. FIAT DOMAIN
Fiat Operations می‌تواند شامل:
Fiat Deposit
Fiat Withdrawal
Fiat Transfer
Fiat Conversion
Payment Rail Integration
Banking Integration
باشد.
Fiat State باید مالک مشخص و مستقل داشته باشد.
13. PAYMENTS
Payment Layer مسئول:
Payment Request
Authorization
Routing
Payment Execution
Payment Status
Payment Reversal
Payment Settlement
است.
Payment نباید مستقیماً Blockchain State را تغییر دهد.
14. EXCHANGE
Exchange Layer مسئول:
Market
Order
Matching
Quote
Trade
Fee
Settlement Request
است.
Exchange نباید مالک مستقل Value Ledger باشد.
15. TREASURY
Treasury مسئول مدیریت منابع مالی در سطح Financial Core است.
شامل:
Reserves
Liquidity Allocation
Treasury Accounts
Internal Transfers
Risk Limits
Treasury Settlement
است.
16. LENDING / CREDIT
Credit Layer شامل:
Loan
Borrowing
Repayment
Interest
Collateral
Credit Limits
Liquidation
Default State
است.
محاسبات ارزش باید از UVI استفاده کنند و Stateهای مالی در مالک مربوطه ثبت شوند.
17. LIQUIDITY
Liquidity Layer مسئول:
Liquidity Pools
Liquidity Provision
Liquidity Allocation
Pool Accounting
Liquidity Settlement
است.
18. SETTLEMENT
Settlement مسئول نهایی‌سازی عملیات مالی است.
دو مسیر اصلی:
Internal Settlement
        OR
Blockchain Settlement
هیچ Internal Transaction الزاماً On-chain نمی‌شود.
19. CeFi
CeFi (مالی متمرکز) می‌تواند شامل:
Accounts
Deposits
Withdrawals
Transfers
Clearing
Treasury
Exchange
Lending
Settlement
باشد.
CeFi باید از همان Financial Core و UVI استفاده کند.
20. DeFi
DeFi (مالی غیرمتمرکز) می‌تواند شامل:
Wallets
Staking
Liquidity
Lending
Borrowing
DEX
Smart Contracts
On-chain Settlement
باشد.
DeFi نباید یک Value Calculation Engine موازی ایجاد کند.
21. BLOCKCHAIN DOMAIN
Blockchain Infrastructure مالک:
Network
Consensus
Validators
Wallet Infrastructure
Addresses
Key Infrastructure
Smart Contracts
On-chain Transactions
Blockchain State
Bridges
On-chain Settlement
است.
22. CONSENSUS / VALIDATORS
Consensus Layer مسئول اعتبارسنجی وضعیت شبکه است.
Validator مسئول:
Transaction Validation
Block Validation
Consensus Participation
Network State Verification
است.
قوانین Validator باید نسخه‌پذیر و قابل Governance باشند.
23. WALLET
Wallet Infrastructure مسئول:
Address
Key Reference
Signing
Transaction Construction
Transaction Broadcast
Transaction Status
است.
کلید خصوصی نباید توسط Financial Core به‌صورت مستقیم مدیریت یا منتشر شود.
24. SMART CONTRACTS
Smart Contract Layer مسئول:
Contract Execution
Contract State
Contract Events
Contract Transactions
است.
Smart Contract نباید خارج از قراردادهای تعریف‌شده مالکیت پنهان روی UVI ایجاد کند.
25. BLOCKCHAIN GATEWAY
Blockchain Gateway مرز بین Financial Core و Blockchain است.
Financial Operation
       ↓
UVI Validation
       ↓
UVI Transaction
       ↓
Settlement Request
       ↓
Blockchain Gateway
       ↓
Blockchain Transaction
       ↓
Confirmation
       ↓
Settlement Record
Financial Core نباید مستقیماً به جزئیات داخلی Blockchain وابسته شود.
26. LEDGER SEPARATION
چهار State مهم از یکدیگر جدا هستند:
UVI Ledger
    ≠
Accounting Ledger
    ≠
Financial Account State
    ≠
Blockchain State
هرکدام مالک مستقل دارند.
هیچ Ledger موازی برای همان State مجاز نیست.
27. STATE SEPARATION
مالکیت State:
State
Authoritative Owner
Value State
UVI
Value Ledger
UVI
Accounting State
Accounting
Financial Account State
Financial Accounts
Payment State
Payments
Exchange State
Exchange
Treasury State
Treasury
Credit State
Lending/Credit
Liquidity State
Liquidity
Settlement State
Settlement
Blockchain State
Blockchain
28. TRANSACTION ARCHITECTURE
Transaction باید دارای:
Unique ID
Source
Destination
Value
Amount
Unit
Type
Timestamp
Status
Metadata
Reference
Idempotency Reference
باشد.
Transactionها باید قابل ردیابی باشند.
29. EVENT ARCHITECTURE
ماژول‌ها باید از طریق:
Events
Contracts
APIs
Service Interfaces
با یکدیگر ارتباط داشته باشند.
Hidden Direct Dependency ممنوع است.
نمونه:
Financial Event
      ↓
Financial Core
      ↓
UVI
      ↓
Operation
      ↓
Settlement Event
      ↓
Internal / Blockchain
30. PREVIEW / EXECUTION RULE
هیچ Preview نباید Mutation ایجاد کند.
Preview
= Read / Calculate / Simulate

Execution
= Validate / Mutate / Record / Settle
این مرز برای تمام عملیات مالی الزامی است.
31. FINANCIAL OPERATION MODEL
هر عملیات مالی باید دارای چرخه:
Request
 ↓
Validation
 ↓
Authorization
 ↓
Calculation
 ↓
Operation
 ↓
Ledger / State Mutation
 ↓
Settlement
 ↓
Confirmation
 ↓
Audit / History
باشد.
32. INTERNAL VS ON-CHAIN
Internal Transaction:
User
 ↓
Financial Core
 ↓
UVI
 ↓
Internal Ledger
 ↓
Internal Settlement
On-chain Transaction:
User
 ↓
Financial Core
 ↓
UVI
 ↓
Settlement Decision
 ↓
Blockchain Gateway
 ↓
Blockchain
 ↓
Confirmation
 ↓
Settlement Record
این دو مسیر نباید با یکدیگر مخلوط شوند.
33. COMPLIANCE / REGULATORY BOUNDARY
Compliance Layer باید به‌صورت مستقل قابل توسعه باشد.
شامل:
KYC
AML
Transaction Monitoring
Limits
Risk Controls
Regulatory Reporting
است.
قوانین حقوقی و مقرراتی باید قابل Versioning باشند.
34. SECURITY BOUNDARY
Security باید در تمام لایه‌ها اعمال شود.
اصول:
Least Privilege
Authentication
Authorization
Key Isolation
Transaction Signing
Replay Protection
Idempotency
Auditability
Secure Secrets Handling
35. RECONCILIATION
Reconciliation (تطبیق) باید بتواند Stateهای زیر را با یکدیگر تطبیق دهد:
UVI
Accounting
Financial Accounts
Settlement
Blockchain
Reconciliation نباید مالک State جدیدی ایجاد کند.
36. MODULARITY
هر Domain باید مستقل و قابل توسعه باشد.
ساختار مفهومی:
financial_core/
├── uvi/
├── accounting/
├── accounts/
├── payments/
├── exchange/
├── treasury/
├── lending/
├── liquidity/
├── settlement/
├── defi/
├── cefi/
├── blockchain/
├── wallet/
├── smart_contracts/
└── compliance/
ماژول‌ها باید از طریق Contract و Interface به یکدیگر متصل شوند.
37. REPOSITORY BOUNDARY
2FUN-OS مالک اکوسیستم است.
2FUN-FINANCE-BLOCKCHAIN مالک Financial Core و زیرساخت مالی/بلاکچین تخصصی است.
مرز:
2FUN-OS
     ↓
Financial Interface / Events
     ↓
2FUN-FINANCE-BLOCKCHAIN
نباید کل 2FUN-OS بدون نیاز در Repository مالی کپی شود.
38. MIGRATION PRINCIPLE
هر انتقال معماری باید:
Archive
   ↓
Integrate
   ↓
Validate
   ↓
Switch Runtime Ownership
   ↓
Cleanup
باشد.
اصل:
ARCHIVE, NEVER DELETE
حفظ تاریخچه و قابلیت بازیابی الزامی است.
39. VERSIONING
هر تغییر بنیادی در معماری باید:
Version
Change Record
Effective Date
Architecture Snapshot
داشته باشد.
تغییر نسبت‌های Value یا مالکیت State بدون Snapshot جدید مجاز نیست.
40. ARCHITECTURAL AUTHORITY
این سند مرجع مادر معماری Financial Core است.
سندهای تخصصی آینده باید با این Architecture Contract سازگار باشند.
در صورت تعارض، Architecture Snapshot نسخه معتبر معماری را مشخص می‌کند.
41. IMPLEMENTATION RULE
پیاده‌سازی باید تدریجی و ماژولار باشد.
ترتیب پیشنهادی:
Architecture
   ↓
Contracts
   ↓
Core Interfaces
   ↓
UVI Integration
   ↓
Ledger / Transactions
   ↓
Financial Operations
   ↓
Settlement
   ↓
Blockchain Gateway
   ↓
Blockchain Infrastructure
   ↓
Advanced DeFi / CeFi
هیچ قابلیت جدیدی نباید یک Value Engine یا Ledger موازی ایجاد کند.
42. FINAL ARCHITECTURE PRINCIPLE
معماری نهایی:
2FUN-OS
    │
    ▼
2FUN FINANCIAL CORE
    │
    ├── UVI
    │
    ├── Accounting
    ├── Accounts
    ├── Payments
    ├── Exchange
    ├── Treasury
    ├── Lending
    ├── Liquidity
    ├── CeFi
    └── DeFi
    │
    ▼
Settlement
    │
    ├── Internal
    │
    └── Blockchain Gateway
             │
             ▼
        Blockchain
اصل نهایی:
ONE ARCHITECTURE
ONE VALUE AUTHORITY
ONE AUTHORITATIVE OWNER PER STATE
NO PARALLEL VALUE ENGINE
NO PARALLEL LEDGER
EXPLICIT EXECUTION
TRACEABLE SETTLEMENT
MODULAR FINANCIAL CORE
43. LOCK
Architecture ID: 2FUN-FIN-ARCH-005
Document: Unified Financial & Blockchain Architecture
Version: 1.0
Status: ARCHITECTURE LOCKED
این سند مرجع مادر معماری Financial Core، UVI، Financial Operations و Blockchain است.
هر تغییر بنیادی باید با نسخه جدید Architecture Snapshot انجام شود.

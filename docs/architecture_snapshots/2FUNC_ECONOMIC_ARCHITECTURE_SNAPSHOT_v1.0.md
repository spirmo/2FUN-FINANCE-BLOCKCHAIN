# 2FUNC Economic Architecture Snapshot v1.0

## 2FUN / توفان
## Unified Value, Points, Settlement and Token Economics

- Document: 2FUNC Economic Architecture Snapshot
- Version: 1.0
- Status: Architecture Snapshot
- Purpose: Establish the economic design decisions and implementation boundaries
- Primary Asset: 2FUNC
- Calculation Engine: UVI
- Reference Value Unit: Drik (دریک)
- Ecosystem: 2FUN
- Scope: POINT, SHIR, ΣSHIR, 2FUNC, Drik, Drika, reward valuation, settlement, issuance and economic history

---

# 1. Purpose and Scope

This document records the economic architecture decisions established for 2FUN and 2FUNC.

It defines the relationships between activity points, progression, value-based rewards, settlement, the six principal units, and the eventual blockchain asset.

This snapshot is the reference for subsequent implementation planning.

It does not, by itself, authorize deployment, minting, token issuance, or changes to an existing smart contract.

Unresolved formulas and policies must remain explicitly unresolved until formally decided.

## 1.1 Core Architecture Principles

1. POINT is the base activity and progression score.
2. The value-based reward amount is distinct from the base score.
3. POINT is not a directly spendable economic asset.
4. Economic assets are used for eligible in-ecosystem expenditures.
5. UVI calculates value-based rewards and settlement amounts.
6. Settlement must not erase a user's historical base-point progression.
7. A valid activity must be validated before points are awarded.
8. Proven fraud requires a recorded correction of the affected base and value-based rewards.
9. Every settlement must be traceable and protected against duplicate execution.
10. 2FUNC issuance must comply with the supply cap and the applicable issuance policy.
11. The central EventBus communicates events between system components.
12. Historical records must be preserved. Follow the principle:
    **Archive, Never Delete.**

---

# 2. The Six Principal Units

The economic architecture recognizes six principal units.

| No. | Unit | Persian Name | Principal Role |
|---|---|---|---|
| 1 | POINT | پوینت | Base activity score and progression |
| 2 | SHIR | شیر | Intermediate value-computation unit |
| 3 | ΣSHIR | تن شیر | Intermediate value-computation unit |
| 4 | 2FUNC | توفان سی | Principal intended blockchain coin |
| 5 | Drik | دریک | Reference value unit |
| 6 | Drika | دریکا | Value asset and automatic settlement destination |

The exact economic and technical interfaces between all six units must be implemented through consistent central rules rather than duplicated conversion formulas across independent modules.

POINT is a score, not one of the spendable economic assets.

The five value assets available for in-ecosystem economic use are:

- Drika
- SHIR
- ΣSHIR
- 2FUNC
- Drik

2FUNC is the principal intended blockchain coin. SHIR, ΣSHIR, Drik and Drika must retain their defined roles and must not be silently treated as interchangeable with POINT.

The implementation must not invent additional conversion guarantees beyond the ratios and rules explicitly established in this document or subsequently approved.

---

# 3. POINT Semantics

## 3.1 Canonical Meaning

Whenever POINT is mentioned in 2FUN economic discussions, the default meaning is:

**Base POINT — امتیاز پایه**

Unless explicitly qualified, POINT means base points, not value points, settlement units, or a blockchain token.

## 3.2 Base Points

Technical field:

`base_points`

Purpose:

- Measure valid user activity.
- Determine progression and level eligibility.
- Support rank and colony-position rules where base points are the specified criterion.
- Preserve the historical value of a user's valid activities.

Base points must not decrease merely because the value of 2FUNC increases.

Spending or settling an economic asset must not erase the user's historical base-point achievement.

If a rank requires a cumulative threshold of valid base points, the system must evaluate that threshold according to the rank's explicit rules.

A governance position must not, by itself, grant unrestricted authority to mint 2FUNC.

## 3.3 Value Points

Technical field:

`value_points`

Meaning:

The value-based reward amount calculated from an eligible activity's base reward and the applicable 2FUNC value index and UVI policy.

Purpose:

- Reflect the value-based reward calculation.
- Determine the amount eligible for the settlement calculation.
- Prevent historical base-point progression from being confused with economic reward value.

Value points are not the user's base points and must not replace the base-point history.

The exact formula connecting `base_points`, the 2FUNC value index, and `value_points` remains subject to the formula decision recorded in Section 12.

## 3.4 Settlement Units

Concept:

Independent settlement amount calculated by UVI from value points.

A settlement amount is not a new base-point achievement.

The settlement result must not modify the historical `base_points` earned by a user.

A settlement operation must consume or close the corresponding eligible settlement entitlement so that it cannot be settled twice.

The final technical field name and exact formula for settlement units remain implementation decisions.

---

# 4. Base Reward and Value-Based Reward

## 4.1 Fixed Base Reward for an Activity

The base reward for the same activity under the same reward-rule version remains fixed.

If an activity has a base reward of 2,000 POINT, its base reward remains 2,000 POINT even if the value of 2FUNC later increases.

Changes to the reward rules must be versioned. The system must be able to identify the reward-rule version applicable to an activity.

## 4.2 Value-Based Reward Calculation

The value-based reward can change as the applicable 2FUNC value index changes.

Illustrative example:

| Property | User A | User B |
|---|---:|---:|
| Activity | Same valid activity | Same valid activity |
| Base reward | 2,000 POINT | 2,000 POINT |
| 2FUNC reference value | $0.01 | $0.02 |
| Value-based reward | 2,000 | 1,000 |
| Base-point progression | 2,000 | 2,000 |

This example illustrates the intended distinction between progression and value-based reward calculation.

The numbers are illustrative, not a finalized economic forecast.

For equivalent valid activities governed by the same base-reward rule, a change in 2FUNC value must not silently rewrite the base reward.

## 4.3 Transparent Calculation Records

For each valid activity, the system should preserve at least:

- Unique activity/event identifier.
- User identifier.
- Activity type.
- Activity timestamp.
- Applicable reward-rule version.
- Base reward in POINT.
- Applicable 2FUNC value index.
- Value-index source and observation time.
- Calculated value points.
- Applicable UVI policy version.
- Resulting settlement eligibility, where applicable.
- Settlement status and settlement reference, when settled.

A separate field representing an unexplained deduction is not required.

The system should use the term `value_points` for the value-based reward amount rather than presenting the calculation as an arbitrary deduction from the user's base score.

---

# 5. Activity Validation and Proven Fraud

## 5.1 Invalid Activities

A valid activity must be established before points are awarded.

Activities that fail the required validity rules receive no points.

This architecture does not require a separate points category for incomplete or invalid activities.

## 5.2 Proven Fraud

When fraud is established under the applicable rules:

- The affected base-point achievements must be corrected.
- The affected value-based rewards must be corrected.
- Any affected rank or eligibility decision must be re-evaluated when required by the governing rules.
- The correction must have a traceable reason, timestamp, reference and authorized decision.
- The original event history must remain available for audit.

Corrections must not silently erase historical records.

If affected rewards have already been spent, settled, transferred or converted into assets, reversing the original score alone is insufficient.

Recovery, debt, asset reversal or other remedies must follow a separately defined and authorized policy.

No recovery mechanism may silently violate the token's supply or accounting rules.

---

# 6. Point-to-Value Ratios

The following ratios have been established as the current reference relationships.

## 6.1 Drika

**4 base POINT = 1 Drika**

This ratio is based on POINT in its canonical meaning: base points.

It must not be silently reinterpreted as four value points.

However, this base ratio alone does not establish that every base POINT is automatically and independently convertible into a spendable Drika.

The settlement calculation must respect the distinction between base points and value points.

UVI must define the eligible conversion basis and apply the appropriate policy without counting the same entitlement more than once.

## 6.2 Drik

**1 Drik = 2,000,000 2FUNC**

This is the established reference ratio.

Before implementation as an unconditional conversion guarantee, the system must distinguish between:

- A reference calculation ratio.
- A fixed protocol conversion ratio.
- A market price.
- A redeemable or collateral-backed promise.

If the ratio is intended to guarantee actual conversion into 2FUNC, the implementation must specify the source of the 2FUNC, the settlement mechanism, the available reserves or issuance authority, and the applicable supply-cap controls.

The ratio must not provide a path to bypass the 2FUNC supply cap.

## 6.3 SHIR and ΣSHIR

Current computational reference ratios:

- 1 SHIR = 1,000 POINT.
- 1 ΣSHIR = 10 SHIR.
- 1 ΣSHIR = 10,000 POINT.
- 1 2FUNC = 2 ΣSHIR.
- 1 2FUNC = 20,000 POINT under the existing UVI computational reference.

These ratios describe the established computational model.

They do not automatically guarantee that every 20,000 base POINT can be converted into one on-chain 2FUNC.

Actual conversion requires an eligible entitlement, the applicable UVI policy, settlement rules, issuance authorization and remaining supply capacity.

Because base POINT and value points are separate concepts, the technical implementation must explicitly identify the correct calculation basis for each conversion rather than applying these ratios indiscriminately.

---

# 7. Daily Settlement Window

## 7.1 User Selection Window

The established proposed daily settlement schedule is:

- Opens: 22:30.
- Closes: 23:30.
- Automatic settlement: 24:00.

The settlement scheduler must use a defined reference time zone.

The time zone must be consistent across the backend, user interface, scheduled jobs and settlement records.

The exact production time-zone identifier must be configured explicitly. It must not depend implicitly on the device's local time.

## 7.2 User-Selected Settlement

During the 22:30–23:30 window, the user may select one of four settlement destinations:

1. Drika
2. SHIR
3. ΣSHIR
4. 2FUNC

The selection applies to the eligible settlement amount under the applicable UVI rules.

A selection must be validated and recorded before the settlement deadline.

The conversion result must be determined by the relevant conversion policy and must not be calculated using an unrelated or silently substituted ratio.

Drik is not one of the four user-selectable destinations in this daily selection window.

## 7.3 Automatic Settlement

At 24:00, the system automatically settles eligible outstanding amounts for which no valid user-selected settlement has been completed.

**The automatic settlement destination is always Drika.**

The automatic process must:

- Identify eligible outstanding settlement entitlements.
- Exclude amounts already successfully settled.
- Exclude amounts currently being processed under a valid settlement request.
- Apply the approved Drika settlement rule.
- Record the resulting amount and settlement reference.
- Prevent duplicate execution.
- Preserve the base-point history.
- Respect applicable accounting and conversion policies.

A user who misses the selection window must not be able to leave the same eligible settlement amount indefinitely pending merely by taking no action.

## 7.4 Idempotency and Duplicate Prevention

Each settlement entitlement and settlement execution must have a unique identifier.

Repeated execution of the same scheduled job or repeated submission of the same request must not settle the same entitlement twice.

The settlement process should follow an explicit state transition, such as:

`PENDING -> PROCESSING -> SETTLED`

Failed or interrupted processing must have a safe recovery path.

A partially completed settlement must not be treated as a successful full settlement.

---

# 8. POINT Is Not Spendable

POINT is an activity and progression score.

POINT is not directly spendable for goods, services or other in-ecosystem expenditures.

The value assets used for eligible ecosystem expenses are:

- Drika
- SHIR
- ΣSHIR
- 2FUNC
- Drik

The economic flow is:

`Valid Activity`
    -> `Base POINT`
    -> `Value-Based Reward Calculation`
    -> `UVI Settlement Calculation`
    -> `Eligible Value Asset`
    -> `In-Ecosystem Expenditure`

The user's base-point progression must not be reduced simply because an eligible value asset is spent.

The following concepts must remain separate:

- Lifetime base points earned.
- Historical corrections to base points.
- Value points calculated.
- Outstanding settlement entitlement.
- Settlement already completed.
- Current balances of value assets.
- 2FUNC allocated but not yet issued.
- 2FUNC actually issued on-chain.

An asset balance and a historical activity score are different accounting concepts.

## 8.1 Example

A user may have:

- 150,000,000 lifetime base POINT earned.
- 110,000,000 POINT-equivalent historical expenditure or settlement activity, if such an accounting metric is explicitly maintained.
- 40,000,000 current spendable units only if the relevant asset-accounting rules independently establish that balance.

These figures must not be used to infer a spendable POINT balance, because POINT is not a spendable asset.

The example illustrates why score history and asset balances must remain separate.

---

# 9. Historical Growth and Value Index

The value-based reward model must preserve sufficient historical information to explain how reward calculations changed over time.

The system should support reports such as:

- The 2FUNC value index applicable when a user joined.
- The current 2FUNC value index.
- The change between the two observations.
- The reward-rule version applicable to each activity.
- The base reward for an activity.
- The value points calculated for that activity.
- The effect of the value-index policy on the calculated reward.
- Historical changes in the value index from system launch to the present.

The value index must have a defined source, timestamp, validity policy and historical record.

A market price and a protocol value index must not be assumed to be identical.

If market price is used, the implementation must address unreliable observations, missing data, manipulation, short-term volatility and the policy used when no valid observation is available.

The exact index methodology and inverse reward formula remain open until formally approved.

Historical activity records must not be rewritten whenever the current value index changes.

New index observations affect calculations governed by the applicable policy. Historical corrections require an explicit authorized correction event.

---

# 10. UVI Responsibilities

UVI is the Universal Value computational engine.

UVI is not the general economic authority and must not independently invent economic policy.

Its responsibilities include:

- Calculating value-based rewards.
- Applying approved conversion ratios.
- Calculating eligible settlement amounts.
- Enforcing the applicable value and settlement policies.
- Producing traceable calculation results.
- Preserving calculation inputs and policy versions.
- Preventing repeated use of the same settlement entitlement.
- Providing evidence needed by downstream accounting and issuance components.

Economic policy and governance rules determine which calculations and conversions are permitted.

AI may provide recommendations but is not the final policy or issuance authority.

## 10.1 Existing UVI Integration Direction

The established integration direction is:

`EventBus -> Activity Validation -> POINT Ledger -> UVI Pipeline -> Settlement/Transaction -> Value Ledger`

The relevant existing UVI infrastructure includes:

`platform_core/universal_value/`

Known component groups include:

- `core/`
- `pipeline/`
- `policies/`
- `converters/`
- `ledger/`
- `transactions/`
- `events/`
- `integrations/`
- `adapters/`

The snapshot records the intended architecture; it does not assert that all described settlement behavior is already implemented.

Implementation must extend the existing UVI infrastructure where appropriate instead of creating an unnecessary competing value engine.

---

# 11. Accounting, Ledger and Event Integrity

The system must maintain distinct records for:

1. Base-point activity history.
2. Value-point calculation history.
3. Outstanding settlement entitlements.
4. Completed settlement records.
5. Economic asset balances and transfers.
6. 2FUNC issuance and supply accounting.

A single field must not be used to represent multiple incompatible concepts.

Each valid activity and settlement must have a unique identifier.

Duplicate events must not produce duplicate rewards, duplicate settlements or duplicate issuance.

Corrections must be recorded as traceable events.

Runtime accounting must have a clearly defined source of truth. In the existing 2FUN architecture, SQLite is used as a runtime/source-of-truth store for applicable internal system data, while the blockchain is authoritative for actual on-chain 2FUNC issuance and transactions.

JSON may be used for configuration, snapshots and historical artifacts, but must not silently replace the authoritative runtime ledger.

The central EventBus must be used for the appropriate cross-component event communication. Hidden direct dependencies must not bypass ownership and policy boundaries.

---

# 12. 2FUNC Supply and Issuance Controls

## 12.1 Maximum Supply

The previously supplied total-supply figure is recorded as:

`14441417005600`

The exact digit grouping and human-readable presentation must be verified against the authoritative tokenomics decision before implementation.

This snapshot does not reinterpret or silently normalize that number.

## 12.2 Ten-Stage Release Plan

The established release-plan direction is:

- Divide the planned supply release into 10 stages.
- Each successive stage must begin at least six months after the preceding stage.

The exact allocation amount or percentage for each stage, the stage-start reference date, unlock rules, and whether each stage represents minting, unlocking or distribution remain to be specified.

A staged release schedule does not itself authorize supply beyond the maximum supply.

## 12.3 Allocation Versus Issuance

The architecture must distinguish:

- `allocated`: entitlement or allocation recorded by the internal system.
- `issued/minted`: 2FUNC actually created on-chain.
- `transferred`: existing 2FUNC moved between accounts.
- `burned`: 2FUNC destroyed under the applicable protocol rules.

An internal allocation is not automatically an on-chain issuance.

Actual issuance must comply with the contract's supply constraints.

Burning tokens must not automatically authorize re-minting unless an explicit, approved protocol rule permits it.

## 12.4 Supply Exhaustion

Before implementation, the issuance policy must define what happens if eligible rewards exceed the remaining permitted issuance.

Possible policy choices include proportional scaling, deferral to a later period, or another explicitly approved method.

No behavior is finalized by this snapshot.

A reward calculation must not silently exceed the permitted issuance cap.

## 12.5 On-Chain and Off-Chain Boundary

The game and UVI should not place all gameplay and colony calculations directly inside the token contract.

The intended separation is:

`Game / Validated Activity`
    -> `POINT Ledger`
    -> `UVI Calculation`
    -> `Approved Settlement and Issuance Policy`
    -> `Authorized Issuance Interface`
    -> `2FUNC Smart Contract`

The contract must enforce the applicable on-chain supply and authorization constraints.

The mechanism used to authorize or relay eligible issuance must be specified and secured before deployment.

---

# 13. Conversion Costs and Gas Fees

A conversion does not necessarily require a separate blockchain transaction.

The implementation must distinguish between:

- Internal ledger conversion.
- Internal settlement accounting.
- On-chain asset transfer.
- On-chain minting.
- On-chain contract execution.

Internal operations may be recorded without a separate on-chain transaction, depending on the implementation.

Operations requiring blockchain execution may incur gas fees unless a supported fee-sponsorship, batching or transaction-abstraction mechanism is implemented.

The daily settlement design is intended to reduce unnecessary repeated user actions and avoid leaving eligible POINT-derived value indefinitely unsettled.

It does not, by itself, guarantee that every conversion is gas-free.

The exact settlement execution model and responsibility for gas fees must be defined in the relevant implementation specification.

---

# 14. Rank, Governance and Economic Eligibility

Rank eligibility, base-point progression, value-point calculation, settlement eligibility and 2FUNC issuance are separate decisions.

A user's rank must be evaluated against the specific requirements defined for that rank.

If a position requires a cumulative base-point threshold, the system must verify that threshold using valid base-point history.

A discrepancy between the recorded base-point history and a rank claim must trigger the applicable validation and correction process.

A rank or governance position must not independently authorize unrestricted token issuance.

Governance and approved rules retain final authority over policy.

AI remains advisory-only.

---

# 15. Unresolved Decisions — Must Not Be Invented

The following items remain open and must be decided before their respective production implementations.

## 15.1 Value-Reward Formula

The exact formula converting base reward and the applicable 2FUNC value index into `value_points` has not been finalized.

An inverse relationship has been considered:

`Reward_new = Reward_base * Value_base / Value_new`

This is a candidate formula, not a finalized rule.

The reference index, observation time, baseline, precision, rounding behavior and missing-data policy must be specified.

## 15.2 Settlement Formula

The exact formula converting `value_points` into independent settlement units must be finalized.

It must preserve the distinction between base POINT progression and value-based settlement.

The fixed reference ratio of 4 base POINT to 1 Drika must not be confused with a guarantee that every base POINT is automatically convertible.

## 15.3 Conversion and Rounding

The system must define:

- Numeric precision for each unit.
- Minimum representable amounts.
- Integer and fractional conversion behavior.
- Rounding and remainder handling.
- Consistent calculations across UVI, ledgers, exchange and contracts.

Exact remainders must not be silently discarded.

## 15.4 Value Index

The source and methodology of the 2FUNC value index remain to be approved.

A market price must not be treated as a reliable protocol index without an explicit policy.

## 15.5 Settlement Time Zone

The production time-zone identifier for the daily 22:30–23:30 selection window and 24:00 automatic settlement must be configured explicitly.

## 15.6 Failed or Interrupted Settlement

Retry, rollback, reconciliation and recovery behavior must be defined without allowing duplicate settlement.

## 15.7 Supply Stages

The amount or percentage assigned to each of the 10 release stages, and whether each stage is a mint, unlock or distribution, remain to be specified.

## 15.8 Supply Exhaustion

The system must define the handling of eligible rewards when the remaining permitted issuance is insufficient.

## 15.9 Drik and Drika Guarantees

The established ratios are recorded, but any guaranteed redemption, reserve requirement, liquidity promise or on-chain conversion obligation must be specified separately.

## 15.10 Previously Settled Rewards and Fraud

A correction to base or value points does not automatically reverse a completed asset transfer or on-chain transaction.

A separate authorized recovery policy is required for such cases.

---

# 16. Consolidated Decisions

The following decisions are recorded in this snapshot.

1. POINT means base points by default.
2. Four base POINT equal one Drika as the established reference ratio.
3. One Drik equals 2,000,000 2FUNC as the established reference ratio.
4. The existing UVI computational references are:
   - 1 SHIR = 1,000 POINT.
   - 1 ΣSHIR = 10 SHIR.
   - 1 ΣSHIR = 10,000 POINT.
   - 1 2FUNC = 2 ΣSHIR.
   - 1 2FUNC = 20,000 POINT under the existing computational reference.
5. Base points determine progression and applicable rank eligibility.
6. Value points are calculated using the approved value-based reward policy.
7. UVI calculates independent settlement amounts from value points.
8. POINT is not directly spendable.
9. The five value assets for eligible in-ecosystem expenses are Drika, SHIR, ΣSHIR, 2FUNC and Drik.
10. The daily user-selected settlement window is 22:30–23:30.
11. The four user-selectable settlement destinations are Drika, SHIR, ΣSHIR and 2FUNC.
12. At 24:00, eligible outstanding amounts without a completed user-selected settlement are automatically settled to Drika.
13. The production time zone must be explicitly configured.
14. Settlement must be traceable and protected against duplicate execution.
15. Historical base-point progression must survive ordinary spending and settlement.
16. Invalid activities receive no points.
17. Proven fraud requires traceable correction of affected base and value-based rewards.
18. Historical records must be preserved.
19. 2FUNC issuance must comply with the approved maximum supply and issuance rules.
20. The planned supply release consists of 10 stages, each beginning at least six months after the preceding stage.
21. Internal allocation is distinct from actual on-chain issuance.
22. The existing UVI infrastructure should be reused where appropriate.
23. EventBus is the central mechanism for applicable cross-component event communication.
24. Governance and approved rules have final policy authority; AI is advisory-only.
25. Unresolved formulas and policies must not be treated as finalized merely because this snapshot exists.

---

# 17. Next Implementation Sequence

The next work should proceed in focused steps.

1. Confirm this snapshot as the architecture reference.
2. Specify the exact UVI formula for calculating value points.
3. Specify the conversion from value points to independent settlement units.
4. Specify the daily settlement state machine and idempotency rules.
5. Define the value-index source and historical observation policy.
6. Define numeric precision and remainder handling.
7. Integrate the rules into the existing UVI and ledger infrastructure.
8. Specify issuance authorization and supply-cap enforcement for 2FUNC.
9. Test calculations, settlement deadlines, duplicate requests, retries, corrections and supply-cap boundaries.
10. Only then finalize the production smart-contract and deployment requirements.

The implementation must remain consistent with the existing 2FUN architecture and must not create a parallel economic engine unnecessarily.

---

# End of Snapshot

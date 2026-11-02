# Example spec (minimal, for structure only)

<!-- file: 0-overview.md -->
# Expense Book — Feature Spec

## 1. Product overview

Expense Book is a web app for recording personal spending.

## User roles

| Role | Main tasks | Main module |
| --- | --- | --- |
| User | Record and view spending | 1, 2 |


<!-- file: 1-expenses.md -->
# 1. Expenses

## Summary

The Expenses module helps users manage personal spending.

## Roles & permissions

| Role | Can do | Cannot do |
| --- | --- | --- |
| User | Record and view expenses | See other people's data |

## Feature map

| # | Feature | Screen | Main role | Status on dev |
| --- | --- | --- | --- | --- |
| 1.1 | Record an expense | /m1/f1 | User | Works |
| 1.2 | Expense list | /m1/f2 | User | Works |

## 1.1 Record an expense `/m1/f1`

**Problem & value** — Users need to record an expense quickly to follow their budget.

**User stories**

- As a user, I want to record an expense in 10 seconds so that I do not forget it.

**Main flow**

1. User opens the screen. System shows the list.
2. User presses Add and enters the amount. System checks that the amount is greater than 0.
3. User presses Save. System saves and shows a message.

**Alternate flows & exceptions**

- When the amount is 0 → System shows "Amount must be greater than 0" and does not save.

**Business rules**

- BR-1.1.1 The amount is greater than 0.

**UI & data**

| Field | Type | Required |
| --- | --- | --- |
| Amount | number | yes |

**Acceptance criteria**

- AC-1.1.1 Given amount 0, When Save is pressed, Then an error is shown.

**Field specification**

| Field | Type | Required | Format / length | Default | Validation | Error message |
| --- | --- | --- | --- | --- | --- | --- |
| Amount | number | Yes | at most 12 digits | — | greater than 0 | Observed: "Amount must be greater than 0" |

**Test cases**

| Code | Precondition | Steps | Expected result | Type |
| --- | --- | --- | --- | --- |
| TC-1.1.1 | Logged in | Enter 50,000, Save | Expense appears | Main |
| TC-1.1.2 | Logged in | Enter 0, Save | Error shown | Edge |
| TC-1.1.3 | Guest | Open screen | Redirect to login | Permission |

**Open questions & assumptions**

| Question | Current assumption | Who answers | Priority |
| --- | --- | --- | --- |
| Is there a daily limit on expenses? | Verified 29/10/2026: no limit | QA | Low |

## 1.2 Expense list `/m1/f2`

**Problem & value** — Users need to record an expense quickly to follow their budget.

**User stories**

- As a user, I want to record an expense in 10 seconds so that I do not forget it.

**Main flow**

1. User opens the screen. System shows the list.
2. User presses Add and enters the amount. System checks that the amount is greater than 0.
3. User presses Save. System saves and shows a message.

**Alternate flows & exceptions**

- When the amount is 0 → System shows "Amount must be greater than 0" and does not save.

**Business rules**

- BR-1.2.1 The amount is greater than 0.

**UI & data**

| Field | Type | Required |
| --- | --- | --- |
| Amount | number | yes |

**Acceptance criteria**

- AC-1.2.1 Given amount 0, When Save is pressed, Then an error is shown.

**Field specification**

| Field | Type | Required | Format / length | Default | Validation | Error message |
| --- | --- | --- | --- | --- | --- | --- |
| Amount | number | Yes | at most 12 digits | — | greater than 0 | Observed: "Amount must be greater than 0" |

**Test cases**

| Code | Precondition | Steps | Expected result | Type |
| --- | --- | --- | --- | --- |
| TC-1.2.1 | Logged in | Enter 50,000, Save | Expense appears | Main |
| TC-1.2.2 | Logged in | Enter 0, Save | Error shown | Edge |
| TC-1.2.3 | Guest | Open screen | Redirect to login | Permission |

**Open questions & assumptions**

| Question | Current assumption | Who answers | Priority |
| --- | --- | --- | --- |
| Is there a daily limit on expenses? | Verified 29/10/2026: no limit | QA | Low |

## Appendix A — Integration & API

GET /api/expenses.


<!-- file: 2-reports.md -->
# 2. Reports

## Summary

The Reports module shows users how they spend.

## Roles & permissions

| Role | Can do | Cannot do |
| --- | --- | --- |
| User | Record and view expenses | See other people's data |

## Feature map

| # | Feature | Screen | Main role | Status on dev |
| --- | --- | --- | --- | --- |
| 2.1 | Monthly report | /m2/f1 | User | Works |

## 2.1 Monthly report `/m2/f1`

**Problem & value** — Users need to record an expense quickly to follow their budget.

**User stories**

- As a user, I want to record an expense in 10 seconds so that I do not forget it.

**Main flow**

1. User opens the screen. System shows the list.
2. User presses Add and enters the amount. System checks that the amount is greater than 0.
3. User presses Save. System saves and shows a message.

**Alternate flows & exceptions**

- When the amount is 0 → System shows "Amount must be greater than 0" and does not save.

**Business rules**

- BR-2.1.1 The amount is greater than 0.

**UI & data**

| Field | Type | Required |
| --- | --- | --- |
| Amount | number | yes |

**Acceptance criteria**

- AC-2.1.1 Given amount 0, When Save is pressed, Then an error is shown.

**Field specification**

| Field | Type | Required | Format / length | Default | Validation | Error message |
| --- | --- | --- | --- | --- | --- | --- |
| Amount | number | Yes | at most 12 digits | — | greater than 0 | Observed: "Amount must be greater than 0" |

**Test cases**

| Code | Precondition | Steps | Expected result | Type |
| --- | --- | --- | --- | --- |
| TC-2.1.1 | Logged in | Enter 50,000, Save | Expense appears | Main |
| TC-2.1.2 | Logged in | Enter 0, Save | Error shown | Edge |
| TC-2.1.3 | Guest | Open screen | Redirect to login | Permission |

**Open questions & assumptions**

| Question | Current assumption | Who answers | Priority |
| --- | --- | --- | --- |
| Is there a daily limit on expenses? | Verified 29/10/2026: no limit | QA | Low |

## Appendix A — Integration & API

GET /api/expenses.



# Functional Audit v8.4.7

- Backend Python compile: PASS
- Calendar API: CRUD + ownership present
- Accounting API: transactions/tax reports/deductions present
- Contracts mobile: corrected to `/api/contracts/my`
- Svetlana API: JSON body schema fixed; OpenRouter integration with safe local fallback
- Bank mobile: connect action now calls `/api/bank/connect`
- Receipt mobile: check action now calls `/api/fns/check-receipt`
- Dead Flutter button handlers: removed from active screens
- Release artifacts: cleaned before packaging

Runtime SDK builds still require a network-enabled environment with Flutter/npm/Python dependencies installed.

"""Static regression checks for cross-resource integrity and payment race safety."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
crm = (root/'app/api/crm.py').read_text()
tasks = (root/'app/api/tasks.py').read_text()
sales = (root/'app/api/sales.py').read_text()
checks = {
    'deal create validates stage ownership': 'PipelineStage.id == deal.stage_id' in crm and 'PipelineStage.user_id == current_user.id' in crm,
    'deal update validates client ownership': 'Client.id == update_data["client_id"]' in crm and 'Client.user_id == current_user.id' in crm,
    'deal update validates stage ownership': 'PipelineStage.id == update_data["stage_id"]' in crm,
    'crm calls validate client ownership': 'call_data["client_id"]' in crm and 'action="call_created"' in crm,
    'crm tasks validate client ownership': 'task_data["client_id"]' in crm,
    'crm tasks validate deal ownership': 'task_data["deal_id"]' in crm,
    'crm tasks enforce deal/client consistency': 'Клиент задачи не соответствует клиенту сделки' in crm,
    'task API enforces deal/client consistency': 'Клиент задачи не соответствует клиенту сделки' in tasks,
    'complete task awards points only once': 'was_completed = task.status == "completed"' in tasks,
    'invoice number avoids count race': 'uuid4().hex[:8].upper()' in sales,
    'yookassa webhook locks invoice': 'select(Invoice).where(Invoice.id == invoice_id).with_for_update()' in sales,
    'yookassa webhook binds payment to invoice': 'Payment does not match invoice' in sales,
    'paid invoice cannot be cancelled by late webhook': 'if invoice.status == "paid":' in sales and '"duplicate": True' in sales,
}
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL') + ' ' + name)
failed = [n for n,v in checks.items() if not v]
print(f'RESULT: {len(checks)-len(failed)}/{len(checks)} PASS')
sys.exit(1 if failed else 0)

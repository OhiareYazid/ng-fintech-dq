{{ bronze_select('transactions', [
    'transaction_id', 'session_id', 'account_id', 'terminal_id', 'channel', 'direction',
    'amount', 'fee', 'currency', 'status', 'counterparty_bank_code', 'counterparty_account',
    'narration', 'created_at', 'settled_at', 'source_system',
]) }}

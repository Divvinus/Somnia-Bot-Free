from loguru import logger


def show_trx_log(address: str, trx_type: str, status: bool, result: str):
    status_icon = "✅" if status else "❌"

    log_message = (
        f"\n{'=' * 50}\n"
        f"Transaction Type: {trx_type}\n"
        f"Status: {status_icon} {'SUCCESS' if status else 'FAILED'}\n"
        f"Wallet: {address}\n"
        f"{'TX Hash: ' + result if isinstance(result, str) and result.startswith('0x') else 'Error: ' + str(result)}\n"
        f"{'=' * 50}"
    )


    if status:
        logger.success(log_message)
    else:
        logger.error(log_message)
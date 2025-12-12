from requests.exceptions import HTTPError

def get_HTTP_ERROR_message(err: HTTPError) -> str:
    """
    Generate a detailed error message from an HTTPError.

    Args:
        err (HTTPError): The HTTPError instance to extract information from.

    Returns:
        str: A formatted error message including status code, reason, and
        additional details for 400 Bad Request errors.
    """
    message = f'[HTTP ERROR ({err.response.status_code})]: {err.response.reason}'
    message += f'\n\n{err.args[0]}'

    if err.response.status_code == 400:
        message += f'\n\n{err.response.text}'

    return message
from http import HTTPStatus


class SolisCloudControlApiError(Exception):
    # see https://developer.soliscloud.com/guide/error-codes.html
    _TRANSIENT_RESPONSE_CODES = frozenset(
        {
            "S9999",  # system busy (concurrency limit)
            "B0119",  # request frequency too high
            "B0250",  # device unresponsive, please retry
            "B0115",  # command dispatch failed
            "B0180",  # read result timeout
        }
    )
    _TRANSIENT_HTTP_STATUSES = frozenset({HTTPStatus.REQUEST_TIMEOUT, HTTPStatus.TOO_MANY_REQUESTS, *range(500, 600)})

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_code: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_code = response_code
        final_message = message
        if status_code is not None:
            final_message = f"{final_message} (HTTP status code: {status_code})"
        if response_code is not None:
            final_message = f"{final_message} (API response code: {response_code})"

        super().__init__(final_message)

    @staticmethod
    def create(
        message: str,
        status_code: int | None = None,
        response_code: str | None = None,
    ) -> SolisCloudControlApiError:
        if (
            status_code in SolisCloudControlApiError._TRANSIENT_HTTP_STATUSES
            or response_code in SolisCloudControlApiError._TRANSIENT_RESPONSE_CODES
        ):
            return SolisCloudControlTransientApiError(message, status_code=status_code, response_code=response_code)

        return SolisCloudControlPermanentApiError(message, status_code=status_code, response_code=response_code)


class SolisCloudControlTransientApiError(SolisCloudControlApiError):
    pass


class SolisCloudControlPermanentApiError(SolisCloudControlApiError):
    pass

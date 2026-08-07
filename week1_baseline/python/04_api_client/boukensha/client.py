import http.client
import json
import ssl
import time
import urllib.error
import urllib.request

from .errors import ApiError


class Client:
    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
    TRANSIENT_ERRORS = (
        urllib.error.URLError,
        TimeoutError,
        ConnectionResetError,
        ConnectionRefusedError,
        ssl.SSLError,
        http.client.HTTPException,
        EOFError,
    )
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def __init__(self, builder):
        self.builder = builder

    def call(self, max_output_tokens=1024):
        payload = self.builder.to_api_payload(max_output_tokens=max_output_tokens)
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.builder.url, data=body, headers=self.builder.headers, method="POST"
        )

        attempts = 0

        while True:
            attempts += 1

            try:
                with urllib.request.urlopen(request) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as e:
                if e.code in self.RETRYABLE_STATUS_CODES and attempts <= self.MAX_RETRIES:
                    time.sleep(self._retry_delay(attempts))
                    continue
                body_text = e.read().decode("utf-8", errors="replace")
                plural = "s" if attempts != 1 else ""
                raise ApiError(
                    f"API request failed after {attempts} attempt{plural} ({e.code}): {body_text}"
                ) from e
            except self.TRANSIENT_ERRORS as e:
                if attempts > self.MAX_RETRIES:
                    raise ApiError(
                        f"API request failed after {attempts} attempts: {type(e).__name__}: {e}"
                    ) from e
                time.sleep(self._retry_delay(attempts))

    def _retry_delay(self, attempt):
        return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))

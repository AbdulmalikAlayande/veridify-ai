class VeridifiError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int, detail: dict | None = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)


class InsufficientBalanceError(VeridifiError):
    def __init__(self, current_balance: int, payment_link: str | None = None):
        super().__init__(
            "INSUFFICIENT_BALANCE",
            "Insufficient balance for verification",
            402,
            {
                "balance_naira": current_balance,
                "verification_cost_naira": 175,
                "payment_link": payment_link,
            },
        )


class InvalidApiKeyError(VeridifiError):
    def __init__(self):
        super().__init__("INVALID_API_KEY", "Invalid or revoked API key", 401)


class ImageTooLargeError(VeridifiError):
    def __init__(self, size_mb: float):
        super().__init__(
            "IMAGE_TOO_LARGE",
            f"Image size {size_mb:.1f}MB exceeds 10MB limit",
            413,
        )


class UnsupportedImageTypeError(VeridifiError):
    def __init__(self, mime_type: str):
        super().__init__(
            "UNSUPPORTED_IMAGE_TYPE",
            f"Image type {mime_type} is not supported",
            415,
        )


class InferenceFailedError(VeridifiError):
    def __init__(self, reason: str = "Inference failed"):
        super().__init__(
            "INFERENCE_FAILED",
            reason,
            500,
        )


class SquadAPIError(VeridifiError):
    def __init__(self, message: str, upstream_status: int | None = None, upstream_body: dict | None = None):
        super().__init__(
            "SQUAD_API_ERROR",
            message,
            502,
            {"upstream_status": upstream_status, "upstream_body": upstream_body or {}},
        )

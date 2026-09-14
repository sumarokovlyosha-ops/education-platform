from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "education_platform_http_requests_total",
    "Total number of HTTP requests",
    ["method", "route", "status_code"],
)


HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "education_platform_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "education_platform_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"],
)

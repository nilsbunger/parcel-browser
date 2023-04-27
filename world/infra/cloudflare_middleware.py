# When using Cloudflare DNS proxy to the web app, all requests go to a Cloudflare server which then proxies them
# to the web app. Patch up the request here so we still get the client IP address.
import logging

log = logging.getLogger(__name__)


class CloudflareMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        log.info("Cloudflare Middleware: info log")
        log.warning("Cloudflare Middleware: warning log")
        log.error("Cloudflare Middleware: error log")

    def __call__(self, request):
        # Check if the request has the CF-Connecting-IP header
        if "HTTP_CF_CONNECTING_IP" in request.META:
            request.META["REMOTE_ADDR"] = request.META["HTTP_CF_CONNECTING_IP"]
            log.info("CloudflareMiddleware: REMOTE_ADDR set to " + request.META["REMOTE_ADDR"])
        else:
            log.error(
                "CloudflareMiddleware: HTTP_CF_CONNECTING_IP not found in request.META. IP="
                + request.META["REMOTE_ADDR"]
            )

        response = self.get_response(request)
        return response

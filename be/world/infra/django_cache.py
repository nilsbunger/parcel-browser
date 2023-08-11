from django.middleware.cache import CacheMiddleware
from django.utils.decorators import decorator_from_middleware_with_args


## Create our own thin layer around Django caching middleware so we can cache empty responses.
class H3CacheMiddleware(CacheMiddleware):
    def process_response(self, request, response):
        if response.status_code == 204:
            # Fudge the response so that it's cacheable.
            response.status_code = 200
            resp = super().process_response(request, response)
            resp.status_code = 204
            return resp
        else:
            return super().process_response(request, response)


# cache_page decorator, adapted from django.views.decorator.cache
def h3_cache_page(seconds, *, cache=None, key_prefix=None):
    return decorator_from_middleware_with_args(H3CacheMiddleware)(
        page_timeout=seconds,
        cache_alias=cache,
        key_prefix=key_prefix,
    )

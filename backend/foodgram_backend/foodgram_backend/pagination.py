from foodgram_backend.constants import PAGE_SIZE, MAX_PAGE_SIZE
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    Кастомная пагинация с поддержкой `limit` и `page`
    """
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
    max_page_size = MAX_PAGE_SIZE

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

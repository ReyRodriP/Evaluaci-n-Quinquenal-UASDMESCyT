"""Consulta del historial global con la misma visibilidad interna que las decisiones."""

from rest_framework.pagination import PageNumberPagination

from accounts.permissions import ROLES_SIN_RESTRICCION, _grupos_usuario


def puede_consultar_historial(request):
    grupos = _grupos_usuario(request.user)
    return request.user.is_superuser or bool(grupos & ROLES_SIN_RESTRICCION) or 'Evaluador Externo' not in grupos


class HistorialAsignacionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['page'] = self.page.number
        response.data['page_size'] = self.get_page_size(self.request)
        return response

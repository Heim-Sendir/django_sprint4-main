from django.core.paginator import Paginator

PAGIN_PAGE = 10


def paginator(context, request):
    paginator = Paginator(context, PAGIN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj,
    }

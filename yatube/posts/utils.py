from django.core.paginator import Paginator


def post_obj(request, post_list, count: int):
    """Расчитывает паджинатор"""
    paginator = Paginator(post_list, count)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

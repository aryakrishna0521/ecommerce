from store.models import BasketItem

def cart_count_context(request):
    count=0
    if request.user.is_authenticated:
        count=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False).count()
    return {"item_count":count}
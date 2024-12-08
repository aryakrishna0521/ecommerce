from django.shortcuts import render,redirect
from django.views.generic import View
from store.forms import SignUpForm,LoginForm,OrderForm
from django.core.mail import send_mail
from store.models import User,Size,BasketItem,OrderItem,Order
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from store.models import Product
from django.db.models import Sum
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from decouple import config

# Create your views here.

RZP_KEY_ID=config('RZP_KEY_ID')
RZP_KEY_SECRET=config('RZP_KEY_SECRET')


def sent_otp_phone(otp):
    from twilio.rest import Client
    account_sid = 'AC14ecdf07af3fb8c319710c3146d4ca93'
    auth_token = 'd07ce839953cbb34684eae11dd5fc80c'
    client = Client(account_sid, auth_token)
    message = client.messages.create(
    from_='+15633629101',
    body=otp,
    to='+919037911850'
    )
    print(message.sid)

def send_otp_email(user):
    user.generate_otp()
    sent_otp_phone(user.otp)
    subject="verify your email"
    message=f"otp for account verification is{user.otp}"
    from_email="aryakrishna0521@gmail.com"
    to_email=[user.email]
    send_mail(subject,message,from_email,to_email)




class SignUpView(View):
    template_name="register.html"
    form_class=SignUpForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        return render(request,self.template_name,{"form":form_instance})

    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)
        if form_instance.is_valid():
            user_object=form_instance.save(commit=False)
            user_object.is_active=False
            user_object.save()
            send_otp_email(user_object)
            # return render(request,verify_otp.html)
            return redirect('verify-email')
        return render(request,self.template_name,{"form":form_instance})


class VerifyEmailView(View):

    template_name="verify_email.html"
    def get(self,request,*args,**kwargs):
        return render(request,self.template_name)

    def post(self,request,*args,**kwargs):
        otp=request.POST.get("otp")
        try:
            user_object=User.objects.get(otp=otp)
            user_object.is_active=True
            user_object.is_verified=True
            user_object.otp=None
            user_object.save()
            return redirect("register")
        except:
            messages.error(request,"invalid otp")
            return render(request,self.template_name)


class SignInView(View):
    template_name="login.html"
    form_class=LoginForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        return render(request,self.template_name,{"form":form_instance})
    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)
        if form_instance.is_valid():
            uname=form_instance.cleaned_data.get("username")
            pwd=form_instance.cleaned_data.get("password")
            user_object=authenticate(request,username=uname,password=pwd)
            if user_object:
                login(request,user_object)
                return redirect('product-list')
        return render(request,self.template_name,{"form":form_instance})

class ProductListView(View):
    template_name="index.html"
    def get(self,request,*args,**kwargs):
        qs=Product.objects.all()
        paginator=Paginator(qs,4)
        page_number=request.GET.get("page")
        page_obj=paginator.get_page(page_number)
        return render(request,self.template_name,{"data":qs,"page_obj":page_obj})

        """
        current page number=  ?page={{page_obj.number}}

        next page number =    ?page={{page_obj.next_page_nuumber}}

        previous page number =?page={{page_obj.previous_page_number}}
        
        last page number=     ?pafe=={{page_obj.paginator.num_pages}}
        
        """

class ProductDetailView(View):
    template_name='product.html'
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        qs=Product.objects.get(id=id)
        return render(request,self.template_name,{"product":qs})

class AddToCartView(View):
    def post(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        size=request.POST.get("size")
        quantity=request.POST.get("quantity")
        product_object=Product.objects.get(id=id)
        size_object=Size.objects.get(name=size)
        # basket_object=Basket.objects.get(owner=request.user)
        basket_object=request.user.cart

        BasketItem.objects.create(
            product_object=product_object,
            quantity=quantity,
            size_object=size_object,
            basket_object=basket_object

        )
        print("item has been added to cart")
        return redirect("cart-summary")

class CartSummaryView(View):
    template_name="cartsummary.html"
    def get(self,request,*args,**kwargs):
        qs=BasketItem.objects.filter(basket_object=request.user.cart,is_order_placed=False)
        basket_total=sum([bi.item_total for bi in qs])
        basket_item_count=qs.count()
        return render(request,self.template_name,{"basketitems":qs,"basket_total":basket_total,"basket_item_count":basket_item_count})

class BasketItemDeleteview(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get('pk')
        item_delete=BasketItem.objects.get(id=id).delete()
        return redirect('cart-summary')


import razorpay

class PlaceOrderView(View):
    template_name="place_order.html"
    form_class=OrderForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        qs=request.user.cart.cart_item.filter(is_order_placed=False)
        total=sum(bi.item_total for bi in qs)
        return render(request,self.template_name,{"form":form_instance,"items":qs,"total":total})

    def post(self,request,*args,**kwargs):
        form_data=request.POST
        form_instance=self.form_class(form_data)
        if form_instance.is_valid():
            form_instance.instance.customer=request.user

            order_instance=form_instance.save()
            basket_items=request.user.cart.cart_item.filter(is_order_placed=False)

            payment_method=form_instance.cleaned_data.get("payment_method")
            print(payment_method)

            for bi in basket_items:
                OrderItem.objects.create(

                    order_object=order_instance,
                    product_object=bi.product_object,
                    quantity=bi.quantity,
                    size_object=bi.size_object,
                    price=bi.product_object.price
                )
                bi.is_order_placed=True
                bi.save()

            #rzp integration 
            if payment_method=="ONLINE":
                client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))
                total=sum([bi.item_total for bi in basket_items])*100
                data = { "amount": total, "currency": "INR", "receipt": "order_rcptid_11" }
                payment = client.order.create(data=data)

                print(payment_method)
                print(payment)

                rzp_order_id=payment.get("id")
                order_instance.rzp_order_id=rzp_order_id
                order_instance.save()
                context={
                    "amount":total,
                    "key_id":RZP_KEY_ID,
                    "order_id":rzp_order_id,
                    "currency":"INR"
                    
                    }
                return render(request,"payment.html",context)


            
        return redirect('product-list')

class OrderSummaryView(View):
    template_name="ordersummary.html"
    def get(self,request,*args,**kwargs):
        qs=request.user.orders.all().order_by("-created_date")
        return render(request,self.template_name,{"orders":qs})

@method_decorator([csrf_exempt],name="dispatch")
class PaymentVerificationView(View):
    def post(self,request,*args,**kwargs):
        client = razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))
        try:
           client.utility.verify_payment_signature(request.POST)
           print("payment success")
           ordet_id=request.POST.get("razorpay_order_id")
           order_object=Order.objects.get(rzp_order_id=ordet_id)
           order_object.is_paid=True
           order_object.save()
           login(request,order_object.customer)



        except:
            print("payment failed")

        print(request.POST)
        return redirect("order-summary")


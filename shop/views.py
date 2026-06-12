from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Product, Category, Cart, CartItem, Order, OrderItem

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

def index(request):
    if not Product.objects.exists():
        seed_data()
    new_products = Product.objects.filter(is_new=True)[:4]
    bestsellers = Product.objects.filter(is_bestseller=True)[:4]
    return render(request, 'shop/index.html', {'new_products': new_products, 'bestsellers': bestsellers})

def catalog(request):
    products = Product.objects.all()
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    sort = request.GET.get('sort', '-created_at')

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    if sort in ['price', '-price', 'name', '-name', '-created_at']:
        products = products.order_by(sort)

    categories = Category.objects.all()
    return render(request, 'shop/catalog.html', {'products': products, 'categories': categories})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'shop/product_detail.html', {'product': product})

def cart_view(request):
    cart = get_or_create_cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.save()
    return redirect('cart')

def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart=get_or_create_cart(request))
    item.delete()
    return redirect('cart')

def update_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, cart=get_or_create_cart(request))
        qty = int(request.POST.get('quantity', 1))
        if qty > 0:
            item.quantity = qty
            item.save()
        else:
            item.delete()
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        return redirect('cart')
    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            total=cart.get_total(),
            address=request.POST['address'],
            phone=request.POST['phone'],
            comment=request.POST.get('comment', '')
        )
        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        cart.items.all().delete()
        return redirect('order_success', order_id=order.id)
    return render(request, 'shop/checkout.html', {'cart': cart})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/orders.html', {'order': order, 'success': True})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/orders.html', {'orders': orders})

def seed_data():
    """Автоматическое наполнение БД для демонстрации"""
    cat1 = Category.objects.create(name='Зелёный чай', slug='green')
    cat2 = Category.objects.create(name='Улун', slug='oolong')
    cat3 = Category.objects.create(name='Пуэр', slug='puer')

    products = [
        Product(name='Лунцзин', slug='longjing', category=cat1, description='Знаменитый китайский зелёный чай с нежным ореховым вкусом.', price=1200, stock=50, is_new=True, is_bestseller=True),
        Product(name='Те Гуань Инь', slug='tgy', category=cat2, description='Светлый улун с цветочным ароматом и сладким послевкусием.', price=1500, stock=30, is_bestseller=True),
        Product(name='Да Хун Пао', slug='dhp', category=cat2, description='Легендарный тёмный улун с глубоким древесным вкусом.', price=1800, stock=20),
        Product(name='Шу Пуэр 2015', slug='shu_puer', category=cat3, description='Выдержанный пуэр с мягким земляным вкусом.', price=2200, stock=15, is_new=True),
        Product(name='Сенча', slug='sencha', category=cat1, description='Японский зелёный чай с освежающим травяным вкусом.', price=950, stock=40),
        Product(name='Билочунь', slug='bilochun', category=cat1, description='Нежный весенний чай с фруктовыми нотами.', price=1350, stock=25, is_bestseller=True),
    ]
    for p in products:
        p.save()
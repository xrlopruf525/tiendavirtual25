from django.shortcuts import get_object_or_404, render, redirect
from .models import *
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView,DeleteView
from django.urls import reverse_lazy
from .forms import CompraForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count


# Create your views here.

class ListadoProductos (ListView):
    model = Producto
    template_name = 'tienda/productos_listado.html'
    # context_object_name = 'listaProductos'

class DetalleProducto (DetailView):
    model = Producto
    template_name = 'tienda/producto_detalle.html'

class EditarProducto (UpdateView):
    model = Producto
    template_name = 'tienda/producto_editar.html'
    fields = '__all__'
    success_url = reverse_lazy("listado")

class BorrarProducto (DeleteView):
    model = Producto
    success_url = reverse_lazy("listado")

class CrearProductos(CreateView):
    model = Producto
    template_name = 'tienda/producto_crear.html'
    fields = '__all__'
    success_url = reverse_lazy("listado")

class ComprarProducto (LoginRequiredMixin,ListView):
    model = Producto
    template_name = 'tienda/compra_listado.html'
    context_object_name = 'productos'
    paginate_by=2
    
    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        marcas = Marca.objects.filter(producto__isnull=False).distinct()
        contexto["marcas"] = marcas

        form = CompraForm()
        contexto['compra_form'] = form

        return contexto

    def get_queryset(self):

        query = super().get_queryset()
        filtro_nombre = self.request.GET.get("filtro_nombre")
        filtro_marca = self.request.GET.get("filtro_marca")
        filtro_precio_max = self.request.GET.get("filtro_precio")

        if filtro_nombre :
            query = query.filter(nombre__icontains = filtro_nombre)
        
        if filtro_marca:
            query = query.filter(marca__nombre = filtro_marca)

        if filtro_precio_max:
            query = query.filter(precio__lte = filtro_precio_max)
        


        return query
    
class Checkout(LoginRequiredMixin,View):

    def get(self, request, pk):
        producto = get_object_or_404(Producto,pk=pk)
        unidades = request.GET.get('unidades')
        total = int(unidades) * producto.precio
        #form = CompraForm({'unidades':unidades})
        return render(request, 'tienda/checkout.html',{'producto': producto,'unidades':unidades,'total':total})
    
    def post(self, request, pk):
        producto = get_object_or_404(Producto,pk=pk)
        unidades = int(request.POST.get('unidades'))
        usuario = request.user
        total = unidades * producto.precio
   
        if usuario.saldo >= total:
            
            if unidades <= producto.unidades:
                Compra.objects.create(usuario=usuario,unidades=int(unidades),producto=producto,importe= total)
                usuario.saldo -= total
                usuario.save()
                producto.unidades -= unidades
                producto.save()
                messages.success(request, "Compra realizada correctamente")

            else:
                messages.error(request, "No existen sucientes unidades en stock")
    
        else:
            messages.error(request, 'No tienes suficiente saldo')

        return redirect('compra_listado')

        
@staff_member_required
def informes(request):
    
    topclients = Usuario.objects.annotate(importe_compras = Sum('compra__importe'), total_compras=Count('compra')).order_by('-importe_compras')[:10]
    topProductos = Producto.objects.annotate(total_vendidos = Sum('compra__unidades')).order_by('-total_vendidos')[:10]
    return render(request, 'tienda/informes.html',{'topclients':topclients, 'topProductos':topProductos})


class PerfilView(LoginRequiredMixin, ListView):
    model = Compra
    paginate_by= 4
    template_name='tienda/perfil.html'

    def get_queryset(self):
        query = super().get_queryset()
        query = query.filter(usuario = self.request.user)
        return query

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from ..models import Material
from ..decorators import check_auth_tokens
from django.utils.decorators import method_decorator

class MaterialView(View):
    template_name = 'materials.html'
    detail_template = 'material_detail.html'  # Шаблон для детального просмотра
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, material_id=None, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        # Проверка авторизации
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        # Базовый контекст с информацией о пользователе
        context = {
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        
        # Если указан ID материала, показываем детальную страницу
        if material_id:
            material = get_object_or_404(Material, id=material_id)
            context.update({
                'material': material,
                'title': material.title
            })
            return render(request, self.detail_template, context)
        
        # Иначе показываем список всех материалов
        materials = Material.objects.all()
        context.update({
            'materials': materials,
            'title': 'Материалы'
        })
        return render(request, self.template_name, context)

    def post(self, request, material_id=None, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        # Обработка действия удаления материала
        if 'delete_material' in request.POST:
            material_id = material_id or request.POST.get('material_id')
            if material_id:
                material = get_object_or_404(Material, id=material_id)
                # Удалять могут только суперпользователи
                if user_info.get('is_superuser', False):
                    material.delete()
                    messages.success(request, 'Материал успешно удален.')
                else:
                    messages.error(request, 'У вас нет прав для удаления этого материала.')
            return redirect('materials') 
# views_prueba.py

def funcion_simple(request):
    """
    Complejidad esperada: 2
    Comportamiento: Silencio. Pasa la validación sin imprimir nada.
    Desglose: 1 (base) + 1 (if) = 2.
    """
    if request.method == 'POST':
        return "Guardado"
    return "Formulario"


def funcion_mediana(usuario):
    """
    Complejidad esperada: 11
    Comportamiento: Advertencia (⚠️ AVISO). Está en el rango de (Límite - 5).
    Desglose: 
    1 (base) + 1(if) + 1(if) + 1(elif) + 1(for) + 1(if) + 1(elif) + 
    1(elif) + 1(and) + 1(except) + 1(if) = 11.
    """
    nivel = 0
    if usuario.is_authenticated:
        if usuario.is_staff:
            nivel = 1
        elif usuario.is_superuser:
            nivel = 2
            
    for permiso in usuario.permisos:
        if permiso == 'leer':
            pass
        elif permiso == 'escribir':
            pass
        elif permiso == 'borrar' and usuario.is_admin:
            pass
            
    try:
        procesar(usuario)
    except Exception:
        if usuario.reintentos > 0:
            pass
            
    return nivel


def funcion_compleja(request):
    """
    Complejidad esperada: 17
    Comportamiento: Fallo (❌ FALLO). Supera el límite de 15. Rompe la Pull Request.
    Desglose: 
    1 (base) + 1(if) + 1(if) + 1(if) + 1(and) + 1(for) + 1(if) + 1(elif) + 
    1(elif) + 1(or) + 1(elif) + 1(if) + 1(elif) + 1(elif) + 1(for) + 
    1(if) + 1(if) = 17.
    """
    if request.method == 'GET':
        if request.GET.get('filtro1'):
            if request.GET.get('filtro2') and request.GET.get('filtro3'):
                for item in request.items:
                    if item.valido:
                        pass
                    elif item.pendiente:
                        pass
                    elif item.rechazado or item.expirado:
                        pass
        elif request.GET.get('orden'):
            if request.GET['orden'] == 'asc':
                pass
            elif request.GET['orden'] == 'desc':
                pass
    elif request.method == 'POST':
        for x in range(10):
            if x == 5:
                continue
            if x == 9:
                break
                
    return "Fin"
import os
import sys, ast

class AnalizadorComplejidad(ast.NodeVisitor):
    def __init__(self):
        self.complejidad = 1

    def visit_If(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complejidad += len(node.values) - 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_match_case(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complejidad += 1
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complejidad += 1
        self.generic_visit(node)

def calcular(codigo_fuente: str) -> int:
    """Parsea el código y devuelve su complejidad ciclomática."""
    try:
        arbol = ast.parse(codigo_fuente)
    except SyntaxError:
        return 0 
        
    visitante = AnalizadorComplejidad()
    visitante.visit(arbol)
    return visitante.complejidad

def analizar_proyecto(ruta_directorio: str, limite_complejidad: int = 15):
    exito = True
    
    for raiz, _, archivos in os.walk(ruta_directorio):
        if 'migrations' in raiz or 'venv' in raiz or '__pycache__' in raiz or '.git' in raiz:
            continue
            
        for archivo in archivos:
            if '__init__' in archivo:
                continue
            if archivo.endswith('.py'):
                ruta_completa = os.path.join(raiz, archivo)
                
                with open(ruta_completa, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    
                complejidad = calcular(contenido)
                
                if complejidad > limite_complejidad:
                    print(f"❌ PELIGRO: {ruta_completa} tiene complejidad {complejidad}")
                    exito = False
                elif complejidad >= limite_complejidad - 5:
                    print(f"⚠️ AVISO: {ruta_completa} tiene complejidad {complejidad}")
                else:
                    # Añade esto para ver el escaneo completo
                    print(f"✅ OK: {ruta_completa} (Complejidad: {complejidad})")    
    if not exito:
        sys.exit(1)
    else:
        print("✅ Análisis completado. El código cumple con los estándares.")
        sys.exit(0)

if __name__ == "__main__":
    analizar_proyecto('./')
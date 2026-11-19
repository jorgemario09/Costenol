"""
Intérprete del lenguaje Costeñol.
Ejecuta el AST generado por el parser.
"""
import re

class CostenolError(Exception):
    """Error en tiempo de ejecución del programa Costeñol."""
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(message)


class CostenolInterpreter:
    def __init__(self, ast, symbol_table, input_func=None, output_func=None):
        self.ast = ast
        self.variables = {var: None for var in symbol_table}
        self.types = dict(symbol_table)
        self.output_func = output_func or print
        self.input_func = input_func
        self.runtime_errors = []
        self._stopped = False
        self._max_iterations = 10000

    def stop(self):
        self._stopped = True

    def run(self):
        self._stopped = False
        self.runtime_errors = []
        try:
            for statement in self.ast:
                if self._stopped: 
                    raise Exception("CANCELADO_POR_USUARIO")
                self.execute(statement)
        except CostenolError as e:
            self.runtime_errors.append(str(e))
            self.output_func(f"[COMETISTES ERRORES CUADRO] {e.message}")
        except Exception as e:
            if str(e) == "CANCELADO_POR_USUARIO":
                self.output_func("\n[AVISO] Cancelaste la jugada. Ejecución abortada, llave.")
            else:
                self.runtime_errors.append(f"Error interno: {str(e)}")
                self.output_func(f"[ERROR DEL SISTEMA] {str(e)}")

    def execute(self, stmt):
        if self._stopped: 
            raise Exception("CANCELADO_POR_USUARIO")
            
        if not stmt: return
        st_type = stmt[0]

        if st_type == 'DECL':
            var_name = stmt[1]
            var_type = stmt[2]
            if var_name not in self.variables:
                self.variables[var_name] = self._default_value(var_type)

        elif st_type == 'ASSIGN_CAPTURA':
            self._execute_captura(stmt)

        elif st_type == 'ASSIGN_EXPR':
            var_name = stmt[1]
            expr_node = stmt[2]
            line = stmt[3] if len(stmt) > 3 else None
            try:
                val = self.eval_expr(expr_node)
                if var_name in self.types:
                    val = self._coerce_value(val, self.types[var_name], line)
                self.variables[var_name] = val
            except CostenolError:
                raise
            except Exception as e:
                if str(e) == "CANCELADO_POR_USUARIO": raise
                raise CostenolError(f"¡Tronco e' problema evaluando '{var_name}'!: {str(e)}", line)

        elif st_type == 'MENSAJE':
            expr_node = stmt[1]
            val = self.eval_expr(expr_node)
            if val is None: val = ""
            self.output_func(str(val))

        elif st_type == 'IF':
            cond_node = stmt[1]
            then_branch = stmt[2]
            else_branch = stmt[3]
            cond_val = self.eval_expr(cond_node)
            if bool(cond_val):
                for s in then_branch:
                    if self._stopped: raise Exception("CANCELADO_POR_USUARIO")
                    self.execute(s)
            else:
                for s in else_branch:
                    if self._stopped: raise Exception("CANCELADO_POR_USUARIO")
                    self.execute(s)

        elif st_type == 'WHILE':
            cond_node = stmt[1]
            body = stmt[2]
            line = stmt[3] if len(stmt) > 3 else None
            iterations = 0
            while not self._stopped:
                if self._stopped: raise Exception("CANCELADO_POR_USUARIO")
                
                cond_val = self.eval_expr(cond_node)
                if not bool(cond_val): break
                for s in body:
                    if self._stopped: raise Exception("CANCELADO_POR_USUARIO")
                    self.execute(s)
                iterations += 1
                if iterations >= self._max_iterations:
                    raise CostenolError(
                        f"¡Uy zona! Te quedaste patinando en un bucle infinito (van más de {self._max_iterations} vueltas).",
                        line
                    )
            if self._stopped: raise Exception("CANCELADO_POR_USUARIO")

    def _execute_captura(self, stmt):
        var_name = stmt[1]
        cap_type = stmt[2]
        line = stmt[3] if len(stmt) > 3 else None
        
        # 1 intento inicial + 1 reintento (2 intentos en total)
        max_intentos = 2

        for intento in range(max_intentos):
            if self._stopped: raise Exception("CANCELADO_POR_USUARIO")

            if self.input_func:
                val_in = self.input_func(f"Manda el {cap_type} pa' [{var_name}]: ")
            else:
                val_in = input(f"Manda el {cap_type} pa' [{var_name}]: ")

            if val_in is None:
                self.stop()
                raise Exception("CANCELADO_POR_USUARIO")

            try:
                valor = self._cast_input(val_in, cap_type)
                self.variables[var_name] = valor
                return
            except ValueError as e:
                remaining = max_intentos - intento - 1
                if remaining > 0:
                    self.output_func(f"¡Eche, pilas! Eso no es un '{cap_type}' válido. Mételo bien de nuevo, te queda un solo cartucho.")
                else:
                    # Mensaje exacto exigido en puro costeño
                    raise CostenolError(f"¡Ombe estás metiendo mal los datos !", line)

    def _cast_input(self, val_str, data_type):
        val_clean = val_str.strip()
        if not val_clean: raise ValueError("Valor vacío")

        if data_type == 'Entero':
            if not re.match(r'^-?\d+$', val_clean):
                raise ValueError(f"'{val_clean}' no cuadra como entero.")
            return int(val_clean)
            
        elif data_type == 'Real':
            val_converted = val_clean.replace(',', '.')
            if not re.match(r'^-?\d+(\.\d+)?$', val_converted):
                raise ValueError(f"'{val_clean}' no tiene pinta de real.")
            return float(val_converted)
            
        elif data_type == 'Logico':
            if val_clean in ('Verdadero', 'verdadero', 'True', 'true'): return True
            elif val_clean in ('Falso', 'falso', 'False', 'false'): return False
            else: raise ValueError(f"'{val_clean}' no sirve, usa 'Verdadero' o 'Falso'.")
            
        elif data_type == 'Texto':
            # Si el tipo declarado es Texto, prohibimos que metan números puros
            if re.match(r'^-?\d+([,\.]\d+)?$', val_clean):
                raise ValueError(f"El campo es de tipo Texto, no metan números pelados.")
            return val_clean
            
        return val_clean

    def _coerce_value(self, value, target_type, line=None):
        if value is None: return self._default_value(target_type)
        if target_type == 'Entero':
            if isinstance(value, int): return value
            if isinstance(value, float): return int(value)
            if isinstance(value, bool): return 1 if value else 0
        elif target_type == 'Real':
            if isinstance(value, (int, float)): return float(value)
        elif target_type == 'Logico':
            if isinstance(value, bool): return value
        elif target_type == 'Texto':
            return str(value)
        return value

    def _default_value(self, var_type):
        defaults = {'Entero': 0, 'Real': 0.0, 'Logico': False, 'Texto': ""}
        return defaults.get(var_type)

    def eval_expr(self, node):
        if node is None: return None
        node_type = node[0]
        
        if self._stopped: raise Exception("CANCELADO_POR_USUARIO")

        if node_type == 'STRING': return node[1]
        elif node_type in ('INT', 'REAL', 'BOOL'): return node[1]
        elif node_type == 'VAR':
            var_name = node[1]
            if var_name in self.variables:
                val = self.variables[var_name]
                if val is None: return self._default_value(self.types.get(var_name, 'Texto'))
                return val
            return None
        elif node_type == 'UNARY_NEG':
            operand = self.eval_expr(node[1])
            if isinstance(operand, (int, float)): return -operand
            raise CostenolError("¡Mandas cáscara! No se le puede sacar el negativo a un texto.")
        elif node_type == 'BINOP':
            return self._eval_binop(node)
        return None

    def _eval_binop(self, node):
        op = node[1]
        left_val = self.eval_expr(node[2])
        right_val = self.eval_expr(node[3])

        if op == '+':
            if isinstance(left_val, str) or isinstance(right_val, str):
                return str(left_val if left_val is not None else "") + str(right_val if right_val is not None else "")
            if left_val is None or right_val is None: return 0
            return left_val + right_val
        elif op == '-':
            if left_val is None or right_val is None: return 0
            return left_val - right_val
        elif op == '*':
            if left_val is None or right_val is None: return 0
            return left_val * right_val
        elif op == '/':
            if right_val is None or right_val == 0:
                raise CostenolError("¡No joda, cuadro! ¿Dividir por cero? Te pasaste de piña.")
            if left_val is None: return 0
            return left_val / right_val
        elif op == '==': return left_val == right_val
        elif op == '!=': return left_val != right_val
        elif op == '<': return left_val < right_val
        elif op == '>': return left_val > right_val
        elif op == '<=': return left_val <= right_val
        elif op == '>=': return left_val >= right_val

        return None
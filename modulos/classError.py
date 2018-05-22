class Error(Exception):
    """Clase base para excepciones en el módulo."""
    pass

class GenericError(Error):
    """Excepción lanzada por errores en las entradas.

    Atributos:
        expresion -- expresión de entrada en la que ocurre el error
        mensaje -- explicación del error
    """

    def __init__(self, expresion, mensaje):
        self.number = 109
        self.expresion = expresion
        self.mensaje = mensaje
        super(GenericError, self).__init__(self.mensaje)

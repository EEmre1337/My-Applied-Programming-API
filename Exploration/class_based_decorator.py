"""
Exploration für Tag 6: Klassen-basierter Decorator
Hier testen wir das Konzept des Callcounters mit __call__.
"""

from functools import wraps

class CallCounter:
    """
    Ein klassenbasierter Decorator, der mitzählt, 
    wie oft eine Funktion aufgerufen wurde.
    """
    def __init__(self, func):
        self.func = func
        self.count = 0
        wraps(func)(self) # Bewahrt den Namen und Docstring der Originalfunktion

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"[CallCounter] Die Funktion '{self.func.__name__}' wurde {self.count} Mal aufgerufen.")
        return self.func(*args, **kwargs)

# === Test des Decorators ===

@CallCounter
def test_funktion(name: str):
    print(f"Hallo {name}!")

if __name__ == "__main__":
    print("--- Starte Decorator Test ---")
    test_funktion("Emre")
    test_funktion("Martin")
    test_funktion("FastAPI")
    print(f"Finaler Counter-Wert: {test_funktion.count}")
"""
Krótki skrypt testowy uruchamiający `data_generator.generate_corpus` i wypisujący wynik.
Skrypt łapie wyjątki i wypisuje stack trace dla debugowania środowiska.
"""
import traceback

print("RUNNING run_test.py")
try:
    import data_generator as dg
    print("Imported data_generator OK")
    c = dg.generate_corpus(n_per_template=2)
    print("GENERATED: train=", len(c.train), "dev=", len(c.dev), "test=", len(c.test))
except Exception:
    print("EXCEPTION DURING GENERATION:")
    traceback.print_exc()

try:
    import plotly
    import plotly.express as px
    print(f"✅ Plotly {plotly.__version__} is installed and working.")
except ImportError as e:
    print(f"❌ Error: {e}")

try:
    import peewee
    print(f"✅ Peewee {peewee.__version__} is installed and working.")
except ImportError as e:
    print(f"❌ Error Peewee: {e}")

from app.database import engine
from sqlalchemy import text

conn = engine.connect()
result = conn.execute(text("SELECT * FROM pg_extension WHERE extname='vector';"))
print(list(result))
conn.close()
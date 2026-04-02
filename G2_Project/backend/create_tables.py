<<<<<<< HEAD
from db import engine
from models import Base

Base.metadata.create_all(bind=engine)

=======
from db import engine
from models import Base

Base.metadata.create_all(bind=engine)

>>>>>>> 078f103c00d85cbbec5ede50581083ac1663ff12
print("Tables created successfully.")
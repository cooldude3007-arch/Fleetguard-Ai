from app.database import Base, engine

from app import models


def create_database():
    Base.metadata.create_all(bind=engine)
    print("FleetGuard database created successfully.")


if __name__ == "__main__":
    create_database()
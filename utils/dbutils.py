from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

# Define the base class for declarative class 
Base = declarative_base()

# Define the UploadedFile 
class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True)
    file_path = Column(String)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    email = Column(String)

    def __repr__(self):
        return f"<UploadedFile(filename='{self.filename}', file_path='{self.file_path}', email='{self.email}')>"

# Create an engine that stores data in the local directory's test.db file
engine = create_engine('sqlite:///test.db')

# Create all tables in the database that are defined by Base's subclasses
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Session
session = Session()

# Example CRUD operations

# Create: Insert a new user
new_user = User(name='Alice', age=30)
session.add(new_user)
session.commit()

# Read: Query all users
users = session.query(User).all()
print("All Users:")
print(users)

# Update: Update the age of the user
alice = session.query(User).filter_by(name='Alice').first()
if alice:
    alice.age = 31
    session.commit()
    print("Updated Alice's age to 31")

# Delete: Delete the user
if alice:
    session.delete(alice)
    session.commit()
    print("Deleted Alice")

# Close the session
session.close()

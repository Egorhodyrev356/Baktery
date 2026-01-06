from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///books.db')
Base = declarative_base()


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)



Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

book1 = Book(title="Гарри Поттер", author="Дж.К Роулинг")
book2 = Book(title="Властелин колец", author="Джон Толкин")
book3 = Book(title='1984', author='Джордж Оруэлл')

session.add(book1)
session.add(book2)
session.add(book3)
session.commit()

for book in session.query(Book).all():
    print(f"{book.title} – {book.author}")
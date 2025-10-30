from pyormEngine.orm import BaseModel, PRIMARYKEY, FOREIGNKEY,MetaConstruct

# -------------------------------
#  MODELS
# -------------------------------

class Author(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    country: str

    def __repr__(self):
        return f"Author(id={getattr(self, 'id', None)}, name={self.name}, country={self.country})"


class Publisher(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    location: str

    def __repr__(self):
        return f"Publisher(id={getattr(self, 'id', None)}, name={self.name}, location={self.location})"


class Book(BaseModel):
    id: PRIMARYKEY[int]
    title: str
    genre: str
    author: FOREIGNKEY[Author]
    publisher: FOREIGNKEY[Publisher]
    pages: int

    def __repr__(self):
        return (
            f"Book(id={getattr(self, 'id', None)}, "
            f"title={self.title}, genre={self.genre}, "
            f"author={self.author}, publisher={self.publisher}, "
            f"pages={self.pages})"
        )


# -------------------------------
#  DUMMY DATA CREATION (USING .id for FK)
# -------------------------------

class Ret(MetaConstruct):
    id: int 
    name: str

    def __repr__(self):
        return f"Ret {self.id} -- {self.name}"


if __name__ == "__main__":
    Author.create_table()
    Publisher.create_table()
    Book.create_table()

    q = (
        Book.query().select(Book.id,Publisher.name).filter((Publisher.id == 4) & (Author.id == 4)).fill_type(Ret)
    )
    
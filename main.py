from pyormEngine.orm import BaseModel, PRIMARYKEY, FOREIGNKEY, QueryChainer

class User(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    country: str

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, country={self.country})"


class PlayList(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    user: FOREIGNKEY[User]

    def __repr__(self):
        return f"PlayList(id={self.id}, name={self.name}, user={self.user})"


class Song(BaseModel):
    id: PRIMARYKEY[int]
    title: str
    genre: str
    duration: int  # in seconds
    playlist: FOREIGNKEY[PlayList]

    def __repr__(self):
        return f"Song(id={self.id}, title={self.title}, genre={self.genre}, playlist={self.playlist})"





from pyormEngine.orm import BaseModel, PRIMARYKEY, FOREIGNKEY


# -------------------------------
#  MODELS
# -------------------------------

class User(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    country: str

    def __repr__(self):
        return f"User(id={getattr(self, 'id', None)}, name={self.name}, country={self.country})"


class PlayList(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    user: FOREIGNKEY[User]

    def __repr__(self):
        return f"PlayList(id={getattr(self, 'id', None)}, name={self.name}, user={self.user})"


class Song(BaseModel):
    id: PRIMARYKEY[int]
    title: str
    genre: str
    duration: int
    playlist: FOREIGNKEY[PlayList]

    def __repr__(self):
        return f"Song(id={getattr(self, 'id', None)}, title={self.title}, genre={self.genre}, playlist={self.playlist})"


# -------------------------------
#  DUMMY DATA CREATION
# -------------------------------

if __name__ == "__main__":
    User.create_table()
    PlayList.create_table()

    query = (
        PlayList.query()
        .filter(User.id == PlayList.user)  
    )

    print(query.toSql())

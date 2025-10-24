from orm import BaseModel, FOREIGNKEY, PRIMARYKEY, QueryChainer

class User(BaseModel):
    id: PRIMARYKEY[int]
    name: str

    def __repr__(self): 
        return f"User(id={self.id}, name={self.name})"

class PlayList(BaseModel):
    id: PRIMARYKEY[int]
    name: str
    songs: str
    user: FOREIGNKEY[User]

    def __repr__(self):
        return f"PlayList(id={self.id}, name={self.name}, user={self.user})"


if __name__ == '__main__':
    User.create_table()
    PlayList.create_table()

    # u1 = User(name="Alice").save()
    # u2 = User(name="Bob").save()
    # u3 = User(name="Charlie").save()

    # PlayList(name="Chill Beats", songs="song1,song2,song3", user=1).save()
    # PlayList(name="Workout Mix", songs="song4,song5", user=1).save()
    # PlayList(name="Rock Classics", songs="song6,song7", user=2).save()
    # PlayList(name="Pop Hits", songs="song8,song9", user=3).save()
    # PlayList(name="Lo-fi Mix", songs="song20,song11", user=2).save()


    # f = PlayList.filter((User.id == 1) & (PlayList.name=="Chill Beats"))
    # print(f)

    print(PlayList.query().select(PlayList.name).filter(name="Lo-fi Mix").limit(1).all())
    
from orm import BaseModel, FOREIGNKEY, PRIMARYKEY



class PlayList(BaseModel):
    id: PRIMARYKEY[int]
    name: str 
    songs: str 


class User(BaseModel):
    id: PRIMARYKEY[int]
    name: str 
    lists: FOREIGNKEY[PlayList]


if __name__ == '__main__':
    # User.create_table()
    # PlayList.create_table()
    # User.create_table()
    # print(PlayList.id)
    # print(PlayList.id)
    # User.filter(PlayList.id == 1)
    # pass
    User.create_table()
    User.filter(PlayList.id == 1)
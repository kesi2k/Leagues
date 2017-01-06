# These allow ORM maping to the DB
from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

## Allows creatiion of foreign key relationships
from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

# Make an instance of the declarative_base we just imported
Base = declarative_base()

class User(Base):
  __tablename__= 'user'
  id = Column(Integer, primary_key=True)
  name = Column(String(250), nullable=False)
  email= Column(String(250), nullable=False)
  picture = Column(String(250))
  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return{
           'name':self.name,
           'id'  :self.id,
          }



class League(Base):
    # Setting name of table
    __tablename__ = 'league'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



class Team(Base):
    ## Variable setting for table name
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    pts = Column(String(80))
    win = Column(String(80))
    lose = Column(String(80))
    draw = Column(String(80))
    league_id = Column(Integer, ForeignKey('league.id'))
    league = relationship(League)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
               'name'   :self.name,
               'points' :self.pts,
               'id'     :self.id,
               'league_id':self.league_id,
               'userID':self.user_id
       }




class Players(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    position = Column(String(80))
    league_id = Column(Integer, ForeignKey('league.id'))
    league = relationship(League)
    team_id = Column(Integer, ForeignKey('team.id'))
    team = relationship(Team)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
               'name'    :self.name,
               'position':self.position,
               'id' :self.id,
               'team_id':self.team_id,
               'league_id':self.league_id,
       }




## Create instance of imported create_engine and point to DB
# engine = create_engine('sqlite:///restaurantmenu.db')
engine = create_engine('sqlite:///soccerleagues.db')

## Goes into DB and creates tables based on the classes we created
Base.metadata.create_all(engine)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, League, Team, Players

engine = create_engine('sqlite:///soccerleagues.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create user
User1 = User(name="Kesi Hamilton", email="mhamilton868@gmail.com",
             picture='https://pbs.twimg.com/profile_images/448598179924021248/emFJtE02.jpeg')
session.add(User1)
session.commit()


#Leagues containing Teams. Teams have a list of players.
league1 = League(user_id=1, name="League 1")

session.add(league1)
session.commit()


# Team 1 Chelsea
Team1 = Team(user_id=1, name="Chelsea", pts="0", win="0", lose="0", draw="0", league=league1)

session.add(Team1)
session.commit()



# Chelsea Players
Player1 = Players(user_id=1, name="Diego Costa", position="F", team=Team1, league_id=1)
session.add(Player1)
session.commit()

Player2 = Players(user_id=1, name="Cesc Fabregas", position="M", team=Team1, league_id=1)
session.add(Player2)
session.commit()


# Team 2 Man City
Team2 = Team(user_id=1, name="Man City", pts="0", win="0", lose="0", draw="0", league=league1)

session.add(Team2)
session.commit()



# Man City Players
Player1 = Players(user_id=1, name="Kolo Toure", position="M", team=Team2, league_id=1)
session.add(Player1)
session.commit()

Player2 = Players(user_id=1, name="Bacary Sagna", position="D", team=Team2, league_id=1)
session.add(Player2)
session.commit()




# League 2
league2 = League(user_id=1, name="League 2")

session.add(league2)
session.commit()


# Team 1 Leeds Utd
Team1 = Team(user_id=1, name="Leeds Utd", pts="0", win="0", lose="0", draw="0", league=league2)

session.add(Team1)
session.commit()



# Leeds Players
Player1 = Players(user_id=1, name="Harry Kewell", position="F", team=Team1, league_id=2)
session.add(Player1)
session.commit()

Player2 = Players(user_id=1, name="Rio Ferdinand", position="D", team=Team1, league_id=2)
session.add(Player2)
session.commit()


# Team 2 Newcastle Utd
Team2 = Team(user_id=1, name="Newcastle Utd", pts="0", win="0", lose="0", draw="0", league=league2)

session.add(Team2)
session.commit()



# Leeds Players
Player1 = Players(user_id=1, name="Alan Shearer", position="F", team=Team2, league_id=2)
session.add(Player1)
session.commit()

Player2 = Players(user_id=1, name="Garry Glascgoine", position="F", team=Team2, league_id=2)
session.add(Player2)
session.commit()






print "added Info!"
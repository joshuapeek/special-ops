from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# MVP table
class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(500))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description
        }

# MVP table
class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(500))
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id
        }

# MVP table
class Feature(Base):
    __tablename__ = 'feature'
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(String(500))
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id
        }

# MVP table
class Story(Base):
    __tablename__ = 'story'
    id = Column(Integer, primary_key=True)
    scope = Column(String(25), nullable=False)
    want = Column(String(500))
    why = Column(String(500))
    role_id = Column(Integer, ForeignKey('role.id'))
    role = relationship(Role)
    feature_id = Column(Integer, ForeignKey('feature.id'))
    feature = relationship(Feature)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'scope': self.scope,
            'want': self.want,
            'why': self.why,
            'role_id': self.role_id,
            'feature_id': self.feature_id
        }

engine = create_engine('sqlite:///special-ops.db')
Base.metadata.create_all(engine)

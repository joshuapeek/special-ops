from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from database_setup import Project, Role
from database_setup import Feature, Story, Base
from sqlalchemy.pool import StaticPool
from flask import session as login_session
import random
import string
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# set shorthand variable for connecting to database
engine = create_engine('sqlite:///special-ops.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# BASIC READ PAGES

# Super Dash
# displays all Projects in Bear Raptor
@app.route('/')
def mainPage():
    projects = session.query(Project).all()
    return render_template('main.html', projects=projects)

# Project Dash
# displays all Roles and Features in selected Project
@app.route('/project/<int:project_id>')
def projectDash(project_id):
    project = session.query(Project).filter_by(id=project_id).one()
    roles = session.query(Role).filter_by(project_id=project_id).all()
    features = session.query(Feature).filter_by(project_id=project_id).all()
    featureids = []
    # begin with assumption that project is in scope
    scope = 'in'
    for i in features:
        # compile list of feature ids in project
        featureids.append(i.id)
        # ...while checking for out-of-scope features in project
        # ......if any are found, change scope to 'out'
        if i.scope == 'out':
            scope = 'out'
    stories = session.query(Story).filter(Story.feature_id.in_(featureids)).all()
    # if project still in scope,
    # ...check for out-of-scope stories within in each feature
    # ......if any are found, change scope to 'contains'
    if scope != 'out':
        for i in stories:
            if i.scope == 'out':
                scope = 'contains'
    return render_template('project-dash.html', project=project, roles=roles,
                            features=features, scope=scope)

# Feature Page
# displays all Roles and Features in selected Project
@app.route('/project/<int:project_id>/feature/<int:feature_id>')
def featurePage(project_id, feature_id):
    project = session.query(Project).filter_by(id=project_id).one()
    roles = session.query(Role).filter_by(project_id=project_id).all()
    feature = session.query(Feature).filter_by(id=feature_id).one()
    features = session.query(Feature).filter_by(project_id=project_id).all()
    featureids = []
    for i in features:
        # compile list of feature ids in project
        if i.id == feature.id:
            featureids.append(i.id)
    stories = session.query(Story).filter(Story.feature_id.in_(featureids)).all()
    scope = feature.scope
    if scope == 'in':
        for i in stories:
            if i.scope == 'out':
                scope = 'contains'
    return render_template('feature-page.html', project=project, roles=roles,
                            feature=feature, features=features,
                            stories=stories, scope=scope)

# Role Testing Page
# displays all Roles and Features in selected Project
@app.route('/project/<int:project_id>/role/<int:role_id>')
def roleTestPage(project_id, role_id):
    project = session.query(Project).filter_by(id=project_id).one()
    roles = session.query(Role).filter_by(project_id=project_id).all()
    features = session.query(Feature).filter_by(project_id=project_id).all()
    stories = session.query(Story).filter_by(role_id=role_id).all()
    return render_template('role-test-page.html', project=project, roles=roles,
                            features=features, stories=stories)


# JSON Pages---------------------------

# JSON Super page:
# displays all projects in db, serialized
@app.route('/super/JSON')
def superJSON():
    projects = session.query(Project).all()
    return jsonify(Projects=[i.serialize for i in projects])

# JSON Project page:
# displays a set project's details, serialized
@app.route('/projectdetails/<int:project_id>/JSON')
def projectJSON(project_id):
    project = session.query(Project).filter_by(id=project_id).one()
    return jsonify(Project=project.serialize)

# JSON Roles page:
# displays a set project's roles, serialized
@app.route('/allroles/<int:project_id>/JSON')
def rolesJSON(project_id):
    roles = session.query(Role).filter_by(project_id=project_id).all()
    return jsonify(Roles=[i.serialize for i in roles])

# JSON Features page:
# displays a set project's features, serialized
@app.route('/allfeatures/<int:project_id>/JSON')
def featuresJSON(project_id):
    features = session.query(Feature).filter_by(project_id=project_id).all()
    return jsonify(Features=[i.serialize for i in features])

# JSON Stories page:
# displays a set feature's stories, serialized
@app.route('/featurestories/<int:feature_id>/JSON')
def storiesJSON(feature_id):
    stories = session.query(Story).filter_by(feature_id=feature_id).all()
    return jsonify(Stories=[i.serialize for i in stories])


if __name__ == '__main__':
    app.secret_key = 'supersecretkey'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

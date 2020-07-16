from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from database_setup import Project, Role, AcceptanceCriteria
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

# BASIC READ PAGES---------------------

# Super Dash
# displays all Projects in Bear Raptor
@app.route('/')
def mainPage():
    projects = session.query(Project).all()
    flash("Welcome")
    return render_template('main.html', projects=projects)

# Project Dash
# displays all Roles and Features in selected Project
@app.route('/project?<int:project_id>')
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
                            features=features, scope=scope, stories=stories)

# Feature Page
# displays all Roles and Features in selected Project
@app.route('/project?<int:project_id>&feature?<int:feature_id>')
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
    storyids = []
    for i in stories:
        # compile list of story ids in stories
        storyids.append(i.id)
    ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id.in_(storyids)).all()
    scope = feature.scope
    if scope == 'in':
        for i in stories:
            if i.scope == 'out':
                scope = 'contains'
    return render_template('feature-page.html', project=project, roles=roles,
                            feature=feature, features=features,
                            stories=stories, ac=ac, scope=scope)

# Role Testing Page
# displays all Roles and Features in selected Project
@app.route('/project?<int:project_id>&role?<int:role_id>&testing')
def roleTestPage(project_id, role_id):
    project = session.query(Project).filter_by(id=project_id).one()
    roles = session.query(Role).filter_by(project_id=project_id).all()
    features = session.query(Feature).filter_by(project_id=project_id).all()
    stories = session.query(Story).filter_by(role_id=role_id).all()
    return render_template('role-test-page.html', project=project, roles=roles,
                            features=features, stories=stories)


# CREATE Pages-------------------------

# Create Project Page
# requires no data, just creates a project
@app.route('/createproject', methods=['GET', 'POST'])
def createProject():
    if request.method == 'POST':
        createProject = Project(title=request.form['title'],
                        shortname=request.form['shortname'],
                        description=request.form['description'],
                        status=request.form['status'])
        session.add(createProject)
        session.commit()
        session.refresh(createProject)
        flash("New Project Created!")
        return redirect(url_for('mainPage'))
    else:
        return redirect(url_for('mainPage'))

# Create Feature Page
# receives data, creates feature, returns to project page
@app.route('/project?<int:project_id>&createfeature', methods=['GET', 'POST'])
def createFeature(project_id):
    project = session.query(Project).filter_by(id=project_id).one()
    if request.method == 'POST':
        createFeature = Feature(title=request.form['title'],
                        shortname=request.form['shortname'],
                        description=request.form['description'],
                        scope=request.form['scope'],
                        project_id=project.id)
        session.add(createFeature)
        session.commit()
        session.refresh(createFeature)
        flash("New Feature Created!")
        return redirect(url_for('projectDash', project_id=project.id))
    else:
        return redirect(url_for('projectDash', project_id=project.id))

# Create Role Page
# receives data, creates feature, returns to project page
@app.route('/project?<int:project_id>&createRole', methods=['GET', 'POST'])
def createRole(project_id):
    project = session.query(Project).filter_by(id=project_id).one()
    if request.method == 'POST':
        createRole = Role(title=request.form['title'],
                        description=request.form['description'],
                        project_id=project.id)
        session.add(createRole)
        session.commit()
        session.refresh(createRole)
        flash("New Role Created!")
        return redirect(url_for('projectDash', project_id=project.id))
    else:
        return redirect(url_for('projectDash', project_id=project.id))

# Create Story Page
# receives data, creates feature, returns to project page
@app.route('/project?<int:project_id>&feature?<int:feature_id>&createstory', methods=['GET', 'POST'])
def createStory(project_id, feature_id):
    project = session.query(Project).filter_by(id=project_id).one()
    feature = session.query(Feature).filter_by(id=feature_id).one()
    if request.method == 'POST':
        createStory = Story(scope=request.form['scope'],
                        want=request.form['want'],
                        why=request.form['why'],
                        role_id=request.form['role'],
                        feature_id=feature_id)
        session.add(createStory)
        session.commit()
        session.refresh(createStory)
        flash("New Story Created!")
        return redirect(url_for('featurePage', project_id=project.id, feature_id=feature.id))
    else:
        return redirect(url_for('featurePage', project_id=project.id, feature_id=feature.id))


# UPDATE Pages-------------------------

# Update Stories Page
# receives, updates story & acceptance criteria data
@app.route('/project=<int:project_id>&feature?<int:feature_id>&story=<int:story_id>&updatestory', methods=['GET', 'POST'])
def updateStory(project_id, feature_id, story_id):
    project = session.query(Project).filter_by(id=project_id).one()
    feature = session.query(Feature).filter_by(id=feature_id).one()
    story = session.query(Story).filter_by(id=story_id).one()
    ac = session.query(AcceptanceCriteria).filter_by(story_id=story_id).all()
    roles = session.query(Role).filter_by(project_id=project_id).all()
    features = session.query(Feature).filter_by(project_id=project_id).all()
    if request.method == 'POST':
        if request.form['scope']:
            story.scope = request.form['scope'],
            story.want = request.form['want'],
            story.why = request.form['why'],
            story.role = request.form['role']
        session.add(story)
        session.commit()
        session.refresh(story)
        flash("Story Edited Successfully")
        return redirect(url_for('featurePage', project_id=project.id, feature_id=feature.id))
    else:
        return render_template('update-story.html', project=project, roles=roles,
                                feature=feature, story=story, ac=ac, features=features,)


# Delete-Confirm Pages-------------------------

# Delete-Confirm Project
# receives project id, warns deletion removes all ac, stories, and features
# offers confirm or cancel, confirm passes to deletion & cancel returns
@app.route('/project?<int:project_id>&type?<string:type>&typeid?<int:type_id>/confirmdelete')
def confirmDelete(project_id, type, type_id):
    project = session.query(Project).filter_by(id=project_id).one()
    if type == 'Project':
        features = session.query(Feature).filter_by(project_id=project_id).all()
        featureids = []
        featureQuantity = 0
        for i in features:
            # compile list of feature ids in project
            featureids.append(i.id)
            featureQuantity += 1
        stories = session.query(Story).filter(Story.feature_id.in_(featureids)).all()
        storyids = []
        storyQuantity = 0
        for i in stories:
            # compile list of story ids in stories
            storyids.append(i.id)
            storyQuantity += 1
        ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id.in_(storyids)).all()
        acQuantity = 0
        for i in ac:
            acQuantity += 1
        return render_template('delete-confirm.html', project=project,
                                fq=featureQuantity, sq=storyQuantity,
                                acq=acQuantity, type=type, type_id=type_id)

    if type == 'Role':
        role = session.query(Role).filter_by(id=type_id).one()
        return render_template('delete-confirm.html', project=project,
                                type=type, type_id=type_id, role=role)

    if type == 'Feature':
        feature = session.query(Feature).filter_by(id=type_id).one()
        stories = session.query(Story).filter_by(feature_id=feature.id).all()
        storyids = []
        storyQuantity = 0
        for i in stories:
            # compile list of story ids in stories
            storyids.append(i.id)
            storyQuantity += 1
        ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id.in_(storyids)).all()
        acQuantity = 0
        for i in ac:
            acQuantity += 1
        return render_template('delete-confirm.html', project=project,
                                feature=feature, sq=storyQuantity,
                                acq=acQuantity, type=type, type_id=type_id)
    if type == 'Story':
        story = session.query(Story).filter_by(id=type_id).one()
        feature = session.query(Feature).filter(Feature.id(story.feature_id)).one()
        ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id(story.id)).all()
        acQuantity = 0
        for i in ac:
            acQuantity += 1
        return render_template('delete-confirm.html', project=project,
                                story=story, acq=acQuantity, type=type,
                                type_id=type_id)
    else:
        return render_template('project-dash.html', project_id=project.id)

# Delete Pages-------------------------

# receives project id after confirmation, grabs features, stories, ac
# deletes ac, stories, features, and project, returns to main
@app.route('/deletefrom?<int:project_id>/type?<string:type>&typeid?<int:type_id>', methods=['GET', 'POST'])
def deleteAction(project_id, type, type_id):
    if request.method == 'POST':
        project = session.query(Project).filter_by(id=project_id).one()
        if type == 'Project':
            features = session.query(Feature).filter_by(project_id=project_id).all()
            featureids = []
            for i in features:
                # compile list of feature ids in project
                featureids.append(i.id)
            stories = session.query(Story).filter(Story.feature_id.in_(featureids)).all()
            storyids = []
            for i in stories:
                storyids.append(i.id)
            ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id.in_(storyids)).all()
            for i in ac:
                session.delete(i)
            for i in stories:
                session.delete(i)
            for i in features:
                session.delete(i)
            session.delete(project)
            session.commit()
            flash("Project & All Components Removed")
            return redirect(url_for('mainPage'))
        if type == 'Role':
            role = session.query(Role).filter_by(id=type_id).one()
            session.delete(role)
            session.commit()
            return redirect(url_for('projectDash', project_id=project.id))
        if type == 'Feature':
            feature = session.query(Feature).filter_by(id=type_id).one()
            stories = session.query(Story).filter_by(feature_id=feature.id).all()
            storyids = []
            for i in stories:
                storyids.append(i.id)
            ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id.in_(storyids)).all()
            for i in ac:
                session.delete(i)
            for i in stories:
                session.delete(i)
            session.delete(feature)
            session.commit()
            return redirect(url_for('projectDash', project_id=project.id))
        if type == 'Story':
            story = session.query(Story).filter_by(id=type_id).one()
            ac = session.query(AcceptanceCriteria).filter(AcceptanceCriteria.story_id(story.id)).all()
            for i in ac:
                session.delete(i)
            for i in stories:
                session.delete(i)
            session.delete(story)
            session.commit()
            return redirect(url_for('projectDash', project_id=project.id))
        else:
            return redirect(url_for('projectDash', project_id=project.id))

    else:
        return redirect(url_for('projectDash', project_id=project.id))


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
    app.run(host='0.0.0.0', port=5050)

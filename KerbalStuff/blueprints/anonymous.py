from flask import Blueprint, render_template, abort, request, redirect, session, Response
from flask.ext.login import current_user
from sqlalchemy import desc
from KerbalStuff.objects import Featured, BlogPost, Mod, Category, GameVersion
from KerbalStuff.search import search_mods
from KerbalStuff.common import *
from KerbalStuff.config import _cfg

import praw
import math

anonymous = Blueprint('anonymous', __name__, template_folder='../../templates/anonymous')
r = praw.Reddit(user_agent="Kerbal Stuff")
@anonymous.route("/")
def index():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 3, "", "no")[0]
    new = Mod.query.filter(Mod.published).filter(Mod.nsfw != True).order_by(desc(Mod.created)).limit(3)[:3]
    recent = Mod.query.filter(Mod.published).filter(Mod.nsfw != True).order_by(desc(Mod.updated)).limit(3)[:3]
    user_count = User.query.count()
    mod_count = Mod.query.count()
    yours = list()
    if current_user:
        yours = sorted(current_user.following, key=lambda m: m.updated, reverse=True)[:3]
    return render_template("index.html",\
        featured=featured,\
        new=new,\
        top=top,\
        recent=recent,\
        user_count=user_count,\
        mod_count=mod_count,
        yours=yours)

@anonymous.route("/browse")
def browse():
    featured = Featured.query.order_by(desc(Featured.created)).limit(6)[:6]
    top = search_mods("", 1, 6)[:6][0]
    new = Mod.query.filter(Mod.published).order_by(desc(Mod.created)).limit(6)[:6]
    return render_template("browse.html", featured=featured, top=top, new=new)

@anonymous.route("/browse/new")
def browse_new():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.created))
    total_pages = math.ceil(mods.count() / 30)
    page = request.args.get('page')
    if page:
        page = int(page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
    else:
        page = 1
    mods = mods.offset(30 * (page - 1)).limit(30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/new", name="Newest Mods", rss="/browse/new.rss")

@anonymous.route("/browse/new.rss")
def browse_new_rss():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.created))
    mods = mods.limit(30)
    return Response(render_template("rss.xml", mods=mods, title="New mods on Kerbal Stuff",\
            description="The newest mods on Kerbal Stuff", \
            url="/browse/new"), mimetype="text/xml")

@anonymous.route("/browse/updated")
def browse_updated():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.updated))
    total_pages = math.ceil(mods.count() / 30)
    page = request.args.get('page')
    if page:
        page = int(page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
    else:
        page = 1
    mods = mods.offset(30 * (page - 1)).limit(30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/updated", name="Recently Updated Mods", rss="/browse/updated.rss")

@anonymous.route("/browse/updated.rss")
def browse_updated_rss():
    mods = Mod.query.filter(Mod.published).order_by(desc(Mod.updated))
    mods = mods.limit(30)
    return Response(render_template("rss.xml", mods=mods, title="Recently updated on Kerbal Stuff",\
            description="Mods on Kerbal Stuff updated recently", \
            url="/browse/updated"), mimetype="text/xml")

@anonymous.route("/browse/top")
def browse_top():
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 1
    mods, total_pages = search_mods("", page, 30)
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/top", name="Popular Mods")

@anonymous.route("/browse/featured")
def browse_featured():
    mods = Featured.query.order_by(desc(Featured.created))
    total_pages = math.ceil(mods.count() / 30)
    page = request.args.get('page')
    if page:
        page = int(page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
    else:
        page = 1
    if page != 0:
        mods = mods.offset(30 * (page - 1)).limit(30)
    mods = [f.mod for f in mods]
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages,\
            url="/browse/featured", name="Featured Mods", rss="/browse/featured.rss")

@anonymous.route("/browse/featured.rss")
def browse_featured_rss():
    mods = Featured.query.order_by(desc(Featured.created))
    mods = mods.limit(30)
    # Fix dates
    for f in mods:
        f.mod.created = f.created
    mods = [dumb_object(f.mod) for f in mods]
    db.rollback()
    return Response(render_template("rss.xml", mods=mods, title="Featured mods on Kerbal Stuff",\
            description="Featured mods on Kerbal Stuff", \
            url="/browse/featured"), mimetype="text/xml")

@anonymous.route("/about")
def about():
    return render_template("about.html")

@anonymous.route("/markdown")
def markdown_info():
    return render_template("markdown.html")

@anonymous.route("/privacy")
def privacy():
    return render_template("privacy.html")
@anonymous.route("/donating")
def donating():
    return render_template("donating.html")
@anonymous.route("/browse/ProjectM")
def browse_pm():
    return render_template("CSS/ProjectM.html")
@anonymous.route("/browse/Brawl")
def browse_brawl():
    return render_template("CSS/Brawl.html")
@anonymous.route("/browse/Melee")
def browse_melee():
    return render_template("CSS/Melee.html")
@anonymous.route("/mod_manager")
def mod_manager():
    return render_template("modmm.html")
@anonymous.route("/search")
def search():
    query = request.args.get('query')
    category = request.args.get('category')
    nsfw = request.args.get('nsfw')
    game_a = request.args.get('game')
    if(game_a == None):
        game_a = "all"
    if(nsfw == None or nsfw == ""):
        nsfw = "no"
    if not query:
        query = ''
    page = request.args.get('page')
    if page:
        page = int(page)
    else:
        page = 1
    mods, total_pages = search_mods(query, page, 30, category, nsfw, game_a)
    
    return render_template("browse-list.html", mods=mods, page=page, total_pages=total_pages, search=True, query=query, category=category)
@anonymous.route("/search_advanced")
def search_advanced():
    return render_template("search_advanced.html", categories=Category.query, games = GameVersion.query)
@anonymous.route("/c/")
def c():
    s = r.get_subreddit("awwnime").get_hot(limit=212)
    return render_template("c.html", s=s)

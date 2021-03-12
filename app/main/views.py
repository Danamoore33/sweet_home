from flask import url_for,render_template,make_response,flash,redirect,request,current_app
from . import main
from datetime import datetime
from .forms import PostForm,EditProfileForm,CommentForm
from app.models import Post,User,Sex,Permission,Comment
from app import db
from flask_login import login_required,current_user
from app.decorators import permission_required
import re
import random
import os

@main.route('/',methods=['GET','POST'])
def index():
    set_show = False
    if current_user.is_authenticated:
        set_show = bool(request.cookies.get('set_show',''))
    if set_show:
        query = current_user.followed_posts
    else:
        query = Post.query
    page = request.args.get('page',1,type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page=page,per_page=current_app.config['POST_PER_PAGE'],error_out=False)
    posts = pagination.items
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        flash('你的博客 {!s} 发表成功了'.format(form.body.data[:10]+'...'))
        return redirect(url_for('.index'))
    return render_template('index.html',current_time=datetime.utcnow(),form=form,posts=posts,
                           pagination=pagination,set_show=set_show)

@main.route('/comments/<int:post_id>',methods=['GET','POST'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          author=current_user._get_current_object(),
                          post=post)
        db.session.add(comment)
        db.session.commit()
        page = -1
        flash('你的评论发表成功了~')
        return redirect(url_for('.get_post',post_id=post.id))
    page = request.args.get('page',1,type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['COMMENT_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page=page,per_page=current_app.config['COMMENT_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('post.html',posts=[post],form=form,pagination=pagination,comments=comments)

@main.route('/follower_posts')
@login_required
def follower_posts():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('set_show','1',max_age=60*60*24*30)
    return resp

@main.route('/show_all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('set_show','',max_age=60*60*24*30)
    return resp

@main.route('/profile/<username>')
@login_required
def get_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html',user=user)

@main.route('/set_disabled/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE)
def set_disabled(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.get_post',post_id=comment.post_id))

@main.route('/cancel_disabled/<int:comment_id>')
@permission_required(Permission.MODERATE)
@login_required
def cancel_disabled(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.get_post',post_id=comment.post_id))

@main.route('/edit-profile/<username>',methods=['GET','POST'])
@login_required
def edit_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EditProfileForm()
    if form.validate_on_submit():
        user.user = form.name.data
        user.sex = Sex.query.get(form.sex.data)
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('你的个人信息修改成功了')
        return redirect(url_for('.get_user',username=user.username))
    form.name.data = user.user
    form.location.data = user.location
    form.about_me.data = user.about_me
    form.sex.data = user.sex_id
    return render_template('edit_profile.html',form=form)

@main.route('/delete_post/<int:post_id>')
@permission_required(Permission.WRITE)
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('删除成功~~')
    return redirect(url_for('.index'))

@main.route('/upload_photo/<username>',methods=['GET','POST'])
@login_required
def change_photo(username):
    user = User.query.filter_by(username=username).first_or_404()
    if request.method == 'POST':
        img = request.files.get('photo')
        filenameSplit = [f for f in img.filename.split('.')]
        if filenameSplit[-1] not in current_app.config['ALLOW_PHOTO_FMT']:
            flash('不支持的图片格式')
            return redirect(url_for('.get_user',username=user.username))
        photo_name = ''.join(re.findall('\d+',str(datetime.utcnow())))+str(random.randint(0,99))+'.'+filenameSplit[-1]
        _path = current_app.config['ALL_UPLOAD_DIR'] + photo_name
        img.save(_path)
        if user.avatar_hash != current_app.config['BASE_PHOTO_PATH']:
            try:
                os.remove(current_app.config['LOCAL_IMG_PATH']+user.avatar_hash)
            except:
                pass
        user.avatar_hash = current_app.config['UPLOAD_DIR'] + photo_name
        db.session.add(user)
        db.session.commit()
        flash('图片上传成功')
        return redirect(url_for('.get_user',username=user.username))

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('该用户未注册')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注了 {}'.format(user.username))
        return redirect(url_for('.get_user',username=user.username))
    current_user.follow(user)
    db.session.commit()
    return redirect(url_for('.get_user',username=user.username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('该用户未注册')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('你还没有关注 {}'.format(user.username))
        return redirect(url_for('.get_user', username=user.username))
    current_user.unfollow(user)
    db.session.commit()
    return redirect(url_for('.get_user',username=user.username))

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('查无此用户')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followers.paginate(
        page,per_page=current_app.config['FOLLOW_PER_PAGE'],error_out=False)
    follows = [{'user': item.follower,'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html',user=user,title='他(她)的关注',endpoint='.followers',
                           pagination=pagination,follows=follows)

@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('查无此用户')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followed.paginate(
        page,per_page=current_app.config['FOLLOW_PER_PAGE'],error_out=False)
    follows = [{'user': item.followed,'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html',user=user,title='粉丝',endpoint='.followed_by',
                           pagination=pagination,follows=follows)






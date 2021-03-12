from flask_migrate import Migrate
from app import create_app,db
import os
from app.models import User,Role,Permission,Post,Comment

app = create_app(os.environ.get('sweet_home_mode') or 'default')
migrate = Migrate(app,db)

@app.shell_context_processor
def from_models():
    return dict(User=User,Role=Role,Permission=Permission,db=db,Post=Post,Comment=Comment)

@app.cli.command()
def create_photo():
    upload_dir = os.path.exists(app.config['UPLOAD_DIR'])
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

@app.cli.command()
def test():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    app.run()
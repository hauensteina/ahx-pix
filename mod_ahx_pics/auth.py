# /********************************************************************
# Filename: mod_ahx_pics/auth.py
# Author: AHN
# Creation Date: Feb, 2023
# **********************************************************************/
#
# Flask login with postgres
#

from pdb import set_trace as BP
import json
import datetime
from flask_login import UserMixin, current_user
from mod_ahx_pics import pg as db
from mod_ahx_pics import login_manager, bcrypt, AppError, log

class User(UserMixin):
    def __init__( self, login):
        log( f'>>>>> auth:__init__()')
        self.valid = True
        self.id = login.strip().upper()
        self.data = {}
        if not self.read_from_db():
            self.valid = False
            return

    def create_user( self, data, password):
        """ Create User in DB """
        log( f'>>>>> auth:create_user()')
        rows = db.find( 'login', 'username',  self.id)
        if rows:
            raise AppError( f'User {self.id} exists in t_login')
        self.data = data
        self.data['username'] = self.id
        self.data['password'] = bcrypt.generate_password_hash( password).decode('utf-8')
        db.insert( 'login', [self.data]) 
        self.valid = True

    def update_db( self):
        """ Write our data back to the db """
        log( f'>>>>> auth:update_db()')
        db.update_row( 'login', 'username' ,self.id)

    def read_from_db( self):
        """ Read our data from the db """
        log( f'>>>>> auth:read_from_db()')
        rows = db.find( 'login', 'username', self.id)
        if not rows: return False
        row = rows[0]
        self.data.update( row)
        return True

    def password_matches( self, password):
        """ Check password """
        log( f'>>>>> auth:password_matches()')
        t0 = datetime.datetime.now()
        good = bcrypt.check_password_hash( self.data['password'], password)
        return good

    def set_password( self, password):
        """ Update password """
        log( f'>>>>> auth:set_password()')
        hashed_password = bcrypt.generate_password_hash( password).decode('utf-8')
        self.data['password'] = hashed_password
        self.update_db()

# flask_login needs this callback
@login_manager.user_loader
def load_user( login):
    user = User( login)
    if not user.valid:
        return None
    return user

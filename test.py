##import os
##import scrypt
##
##from simple_recipes.db.users import *
##
##pw = 'Jedikiller1'
##salt = os.urandom(64)
##hashed = scrypt.hash(pw, salt)
##add_user('pam', hashed, salt)


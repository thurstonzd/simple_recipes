from enum import IntEnum, auto
import os

import click
import scrypt

from simple_recipes.db.users import *

class Options(IntEnum):
    SHOW_USER_INFO = auto()
    LOCK_USER = auto()
    UNLOCK_USER = auto()
    ADD_USER = auto()
    CHANGE_USER_PASSWORD = auto()
    SHOW_OPTIONS = auto()
    QUIT = auto()

def show_options():
    for name, member in Options.__members__.items():
        print(f'{member.value}: {name}')

def main():
    option = Options.SHOW_OPTIONS
    while option != Options.QUIT:

        #############################################################
        if option == Options.SHOW_OPTIONS:
            show_options()
        #############################################################
        if option == Options.SHOW_USER_INFO:
            user_name = input("Enter User Name: ")
            user_data = get_user(user_name=user_name)
            user_status = user_data['user_status']

            print()
            print(f"User Name: {user_data['user_name']}")

            if user_status == LOCKED: print(f"Account Status: Locked")
            elif user_status == RESET: print("Account Status: Reset")
            else: print("Account Status: Default")
            print()
            
        #############################################################
        elif option == Options.LOCK_USER:
            user_name = input("Enter User Name: ")
            lock_user(user_name=user_name)
            print(f"\nAccount '{user_name}' locked")
        #############################################################
        elif option == Options.UNLOCK_USER:
            user_name = input("Enter User Name: ")
            unlock_user(user_name=user_name)
            print(f"\nAccount for '{user_name}' unlocked.\n")
        #############################################################
        elif option == Options.ADD_USER:
            user_name = input("Enter new user name: ")
            pw = click.prompt("Enter password: ", hide_input=True)
            salt = os.urandom(64)
            hashed = scrypt.hash(pw, salt)
            add_user(user_name, hashed, salt)
            print(f"\nAccount created for '{user_name}'\n")
        #############################################################
        elif option == Options.CHANGE_USER_PASSWORD:
            user_name = input("Enter user name: ")
            pw = click.prompt("Enter new password: ", hide_input=True)
            salt = os.urandom(64)
            hashed = scrypt.hash(pw, salt)
            update_user_password(hashed, salt, user_name=user_name)
            print(f"\nPassword change for User ID '{user_name}'")
        #############################################################

        option = int(input("Enter option number: "))

if __name__ == "__main__": main()
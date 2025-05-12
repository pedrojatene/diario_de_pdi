import streamlit_authenticator as stauth

passwords = ['Pj#324639', 'jatene', 'jatene', 'jatene', 'jatene', 'jatene']
hashed_passwords = stauth.Hasher(passwords).generate()

for pw in hashed_passwords:
    print(pw)
import os
import streamlit as st

users = {'iFA': '123456'}


def check_password(inputs, password):
    max_length = 32
    while len(inputs) < max_length:
        inputs += '0'
    while len(password) < max_length:
        password += '0'
    correct = True
    for i in range(max_length):
        correct &= inputs[i] == password[i]
    return correct


def login():
    username = st.text_input('用户名：')
    if username and username not in users:
        st.write('用户名不存在！')
    password = st.text_input('密码：', type='password')
    if username and password and check_password(password, users[username]):
        print("password correct!")
        return True
    elif username and password:
        st.write('密码错误！')


def main():
    if login():
        os.system('streamlit run interact.py')


if __name__ == '__main__':
    main()

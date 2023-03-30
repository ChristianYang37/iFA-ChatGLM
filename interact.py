# https://sysu-ifa.streamlit.app/
import streamlit as st
import paramiko
import time


class SSH:
    def __init__(self, hostname, password, username, port):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=hostname, port=port, username=username, password=password)

    def post(self, input_text, history):
        ssh = self.client.get_transport().open_session()
        ssh.get_pty()
        ssh.invoke_shell()

        ssh.send(bytes("cd ChatGLM-6B\n", encoding='utf-8'))
        time.sleep(3)
        _ = ssh.recv(8192)

        s = ''
        for record in history:
            s += record[0] + 'STT'
            s += record[1] + 'STT'
        s = s[:-5]

        ssh.send(bytes(f"python post.py --input_text {input_text} --history {s}\n", encoding='utf-8'))
        time.sleep(3)
        response = ssh.recv(8192)

        print(response.decode('utf-8'))

        response = eval(response.decode('utf-8').split('\r')[1][1:])
        response, history = response['response'], response['history']

        return response, history


class APP:
    txt = ''

    def __init__(self):
        self.client = SSH(st.secrets['hostname'], st.secrets['password'], st.secrets['username'], st.secrets['port'])
        # st.title('iFA: 你的智能法律咨询顾问')
        st.title('Chat with ChatGLM-6B!')
        self.SHARE = st.checkbox('与开发者共享聊天数据')

    def loop(self):
        chat_state = {'LoopTimeCount': 0, 'GetInput': True, 'History': []}
        while True:
            chat_state = self.interact(**chat_state)

    def interact(self, LoopTimeCount, GetInput, History):
        input_text = ''
        if GetInput:
            input_text = st.text_input('请输入', key=LoopTimeCount)
        if input_text:
            print(input_text, History)
            response, History = self.client.post(input_text, History)

            st.code(response)

            if self.SHARE:
                self.record(input_text, response)

            del input_text
        else:
            GetInput = False
        return {'LoopTimeCount': LoopTimeCount + 1, 'GetInput': GetInput, 'History': History}

    def record(self, input_text, response):
        self.txt += f'ASK: {input_text}\n'
        self.txt += f'ANSWER: {response}\n\n'


if __name__ == '__main__':
    app = APP()
    app.loop()

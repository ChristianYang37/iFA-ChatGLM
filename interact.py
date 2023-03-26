import streamlit as st
import paramiko


def connect(hostname, password, username, port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, port=port, username=username, password=password)
    return client


class APP:
    txt = ''

    def __init__(self):
        self.client = connect(st.secrets['hostname'], st.secrets['password'], st.secrets['username'],
                              st.secrets['port'])
        st.title('iFA: 你的智能法律咨询顾问')
        self.SHARE = st.checkbox('与开发者共享聊天数据')

    def loop(self):
        chat_state = {'LoopTimeCount': 0, 'GetInput': True, 'History': []}
        while True:
            chat_state = self.interact(**chat_state)

    def interact(self, LoopTimeCount, GetInput, History):
        input_text = ''
        if GetInput:
            input_text = st.text_input('', key=LoopTimeCount)
        if input_text:
            stdin, stdout, stderr = self.client.exec_command(
                f"cd ChatGLM-6B && python post.py --input_text {input_text} --history {History}")
            print(stdout.read().decode('utf-8'))
            response = eval(stdout.read().decode('utf-8'))
            response, History = response['response'], response['history']

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
